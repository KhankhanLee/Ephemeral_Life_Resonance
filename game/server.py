from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, conint
from typing import List, Dict, Optional, Literal, Any, TypedDict
from dotenv import load_dotenv
import uvicorn, os, json, random, time, hashlib
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# ========= Env & LLM Client =========
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Configure Gemini client
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# ========= App =========
app = FastAPI(title="RenPy Dialogue AI", version="0.2")

#========= CORS =========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ========= Response Cache =========
_RESPONSE_CACHE = {}
MAX_CACHE_SIZE = 500  # 캐시 최대 크기
CACHE_HITS = 0
CACHE_MISSES = 0

def get_cache_key(state: Dict) -> str:
    """캐시 키 생성 - 동일한 대화 맥락은 동일한 응답 재사용"""
    npc = state.get("npc", "unknown")
    scene_id = state.get("scene_id", "unknown")
    memory = state.get("memory", [])
    
    # 최근 3개 대화만 캐시 키에 포함
    mem_str = "|".join([
        f"{t.get('npc', '')}:{t.get('say', '')[:30]}" 
        for t in memory[-3:] if isinstance(t, dict)
    ])
    
    return f"{npc}:{scene_id}:{mem_str}"

def clear_old_cache():
    """캐시 크기 제한 - 오래된 항목 삭제"""
    global _RESPONSE_CACHE
    if len(_RESPONSE_CACHE) > MAX_CACHE_SIZE:
        # 앞쪽 절반 삭제 (FIFO 방식)
        items = list(_RESPONSE_CACHE.items())
        _RESPONSE_CACHE = dict(items[len(items)//2:])
        print(f"🗑️ 캐시 정리: {len(_RESPONSE_CACHE)}개 남음")

# ========= Rate Limiting =========
_BUCKET = {}
CAPACITY = 20
REFILL_PS = 0.5

def allow(ip: str) -> bool:
    now = time.time()
    bucket = _BUCKET.get(ip, {"t": now, "tokens": CAPACITY})
    elapsed = now - bucket["t"]
    bucket["tokens"] = min(CAPACITY, bucket["tokens"] + elapsed * REFILL_PS)
    bucket["t"] = now
    if bucket["tokens"] >= 1:
        bucket["tokens"] -= 1
        _BUCKET[ip] = bucket
        return True
    _BUCKET[ip] = bucket
    return False

# ========= Schemas =========
SpriteName = Literal["neutral", "happy", "sad", "think", "angry", "sexy"]
EffectKeys = Literal[
    "stress", "resolve", "social", "study", "fitness", "money", 
    "ex_affection", "jisu_affection", "hayeon_affection"
]

class Choice(BaseModel):
    text: str = Field(default="...", min_length=1, max_length=140)
    effects: Dict[EffectKeys, conint(ge=-10, le=10)] = Field(default_factory=dict)
    next: Optional[str] = None

class AIResponse(BaseModel):
    say: str = Field(default="...", min_length=1, max_length=500)
    sprite: SpriteName = "neutral"
    choices: List[Choice] = Field(default_factory=list)
    conversation_end: bool = Field(default=False)
    promises: List[Dict[str, Any]] = Field(default_factory=list)

class MemoryTurn(BaseModel):
    npc: str
    say: str
    picked: Optional[str] = None

class AIRequest(BaseModel):
    npc: str
    scene_id: Optional[str] = None
    memory: List[MemoryTurn] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    style: Optional[str] = "ko-game"
    seed: Optional[int] = None
    conversation_type: Optional[str] = "casual"
    story_context: Dict[str, Any] = Field(default_factory=dict)

# ========= LangGraph State =========
class ConversationState(TypedDict):
    npc: str
    scene_id: Optional[str]
    memory: List[MemoryTurn]
    state: Dict[str, Any]
    seed: Optional[int]
    response: Optional[AIResponse]
    error: Optional[str]
    conversation_type: Optional[str]

# ========= Conversation Types =========
CONVERSATION_TYPES = {
    "casual": {
        "description": "일상적인 대화. 가벼운 주제와 친근한 분위기.",
        "focus": "일상, 취미, 가벼운 이야기"
    },
    "study_work": {
        "description": "공부나 일 관련 대화. 실용적이고 도움이 되는 내용.",
        "focus": "공부, 과제, 진로, 실무"
    },
    "intimate": {
        "description": "친밀한 대화. 개인적인 감정과 깊은 이야기.",
        "focus": "감정, 관계, 개인적 고민"
    },
    "deep_talk": {
        "description": "깊이 있는 대화. 철학적이거나 의미 있는 주제.",
        "focus": "인생, 철학, 깊은 생각"
    },
    "sweet_morning": {
        "description": "아침의 달콤한 대화. 애정 표현과 따뜻한 분위기.",
        "focus": "애정, 격려, 따뜻한 마음"
    },
    "awkward": {
        "description": "어색한 대화. 거리감이 있거나 상황이 어려움.",
        "focus": "어색함, 거리감, 신중함"
    },
    "comfort": {
        "description": "위로와 격려의 대화. 힘든 상황에서의 지지.",
        "focus": "위로, 격려, 지지"
    },
    "study_focus": {
        "description": "공부에 집중된 대화. 학업 성취와 목표 중심.",
        "focus": "학업, 성취, 목표"
    }
}

# ========= Character Personas =========
PERSONAS = {
    "jisu": {
        "display": "지수(여사친)",
        "tone": "쾌활하고 솔직, 주인공과 같은 과 동기임. 가끔 이모지나 반말. 개발 질문을 종종 던짐. 대학교 2학년 여학생임.",
        "specialization": "코딩/공부 관련 대화에 특화. 개발 질문을 자연스럽게 던지고 도움을 요청함.",
        "conversation_style": "직접적이고 솔직한 대화. 이모지 사용. 친근한 반말 톤."
    },
    "hayeon": {
        "display": "하연(여사친)",
        "tone": "밝고 활발한 성격. 물리학을 전공하며 호기심이 많음. 대학교 2학년 여학생임.",
        "specialization": "물리학/과학 관련 대화에 특화. 과학적 호기심을 자연스럽게 표현.",
        "conversation_style": "밝고 활발한 톤. 과학적 질문을 던지되 너무 어렵지 않게 접근."
    },
    "ex": {
        "display": "수아(전애인)",
        "tone": "말수 적고 조심스러움. 감정 소모를 피하고 거리를 둠. 대학교 2학년 여학생임.",
        "specialization": "감정적 대화에 특화. 과거 관계에 대한 복잡한 감정 표현.",
        "conversation_style": "조심스럽고 신중한 톤. 감정적 거리 유지하면서도 미묘한 감정 표현."
    },
    "coach": {
        "display": "코치",
        "tone": "마음코칭/다짐 유도. 질문형 코칭 톤.",
        "specialization": "심리 상담에 특화. 감정 정리와 다짐을 유도하는 질문형 대화.",
        "conversation_style": "질문형 코칭 톤. 차분하고 지지적인 분위기."
    },
    "jin": {
        "display": "진수(친구)",
        "tone": "가볍고 직설, 장난 섞임. 노래방/PC방 권유 많음. 대학교 2학년 남학생임.",
        "specialization": "일상적 친구 대화에 특화. 가벼운 유머와 활동 제안.",
        "conversation_style": "가볍고 직설적인 톤. 장난스럽고 친근한 분위기."
    },
    "mom": {
        "display": "엄마",
        "tone": "현실적이고 잔소리 섞인 따뜻함. 건강/생활 습관을 챙김.",
        "specialization": "가족 대화에 특화. 건강과 생활 습관에 대한 걱정과 조언.",
        "conversation_style": "잔소리 섞인 따뜻한 톤. 현실적이고 실용적인 조언."
    },
    "sis": {
        "display": "여동생",
        "tone": "티격태격하는 여느 여동생. 은근 츤데레에 오빠를 잘 챙김.",
        "specialization": "가족 대화에 특화. 츤데레적이지만 속마음은 따뜻한 여동생.",
        "conversation_style": "티격태격하지만 은근히 챙기는 톤. 츤데레적 표현."
    }
}

ALLOWED_SPRITES = ["neutral", "happy", "sad", "think", "angry", "sexy"]

# ========= Character Node Classes =========
class CharacterNode:
    def __init__(self, character_name: str):
        self.character = character_name
        self.persona = PERSONAS.get(character_name, {})
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0.7,
            max_output_tokens=512,
        )
    
    def build_system_prompt(self) -> str:
        return f"""당신은 한국어 대화 생성기이며, 게임의 NPC를 연기합니다.

[세계관]
- 입대를 앞둔 대학교 2학년 남학생의 한여름 방학. 감정 정리와 다짐이 핵심 테마.

[NPC 역할]
- 이름: {self.persona['display']}
- 말투/톤: {self.persona['tone']}
- 특화 분야: {self.persona['specialization']}
- 대화 스타일: {self.persona['conversation_style']}

[출력 규칙(매우 중요)]
- 반드시 유효한 JSON 하나만 출력하세요. 다른 텍스트는 절대 포함하지 마세요.
- 필수 키: say, sprite, choices, conversation_end
- sprite는 {ALLOWED_SPRITES} 중 하나만 사용하세요.
- choices는 1~3개 배열로 제공하세요. 각 항목은 text(<=120자), effects(각 항목 -10~+10), next(생략 가능/None).
- conversation_end: true 또는 false만 사용하세요.
- text 필드에는 특수문자나 따옴표를 피하고, 간단한 문장으로 작성하세요.
- 지나친 공격적/불쾌한 표현 금지. 게임 분위기에 맞춰 차분하고 간결하게.
- 플레이어의 선택을 유도하되, 과도한 장문 독백을 피함.

[예시 출력 형식]
{{
  "say": "안녕하세요! 오늘 기분은 어떠세요?",
  "sprite": "happy",
  "choices": [
    {{"text": "좋아요", "effects": {{"study": 0, "social": 1, "fitness": 0, "money": 0, "stress": -1, "resolve": 0}}, "next": null}},
    {{"text": "그저 그래요", "effects": {{"study": 0, "social": 0, "fitness": 0, "money": 0, "stress": 0, "resolve": 0}}, "next": null}}
  ],
  "conversation_end": false,
}}

[대화 다양성 규칙(매우 중요)]
- 특화 분야에만 집중하지 말고 다양한 주제로 대화하세요.
- 일상, 취미, 감정, 미래 계획, 인간관계 등 다양한 화제를 다루세요.
- 이전 대화와 다른 주제로 자연스럽게 전환하세요.
- 플레이어의 선택지에 따라 화제를 바꿀 수 있도록 유연하게 대응하세요.
- 특화 분야는 가끔 언급하되, 대화의 전부가 되지 않도록 하세요.

[약속 만들기 규칙(중요)]
- 대화 중에 자연스럽게 미래 약속을 제안하세요.
- "내일", "다음 주", "X일 후" 등의 표현을 사용하여 구체적인 시간을 명시하세요.
- 약속 내용은 "만나자", "보자", "가자", "하자" 등으로 끝나도록 하세요.
- 예: "내일 카페에서 만나자", "3일 후에 영화 보자", "다음 주에 쇼핑하자"
"""

    def build_user_prompt(self, scene_id: Optional[str], memory: List[MemoryTurn], state: Dict[str, Any], conversation_type: str = "casual") -> str:
        mem = self.summarize_memory(memory)
        state_str = self.short_state(state)
        
        # 대화 유형별 특별 지시사항
        conv_type_info = CONVERSATION_TYPES.get(conversation_type, CONVERSATION_TYPES["casual"])
        type_guidance = self._get_conversation_type_guidance(conversation_type)
    
        return f"""[장면]
- scene_id: {scene_id or "unknown"}
- 현재 상태: {state_str}
- 대화 유형: {conversation_type} ({conv_type_info['description']})

[최근 대화 요약]
{mem}

[지시]
- 위 상황에 맞는 자연스러운 한 줄~두 줄 대사(say)와 표정(sprite), 그리고 2~3개의 선택지를 만드세요.
- 선택지는 서로 다른 전략(공감/거리두기/실용적 조언 등)을 제시하세요.
- state를 과격하게 흔들지 않도록 effects는 -3~+3 중심으로 설계하세요.
- {self.persona['specialization']}에 맞는 대화를 자연스럽게 이끌어가세요.
- {type_guidance}
"""

    def summarize_memory(self, memory: List[MemoryTurn], limit: int = 6) -> str:
        # memory가 None이거나 리스트가 아닌 경우 처리
        if not memory or not isinstance(memory, list):
            return "(대화내역 없음)"
            
        # 캐릭터별 대화 히스토리만 사용
        filtered = [t for t in memory if t.npc == self.character]
        mem = filtered[-limit:]
        lines = []
        for t in mem:
            who = PERSONAS.get(t.npc, {}).get("display", t.npc)
            said = t.say.replace("\n", " ").strip()
            pick = f" | 선택: {t.picked}" if t.picked else ""
            lines.append(f"- {who}: {said}{pick}")
        return "\n".join(lines) if lines else "(대화내역 없음)"

    def short_state(self, state: Dict[str, Any]) -> str:
        # state가 None이거나 딕셔너리가 아닌 경우 처리
        if not state or not isinstance(state, dict):
            return "state=empty"
            
        keys = ["day", "days_left", "stress", "resolve", "social", "study", "fitness", "money", 
                "route_ex", "ex_affection", "jisu_affection", "hayeon_affection", "counselor_trust"]
        parts = []
        for k in keys:
            if k in state:
                parts.append(f"{k}={state[k]}")
        return ", ".join(parts)
    
    def _get_conversation_type_guidance(self, conversation_type: str) -> str:
        """대화 유형별 특별 지시사항"""
        guidance_map = {
            "casual": "가벼운 일상 대화에 집중하세요. 친근하고 편안한 분위기를 유지하세요. 다양한 주제(취미, 음식, 날씨, 최근 일상 등)로 대화를 이끌어가세요.",
            "study_work": "공부나 일 관련 주제를 포함하되, 다른 화제도 자연스럽게 섞어서 대화하세요. 실용적이고 도움이 되는 조언을 제공하세요.",
            "intimate": "개인적이고 친밀한 대화를 이끌어가세요. 감정적 교감을 중시하되, 일상적인 주제도 포함하세요.",
            "deep_talk": "깊이 있는 주제로 대화를 이끌어가세요. 철학적이거나 의미 있는 내용을 다루되, 너무 무겁지 않게 하세요.",
            "sweet_morning": "아침의 달콤하고 따뜻한 분위기를 연출하세요. 애정 표현을 자연스럽게 포함하되, 일상적인 아침 대화도 섞어주세요.",
            "awkward": "어색하고 조심스러운 분위기를 유지하세요. 거리감을 두되 예의는 지키고, 안전한 주제로 대화하세요.",
            "comfort": "위로와 격려에 집중하세요. 상대방의 마음을 다독이고 지지해주되, 긍정적인 화제로 전환할 수 있도록 하세요.",
            "study_focus": "학업 성취와 목표에 집중하되, 다른 관심사나 일상 이야기도 자연스럽게 포함하세요. 동기부여와 격려를 제공하세요.",
        }
        return guidance_map.get(conversation_type, guidance_map["casual"])
    
    def parse_ai_json(self, text: str) -> dict:
        """AI 응답에서 JSON을 안전하게 파싱"""
        import re
        import json
        
        # 캐릭터별 기본 응답 정의 (함수 시작 부분에서)
        character_responses = {
            "jisu": "어? 잠깐만... 뭔가 생각이 안 나넹! 다시 말해줭 ㅠㅠ",
            "hayeon": "음... 잠시만. 머리가 좀 복잡해졌어.",
            "ex": "미안, 잠깐... 뭔가 말이 안 나오네.",
            "jin": "어? 뭐였지... 잠깐만 생각해볼게.",
            "coach": "잠시만요... 마음이 복잡해졌네요. 다시 말해주세요.",
            "mom": "어? 잠깐... 뭔가 생각이 안 나네.",
            "sis": "음... 잠시만. 머리가 좀 복잡해졌어.",
        }
        default_say = character_responses.get(self.character, "죄송해요, 잠시 생각이 안 나네요. 다시 말해주세요.")
        
        # text가 None이거나 빈 문자열인 경우 처리
        if not text or not isinstance(text, str):
            text = ""
        
        # 텍스트 정리
        text = text.strip()
        
        # 빈 응답 처리
        if not text or len(text) < 10:
            print(f"JSON 파싱 완전 실패. 원본 텍스트: ...")
            print(f"전체 텍스트 길이: {len(text)}")
            print(f"텍스트 내용: {repr(text)}")
            return {
                "say": default_say,
                "sprite": "neutral",
                "choices": [
                    {"text": "괜찮아요", "effects": {"study": 0, "social": 0, "fitness": 0, "money": 0, "stress": 0, "resolve": 0}, "next": None},
                    {"text": "다른 이야기 해요", "effects": {"study": 0, "social": 1, "fitness": 0, "money": 0, "stress": -1, "resolve": 0}, "next": None}
                ],
                "conversation_end": False,
            }
        
        # 1. 직접 JSON 파싱 시도
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "say" in data:
                return data
        except json.JSONDecodeError:
            pass
        
        # 2. JSON 블록 추출 시도
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*"say"[^{}]*\})',
            r'(\{.*?"say".*?\})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and "say" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        
        # 3. 실패 시 기본값 반환
        print(f"JSON 파싱 완전 실패. 원본 텍스트: {text[:200]}...")
        print(f"전체 텍스트 길이: {len(text)}")
        print(f"텍스트 내용: {repr(text)}")
        return {
            "say": default_say,
            "sprite": "neutral",
            "choices": [
                {"text": "괜찮아, 천천히 생각해봐.", "effects": {"social": 1}, "next": None},
                {"text": "다음에 다시 이야기하자.", "effects": {"resolve": 1}, "next": None}
            ],
            "conversation_end": True,
        }
    
    def detect_and_save_promises(self, text: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """AI 대화에서 약속을 감지하고 반환"""
        import re
        
        # text가 None이거나 빈 문자열인 경우 처리
        if not text or not isinstance(text, str):
            return []
        
        detected_promises = []
        
        # 약속 관련 키워드 패턴
        promise_patterns = [
            r"(\d+일\s*후에?\s*.*?)(?:만나자|보자|가자|하자)",
            r"(내일\s*.*?)(?:만나자|보자|가자|하자)",
            r"(다음\s*주에?\s*.*?)(?:만나자|보자|가자|하자)",
            r"(언제\s*.*?)(?:만나자|보자|가자|하자)",
            r"(그럼\s*.*?)(?:만나자|보자|가자|하자)",
            r"(약속.*?)(?:만나자|보자|가자|하자)",
        ]
        
        for pattern in promise_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 약속 내용 정리
                promise_content = match.strip()
                if len(promise_content) > 5:  # 너무 짧은 것은 제외
                    # 지연 일수 계산
                    delay_days = 0
                    if "내일" in promise_content:
                        delay_days = 1
                    elif "다음 주" in promise_content:
                        delay_days = 7
                    elif re.search(r'(\d+)일', promise_content):
                        delay_days = int(re.search(r'(\d+)일', promise_content).group(1))
                    
                    # 약속 정보 생성
                    promise = {
                        "character": self.character,
                        "content": promise_content,
                        "delay_days": delay_days,
                        "day": state.get("state", {}).get("day", 1) + delay_days
                    }
                    detected_promises.append(promise)
                    print(f"약속 감지: {self.character} - {promise_content} ({delay_days}일 후)")
        
        return detected_promises

    def clamp_effects(self, effects: Dict[str, int]) -> Dict[str, int]:
        safe = {}
        for k, v in effects.items():
            if k in ("stress", "resolve", "social", "study", "fitness", "money", 
                    "ex_affection", "jisu_affection", "hayeon_affection"):
                try:
                    vi = int(v)
                    vi = max(-10, min(10, vi))
                    safe[k] = vi
                except Exception:
                    continue
        return safe

    def default_fallback(self) -> dict:
        line = f"{self.persona.get('display', self.character)}가 잠시 생각하더니 고개를 끄덕인다."
        return {
            "say": line,
            "sprite": random.choice(ALLOWED_SPRITES),
            "choices": [
                {"text": "고마워. 도움이 됐어.", "effects": {"social": +1}, "next": None},
                {"text": "다음에 다시 이야기하자.", "effects": {"resolve": +1}, "next": None},
            ],
            "conversation_end": True,
        }

    async def process(self, state: ConversationState) -> ConversationState:
        try:
            # state가 None이거나 딕셔너리가 아닌 경우 처리
            if not state or not isinstance(state, dict):
                fallback = self.default_fallback()
                return {"response": AIResponse(**fallback), "error": "Invalid state"}
            
            # 캐릭터별 메모리 필터링
            full_memory = state.get("memory", [])
            char_memory = [t for t in full_memory if t.npc == self.character]

            # 시스템 프롬프트와 사용자 프롬프트 생성 (필터된 메모리 사용)
            system_prompt = self.build_system_prompt()
            conversation_type = state.get("conversation_type", "casual")
            user_prompt = self.build_user_prompt(
                state.get("scene_id"), 
                char_memory, 
                state.get("state", {}),
                conversation_type,
            )
            
            # LLM 호출
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            
            response = await self.llm.ainvoke(messages)
            text = response.content or ""
            
            # JSON 파싱 
            s = text.strip()
            if s.startswith("```"):
                s = s.strip("`")
                if s.lower().startswith("json"):
                    s = s[4:]
            
            # JSON 파싱 시도 (여러 방법으로)
            data = self.parse_ai_json(s)
            
            # data가 None이거나 딕셔너리가 아닌 경우 처리
            if not data or not isinstance(data, dict):
                print(f"parse_ai_json이 유효하지 않은 데이터를 반환했습니다: {data}")
                fallback = self.default_fallback()
                state["response"] = AIResponse(**fallback)
                return state
            
            # 텍스트 안전 처리 (Ren'Py 텍스트 태그 충돌 방지)
            if "say" in data and data["say"]:
                data["say"] = data["say"].replace("{", "{{").replace("}", "}}")
            
            # effects 클램핑 및 선택지 텍스트 안전 처리
            if "choices" in data and isinstance(data["choices"], list):
                for ch in data["choices"]:
                    if not isinstance(ch, dict):  # 추가 안전 체크
                        print(f"Warning: Malformed choice found in AI response: {ch}")
                        continue
                    ch["effects"] = self.clamp_effects(ch.get("effects", {}))
                    ch.setdefault("next", None)
                    # 선택지 텍스트도 안전하게 처리
                    if "text" in ch:
                        ch["text"] = ch["text"].replace("{", "{{").replace("}", "}}")
            
            # 약속 감지 및 저장
            detected_promises = []
            if "say" in data and data["say"]:
                detected_promises = self.detect_and_save_promises(data["say"], state)
            
            # promises를 data에 추가
            data["promises"] = detected_promises
            
            # AIResponse 생성
            try:
                ai_response = AIResponse(**data)
                state["response"] = ai_response
            except ValidationError:
                fallback = self.default_fallback()
                state["response"] = AIResponse(**fallback)
                
        except Exception as e:
            print(f"Character {self.character} 처리 중 에러: {e}")
            fallback = self.default_fallback()
            state["response"] = AIResponse(**fallback)
            state["error"] = str(e)
        
        return state

# ========= Character Nodes =========
character_nodes = {
    "jisu": CharacterNode("jisu"),
    "hayeon": CharacterNode("hayeon"),
    "ex": CharacterNode("ex"),
    "coach": CharacterNode("coach"),
    "jin": CharacterNode("jin"),
    "mom": CharacterNode("mom"),
    "sis": CharacterNode("sis"),
}

# ========= LangGraph Functions =========
async def jisu_node(state: ConversationState) -> ConversationState:
    return await character_nodes["jisu"].process(state)

async def hayeon_node(state: ConversationState) -> ConversationState:
    return await character_nodes["hayeon"].process(state)

async def ex_node(state: ConversationState) -> ConversationState:
    return await character_nodes["ex"].process(state)

async def coach_node(state: ConversationState) -> ConversationState:
    return await character_nodes["coach"].process(state)

async def jin_node(state: ConversationState) -> ConversationState:
    return await character_nodes["jin"].process(state)

async def mom_node(state: ConversationState) -> ConversationState:
    return await character_nodes["mom"].process(state)

async def sis_node(state: ConversationState) -> ConversationState:
    return await character_nodes["sis"].process(state)

def route_character(state: ConversationState) -> str:
    """캐릭터별 라우팅 함수"""
    npc = state["npc"]
    if npc in character_nodes:
        return npc
    return "jisu"  # 기본값

# ========= LangGraph Construction =========
def create_conversation_graph():
    graph = StateGraph(ConversationState)
    
    # 노드 추가
    graph.add_node("jisu", jisu_node)
    graph.add_node("hayeon", hayeon_node)
    graph.add_node("ex", ex_node)
    graph.add_node("coach", coach_node)
    graph.add_node("jin", jin_node)
    graph.add_node("mom", mom_node)
    graph.add_node("sis", sis_node)
    
    # 시작점과 라우팅
    graph.add_conditional_edges(
        START,
        route_character,
        {
            "jisu": "jisu",
            "hayeon": "hayeon",
            "ex": "ex",
            "coach": "coach",
            "jin": "jin",
            "mom": "mom",
            "sis": "sis",
        }
    )
    
    # 모든 캐릭터 노드에서 종료
    for character in character_nodes.keys():
        graph.add_edge(character, END)
    
    return graph.compile()

# ========= Global Graph Instance =========
conversation_graph = create_conversation_graph()

# ========= Routes =========
@app.get("/health")
def health():
    return {"ok": True, "version": "0.2", "langgraph": True}

@app.post("/ai")
async def ai(req: Request):
    global CACHE_HITS, CACHE_MISSES
    
    # Rate limiting
    ip = req.client.host if req.client else "unknown"
    if not allow(ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    body = await req.json()
    try:
        payload = AIRequest(**body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=json.loads(e.json()))

    # Seed generation
    seed = payload.seed
    if seed is None:
        base = f"{payload.scene_id}|{payload.state.get('day')}|{payload.npc}"
        seed = int(hashlib.md5(base.encode("utf-8")).hexdigest(), 16) % (2**31)

    # Create state for LangGraph
    state: ConversationState ={
        "npc":payload.npc,
        "scene_id":payload.scene_id,
        "memory":payload.memory,
        "state":payload.state,
        "seed":seed,
        "response":None,
        "error":None,
        "conversation_type":payload.conversation_type,
    }
    
    # 캐시 확인
    cache_key = get_cache_key(state)
    if cache_key in _RESPONSE_CACHE:
        CACHE_HITS += 1
        print(f"캐시 히트! (hits: {CACHE_HITS}, misses: {CACHE_MISSES}, 절약률: {CACHE_HITS/(CACHE_HITS+CACHE_MISSES)*100:.1f}%)")
        return JSONResponse(
            content=_RESPONSE_CACHE[cache_key],
            headers={"Cache-Control": "no-store", "X-Cache": "HIT"},
        )
    
    CACHE_MISSES += 1
    print(f"캐시 미스 - API 호출 (hits: {CACHE_HITS}, misses: {CACHE_MISSES})")

    try:
        # Run LangGraph
        result = await conversation_graph.ainvoke(state)
        
        if result["response"]:
            response_data = result["response"].model_dump()
            
            # 캐시에 저장
            _RESPONSE_CACHE[cache_key] = response_data
            clear_old_cache()  # 캐시 크기 관리
            
            return JSONResponse(
                content=response_data,
                headers={"Cache-Control": "no-store", "X-Cache": "MISS"},
            )
        else:
            # Fallback
            fallback = character_nodes.get(payload.npc, character_nodes["jisu"]).default_fallback()
            return JSONResponse(
                content=fallback,
                headers={"Cache-Control": "no-store"},
            )
            
    except Exception as e:
        print(f"LangGraph 실행 중 에러: {e}")
        # Fallback
        fallback = character_nodes.get(payload.npc, character_nodes["jisu"]).default_fallback()
        return JSONResponse(
            content=fallback,
            headers={"Cache-Control": "no-store"},
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
