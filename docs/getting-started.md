# Getting started

## Install

```bash
uv add git+https://github.com/Zalshy/tui-z
# or
pip install git+https://github.com/Zalshy/tui-z
```

tui-z needs Python 3.12+ and installs [Textual](https://textual.textualize.io) as its only dependency. It helps to know some Textual (apps, `compose`, events), but you don't need to know Textual CSS.

## Your first app

```python
from tui_z import TwApp, Panel, Row, Text, Badge, Bar

class Hello(TwApp):
    def compose(self):
        yield Panel(
            Row(Text("Build status", "bold grow"), Badge("passing", cls="bg-success/20 text-success")),
            Bar(0.82, "text-success"),
            title="CI",
            cls="w-50 m-1",
        )

if __name__ == "__main__":
    Hello().run()
```

- `TwApp` replaces `textual.app.App`. It registers the themes and compiles your class strings.
- Every widget takes `cls`. The second positional argument of `Text`, `Bar`, `Sparkline` and `LineChart` is `cls`. The containers take `cls=` as a keyword, after their children.
- `w-50 m-1` means 50 columns wide with a margin of one cell.

## Layout

`Row` lays out children horizontally and `Col` vertically. Size them with `w-*` / `h-*`, where `fr` shares the remaining space:

```python
with Row(cls="h-fr"):
    with Col(cls="w-30 border-r border-line"):    # fixed-width side column
        ...
    with Col(cls="grow p-1"):                     # takes the rest
        with Row(cls="h-auto"):
            yield Stat("Open", "4", cls="w-12")
            yield Stat("Win%", "64%", cls="w-12")
        yield LineChart(cls="h-fr text-success")  # fills the remaining height
```

Use `Grid` for card layouts:

```python
Grid(*cards, cls="grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-1")
```

Breakpoints are min-width in **columns**: `md:` applies once the terminal is 120 columns wide.

## Live updates

Use Textual timers or workers, and update components in place:

```python
class Live(TwApp):
    def compose(self):
        self.price = Stat("Price", "-", cls="w-12")
        self.spark = Sparkline(cls="h-3 text-primary")
        self.feed = LogView(cls="h-fr")
        yield Panel(Row(self.price, self.spark), self.feed, title="Ticker", cls="h-fr")

    def on_mount(self):
        self.set_interval(0.25, self.tick)

    def tick(self):
        value = fetch_price()
        self.price.update(f"{value:.2f}", value_cls="text-success" if value > 100 else "text-error")
        self.spark.push(value)
        self.feed.write(f"price {value:.2f}", tag="TICK")
```

- `update(...)` and `set_cls(...)` do nothing when the value hasn't changed.
- Charts stream: `push()` adds a point on the right and scrolls the rest left without changing its shape.
- `Table` and `LogView` render only visible lines, so thousands of rows are fine.

> Don't name an attribute `self.log` on your app. Textual's `App.log` already uses that name.

## Interaction

```python
from tui_z import Button

class Trade(TwApp):
    def compose(self):
        yield Row(Button("Buy", "text-success border-success mr-1"), Button("Sell", "text-error border-error"))

    def on_button_pressed(self, event: Button.Pressed):
        self.notify(f"{event.button.label} pressed")
```

Interactive styles are variants: `hover:bg-boost`, `focus:border-primary`, `disabled:opacity-50`.

## Themes

```python
class App(TwApp):
    TW_THEME = "tokyo-night"
    BINDINGS = [("t", "next_theme", "Theme")]
```

See [theming](theming.md) for the full list and how to write your own theme.

## When something is wrong

tui-z raises `TailError` instead of silently ignoring a utility:

```
TailError: unknown utility 'padd-1' (in cls='padd-1')
```

An unknown theme color raises when the app starts, and the error lists the colors that are available.

## Next steps

- [Utility reference](utilities.md)
- [Components](components.md)
- [Custom components](custom-components.md)
- Read `demos/showcase.py`: it uses nearly every feature.
