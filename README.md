# 찰나의 그 아이 (Ephemeral Life Resonance)

> 입대를 앞둔 대학생의 마지막 방학을 그린 AI 기반 생존 시뮬레이션 게임

![Game Status](https://img.shields.io/badge/Status-Beta%20v0.1.1-green)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Ren'Py](https://img.shields.io/badge/Ren'Py-8.4.1+-red)
![AI](https://img.shields.io/badge/AI-LangGraph%20%2B%20Gemini-orange)

## 🎮 게임 소개

**찰나의 그 아이**는 입대를 앞둔 대학생의 마지막 방학을 그린 AI 기반 생존 시뮬레이션 게임입니다. 플레이어는 복잡한 인간관계, 경제적 압박, 감정적 갈등 속에서 의미 있는 마무리를 찾아야 합니다.

### ✨ 주요 특징

- **🤖 AI 기반 대화**: LangGraph와 Google Gemini를 활용한 자연스러운 NPC 대화
- **📝 약속 시스템**: AI 대화에서 나온 약속을 자동으로 감지하고 추적
- **🎵 위치 기반 음악**: 조용한 공간에서는 음악이 정지되는 현실적인 오디오
- **⚖️ 전략적 밸런스**: 돈, 관계, 스트레스의 균형잡힌 관리
- **🎭 몰입도 높은 UI**: 스탯 수치를 숨겨 진정한 역할극 경험

## 🎯 게임플레이

### 핵심 시스템

#### 📊 6차원 스탯 시스템
- **스트레스**: 일상의 압박과 부담
- **다짐**: 정신적 의지와 결단력
- **관계**: 사회적 연결과 인간관계
- **공부**: 학업 성취와 지식
- **피트니스**: 신체 건강과 체력
- **돈**: 경제적 자원과 생존

#### 🤖 AI 캐릭터들
- **진수**: 오랜 친구, 활발하고 에너지 넘침
- **지수**: 여사친, 코딩에 열정적인 개발자
- **하연**: 여사친, 물리학을 전공하는 똑똑한 친구
- **전애인**: 복잡한 감정의 과거 연인
- **가족**: 엄마, 여동생과의 따뜻한 관계

#### 📅 일일 루프
1. **아침**: 공부/운동/아르바이트/감정정리/AI 대화
2. **낮**: 팀플/체력단련/친구와 점심/감정정리/낮잠
3. **밤**: 복습/독서/가족 대화/휴식/연락하기

### 🎵 혁신적 기능

#### 약속 시스템
- AI 대화에서 자동으로 약속 감지
- HUD에 실시간 약속 목록 표시
- 약속 이행 시 자동 완료 처리

#### 위치 기반 음악
- **조용한 공간**: 도서관, 캠퍼스, 집 → 음악 정지
- **활기찬 공간**: 체육관, 카페, 노래방 → 음악 재생

## 🚀 설치 및 실행

### 필요 조건
- Python 3.12+
- Ren'Py 8.4.1+
- Google Gemini API 키

### 설치 방법

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/ephemeral-life-resonance.git
cd ephemeral-life-resonance
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
```bash
export GOOGLE_API_KEY="your_actual_api_key_here"
```

4. **AI 서버 실행**
```bash
cd game
python server.py
```

5. **게임 실행**
- **오디오 파일 추가** (저작권 문제로 포함되지 않음) 
```bash
# 오디오 파일을 game/audio/ 폴더에 추가하세요
# - title_theme.ogg (메인 메뉴 음악)
# - sub_theme.ogg (기본 게임 음악)
# - peaceful_theme.ogg (평온한 일상)
# - energetic_theme.ogg (활기찬 순간)
# - romantic_theme.ogg (로맨틱한 순간)
```

- Ren'Py Launcher에서 `game` 폴더 열기
- "찰나의 그 아이" 실행

## 🛠️ 기술 스택

### 백엔드
- **Python 3.12+**: 메인 개발 언어
- **FastAPI**: AI 서버 API
- **LangGraph**: AI 대화 시스템
- **Google Gemini**: 대화 생성 AI
- **Pydantic**: 데이터 검증

### 프론트엔드
- **Ren'Py**: 게임 엔진
- **Python**: 게임 로직
- **Ren'Py Script**: 스토리텔링

### AI/ML
- **LangGraph**: 캐릭터별 독립 AI 노드
- **Google Gemini 2.0 Flash**: 대화 생성
- **Context-Aware System**: 게임 상태 기반 캐릭터 선택

## 📁 프로젝트 구조

```
Ephemeral_Life_Resonance/
├── game/
│   ├── script.rpy              # 메인 게임 로직
│   ├── definitions.rpy         # 변수, 함수 정의
│   ├── screens_stats.rpy       # UI/UX 스크린
│   ├── server.py              # AI 서버 (FastAPI)
│   ├── context_aware_system.py # 맥락 인식 시스템
│   ├── audio/                 # 음악 파일
│   ├── images/                # 이미지 리소스
│   └── gui/                   # GUI 리소스
├── requirements.txt           # Python 의존성
└── README.md                 # 프로젝트 문서
```

## 🎨 게임 스크린샷

*게임 스크린샷을 추가하세요*

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👨‍💻 개발자

**Your Name** - [@yourusername](https://github.com/yourusername)

## 🙏 감사의 말

- **Ren'Py Community**: 훌륭한 게임 엔진 제공
- **LangGraph Team**: 혁신적인 AI 프레임워크
- **Google AI**: 강력한 Gemini 모델
- **모든 테스터들**: 귀중한 피드백 제공

## 📞 연락처

프로젝트 링크: [https://github.com/yourusername/ephemeral-life-resonance](https://github.com/yourusername/ephemeral-life-resonance)

---

**찰나의 그 아이** - 인생의 소중한 순간들을 담은 게임 🎮✨
