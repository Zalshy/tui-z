import pytest
from helpers import plain

from tui_z import THEME_NAMES, Button, Checkbox, Input, RadioGroup, Select, Switch, Text, ThemeSwitcher, TwApp


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


# -- toggles --------------------------------------------------------------------

class Toggles(TwApp):
    def __init__(self) -> None:
        super().__init__()
        self.changes: list[tuple[str, object]] = []

    def compose(self):
        yield Checkbox("Copy trades", id="c")
        yield Switch("Live", True, id="s")
        yield RadioGroup(["Kelly", "Fixed", "Off"], id="r")
        yield Checkbox("Off limits", disabled=True, id="d")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.changes.append(("checkbox", event.value))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.changes.append(("switch", event.value))

    def on_radio_group_changed(self, event: RadioGroup.Changed) -> None:
        self.changes.append(("radio", event.value))


async def test_checkbox_and_switch_toggle_by_click_and_keys():
    app = Toggles()
    async with app.run_test() as pilot:
        c, s = app.query_one("#c", Checkbox), app.query_one("#s", Switch)
        assert plain(c) == "[ ] Copy trades" and plain(s) == "━━● Live"
        await pilot.click(c)
        s.focus()
        await pilot.press("space")
        await pilot.press("enter")
        await pilot.pause()
        assert c.value and s.value
        assert plain(c) == "[✓] Copy trades"
        assert app.changes == [("checkbox", True), ("switch", False), ("switch", True)]


async def test_disabled_toggle_ignores_clicks():
    app = Toggles()
    async with app.run_test() as pilot:
        d = app.query_one("#d", Checkbox)
        await pilot.click(d)
        await pilot.pause()
        assert not d.value


async def test_radio_group_arrows_and_clicks():
    app = Toggles()
    async with app.run_test() as pilot:
        r = app.query_one("#r", RadioGroup)
        assert plain(r).split("\n") == ["◉ Kelly", "○ Fixed", "○ Off"]
        r.focus()
        await pilot.press("down")
        await pilot.press("up", "up")  # wraps around
        await pilot.click(r, offset=(2, 1))
        await pilot.pause()
        assert r.index == 1 and r.value == "Fixed"
        assert app.changes == [("radio", "Fixed"), ("radio", "Kelly"), ("radio", "Off"), ("radio", "Fixed")]


def test_radio_group_validates():
    with pytest.raises(ValueError, match="option"):
        RadioGroup([])
    assert RadioGroup(["a", "b"], value=9).index == 1


# -- Input / Select ----------------------------------------------------------------

class Form(TwApp):
    def __init__(self) -> None:
        super().__init__()
        self.submitted: list[str] = []
        self.selected: list[object] = []

    def compose(self):
        yield Input("", "w-30", placeholder="Search", id="i")
        yield Select([("Macro", "macro"), ("Crypto", "crypto")], "w-30", prompt="Category", id="sel")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submitted.append(event.value)

    def on_select_changed(self, event: Select.Changed) -> None:
        self.selected.append(event.value)


async def test_input_types_submits_and_restyles_on_focus():
    app = Form()
    async with app.run_test() as pilot:
        field = app.query_one("#i", Input)
        app.query_one("#sel").focus()  # the app focuses the input on start
        await pilot.pause()
        blurred = field.styles.border_top[1]
        field.focus()
        await pilot.pause()
        assert field.styles.border_top[1] != blurred  # focus:border-primary
        await pilot.press(*"btc", "enter")
        assert app.submitted == ["btc"]


async def test_select_styles_its_parts_and_selects():
    app = Form()
    async with app.run_test() as pilot:
        select = app.query_one("#sel", Select)
        current = select.query_one("SelectCurrent")
        assert current._tw_compiled is not None  # styled by tw()
        before = current.styles.border_top[1]
        select.focus()
        await pilot.pause()
        assert current.styles.border_top[1] != before  # group-focus:border-primary
        await pilot.press("enter", "down", "enter")
        await pilot.pause()
        assert select.value == "macro" and app.selected[-1] == "macro"
