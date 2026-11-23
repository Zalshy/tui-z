"""The utility-class engine: turns `cls="text-success bold p-1"` into Textual CSS.

Each *unique class string* compiles to one generated CSS class (``tw-<hash>``).
Compiling the whole string at once (instead of one CSS class per utility) lets
us merge utilities that map onto a single Textual property (``border-heavy`` +
``border-success`` -> ``border: heavy $success``) and resolve conflicts
For the same property, the **last** utility wins.
That is what makes component defaults overridable:
``merge(component_defaults, user_cls)``.

This module is pure: it never touches a running app. Color tokens become
``$variables``; checking that they exist in the theme happens in ``TwApp``.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from functools import lru_cache

from .theme import PALETTE

try:  # Textual's table of named colors (red, ansi_bright_green, ...)
    from textual._color_constants import COLOR_NAME_TO_RGB as _NAMED_COLORS
except ImportError:  # pragma: no cover - fall back to a parse probe
    _NAMED_COLORS = None


def _is_named_color(name: str) -> bool:
    if _NAMED_COLORS is not None:
        return name in _NAMED_COLORS
    from textual.color import Color, ColorParseError

    try:
        Color.parse(name)
    except ColorParseError:
        return False
    return True


class TailError(ValueError):
    """Raised for an unknown utility, a bad value or an unknown theme color."""


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #

COLOR_ALIASES = {
    "fg": "foreground",
    "bg": "background",
    "danger": "error",
    "warn": "warning",
}

BORDER_TYPES = {
    "ascii", "blank", "dashed", "double", "heavy", "hidden", "hkey", "inner",
    "outer", "panel", "round", "solid", "tall", "tab", "thick", "block",
    "vkey", "wide",
}
SIDES = {"t": ("top",), "r": ("right",), "b": ("bottom",), "l": ("left",),
         "x": ("left", "right"), "y": ("top", "bottom")}
ALL_SIDES = ("top", "right", "bottom", "left")

TEXT_STYLES = {"bold", "italic", "underline", "strike", "reverse", "dim", "blink", "overline"}
TEXT_STYLE_OFF = {"font-normal": "bold", "not-italic": "italic", "no-underline": "underline"}

# Content transforms: not CSS, applied by tui_z components when rendering text.
TRANSFORMS = {"uppercase", "lowercase", "capitalize", "tracking-wide", "tracking-wider", "tracking-normal"}

PSEUDO_VARIANTS = {
    "hover": ":hover", "focus": ":focus", "focus-within": ":focus-within",
    "blur": ":blur", "disabled": ":disabled", "enabled": ":enabled",
    "first": ":first-child", "last": ":last-child", "odd": ":odd", "even": ":even",
    "empty": ":empty", "dark": ":dark", "light": ":light",
}
# min-width breakpoints in terminal columns (see TwApp.HORIZONTAL_BREAKPOINTS)
BREAKPOINTS = {"sm": 80, "md": 120, "lg": 160, "xl": 200}
BREAKPOINT_ORDER = list(BREAKPOINTS)

STATIC: dict[str, dict[str, str]] = {
    # layout
    "row": {"layout": "horizontal"}, "flex-row": {"layout": "horizontal"},
    "col": {"layout": "vertical"}, "flex-col": {"layout": "vertical"},
    "grid": {"layout": "grid"},
    # display / visibility
    "hidden": {"display": "none"}, "block": {"display": "block"},
    "invisible": {"visibility": "hidden"}, "visible": {"visibility": "visible"},
    # position
    "absolute": {"position": "absolute"}, "relative": {"position": "relative"},
    # text
    "text-left": {"text-align": "left"}, "text-center": {"text-align": "center"},
    "text-right": {"text-align": "right"}, "text-justify": {"text-align": "justify"},
    "truncate": {"text-wrap": "nowrap", "text-overflow": "ellipsis"},
    "nowrap": {"text-wrap": "nowrap"}, "wrap": {"text-wrap": "wrap"},
    # alignment of children
    "justify-start": {"align-horizontal": "left"},
    "justify-center": {"align-horizontal": "center"},
    "justify-end": {"align-horizontal": "right"},
    "items-start": {"align-vertical": "top"},
    "items-center": {"align-vertical": "middle"},
    "items-end": {"align-vertical": "bottom"},
    "place-center": {"align": "center middle"},
    # alignment of own content
    "content-left": {"content-align-horizontal": "left"},
    "content-center": {"content-align-horizontal": "center"},
    "content-right": {"content-align-horizontal": "right"},
    "content-top": {"content-align-vertical": "top"},
    "content-middle": {"content-align-vertical": "middle"},
    "content-bottom": {"content-align-vertical": "bottom"},
    # sizing shortcuts
    "grow": {"width": "1fr"}, "grow-y": {"height": "1fr"},
    # scrollbars
    "scrollbar-none": {"scrollbar-size": "0 0"},
    "scrollbar-thin": {"scrollbar-size": "1 1"},
    # misc
    "cursor-pointer": {"pointer": "pointer"},
}
for _edge in ("top", "bottom", "left", "right"):
    STATIC[f"dock-{_edge}"] = {"dock": _edge}
for _mode in ("auto", "hidden", "scroll"):
    STATIC[f"overflow-{_mode}"] = {"overflow-x": _mode, "overflow-y": _mode}
    STATIC[f"overflow-x-{_mode}"] = {"overflow-x": _mode}
    STATIC[f"overflow-y-{_mode}"] = {"overflow-y": _mode}

SIZE_PROPS = {"w": "width", "h": "height", "min-w": "min-width", "max-w": "max-width",
              "min-h": "min-height", "max-h": "max-height"}
SPACE_PROPS = {"p": "padding", "m": "margin"}
SPACE_SIDES = {"": ALL_SIDES, "x": ("left", "right"), "y": ("top", "bottom"),
               "t": ("top",), "r": ("right",), "b": ("bottom",), "l": ("left",)}

_NUM = r"\d+"
_RE_SIZE = re.compile(r"^(min-w|max-w|min-h|max-h|w|h)-(.+)$")
_RE_SPACE = re.compile(r"^(-?)([pm])([xytrbl]?)-(.+)$")
_RE_TOKEN = re.compile(r"[a-z][a-z0-9-]*")


# --------------------------------------------------------------------------- #
# Value parsers
# --------------------------------------------------------------------------- #

def _arbitrary(value: str) -> str | None:
    """`[30%]` -> `30%`; `[1fr_2fr]` -> `1fr 2fr` (underscore = space)."""
    if value.startswith("[") and value.endswith("]"):
        return value[1:-1].replace("_", " ")
    return None


def size_value(value: str) -> str:
    if (raw := _arbitrary(value)) is not None:
        return raw
    if value == "full":
        return "100%"
    if value == "auto":
        return "auto"
    if value == "screen":
        return "100vw"
    if value == "fr":
        return "1fr"
    if re.fullmatch(r"\d+fr", value):
        return value
    if re.fullmatch(_NUM, value):
        return value
    if m := re.fullmatch(r"(\d+)/(\d+)", value):
        num, den = int(m[1]), int(m[2])
        if den == 0:
            raise TailError(f"division by zero in size '{value}'")
        pct = num * 100 / den
        return f"{pct:g}%" if pct == int(pct) else f"{pct:.4f}%"
    raise TailError(f"invalid size value '{value}'")


def color_value(token: str, sources: dict[str, str], utility: str) -> str:
    """Resolve a color token to TCSS.

    `success` -> `$success`, `success/20` -> `$success 20%`, `red` -> `$red`
    (themeable palette), `[#1a2b3c]` -> `#1a2b3c`, `[red]` -> `red`. Theme variables referenced are recorded in
    `sources` (var -> utility) so the app can validate them against the theme.
    """
    alpha = ""
    if "/" in token and not token.startswith("["):
        token, _, pct = token.rpartition("/")
        if not pct.isdigit() or not 0 <= int(pct) <= 100:
            raise TailError(f"invalid opacity '/{pct}' in '{utility}'")
        alpha = f" {int(pct)}%"
    if (raw := _arbitrary(token)) is not None:
        return raw + alpha
    if token in ("transparent", "none"):
        return "transparent"
    name = COLOR_ALIASES.get(token, token)
    if name in PALETTE:  # themeable palette wins over CSS color names
        sources[name] = utility
        return f"${name}{alpha}"
    # NB: never probe with Color.parse() + except: a failed parse runs a fuzzy
    # "did you mean" search over every color name (~0.8 ms per token).
    if _is_named_color(name):
        return name + alpha
    if not _RE_TOKEN.fullmatch(name):
        raise TailError(f"invalid color '{token}' in '{utility}'")
    sources[name] = utility
    return f"${name}{alpha}"


# --------------------------------------------------------------------------- #
# Per-variant accumulator
# --------------------------------------------------------------------------- #

@dataclass
class _Block:
    """All declarations for one selector (base, `:hover`, `md:` ...)."""

    props: dict[str, str] = field(default_factory=dict)
    text_style: dict[str, bool] = field(default_factory=dict)  # flag -> on/off, ordered
    text_style_cleared: bool = False
    border_type: str | None = None
    border_color: str | None = None
    border_sides: set[str] = field(default_factory=set)
    border_none: bool = False
    grid_cols: str | None = None
    grid_rows: str | None = None
    gutter: list[str | None] = field(default_factory=lambda: [None, None])  # [h, v]
    title: dict[str, dict] = field(default_factory=lambda: {"title": {}, "subtitle": {}})

    def declarations(self) -> dict[str, str]:
        out = dict(self.props)
        if self.text_style:
            flags = [k for k, on in self.text_style.items() if on]
            out["text-style"] = " ".join(flags) if flags else "none"
        elif self.text_style_cleared:
            out["text-style"] = "none"
        if self.border_none:
            out["border"] = "none"
        elif self.border_type or self.border_color or self.border_sides:
            spec = f"{self.border_type or 'solid'} {self.border_color or '$line'}"
            sides = self.border_sides or set(ALL_SIDES)
            if sides == set(ALL_SIDES):
                out["border"] = spec
            else:
                for side in ALL_SIDES:
                    if side in sides:
                        out[f"border-{side}"] = spec
        if self.grid_cols or self.grid_rows:
            out.setdefault("layout", "grid")
            out["grid-size"] = f"{self.grid_cols or 1} {self.grid_rows}" if self.grid_rows else str(self.grid_cols)
        h, v = self.gutter
        if h is not None or v is not None:
            out["grid-gutter"] = f"{h or 0} {v or 0}"
        for kind, spec in self.title.items():
            prefix = f"border-{kind}"
            if "color" in spec:
                out[f"{prefix}-color"] = spec["color"]
            if "background" in spec:
                out[f"{prefix}-background"] = spec["background"]
            if "align" in spec:
                out[f"{prefix}-align"] = spec["align"]
            if spec.get("style"):
                out[f"{prefix}-style"] = " ".join(spec["style"])
        return out


def _apply(block: _Block, util: str, sources: dict[str, str]) -> None:
    """Apply one utility (variant prefix already stripped) to a block."""
    if util in STATIC:
        block.props.update(STATIC[util])
        return

    # -- text style flags ----------------------------------------------------
    if util in TEXT_STYLES:
        block.text_style.pop(util, None)
        block.text_style[util] = True
        return
    if util in TEXT_STYLE_OFF:
        block.text_style[TEXT_STYLE_OFF[util]] = False
        return
    if util == "style-none":
        block.text_style.clear()
        block.text_style_cleared = True
        return

    # -- sizes ---------------------------------------------------------------
    if m := _RE_SIZE.match(util):
        prop = SIZE_PROPS[m[1]]
        value = size_value(m[2])
        if value == "100vw" and prop in ("height", "min-height", "max-height"):
            value = "100vh"
        block.props[prop] = value
        return

    # -- padding / margin ----------------------------------------------------
    if m := _RE_SPACE.match(util):
        neg, kind, side, raw = m[1], SPACE_PROPS[m[2]], m[3], m[4]
        if neg and kind == "padding":
            raise TailError(f"negative padding is not allowed: '{util}'")
        if (arb := _arbitrary(raw)) is not None:
            raw = arb
        elif not raw.isdigit():
            raise TailError(f"invalid spacing '{util}'")
        value = f"-{raw}" if neg else raw
        for s in SPACE_SIDES[side]:
            block.props[f"{kind}-{s}"] = value
        return

    # -- grid ----------------------------------------------------------------
    if m := re.fullmatch(r"grid-(cols|rows)-(.+)", util):
        axis, raw = m[1], m[2]
        if (arb := _arbitrary(raw)) is not None:
            # explicit track sizes; they repeat, so they never fix the row count
            block.props["grid-columns" if axis == "cols" else "grid-rows"] = arb
            if axis == "cols" and block.grid_cols is None:
                block.grid_cols = str(len(arb.split()))
        elif raw.isdigit():
            if axis == "cols":
                block.grid_cols = raw
            else:
                block.grid_rows = raw
        else:
            raise TailError(f"invalid grid value '{util}'")
        block.props.setdefault("layout", "grid")
        return
    if m := re.fullmatch(r"(col|row)-span-(\d+)", util):
        block.props["column-span" if m[1] == "col" else "row-span"] = m[2]
        return
    if m := re.fullmatch(r"gap(-[xy])?-(\d+)", util):
        if m[1] in (None, "-x"):
            block.gutter[0] = m[2]
        if m[1] in (None, "-y"):
            block.gutter[1] = m[2]
        return

    # -- opacity -------------------------------------------------------------
    if m := re.fullmatch(r"(text-)?opacity-(\d+)", util):
        pct = int(m[2])
        if pct > 100:
            raise TailError(f"opacity above 100 in '{util}'")
        block.props["text-opacity" if m[1] else "opacity"] = f"{pct}%"
        return

    # -- borders -------------------------------------------------------------
    if util == "border":
        block.border_none = False
        block.border_type = block.border_type or "solid"
        return
    if util == "border-none":
        block.border_none = True
        return
    if util.startswith("border-"):
        rest = util[len("border-"):]
        block.border_none = False
        if rest in BORDER_TYPES:
            block.border_type = rest
        elif rest in SIDES:
            block.border_sides.update(SIDES[rest])
        else:
            block.border_color = color_value(rest, sources, util)
        return

    # -- border title / subtitle --------------------------------------------
    if m := re.fullmatch(r"(title|subtitle)-(.+)", util):
        spec, rest = block.title[m[1]], m[2]
        if rest in ("left", "center", "right"):
            spec["align"] = rest
        elif rest in TEXT_STYLES:
            spec.setdefault("style", []).append(rest)
        elif rest.startswith("bg-"):
            spec["background"] = color_value(rest[3:], sources, util)
        else:
            spec["color"] = color_value(rest, sources, util)
        return

    # -- colors --------------------------------------------------------------
    if util.startswith("text-"):
        block.props["color"] = color_value(util[5:], sources, util)
        return
    if util.startswith("bg-"):
        block.props["background"] = color_value(util[3:], sources, util)
        return
    if util.startswith("tint-"):
        block.props["tint"] = color_value(util[5:], sources, util)
        return
    if util.startswith("scrollbar-"):
        block.props["scrollbar-color"] = color_value(util[10:], sources, util)
        return
    if util.startswith("hatch-"):
        # hatch-cross, hatch-right-success/30
        parts = util[6:].split("-", 1)
        kind = parts[0]
        if kind not in ("left", "right", "cross", "vertical", "horizontal"):
            raise TailError(f"invalid hatch '{util}'")
        color = color_value(parts[1], sources, util) if len(parts) > 1 else "$foreground 20%"
        block.props["hatch"] = f"{kind} {color}"
        return

    raise TailError(f"unknown utility '{util}'")


# --------------------------------------------------------------------------- #
# Compile
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Compiled:
    """The result of compiling one class string."""

    name: str  # generated Textual class name, e.g. "tw-3fa9c1d2e0"
    css: str  # TCSS for that class (may be empty)
    transforms: tuple[str, ...]  # content transforms (uppercase, tracking-wide ...)
    variables: tuple[tuple[str, str], ...]  # (theme variable, utility that used it)


def split_tokens(cls: str) -> list[str]:
    return cls.split()


def _split_variants(token: str) -> tuple[list[str], str]:
    """`md:hover:bg-panel` -> (['md', 'hover'], 'bg-panel'). Colons inside [] are kept."""
    parts, depth, cur = [], 0, ""
    for ch in token:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == ":" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return parts, cur


def _selector(name: str, variants: list[str]) -> list[str]:
    """Build the selector(s) for a variant chain."""
    pseudo = ""
    group = ""
    breakpoint: str | None = None
    for v in variants:
        if v in PSEUDO_VARIANTS:
            pseudo += PSEUDO_VARIANTS[v]
        elif v.startswith("group-") and v[6:] in PSEUDO_VARIANTS:
            group += PSEUDO_VARIANTS[v[6:]]
        elif v in BREAKPOINTS:
            if breakpoint is not None:
                raise TailError(f"more than one breakpoint in variant chain: {variants}")
            breakpoint = v
        else:
            raise TailError(f"unknown variant '{v}:'")
    sel = f".{name}{pseudo}"
    if group:
        sel = f".group{group} {sel}"
    if breakpoint is None:
        return [sel]
    # min-width semantics: md: applies at md and every larger breakpoint
    idx = BREAKPOINT_ORDER.index(breakpoint)
    return [f"Screen.-tw-{bp} {sel}" for bp in BREAKPOINT_ORDER[idx:]]


def class_name_for(cls: str) -> str:
    digest = hashlib.blake2s(cls.encode(), digest_size=5).hexdigest()
    return f"tw-{digest}"


@lru_cache(maxsize=4096)
def compile_cls(cls: str) -> Compiled:
    """Compile a class string. Cached; raises TailError on bad input."""
    tokens = split_tokens(cls)
    normalized = " ".join(tokens)
    name = class_name_for(normalized)
    blocks: dict[tuple[str, ...], _Block] = {}
    transforms: dict[str, None] = {}
    sources: dict[str, str] = {}

    for token in tokens:
        variants, util = _split_variants(token)
        if util in TRANSFORMS:
            if variants:
                raise TailError(f"'{util}' is a content transform and can't take variants: '{token}'")
            if util.startswith("tracking-"):
                for t in [t for t in transforms if t.startswith("tracking-")]:
                    del transforms[t]
            transforms[util] = None
            continue
        block = blocks.setdefault(tuple(variants), _Block())
        try:
            _apply(block, util, sources)
        except TailError as error:
            raise TailError(f"{error} (in cls={cls!r})") from None

    rules = []
    for variants, block in blocks.items():
        decls = block.declarations()
        if not decls:
            continue
        selectors = _selector(name, list(variants))
        body = "\n".join(f"    {k}: {v};" for k, v in decls.items())
        rules.append(f"{', '.join(selectors)} {{\n{body}\n}}")

    return Compiled(
        name=name,
        css="\n".join(rules),
        transforms=tuple(transforms),
        variables=tuple(sources.items()),
    )


def merge(*classes: str | None) -> str:
    """Concatenate class strings; later ones win on conflicts (at compile time)."""
    return " ".join(c for c in classes if c)


def apply_transforms(text: str, transforms: tuple[str, ...]) -> str:
    for t in transforms:
        if t == "uppercase":
            text = text.upper()
        elif t == "lowercase":
            text = text.lower()
        elif t == "capitalize":
            text = text.title()
        elif t == "tracking-wide":
            text = " ".join(text)
        elif t == "tracking-wider":
            text = "  ".join(text)
    return text
