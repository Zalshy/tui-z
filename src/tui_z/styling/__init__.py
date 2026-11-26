"""The styling layer: class strings -> Textual CSS, inline styles and themes.

Pure: nothing here touches a running app or imports a widget.
"""

from .engine import Compiled, apply_transforms, compile_cls, merge
from .errors import TailError
from .inline import inline
from .themes import PALETTE, THEME_NAMES, THEMES, make_theme

__all__ = [
    "PALETTE",
    "THEMES",
    "THEME_NAMES",
    "Compiled",
    "TailError",
    "apply_transforms",
    "compile_cls",
    "inline",
    "make_theme",
    "merge",
]
