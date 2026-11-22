# Custom components

The point of tui-z is to make a UI element once and reuse it everywhere. There are three levels, from lightest to most complete.

## 1. Named class strings

The simplest form of reuse is a constant:

```python
CARD = "border border-line bg-panel px-1 mb-1"
UP, DOWN = "text-success", "text-error"

Col(..., cls=CARD)
Text("+2.1%", f"w-8 text-right {UP}")
```

This also keeps the number of distinct class strings small, which keeps compilation cheap (see [internals](internals.md)).

## 2. Subclass with `DEFAULT_CLS`

Every tui-z component has a `DEFAULT_CLS`. A subclass's `DEFAULT_CLS` **adds to** its parent's instead of replacing it:

```python
from tui_z import Badge, Col

class Card(Col):
    DEFAULT_CLS = "h-auto border border-line bg-panel px-1 mb-1"
    # still has Col's "col w-full h-auto"

class LiveBadge(Badge):
    DEFAULT_CLS = "bg-success/20 text-success"
    # keeps Badge's padding, bold and uppercase; changes only the colors

Card(..., cls="border-primary")      # the user cls still wins
```

Components also expose their inner parts as class attributes, so you can restyle a part without rebuilding the component:

```python
from tui_z import Panel, Stat

class QuietPanel(Panel):
    DEFAULT_CLS = "border-round"
    TITLE_CLS = "text-primary italic"

class BigStat(Stat):
    VALUE_CLS = "text-primary bold"
```

## 3. Composite components

Build a widget from other widgets and keep references to the parts you'll update:

```python
from tui_z import Badge, Bar, Col, Row, Text

class MarketRow(Col):
    DEFAULT_CLS = "h-auto mb-1"

    def __init__(self, question: str, price: float) -> None:
        self.price_text = Text("", "w-6 text-right bold")
        self.bar = Bar(0, "w-full text-success")
        super().__init__(
            Row(Text(question, "grow truncate"), self.price_text),
            self.bar,
        )
        self.set_price(price)

    def set_price(self, price: float) -> None:
        self.price_text.update(f"{price * 100:.0f}¢")
        self.price_text.set_cls("w-6 text-right bold " + ("text-success" if price >= 0.5 else "text-error"))
        self.bar.value = price
```

Some tips:

- `Text.update` and `set_cls` do nothing when the value hasn't changed, so you can call them on every tick.
- Switching between a few class strings is cheap. Each one compiles once, and swapping costs one class change.
- Put data in the **content**, not in class names. Avoid `f"w-{n}"` with an unbounded `n`.

## Styling Textual widgets

Mix in `Tw` to give any Textual widget `cls` support and a `DEFAULT_CLS`:

```python
from textual.widgets import Static
from tui_z import Tw

class Clock(Tw, Static):
    DEFAULT_CLS = "w-auto text-muted"

    def __init__(self, cls: str = "") -> None:
        super().__init__("00:00:00")
        self._tw_init(cls)
```

For a one-off, `tw(widget, "cls")` is enough.
