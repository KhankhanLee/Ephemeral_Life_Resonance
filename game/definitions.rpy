# ===== Characters =====
define m          = Character("[mc_name]", color="#88c0d0")          # 주인공 대사용
define jin        = Character("진수",     color="#b48ead", image="jin")
define ex         = Character("수아",     color="#d08770", image="ex")
define sis        = Character("여동생",   color="#a3be8c", image="sis")
define new_girl_1 = Character("지수",     color="#e78ac3", image="jisu")
define jisu       = new_girl_1  
define coach      = Character("코치",     color="#81a1c1", image="coach")
define n          = Character("",color="#FFF0") #내레이터 
define mom        = Character("엄마",    color="#e88ac2", image="mom")
define new_girl_2 = Character("하연",    color="#e88ac1", image="hayeon")
define hayeon     = new_girl_2 

# ===== Defaults =====
default mc_name = "하진"

default day = 1
default days_left = 30

default stress  = 35
default resolve = 45
default social  = 40
default study   = 40
default fitness = 35
default money   = 80

default met_coach = False
default route_ex = False
default ex_affection = 10
default new_girl_1_affection = 20
default new_girl_2_affection = 20
default counselor_trust = 0

# ===== 지연 이벤트 시스템 =====
default scheduled_events = {}  # {day: [event_list]}
default pending_events = []    # 대기 중인 이벤트들

# ===== 약속 시스템 =====
default promises = []  # [{"id": str, "character": str, "content": str, "day": int, "status": str}]
default promise_id_counter = 0  # 약속 ID 카운터

# 지연 이벤트 관리 함수들
init python:
    def schedule_event(event_type, delay_days, **kwargs):
        """지연 이벤트를 스케줄에 추가"""
        target_day = day + delay_days
        
        if target_day not in scheduled_events:
            scheduled_events[target_day] = []
        
        event = {
            "type": event_type,
            "kwargs": kwargs
        }
        scheduled_events[target_day].append(event)
        
        print(f"이벤트 스케줄 추가:")
        print(f"   - 타입: {event_type}")
        print(f"   - 목표일: Day {target_day} ({delay_days}일 후)")
        print(f"   - 데이터: {kwargs}")
        print(f"   - 현재 Day {target_day} 스케줄: {len(scheduled_events[target_day])}개 이벤트")
    
    def check_scheduled_events():
        """오늘 예정된 이벤트들을 확인하고 실행"""
        print(f"Day {day} 이벤트 체크 시작...")
        print(f"전체 스케줄: {scheduled_events}")
        
        if day in scheduled_events:
            events = scheduled_events[day]
            print(f"Day {day}에 {len(events)}개 이벤트 발견!")
            
            for event in events:
                event_type = event["type"]
                kwargs = event["kwargs"]
                
                print(f"이벤트 실행: {event_type}")
                
                if event_type == "baseball_game":
                    renpy.call("event_baseball_game", **kwargs)
                elif event_type == "jisu_help":
                    renpy.call("event_jisu_help", **kwargs)
                elif event_type == "hayeon_study":
                    renpy.call("event_hayeon_study", **kwargs)
                elif event_type.startswith("promise_"):
                    # 약속 이벤트 처리
                    character = kwargs.get("character", "")
                    content = kwargs.get("content", "")
                    if character and content:
                        print(f"약속 이벤트 실행: {character} - {content}")
                        handle_promise_event(character, content)
                        # 약속 이벤트 라벨 호출
                        renpy.call("event_promise", character=character, content=content)
                    else:
                        print(f"약속 이벤트 데이터 부족: character={character}, content={content}")
                else:
                    print(f"알 수 없는 이벤트 타입: {event_type}")
            
            # 실행된 이벤트 제거
            del scheduled_events[day]
            print(f"Day {day} 이벤트 정리 완료")
        else:
            print(f"Day {day}에 예정된 이벤트 없음")
    
    def has_scheduled_event(event_type, delay_days=None):
        """특정 이벤트가 스케줄되어 있는지 확인"""
        if delay_days:
            target_day = day + delay_days
            if target_day in scheduled_events:
                return any(event["type"] == event_type for event in scheduled_events[target_day])
        else:
            # 모든 미래 날짜에서 확인
            for future_day in scheduled_events:
                if future_day > day:
                    if any(event["type"] == event_type for event in scheduled_events[future_day]):
                        return True
        return False
    
    # ===== 약속 관리 함수들 =====
    def add_promise(character, content, delay_days=0):
        """새로운 약속을 추가"""
        global promise_id_counter
        promise_id_counter += 1
        
        promise = {
            "id": f"promise_{promise_id_counter}",
            "character": character,
            "content": content,
            "day": day + delay_days if delay_days > 0 else day,
            "status": "pending"  # pending, completed, broken
        }
        
        promises.append(promise)
        print(f"약속 추가: {character} - {content} (Day {promise['day']})")
        return promise["id"]
    
    def complete_promise(promise_id):
        """약속을 완료로 표시"""
        for promise in promises:
            if promise["id"] == promise_id:
                promise["status"] = "completed"
                print(f"약속 완료: {promise['character']} - {promise['content']}")
                return True
        return False
    
    def break_promise(promise_id):
        """약속을 깨뜨린 것으로 표시"""
        for promise in promises:
            if promise["id"] == promise_id:
                promise["status"] = "broken"
                print(f"약속 파기: {promise['character']} - {promise['content']}")
                return True
        return False
    
    def get_pending_promises():
        """대기 중인 약속들을 반환"""
        return [p for p in promises if p["status"] == "pending"]
    
    def handle_promise_event(character, content):
        """약속 이벤트 처리"""
        # 해당 캐릭터의 대기 중인 약속 찾기
        for promise in promises:
            if (promise["character"] == character and 
                promise["content"] == content and 
                promise["status"] == "pending"):
                # 약속 완료 처리
                promise["status"] = "completed"
                print(f"약속 이벤트 실행: {character} - {content}")
                return True
        return False
    
    def get_promises_by_character(character):
        """특정 캐릭터의 약속들을 반환"""
        return [p for p in promises if p["character"] == character]
    
    # ===== 음악 관리 함수들 =====
    def play_music(music_name, fade_time=2.0, loop=True):
        """음악을 재생합니다"""
        global current_music
        if current_music != music_name:
            renpy.music.play(music_name, fadein=fade_time, loop=loop)
            current_music = music_name
            print(f"🎵 음악 재생: {music_name}")
    
    def stop_music(fade_time=2.0):
        """음악을 정지합니다"""
        global current_music
        renpy.music.stop(fadeout=fade_time)
        current_music = None
        print(f"음악 정지")
    
    def fade_music(music_name, fade_time=2.0, loop=True):
        """음악을 페이드로 전환합니다"""
        global current_music
        if current_music != music_name:
            renpy.music.play(music_name, fadein=fade_time, loop=loop)
            current_music = music_name
            print(f"🎵 음악 전환: {music_name}")
    
    def toggle_music():
        """음악을 켜고 끕니다"""
        global current_music
        if current_music:
            stop_music(1.0)
        else:
            play_music(sub_music, fade_time=1.0)
    
    # 음악 토글 액션
    class ToggleMusic(Action):
        def __call__(self):
            toggle_music()
            return True
    
    def get_mood_music(mood):
        """감정에 따른 음악 선택"""
        mood_music = {
            "peaceful": music_peaceful,
            "melancholy": music_melancholy,
            "energetic": music_energetic,
            "romantic": music_romantic,
            "dramatic": music_dramatic,
            "study": music_study,
            "social": music_social,
            "family": music_family,
            "ai_chat": music_ai_chat,
            "ending": music_ending
        }
        return mood_music.get(mood, music_peaceful)
    
    def play_mood_music(mood, fade_time=2.0):
        """감정에 맞는 음악을 재생"""
        global current_mood
        music_file = get_mood_music(mood)
        if current_mood != mood:
            fade_music(music_file, fade_time)
            current_mood = mood
            print(f"🎵 감정 음악: {mood} -> {music_file}")
    
    def analyze_emotional_state():
        """현재 게임 상태를 분석해서 감정 결정"""
        # 스트레스가 높으면 우울한 음악
        if stress >= 70:
            return "melancholy"
        # 관계도가 높고 AI 대화 중이면 로맨틱
        elif social >= 60 and current_mood == "ai_chat":
            return "romantic"
        # 공부 중이면 공부 음악
        elif study >= 50:
            return "study"
        # 피트니스가 높으면 활기찬 음악
        elif fitness >= 60:
            return "energetic"
        # 가족과 대화 중이면 가족 음악
        elif current_mood == "family":
            return "family"
        # 기본적으로 평온한 음악
        else:
            return "peaceful"
    
    def update_location_music(location):
        """위치에 따른 음악 제어"""
        global current_location
        current_location = location
        
        # 조용한 공간에서는 음악 정지
        if location in quiet_places:
            if current_music:
                stop_music(1.0)
                print(f"조용한 공간: {location} - 음악 정지")
        else:
            # 조용하지 않은 공간에서는 감정에 맞는 음악 재생
            mood = analyze_emotional_state()
            play_mood_music(mood, fade_time=1.0)
            print(f"🎵 공간 변경: {location} - {mood} 음악 재생")
    
    def is_quiet_place(location):
        """해당 위치가 조용한 공간인지 확인"""
        return location in quiet_places

default RANDOM_EVENT_CHANCE = 35  # 쓰고 있으니 기본값 필요

# 화면을 꽉 채우는 커버 스케일(중앙 기준)
image bg campus  = Transform("images/bg_campus.png",  fit="cover", xalign=0.5, yalign=0.5)

# ===== 캐릭터 위치 정의 =====
transform pos_left:
    xalign 0.2
    yalign 1.0

transform pos_right:
    xalign 0.8
    yalign 1.0

image bg home    = Transform("images/bg_home.png",    fit="cover", xalign=0.5, yalign=0.5)
image bg room    = Transform("images/bg_home.png",    fit="cover", xalign=0.5, yalign=0.5)
image bg cafe    = Transform("images/bg_cafe.png",    fit="cover", xalign=0.5, yalign=0.5)
image bg gym     = Transform("images/bg_gym.png",     fit="cover", xalign=0.5, yalign=0.5)
image bg karaoke = Transform("images/bg_karaoke.png", fit="cover", xalign=0.5, yalign=0.5)
image bg library = Transform("images/bg_library.png", fit="cover", xalign=0.5, yalign=0.5)


# ===== Sprites =====
# MC
image mc_neutral = "images/char/mc/mc_neutral.png"
image mc_happy   = "images/char/mc/mc_happy.png"
image mc_sad     = "images/char/mc/mc_sad.png"
image mc_think   = "images/char/mc/mc_think.png"
image mc_angry   = "images/char/mc/mc_angry.png"

# Jisu (new_girl_1)
image jisu_neutral = "images/char/jisu/jisu_neutral.png"
image jisu_happy   = "images/char/jisu/jisu_happy.png"
image jisu_sad     = "images/char/jisu/jisu_sad.png"
image jisu_think   = "images/char/jisu/jisu_think.png"

# Hayeon (new_girl_2)
image hayeon_neutral = "images/char/hayeon/hayeon_neutral.png"
image hayeon_happy   = "images/char/hayeon/hayeon_happy.png"
image hayeon_sad     = "images/char/hayeon/hayeon_sad.png"
image hayeon_think   = "images/char/hayeon/hayeon_think.png"
image hayeon_angry   = "images/char/hayeon/hayeon_angry.png"
image hayeon_sexy    = "images/char/hayeon/hayeon_sexy.png"

# Ex (Sua)
image ex_neutral = "images/char/ex/ex_neutral.png"
image ex_happy   = "images/char/ex/ex_happy.png"
image ex_sad     = "images/char/ex/ex_sad.png"
image ex_think   = "images/char/ex/ex_think.png"
image ex_angry   = "images/char/ex/ex_angry.png"
image ex_sexy    = "images/char/ex/ex_sexy.png"

# Sister
image sis_neutral = "images/char/sis/sis_neutral.png"
image sis_happy   = "images/char/sis/sis_happy.png"
image sis_sad     = "images/char/sis/sis_sad.png"
image sis_think   = "images/char/sis/sis_think.png"
image sis_angry   = "images/char/sis/sis_angry.png"

# Coach
image coach_neutral = "images/char/coach/coach_neutral.png"
image coach_happy   = "images/char/coach/coach_happy.png"
image coach_sad     = "images/char/coach/coach_sad.png"
image coach_think   = "images/char/coach/coach_think.png"
image coach_angry   = "images/char/coach/coach_angry.png"

# Jin(friend)
image jin_neutral = "images/char/jin/jin_neutral.png"
image jin_happy = "images/char/jin/jin_happy.png"
image jin_sad = "images/char/jin/jin_sad.png"
image jin_think = "images/char/jin/jin_think.png"
image jin_angry = "images/char/jin/jin_angry.png"

# Mom
image mom_neutral = "images/char/mom/mom_neutral.png"
image mom_happy = "images/char/mom/mom_happy.png"
image mom_sad = "images/char/mom/mom_sad.png"
image mom_think = "images/char/mom/mom_think.png"
image mom_angry = "images/char/mom/mom_angry.png"

# ===== Positions =====
transform pos_left:
    xalign 0.2
    yalign 1.0

transform pos_right:
    xalign 0.8
    yalign 1.0

# ===== 투명 배경 처리 Transform =====
transform transparent_bg:
    # 투명 배경을 위한 블렌드 모드
    blend "alpha"
    # 배경 제거를 위한 마스크 처리
    matrixcolor TintMatrix("#ffffff")

# ===== 배경 제거를 위한 고급 Transform =====
transform remove_bg:
    # 알파 채널을 사용한 투명 처리
    blend "alpha"
    # 색상 마스킹으로 배경 제거
    matrixcolor TintMatrix("#ffffff")
    # 투명도 조절
    alpha 1.0

# ===== 캐릭터 전용 배경 제거 Transform =====
transform char_no_bg:
    # 캐릭터 이미지의 배경을 제거
    blend "alpha"
    # 투명도 유지
    alpha 1.0

# ===== 간단한 배경 제거 Transform =====
transform no_bg:
    # 투명 배경 처리
    blend "alpha"
    alpha 1.0

# ===== 캐릭터별 배경 제거 Transform =====
transform mom_no_bg:
    blend "alpha"
    alpha 1.0

transform sis_no_bg:
    blend "alpha"
    alpha 1.0

transform hayeon_no_bg:
    blend "alpha"
    alpha 1.0

# ===== 배경 제거 Transition =====
define no_bg_transition = Dissolve(0.1)

# 옵션: 기본 음악 볼륨(0.0~1.0)
define config.default_music_volume = 0.6

# ===== 음악 시스템 =====
# 메인 메뉴 음악
define main_menu_music = "audio/title_theme.ogg"

# 서브 음악 (기본 게임 음악)
define sub_music = "audio/sub_theme.ogg"

# 감정별 음악
define music_peaceful = "audio/peaceful_theme.ogg"      # 평온한 일상
define music_melancholy = "audio/sub_theme.ogg"    # 우울/그리움 
define music_energetic = "audio/energetic_theme.ogg"     # 활기찬 순간 
define music_romantic = "audio/romantic_theme.ogg"      # 로맨틱한 순간 
define music_dramatic = "audio/sub_theme.ogg"      # 드라마틱한 순간 

# 상황별 음악
define music_study = "audio/study_theme.ogg"         # 공부 시간
define music_social = "audio/social_theme.ogg"        # 친구들과의 만남
define music_family = "audio/family_theme.ogg"        # 가족과의 대화
define music_ai_chat = "audio/ai_chat_theme.ogg"       # AI 대화
define music_ending = "audio/sub_theme.ogg"        # 엔딩

# 음악 상태 관리
default current_music = None
default music_fade_time = 2.0
default current_mood = "peaceful"  # 현재 감정 상태

# 조용한 공간 정의
default quiet_places = ["library", "campus", "home"]  # 음악이 나오지 않는 공간들
default current_location = "campus"  # 현재 위치

# ===== 돈 관리 시스템 =====
default daily_expenses = 15  # 하루 생활비
default money_warning_threshold = 50  # 돈 부족 경고 임계값
# 메인 음악 제목: 영혼의 여행
# 서브 음악 제목: 한 때 그 아인

init -100 python:
    import json, ssl, urllib.request, urllib.error, urllib.parse
    import re

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def random_(n=100):
        import random
        return random.randint(1, n)

    def choose_(arr):
        import random
        return random.choice(arr)

    # 질문은행: id, 질문문구(text), 기본표정(face), 정답카테고리(cat), 키워드(자유입력용), 해설(tip) :지수의 질문 (코딩)
    JISU_QS = [dict(id="indexerror", text="파이썬에서 list[index] 하다 IndexError 떠… off-by-one 때문인가?",
                face="sad",   cat="bounds", keywords=[r"index", r"범위", r"len", r"range", r"0부터"], 
                tip="인덱스는 0부터 len(list)-1. 접근 전 길이/경계 체크!"),
        dict(id="bfsdfs", text="DFS/BFS 방문 순서가 매번 달라져… visited 초기화 어디서 해?",
                face="think", cat="bounds", keywords=[r"visited", r"초기화", r"reset", r"queue", r"stack"],
                tip="각 케이스마다 visited를 올바른 스코프에서 초기화해."),
        dict(id="two_pointer", text="정렬+투포인터로 합 K 찾는 거 중복 처리 어떻게 해?",
                face="think", cat="algo", keywords=[r"정렬", r"두 포인터", r"중복", r"left", r"right"],
                tip="정렬 후 left/right 이동 규칙과 중복 스킵 조건을 분리해."),
        dict(id="cors", text="fetch 했는데 CORS 막혀… 프론트에서 해결 가능해?",
                face="sad",   cat="env", keywords=[r"cors", r"origin", r"header", r"proxy", r"preflight"],
                tip="서버에서 허용 헤더/오리진 설정 or dev 프록시 사용."),
        dict(id="git_merge", text="깃 충돌 났어. <<<<<<< 이런 마커 보이는데 머지 순서가 헷갈려…",
                face="sad",   cat="env", keywords=[r"merge", r"rebase", r"conflict", r"<<<<<<<", r">>>>>>>"],
                tip="충돌난 파일을 열어 우리/그들 블록을 수동 정리 후 add/commit."),
        dict(id="npe", text="자바에서 NPE 나는데, 생성자에서 리스트 초기화 안 해서 그런가?",
                face="neutral", cat="bounds", keywords=[r"null", r"생성자", r"init", r"new", r"Optional"],
                tip="필드 null 초기화/생성자 new 확인. 널가드/Optional 고려."),
        dict(id="sql_join", text="학생–수강 조인했더니 중복 폭발… JOIN이랑 GROUP BY 뭐가 맞아?",
                face="think", cat="algo", keywords=[r"join", r"group by", r"distinct", r"count", r"fk"],
                tip="기댓값에 맞는 JOIN(내부/외부) 선택, 집계는 GROUP BY+DISTINCT."),
        dict(id="regex_email", text="정규식으로 이메일만 뽑고 싶은데 공백 끼면 깨져… 패턴 도움!",
                face="think", cat="algo", keywords=[r"regex", r"\w", r"+", r"@", r"\."],
                tip=r"양 끝 공백 제거 후 패턴 적용. 예: r'^[^\s@]+@[^\s@]+\.[^\s@]+$'"),]
    
    # 질문은행: id, 질문문구(text), 기본표정(face), 정답카테고리(cat), 키워드(자유입력용), 해설(tip) :하연의 질문 (물리)
    HAYEON_QS = [
        dict(id="newton3", text="책상을 밀었는데도 왜 내가 뒤로 밀려? 힘은 어디서 생겨?",
            face="think", cat="force", keywords=[r"작용", r"반작용", r"뉴턴", r"3법칙", r"상호작용"],
            tip="뉴턴 제3법칙: 내가 책상에 힘 → 책상도 같은 크기 반대 방향 힘을 나에게."),
    
        dict(id="freefall", text="진공에서 떨어뜨리면 깃털도 쇳덩이랑 같이 떨어진다고?",
            face="surprise", cat="motion", keywords=[r"자유낙하", r"질량", r"가속도", r"중력"],
            tip="공기저항 없으면 모든 물체는 g(9.8m/s²)로 같은 가속도로 떨어져."),
    
        dict(id="circular", text="원운동 할 때 안쪽으로 힘이 작용한다는데… 원심력은 가짜야?",
            face="think", cat="motion", keywords=[r"원운동", r"구심력", r"원심력", r"가속도"],
            tip="실제 힘은 구심력(안쪽). 원심력은 회전계에서 보이는 가상힘."),
    
        dict(id="voltage", text="전압이 높으면 전류가 무조건 커져? 아니면 저항이랑도 관련 있어?",
            face="neutral", cat="electric", keywords=[r"전압", r"전류", r"저항", r"옴의 법칙"],
            tip="옴의 법칙 V=IR. 전류는 전압뿐 아니라 저항에도 좌우됨."),
    
        dict(id="doppler", text="구급차가 가까워질 때 소리가 왜 더 높게 들려?",
            face="surprise", cat="wave", keywords=[r"도플러", r"파동", r"주파수", r"파장"],
            tip="파원 가까워질 때 파장이 압축 → 주파수↑ → 높은 음. 멀어지면 반대."),
    
        dict(id="entropy", text="엔트로피는 왜 항상 증가한다는 거야?",
            face="sad", cat="thermo", keywords=[r"엔트로피", r"열역학", r"무질서", r"자연 과정"],
            tip="고립계에서 자연스러운 과정은 무질서 증가 → 엔트로피 증가."),
    
        dict(id="relativity", text="빛보다 빠르게 움직이면 시간이 거꾸로 간다고?",
            face="think", cat="relativity", keywords=[r"상대성", r"광속", r"시간 지연", r"원인"],
            tip="빛보다 빠른 속도는 불가능. 광속 근처에서만 시간 지연 효과가 발생."),
    
        dict(id="quantum", text="전자 위치는 왜 확실히 알 수 없는 거야?",
            face="neutral", cat="quantum", keywords=[r"불확정성", r"하이젠베르크", r"위치", r"운동량"],
            tip="불확정성 원리: 위치·운동량은 동시에 정확히 측정 불가."),]
    
    # 코치 질문 은행: id, 질문문구(text), 기본표정(face), 정답카테고리(cat), 키워드(자유입력용), 해설(tip)
    COACH_QS = [
        dict(id="mental", text="네가 생각하는 마음을 정리하는 방법은?", face="think", cat="mental", keywords=[r"마음", r"정리", r"관리", r"부정적", r"긍정적" ], tip= "마음을 정리하는 방법은 다양해. 책을 보고 정리하는 방법도 있고, 일기를 쓰는 방법도 있어."),
    ]

    # 자유 입력 채점 (키워드 히트 수로 0/1/2) 
    def eval_text_answer(qid, answer, QS):
        ans = (answer or "").lower()
        for q in QS:
            if q["id"] == qid:
                hits = sum(1 for kw in q["keywords"] if re.search(kw, ans))
                score = 2 if hits >= 2 else (1 if hits >= 1 else 0)
                return score, q["tip"], q["cat"]
        return 0, "음… 다른 관점으로도 생각해보자!", "algo"

    # 선택지 채점 (카테고리 일치 여부)
    def eval_choice_answer(qid, picked_cat, QS):
        for q in QS:
            if q["id"] == qid:
                score = 2 if picked_cat == q["cat"] else (1 if picked_cat in ("bounds","algo","env") else 0)
                return score, q["tip"], picked_cat
    
    # 점수→효과
    def apply_effects_by_score(score):
        if score >= 2:   # 잘 답변
            return dict(social=+2, newgirl=+3, resolve=+1, stress=-1)
        elif score == 1: # 반쯤 맞춤
            return dict(social=+1, newgirl=+1)
        else:            # 빗맞춤
            return dict(stress=+1, newgirl=-1)

    # 게임 상태를 한 번에 모아 전달
    def get_game_state():
        return dict(
            mc_name=mc_name, day=day, days_left=days_left,
            stress=stress, resolve=resolve, social=social,
            study=study, fitness=fitness, money=money,
            route_ex=route_ex, ex_affection=ex_affection,
            jisu_affection=new_girl_1_affection,
            counselor_trust=counselor_trust,
            hayeon_affection=new_girl_2_affection,
        )

    # HTTP POST (requests 라이브러리 사용)
    def post_json(url, payload, headers=None, timeout=20):
        if headers is None: headers = {}
        try:
            import requests
            response = requests.post(
                url, 
                json=payload, 
                headers={"Content-Type": "application/json", **headers},
                timeout=timeout,
                verify=True  # SSL 검증 활성화
            )
            response.raise_for_status()  # HTTP 오류 시 예외 발생
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP 요청 오류: {e}")
            return {"error": f"연결 실패: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return {"error": f"응답 파싱 실패: {str(e)}"}
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return {"error": f"알 수 없는 오류: {str(e)}"}

    # LLM 에이전트 래퍼
    class DialogueAI(object):
        def __init__(self, endpoint, api_key=None):
            self.endpoint = endpoint
            self.api_key = api_key

        def ask(self, npc, scene_id, memory, state, conversation_type="casual"):
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "npc": npc,            # "jisu" / "ex" / "mom" ...
                "scene_id": scene_id,  #구분자 붙이기 좋게
                "memory": memory,      # 최근 대화 몇 턴
                "state": state,        # 스탯/플래그
                "style": "ko-game",    # 톤 힌트
                "conversation_type": conversation_type  # 대화 유형
            }
            return post_json(self.endpoint, payload, headers=headers)

    # 인스턴스 만들기 
    #ai = DialogueAI(endpoint="https://ren-py-chat-dialogue-ai-production.up.railway.app/ai") 
    ai = DialogueAI(endpoint="http://127.0.0.1:8000/ai") 
    ai_memory = []   # 최근 대화 로그 저장 (세이브/로드에 같이 저장됨)
