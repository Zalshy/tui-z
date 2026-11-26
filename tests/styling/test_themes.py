from textual.color import Color

from tui_z import THEMES, make_theme
from tui_z.styling.themes import EXTRA_TOKENS, PALETTE, fill_extra_tokens


def _contrast(a: str, b: str) -> float:
    def lum(c: Color) -> float:
        f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b)
    x, y = sorted((lum(Color.parse(a)), lum(Color.parse(b))), reverse=True)
    return (x + 0.05) / (y + 0.05)


def test_theme_legibility():
    for t in THEMES:
        v = t.variables
        assert _contrast(t.foreground, t.background) >= 4.5, t.name
        assert _contrast(v["muted"], t.background) >= 3.4, t.name   # labels stay readable
        assert _contrast(v["line"], t.background) >= 1.3, t.name    # borders stay visible


def test_every_theme_defines_every_token():
    for t in THEMES:
        for token in EXTRA_TOKENS:
            assert token in t.variables, (t.name, token)


def test_make_theme_defaults_semantic_roles():
    colors = {c: f"#0000{i:02x}" for i, c in enumerate(PALETTE)}
    t = make_theme("t", dark=True, background="#000000", surface="#111111", panel="#222222",
                   foreground="#ffffff", muted="#999999", line="#444444", **colors)
    assert t.primary == colors["blue"] and t.success == colors["green"] and t.error == colors["red"]
    t2 = make_theme("t2", dark=False, background="#ffffff", surface="#eeeeee", panel="#dddddd",
                    foreground="#000000", muted="#666666", line="#bbbbbb", primary="#123456", **colors)
    assert t2.primary == "#123456" and not t2.dark


def test_fill_extra_tokens_gives_foreign_themes_every_token():
    filled = fill_extra_tokens({"primary": "#0000ff", "success": "#00ff00"})
    assert set(EXTRA_TOKENS) <= set(filled)
    assert filled["blue"] == "#0000ff" and filled["green"] == "#00ff00"
    assert fill_extra_tokens({"red": "#ff0000"})["red"] == "#ff0000"  # never overrides
