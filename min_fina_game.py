import flet as ft
import random
from min_fina_questions import min_fina_questions

state = {}

def destroy_min_fina():
    state.clear()

def min_fina_game(page: ft.Page, go_home):
    destroy_min_fina()
    page.on_resized = None

    state.update({
        "page": "rules",
        "num_players": 3,
        "player_names": [],
        "current_question": None,
        "used_questions": set(),
        "votes": {},
        "vote_index": 0,
        "skip_chances": 2,
    })

    def safe_go_home(e=None):
        destroy_min_fina()
        page.views.clear()
        go_home(e)

    def update_ui():
        page.views.clear()
        view = ft.View(route="/min_fina", controls=[], scroll=ft.ScrollMode.AUTO)
        page.views.append(view)

        if state["page"] == "rules":
            view.controls += [
                ft.Text("📜 قوانين لعبة: من فينا؟ 👀", size=28, weight="bold"),
                ft.Text("👥 عدد اللاعبين: من 3 إلى 12", size=20),

                ft.Text("🎯 فكرة اللعبة:", size=22, weight="bold"),
                ft.Text("كل سؤال يبدأ بـ \"من فينا...؟\"، وعلى الجميع التصويت بسرية على اللاعب الذي ينطبق عليه السؤال.", size=18),
                ft.Text("الأسئلة اجتماعية، مضحكة، وأحيانًا محرجة!", size=18),

                ft.Text("🕹 كيفية اللعب:", size=22, weight="bold"),
                ft.Text("1️⃣ يتم عرض سؤال عشوائي على الجميع.", size=18),
                ft.Text("2️⃣ يمكن تخطي السؤال مرتين فقط في كل جولة.", size=18),
                ft.Text("3️⃣ بعد التأكيد، يبدأ كل لاعب بالتصويت بسرية.", size=18),

                ft.Text("📊 النتائج:", size=22, weight="bold"),
                ft.Text("يتم عرض جدول يوضح عدد ونسبة الأصوات لكل لاعب حتى من لم يحصل على أي صوت.", size=18),
                ft.Text("ثم يتم عرض اسم اللاعب أو اللاعبين الذين حصلوا على أعلى نسبة تصويت.", size=18),

                ft.Text("🔁 الجولة التالية:", size=22, weight="bold"),
                ft.Text("بعد كل جولة يمكنك البدء بسؤال جديد أو الرجوع إلى القائمة الرئيسية.", size=18),

                ft.Row([
                    ft.ElevatedButton("🚀 ابدأ اللعبة", on_click=lambda e: go_to_player_count()),
                    ft.ElevatedButton("🏠 العودة للقائمة", on_click=safe_go_home)
                ], alignment="center")
            ]


        elif state["page"] == "player_count":
            view.controls.append(ft.Text("اختر عدد اللاعبين:", size=22))
            view.controls.append(
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: update_num_players(-1)),
                    ft.Text(str(state["num_players"]), size=24),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: update_num_players(1)),
                ], alignment="center")
            )
            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: go_to_input_names()))

        elif state["page"] == "input_names":
            inputs = []
            for i in range(state["num_players"]):
                tf = ft.TextField(label=f"اسم اللاعب {i+1}", autofocus=i == 0)
                inputs.append(tf)
                view.controls.append(tf)

            def save_names(e):
                names = [tf.value.strip() for tf in inputs]
                if len(names) != len(set(names)) or any(n == "" for n in names):
                    page.snack_bar = ft.SnackBar(ft.Text("❗ يجب إدخال أسماء فريدة وغير فارغة"))
                    page.snack_bar.open = True
                    page.update()
                    return
                state["player_names"] = names
                go_to_question()

            view.controls.append(ft.ElevatedButton("ابدأ اللعبة", on_click=save_names))

        elif state["page"] == "question":
            q = state["current_question"]
            view.controls.append(ft.Text("من فينا؟ 👀", size=28, weight="bold"))
            view.controls.append(ft.Text(q, size=22, text_align="center"))
            if state["skip_chances"] > 0:
                view.controls.append(ft.Text(f"لديكم {state['skip_chances']} فرصة لتغيير السؤال", size=16))
                view.controls.append(ft.ElevatedButton("تغيير السؤال", on_click=lambda e: skip_question()))
            else:
                view.controls.append(ft.Text("❌ لا يمكن تغيير السؤال بعد الآن", size=16))
            view.controls.append(ft.ElevatedButton("التصويت", on_click=lambda e: start_voting()))

        elif state["page"] == "voting":
            voter = state["player_names"][state["vote_index"]]
            view.controls.append(ft.Text(f"مرحباً {voter}!", size=22))
            view.controls.append(ft.Text(f"صوّت على:\n{state['current_question']}", size=20))
            for name in state["player_names"]:
                view.controls.append(ft.ElevatedButton(name, on_click=lambda e, n=name: cast_vote(voter, n)))

        elif state["page"] == "results":
            view.controls.append(ft.Text("📊 نتيجة التصويت", size=24, weight="bold"))
            view.controls.append(ft.Text(state["current_question"], size=20))

            # Count votes
            counter = {}
            for name in state["player_names"]:
                counter[name] = 0  # Initialize with 0 votes
            for vote in state["votes"].values():
                counter[vote] += 1

            total_votes = len(state["votes"])
            sorted_results = sorted(counter.items(), key=lambda x: x[1], reverse=True)

            # DataTable format
            view.controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("اللاعب", text_align="right")),
                        ft.DataColumn(ft.Text("عدد الأصوات", text_align="right")),
                        ft.DataColumn(ft.Text("النسبة %", text_align="right")),
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(name)),
                            ft.DataCell(ft.Text(str(count))),
                            ft.DataCell(ft.Text(f"{round((count / total_votes) * 100, 1)}%" if total_votes > 0 else "0%")),
                        ])
                        for name, count in sorted_results
                    ]
                )
            )

            # Announce the most voted
            if total_votes > 0:
                max_votes = sorted_results[0][1]
                most_voted = [name for name, count in sorted_results if count == max_votes and max_votes > 0]
                if most_voted:
                    view.controls.append(ft.Text(f"أغلبية الأصوات لـ {' و '.join(most_voted)}", size=20, weight="bold"))
                else:
                    view.controls.append(ft.Text("🤷‍♂️ لا أحد حصل على أصوات", size=18))
            else:
                view.controls.append(ft.Text("❌ لم يتم التصويت", size=18))

            view.controls.append(ft.Row([
                ft.ElevatedButton("🔁 سؤال جديد", on_click=lambda e: restart_round()),
                ft.ElevatedButton("🏠 العودة للقائمة", on_click=safe_go_home),
            ], alignment="center"))

        page.update()

    def update_num_players(delta):
        state["num_players"] = max(3, min(12, state["num_players"] + delta))
        update_ui()

    def go_to_player_count():
        state["page"] = "player_count"
        update_ui()

    def go_to_input_names():
        state["page"] = "input_names"
        update_ui()

    def go_to_question():
        choose_new_question()
        state["skip_chances"] = 2
        state["page"] = "question"
        update_ui()

    def choose_new_question():
        available = list(set(min_fina_questions) - state["used_questions"])
        if not available:
            state["used_questions"] = set()
            available = list(min_fina_questions)
        state["current_question"] = random.choice(available)
        state["used_questions"].add(state["current_question"])

    def skip_question():
        if state["skip_chances"] > 0:
            state["skip_chances"] -= 1
            choose_new_question()
            update_ui()

    def start_voting():
        state["votes"] = {}
        state["vote_index"] = 0
        state["page"] = "voting"
        update_ui()

    def cast_vote(voter, voted_for):
        state["votes"][voter] = voted_for
        state["vote_index"] += 1
        if state["vote_index"] < len(state["player_names"]):
            update_ui()
        else:
            state["page"] = "results"
            update_ui()

    def restart_round():
        go_to_question()

    update_ui()
    page.on_resized = lambda e: update_ui() if "page" in state else None
