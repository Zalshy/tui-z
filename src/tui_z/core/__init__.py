"""The core layer: the `Tw` mixin, the class registry and stylesheet sync.

Depends only on `tui_z.styling`. Components build on this layer.
"""

from . import registry
from .stylesheet import UtilityStylesheet
from .tw import Tw, transform_markup, tw

__all__ = ["Tw", "UtilityStylesheet", "registry", "transform_markup", "tw"]
