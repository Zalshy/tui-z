"""The class compiler: turns `cls="text-success bold p-1"` into Textual CSS.

Each *unique class string* compiles to one generated CSS class (``tw-<hash>``).
Compiling the whole string at once (instead of one CSS class per utility) lets
us merge utilities that map onto a single Textual property (``border-heavy`` +
``border-success`` -> ``border: heavy $success``) and resolve conflicts:
for the same property, the **last** utility wins.
That is what makes component defaults overridable:
``merge(component_defaults, user_cls)``.

What each utility means lives in `tui_z.styling.utilities`; this module splits
the string, resolves variants (`hover:`, `md:`) and emits the CSS.

This module is pure: it never touches a running app. Color tokens become
``$variables``; checking that they exist in the theme happens in ``TwApp``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from .errors import TailError
from .utilities import (
    BREAKPOINT_ORDER,
    BREAKPOINTS,
    PSEUDO_VARIANTS,
    TRANSFORMS,
    Block,
    add_transform,
    apply_utility,
)

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


def split_variants(token: str) -> tuple[list[str], str]:
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
    blocks: dict[tuple[str, ...], Block] = {}
    transforms: dict[str, None] = {}
    sources: dict[str, str] = {}

    for token in tokens:
        variants, util = split_variants(token)
        if util in TRANSFORMS:
            if variants:
                raise TailError(f"'{util}' is a content transform and can't take variants: '{token}'")
            add_transform(transforms, util)
            continue
        block = blocks.setdefault(tuple(variants), Block())
        try:
            apply_utility(block, util, sources)
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
