import flet as ft
import random
import importlib

categories = {
    "The Office": "trivia_data.trivia_the_office",
    "الرياضة": "trivia_data.trivia_sports",
    "الجغرافيا": "trivia_data.trivia_geography",
    "الأفلام": "trivia_data.trivia_movies",
    "الموسيقى": "trivia_data.trivia_music",
    "ثقافة عامة": "trivia_data.trivia_general_knowledge",
    "تكنولوجيا": "trivia_data.trivia_technology",
    "تاريخ": "trivia_data.trivia_history",
    "رمضان": "trivia_data.trivia_ramadan",
    "ألعاب فيديو": "trivia_data.trivia_video_games",
    "أنمي": "trivia_data.trivia_anime",
    "كرتون": "trivia_data.trivia_cartoons"
}

def load_questions(module_path):
    try:
        mod = importlib.import_module(module_path)
        return mod.trivia_questions
    except Exception as e:
        return []

def trivia_battle_game(page: ft.Page, go_home):
    page.scroll = True

    state = {
        "step": "choose_team_count",
        "team_count": 2,
        "team_inputs": [],
        "teams": [],
        "scores": {},
        "selected_category": None,
        "question_pool": [],
        "question_order": [],
        "question_index": 0,
        "current_team_index": 0,
        "has_answered": False,
        "last_answer_correct": None,
        "last_correct_answer": None,
    }

    def update_ui():
        page.views.clear()
        view = ft.View(route="/trivia_battle", controls=[], scroll=ft.ScrollMode.AUTO)
        page.views.append(view)

        if state["step"] == "choose_team_count":
            view.controls.append(ft.Text("👥 كم عدد الفرق؟", size=24))
            view.controls.append(
                ft.Row([
                    ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda e: change_team_count(-1)),
                    ft.Text(str(state["team_count"]), size=26),
                    ft.IconButton(icon=ft.Icons.ADD, on_click=lambda e: change_team_count(1)),
                ])
            )
            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: go_to_team_names()))
            view.controls.append(ft.ElevatedButton("🔙 رجوع للقائمة الرئيسية", on_click=go_home))

        elif state["step"] == "enter_team_names":
            view.controls.append(ft.Text("✏️ أدخل أسماء الفرق:", size=24))
            for tf in state["team_inputs"]:
                view.controls.append(tf)

            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: save_teams()))
            view.controls.append(ft.ElevatedButton("🔙 رجوع", on_click=lambda e: go_to_team_count()))

        elif state["step"] == "choose_category":
            view.controls.append(ft.Text("🧠 اختر فئة الأسئلة", size=24))
            dd = ft.Dropdown(options=[ft.dropdown.Option(cat) for cat in categories.keys()])

            def confirm_category(e):
                if dd.value:
                    state["selected_category"] = dd.value
                    module_path = categories[dd.value]
                    all_questions = load_questions(module_path)
                    questions_needed = len(state["teams"]) * 10
                    state["question_pool"] = random.sample(all_questions, min(questions_needed, len(all_questions)))
                    state["question_order"] = list(range(len(state["question_pool"])))
                    random.shuffle(state["question_order"])
                    state["step"] = "question"
                    update_ui()

            view.controls.append(dd)
            view.controls.append(ft.ElevatedButton("بدء اللعبة", on_click=confirm_category))
            view.controls.append(ft.ElevatedButton("🔙 رجوع", on_click=lambda e: go_to_team_names()))

        elif state["step"] == "question":
            if state["question_index"] < len(state["question_order"]):
                team = state["teams"][state["current_team_index"]]
                qid = state["question_order"][state["question_index"]]
                question = state["question_pool"][qid]

                view.controls.append(ft.Text(f"❓ السؤال {state['question_index']+1} - الفريق: {team}", size=22))
                view.controls.append(ft.Text(question["question"], size=20))

                if not state["has_answered"]:
                    for option in question["options"]:
                        def make_choice(opt):
                            def handler(e):
                                state["has_answered"] = True
                                state["last_correct_answer"] = question["answer"]
                                if opt == question["answer"]:
                                    state["last_answer_correct"] = True
                                    state["scores"][team] += 1
                                else:
                                    state["last_answer_correct"] = False
                                update_ui()
                            return handler
                        view.controls.append(ft.ElevatedButton(option, on_click=make_choice(option)))
                else:
                    if state["last_answer_correct"]:
                        view.controls.append(ft.Text("✅ إجابة صحيحة!", color="green"))
                    else:
                        view.controls.append(ft.Text(f"❌ خاطئة! الجواب الصحيح: {state['last_correct_answer']}", color="red"))

                    view.controls.append(ft.Text("📊 النقاط الحالية:", size=20))
                    for t in state["teams"]:
                        view.controls.append(ft.Text(f"- {t}: {state['scores'][t]} نقطة"))

                    view.controls.append(ft.ElevatedButton("السؤال التالي", on_click=lambda e: next_question()))

                view.controls.append(ft.ElevatedButton("🔙 رجوع للقائمة الرئيسية", on_click=go_home))

            else:
                state["step"] = "results"
                update_ui()

        elif state["step"] == "results":
            view.controls.append(ft.Text("🎉 انتهت اللعبة!", size=24))
            view.controls.append(ft.Text("🏆 النتائج النهائية:", size=22))
            for t in state["teams"]:
                view.controls.append(ft.Text(f"- {t}: {state['scores'][t]} نقطة"))

            view.controls.append(ft.ElevatedButton("🔁 العب مرة أخرى", on_click=lambda e: restart_game()))
            view.controls.append(ft.ElevatedButton("🔙 رجوع للقائمة الرئيسية", on_click=go_home))

        page.update()

    def change_team_count(delta):
        state["team_count"] = max(2, min(6, state["team_count"] + delta))
        update_ui()

    def go_to_team_names():
        state["team_inputs"] = [ft.TextField(label=f"اسم الفريق {i+1}") for i in range(state["team_count"])]
        state["step"] = "enter_team_names"
        update_ui()

    def go_to_team_count():
        state["step"] = "choose_team_count"
        update_ui()

    def save_teams():
        names = [tf.value.strip() for tf in state["team_inputs"] if tf.value.strip()]
        if len(names) < 2 or len(names) != len(set(names)):
            page.snack_bar = ft.SnackBar(ft.Text("❗ أدخل أسماء فِرَق فريدة وصحيحة (2 على الأقل)"))
            page.snack_bar.open = True
            page.update()
            return
        state["teams"] = names
        state["scores"] = {name: 0 for name in names}
        state["step"] = "choose_category"
        update_ui()

    def next_question():
        state["question_index"] += 1
        state["current_team_index"] = (state["current_team_index"] + 1) % len(state["teams"])
        state["has_answered"] = False
        state["last_answer_correct"] = None
        update_ui()

    def restart_game():
        state.clear()
        state.update({
            "step": "choose_team_count",
            "team_count": 2,
            "team_inputs": [],
            "teams": [],
            "scores": {},
            "selected_category": None,
            "question_pool": [],
            "question_order": [],
            "question_index": 0,
            "current_team_index": 0,
            "has_answered": False,
            "last_answer_correct": None,
            "last_correct_answer": None,
        })
        update_ui()

    update_ui()
    page.on_resized = lambda e: update_ui()
