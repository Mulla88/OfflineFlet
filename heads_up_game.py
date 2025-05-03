import flet as ft
import random
import threading
import time
from heads_up_words import HEADS_UP_WORDS

def heads_up_game(page: ft.Page, go_home):
    state = {
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
    }

    word_text = ft.Text(size=40, weight="bold", text_align="center")
    timer_text = ft.Text(size=30, color="red", weight="bold")
    score_text = ft.Text(size=24, color="green")

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
        page.views.clear()
        view = ft.View(route="/heads_up", controls=[], scroll=ft.ScrollMode.AUTO)
        page.views.append(view)
        view.controls.append(ft.Text("✏️ أدخل أسماء اللاعبين:", size=24))
        inputs = []
        for i in range(state["num_players"]):
            tf = ft.TextField(label=f"اسم اللاعب {i+1}")
            inputs.append(tf)
            view.controls.append(tf)
        view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: save_names(e, inputs)))
        view.controls.append(ft.ElevatedButton("🔙 رجوع", on_click=lambda e: set_page("select_players")))
        page.update()

    def set_page(new_page):
        state["page"] = new_page
        update_ui()

    def update_ui():
        page.views.clear()

        if state["page"] == "playing":
            page.window_width = 700
            page.window_height = 300
        else:
            page.window_width = None
            page.window_height = None

        view = ft.View(route="/heads_up", controls=[], horizontal_alignment="center", vertical_alignment="center")
        page.views.append(view)

        if state["page"] == "rules":
            view.controls.append(ft.Text("📜 قوانين لعبة الجوال على الرأس", size=28, weight="bold"))
            view.controls.append(ft.Text("👥 عدد اللاعبين: من 2 إلى 10", size=20))
            view.controls.append(ft.Text("🎯 فكرة اللعبة:", size=22, weight="bold"))
            view.controls.append(ft.Text("كل لاعب يضع الجوال على رأسه، ويحاول تخمين الكلمة الظاهرة بناءً على تلميحات الآخرين.", size=18))
            view.controls.append(ft.Text("🕹 كيفية اللعب:", size=22, weight="bold"))
            view.controls.append(ft.Text("كل لاعب يلعب جولة واحدة مدتها 60 ثانية. يضغط على ✅ إذا خمن الكلمة، أو ⏭ لتخطيها.", size=18))
            view.controls.append(ft.Text("🏁 النتائج:", size=22, weight="bold"))
            view.controls.append(ft.Text("بعد أن يلعب الجميع، تُعرض النقاط ويُعلن الفائز.", size=18))
            view.controls.append(ft.Row([
                ft.ElevatedButton("🚀 ابدأ اللعبة", on_click=lambda e: set_page("select_players")),
                ft.ElevatedButton("🔙 العودة للقائمة", on_click=go_home)
            ], alignment="center"))

        elif state["page"] == "select_players":
            view.controls.append(ft.Text("📱 الجوال على الرأس", size=30, weight="bold"))
            view.controls.append(ft.Text("عدد اللاعبين:", size=18))
            view.controls.append(
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: update_num_players(-1)),
                    ft.Text(f"{state['num_players']}", size=24),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: update_num_players(1)),
                ], alignment="center")
            )
            view.controls.append(ft.ElevatedButton("التالي", on_click=lambda e: set_page("input_players")))

        elif state["page"] == "input_players":
            show_input_names()
            return

        elif state["page"] == "handoff":
            player = state["players"][state["current_index"]]
            view.controls.append(ft.Text(f"📱 أعط الجوال إلى: {player}", size=26, weight="bold"))
            view.controls.append(ft.Text("↪️ تأكد من وضع الجوال بشكل أفقي على الرأس قبل البدء", size=20, color="orange"))
            view.controls.append(ft.ElevatedButton("ابدأ الجولة", on_click=lambda e: start_round()))

        elif state["page"] == "playing":
            view.horizontal_alignment = "stretch"
            view.vertical_alignment = "stretch"
            view.controls += [
                timer_text,
                word_text,
                ft.Column([
                    ft.Row([
                        ft.ElevatedButton("✅ صحيح", on_click=handle_correct, visible=True),
                        ft.ElevatedButton("⏭ تخطي", on_click=next_word, visible=True)
                    ], alignment="center"),
                    ft.Row([
                        ft.ElevatedButton("⏹ إنهاء الجولة", on_click=end_round, visible=True)
                    ], alignment="center")
                ], alignment="center"),
                score_text,
            ]

        elif state["page"] == "summary":
            player = state["players"][state["current_index"]]
            view.controls.append(ft.Text(f"⏰ انتهى الوقت! {player}", size=24, weight="bold"))
            view.controls.append(ft.Text(f"✅ النقاط: {state['score']}", size=22))
            view.controls.append(ft.ElevatedButton("▶ اللاعب التالي", on_click=lambda e: next_player()))

        elif state["page"] == "final_results":
            view.controls.append(ft.Text("🏁 انتهت اللعبة!", size=28, weight="bold"))
            view.controls.append(ft.Text("📊 النتائج النهائية:", size=22))
            sorted_scores = sorted(state["player_scores"].items(), key=lambda x: x[1], reverse=True)
            for name, score in sorted_scores:
                view.controls.append(ft.Text(f"{name}: {score} نقطة", size=20))
            view.controls.append(ft.Row([
                ft.ElevatedButton("🔁 العب مرة أخرى", on_click=lambda e: restart_game()),
                ft.ElevatedButton("🏠 القائمة الرئيسية", on_click=go_home)
            ], alignment="center"))

        view.controls.append(ft.ElevatedButton("🔙 رجوع", on_click=go_home))
        page.update()

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
        player = state["players"][state["current_index"]]
        state["player_scores"][player] = state["score"]
        state["playing"] = False
        state["stop_timer_event"].set()
        if state["current_index"] + 1 >= len(state["players"]):
            state["page"] = "final_results"
        else:
            state["page"] = "summary"
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
        next_word()
        update_ui()
        start_timer()

    def next_player():
        state["current_index"] += 1
        if state["current_index"] >= len(state["players"]):
            state["page"] = "final_results"
        else:
            state["page"] = "handoff"
        update_ui()

    def restart_game():
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
        update_ui()

    update_ui()
    page.on_resized = lambda e: update_ui()
