label splashscreen:
    return

label before_main_menu:
    # 메인 메뉴 음악 재생
    $ play_music(main_menu_music, fade_time=1.0)
    return

label start:
    scene bg campus
    show screen hud

    # 게임 시작 시 서브 음악으로 전환
    $ fade_music(sub_music, fade_time=3.0)
    
    $ mc_name = renpy.input("주인공 이름은? (미입력 시 기본값:하진)", length=8) or "하진"
    $ mc_name = mc_name.strip()
    show mc_think at left
    n "서울시 동작구. 한 여름의 캠퍼스."
    n "입대 영장을 받은 [mc_name]은(는) 입대 전 마지막 방학을 보내고 있다."
    n "숭실대학교 전자정보공학부 2학년 [mc_name] 은(는) 다사다난한 나날들을 보내고 있다."
    n "많은 힘듦이 있었지만 그럼에도 불구하고 여러 프로젝트들을 진행하고 있으며 진로, 미래에 대한 고민을 하고있다."
    m "...드디어 끝나가네. 이 여름방학도..."
    m "'입대를 앞두고 많은 일들이 있었고 많이 힘들었지만, 그래도 마무리를 잘 해야지...'"
    n "입대가 가까워지며 [mc_name]의 마음은 복잡했다."
    n "그러나 그럼에도 불구하고 의미있는 마무리를 하고 싶어한다."
    
    # 튜토리얼/초기 선택
    n "입대 전 목표를 정하자."
    menu:
        "마음을 단단히. 감정 정리 & 다짐":
            $ resolve += 10
            $ met_coach = True
            jump meet_coach_first
        "현실 챙기기. 공부/돈/운동":
            $ study += 5
            $ money += 10
            $ fitness += 5
            jump day_loop

label meet_coach_first:
    scene bg room
    show coach_neutral at left
    coach "오늘부터 짧게라도 마음을 정리하는 시간을 가져보자."
    coach "'무엇을 통제할 수 있고, 무엇을 놓아줘야 하는가'를 매일 점검해."
    coach "감정적으로 힘든 부분들도 많이 있었겠지만, 오늘부터 관리를 잘 해나가자!"
    $ mental_answer = renpy.input("네가 생각하는 마음을 정리하는 방법은?", length=80)
    $ score, tip, cat = eval_text_answer("mental", mental_answer, COACH_QS)
    $ mental_answer = mental_answer.strip()
    $ mental_answer = mental_answer.replace("\n", " ")
    $ mental_answer = mental_answer.replace("\r", " ")
    $ mental_answer = mental_answer.replace("\t", " ")
    $ mental_answer = mental_answer.replace("  ", " ")
    coach "{i}[tip]{/i}"

    $ counselor_trust += 1
    hide coach_neutral
    jump day_loop

# ====== DAY LOOP ======
label day_loop:
    if days_left <= 0:
        jump check_endings

    # 아침 슬롯
    call morning_slot
    # 낮 슬롯
    call afternoon_slot
    # 밤 슬롯
    call night_slot

    # 지연 이벤트 체크 (하루 마감 전)
    $ check_scheduled_events()
    
    # 랜덤 이벤트(하루 마감 전)
    $ roll = random_(100)
    if roll <= RANDOM_EVENT_CHANCE:
        call random_event

    # 밤 휴식 효과 (약간의 자연 회복)
    $ stress = clamp(stress - 1, 0, 100)
    
    # 일일 생활비 차감
    $ money = clamp(money - daily_expenses, 0, 999)
    if money < money_warning_threshold:
        n "돈이 부족해지고 있다... 아르바이트를 더 해야 할 것 같다."

    # 시간 경과
    $ day += 1
    $ days_left -= 1

    jump day_loop

# ====== SLOT MENUS ======
label morning_slot:
    # 아침 시간대 약속 체크
    python:
        morning_promises = [e for d, events in scheduled_events.items() if d == day 
                            for e in events if e.get("kwargs", {}).get("time_slot") == "morning"]
    
    # 약속이 있으면 약속 이벤트만 실행하고 일반 메뉴 건너뛰기
    if morning_promises:
        python:
            for event in morning_promises:
                character = event["kwargs"]["character"]
                content = event["kwargs"]["content"]
                print(f"아침 약속 실행: {character} - {content}")
        call event_promise_with_ai(morning_promises[0]["kwargs"]["character"], morning_promises[0]["kwargs"]["content"], "morning_promise")
        
        # 약속 실행 후 이벤트 제거
        python:
            for event in morning_promises:
                if day in scheduled_events:
                    if event in scheduled_events[day]:
                        scheduled_events[day].remove(event)
                    if not scheduled_events[day]:  # 리스트가 비었으면 키 삭제
                        del scheduled_events[day]
        return
    
    # 약속이 없을 때만 일반 메뉴 실행
    scene bg home
    n "아침. 무엇을 할까?"
    $ t= random_(100)
    if t<=60:
        menu:
            "도서관: 공부 , 스트레스":
                scene bg library
                show mc_think at left
                $ study = clamp(study + 3, 0, 100)
                $ stress = clamp(stress + 1, 0, 100)
                $ update_location_music("library")  # 도서관은 조용한 공간
                m "아침부터 집중 잘 됐다."
                hide mc_think
            "조깅: 피트니스 , 스트레스":
                scene bg gym
                show mc_happy at left
                $ fitness = clamp(fitness + 3, 0, 100)
                $ stress = clamp(stress - 2, 0, 100)
                $ update_location_music("gym")  # 체육관은 음악 재생
                m "땀 좀 흘리니 머리가 맑아졌다."
                hide mc_happy
            "아르바이트: 돈 , 스트레스":
                scene bg cafe
                show mc_neutral at left
                $ money = clamp(money + 8, 0, 999)  
                $ stress = clamp(stress + 2, 0, 100)
                $ update_location_music("cafe")  # 카페는 음악 재생
                m "바쁜 아침. 그래도 벌 땐 벌어야지."
                hide mc_neutral
            "감정정리(코치): 다짐 , 스트레스":
                show coach_happy at left
                $ resolve = clamp(resolve + 4, 0, 100)
                $ stress = clamp(stress - 1, 0, 100)
                $ counselor_trust += 1
                $ met_coach = True
                coach "어제의 감정에서 오늘로 가져올 건 무엇일까?"
                hide coach_happy
            "연락하기 (확률 이벤트)":
                jump morning_contact_roll
        return
    elif t<=75: # 15% 확률 AI 대화 (맥락 기반)
        scene bg campus
        python:
            # 맥락 기반 AI 캐릭터 선택
            from context_aware_system import get_context_aware_ai_call, update_emotional_state
            
            # 현재 스탯 상태 업데이트
            current_stats = {
                "stress": stress,
                "resolve": resolve, 
                "social": social,
                "study": study,
                "fitness": fitness,
                "money": money,
            }
            update_emotional_state(current_stats)
            
            # 맥락을 고려한 캐릭터 선택
            selected_character, conversation_type = get_context_aware_ai_call("morning_contact")
            renpy.log(f"== AI: {selected_character} / morning_contact / {conversation_type} ==")
        
        # AI 대화 시 위치에 따른 음악 제어
        $ update_location_music("campus")  # 캠퍼스는 조용한 공간
        call ai_turn(selected_character, "morning_contact", side="left", conversation_type=conversation_type)
        return
    elif t<=85: # 10% 확률 AI 대화 (맥락 기반)
        scene bg library
        python:
            from context_aware_system import get_context_aware_ai_call, update_emotional_state
            
            current_stats = {
                "stress": stress,
                "resolve": resolve,
                "social": social, 
                "study": study,
                "fitness": fitness,
                "money": money,
            }
            update_emotional_state(current_stats)
            
            selected_character, conversation_type = get_context_aware_ai_call("morning_contact")
            renpy.log(f"== AI: {selected_character} / morning_contact / {conversation_type} ==")
        
        # 도서관은 조용한 공간
        $ update_location_music("library")
        call ai_turn(selected_character, "morning_contact", side="left", conversation_type=conversation_type)
        return
    else: # 15% 확률 AI 대화 (맥락 기반)
        scene bg cafe
        python:
            from context_aware_system import get_context_aware_ai_call, update_emotional_state
            
            current_stats = {
                "stress": stress,
                "resolve": resolve,
                "social": social,
                "study": study, 
                "fitness": fitness,
                "money": money,
            }
            update_emotional_state(current_stats)
            
            selected_character, conversation_type = get_context_aware_ai_call("morning_contact")
            renpy.log(f"== AI: {selected_character} / morning_contact / {conversation_type} ==")
        
        # 카페는 음악 재생
        $ update_location_music("cafe")
        call ai_turn(selected_character, "morning_contact", side="left", conversation_type=conversation_type)
        
#연락하기 (확률 이벤트)
label morning_contact_roll:
    # 1~100 사이 주사위
    $ r = random_(100)
    if r <= 30:
        # 친구 진수: 빠른 답장 (30%)
        scene bg cafe
        show jin_happy at right
        jin "피방 ㄱㄱ"
        $ social = clamp(social + 2, 0, 100)  
        $ stress = clamp(stress - 1, 0, 100)
        m "뭐, 짜피 할 것도 없고. 그려그려. ㄱㄱ"
        jin "ㄱㄱ"
        hide jin_happy
    
    elif r<=45:
        # 여사친 지수: 쾌활하고 밝은 연락이 온다 (15%)
        scene bg campus
        #question 하나 뽑기
        $ _q = choose_(JISU_QS)
        $ _face = _q["face"]
        $ _tag = "jisu_" + _face
        show expression _tag at left
        new_girl_1 "[mc_name]! 너 오늘 시간 돼? 나 코딩하다가 모르는게 있어서 ㅠㅠ 나 도와줄 수 있어?"
        menu:
            "수락한다":
                $ money = clamp(money -10, 0, 999)  # 5 → 10으로 증가
                $ social = clamp(social +3, 0, 100)  # 7 → 3으로 감소
                $ new_girl_1_affection +=1
                m "응, 그래 내가 도와줄게!"
                new_girl_1 "음..."
                new_girl_1 "[_q['text']]"
                # 답변 방식 선택 (자유입력 or 카테고리 선택)
                menu:
                    "직접 답변 입력하기":
                        $ user_ans = renpy.input("네가 생각하는 해결책은? (핵심 키워드 위주로 적어줘)", length=80)
                        $ score, tip, cat = eval_text_answer(_q["id"], user_ans, JISU_QS)
                    "선택지로 답하기(요점만)":
                        menu:
                            "경계/초기화/예외(배열 범위, visited, null 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "bounds", JISU_QS)
                            "알고리즘/자료구조(정렬, 두 포인터, JOIN/정규식 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "algo", JISU_QS)
                            "환경/설정(CORS, 깃 충돌, 빌드/경로 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "env", JISU_QS)
                # 점수에 따른 반응/스탯 변화
                if score >= 2:
                    hide all
                    hide jisu_neutral
                    hide jisu_sad
                    hide jisu_think
                    show jisu_happy at left with dissolve
                    new_girl_1 "오… 그거였넹! 확실히 이해됐엉. 고마웡!!"
                elif score == 1:
                    hide all
                    hide jisu_happy
                    hide jisu_sad
                    hide jisu_think
                    show jisu_neutral at left with dissolve
                    new_girl_1 "힌트가 좀 감 잡히는 듯! 방향 잡아볼게."
                else:
                    hide all
                    hide jisu_happy
                    hide jisu_neutral
                    hide jisu_think
                    show jisu_sad at left with dissolve
                    new_girl_1 "흐음… 아직 잘 모르겠다. 같이 더 보자!"
                # 해설 한 줄 (내레이션으로)
                n "{i}[tip]{/i}"
                # 효과 적용
                $ _eff = apply_effects_by_score(score)
                $ social = clamp(social + _eff.get("social", 0), 0, 100)
                $ resolve = clamp(resolve + _eff.get("resolve", 0), 0, 100)
                $ stress = clamp(stress + _eff.get("stress", 0), 0, 100)
                $ new_girl_1_affection = clamp(new_girl_1_affection + _eff.get("newgirl", 0), 0, 100)
                return
            "거절한다":
                show mc_sad at right
                hide expression _tag
                show jisu_think at left
                $ money = clamp(money +0, 0, 999)
                $ social = clamp(social +0, 0, 100)
                m "미안, 내가 바빠서..."
                new_girl_1 "웅... 그래? 그럼 언제 시간 돼? 시간 맞춰볼까?"
                hide mc_sad
                hide jisu_think
                menu:
                    "수락한다":
                        show mc_think at right
                        show jisu_happy at left with dissolve
                        $ money = clamp(money -5, 0, 999)
                        $ social = clamp(social +3, 0, 100)
                        $ new_girl_1_affection +=1
                        m "뭐, 나 내일은 시간 되는데. 내일 점심 어때?"
                        new_girl_1 "웅 조아! 그럼 내일 점심에 보자~!"
                        $ schedule_event("jisu_help", 1, help_type="coding")
                        $ add_promise("지수", "코딩 도움주기", 1)
                        hide mc_think
                        hide jisu_happy
                    "거절한다":
                        show mc_sad at right
                        show jisu_sad at left with dissolve
                        $ money = clamp(money +0, 0, 999)
                        $ social = clamp(social +0, 0, 100)
                        $ new_girl_1_affection -=7
                        m "미안, 내가 요즘 바쁘고 힘든 일이 있어서 못 도와줄거 같아."
                        new_girl_1 "음... 그래 그럼 어쩔 수 없지 ㅠㅠ 알겠어."
                        hide mc_sad
                        hide jisu_sad

    elif r <= 55:
        # 가족: 안부 통화 (10%)
        scene bg home
        show mom_neutral at left         
        $ update_location_music("home")  # 집은 조용한 공간
        mom "아침은 먹고 다니니? 뭔 일 없지? 좀 글고 일찍 자고!"
        $ social = clamp(social + 1, 0, 100)  # 2 → 1로 감소
        $ resolve = clamp(resolve + 1, 0, 100)
        m "네 엄마. 그럴게요."
        hide mom_neutral

    elif r <= 65:
        # 하연 (새로운 여사친2): 물리와 관련된 질문을 한다.
        scene bg campus
        show hayeon_sexy at left         
        new_girl_2 "안녕! [mc_name]! 오늘 바빠?"
        menu:
            "안 바빠":
                $ money = clamp(money -10, 0, 999)  # 5 → 10으로 증가
                $ social = clamp(social +3, 0, 100)  # 7 → 3으로 감소
                new_girl_2 "나랑 같이 물리 공부할래? 곧 시험 있는데 도와줄래?"
                menu:
                    "수락한다":
                        new_girl_2"어디서 공부할까?"
                        menu:
                            "도서관":
                                scene bg library
                                $ _q = choose_(HAYEON_QS)
                                $ _face = _q["face"]
                                $ _tag = "new_girl_2" + _face
                                show expression _tag at left
                                new_girl_2 "[_q['text']]"
                                menu:
                                    "직접 답변 입력하기":
                                        $ user_ans = renpy.input("네가 생각하는 답은? (핵심 키워드 위주로 적어줘)", length=80)
                                        $ score, tip, cat = eval_text_answer(_q["id"], user_ans, HAYEON_QS)
                                    "선택지로 답하기":
                                        menu:
                                            "물리/역학 (힘, 운동량, 운동방정식 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "physics", HAYEON_QS)
                                            "전자기학 (전기, 자기, 전자기 장 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "electronics", HAYEON_QS)
                                            "통계/확률 (통계, 확률, 통계학 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "statistics", HAYEON_QS)
                                            "열역학 (열, 열기관, 열역학 제1법칙 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "thermodynamics", HAYEON_QS)
                                            "기타 (기타 물리 문제 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "etc", HAYEON_QS)
                            "카페":
                                scene bg cafe
                                $ _q = choose_(HAYEON_QS)
                                $ _face = _q["face"]
                                $ _tag = "new_girl_2" + _face
                                show expression _tag at left
                                new_girl_2 "[_q['text']]"
                                menu:
                                    "직접 답변 입력하기":
                                        $ user_ans = renpy.input("네가 생각하는 답은? (핵심 키워드 위주로 적어줘)", length=80)
                                        $ score, tip, cat = eval_text_answer(_q["id"], user_ans, HAYEON_QS)
                                    "선택지로 답하기":
                                        menu:
                                            "물리/역학 (힘, 운동량, 운동방정식 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "physics", HAYEON_QS)
                                            "전자기학 (전기, 자기, 전자기 장 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "electronics", HAYEON_QS)
                                            "통계/확률 (통계, 확률, 통계학 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "statistics", HAYEON_QS)
                                            "열역학 (열, 열기관, 열역학 제1법칙 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "thermodynamics", HAYEON_QS)
                                            "기타 (기타 물리 문제 등)":
                                                $ score, tip, cat = eval_choice_answer(_q["id"], "etc", HAYEON_QS)

                                # 점수에 따른 반응/스탯 변화
                                if score >= 2:
                                    hide new_girl_2_sad
                                    show new_girl_2 happy at left
                                    new_girl_2 "오… 그거였넹! 확실히 이해됐엉. 고마웡!!"
                                elif score == 1:
                                    hide new_girl_2_sad
                                    show new_girl_2 neutral at left
                                    new_girl_2 "힌트가 좀 감 잡히는 듯! 방향 잡아볼게."
                                else:
                                    hide new_girl_2_sad
                                    show new_girl_2 sad at left
                                    new_girl_2 "흐음… 아직 잘 모르겠다. 같이 더 보자!"
                                # 해설 한 줄 (내레이션으로)
                                n "{i}[tip]{/i}"
                                # 효과 적용
                                $ _eff = apply_effects_by_score(score)
                                $ social = clamp(social + _eff.get("social", 0), 0, 100)
                                $ resolve = clamp(resolve + _eff.get("resolve", 0), 0, 100)
                                $ stress = clamp(stress + _eff.get("stress", 0), 0, 100)
                                $ new_girl_2_affection = clamp(new_girl_2_affection + _eff.get("newgirl", 0), 0, 100)
                                return
                    "거절한다":
                        show mc_sad at right
                        hide new_girl_2_sad
                        show new_girl_2_think at left
                        $ money = clamp(money +0, 0, 999)
                        $ social = clamp(social +0, 0, 100)
                        m "미안, 내가 바빠서..."
                        new_girl_2 "웅... 그래? 그럼 언제 시간 돼? 시간 맞춰볼까?"
                        hide mc_sad
                        hide new_girl_2_think
                        menu:
                            "수락한다":
                                show mc_think at right
                                show new_girl_2_happy at left
                                $ money = clamp(money -5, 0, 999)
                                $ social = clamp(social +7, 0, 100)
                                $ new_girl_2_affection +=1
                                m "뭐, 나 내일은 시간 되는데. 내일 점심 어때?"
                                new_girl_2 "웅 조아! 그럼 내일 점심에 보자~!"
                                $ schedule_event("hayeon_help", 1, help_type="physics")
                                $ add_promise("하연", "물리학 공부 도움주기", 1)
                                hide mc_think
                                hide new_girl_2_happy
                            "거절한다":
                                show mc_sad at right
                                show new_girl_2_sad at left
                                $ money = clamp(money +0, 0, 999)
                                $ social = clamp(social +0, 0, 100)
                                $ new_girl_2_affection -=7
                                m "미안, 내가 요즘 바쁘고 힘든 일이 있어서 못 도와줄거 같아."
                                new_girl_2 "음... 그래 그럼 어쩔 수 없지 ㅠㅠ 알겠어."
                                hide mc_sad
                                hide new_girl_2_sad
            "바빠":
                $ social = clamp(social-8, 0, 100)
                new_girl_2 "그래..? 그럼 뭐 어쩔 수 없지..."
                hide hayeon_sexy

    elif r <= 80:
        # 전애인: 연락이 불편하다. (15%)
        scene bg campus
        # 감정적 대화 시 서브 음악 재생
        $ fade_music(sub_music, fade_time=2.0)
        m "수아야, 잘 지내..?"
        m "그동안 정말 미안하고 고마웠어. 짧게라도 너랑 이야기하고 싶은데 안될까?"
        show ex_sad at left
        ex "미안, 더이상 연락 안하면 좋겠어."
        hide ex_sad
        $ stress = clamp(stress + 5, 0, 100)
        $ ex_affection = clamp(ex_affection - 5, 0, 100)
        menu:
            "계속 연락을 이어간다":
                $ s = random_(10)
                if s <= 7:
                    #미련으로 인한 더 큰 단절.
                    $ stress = clamp(stress +5, 0, 100)
                    $ ex_affection = clamp(ex_affection - 5, 0, 100)
                    m "수아야, 내가 그동안 잘못했어. 미안해. 내가 더 노력할게 제발..."
                    show ex_sad at left
                    ex "이제 그만해. 다신 연락하지 마."
                    n "쓸쓸한 적막만이 이 공간을 차갑게 채웠다."
                else:
                    #미련과 미련
                    $ stress = clamp(stress -1, 0, 100)
                    $ ex_affection = clamp(ex_affection + 3, 0, 100)
                    m "수아야... 나도 알아. 이미 끝난 거라는 거."
                    m "근데 가끔은... 그냥 네가 잘 지내는지만 알고 싶어. 난 너가 행복하길 바래. 너 웃는 모습이 가장 예뻐."
                    show ex_neutral at left
                    ex "……."
                    ex "나도 네가 행복했으면 좋겠어. 너가 싫은게 아냐. 더는 우리 얘기로 아프지 않길 바래."
                    ex "하지만 지금은... 서로에게 거리를 두는 게 맞는 것 같아."
                    hide ex_neutral
                    n "짧지만 깊은 여운이 남았다. 아직 완전히 지워지지 않은 마음이, 공기 속에 흩날렸다."
            "더이상 연락하지 않는다":
                show mc_sad at left
                n "어딘가 마음 한 켠이 아려온다."
                m "군대에서 고생하고 시간 지나면... 시간이... 해결해 줄까?"
                n "그는 알고있었다. 시간은 그저 무뎌지게 할 뿐 상처를 치료해주진 못한다는 것을..."
                hide mc_sad

    elif r <= 92:
        # 전애인: 짧은 안부(루트 플래그 ON) (12%)
        scene bg campus
        show ex_neutral at left
        ex "잘 지내지? 바쁘지 않으면… 건강만 챙겨."
        $ route_ex = True
        $ ex_affection = clamp(ex_affection + 2, 0, 100)
        $ stress = clamp(stress - 1, 0, 100)
        m "(짧은 말이지만, 마음이 조금 정리되는 느낌이 들었다.)"
        hide ex_neutral

    else:
        # 번외: 알바 추가콜/오입력 문자 등 가벼운 이벤트 (8%)
        scene bg cafe
        n "가게에서 오전 단기 알바 제안 문자가 왔다."
        menu:
            "수락한다 (돈 +8, 스트레스 +1)":
                show mc_happy at left
                $ money = clamp(money + 8, 0, 999)
                $ stress = clamp(stress + 1, 0, 100)
                m "이럴 때 한 푼이라도 더 벌어두자."
                hide mc_happy
            "거절한다 (스트레스 -1)":
                show mc_neutral at left
                $ stress = clamp(stress - 1, 0, 100)
                m "오늘은 내 컨디션을 우선하자."
                hide mc_neutral
    return

label afternoon_slot:
    # 오후 시간대 약속 체크
    python:
        afternoon_promises = [e for d, events in scheduled_events.items() if d == day 
                            for e in events if e.get("kwargs", {}).get("time_slot") == "afternoon"]
    
    # 약속이 있으면 약속 이벤트만 실행하고 일반 메뉴 건너뛰기
    if afternoon_promises:
        python:
            for event in afternoon_promises:
                character = event["kwargs"]["character"]
                content = event["kwargs"]["content"]
                print(f"오후 약속 실행: {character} - {content}")
        call event_promise_with_ai(afternoon_promises[0]["kwargs"]["character"], afternoon_promises[0]["kwargs"]["content"], "afternoon_promise")
        
        # 약속 실행 후 이벤트 제거
        python:
            for event in afternoon_promises:
                if day in scheduled_events:
                    if event in scheduled_events[day]:
                        scheduled_events[day].remove(event)
                    if not scheduled_events[day]:  # 리스트가 비었으면 키 삭제
                        del scheduled_events[day]
        return
    
    # 약속이 없을 때만 일반 메뉴 실행
    scene bg campus
    # 낮 슬롯 시작 시 조용한 공간으로 설정
    $ update_location_music("campus")
    n "낮. 햇살이 강하다."
    menu:
        "팀플/수업: 공부 , 관계 , 스트레스":
            show mc_think at left
            $ study = clamp(study + 3, 0, 100)
            $ social = clamp(social + 1, 0, 100)
            $ stress = clamp(stress + 1, 0, 100)
            m "프로젝트도 언젠간 끝나겠지..."
            hide mc_think
        "체력단련: 피트니스 , 다짐":
            scene bg gym
            show mc_neutral at left
            $ fitness = clamp(fitness + 4, 0, 100)
            $ resolve = clamp(resolve + 1, 0, 100)
            m "몸이 버티면 마음도 버틴다."
            hide mc_neutral
        "친구와 점심: 관계 , 돈":
            scene bg cafe
            $ social = clamp(social + 2, 0, 100)  
            $ money = clamp(money - 5, 0, 999)
            show jin_think at left
            jin "야, 너 표정 좋아졌다? 준비 잘 되고 있어?"
            m "어... 나름?"
            jin "짜식, 다행이네. 요즘 많이 힘들어 보였었거든."
            m "뭐, 잘 해야지 뭐."
            hide jin_think
        "감정정리(코치) 세션: 다짐 , 스트레스":
            $ resolve = clamp(resolve + 3, 0, 100)
            $ stress = clamp(stress - 1, 0, 100)
            $ counselor_trust += 1
            show coach_think at left
            coach "나는 왜 사는걸까? 핵심가치 세 가지를 적어보자. 생각이 정리가 될거야."
            coach "소소한 행복? 평범한 삶? 아님 뭐 프로젝트가 될수도 있고? 뭐든 좋아."
            hide coach_think
        "낮잠: 의지 , 스트레스":
            show mc_happy at left
            $ resolve = clamp(resolve -3, 0, 100)
            $ stress = clamp(stress -3, 0, 100)
            m "zzz...(현실을 잠시 회피할 순 있으나 무기력해지고 수면욕만 강해진다.)"
            hide mc_happy
    return

label night_slot:
    # 밤 시간대 약속 체크
    python:
        night_promises = [e for d, events in scheduled_events.items() if d == day 
                        for e in events if e.get("kwargs", {}).get("time_slot") == "night"]
    
    # 약속이 있으면 약속 이벤트만 실행하고 일반 메뉴 건너뛰기
    if night_promises:
        python:
            for event in night_promises:
                character = event["kwargs"]["character"]
                content = event["kwargs"]["content"]
                print(f"밤 약속 실행: {character} - {content}")
        call event_promise_with_ai(night_promises[0]["kwargs"]["character"], night_promises[0]["kwargs"]["content"], "night_promise")
        
        # 약속 실행 후 이벤트 제거
        python:
            for event in night_promises:
                if day in scheduled_events:
                    if event in scheduled_events[day]:
                        scheduled_events[day].remove(event)
                    if not scheduled_events[day]:  # 리스트가 비었으면 키 삭제
                        del scheduled_events[day]
        return
    
    # 약속이 없을 때만 일반 메뉴 실행
    scene bg room
    # 밤 슬롯 시작 시 조용한 공간으로 설정
    $ update_location_music("home")
    n "밤. 하루를 마무리할 시간."
    menu:
        "복습/과제: 공부 , 스트레스":
            $ study = clamp(study + 2, 0, 100)
            $ stress = clamp(stress + 1, 0, 100)
            show mc_think at left
            m "조금만 더...근데.. 나는 무얼 위해 공부하는 거지?"
            hide mc_think
        "독서/저널링: 다짐 , 스트레스":
            $ resolve = clamp(resolve + 2, 0, 100)
            $ stress = clamp(stress - 2, 0, 100)
            show mc_think at left
            m "글로 쓰며 마음을 정리했다. 인생을 어떻게 마무리 해야 의미있고 아름다울까?"
            hide mc_think
        "가족 대화: 관계 , 돈":
            $ social = clamp(social + 2, 0, 100)
            show mom_think at left             
            mom "요즘 무슨 일 없지? 입대가 얼마 안 남아서 마음이 좀 그러니?"
            m "엄마, 괜찮아요. 무슨 일 없어요! 그동안 감사했습니다."
            hide mom_think
        "휴식: 스트레스":
            $ stress = clamp(stress - 3, 0, 100)
            show mc_happy at left
            m "아무것도 안 하는 용기. 잠시 쉬는 것도 꼭 필요해!"
            hide mc_happy
        "야간 알바: 돈, 스트레스":
            $ money = clamp(money + 10, 0, 999)
            $ stress = clamp(stress + 2, 0, 100)
            show mc_happy at left
            m "이럴 때 한 푼이라도 더 벌어두자."
            hide mc_happy
        "연락하기":
            jump night_contact_roll
    return

label night_contact_roll:
    # 1~100 사이 주사위
    $ r = random_(100)
    if r <= 30:
        # 친구 진수: 빠른 답장 (30%)
        scene bg cafe
        show jin_neutral at left
        jin "뭐하냐?"
        $ social = clamp(social + 2, 0, 100)  # 3 → 2로 감소
        $ stress = clamp(stress + 1, 0, 100)
        m "그냥 있는데 왜?"
        jin "노래방 ㄱㄱ"
        scene bg karaoke
        $ update_location_music("karaoke")  # 노래방은 음악 재생
        $ play_music(music_energetic, fade_time= 1.0)
        n "둘은 신나게 노래방에서 노래를 불렀다. 어딘가 마음은 쓰렸지만 말이다."
        hide jin_neutral
        # 노래방에서 나온 후 음악 정지
        $ update_location_music("campus")  # 캠퍼스로 돌아가면 조용한 공간
    
    elif r<=45:
        # 여사친 지수: 쾌활하고 밝은 연락이 온다 (15%)
        scene bg campus
        #question 하나 뽑기
        $ _q = choose_(JISU_QS)
        $ _face = _q["face"]
        $ _tag = "jisu_" + _face
        show expression _tag at left

        new_girl_1 "[mc_name]! 너 오늘 시간 돼? 나 코딩하다가 모르는게 있어서 ㅠㅠ 나 도와줄 수 있어?"
        menu:
            "수락한다":
                $ new_girl_1_affection +=1
                m "응, 그래 내가 도와줄게!"
                new_girl_1 "음... "
                new_girl_1 "[_q['text']]"
                # 답변 방식 선택 (자유입력 or 카테고리 선택)
                menu:
                    "직접 답변 입력하기":
                        $ user_ans = renpy.input("네가 생각하는 해결책은? (핵심 키워드 위주로 적어줘)", length=80)
                        $ score, tip, cat = eval_text_answer(_q["id"], user_ans, JISU_QS)
                    "선택지로 답하기(요점만)":
                        menu:
                            "경계/초기화/예외(배열 범위, visited, null 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "bounds", JISU_QS)
                            "알고리즘/자료구조(정렬, 두 포인터, JOIN/정규식 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "algo", JISU_QS)
                            "환경/설정(CORS, 깃 충돌, 빌드/경로 등)":
                                $ score, tip, cat = eval_choice_answer(_q["id"], "env", JISU_QS)
                # 점수에 따른 반응/스탯 변화
                if score >= 2:
                    hide all
                    hide jisu_neutral
                    hide jisu_sad
                    hide jisu_think
                    show jisu_happy at left with dissolve
                    new_girl_1 "오… 그거였넹! 확실히 이해됐엉. 고마웡!!"
                elif score == 1:
                    hide all
                    hide jisu_happy
                    hide jisu_sad
                    hide jisu_think
                    show jisu_neutral at left with dissolve
                    new_girl_1 "힌트가 좀 감 잡히는 듯! 방향 잡아볼게."
                else:
                    hide all
                    hide jisu_happy
                    hide jisu_neutral
                    hide jisu_think
                    show jisu_sad at left with dissolve
                    new_girl_1 "흐음… 아직 잘 모르겠다. 같이 더 보자!"
                # 해설 한 줄 (내레이션으로)
                n "{i}[tip]{/i}"
                # 효과 적용
                $ _eff = apply_effects_by_score(score)
                $ social = clamp(social + _eff.get("social", 0), 0, 100)
                $ resolve = clamp(resolve + _eff.get("resolve", 0), 0, 100)
                $ stress = clamp(stress + _eff.get("stress", 0), 0, 100)
                $ new_girl_1_affection = clamp(new_girl_1_affection + _eff.get("newgirl", 0), 0, 100)
                return
            "거절한다":
                hide all
                hide jisu_happy
                hide jisu_neutral
                hide jisu_think
                show jisu_sad at left with dissolve
                show mc_think at right
                $ money = clamp(money +0, 0, 999)
                $ social = clamp(social +0, 0, 100)
                m "미안, 내가 바빠서..."
                new_girl_1 "웅... 그래? 그럼 언제 시간 돼? 시간 맞춰볼까?"
                hide jisu_sad
                hide mc_think
                menu:
                    "수락한다":
                        show mc_think at right
                        show jisu_happy at left with dissolve
                        $ money = clamp(money -5, 0, 999)
                        $ social = clamp(social +3, 0, 100)
                        $ new_girl_1_affection +=1
                        m "뭐, 나 내일은 시간 되는데. 내일 점심 어때?"
                        new_girl_1 "웅 조아! 그럼 내일 점심에 보자~!"
                        $ schedule_event("jisu_help", 1, help_type="coding")
                        $ add_promise("지수", "코딩 도움주기", 1)
                        hide mc_think
                        hide jisu_happy
                    "거절한다":
                        show mc_sad at right
                        show jisu_sad at left with dissolve
                        $ money = clamp(money +0, 0, 999)
                        $ social = clamp(social +0, 0, 100)
                        $ new_girl_1_affection -=7
                        m "미안, 내가 요즘 바쁘고 힘든 일이 있어서 못 도와줄거 같아."
                        new_girl_1 "음... 그래 그럼 어쩔 수 없지 ㅠㅠ 알겠어."
                        hide mc_sad
                        hide jisu_sad

    elif r <= 65:
        # 가족: 안부 통화 (20%)
        scene bg home
        show mom_think at left         
        mom "뭔 일 없지? 좀 빨리빨리 움직이고! 네 물건 잘 챙기고!"
        $ social = clamp(social + 2, 0, 100)
        $ resolve = clamp(resolve + 1, 0, 100)
        m "네 엄마. 그럴게요."
        hide mom_think

    elif r <= 80:
        # 전애인: 연락이 불편하다. (15%)
        scene bg campus
        show mc_sad at right
        m "수아야, 잘 지내..?"
        m "그동안 정말 미안하고 고마웠어. 짧게라도 너랑 이야기하고 싶은데 안될까?"
        show ex_neutral at left
        ex "미안, 더이상 연락 안하면 좋겠어."
        $ stress = clamp(stress + 5, 0, 100)
        $ ex_affection = clamp(ex_affection - 5, 0, 100)
        hide ex_neutral
        hide mc_sad
        menu:
            "계속 연락을 이어간다":
                $ s = random_(10)
                if s <= 7:
                    #미련으로 인한 더 큰 단절.
                    $ stress = clamp(stress +5, 0, 100)
                    $ ex_affection = clamp(ex_affection - 5, 0, 100)
                    show mc_sad at left
                    m "수아야, 내가 그동안 잘못했어. 미안해. 내가 더 노력할게 제발..."
                    show ex_neutral at right
                    ex "이제 그만해. 다신 연락하지 마."
                    n "쓸쓸한 적막만이 이 공간을 차갑게 채웠다."
                    hide mc_sad
                    hide ex_neutral
                else:
                    #미련과 미련
                    $ stress = clamp(stress -1, 0, 100)
                    $ ex_affection = clamp(ex_affection + 3, 0, 100)
                    show mc_sad at left
                    m "수아야... 나도 알아. 이미 끝난 거라는 거."
                    m "근데 가끔은... 그냥 네가 잘 지내는지만 알고 싶어. 난 너가 행복하길 바래. 너 웃는 모습이 가장 예뻐."
                    show ex_sad at right
                    ex "……."
                    ex "나도 네가 행복했으면 좋겠어. 너가 싫은게 아냐. 더는 우리 얘기로 아프지 않길 바래."
                    ex "하지만 지금은... 서로에게 거리를 두는 게 맞는 것 같아."
                    n "짧지만 깊은 여운이 남았다. 아직 완전히 지워지지 않은 마음이, 공기 속에 흩날렸다."
                    hide mc_sad
                    hide ex_sad
            "연락을 그만둔다":
                # 분위기 롤
                $ s2 = random_(100)
                if s2 <= 40:
                # 1) 성숙한 작별
                    $ stress = clamp(stress - 2, 0, 100)
                    $ resolve = clamp(resolve + 2, 0, 100)
                    show mc_neutral at left
                    m "…알겠어. 더는 연락하지 않을게. 그동안 고마웠어. 건강히 지내."
                    hide mc_neutral
                    n "보내지 못한 말들이 목구멍까지 차올랐지만, [mc_name]은(는) 천천히 폰을 내려놓았다."
                elif s2 <= 80:
                # 2) 씁쓸한 포기
                    $ stress = clamp(stress - 1, 0, 100)
                    $ resolve = clamp(resolve + 1, 0, 100)
                    show mc_sad at left
                    m "(이제… 놓자.)"
                    hide mc_sad
                    n "대화창을 닫는 소리가 방에 또각 하고 울렸다. 공기가 조금 가벼워졌다."
                else:
                # 3) 냉정한 단절(무말)
                    $ stress = clamp(stress - 3, 0, 100)
                    $ resolve = clamp(resolve + 1, 0, 100)
                    $ ex_affection = clamp(ex_affection - 2, 0, 100)
                    n "[mc_name]은(는) 알림을 끄고 대화방을 정리했다. 마지막 말은 남기지 않았다."
                # 레어: 전애인이 짧게 답장(15%)
                $ p = random_(100)
                if p <= 15:
                    show ex_neutral at right
                    ex "…응, 잘 지내."
                    hide ex_neutral
                    n "짧은 한 줄이 묘하게 오래 남았다."
                return
    elif r <= 92:
        # 전애인: 짧은 안부(루트 플래그 ON) (12%)
        scene bg campus
        show ex_neutral at left
        ex "잘 지내지? 바쁘지 않으면… 건강만 챙겨."
        $ route_ex = True
        $ ex_affection = clamp(ex_affection + 2, 0, 100)
        $ stress = clamp(stress - 1, 0, 100)
        m "(짧은 말이지만, 마음이 조금 정리되는 느낌이 들었다.)"
        hide ex_neutral
    else:
        # 번외: 알바 추가콜/오입력 문자 등 가벼운 이벤트 (8%)
        scene bg cafe
        n "발신표시제한으로 전화가 온다."
        menu:
            "수락한다":
                $ money = clamp(money + 8, 0, 999)
                $ stress = clamp(stress + 1, 0, 100)
                m "여보세요?"
                n "???: 책 사게 돈 10만원만 보내줘."
                show mc_happy at left
                m "누구세요? 저 아세요? ㅋㅋ"
                show sis_think at right                 
                sis "아 좀! 오빠 나 진짜 급하게 필요해서 그래.. 제발 응?"
                m "에휴. 근데 왜 대체 발신표시제한으로 전화 거냐? ㅋㅋ 뭐가 찔려서."
                sis "오빠! 진짜 제발. 급해서 그래. 그리고 며칠 전에 부모님한테 용돈 받아서 또 말하기가 좀 그래서..."
                hide mc_happy
                hide sis_think
                menu:
                    "돈을 보내준다":
                        $ money = clamp(money - 10, 0, 999)
                        show mc_neutral at left
                        m "그래. 수능 얼마 안남았으니까 공부 열심히 하고."
                        show sis_happy at right
                        sis "응응! 오빠 진짜 고마워! 빠이~"
                        hide mc_neutral
                        hide sis_happy
                    "돈을 보내주지 않는다":
                        $ money = clamp(money - 0, 0, 999)
                        $ stress = clamp(stress - 3, 0, 100)
                        $ social = clamp(social -3, 0, 100)
                        show mc_neutral at left
                        m "꺼져. 수험생이 무슨 돈 쓸 때가 그리 많다고.."
                        show sis_neutral at right
                        sis "아 오빠 좀! 하여간 도움이 안되요 흥!"
                        hide mc_neutral
                        hide sis_neutral

            "거절한다":
                $ stress = clamp(stress - 1, 0, 100)
                m "모르는 연락은 받지 말자."
    return

# ====== PROMISE EVENTS ======
label event_promise(character, content):
    """약속 이벤트 처리"""
    scene bg home
    n "오늘은 [character]와의 약속이 있는 날이다."
    n "약속 내용: [content]"
    
    # 캐릭터별 약속 이벤트 처리
    if character == "hayeon":
        show hayeon_happy at left
        hayeon "안녕! 약속한 대로 왔어!"
        m "그래, [content]하러 왔어."
        hayeon "고마워! 정말 기뻐."
        $ new_girl_2_affection = clamp(new_girl_2_affection + 3, 0, 100)
        $ social = clamp(social + 2, 0, 100)
        hide hayeon_happy
    elif character == "jisu":
        show jisu_happy at left
        jisu "와! 정말 왔구나!"
        m "당연하지, [content]하자고 했잖아."
        jisu "고마워! 정말 기뻐."
        $ new_girl_1_affection = clamp(new_girl_1_affection + 3, 0, 100)
        $ social = clamp(social + 2, 0, 100)
        hide jisu_happy
    elif character == "ex":
        show ex_happy at left
        ex "정말 왔구나... 고마워."
        m "약속했으니까, [content]하러 왔어."
        ex "정말 고마워."
        $ ex_affection = clamp(ex_affection + 3, 0, 100)
        $ social = clamp(social + 2, 0, 100)
        hide ex_happy
    elif character == "jin":
        show jin_happy at left
        jin "야! 정말 왔구나!"
        m "당연하지, [content]하자고 했잖아."
        jin "고마워! 정말 기뻐."
        $ social = clamp(social + 3, 0, 100)
        hide jin_happy
    else:
        n "[character]와 [content]를 하며 좋은 시간을 보냈다."
        $ social = clamp(social + 2, 0, 100)
    
    n "약속을 지켜서 기분이 좋다."
    $ resolve = clamp(resolve + 1, 0, 100)
    return

# 시간대 약속 이벤트 (AI와 대화)
label event_promise_with_ai(character, content, scene_id):
    """시간대 약속 - AI가 기억을 가지고 나타남"""
    scene bg campus
    n "[character]와의 약속 시간이다."
    n "약속 내용: [content]"
    
    # AI 메모리에 약속 정보 추가
    python:
        ai_memory.append({
            "npc": "system",
            "say": f"오늘 {content} 약속이 있었음",
            "picked": "약속 시작"
        })
    
    # AI 대화 시작 (약속 맥락 포함)
    call ai_single_turn(character, scene_id, "left", "promise_event")
    
    # 추가 대화 (선택지에 따라)
    python:
        continue_conversation = True
        turns = 0
        max_turns = 5  # 최대 5턴
    
    while continue_conversation and turns < max_turns:
        $ turns += 1
        $ last_choice = ai_memory[-1].get("picked", "") if ai_memory else ""
        
        # 대화 종료 조건 체크
        if "나중에" in last_choice or "그만" in last_choice or "끝" in last_choice:
            $ continue_conversation = False
        else:
            call ai_single_turn(character, scene_id, "left", "promise_event")
    
    n "약속을 지켜서 기분이 좋다."
    $ resolve = clamp(resolve + 1, 0, 100)
    
    # 호감도 증가
    python:
        if character == "hayeon":
            new_girl_2_affection = clamp(new_girl_2_affection + 3, 0, 100)
        elif character == "jisu":
            new_girl_1_affection = clamp(new_girl_1_affection + 3, 0, 100)
        elif character == "ex":
            ex_affection = clamp(ex_affection + 3, 0, 100)
        social = clamp(social + 2, 0, 100)
    
    return

# ====== RANDOM EVENTS ======
label random_event:
    $ r = random_(5)
    if r == 1 and not route_ex:
        # 잠재적 전애인 루트 오픈
        scene bg campus
        show ex_neutral at left
        show mc_neutral at right
        n "복도에서 낯익은 뒷모습."
        ex "... [mc_name]?"
        m "어... 잘 지냈어?"
        $ route_ex = True
        $ ex_affection += 2
        hide ex_neutral
        hide mc_neutral
        return
    elif r == 2:
        scene bg cafe
        show jin_happy at left
        show mc_think at right
        jin "이번 주에 야구장 가자."
        menu:
            "간다 (3일 후 야구장 이벤트)":
                $ schedule_event("baseball_game", 3, with_jin=True)
                $ add_promise("진수", "야구장 가기", 3)
                jin "아, 그래 좋아! 좋은 생각이야! 그럼 3일 후에 만나자!"
                n "진수와 야구장 가기로 약속했다. 3일 후에 만나기로 했다."
            "패스한다 (공부+1, 관계-1)":
                $ study = clamp(study + 1, 0, 100)
                $ social = clamp(social - 1, 0, 100)
                jin "쩝, 어쩔 수 없지. 다음엔 꼭 같이 가기다!"
        return
    elif r == 3 and money < 80:
        scene bg home
        show sis_think at right         
        sis "오빠... 용돈 조금만 줄까?ㅋㅋ"
        m "됐어. 오빠가 알아서 할게. 고3이라 힘들텐데 공부나 열심히 혀라."
        $ resolve = clamp(resolve + 1, 0, 100)
        hide sis_think
        return
    elif r == 4 and met_coach:
        scene bg room
        show coach_sad at left
        coach "오늘의 체크인: 통제할 수 없는 것 하나를 떠올리고, 놓아주자."
        $ stress = clamp(stress - 2, 0, 100)
        $ resolve = clamp(resolve + 1, 0, 100)
        hide coach_sad
        return
    else:
        # 소소한 일상
        n "잔잔한 하루였다. 작은 평안이 스며든다."
        $ stress = clamp(stress - 1, 0, 100)
        return

#ai LLM 기반 스토리 및 상황 
label ai_turn(npc, scene_id, side="right", conversation_type="casual"):
    # 대화가 자연스럽게 끝날 때까지 계속
    $ conversation_count = 0
    $ conversation_ended = False
    
    # AI 대화 시작 시 기본 캐릭터 표시 (neutral 표정으로)
    $ default_image = f"{npc}_neutral"
 
    # 모든 캐릭터는 일반 크기로 표시
    if side == "right":
        show expression default_image as ai_face at pos_right
    else:
        show expression default_image as ai_face at pos_left
    # 대화 루프 시작
    call ai_conversation_loop(npc, scene_id, side, conversation_count, conversation_ended, conversation_type)

    # 대화 종료 시 캐릭터 숨기기
    hide ai_face
    
    # 분기 점프 (마지막 선택지의 next가 있으면)
    python:
        if choice.get("next"):
            _next = choice["next"]
            renpy.jump(_next)
    return

# 대화 루프 함수
label ai_conversation_loop(npc, scene_id, side, conversation_count, conversation_ended, conversation_type="casual"):
    # 대화 카운트 증가
    $ conversation_count += 1
    
    # scene_id 업데이트 (첫 번째 대화가 아니면)
    if conversation_count > 1:
        $ scene_id = f"{scene_id}_turn_{conversation_count}"
    
    # 단일 대화 처리
    call ai_single_turn(npc, scene_id, side, conversation_type)
    
    # AI가 대화 종료를 원하는지 확인
    python:
        if "conversation_end" in resp and resp["conversation_end"]:
            conversation_ended = True
        # 최대 10번까지만 대화 (무한 루프 방지)
        elif conversation_count >= 10:
            conversation_ended = True
    
    # 대화가 끝나지 않았으면 계속
    if not conversation_ended:
        call ai_conversation_loop(npc, scene_id, side, conversation_count, conversation_ended, conversation_type)
    
    return

# 단일 대화 처리 함수
label ai_single_turn(npc, scene_id, side, conversation_type="casual"):
    # 1) 상태/메모리 수집 + LLM 호출
    python:
        state = get_game_state()
        mem = ai_memory[-8:]
        resp = ai.ask(npc, scene_id, mem, state, conversation_type)

    if "error" in resp:
        python:
            who = renpy.store.__dict__.get(npc, n)
        $ renpy.say(who, "(AI 서버 오류) 연결 실패")
        return

    # 2) 스프라이트 표시 (별칭 as ai_face 사용)
    $ sprite = resp.get("sprite", "neutral")
    $ image_expr = f"{npc}_{sprite}"
    # 모든 캐릭터는 일반 크기로 표시
    if side == "right":
        show expression image_expr as ai_face at pos_right
    else:
        show expression image_expr as ai_face at pos_left 
    # 3) 대사 출력
    python:
        who = renpy.store.__dict__.get(npc, n)
        line = resp.get("say", "...")
        # Ren'Py 텍스트 태그 충돌 방지: {}를 안전하게 처리
        line = line.replace("{", "{{").replace("}", "}}")
    $ renpy.say(who, line)

    # 4) 선택지 처리
    python:
        chs = resp.get("choices", [])
        # 선택지 텍스트도 안전하게 처리
        for ch in chs:
            if "text" in ch:
                ch["text"] = ch["text"].replace("{", "{{").replace("}", "}}")
    if not chs:
        hide ai_face
        return

    python:
        idx = renpy.call_screen("ai_choices", chs)
        choice = chs[idx]

    # 5) 스탯 반영
    python:
        eff = choice.get("effects", {})
        stress = clamp(stress + eff.get("stress", 0), 0, 100)
        resolve = clamp(resolve + eff.get("resolve", 0), 0, 100)
        social = clamp(social + eff.get("social", 0), 0, 100)
        study = clamp(study + eff.get("study", 0), 0, 100)
        fitness = clamp(fitness + eff.get("fitness", 0), 0, 100)
        money = clamp(money + eff.get("money", 0), 0, 999)
        ex_affection = clamp(ex_affection + eff.get("ex_affection", 0), 0, 100)
        new_girl_1_affection = clamp(new_girl_1_affection + eff.get("jisu_affection", 0), 0, 100)
        new_girl_2_affection = clamp(new_girl_2_affection + eff.get("hayeon_affection", 0), 0, 100)

    # 6) 기억 업데이트
    python:
        picked_text = choice.get("text", "")
        ai_memory.append({"npc": npc, "say": line, "picked": picked_text})

    # 7) 약속 처리 (플레이어 선택 기반)
    python:
        import re
        
        # 플레이어가 선택한 텍스트에서 약속 감지
        picked_text = choice.get("text", "")
        detected_promise = None
        
        # 약속 패턴 감지 (선택지에서)
        promise_keywords = [r"만나자", r"보자", r"가자", r"하자"]
        has_promise_keyword = any(re.search(kw, picked_text) for kw in promise_keywords)
        
        if has_promise_keyword:
            print(f"플레이어가 약속 선택: {picked_text}")
            
            # 시간대 감지
            time_slot = None
            delay_days = 0
            
            # 오늘 + 시간
            if re.search(r"오늘\s*(\d+)시", picked_text):
                time_slot = "afternoon"
                delay_days = 0
                print(f"오늘 시간 약속 감지")
            elif re.search(r"오늘\s*(오전|아침)", picked_text):
                time_slot = "morning"
                delay_days = 0
            elif re.search(r"오늘\s*(점심|낮|오후)", picked_text):
                time_slot = "afternoon"
                delay_days = 0
            elif re.search(r"오늘\s*(저녁|밤)", picked_text):
                time_slot = "night"
                delay_days = 0
            # 날짜 감지
            elif "내일" in picked_text:
                delay_days = 1
            elif "다음 주" in picked_text or "다음주" in picked_text:
                delay_days = 7
            elif re.search(r'(\d+)일\s*후', picked_text):
                match = re.search(r'(\d+)일\s*후', picked_text)
                delay_days = int(match.group(1))
            
            # 약속 등록
            promise_id = add_promise(npc, picked_text, delay_days)
            print(f"약속 등록: {npc} - {picked_text} (Day {day + delay_days})")
            
            # 이벤트 스케줄
            if time_slot:
                event_type = f"promise_{npc}_{promise_id}_slot_{time_slot}"
                schedule_event(event_type, delay_days, npc=npc, character=npc, content=picked_text, time_slot=time_slot)
                print(f"시간대 이벤트 스케줄: {event_type} - {time_slot}")
            else:
                event_type = f"promise_{npc}_{promise_id}"
                schedule_event(event_type, delay_days, npc=npc, character=npc, content=picked_text)
                print(f"이벤트 스케줄: {event_type} - {delay_days}일 후")
            
            # AI 메모리에 약속 정보 추가
            ai_memory.append({
                "npc": "system",
                "say": f"약속 확정: {picked_text}",
                "picked": "약속 등록됨"
            })

    return


# ====== ENDINGS ======
label check_endings:
    scene bg campus

    # 1) 특수 루트 우선
    if route_ex and ex_affection >= 65 and resolve >= 60 and stress <= 60:
        jump ending_peace_closure
    elif new_girl_1_affection >= 60 and resolve >= 60 and social >= 55 and study >= 80:
        jump ending_love_1_closure
    elif new_girl_2_affection >= 60 and resolve >= 60 and social >= 55 and study >= 80:
        jump ending_love_2_closure

    # 2) 일반 성취/소진 엔딩
    elif resolve >= 85 and stress <= 30 and fitness >= 70 and counselor_trust >= 4:
        jump ending_new_start
    elif study >= 85 and resolve >= 65:
        jump ending_focus_future
    elif stress >= 85:
        jump ending_burnout
    else:
        jump ending_bittersweet

label ending_new_start:
    show mc_neutral at left
    n "입대 전날 밤."
    m "두렵지만, 준비는 됐다. 내가 선택해온 날들이 나를 만든다."
    n "새벽 공기를 가르며, [mc_name]의 새로운 시작이 열린다."
    m "비록 내가 원한 입대시기도 아니고 내가 원하는 대로 된게 없지만 그래도 아직 나아갈 기회가 남았어!"
    n "굳게 다짐하는 [mc_name]. 내일 공군에 입대하게 된다."
    n "비록 힘들었던 순간이 많았지만, 결국 [mc_name]은 다 이겨냈고 새로운 시작을 할 수 있을 것이다."
    hide mc_neutral
    return

label ending_focus_future:
    show mc_think at left
    n "정리된 책상, 조용한 마음."
    m "돌아와서도 이어갈 공부와 길. 나는 나의 미래를 택한다. 그래도 하루하루 버티며 살아는 있어야지."
    hide mc_think
    return

label ending_burnout:
    show coach_sad at left
    n "과열된 엔진은 잠시 쉬어야 한다."
    coach "멈춤도 전략이야. 도움을 요청하는 건 용기야."
    n "[mc_name]은(는) 소주를 연거푸 마신다. 쓰라린 소주가 더이상 쓰지 않다."
    hide coach_sad
    return

label ending_peace_closure:
    show ex_neutral at left
    show mc_neutral at right
    ex "잘 지내. 서로 각자의 길에서."
    m "고마웠어. 그 모든 날들."
    n "한 페이지를 덮고, 더 단단해진 마음으로 내일을 맞는다."
    hide ex_neutral
    hide mc_neutral
    return

label ending_love_1_closure:
    show mc_happy at right
    show jisu_happy at left
    m "지수야, 내가 힘들 때도 즐거울 때에도 내 곁에 있어줘서 고마워!"
    new_girl_1 "ㅎㅎ 뭘.. 나도 너한테 고마워!"
    hide mc_happy
    show mc_think at right
    m "그래서 내가 곰곰히 생각해 봤는데..."
    hide mc_think
    hide jisu_happy
    menu:
        "고백한다":
            show mc_happy at right
            show jisu_happy at left
            m "지수야, 나 너 좋아해. 나랑 사귀자."
            n "지수의 얼굴이 붉어지며 눈웃음이 지어진다."
            new_girl_1 "웅! 조아! 오늘부터 1일!"
            new_girl_1 "군대에서도 꼭 연락하고! 내가 편지 꼭 쓸게! 사랑해~"
            hide mc_happy
            hide jisu_happy
        "고백하지 않는다":
            show mc_neutral at right
            show jisu_sad at left
            m "넌 정말 좋은 친구인거 같아! 앞으로도 우리 우정 변치 말자."
            n "지수의 표정이 미묘하게 흔들린다."
            new_girl_1 "친구..? 그..그래.."
            n "지수의 표정이 미묘하게 슬퍼보인다."
            n "[mc_name]또한 마음이 그리 썩 좋지 않았다. 불확실한 미래 때문에 군대 떄문에 그리고 자기 마음 때문에..."
            hide mc_neutral
            hide jisu_sad
    return

label ending_love_2_closure:
    show mc_happy at right
    show hayeon_happy at left     
    m "하연아, 내가 힘들 때에도 즐거울 때에도 내 곁에 있어줘서 고마워!"
    new_girl_2 "ㅎㅎ 뭘.. 나도 너한테 고마워"
    hide mc_happy
    hide hayeon_happy
    menu:
        "고백한다":
            show mc_happy at right
            show hayeon_happy at left             
            m "하연아, 나 너 좋아해. 나랑 사귀자."
            n "하연의 얼굴이 붉어지며 눈웃음이 지어진다."
            new_girl_2 "웅! 조아! 오늘부터 1일!"
            new_girl_2 "군대에서도 꼭 연락하고! 내가 편지 꼭 쓸게! 사랑해"
            hide mc_happy
            hide hayeon_happy
        "고백하지 않는다":
            show mc_neutral at right
            show hayeon_sad at left             
            m "넌 정말 좋은 친구야. 앞으로도 우리 우정 변치 말자."
            n "하연의 표정이 미묘하게 흔들린다."
            new_girl_2 "친구..? 그.. 그래..."
            hide mc_neutral
            hide hayeon_sad
    return

label ending_bittersweet:
    show mc_sad at left
    n "쓰라리다."
    m "삶이 더욱 흐릿해져간다."
    n "입대라는 경계 앞에서, [mc_name]은(는) 결국 운명에 순응한채 하루하루를 그저 버티며 슬퍼한다."
    hide mc_sad
    return

# ===== 지연 이벤트들 =====
label event_baseball_game(with_jin=False):
    scene bg campus
    # 특별한 이벤트 시 서브 음악 재생
    $ fade_music(sub_music, fade_time=2.0)
    n "며칠 전에 약속했던 야구장에 왔다."
    
    # 약속 완료 처리
    python:
        jin_promises = get_promises_by_character("진수")
        baseball_promise = None
        for promise in jin_promises:
            if "야구장" in promise["content"] and promise["status"] == "pending":
                baseball_promise = promise
                break
    
    if with_jin:
        show jin_happy at left
        jin "야! 드디어 왔네! 오늘 경기 진짜 재밌을 것 같은데?"
        m "응! 기대된다!"
        $ social = clamp(social + 5, 0, 100)
        $ stress = clamp(stress - 3, 0, 100)
        n "진수와 함께 야구 경기를 관람했다. 시원한 맥주와 함께 즐거운 시간을 보냈다."
        hide jin_happy
        
        # 약속 완료 처리
        if baseball_promise:
            $ complete_promise(baseball_promise["id"])
            n "진수와의 약속을 지켰다. 마음이 한결 가벼워졌다."
    else:
        show mc_happy at left
        m "와... 야구장 분위기가 정말 좋네!"
        $ stress = clamp(stress - 2, 0, 100)
        n "혼자서도 야구 경기를 즐겼다. 마음이 한결 편해졌다."
        hide mc_happy
    
    return

label event_jisu_help(help_type="coding"):
    scene bg library
    show jisu_happy at left
    new_girl_1 "야! [mc_name]! 그때 말한 도움, 이제 받을 수 있어?"
    
    if help_type == "coding":
        new_girl_1 "코딩 프로젝트가 막막해... 도와줄 수 있어?"
        menu:
            "도와준다 (공부 +2, 사회성 +3, 돈 -10)":
                $ study = clamp(study + 2, 0, 100)
                $ social = clamp(social + 3, 0, 100)
                $ money = clamp(money - 10, 0, 999)
                $ new_girl_1_affection += 2
                new_girl_1 "고마워! 정말 도움이 많이 됐어!"
                n "지수와 함께 코딩 프로젝트를 완성했다. 서로 도움이 되는 시간이었다."
            "바쁘다고 거절한다":
                $ new_girl_1_affection -= 1
                new_girl_1 "아... 그렇구나. 괜찮아, 다른 사람한테 물어볼게."
                n "지수의 표정이 조금 실망스러워 보였다."
    
    hide jisu_happy
    return

label event_hayeon_study(subject="physics"):
    scene bg library
    show hayeon_happy at left     
    new_girl_2 "[mc_name]! 그때 말한 공부, 같이 할까?"
    
    if subject == "physics":
        new_girl_2 "물리학 문제가 너무 어려워... 같이 풀어보자!"
        menu:
            "함께 공부한다 (공부 +3, 사회성 +2)":
                $ study = clamp(study + 3, 0, 100)
                $ social = clamp(social + 2, 0, 100)
                $ new_girl_2_affection += 2
                new_girl_2 "와! 이제 이해됐어! 고마워!"
                n "하연과 함께 물리학 문제를 풀었다. 서로 도움이 되는 시간이었다."
            "바쁘다고 거절한다":
                $ new_girl_2_affection -= 1
                new_girl_2 "아... 그렇구나. 괜찮아, 혼자 해볼게."
                n "하연의 표정이 조금 실망스러워 보였다."
    
    hide hayeon_happy
    return