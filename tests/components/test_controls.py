from helpers import plain

from tui_z import THEME_NAMES, Button, Text, ThemeSwitcher, TwApp


class Pressed(TwApp):
    def __init__(self) -> None:
        super().__init__()
        self.presses: list[Button] = []

    def compose(self):
        yield Button("buy yes", "text-success", id="b")
        yield Text("x", "text-purple bg-panel border border-line", id="t")
        yield ThemeSwitcher(id="switcher")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.presses.append(event.control)


async def test_button_press_by_click_enter_and_space():
    app = Pressed()
    async with app.run_test() as pilot:
        button = app.query_one("#b", Button)
        assert button.label == "buy yes" and plain(button) == "BUY YES"
        await pilot.click(button)
        button.focus()
        await pilot.press("enter", "space")
        await pilot.pause()
        assert app.presses == [button] * 3


async def test_switcher_follows_and_sets_the_theme():
    app = Pressed()
    async with app.run_test() as pilot:
        switcher = app.query_one(ThemeSwitcher)
        app.action_prev_theme()
        await pilot.pause()
        active = [i for i in switcher.items if "●" in plain(i)]
        assert [i.theme_name for i in active] == [THEME_NAMES[-1]]
        await pilot.click(switcher.items[2])
        await pilot.pause()
        assert app.theme == THEME_NAMES[2]


async def test_switcher_with_a_subset_of_themes(mount):
    switcher = ThemeSwitcher(["tokyo-night", "amber"], cls="row")
    async with mount(switcher):
        assert [i.theme_name for i in switcher.items] == ["tokyo-night", "amber"]
