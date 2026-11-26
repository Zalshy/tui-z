# Utility reference

Every tui-z widget takes a `cls` string. Units are **terminal cells**: `p-1` is one cell of padding, `w-20` is twenty columns wide.

```python
Text("67¢", "w-6 text-right text-success bold")
```

For the same property, the **last utility wins**: `"text-success text-error"` gives error. A component's own look (`DEFAULT_CLS`) comes first and your `cls` after it, so you can override any part of it.

## Layout

| Utility | Effect |
|---|---|
| `row` / `col` | Lay out children horizontally / vertically |
| `grid` | Grid layout |
| `grid-cols-3` `grid-rows-2` | Number of grid columns / rows |
| `grid-cols-[2fr_1fr]` `grid-rows-[5]` | Arbitrary column or row sizes (`_` separates values) |
| `col-span-2` `row-span-2` | Make a grid cell span several columns / rows |
| `gap-1` `gap-x-2` `gap-y-1` | Grid gutters (grid only) |

## Size

`w-` `h-` `min-w-` `max-w-` `min-h-` `max-h-` followed by:

| Value | Meaning |
|---|---|
| `10` | Ten cells |
| `full` | 100% of the parent |
| `auto` | Size to content |
| `fr` `2fr` | Share of the remaining space |
| `1/2` `1/3` … | Fraction of the parent |
| `screen` | Viewport width / height |
| `[30%]` `[40vw]` | Arbitrary Textual value |

Shortcuts: `grow` (= `w-fr`), `grow-y` (= `h-fr`).

## Spacing

| Utility | Effect |
|---|---|
| `p-1` `px-2` `py-1` `pt-1` `pr-1` `pb-1` `pl-1` | Padding |
| `m-1` `mx-2` `my-1` `mt-1` `mr-1` `mb-1` `ml-1` | Margin |
| `-mt-1` … | Negative margin |

## Color

| Utility | Effect |
|---|---|
| `text-{c}` | Text color |
| `bg-{c}` | Background |
| `border-{c}` | Border color |
| `tint-{c}` | Tint over the whole widget |
| `scrollbar-{c}` | Scrollbar color |
| `hatch-cross-{c}` | Hatched background |

Add `/NN` for opacity: `bg-success/20`. Use brackets for a fixed color: `text-[#ff8800]`, `bg-[rgb(20,20,30)]`, `text-[red]`, and `bg-[#ff8800]/30` for both.

### Theme colors

| Group | Names |
|---|---|
| Semantic | `primary` `secondary` `accent` `success` `warning` `error` `info` |
| Surfaces and text | `background` `surface` `panel` `boost` `foreground` `muted` `line` |
| Palette | `red` `orange` `yellow` `green` `teal` `cyan` `blue` `purple` `pink` |
| Aliases | `fg` `bg` `danger` `warn` |
| Derived shades | `success-darken-2` `primary-lighten-1` `primary-muted` … (from Textual) |

Palette names are **themeable**: `text-purple` is mauve in Catppuccin and magenta in Tokyo Night. An unknown color raises a `TailError` when the app starts.

## Borders

| Utility | Effect |
|---|---|
| `border` `border-none` | Solid border on all sides / no border |
| `border-round` `border-heavy` `border-double` `border-dashed` `border-tall` `border-wide` `border-thick` `border-panel` `border-ascii` `border-hkey` `border-vkey` `border-inner` `border-outer` `border-blank` | Border type |
| `border-t` `border-r` `border-b` `border-l` `border-x` `border-y` | Individual sides |
| `title-{c}` `title-left` `title-center` `title-right` `title-bold` | Border title styling |
| `subtitle-{c}` `subtitle-left` … | Border subtitle styling |

## Text

| Utility | Effect |
|---|---|
| `bold` `italic` `underline` `strike` `reverse` `dim` | Text style |
| `font-normal` `not-italic` `style-none` | Remove styles |
| `text-left` `text-center` `text-right` `text-justify` | Text alignment |
| `truncate` `nowrap` `wrap` | Overflow and wrapping |
| `text-opacity-50` | Text opacity |

### Content transforms

`uppercase` `lowercase` `capitalize` `normal-case` · `tracking-wide` `tracking-wider` `tracking-normal`

The last case transform wins, and so does the last tracking one. `normal-case` and `tracking-normal` undo a component's default: `Label("Fair value", cls="normal-case")`.

These change the text itself, so tui-z components apply them (Textual CSS can't). They work on `Text`, `Label`, `Badge`, `Stat`, `Panel` titles, table cells and log lines. Markup tags are left intact.

## Alignment

| Utility | Effect |
|---|---|
| `justify-start` `justify-center` `justify-end` | Children, horizontal |
| `items-start` `items-center` `items-end` | Children, vertical |
| `place-center` | Children, both axes |
| `content-left` `content-center` `content-right` `content-top` `content-middle` `content-bottom` | The widget's own content |

## Display and position

| Utility | Effect |
|---|---|
| `hidden` `block` | Remove from / restore to layout |
| `invisible` `visible` | Hide but keep the space |
| `dock-top` `dock-bottom` `dock-left` `dock-right` | Dock to an edge |
| `overflow-auto` `overflow-hidden` `overflow-scroll` (`overflow-x-…`, `overflow-y-…`) | Scrolling |
| `absolute` `relative` | Positioning |
| `opacity-50` | Whole-widget opacity |
| `scrollbar-none` `scrollbar-thin` | Scrollbar size |
| `cursor-pointer` | Pointer cursor (where the terminal supports it) |

## Variants

Prefix any utility with a variant. Variants stack: `md:hover:bg-boost`.

| Variant | Applies when |
|---|---|
| `hover:` | The mouse is over the widget |
| `focus:` | The widget has focus |
| `focus-within:` | A descendant has focus |
| `disabled:` | The widget is disabled |
| `first:` `last:` | First / last child |
| `odd:` `even:` | Odd / even child |
| `dark:` `light:` | The active theme is dark / light |
| `group-hover:` | An ancestor with the `group` class is hovered |

### Breakpoints

Breakpoints use **min-width in columns**, so `md:` applies at 120 columns and wider.

| Prefix | Columns |
|---|---|
| `sm:` | 80+ |
| `md:` | 120+ |
| `lg:` | 160+ |
| `xl:` | 200+ |

```python
Grid(*cards, cls="grid-cols-1 md:grid-cols-2 xl:grid-cols-4")
```

## Inline styles

`Table` cells, table rows and `LogView` lines are drawn inside one widget, so their `cls` is applied as an **inline text style**. Only text-level utilities work there:

- `text-{c}` `bg-{c}` (with `/NN`)
- `bold` `italic` `underline` `strike` `reverse` `dim` `font-normal`
- content transforms

Table column `cls` also takes widths (`w-N`, `w-fr`, `w-Nfr`) and alignment (`text-left/center/right`). Row `cls` takes the `odd:`, `even:` and `hover:` variants. A layout utility such as `p-1` raises `TailError`.

Use `inline("bold text-success")` to get a Textual style string for your own `Content`.

## Errors

tui-z fails loudly instead of rendering something unexpected:

```python
Text("x", "text-sucess")   # TailError at startup: unknown color 'sucess' (lists the theme colors)
Text("x", "padd-1")        # TailError immediately: unknown utility
```
