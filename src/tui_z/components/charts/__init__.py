"""Charts drawn with text cells: bars, sparklines, braille line/area charts.

All charts use the widget's text color (`text-*`) for the main series and
theme tokens (`"success"`, `"muted"` ...) for anything extra, so they follow
theme switches.
"""

from .bar import Bar
from .linechart import LineChart
from .sparkline import Sparkline

__all__ = ["Bar", "LineChart", "Sparkline"]
