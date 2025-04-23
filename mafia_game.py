import flet as ft
import random

def mafia_game(page: ft.Page, go_home):
    page.scroll = True

    state = {
        "log": [],
        "page": "setup",
        "players": [],
        "roles": {},
        "num_players": 5,
        "current_player_turn": 0,
        "eliminated_players": [],
        "night_results": {},
        "night_step": "mafia",
        "last_doctor_save": None,
        "night_counter": 1,
    }

    def assign_roles():
        players = state["players"]
        num_players = len(players)
        roles = ['مافيا'] * (1 if num_players <= 6 else 2 if num_players <= 10 else 3)
        roles += ['طبيب', 'محقق']
        roles += ['مواطن'] * (num_players - len(roles))
        random.shuffle(roles)
        state["roles"] = {player: role for player, role in zip(players, roles)}
        state["page"] = "show_roles"
        update_ui()

    def game_over_check():
        mafia_alive = sum(1 for p in state["players"] if state["roles"][p] == 'مافيا' and p not in state["eliminated_players"])
        citizens_alive = sum(1 for p in state["players"] if state["roles"][p] != 'مافيا' and p not in state["eliminated_players"])
        return mafia_alive == 0 or mafia_alive >= citizens_alive

    def update_ui():
        page.views.clear()
        view = ft.View("/mafia", controls=[], scroll=ft.ScrollMode.AUTO)
        page.views.append(view)

        if state["page"] == "setup":
            view.controls.append(ft.Text("🎭 إعداد لعبة المافيا", size=28))
            num_display = ft.Text(f"عدد اللاعبين: {state['num_players']}", size=20)

            def update_num(change):
                state["num_players"] = max(5, min(15, state["num_players"] + change))
                update_ui()

            view.controls += [
                num_display,
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: update_num(-1)),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: update_num(1)),
                ]),
                ft.ElevatedButton("التالي", on_click=lambda e: to_input_players()),
                ft.ElevatedButton("🔙 رجوع للقائمة الرئيسية", on_click=go_home)
            ]

        elif state["page"] == "input_players":
            view.controls.append(ft.Text("👥 أدخل أسماء اللاعبين:", size=24))
            inputs = [ft.TextField(label=f"اللاعب {i+1}") for i in range(state["num_players"])]
            view.controls.extend(inputs)

            def save_players(e):
                names = [tf.value.strip() for tf in inputs]
                if len(set(names)) != len(names) or any(n == "" for n in names):
                    page.snack_bar = ft.SnackBar(ft.Text("❗ الأسماء يجب أن تكون فريدة ومملوءة"))
                    page.snack_bar.open = True
                    page.update()
                    return
                state["players"] = names
                assign_roles()

            view.controls.append(ft.ElevatedButton("تأكيد وتوزيع الأدوار", on_click=save_players))

        elif state["page"] == "show_roles":
            player = state["players"][state["current_player_turn"]]
            view.controls += [
                ft.Text(f"📱 أعط الجهاز للاعب: {player}", size=22),
                ft.ElevatedButton("👀 عرض الدور", on_click=lambda e: switch_page("display_role"))
            ]

        elif state["page"] == "display_role":
            player = state["players"][state["current_player_turn"]]
            role = state["roles"][player]
            eliminated = player in state["eliminated_players"]
            desc = {
                'مافيا': "مهمتك قتل المدنيين ليلاً والتعاون مع زملائك في المافيا.",
                'طبيب': "يمكنك إنقاذ لاعب واحد كل ليلة من القتل.",
                'محقق': "يمكنك التحقق من دور لاعب واحد كل ليلة.",
                'مواطن': "مهمتك اكتشاف المافيا وتصويتهم خارج المدينة أثناء النهار."
            }[role]
            view.controls += [
                ft.Text(f"{player}، دورك هو: {role}" + (" (❌ تم قتلك)" if eliminated else ""), size=22),
                ft.Text(desc)
            ]

            def next_player(e):
                if state["current_player_turn"] + 1 < len(state["players"]):
                    state["current_player_turn"] += 1
                    state["page"] = "show_roles"
                else:
                    state["current_player_turn"] = 0
                    state["page"] = "night_phase_intro"
                    state["night_step"] = "mafia"
                    state["night_results"] = {}
                update_ui()

            view.controls.append(ft.ElevatedButton("التالي", on_click=next_player))

        elif state["page"] == "night_phase_intro":
            step = state["night_step"]
            intro_text = {
                "mafia": "😴 الجميع ينام الآن... فقط المافيا تستيقظ.",
                "doctor": "😴 المافيا تنام الآن... الطبيب فقط يستيقظ.",
                "detective": "😴 الطبيب ينام الآن... المحقق فقط يستيقظ."
            }[step]
            view.controls.append(ft.Text(intro_text, size=24, weight="bold"))
            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: switch_page("night_phase")))

        elif state["page"] == "night_phase":
            view.controls.append(ft.Text("🌙 مرحلة الليل", size=26))
            alive = [p for p in state["players"] if p not in state["eliminated_players"]]
            step = state["night_step"]

            if step == "mafia":
                mafia_players = [p for p in alive if state["roles"][p] == 'مافيا']
                targets = [p for p in alive if p not in mafia_players]
                dropdown = ft.Dropdown(label="اختر الهدف", options=[ft.dropdown.Option(p) for p in targets], width=300)
                view.controls += [
                    ft.Text("☠️ المافيا تختار الضحية"),
                    dropdown,
                    ft.ElevatedButton("التالي", on_click=lambda e: save_and_continue("mafia_target", dropdown.value, "doctor"))
                ]

            elif step == "doctor":
                doctors = [p for p in alive if state["roles"][p] == 'طبيب']
                view.controls.append(ft.Text("🛡 الطبيب يستعد للاختيار (حتى لو كان ميتًا)", italic=True))
                if doctors:
                    dropdown = ft.Dropdown(label="اختر من تريد إنقاذه", options=[ft.dropdown.Option(p) for p in alive], width=300)
                    error_text = ft.Text()

                    def save_choice(e):
                        choice = dropdown.value
                        if choice == state["last_doctor_save"]:
                            error_text.value = "❗ لا يمكنك إنقاذ نفس الشخص مرتين متتاليتين!"
                            page.update()
                        else:
                            state["night_results"]["doctor_save"] = choice
                            state["last_doctor_save"] = choice
                            state["night_step"] = "detective"
                            state["page"] = "night_phase_intro"
                            update_ui()

                    view.controls += [dropdown, ft.ElevatedButton("التالي", on_click=save_choice), error_text]
                else:
                    view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: save_and_continue(None, None, "detective")))

            elif step == "detective":
                detectives = [p for p in alive if state["roles"][p] == 'محقق']
                view.controls.append(ft.Text("🕵️ المحقق يستعد للتحقيق (حتى لو كان ميتًا)", italic=True))
                if detectives:
                    detective = detectives[0]
                    targets = [p for p in alive if p != detective]
                    dropdown = ft.Dropdown(label="اختر من تتحقق منه", options=[ft.dropdown.Option(p) for p in targets], width=300)
                    feedback = ft.Text()

                    def investigate(e):
                        t = dropdown.value
                        result = state["roles"][t]
                        feedback.value = f"{t} {'هو' if result == 'مافيا' else 'ليس'} مافيا"
                        state["night_results"]["detective_investigation"] = {"target": t, "result": result}
                        view.controls.append(feedback)
                        view.controls.append(ft.ElevatedButton("التالي", on_click=lambda x: switch_page("night_summary")))
                        page.update()

                    view.controls += [dropdown, ft.ElevatedButton("تحقق", on_click=investigate)]
                else:
                    view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: switch_page("night_summary")))

        elif state["page"] == "night_summary":
            mafia_target = state["night_results"].get("mafia_target")
            doctor_save = state["night_results"].get("doctor_save")
            detective_info = state["night_results"].get("detective_investigation")

            view.controls.append(ft.Text(f"📜 ملخص ليلة {state['night_counter']}:", size=20, weight="bold"))

            if mafia_target == doctor_save:
                view.controls.append(ft.Text(f"✅ تم إنقاذ {mafia_target} من قبل الطبيب!", color="green"))
                state["log"].append(f"ليلة {state['night_counter']}: تم إنقاذ {mafia_target} من قبل الطبيب")
            elif mafia_target:
                view.controls.append(ft.Text(f"☠️ تم قتل {mafia_target}!", color="red"))
                state["log"].append(f"ليلة {state['night_counter']}: تم قتل {mafia_target} من قبل المافيا")
                if mafia_target not in state["eliminated_players"]:
                    state["eliminated_players"].append(mafia_target)

            if detective_info:
                t = detective_info["target"]
                res = detective_info["result"]
                view.controls.append(ft.Text(f"🔍 تحقق المحقق من {t} - {'مافيا' if res == 'مافيا' else 'مدني'}"))
                state["log"].append(f"ليلة {state['night_counter']}: تحقق المحقق من {t} ووجده {'مافيا' if res == 'مافيا' else 'مدني'}")

            view.controls.append(ft.ElevatedButton("الانتقال إلى النهار", on_click=lambda e: switch_page("night_wakeup")))

        elif state["page"] == "night_wakeup":
            view.controls.append(ft.Text("🌞 الجميع يستيقظ الآن... يبدأ التصويت!", size=24, weight="bold"))
            view.controls.append(ft.ElevatedButton("ابدأ مرحلة النهار", on_click=lambda e: switch_page("day_phase")))

        elif state["page"] == "day_phase":
            view.controls.append(ft.Text("☀️ مرحلة النهار", size=26))
            alive = [p for p in state["players"] if p not in state["eliminated_players"]]
            dropdown = ft.Dropdown(label="اختر من تصوت ضده", options=[ft.dropdown.Option(p) for p in alive], width=300)

            def vote_out(e):
                selected = dropdown.value
                if selected:
                    state["eliminated_players"].append(selected)
                    state["log"].append(f"تم التصويت ضد {selected} خلال النهار")
                    if game_over_check():
                        switch_page("game_over")
                    else:
                        switch_page("daily_summary")

            view.controls += [dropdown, ft.ElevatedButton("تصويت", on_click=vote_out)]

        elif state["page"] == "daily_summary":
            view.controls.append(ft.Text("📊 ملخص الجولة:", size=22, weight="bold"))
            for player, role in state["roles"].items():
                status = "✅ حي" if player not in state["eliminated_players"] else "❌ مقتول"
                view.controls.append(ft.Text(f"{player}: {role} ({status})"))
            view.controls.append(ft.Text("📘 سجل الأحداث:", size=20, weight="bold"))
            for event in state["log"]:
                view.controls.append(ft.Text(f"- {event}"))
            view.controls.append(ft.ElevatedButton("الاستمرار إلى الليل", on_click=lambda e: continue_to_night()))

        elif state["page"] == "game_over":
            view.controls.append(ft.Text("📜 الأدوار:", size=20, weight="bold"))
            for player, role in state["roles"].items():
                status = "✅ حي" if player not in state["eliminated_players"] else "❌ مقتول"
                view.controls.append(ft.Text(f"{player}: {role} ({status})"))
            view.controls.append(ft.Text("📘 سجل الأحداث:", size=20, weight="bold"))
            for event in state["log"]:
                view.controls.append(ft.Text(f"- {event}"))
            mafia_alive = sum(1 for p in state["players"] if state["roles"][p] == 'مافيا' and p not in state["eliminated_players"])
            if mafia_alive == 0:
                view.controls.append(ft.Text("🏆 فاز المدنيون! كل المافيا تم التخلص منهم!", color="green", size=24))
            else:
                view.controls.append(ft.Text("🏴 فازت المافيا! سيطروا على المدينة!", color="red", size=24))
            view.controls.append(ft.ElevatedButton("🏠 العودة للرئيسية", on_click=go_home))

        page.update()

    def switch_page(name):
        state["page"] = name
        update_ui()

    def save_and_continue(key, value, next_step):
        if value:
            state["night_results"][key] = value
        state["night_step"] = next_step
        state["page"] = "night_phase_intro"
        update_ui()

    def to_input_players():
        state["page"] = "input_players"
        update_ui()

    def continue_to_night():
        state["night_step"] = "mafia"
        state["night_counter"] += 1
        state["night_results"] = {}
        switch_page("night_phase_intro")

    update_ui()
