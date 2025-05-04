import flet as ft
import random
import threading
import time
from heads_up_words import HEADS_UP_WORDS

def heads_up_game(page: ft.Page, go_home):
    state = {}

    word_text = ft.Text(size=40, weight="bold", text_align="center")
    timer_text = ft.Text(size=30, color="red", weight="bold")
    score_text = ft.Text(size=24, color="green")
    team_name_fields = []

    def initialize_state():
        state.clear()
        state.update({
            "num_players": 2,
            "players": [],
            "current_index": 0,
            "playing": False,
            "words_used": [],
            "score": 0,
            "player_scores": {},
            "current_word": "",
            "page": "rules",
            "stop_timer_event": threading.Event()
        })

    def cleanup_and_go_home(e=None):
        if "stop_timer_event" in state:
            state["stop_timer_event"].set()
        state.clear()
        page.views.clear()
        go_home(e)

    def update_num_players(delta):
        state["num_players"] = max(2, min(10, state["num_players"] + delta))
        update_ui()

    def save_names(e, inputs):
        names = [tf.value.strip() for tf in inputs]
        if len(names) != len(set(names)) or any(n == "" for n in names):
            page.snack_bar = ft.SnackBar(ft.Text("❗ أسماء اللاعبين غير صالحة"))
            page.snack_bar.open = True
            page.update()
            return
        state["players"] = names
        state["page"] = "handoff"
        update_ui()

    def show_input_names():
        inputs = [ft.TextField(label=f"اسم اللاعب {i+1}", expand=True) for i in range(state["num_players"])]
        content = [
            ft.Text("✏️ أدخل أسماء اللاعبين:", size=24),
            *inputs,
            ft.ElevatedButton("التالي", on_click=lambda e: save_names(e, inputs)),
            ft.ElevatedButton("🔙 رجوع", on_click=lambda e: set_page("select_players"))
        ]
        set_view(content)

    def set_page(new_page):
        state["page"] = new_page
        update_ui()

    def set_view(controls):
        page.views.clear()
        view = ft.View(
            route="/heads_up",
            controls=controls,
            horizontal_alignment="center",
            vertical_alignment="center",
            scroll=ft.ScrollMode.ADAPTIVE
        )
        page.views.append(view)
        page.update()

    def update_ui():
        if "page" not in state:
            return

        if state["page"] == "rules":
            set_view([
                ft.Text("📜 قوانين لعبة الجوال على الرأس", size=28, weight="bold"),
                ft.Text("👥 عدد اللاعبين: من 2 إلى 10", size=20),
                ft.Text("🎯 فكرة اللعبة:", size=22, weight="bold"),
                ft.Text("كل لاعب يضع الجوال على رأسه، ويحاول تخمين الكلمة الظاهرة بناءً على تلميحات الآخرين.", size=18),
                ft.Text("🕹 كيفية اللعب:", size=22, weight="bold"),
                ft.Text("كل لاعب يلعب جولة واحدة مدتها 60 ثانية. يضغط على ✅ إذا خمن الكلمة، أو ⏭ لتخطيها.", size=18),
                ft.Text("🏁 النتائج:", size=22, weight="bold"),
                ft.Text("بعد أن يلعب الجميع، تُعرض النقاط ويُعلن الفائز.", size=18),
                ft.Row([
                    ft.ElevatedButton("🚀 ابدأ اللعبة", on_click=lambda e: set_page("select_players")),
                    ft.ElevatedButton("🏠 العودة للقائمة", on_click=cleanup_and_go_home)
                ], alignment="center")
            ])
        elif state["page"] == "select_players":
            set_view([
                ft.Text("📱 الجوال على الرأس", size=30, weight="bold"),
                ft.Text("عدد اللاعبين:", size=18),
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: update_num_players(-1)),
                    ft.Text(f"{state['num_players']}", size=24),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: update_num_players(1)),
                ], alignment="center"),
                ft.ElevatedButton("التالي", on_click=lambda e: set_page("input_players"))
            ])
        elif state["page"] == "input_players":
            show_input_names()
        elif state["page"] == "handoff":
            player = state["players"][state["current_index"]]
            set_view([
                ft.Text(f"📱 أعط الجوال إلى: {player}", size=26, weight="bold"),
                ft.Text("↪️ تأكد من وضع الجوال بشكل أفقي على الرأس قبل البدء", size=20, color="orange"),
                ft.ElevatedButton("ابدأ الجولة", on_click=lambda e: start_round())
            ])
        elif state["page"] == "playing":
            set_view([
                timer_text,
                word_text,
                ft.Row([
                    ft.ElevatedButton("✅ صحيح", on_click=handle_correct),
                    ft.ElevatedButton("⏭ تخطي", on_click=next_word)
                ], alignment="center"),
                ft.Row([
                    ft.ElevatedButton("⏹ إنهاء الجولة", on_click=end_round)
                ], alignment="center"),
                score_text
            ])
        elif state["page"] == "summary":
            player = state["players"][state["current_index"]]
            set_view([
                ft.Text(f"⏰ انتهى الوقت! {player}", size=24, weight="bold"),
                ft.Text(f"✅ النقاط: {state['score']}", size=22),
                ft.ElevatedButton("▶ اللاعب التالي", on_click=lambda e: next_player())
            ])
        elif state["page"] == "final_results":
            results = [
                ft.Text("🏁 انتهت اللعبة!", size=28, weight="bold"),
                ft.Text("📊 النتائج النهائية:", size=22)
            ]
            for name, score in sorted(state["player_scores"].items(), key=lambda x: x[1], reverse=True):
                results.append(ft.Text(f"{name}: {score} نقطة", size=20))
            results += [
                ft.Row([
                    ft.ElevatedButton("🔁 العب مرة أخرى", on_click=lambda e: restart_game()),
                    ft.ElevatedButton("🏠 القائمة الرئيسية", on_click=cleanup_and_go_home)
                ], alignment="center")
            ]
            set_view(results)

    def get_new_word():
        unused = [w for w in HEADS_UP_WORDS if w not in state["words_used"]]
        if not unused:
            return "انتهت الكلمات!"
        word = random.choice(unused)
        state["words_used"].append(word)
        return word

    def next_word(e=None):
        state["current_word"] = get_new_word()
        word_text.value = state["current_word"]
        page.update()

    def handle_correct(e=None):
        state["score"] += 1
        score_text.value = f"النقاط: {state['score']}"
        next_word()

    def end_round(e=None):
        if state.get("playing"):
            player = state["players"][state["current_index"]]
            state["player_scores"][player] = state["score"]
            state["playing"] = False
            state["stop_timer_event"].set()
            state["page"] = "final_results" if state["current_index"] + 1 >= len(state["players"]) else "summary"
            update_ui()

    def start_timer():
        state["stop_timer_event"].clear()

        def run():
            for i in range(60, 0, -1):
                if state["stop_timer_event"].is_set():
                    return
                timer_text.value = f"الوقت المتبقي: {i} ثانية"
                page.update()
                time.sleep(1)
            if not state["stop_timer_event"].is_set():
                timer_text.value = "انتهى الوقت!"
                page.update()
                end_round()

        threading.Thread(target=run, daemon=True).start()

    def start_round():
        state["stop_timer_event"].set()
        state["playing"] = True
        state["page"] = "playing"
        state["score"] = 0
        state["words_used"] = []
        score_text.value = ""
        next_word()
        update_ui()
        start_timer()

    def next_player():
        state["current_index"] += 1
        state["page"] = "final_results" if state["current_index"] >= len(state["players"]) else "handoff"
        update_ui()

    def restart_game():
        initialize_state()
        update_ui()

    # Initialize the game and UI
    initialize_state()
    update_ui()
    page.on_resized = lambda e: update_ui()
