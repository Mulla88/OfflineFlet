import flet as ft
import random
from categories import categories
from flet import Colors

state = {}

def destroy_bara_alsalfa():
    state.clear()

def bara_alsalfa_game(page: ft.Page, go_home):
    destroy_bara_alsalfa()
    page.on_resized = None

    state.update({
        "page": "rules",
        "num_players": 3,
        "player_names": [],
        "selected_category": None,
        "bara_player": None,
        "game_word": None,
        "roles": {},
        "question_pairs": [],
        "current_pair_index": 0,
        "votes": {},
        "vote_index": 0,
        "round_scores": {},
        "global_scores": {},
        "guess_word_options": [],
        "guess_result": "",
        "scores_added": False,
        "role_index": 0,
        "used_words": set()
    })

    def safe_go_home(e=None):
        destroy_bara_alsalfa()
        page.views.clear()
        go_home(e)

    def update_ui():
        if "page" not in state:
            return  # Avoid error if state cleared during resize
        page.views.clear()
        view = ft.View(route="/bara_alsalfa", controls=[], scroll=ft.ScrollMode.AUTO, vertical_alignment="center")
        page.views.append(view)

        if state["page"] == "home":
            view.controls.append(ft.Text("🎮 برا السالفة", size=30, weight="bold"))
            view.controls.append(ft.Text("عدد اللاعبين:", size=18))
            view.controls.append(
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: update_num_players(-1)),
                    ft.Text(f"{state['num_players']}", size=24),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: update_num_players(1)),
                ])
            )
            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: go_to_input_names()))

        elif state["page"] == "input_players":
            inputs = []
            for i in range(state["num_players"]):
                tf = ft.TextField(label=f"اسم اللاعب {i+1}", autofocus=i == 0)
                inputs.append(tf)
                view.controls.append(tf)

            def save_names(e):
                names = [tf.value.strip() for tf in inputs]
                if len(names) != len(set(names)) or any(n == "" for n in names):
                    page.snack_bar = ft.SnackBar(ft.Text("❗ أسماء اللاعبين يجب أن تكون فريدة ومملوءة"))
                    page.snack_bar.open = True
                    page.update()
                    return
                state["player_names"] = names
                state["global_scores"] = {p: 0 for p in names}
                state["round_scores"] = {p: 0 for p in names}
                state["page"] = "select_category"
                update_ui()

            view.controls.append(ft.ElevatedButton("التالي", on_click=save_names))

        elif state["page"] == "select_category":
            dd = ft.Dropdown(options=[ft.dropdown.Option(k) for k in categories.keys()], width=300)

            def confirm_category(e):
                if dd.value:
                    state["selected_category"] = dd.value
                    assign_roles_and_word()

            view.controls += [
                ft.Text("اختر القائمة:", size=20),
                dd,
                ft.ElevatedButton("تأكيد", on_click=confirm_category)
            ]

        elif state["page"] == "show_role":
            current = state["player_names"][state["role_index"]]
            view.controls += [
                ft.Text(f"📱 أعطِ الجوال إلى: {current}", size=24),
                ft.ElevatedButton("👁️ عرض الدور", on_click=lambda e: set_display_role())
            ]

        elif state["page"] == "display_role":
            current = state["player_names"][state["role_index"]]
            role = state["roles"][current]
            category = state["selected_category"]
            view.controls.append(ft.Text(f"🎭 {current}، دورك هو: {role}", size=22))
            view.controls.append(ft.Text(f"📂 القائمة: {category}", size=18))
            if role == "داخل السالفة":
                view.controls.append(ft.Text(f"الكلمة السرية: {state['game_word']}", size=22, color="green"))
            view.controls.append(
                ft.Row([
                    ft.ElevatedButton("التالي", on_click=next_player),
                    ft.ElevatedButton("تغيير الكلمة", on_click=lambda e: assign_roles_and_word(), style=ft.ButtonStyle(bgcolor=Colors.RED, color=Colors.WHITE))
                ], alignment="center")
            )

        elif state["page"] == "rules":
            view.controls += [
                ft.Text("📜 قوانين لعبة برا السالفة", size=28, weight="bold"),
                ft.Text("👥 عدد اللاعبين: من 3 إلى 15", size=20),
                ft.Text("🎯 فكرة اللعبة:", size=22, weight="bold"),
                ft.Text("أحد اللاعبين لا يعرف الكلمة (برة السالفة)، بينما البقية يعرفونها.", size=18),
                ft.Text("🕹 كيفية اللعب:", size=22, weight="bold"),
                ft.Text("اللاعبون يتبادلون الأسئلة لمحاولة كشف من هو برة السالفة، ثم يصوتون عليه.", size=18),
                ft.Text("بعد التصويت، يحاول اللاعب المشتبه به تخمين الكلمة السرية.", size=18),
                ft.Text("🏁 النتيجة:", size=22, weight="bold"),
                ft.Text("نقاط تُمنح لمن يخمن برة السالفة بشكل صحيح، و10 نقاط إذا خمن برة السالفة الكلمة.", size=18),
                ft.Row([
                    ft.ElevatedButton("🚀 ابدأ اللعبة", on_click=lambda e: go_to_home()),
                ], alignment="center")
            ]


        elif state["page"] == "question_or_vote":
            view.controls.append(ft.Text("ماذا تريد أن تفعل الآن؟", size=24))
            view.controls.append(ft.ElevatedButton("🎤 بدء جولة أسئلة", on_click=lambda e: start_questions()))
            view.controls.append(ft.ElevatedButton("🗳 بدء التصويت", on_click=lambda e: start_voting()))

        elif state["page"] == "question_time":
            if state["current_pair_index"] < len(state["question_pairs"]):
                pair = state["question_pairs"][state["current_pair_index"]]
                view.controls.append(ft.Text(f"🗣️ {pair[0]} اسأل {pair[1]}", size=22))
                view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: advance_questions()))
            else:
                state["page"] = "question_or_vote"
                update_ui()
                return

        elif state["page"] == "voting":
            voter = state["player_names"][state["vote_index"]]
            view.controls.append(ft.Text(f"🗳 {voter} يصوت الآن. اختر من تعتقد أنه برة السالفة:", size=22))
            for candidate in state["player_names"]:
                if candidate != voter:
                    view.controls.append(ft.ElevatedButton(candidate, on_click=lambda e, c=candidate: cast_vote(voter, c)))

        elif state["page"] == "voting_results":
            view.controls.append(ft.Text("نتائج التصويت", size=24, weight="bold"))

            # Voting result table
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("صوّت ضد", text_align="right")),
                    ft.DataColumn(ft.Text("اللاعب", text_align="right")),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(vote, text_align="right")),
                            ft.DataCell(ft.Text(voter, text_align="right")),
                        ]
                    )
                    for voter, vote in state["votes"].items()
                ]
            )

            view.controls.append(table)

            view.controls.append(ft.Divider(height=10))
            view.controls.append(ft.Text(f"🎭 برة السالفة كان: {state['bara_player']}", size=20, color="red"))

            correct_voters = [player for player, voted in state["votes"].items() if voted == state["bara_player"]]
            if correct_voters:
                view.controls.append(ft.Text(":حصلوا على 5 نقاط", size=18))
                for player in correct_voters:
                    state["round_scores"][player] += 5
                    view.controls.append(ft.Text(f"- {player}", size=16))
            else:
                view.controls.append(ft.Text("❌ لم يخمن أحد بشكل صحيح", size=16))

            view.controls.append(ft.ElevatedButton("تخمين الكلمة السرية", on_click=lambda e: prepare_guess_phase()))


        elif state["page"] == "guess_word":
            view.controls.append(ft.Text(f"🎯 {state['bara_player']}, خمن الكلمة السرية", size=22))
            for word in state["guess_word_options"]:
                view.controls.append(ft.ElevatedButton(word, on_click=lambda e, w=word: handle_guess(w)))

        elif state["page"] == "total_scores":
            if not state["scores_added"]:
                for p, s in state["round_scores"].items():
                    state["global_scores"][p] += s
                state["scores_added"] = True
            view.controls.append(ft.Text(state["guess_result"], size=22))
            view.controls.append(ft.Text("📊 النقاط الكلية:", size=20))
            for p, s in state["global_scores"].items():
                view.controls.append(ft.Text(f"{p}: {s} نقطة"))
            view.controls.append(ft.ElevatedButton("🔄 جولة جديدة", on_click=lambda e: restart_round()))

        view.controls.append(ft.ElevatedButton("🏠 العودة للرئيسية", on_click=safe_go_home))
        page.update()

    def update_num_players(change):
        state["num_players"] = max(3, min(15, state["num_players"] + change))
        update_ui()

    def go_to_input_names():
        state["page"] = "input_players"
        update_ui()

    def set_display_role():
        state["page"] = "display_role"
        update_ui()

    def assign_roles_and_word():
        available_words = [w for w in categories[state["selected_category"]] if w not in state["used_words"]]
        if not available_words:
            state["used_words"] = set()
            available_words = categories[state["selected_category"]]
        state["game_word"] = random.choice(available_words)
        state["used_words"].add(state["game_word"])
        state["bara_player"] = random.choice(state["player_names"])
        state["roles"] = {
            p: "برة السالفة" if p == state["bara_player"] else "داخل السالفة"
            for p in state["player_names"]
        }
        state["role_index"] = 0
        state["page"] = "show_role"
        update_ui()

    def next_player(e=None):
        if state["role_index"] + 1 < len(state["player_names"]):
            state["role_index"] += 1
            state["page"] = "show_role"
        else:
            state["page"] = "question_or_vote"
        update_ui()

    def start_questions():
        players = state["player_names"].copy()
        random.shuffle(players)
        state["question_pairs"] = [(players[i], players[(i+1)%len(players)]) for i in range(len(players))]
        state["current_pair_index"] = 0
        state["page"] = "question_time"
        update_ui()

    def advance_questions():
        state["current_pair_index"] += 1
        update_ui()

    def start_voting():
        state["vote_index"] = 0
        state["votes"] = {}
        state["page"] = "voting"
        update_ui()

    def go_to_home():
        state["page"] = "home"
        update_ui()


    def cast_vote(voter, voted_for):
        state["votes"][voter] = voted_for
        state["vote_index"] += 1
        if state["vote_index"] < len(state["player_names"]):
            update_ui()
        else:
            state["page"] = "voting_results"
            update_ui()

    def prepare_guess_phase():
        words = [w for w in categories[state["selected_category"]] if w != state["game_word"]]
        options = random.sample(words, min(7, len(words)))
        options.append(state["game_word"])
        random.shuffle(options)
        state["guess_word_options"] = options
        state["page"] = "guess_word"
        update_ui()

    def handle_guess(word):
        if word == state["game_word"]:
            state["round_scores"][state["bara_player"]] += 10
            state["guess_result"] = "✅ صحيح! حصلت على 10 نقاط."
        else:
            state["guess_result"] = "❌ خطأ! لم تخمن الكلمة السرية."
        state["page"] = "total_scores"
        update_ui()

    def restart_round():
        state.update({
            "current_pair_index": 0,
            "votes": {},
            "vote_index": 0,
            "round_scores": {p: 0 for p in state["player_names"]},
            "guess_result": "",
            "scores_added": False,
            "role_index": 0,
            "page": "select_category"
        })
        update_ui()

    update_ui()
    page.on_resized = lambda e: update_ui() if "page" in state else None
