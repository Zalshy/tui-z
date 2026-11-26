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

### `KeyValue`

Aligned key / value rows, for detail panels. Values are markup, and each row can take its own inline `cls`.

```python
info = KeyValue([("Status", "Live", "text-success"), ("Latency", "12 ms")], key_cls="uppercase")
info.set("Latency", "18 ms", "text-warning")   # add or change a row
info.get("Status")                             # "Live"
info.remove_key("Status")
```

Class attributes: `KEY_CLS`, `VALUE_CLS`, `GAP`.

### `Kbd`

A keyboard key: `Kbd("ctrl+s")`. Its defaults are `px-1 bg-boost text-foreground bold`.

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

### `BarChart`

Vertical bars with labels under them. Heights use eighth blocks, so they're precise to 1/8 of a cell.

```python
BarChart([("Mon", 3), ("Tue", 5), ("Wed", 2, "error")], "h-8 text-primary", values=True)
BarChart.histogram(latencies, bins=12, cls="h-6 text-info")
chart.set_data([("Thu", 4)])
```

- Items are a value, `(label, value)` or `(label, value, color)`.
- Bars share the width (up to 8 cells each); `bar_width=` fixes it and `gap=` sets the space between bars. Bars that don't fit are cut.
- `values=True` prints each value above its bar, `labels=False` hides the labels, and `lo` / `hi` fix the scale (`lo` is 0 by default).

### `Heatmap`

A grid of values shaded from faint to full in one theme color, so it follows theme switches.

```python
Heatmap(activity, color="success", row_labels=["Mon", "Tue"], col_labels=["0h", "", "", "3h"])
heatmap.data = new_rows
heatmap.set_color("warning")
```

Values at or below `lo` (by default 0, or the minimum if lower) use the theme's `panel` color. `cell` sets how many columns one cell takes (2), and `steps` how many shades there are (5).

## Controls

### `Button`

A focusable button. Press it with a click, Enter or Space. It posts `Button.Pressed`.

```python
Button("Buy yes", "text-success border-success")

def on_button_pressed(self, event: Button.Pressed) -> None:
    self.notify(f"{event.button.label} pressed")
```

The defaults include `hover:` and `focus:` styles. Override them in `cls`.

> `tui_z.Button` is separate from `textual.widgets.Button`. When you use both, import one under an alias (`from textual import widgets as tx`). The same goes for `Switch`, `Checkbox`, `Input`, `Select`, `Tabs` and `Toast`. Textual applies CSS by class name, so `Button { … }` rules in your app's CSS match both; tui-z's own look doesn't depend on Textual's defaults.

### `Checkbox`, `Switch`

Focusable on/off controls with a label. Toggle them with a click, Enter or Space.

```python
Checkbox("Copy trades", True)
Switch("Live mode", on_cls="text-success")

def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
    self.copy_trades = event.value
```

They post `Checkbox.Changed` / `Switch.Changed` with `.value`. `on_cls` and `off_cls` style the mark (inline styles). Pass `disabled=True` to disable one.

### `RadioGroup`

One choice out of a few, one per line. The arrow keys or a click select.

```python
sizing = RadioGroup(["Kelly", "Fixed", "Off"], value=0)
sizing.value      # "Kelly"
sizing.index = 2
```

It posts `RadioGroup.Changed` with `.index` and `.value`.

### `Input`

Textual's `Input`, restyled: a rounded border that turns `primary` on focus. Its events (`Input.Changed`, `Input.Submitted`) and options (`validators=`, `restrict=`, `password=` …) are Textual's.

```python
Input(placeholder="Search markets…", cls="w-40")
```

### `Select`

Textual's `Select`, restyled. It posts `Select.Changed`.

```python
Select([("Macro", "macro"), ("Crypto", "crypto")], prompt="Category", value="macro")
```

`cls` styles the outer widget, `current_cls` the closed box and `overlay_cls` the open list. `group-focus:` utilities in `current_cls` follow the select's focus. Class attributes: `CURRENT_CLS`, `OVERLAY_CLS`.

### `ThemeSwitcher`

A clickable list of themes that highlights the active one. It follows theme changes made anywhere, such as key bindings or the command palette.

```python
ThemeSwitcher()                                       # every tui-z theme
ThemeSwitcher(["tokyo-night", "catppuccin-mocha"], cls="row", item_cls="w-auto")
```

Class attributes: `ITEM_CLS`, `ACTIVE_CLS`. Arguments: `item_cls`, `active_cls`.

## Navigation

### `TabView`, `TabPane`, `Tabs`

Tabs that switch between panes. Only the active pane is displayed.

```python
with TabView(active="logs", id="tabs"):
    with TabPane("Dashboard", id="dashboard"):
        yield Panel(...)
    with TabPane("Logs", id="logs"):
        yield LogView()

self.query_one(TabView).active = "dashboard"
```

- `TabView` posts `TabView.Changed` with `.pane`. `active_pane` returns the active `TabPane`.
- Click a tab, or focus the tabs and use the left / right arrows.
- `tabs_cls` styles the tab row and `body_cls` the pane area.
- `Tabs` is the row of labels on its own: `Tabs(["Day", "Week"], active=0)` posts `Tabs.Changed` with `.index`. Class attributes: `ITEM_CLS`, `ACTIVE_CLS`.

### `Sidebar`

A side panel that collapses to a thin rail.

```python
Sidebar(ThemeSwitcher(), title="Themes", width="w-26", rail="w-3", side="left", collapsed=False)
```

- `sidebar.toggle()` or `sidebar.collapsed = True` collapses it. Users can also click the `«` / `»` handle.
- `width` and `rail` are class strings, so `"w-26 lg:w-32"` works.
- It posts `Sidebar.Toggled` with a `.collapsed` attribute.
- `side="right"` mirrors the border and arrows.

### `KeyHints`

A one-line list of keys and what they do, like a footer.

```python
KeyHints(cls="dock-bottom")                     # follows the screen's bindings
KeyHints([("q", "quit"), ("[ ]", "theme")])     # or a fixed list
```

With no list, it shows every binding with `show=True` that's active for the focused widget, and updates as focus moves. Class attributes: `KEY_CLS`, `DESC_CLS`, `SEPARATOR`.

## Feedback

### Toasts

Short-lived notifications in a corner of the screen.

```python
self.toast("Order filled", variant="success")
self.toast("Feed lost", title="Connection", variant="error", timeout=None,
           action=("Retry", self.reconnect))
self.notify("Saved")      # Textual's notify() shows a tui-z toast too
```

- **Variants**: `success`, `info`, `warning`, `error` and `neutral`. Each has a theme color and an icon.
- **Timeout**: `timeout` is in seconds. The default is `TwApp.TW_TOAST_TIMEOUT` (4), and `None` keeps the toast until it's dismissed. A countdown bar shows the time left, and hovering pauses it.
- **Dismissing**: click a toast or its `✕`. An `action` adds a button that runs the callback, then dismisses the toast.
- **Repeats**: the same message again shows `×2` on the toast that's already there and restarts its timer, instead of stacking a duplicate.
- **Events**: each toast posts `Toast.Dismissed` with `.reason`: `"timeout"`, `"closed"`, `"clicked"`, `"action"`, `"replaced"` or `"dismissed"`.
- **Threads**: `toast()` and `notify()` are safe to call from a worker thread.

Settings on `TwApp`:

```python
class MyApp(TwApp):
    TW_TOASTS = "top-right"       # where toasts appear: top-/bottom- + left/center/right
    TW_TOAST_MAX = 3              # most on screen; the oldest is dismissed for a new one
    TW_TOAST_TIMEOUT = 6.0
```

Set `TW_TOASTS = None` to keep Textual's own notifications for `notify()`. Toasts are `Toast` widgets inside a `ToastStack`, which `TwApp` docks to each screen. Style one with `cls=` (`self.toast("…", cls="w-60")`), or subclass `Toast` and change `DEFAULT_CLS`.

### `NotificationCenter`

Every toast the app has shown, in a scrolling list, with an unread count.

```python
Sidebar(NotificationCenter(cls="h-fr"), title="Inbox")
center.unread        # toasts since the last mark_read()
center.mark_read()   # clicking the list does this too
center.clear()
```

It lists the toasts shown before it was mounted too: `TwApp.tw_notifications` keeps them all, and `TwApp.tw_notification_signal` publishes each new one.

### `Alert`

A banner that stays in the layout. It uses the same variants as toasts.

```python
Alert("Prices are delayed 15 min", title="Market closed", variant="warning", dismissible=True)
alert.update("Back at 9:30")
```

`dismissible=True` adds a `✕` that removes the alert and posts `Alert.Dismissed`.

### `Progress`

A labelled progress bar with a percentage. The fill takes `text-*`.

```python
sync = Progress(total=100, label="Sync", cls="text-success")
sync.advance(5)
sync.update(value=40, label="Syncing wallets")
sync.percentage        # 0.4
Progress(total=None)   # indeterminate: a segment sweeps back and forth
```

### `Spinner`

An animated spinner with a label. The spinner takes `text-*`.

```python
spinner = Spinner("Syncing", cls="text-primary")
spinner.stop("Synced")    # freezes on ✓ and the new label
spinner.start("Again")
```

### `Dialog`

A modal dialog. It dismisses with the pressed button's result, or `None` on Escape. The last button is focused, so put the main action last.

```python
def on_answer(result: str | None) -> None:
    if result == "delete":
        ...

self.push_screen(
    Dialog("Delete 3 orders?", title="Confirm",
           buttons=[("Cancel", "cancel"), ("Delete", "delete", "text-error border-error")]),
    on_answer,
)
```

Buttons are `(label, result)` or `(label, result, cls)`. With no buttons you get Cancel / OK. `cls` styles the panel (`PANEL_CLS`), and the screen behind it is dimmed.

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
- shows notifications as tui-z toasts: `toast()`, and `notify()` too (see [Toasts](#toasts))

```python
class MyApp(TwApp):
    TW_THEME = "catppuccin-mocha"
    TW_THEMES = ("catppuccin-mocha", "catppuccin-latte")
    BINDINGS = [("t", "next_theme", "Theme")]
```
