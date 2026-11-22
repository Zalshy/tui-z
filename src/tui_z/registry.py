"""Process-wide registry of compiled class strings.

Widgets register their compiled cls here when created. The registry is an
append-only log; each `TwApp` remembers how far into it it has flushed, so
several apps in one process (tests!) each get the full stylesheet.
"""

from __future__ import annotations

from .engine import Compiled

_compiled: dict[str, Compiled] = {}


def add(compiled: Compiled) -> None:
    _compiled.setdefault(compiled.name, compiled)


def version() -> int:
    return len(_compiled)


def since(version: int) -> list[Compiled]:
    return list(_compiled.values())[version:]


def discard(name: str) -> None:
    _compiled.pop(name, None)


def stylesheet() -> str:
    return "\n".join(c.css for c in _compiled.values() if c.css)
