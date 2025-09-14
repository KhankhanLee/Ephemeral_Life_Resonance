# A simple always-on HUD + day planner helper
screen hud():
    frame:
        align (0.98, 0.02)     
        padding (12, 10)

        vbox:
            spacing 6
            text "D-[days_left]  (Day [day])" size 35
            hbox:
                spacing 10
                vbox:
                    text "스트레스: [stress]" size 30
                    text "다짐: [resolve]" size 30
                    text "관계: [social]" size 30
                vbox:
                    text "공부: [study]" size 30
                    text "피트니스: [fitness]" size 30
                    if money < money_warning_threshold:
                        text "돈: [money] ⚠️" size 30 color "#ff6b6b"
                    else:
                        text "돈: [money]" size 30
                    text "음악: [current_music]" size 30
            
            # 약속 섹션
            if len(get_pending_promises()) > 0:
                frame:
                    background "#2a2a2a"
                    padding (8, 6)
                    vbox:
                        text "약속" size 25 color "#ffd700"
                        for promise in get_pending_promises()[:3]:  # 최대 3개만 표시
                            text f"• {promise['character']}: {promise['content']}" size 20 color "#ffffff"
                        if len(get_pending_promises()) > 3:
                            text f"... 외 {len(get_pending_promises()) - 3}개" size 18 color "#cccccc"
    # Quick menu (bottom)
    use quick_menu

screen quick_menu():
    hbox:
        style_prefix "quick"
        xalign 0.98
        yalign 0.98
        spacing 12
        textbutton _("저장") action ShowMenu('save')
        textbutton _("불러오기") action ShowMenu('load')
        textbutton _("환경설정") action ShowMenu('preferences')
        textbutton _("로그") action ShowMenu('history')
        textbutton _("음악") action ToggleMusic()
        textbutton _("건너뛰기") action Skip()
        textbutton _("자동진행") action Preference("auto-forward", "toggle")

screen ai_choices(choices):
    modal True
    frame align (0.5, 0.8) padding (16, 16):
        vbox spacing 8:
            for i, ch in enumerate(choices):
                textbutton "[ch['text']]" action Return(i)
                
style quick_button_text is default:
    color "#e5e7eb"
    size 14
