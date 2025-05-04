import flet as ft
import os

# ✅ Add this line to tell Flet where to serve the manifest and icons from
os.environ["FLET_STATIC_DIR"] = "static"

# Lazy imports to improve load time
def load_taboo(page, go_home):
    from taboo_game import taboo_game
    taboo_game(page, go_home)

def load_bara_alsalfa(page, go_home):
    from bara_alsalfa_game import bara_alsalfa_game
    bara_alsalfa_game(page, go_home)

def load_trivia_battle(page, go_home):
    from trivia_battle_game import trivia_battle_game
    trivia_battle_game(page, go_home)

def load_mafia(page, go_home):
    from mafia_game import mafia_game
    mafia_game(page, go_home)

def load_heads_up(page, go_home):
    from heads_up_game import heads_up_game
    heads_up_game(page, go_home)

def main(page: ft.Page):
    page.title = "🎉 ألعابنا"
    page.scroll = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_maximized = True

    def go_home(e=None):
        page.go("/")

    def view_home():
        return ft.View(
            route="/",
            controls=[
                ft.Text("🎮 أهلاً بك في ألعابنا!", size=32, weight="bold", text_align="center"),
                ft.Text("اختر اللعبة التي تريد لعبها:", size=20),
                ft.ElevatedButton("برة السالفة", on_click=lambda _: page.go("/bara_alsalfa")),
                ft.ElevatedButton("تريفيا باتل 🧠", on_click=lambda _: page.go("/trivia_battle")),
                ft.ElevatedButton("مافيا", on_click=lambda _: page.go("/mafia")),
                ft.ElevatedButton("تابو 🕒", on_click=lambda _: page.go("/taboo")),
                ft.ElevatedButton("📱 الجوال على الرأس", on_click=lambda _: page.go("/heads_up")),
            ],
            vertical_alignment="center",
            horizontal_alignment="center",
        )

    def route_change(e):
        route = page.route
        page.views.clear()

        if route == "/":
            page.views.append(view_home())
        elif route == "/taboo":
            page.views.append(ft.View(route="/taboo", controls=[]))
            load_taboo(page, go_home)
        elif route == "/bara_alsalfa":
            page.views.append(ft.View(route="/bara_alsalfa", controls=[]))
            load_bara_alsalfa(page, go_home)
        elif route == "/trivia_battle":
            page.views.append(ft.View(route="/trivia_battle", controls=[]))
            load_trivia_battle(page, go_home)
        elif route == "/mafia":
            page.views.append(ft.View(route="/mafia", controls=[]))
            load_mafia(page, go_home)
        elif route == "/heads_up":
            page.views.append(ft.View(route="/heads_up", controls=[]))
            load_heads_up(page, go_home)

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

ft.app(target=main, port=int(os.environ.get("PORT", 8550)))
