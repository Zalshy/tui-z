"""Design tokens and themes.

Colors live in Textual themes, so every utility color (`text-success`,
`bg-panel/40`, `text-purple`) resolves to a theme variable and switching
`app.theme` restyles the whole app.

Token families
--------------
semantic   primary secondary accent success warning error info
surfaces   background surface panel boost
text       foreground muted
lines      line
palette    red orange yellow green teal cyan blue purple pink

The palette names are *themeable*: `text-purple` is Catppuccin mauve under
Catppuccin and Tokyo Night magenta under Tokyo Night. For a fixed CSS color
use the arbitrary form: `text-[#ff0000]` / `text-[red]`.
"""

from __future__ import annotations

from textual.theme import Theme

PALETTE = ("red", "orange", "yellow", "green", "teal", "cyan", "blue", "purple", "pink")
EXTRA_TOKENS = ("info", "muted", "line", *PALETTE)
SEMANTIC = ("primary", "secondary", "accent", "success", "warning", "error", "info")
SURFACES = ("background", "surface", "panel", "foreground", "muted", "line")


def make_theme(
    name: str,
    *,
    dark: bool,
    background: str,
    surface: str,
    panel: str,
    foreground: str,
    muted: str,
    line: str,
    red: str,
    orange: str,
    yellow: str,
    green: str,
    teal: str,
    cyan: str,
    blue: str,
    purple: str,
    pink: str,
    primary: str | None = None,
    secondary: str | None = None,
    accent: str | None = None,
    info: str | None = None,
) -> Theme:
    """Build a theme from a palette. Semantic colors default to the usual roles."""
    base = dict(
        primary=primary or blue,
        secondary=secondary or purple,
        accent=accent or orange,
        success=green,
        warning=yellow,
        error=red,
        foreground=foreground,
        background=background,
        surface=surface,
        panel=panel,
    )
    return Theme(
        name=name,
        dark=dark,
        boost="#FFFFFF0A" if dark else "#0000000A",
        **base,
        variables={
            # Textual's color system round-trips colors and can shift a channel
            # by 1 (#FF9E64 -> #FE9E64); re-state the exact palette values.
            **base,
            "info": info or cyan,
            "muted": muted,
            "line": line,
            "red": red, "orange": orange, "yellow": yellow, "green": green, "teal": teal,
            "cyan": cyan, "blue": blue, "purple": purple, "pink": pink,
        },
    )


# --------------------------------------------------------------------------- #
# tui-z originals
# --------------------------------------------------------------------------- #

TERMINAL = make_theme(
    "terminal", dark=True,
    background="#07090C", surface="#0B0F14", panel="#111820",
    foreground="#D7DEE6", muted="#6B7A8A", line="#202C38",
    red="#FF4D5E", orange="#FF8A3D", yellow="#F5B83D", green="#2EE68A", teal="#2DD4BF",
    cyan="#38BDF8", blue="#5B9CFF", purple="#A78BFA", pink="#F472B6",
    primary="#2EE68A", secondary="#38BDF8", accent="#F5B83D",
)

AMBER = make_theme(
    "amber", dark=True,
    background="#0A0700", surface="#110C02", panel="#1A1305",
    foreground="#FFD9A0", muted="#9A7844", line="#3A2C10",
    red="#FF5F45", orange="#FF7A00", yellow="#FFB000", green="#B5E853", teal="#7FD6A4",
    cyan="#FFCC66", blue="#E8B46A", purple="#D9A066", pink="#FF9E7A",
    primary="#FFB000", secondary="#FFCC66", accent="#FF7A00",
)

# --------------------------------------------------------------------------- #
# Catppuccin — https://catppuccin.com/palette (verified against palette.json)
# background=base, surface=mantle, panel=surface0, line=surface1,
# muted=overlay2 (subtext0 on Latte) — the first step that stays readable for
# labels (~4.5:1); overlay1 is meant for code comments and is too faint.
# --------------------------------------------------------------------------- #

CATPPUCCIN_LATTE = make_theme(
    "catppuccin-latte", dark=False,
    background="#EFF1F5", surface="#E6E9EF", panel="#CCD0DA",
    foreground="#4C4F69", muted="#6C6F85", line="#BCC0CC",
    red="#D20F39", orange="#FE640B", yellow="#DF8E1D", green="#40A02B", teal="#179299",
    cyan="#04A5E5", blue="#1E66F5", purple="#8839EF", pink="#EA76CB",
)
CATPPUCCIN_FRAPPE = make_theme(
    "catppuccin-frappe", dark=True,
    background="#303446", surface="#292C3C", panel="#414559",
    foreground="#C6D0F5", muted="#949CBB", line="#51576D",
    red="#E78284", orange="#EF9F76", yellow="#E5C890", green="#A6D189", teal="#81C8BE",
    cyan="#99D1DB", blue="#8CAAEE", purple="#CA9EE6", pink="#F4B8E4",
)
CATPPUCCIN_MACCHIATO = make_theme(
    "catppuccin-macchiato", dark=True,
    background="#24273A", surface="#1E2030", panel="#363A4F",
    foreground="#CAD3F5", muted="#939AB7", line="#494D64",
    red="#ED8796", orange="#F5A97F", yellow="#EED49F", green="#A6DA95", teal="#8BD5CA",
    cyan="#91D7E3", blue="#8AADF4", purple="#C6A0F6", pink="#F5BDE6",
)
CATPPUCCIN_MOCHA = make_theme(
    "catppuccin-mocha", dark=True,
    background="#1E1E2E", surface="#181825", panel="#313244",
    foreground="#CDD6F4", muted="#9399B2", line="#45475A",
    red="#F38BA8", orange="#FAB387", yellow="#F9E2AF", green="#A6E3A1", teal="#94E2D5",
    cyan="#89DCEB", blue="#89B4FA", purple="#CBA6F7", pink="#F5C2E7",
)

# --------------------------------------------------------------------------- #
# Tokyo Night — https://github.com/folke/tokyonight.nvim (verified against the
# generated extras/lua/tokyonight_*.lua; Day is upstream's inverted Night)
# background=bg, surface=bg_dark, panel=bg_highlight, line=fg_gutter,
# muted=dark5 (comment is for code comments: 2.0–2.8:1, unreadable as labels)
# --------------------------------------------------------------------------- #

_TOKYO_ACCENTS = dict(
    red="#F7768E", orange="#FF9E64", yellow="#E0AF68", green="#9ECE6A", teal="#1ABC9C",
    cyan="#7DCFFF", blue="#7AA2F7", purple="#BB9AF7", pink="#FF007C",
)
TOKYO_NIGHT = make_theme(
    "tokyo-night", dark=True,
    background="#1A1B26", surface="#16161E", panel="#292E42",
    foreground="#C0CAF5", muted="#737AA2", line="#3B4261",
    **_TOKYO_ACCENTS,
)
TOKYO_NIGHT_STORM = make_theme(
    "tokyo-night-storm", dark=True,
    background="#24283B", surface="#1F2335", panel="#292E42",
    foreground="#C0CAF5", muted="#737AA2", line="#3B4261",
    **_TOKYO_ACCENTS,
)
TOKYO_NIGHT_MOON = make_theme(
    "tokyo-night-moon", dark=True,
    background="#222436", surface="#1E2030", panel="#2F334D",
    foreground="#C8D3F5", muted="#737AA2", line="#3B4261",
    red="#FF757F", orange="#FF966C", yellow="#FFC777", green="#C3E88D", teal="#4FD6BE",
    cyan="#86E1FC", blue="#82AAFF", purple="#C099FF", pink="#FF007C",
)
TOKYO_NIGHT_DAY = make_theme(
    "tokyo-night-day", dark=False,
    background="#E1E2E7", surface="#D0D5E3", panel="#C4C8DA",
    foreground="#3760BF", muted="#68709A", line="#A8AECB",
    red="#F52A65", orange="#B15C00", yellow="#8C6C3E", green="#587539", teal="#118C74",
    cyan="#007197", blue="#2E7DE9", purple="#9854F1", pink="#D20065",
)

THEMES = (
    TERMINAL, AMBER,
    CATPPUCCIN_MOCHA, CATPPUCCIN_MACCHIATO, CATPPUCCIN_FRAPPE, CATPPUCCIN_LATTE,
    TOKYO_NIGHT, TOKYO_NIGHT_STORM, TOKYO_NIGHT_MOON, TOKYO_NIGHT_DAY,
)
THEME_NAMES = tuple(t.name for t in THEMES)


def fill_extra_tokens(variables: dict[str, str]) -> dict[str, str]:
    """Give non-tui-z themes (Textual's built-ins) values for every tui-z token."""
    v = variables
    defaults = {
        "info": v.get("secondary") or v.get("accent", "cyan"),
        "muted": v.get("foreground-darken-3") or v.get("foreground", "grey"),
        "line": v.get("panel-lighten-1") or v.get("panel", "grey"),
        "red": v.get("error", "red"),
        "orange": v.get("warning", "orange"),
        "yellow": v.get("warning", "yellow"),
        "green": v.get("success", "green"),
        "teal": v.get("success", "teal"),
        "cyan": v.get("secondary", "cyan"),
        "blue": v.get("primary", "blue"),
        "purple": v.get("accent", "purple"),
        "pink": v.get("accent", "pink"),
    }
    for key, value in defaults.items():
        v.setdefault(key, value)
    return v
