import flet as ft
import random
import threading
import time
from taboo_words import WORD_BANK

def taboo_game(page: ft.Page, go_home):
    state = {
        "teams": [],
        "scores": {},
        "current_team_index": 0,
        "used_words": [],
        "word_log": [],
        "current_word": None,
        "team_inputs": [],
        "game_started": False,
        "round": 1,
        "step": "rules",
        "stop_timer_event": threading.Event()
    }

    team_name_fields = []
    word_display = ft.Column(visible=False)
    score_display = ft.Column(visible=False)
    correct_btn = ft.ElevatedButton("✅ إجابة صحيحة", visible=False)
    skip_btn = ft.ElevatedButton("⏭ تخطي / ممنوعة", visible=False)
    end_round_btn = ft.ElevatedButton("⏹ إنهاء الجولة", visible=False)
    timer_text = ft.Text(size=30, weight="bold")
    last_round_warning = ft.Text("", size=20, color="red", visible=False)

    def get_new_word():
        remaining = [w for w in WORD_BANK if w["secret"] not in state["used_words"]]
        if not remaining:
            return None
        word = random.choice(remaining)
        state["used_words"].append(word["secret"])
        return word

    def update_word_display():
        word_display.controls.clear()
        word = state["current_word"]
        if word:
            word_display.controls.append(ft.Text(f"الكلمة السرية: {word['secret']}", size=28, weight="bold", color="green"))
            word_display.controls.append(ft.Text("❌ الكلمات الممنوعة:", size=22))
            for w in word["forbidden"]:
                word_display.controls.append(ft.Text(f"- {w}", size=20, color="red"))

    def update_score_display():
        score_display.controls = [ft.Text(f"{team}: {score}", size=20) for team, score in state["scores"].items()]

    def end_round(e=None):
        state["stop_timer_event"].set()
        correct_btn.visible = False
        skip_btn.visible = False
        end_round_btn.visible = False
        word_display.visible = False
        last_round_warning.visible = False

        team = state["teams"][state["current_team_index"]]
        round_words = [log for log in state["word_log"] if log["team"] == team and log["round"] == state["round"]]

        summary = ft.Column(
            controls=[
                ft.Text(f"⏰ انتهى الوقت! الفريق: {team}", size=24, weight="bold", color="red"),
                ft.Text("🔤 الكلمات التي ظهرت:", size=20)
            ] + [
                ft.Text(f"- {log['word']} ({'✔' if log['correct'] else '✘'})", color="green" if log["correct"] else "red")
                for log in round_words
            ],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )

        def next_team(e):
            state["current_team_index"] += 1
            if state["current_team_index"] >= len(state["teams"]):
                state["current_team_index"] = 0
                state["round"] += 1
            start_round()

        page.views[-1].controls.clear()
        page.views[-1].controls.append(summary)
        page.views[-1].controls.append(ft.ElevatedButton("▶ الفريق التالي", on_click=next_team))
        page.update()

    def start_timer():
        state["stop_timer_event"].clear()

        def run():
            for i in range(60, 0, -1):
                if state["stop_timer_event"].is_set():
                    return
                timer_text.value = f"⏳ الوقت المتبقي: {i} ثانية"
                page.update()
                time.sleep(1)
            if not state["stop_timer_event"].is_set():
                timer_text.value = "انتهى الوقت!"
                page.update()
                end_round()

        threading.Thread(target=run, daemon=True).start()

    def start_round():
        if state["round"] > 3:
            page.views[-1].controls.clear()
            page.views[-1].controls.append(ft.Text("🏁 انتهت اللعبة! النتائج النهائية:", size=24, weight="bold"))
            update_score_display()
            page.views[-1].controls.append(score_display)
            page.views[-1].controls.append(ft.ElevatedButton("🏠 العودة للرئيسية", on_click=go_home))
            page.views[-1].controls.append(ft.ElevatedButton("🔄 العب مرة أخرى", on_click=reset_game))
            page.update()
            return

        view = page.views[-1]
        view.controls.clear()
        current_team = state["teams"][state["current_team_index"]]

        if state["round"] == 3:
            last_round_warning.value = "⚠️ هذا هو الدور الأخير!"
            last_round_warning.visible = True
        else:
            last_round_warning.visible = False

        state["current_word"] = get_new_word()
        update_word_display()
        update_score_display()

        word_display.visible = True
        correct_btn.visible = True
        skip_btn.visible = True
        end_round_btn.visible = True
        score_display.visible = True

        view.controls += [
            ft.Text(f"🎮 الجولة {state['round']} - الفريق: {current_team}", size=22, color="blue"),
            last_round_warning,
            timer_text,
            word_display,
            ft.Column([
                ft.Row([correct_btn, skip_btn], alignment="center"),
                ft.Row([end_round_btn], alignment="center")
            ], alignment="center"),
            ft.Text("📊 النقاط:", size=20),
            score_display,
            ft.ElevatedButton("🔙 الرجوع للرئيسية", on_click=go_home)
        ]
        page.update()
        start_timer()

    def handle_correct(e):
        team = state["teams"][state["current_team_index"]]
        state["scores"][team] += 1
        state["word_log"].append({"team": team, "word": state["current_word"]["secret"], "correct": True, "round": state["round"]})
        state["current_word"] = get_new_word()
        update_word_display()
        update_score_display()
        page.update()

    def handle_skip(e):
        team = state["teams"][state["current_team_index"]]
        state["scores"][team] -= 0.5
        state["word_log"].append({"team": team, "word": state["current_word"]["secret"], "correct": False, "round": state["round"]})
        state["current_word"] = get_new_word()
        update_word_display()
        update_score_display()
        page.update()

    def start_game(e):
        state["teams"] = [field.value.strip() for field in team_name_fields if field.value.strip()]
        if len(state["teams"]) < 2:
            page.snack_bar = ft.SnackBar(ft.Text("❗ أدخل على الأقل اسمين لفريقين."))
            page.snack_bar.open = True
            page.update()
            return

        state["scores"] = {team: 0 for team in state["teams"]}
        state["game_started"] = True
        start_round()

    def reset_game(e):
        state.update({
            "teams": [],
            "scores": {},
            "current_team_index": 0,
            "used_words": [],
            "word_log": [],
            "current_word": None,
            "team_inputs": [],
            "game_started": False,
            "round": 1,
            "step": "rules",
            "stop_timer_event": threading.Event()
        })
        build_ui()

    def build_ui():
        page.views.clear()
        view = ft.View(route="/taboo", controls=[], scroll=ft.ScrollMode.AUTO)
        page.views.append(view)

        if state["step"] == "rules":
            view.controls += [
                ft.Text("📜 قوانين لعبة تابو", size=28, weight="bold"),
                ft.Text("👥 عدد الفرق: فريقان ", size=20),
                ft.Text("🎯 فكرة اللعبة:", size=22, weight="bold"),
                ft.Text("يصف أحد أعضاء الفريق الكلمة السرية بدون استخدام الكلمات الممنوعة.", size=18),
                ft.Text("🕹 كيفية اللعب:", size=22, weight="bold"),
                ft.Text("كل فريق يلعب لمدة 60 ثانية في الجولة.", size=18),
                ft.Text("كل كلمة ممنوعة أو تخطي = -0.5 نقطة", size=18),
                ft.Text("كل إجابة صحيحة = +1 نقطة", size=18),
                ft.Text("🏁 النتيجة:", size=22, weight="bold"),
                ft.Text("اللعبة تتكون من 3 جولات لكل فريق. الفريق ذو أعلى نقاط يفوز.", size=18),
                ft.Row([
                    ft.ElevatedButton("🚀 ابدأ", on_click=lambda e: begin_input()),
                    ft.ElevatedButton("🔙 العودة", on_click=go_home)
                ], alignment="center")
            ]
        else:
            if not state["game_started"]:
                view.controls.append(ft.Text("🎯 لعبة تابو", size=32, weight="bold"))
                view.controls.append(ft.Text("👥 أدخل أسماء الفرق:", size=22))
                team_name_fields.clear()
                for i in range(2):
                    tf = ft.TextField(label=f"اسم الفريق {i+1}", width=300)
                    team_name_fields.append(tf)
                    view.controls.append(tf)
                view.controls.append(ft.ElevatedButton("🚀 ابدأ اللعبة", on_click=start_game))
                view.controls.append(ft.ElevatedButton("🔙 الرجوع للرئيسية", on_click=go_home))

        page.update()

    def begin_input():
        state["step"] = "input_teams"
        build_ui()

    correct_btn.on_click = handle_correct
    skip_btn.on_click = handle_skip
    end_round_btn.on_click = end_round

    build_ui()
