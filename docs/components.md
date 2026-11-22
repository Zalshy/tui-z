# Components

Every component takes `cls` (a class string) and `id`. Each one has a default look, `DEFAULT_CLS`, and your `cls` is merged after it. Most components also expose `*_CLS` class attributes for their inner parts, which you can override in a subclass.

All components support:

```python
widget.set_cls("text-error bold")   # replace the user classes (DEFAULT_CLS still applies)
widget.add_cls("hover:bg-boost")    # append to them
```

## Layout

### `Box`, `Row`, `Col`, `Grid`

Containers. `Box` stacks vertically, `Row` horizontally, `Col` vertically, and `Grid` is a grid.

```python
Row(Text("left"), Spacer(), Text("right"), cls="h-1")
Grid(*cards, cls="grid-cols-2 lg:grid-cols-4 gap-1")
```

All four work as context managers in `compose()`:

```python
with Row(cls="h-fr"):
    yield Sidebar(...)
    with Col(cls="grow p-1"):
        yield Panel(...)
```

Default sizes: `w-full h-auto`. `Grid` also defaults to `grid-rows-[auto]`, so rows fit their content. If every cell in a row has a fixed height, set the rows explicitly (`grid-rows-[5]`).

### `Scroll`

A vertical scroll container (`w-full h-fr scrollbar-thin`).

### `Spacer`

Takes the remaining width in a `Row` (`w-fr h-1`).

### `Divider`

A horizontal rule: `Divider()`, or `Divider("text-primary", char="═")`.

### `Sidebar`

A side panel that collapses to a thin rail.

```python
Sidebar(ThemeSwitcher(), title="Themes", width="w-26", rail="w-3", side="left", collapsed=False)
```

- `sidebar.toggle()` or `sidebar.collapsed = True` collapses it. Users can also click the `«` / `»` handle.
- `width` and `rail` are class strings, so `"w-26 lg:w-32"` works.
- It posts `Sidebar.Toggled` with a `.collapsed` attribute.
- `side="right"` mirrors the border and arrows.

## Content

### `Text`

Text with utilities and [Textual markup](https://textual.textualize.io/guide/content/#markup).

```python
Text("[$success]+8.8%[/] net EV", "bold")
Text("raw [text]", markup=False)
text.update("new value")       # no work when unchanged
```

Content transforms (`uppercase`, `tracking-wide`, …) are applied to the text and leave markup tags alone.

### `Label`

A small caption: muted and uppercase. `Label("Fair value")`.

### `Badge`

A pill: `Badge("Live", cls="bg-success/20 text-success")`. Its defaults are `bold uppercase px-1 bg-primary/15 text-primary`.

### `Stat`

A label above a value, the classic KPI tile.

```python
pnl = Stat("Net PnL", "+$10 554", cls="w-16", value_cls="text-success")
pnl.update("-$120", value_cls="text-error")
```

Inner parts: `LABEL_CLS`, `VALUE_CLS`. Arguments: `label_cls`, `value_cls`.

### `Panel`

A bordered section with a `// TITLE` header and an optional badge on the right.

```python
Panel(*children, title="Live markets", subtitle="refresh 1s",
      badge=Badge("Watching 47"), cls="h-fr")
```

Arguments: `title_cls`, `header_cls`. Class attributes: `HEADER_CLS`, `TITLE_CLS`.

## Data

### `Table`

A fast, virtualized table drawn in a single widget. Only visible rows render, and each rendered row is cached.

```python
table = Table(
    [("#", "w-4 text-muted"), ("Wallet", "w-14 text-info"), ("PnL", "w-fr text-right text-success")],
    [["#1", "0x87cc…aa20", ("+$312k", "bold")]],
    row_cls="odd:bg-panel/40 hover:bg-boost",
    max_rows=200,
)
table.add_row(["#2", "0x3f4a…c91e", "+$184k"], top=True)
table.set_rows(rows)
table.update_row(0, cells)
table.clear()
table.row_count
```

- **Columns** are `(title, cls)`. Column `cls` takes a width (`w-N`, `w-fr`, `w-Nfr`), an alignment (`text-left/center/right`) and inline styles.
- **Cells** are markup strings, or `(text, cls)` to style a single cell.
- **Rows** accept the `odd:`, `even:` and `hover:` variants through `row_cls`.
- Other options: `header=False` hides the header, `header_cls` styles it, and `max_rows` caps the length (the oldest rows are dropped).

### `LogView`

A tail-style log: time, tag, message. It keeps the newest `max_lines` and follows the end unless you've scrolled up.

```python
log = LogView(cls="h-fr", max_lines=1000, time_format="%H:%M:%S", tag_width=7)
log.write("SELL landed [$muted]slot 371,911[/]", tag="Exit", tag_cls="bg-error/20 text-error")
log.write("plain line", msg_cls="text-muted")
log.clear()
```

### `Ticker`

A scrolling one-line feed. Items are markup.

```python
Ticker(["[b $error]LIVE[/]", "BTC [$success]+2.1%[/]"], "bg-surface", speed=0.12)
ticker.set_items([...])
```

## Charts

Charts take their main color from `text-*`. Extra series and marks take theme color names (`"purple"`, `"success"`).

### `Bar`

A horizontal meter from 0 to 1. The track uses the theme's `line` color.

```python
bar = Bar(0.67, "w-20 text-success")
bar.value = 0.8
Bar(0.3, track=False)
```

### `Sparkline`

A block sparkline at any height.

```python
spark = Sparkline(values, "h-4 text-success", lo=0)
spark.push(42)            # streams: newest on the right
Sparkline(values, stretch=True)   # fit the whole series to the width
```

### `LineChart`

A braille line or area chart, with extra series, horizontal marks and a y axis.

```python
chart = LineChart(
    price, "h-12 text-primary",
    series=[(path_a, "purple"), (path_b, "cyan")],
    marks=[(1.4, "success", "TP"), (0.8, "error", "SL")],
    fill=False, axis=True, lo=0.5, hi=1.6,
)
chart.push(new_price, new_a, new_b)    # advance every series together
chart.set_series([(path_a, "purple")])
```

- **`mode="stream"`** (the default): every point gets a fixed slot of `step` dot-columns. New points enter on the right, and what's already drawn scrolls left without changing shape. The y-range is sticky: it grows but doesn't jitter. Set `lo` / `hi` to fix it.
- **`mode="fit"`**: stretches the whole series to the width, for static data.
- **`keep`**: how many points each series retains (2000 by default).

## Interaction

### `Button`

A focusable button. Press it with a click, Enter or Space. It posts `Button.Pressed`.

```python
Button("Buy yes", "text-success border-success")

def on_button_pressed(self, event: Button.Pressed) -> None:
    self.notify(f"{event.button.label} pressed")
```

The defaults include `hover:` and `focus:` styles. Override them in `cls`.

> `tui_z.Button` is separate from `textual.widgets.Button`. When you use both, import one under an alias.

### `ThemeSwitcher`

A clickable list of themes that highlights the active one. It follows theme changes made anywhere, such as key bindings or the command palette.

```python
ThemeSwitcher()                                       # every tui-z theme
ThemeSwitcher(["tokyo-night", "catppuccin-mocha"], cls="row", item_cls="w-auto")
```

Class attributes: `ITEM_CLS`, `ACTIVE_CLS`. Arguments: `item_cls`, `active_cls`.

## Any Textual widget

`tw()` adds utility classes to any widget and returns it:

```python
from textual.widgets import DataTable, Digits, Input
from tui_z import tw

tw(Digits("1,292"), "text-success")
tw(Input(placeholder="search"), "border-none bg-panel focus:bg-boost")
tw(DataTable(), "h-fr")
```

## The app

### `TwApp`

Subclass `TwApp` instead of `textual.app.App`. It:

- registers every tui-z theme and selects `TW_THEME` (default `"terminal"`)
- compiles every class string into the stylesheet before the widgets that use it are styled
- sets the screen breakpoint classes for `sm:`, `md:`, `lg:` and `xl:`
- provides `action_next_theme` / `action_prev_theme`, which cycle through `TW_THEMES`

```python
class MyApp(TwApp):
    TW_THEME = "catppuccin-mocha"
    TW_THEMES = ("catppuccin-mocha", "catppuccin-latte")
    BINDINGS = [("t", "next_theme", "Theme")]
```
