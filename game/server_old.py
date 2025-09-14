from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, conint
from typing import List, Dict, Optional, Literal, Any
from dotenv import load_dotenv
import uvicorn, os, json, random, time, hashlib
import google.generativeai as genai

# ========= Env & LLM Client =========
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "").strip() or None

# Configure Gemini client
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# ========= App =========
app = FastAPI(title="RenPy Dialogue AI", version="0.1")

# ========= (Optional) Very light rate limit (per-ip token bucket) =========
_BUCKET = {}
CAPACITY = 20      # tokens
REFILL_PS = 0.5    # tokens per second
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
SpriteName = Literal["neutral", "happy", "sad", "think","angry","sexy"]
EffectKeys = Literal[
    "stress","resolve","social","study","fitness","money","ex_affection","jisu_affection"
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

# ========= Personas & System Prompt =========
PERSONAS = {
    "jisu": {
        "display": "지수(여사친)",
        "tone": "쾌활하고 솔직, 주인공과 같은 과 동기임. 가끔 이모지나 반말. 개발 질문을 종종 던짐.",
    },
    "hayeon": {
        "display": "하연(여사친)",
        "tone": "밝고 활발한 성격. 물리학을 전공하며 호기심이 많음. 친구에게 도움을 요청할 때는 솔직하고 직접적. 대화할 때는 자연스럽고 편안한 분위기를 만듦.",
    },
    "ex": {
        "display": "수아(전애인)",
        "tone": "말수 적고 조심스러움. 감정 소모를 피하고 거리를 둠. 다른 친구들을 잘 챙김.",
    },
    "mom": {
        "display": "엄마",
        "tone": "현실적이고 잔소리 섞인 따뜻함. 건강/생활 습관을 챙김.",
    },
    "coach": {
        "display": "코치",
        "tone": "마음코칭/다짐 유도. 질문형 코칭 톤.",
    },
    "jin": {
        "display": "진수(친구)",
        "tone": "가볍고 직설, 장난 섞임. 노래방/PC방 권유 많음.",
    },
    "sis": {
        "display": "여동생",
        "tone": "티격태격하는 여느 여동생. 은근 츤데레에 오빠를 잘 챙김.",
    },
    "m": {
        "display": "주인공",
        "tone": "내적 독백/담백한 1인칭.",
    }
}

ALLOWED_SPRITES = ["neutral","happy","sad","think","angry","sexy"]

# ========= Helpers =========
def clamp_effects(effects: Dict[str, int]) -> Dict[str, int]:
    safe = {}
    for k, v in effects.items():
        if k in ("stress","resolve","social","study","fitness","money","ex_affection","jisu_affection","hayeon_affection"):
            try:
                vi = int(v)
                vi = max(-10, min(10, vi))
                safe[k] = vi
            except Exception:
                continue
    return safe

def default_fallback(npc: str) -> dict:
    # rule-based fallback when LLM fails
    line = f"{PERSONAS.get(npc, {}).get('display', npc)}가 잠시 생각하더니 고개를 끄덕인다."
    return {
        "say": line,
        "sprite": random.choice(ALLOWED_SPRITES),
        "choices": [
            {"text":"고마워. 도움이 됐어.", "effects":{"social":+1}, "next": None},
            {"text":"다음에 다시 이야기하자.", "effects":{"resolve":+1}, "next": None},
        ],
        "conversation_end": True
    }

def short_state(state: Dict[str, int]) -> str:
    keys = ["day","days_left","stress","resolve","social","study","fitness","money","route_ex","ex_affection","jisu_affection","hayeon_affection","counselor_trust"]
    parts = []
    for k in keys:
        if k in state:
            parts.append(f"{k}={state[k]}")
    return ", ".join(parts)

def summarize_memory(memory: List[MemoryTurn], limit: int = 6) -> str:
    # last 'limit' turns compact summary
    mem = memory[-limit:]
    lines = []
    for t in mem:
        who = PERSONAS.get(t.npc, {}).get("display", t.npc)
        said = t.say.replace("\n"," ").strip()
        pick = f" | 선택: {t.picked}" if t.picked else ""
        lines.append(f"- {who}: {said}{pick}")
    return "\n".join(lines) if lines else "(대화내역 없음)"

def build_system_prompt(npc: str) -> str:
    persona = PERSONAS.get(npc, {"display": npc, "tone": ""})
    return f"""당신은 한국어 대화 생성기이며, 게임의 NPC를 연기합니다.

[세계관]
- 입대를 앞둔 대학교 2학년 남학생의 한여름 방학. 감정 정리와 다짐이 핵심 테마.

[NPC 역할]
- 이름: {persona['display']}
- 말투/톤: {persona['tone']}

[출력 규칙(중요)]
- 반드시 JSON 하나만 출력하세요. 키: say, sprite, choices, conversation_end
- sprite는 {ALLOWED_SPRITES} 중 하나만.
- choices는 1~3개. 각 항목은 text(<=120자), effects(각 항목 -10~+10), next(생략 가능/None).
- conversation_end: true로 설정하면 대화가 자연스럽게 끝납니다. false면 계속 대화합니다.
- text 필드에는 특수문자나 따옴표를 피하고, 간단한 문장으로 작성하세요.
- 지나친 공격적/불쾌한 표현 금지. 게임 분위기에 맞춰 차분하고 간결하게.
- 플레이어의 선택을 유도하되, 과도한 장문 독백을 피함.
"""

def build_user_prompt(npc: str, scene_id: Optional[str], memory: List[MemoryTurn], state: Dict[str, int]) -> str:
    mem = summarize_memory(memory)
    
    # 하연 캐릭터에 대한 특별한 안내
    special_guidance = ""
    if npc == "hayeon":
        special_guidance = """
[하연 캐릭터 특별 안내]
- 하연은 물리학을 전공하는 밝고 활발한 여학생입니다.
- 대화할 때는 자연스럽고 편안한 분위기를 만듭니다.
- 물리나 과학 관련 질문을 할 수 있지만, 너무 어렵지 않게 접근합니다.
- 친구에게 도움을 요청할 때는 솔직하고 직접적입니다.
- 대화는 2-3번 정도 자연스럽게 이어지도록 하세요.
"""
    
    return f"""[장면]
- scene_id: {scene_id or "unknown"}
- 현재 상태: {short_state(state)}

[최근 대화 요약]
{mem}
{special_guidance}
[지시]
- 위 상황에 맞는 자연스러운 한 줄~두 줄 대사(say)와 표정(sprite), 그리고 2~3개의 선택지를 만드세요.
- 선택지는 서로 다른 전략(공감/거리두기/실용적 조언 등)을 제시하세요.
- state를 과격하게 흔들지 않도록 effects는 -3~+3 중심으로 설계하세요.
"""
def call_gemini(npc: str, scene_id: Optional[str], memory: List[MemoryTurn],
                state: Dict[str, int], seed: Optional[int]) -> dict:
    if not GOOGLE_API_KEY:
        raise RuntimeError("Gemini API key not configured")

    try:
        sys_prompt = build_system_prompt(npc)
        user_prompt = build_user_prompt(npc, scene_id, memory, state)

        # NPC마다 다른 시스템 프롬프트가 필요하므로 호출마다 모델 인스턴스화
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=sys_prompt
        )

        gen_cfg = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=512,
            # JSON 강제
            response_mime_type="application/json",
        )

        resp = model.generate_content(
            user_prompt,
            generation_config=gen_cfg,
            # 안전설정은 기본값 사용(원하면 조정 가능)
        )

        text = resp.text or ""
        # 혹시라도 코드펜스가 끼면 제거
        s = text.strip()
        if s.startswith("```"):
            s = s.strip("`")
            if s.lower().startswith("json"):
                s = s[4:]
        data = json.loads(s)
        return data
    except Exception as e:
        print(f"Gemini API 호출 중 에러 발생: {e}")
        raise

def sanitize_response(raw: dict) -> AIResponse:
    # Fill defaults and clamp effects
    if "choices" in raw and isinstance(raw["choices"], list):
        for ch in raw["choices"]:
            ch["effects"] = clamp_effects(ch.get("effects", {}))
            ch.setdefault("next", None)
    try:
        return AIResponse(**raw)
    except ValidationError as e:
        # Minimal salvage
        fb = default_fallback(raw.get("npc","npc"))
        return AIResponse(**fb)

# ========= Routes =========
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ai")
async def ai(req: Request):
    # light rate limit
    ip = req.client.host if req.client else "unknown"
    if not allow(ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    body = await req.json()
    try:
        payload = AIRequest(**body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=json.loads(e.json()))

    # seed: if not provided, derive from scene_id+day for mild determinism
    seed = payload.seed
    if seed is None:
        base = f"{payload.scene_id}|{payload.state.get('day')}|{payload.npc}"
        seed = int(hashlib.md5(base.encode("utf-8")).hexdigest(), 16) % (2**31)

    # Call LLM
    try:
        raw = call_gemini(
            npc=payload.npc,
            scene_id=payload.scene_id,
            memory=payload.memory,
            state=payload.state,
            seed=seed,
        )
    except Exception as e:
        print(f"AI 요청 처리 중 에러: {e}")
        # fallback
        raw = default_fallback(payload.npc)

    # sanitize & validate
    res = sanitize_response(raw)

    # Final JSON
    return JSONResponse(
        content=res.model_dump(),
        headers={"Cache-Control":"no-store"}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

