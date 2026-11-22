# Theming

Colors in tui-z are **theme tokens**, not fixed values. `text-success`, `bg-panel/40` and `border-line` all resolve to the active theme's variables, so switching themes restyles the whole app, including tables, logs and charts. Run `uv run python demos/showcase.py` and open the **Palette** tab to see every token in each theme.

## Built-in themes

| Family | Themes |
|---|---|
| tui-z | `terminal` (the default: green on near-black) · `amber` (retro phosphor) |
| Catppuccin | `catppuccin-mocha` `catppuccin-macchiato` `catppuccin-frappe` `catppuccin-latte` |
| Tokyo Night | `tokyo-night` `tokyo-night-storm` `tokyo-night-moon` `tokyo-night-day` |

The Catppuccin and Tokyo Night values are checked against upstream: Catppuccin's `palette.json`, and the generated `extras/` files of [folke/tokyonight.nvim](https://github.com/folke/tokyonight.nvim). `tokyo-night-day` is upstream's inverted Night. tui-z also passes the exact hex values through, which avoids the one-step rounding Textual applies to some derived colors.

`muted` is each palette's readable secondary-text color (Catppuccin `overlay2`, or `subtext0` on Latte; Tokyo Night `dark5`). It isn't the comment color, which is too faint for labels. The test suite enforces a minimum contrast for `foreground`, `muted` and `line` against the background in every theme.

## Tokens

| Group | Tokens | Use |
|---|---|---|
| Semantic | `primary` `secondary` `accent` `success` `warning` `error` `info` | Meaning: actions, states, alerts |
| Surfaces | `background` `surface` `panel` `boost` | Layering: app, cards, raised areas, hover |
| Text | `foreground` `muted` | Body text and captions |
| Lines | `line` | Borders, rules, chart tracks |
| Palette | `red` `orange` `yellow` `green` `teal` `cyan` `blue` `purple` `pink` | Categorical colors (tags, series) |

Prefer **semantic** tokens for meaning (`text-success` for profit), and use **palette** tokens when you only need distinct colors, such as chart series or tag categories. Palette names map to each theme's own hues: `purple` is Catppuccin mauve and Tokyo Night magenta.

Textual's derived shades work too: `primary-darken-2`, `success-lighten-1`, `primary-muted`, and so on.

For a color that should **not** change with the theme, use the arbitrary form: `text-[#ff8800]`.

## Switching themes

```python
app.theme = "tokyo-night"          # set it directly
app.action_next_theme()            # cycle through TwApp.TW_THEMES
app.action_prev_theme()
```

- **On startup:** set `TW_THEME = "catppuccin-mocha"` on your app class.
- **Key bindings:** `BINDINGS = [("t", "next_theme", "Theme")]`.
- **A visible picker:** add the `ThemeSwitcher()` widget.
- **Command palette:** Textual's palette (`ctrl+p`) lists the themes too.

Limit the cycle to the themes you support:

```python
class MyApp(TwApp):
    TW_THEMES = ("tokyo-night", "tokyo-night-day")
```

### Light and dark variants

`dark:` and `light:` apply a utility only when the active theme is dark or light:

```python
Panel(..., cls="bg-surface light:border-muted")
```

## Writing your own theme

`make_theme` builds a complete Textual theme from a palette:

```python
from tui_z import TwApp, make_theme

OCEAN = make_theme(
    "ocean", dark=True,
    background="#0B1220", surface="#101A2C", panel="#16233A",
    foreground="#D6E2F0", muted="#7C8DA6", line="#22324D",
    red="#FF6B7A", orange="#FF9F5A", yellow="#F7C873", green="#5FE0A6", teal="#3CC8C8",
    cyan="#5CC8FF", blue="#6B9CFF", purple="#B08CFF", pink="#FF8AC8",
    primary="#5CC8FF",            # optional; defaults: primary=blue, secondary=purple,
    secondary="#5FE0A6",          # accent=orange, info=cyan
)

class MyApp(TwApp):
    TW_THEMES = ("ocean", "tokyo-night")   # what next_theme / prev_theme cycle through

    def __init__(self):
        super().__init__()
        self.register_theme(OCEAN)          # register first,
        self.theme = "ocean"                # then select it
```

Don't set `TW_THEME = "ocean"` for a custom theme. `TwApp` selects `TW_THEME` before your `__init__` can register it.

`make_theme` takes keyword arguments:

- **Required:** `dark`, `background`, `surface`, `panel`, `foreground`, `muted`, `line`, and the nine palette colors.
- **Optional:** `primary`, `secondary`, `accent` and `info`.
- **Fixed roles:** `success` is green, `warning` is yellow and `error` is red.

### Textual's built-in themes

Textual's own themes (`nord`, `dracula`, `gruvbox`, …) work as well. tui-z derives the extra tokens (`muted`, `line`, `info` and the palette) from each theme's semantic colors.
