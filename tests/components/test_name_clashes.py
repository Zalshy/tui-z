"""tui-z components that share a name with a Textual widget.

Textual matches CSS type selectors by class name, so once an app also uses
Textual's `Button`, its `Button { ... }` default CSS applies to tui-z's
`Button` too. Their DEFAULT_CLS sets every property that CSS touches; these
tests mount both and check nothing leaks.
"""

import pytest
from textual import widgets as tx
from textual.notifications import Notification
from textual.widgets._toast import Toast as TextualToast  # not exported; imported only to load its CSS

from tui_z import Button, Checkbox, Switch, Toast, TwApp

CASES = [
    (lambda: Button("go"), lambda: tx.Button("x")),
    (lambda: Switch("live", True), tx.Switch),
    (lambda: Checkbox("copy"), lambda: tx.Checkbox("x")),
    (lambda: Toast("hi", timeout=None), lambda: TextualToast(Notification("x", "", "information", 60))),
]


def look(widget):
    s = widget.styles
    return (widget.outer_size, s.background, s.padding, tuple(s.border), s.min_width, s.line_pad)


async def render(ours, theirs=None):
    class App(TwApp):
        def compose(self):
            yield ours
            if theirs is not None:
                yield theirs

    app = App()
    async with app.run_test(size=(80, 20)) as pilot:
        await pilot.pause()
        return look(ours)


@pytest.mark.parametrize(("ours", "theirs"), CASES, ids=["Button", "Switch", "Checkbox", "Toast"])
async def test_textual_css_for_the_same_name_does_not_leak(ours, theirs):
    assert await render(ours(), theirs()) == await render(ours())
