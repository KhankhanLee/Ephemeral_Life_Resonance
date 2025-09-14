# 맥락 기반 AI 대화 시스템
# 스토리 진행도 + 감정/관계도 기반 상황별 대화 선택
import random
from typing import Dict, List, Tuple, Optional

class StoryContext:
    """스토리 진행도 및 상황 컨텍스트"""
    def __init__(self):
        # 스토리 진행도 (0-100)
        self.story_progress = 0
        self.days_left = 30
        
        # 주요 이벤트 플래그
        self.met_coach = False
        self.jisu_confession = False
        self.hayeon_confession = False
        self.ex_reconciliation = False
        
        # 최근 이벤트 히스토리 (최근 3개)
        self.recent_events = []
        
    def add_event(self, event_type: str, character: str = None):
        """최근 이벤트 추가"""
        self.recent_events.append({
            "type": event_type,
            "character": character,
            "day": self.days_left
        })
        # 최근 3개만 유지
        if len(self.recent_events) > 3:
            self.recent_events.pop(0)

class EmotionalState:
    """감정/관계도 상태"""
    def __init__(self):
        # 기본 스탯
        self.stress = 50
        self.resolve = 50
        self.social = 50
        self.study = 50
        self.fitness = 50
        self.money = 50
        
        # 캐릭터별 관계도
        self.relationships = {
            "jisu": 50,
            "hayeon": 50, 
            "ex": 30,
            "coach": 0,
            "mom": 70,
            "sis": 60,
        }
        
        # 현재 감정 상태
        self.mood = "neutral"  # happy, sad, angry, anxious, excited
        self.energy_level = 50  # 0-100
        
    def get_relationship_tier(self, character: str) -> str:
        """관계도 기반 티어 반환"""
        rel = self.relationships.get(character, 50)
        if rel >= 80: return "intimate"
        elif rel >= 60: return "close"
        elif rel >= 40: return "friendly"
        elif rel >= 20: return "neutral"
        else: return "distant"

class SituationAnalyzer:
    """상황 분석 및 AI 대화 결정"""
    
    def __init__(self):
        self.story_context = StoryContext()
        self.emotional_state = EmotionalState()
        
        # 상황별 대화 가중치
        self.situation_weights = {
            "morning_contact": {
                "jisu": {"base": 40, "study_boost": 20, "stress_penalty": -15},
                "hayeon": {"base": 30, "fitness_boost": 15, "social_boost": 10},
                "ex": {"base": 10, "stress_penalty": -20, "resolve_boost": 10}
            },
            "afternoon_contact": {
                "jisu": {"base": 35, "social_boost": 15},
                "hayeon": {"base": 25, "study_boost": 20},
                "ex": {"base": 15, "mood_penalty": -10}
            },
            "night_contact": {
                "jisu": {"base": 30, "intimate_boost": 25},
                "hayeon": {"base": 20, "close_boost": 20},
                "ex": {"base": 25, "distant_penalty": -15}
            },
        }
    
    def analyze_situation(self, time_slot: str) -> Dict[str, float]:
        """현재 상황 분석하여 캐릭터별 대화 확률 계산"""
        
        weights = self.situation_weights.get(time_slot, {})
        probabilities = {}
        
        for character, base_weights in weights.items():
            # 기본 가중치
            weight = base_weights.get("base", 0)
            
            # 스탯 기반 보정
            if "study_boost" in base_weights and self.emotional_state.study > 60:
                weight += base_weights["study_boost"]
            if "fitness_boost" in base_weights and self.emotional_state.fitness > 60:
                weight += base_weights["fitness_boost"]
            if "social_boost" in base_weights and self.emotional_state.social > 60:
                weight += base_weights["social_boost"]
            if "stress_penalty" in base_weights and self.emotional_state.stress > 70:
                weight += base_weights["stress_penalty"]
            if "resolve_boost" in base_weights and self.emotional_state.resolve > 70:
                weight += base_weights["resolve_boost"]
            
            # 관계도 기반 보정
            rel_tier = self.emotional_state.get_relationship_tier(character)
            if rel_tier == "intimate" and "intimate_boost" in base_weights:
                weight += base_weights["intimate_boost"]
            elif rel_tier == "close" and "close_boost" in base_weights:
                weight += base_weights["close_boost"]
            elif rel_tier == "distant" and "distant_penalty" in base_weights:
                weight += base_weights["distant_penalty"]
            
            # 최근 이벤트 기반 보정
            weight += self._get_recent_event_boost(character)
            
            # 스토리 진행도 기반 보정
            weight += self._get_story_progress_boost(character, time_slot)
            
            probabilities[character] = max(0, min(100, weight))
        
        return probabilities
    
    def _get_recent_event_boost(self, character: str) -> float:
        """최근 이벤트 기반 가중치 보정"""
        boost = 0
        for event in self.story_context.recent_events[-2:]:  # 최근 2개 이벤트만
            if event["character"] == character:
                if event["type"] == "confession":
                    boost += 20
                elif event["type"] == "study_session":
                    boost += 15
                elif event["type"] == "argument":
                    boost -= 10
        return boost
    
    def _get_story_progress_boost(self, character: str, time_slot: str) -> float:
        """스토리 진행도 기반 가중치 보정"""
        progress = self.story_context.story_progress
        
        # 스토리 초반: 기본 캐릭터들 우선
        if progress < 30:
            if character in ["jisu", "hayeon"]:
                return 10
            elif character == "ex":
                return -5
        
        # 스토리 중반: 관계도 기반
        elif progress < 70:
            rel_tier = self.emotional_state.get_relationship_tier(character)
            if rel_tier in ["intimate", "close"]:
                return 15
            elif rel_tier == "distant":
                return -10
        
        # 스토리 후반: 고백/결정 시점
        else:
            if character in ["jisu", "hayeon"] and not getattr(self.story_context, f"{character}_confession", False):
                return 25
            elif character == "ex" and not self.story_context.ex_reconciliation:
                return 15
        
        return 0
    
    def select_character(self, time_slot: str) -> Tuple[str, str]:
        """상황에 맞는 캐릭터와 대화 유형 선택"""
        probabilities = self.analyze_situation(time_slot)
        
        # 가중치 기반 랜덤 선택
        total_weight = sum(probabilities.values())
        if total_weight == 0:
            return "jisu", "casual"  # 기본값
        
        rand = random.uniform(0, total_weight)
        current = 0
        
        for character, weight in probabilities.items():
            current += weight
            if rand <= current:
                # 대화 유형 결정
                conversation_type = self._determine_conversation_type(character, time_slot)
                return character, conversation_type
        
        return "jisu", "casual"
    
    def _determine_conversation_type(self, character: str, time_slot: str) -> str:
        """캐릭터와 시간대에 맞는 대화 유형 결정"""
        rel_tier = self.emotional_state.get_relationship_tier(character)
        
        # 시간대별 기본 유형
        base_types = {
            "morning_contact": "casual",
            "afternoon_contact": "study_work", 
            "night_contact": "intimate"
        }
        
        base_type = base_types.get(time_slot, "casual")
        
        # 관계도에 따른 조정
        if rel_tier == "intimate":
            if time_slot == "night_contact":
                return "deep_talk"
            elif time_slot == "morning_contact":
                return "sweet_morning"
        elif rel_tier == "distant":
            return "awkward"
        elif self.emotional_state.stress > 80:
            return "comfort"
        elif self.emotional_state.study > 80:
            return "study_focus"
        
        return base_type

# 전역 인스턴스
situation_analyzer = SituationAnalyzer()

def get_context_aware_ai_call(time_slot: str) -> Tuple[str, str]:
    """맥락을 고려한 AI 대화 호출"""
    character, conversation_type = situation_analyzer.select_character(time_slot)
    return character, conversation_type

def update_story_context(event_type: str, character: str = None):
    """스토리 컨텍스트 업데이트"""
    situation_analyzer.story_context.add_event(event_type, character)

def update_emotional_state(stats: Dict[str, int]):
    """감정 상태 업데이트"""
    for key, value in stats.items():
        if hasattr(situation_analyzer.emotional_state, key):
            setattr(situation_analyzer.emotional_state, key, value)
