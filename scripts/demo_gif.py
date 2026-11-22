"""Render an animated GIF of the showcase for the README.

    uv run python scripts/demo_gif.py                 # -> docs/assets/showcase.gif
    uv run python scripts/demo_gif.py --size 170x50 --fps 10

The showcase runs headlessly (seeded, so every run looks the same). Each frame
is captured as styled terminal cells and drawn with Pillow:

- text uses DejaVu Sans Mono (falls back to other installed fonts per glyph),
- braille, block elements and box-drawing lines are drawn as shapes, so charts
  and borders are pixel-perfect and gapless whatever the font.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import random
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.segment import Segment
from rich.style import Style

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "demos"))

from showcase import Showcase  # noqa: E402

# --------------------------------------------------------------------------- #
# Capture
# --------------------------------------------------------------------------- #

type Cell = tuple[str, Style]
type Frame = list[list[Segment]]


def capture(app: Showcase) -> Frame:
    """The screen as lines of styled segments (what Textual would paint)."""
    width, height = app.size
    console = Console(width=width, height=height, file=io.StringIO(), force_terminal=True,
                      color_system="truecolor", record=True, legacy_windows=False, safe_box=False)
    console.print(app.screen._compositor.render_update(full=True, screen_stack=app._background_screens))
    lines = list(Segment.split_and_crop_lines(console._record_buffer, width, pad=True))
    return [[Segment(s.text, s.style) for s in line if not s.control] for line in lines[:height]]


async def record(size: tuple[int, int], fps: int, warmup: float,
                 scenes: list[tuple[str, float]]) -> list[tuple[Frame, float]]:
    random.seed(7)
    app = Showcase()
    frames: list[tuple[Frame, float]] = []
    step = 1 / fps
    async with app.run_test(size=size) as pilot:
        app.theme = scenes[0][0]
        await pilot.pause(warmup)  # let the charts and logs fill up
        for theme, seconds in scenes:
            app.theme = theme
            end = time.perf_counter() + seconds
            while time.perf_counter() < end:
                t0 = time.perf_counter()
                await pilot.pause(step)
                frames.append((capture(app), time.perf_counter() - t0))
    return frames


# --------------------------------------------------------------------------- #
# Drawing
# --------------------------------------------------------------------------- #

def font_path(pattern: str) -> str:
    return subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True,
                          check=True).stdout.strip()


class Painter:
    def __init__(self, font_size: int) -> None:
        self.regular = ImageFont.truetype(font_path("DejaVu Sans Mono"), font_size)
        self.bold = ImageFont.truetype(font_path("DejaVu Sans Mono:bold"), font_size)
        self.fallbacks = [ImageFont.truetype(font_path(p), font_size)
                          for p in ("DejaVu Sans", "Noto Sans Symbols2", "Noto Sans")]
        self.cw = round(self.regular.getlength("M"))
        ascent, descent = self.regular.getmetrics()
        self.ch = ascent + descent + 1
        self._missing = {id(f): glyph(f, "\U0010fffd") for f in [self.regular, self.bold, *self.fallbacks]}
        self._fonts: dict[tuple[str, bool], ImageFont.FreeTypeFont] = {}

    def font_for(self, char: str, bold: bool) -> ImageFont.FreeTypeFont:
        key = (char, bold)
        if key not in self._fonts:
            first = self.bold if bold else self.regular
            self._fonts[key] = next(
                (f for f in (first, *self.fallbacks) if glyph(f, char) != self._missing[id(f)]), first)
        return self._fonts[key]

    # -- shapes ---------------------------------------------------------------
    def braille(self, d: ImageDraw.ImageDraw, x: int, y: int, code: int, fg) -> None:
        bits = code - 0x2800
        dots = ((0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08),
                (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80))
        r = max(1, self.cw // 5)
        for col, row, bit in dots:
            if bits & bit:
                cx = x + (self.cw * (1 + 2 * col)) // 4
                cy = y + (self.ch * (1 + 2 * row)) // 8
                d.ellipse((cx - r, cy - r, cx + r - 1, cy + r - 1), fill=fg)

    def block(self, d: ImageDraw.ImageDraw, x: int, y: int, char: str, fg) -> bool:
        o = ord(char)
        w, h = self.cw, self.ch
        if 0x2581 <= o <= 0x2588:  # ▁..█ lower eighths
            top = y + h - round(h * (o - 0x2580) / 8)
            d.rectangle((x, top, x + w - 1, y + h - 1), fill=fg)
        elif o == 0x2580:  # ▀
            d.rectangle((x, y, x + w - 1, y + h // 2 - 1), fill=fg)
        elif 0x2589 <= o <= 0x258F:  # ▉..▏ left eighths
            d.rectangle((x, y, x + round(w * (0x2590 - o) / 8) - 1, y + h - 1), fill=fg)
        elif o == 0x2590:  # ▐
            d.rectangle((x + w // 2, y, x + w - 1, y + h - 1), fill=fg)
        elif o == 0x2594:  # ▔
            d.rectangle((x, y, x + w - 1, y + max(1, h // 8) - 1), fill=fg)
        elif o == 0x2595:  # ▕
            d.rectangle((x + w - max(1, w // 8), y, x + w - 1, y + h - 1), fill=fg)
        else:
            return False
        return True

    BOX = {  # char -> (up, down, left, right, weight)
        "─": (0, 0, 1, 1, 1), "━": (0, 0, 1, 1, 2), "│": (1, 1, 0, 0, 1), "┃": (1, 1, 0, 0, 2),
        "┌": (0, 1, 0, 1, 1), "┐": (0, 1, 1, 0, 1), "└": (1, 0, 0, 1, 1), "┘": (1, 0, 1, 0, 1),
        "╭": (0, 1, 0, 1, 1), "╮": (0, 1, 1, 0, 1), "╰": (1, 0, 0, 1, 1), "╯": (1, 0, 1, 0, 1),
        "├": (1, 1, 0, 1, 1), "┤": (1, 1, 1, 0, 1), "┬": (0, 1, 1, 1, 1), "┴": (1, 0, 1, 1, 1),
        "┼": (1, 1, 1, 1, 1), "┏": (0, 1, 0, 1, 2), "┓": (0, 1, 1, 0, 2), "┗": (1, 0, 0, 1, 2),
        "┛": (1, 0, 1, 0, 2), "┣": (1, 1, 0, 1, 2), "┫": (1, 1, 1, 0, 2), "┳": (0, 1, 1, 1, 2),
        "┻": (1, 0, 1, 1, 2), "╋": (1, 1, 1, 1, 2),
        # half lines (used by Textual's Digits)
        "╴": (0, 0, 1, 0, 1), "╵": (1, 0, 0, 0, 1), "╶": (0, 0, 0, 1, 1), "╷": (0, 1, 0, 0, 1),
        "╸": (0, 0, 1, 0, 2), "╹": (1, 0, 0, 0, 2), "╺": (0, 0, 0, 1, 2), "╻": (0, 1, 0, 0, 2),
    }

    def box(self, d: ImageDraw.ImageDraw, x: int, y: int, char: str, fg) -> bool:
        spec = self.BOX.get(char)
        if spec is None:
            return False
        up, down, left, right, weight = spec
        t = weight
        cx, cy = x + (self.cw - t) // 2, y + (self.ch - t) // 2
        if left:
            d.rectangle((x, cy, cx + t - 1, cy + t - 1), fill=fg)
        if right:
            d.rectangle((cx, cy, x + self.cw - 1, cy + t - 1), fill=fg)
        if up:
            d.rectangle((cx, y, cx + t - 1, cy + t - 1), fill=fg)
        if down:
            d.rectangle((cx, cy, cx + t - 1, y + self.ch - 1), fill=fg)
        return True

    # -- frame ----------------------------------------------------------------
    def paint(self, frame: Frame, default_fg, default_bg) -> Image.Image:
        cols = sum(len(s.text) for s in frame[0])
        img = Image.new("RGB", (cols * self.cw, len(frame) * self.ch), default_bg)
        d = ImageDraw.Draw(img)
        for row, line in enumerate(frame):
            y = row * self.ch
            col = 0
            for seg in line:
                style = seg.style or Style()
                fg = rgb(style.color, default_fg)
                bg = rgb(style.bgcolor, default_bg)
                if style.reverse:
                    fg, bg = bg, fg
                if style.dim:
                    fg = blend(fg, bg, 0.5)
                n = len(seg.text)
                x0 = col * self.cw
                if bg != default_bg:
                    d.rectangle((x0, y, x0 + n * self.cw - 1, y + self.ch - 1), fill=bg)
                for i, char in enumerate(seg.text):
                    if char == " ":
                        continue
                    x = x0 + i * self.cw
                    o = ord(char)
                    if 0x2800 < o <= 0x28FF:
                        self.braille(d, x, y, o, fg)
                    elif not (self.block(d, x, y, char, fg) or self.box(d, x, y, char, fg)):
                        d.text((x, y), char, font=self.font_for(char, bool(style.bold)), fill=fg)
                    if style.underline:
                        d.line((x, y + self.ch - 2, x + self.cw - 1, y + self.ch - 2), fill=fg)
                col += n
        return img


def glyph(font: ImageFont.FreeTypeFont, char: str) -> bytes:
    """Rendered bitmap of a glyph (a missing glyph renders as the font's .notdef box)."""
    img = Image.new("L", (48, 48))
    ImageDraw.Draw(img).text((8, 8), char, font=font, fill=255)
    return img.tobytes()


def rgb(color, default):
    if color is None or color.is_default:
        return default
    return color.get_truecolor()[:3]


def blend(a, b, t: float):
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(a, b, strict=True))


def chrome(img: Image.Image, title: str) -> Image.Image:
    """A minimal window frame around the terminal."""
    pad, bar = 14, 34
    w, h = img.width + 2 * pad, img.height + bar + pad
    out = Image.new("RGB", (w, h), (24, 26, 31))
    d = ImageDraw.Draw(out)
    for i, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = pad + 8 + i * 20
        d.ellipse((cx - 6, bar // 2 - 6, cx + 6, bar // 2 + 6), fill=color)
    font = ImageFont.truetype(font_path("DejaVu Sans:bold"), 13)
    d.text((w // 2, bar // 2), title, font=font, fill=(150, 156, 168), anchor="mm")
    out.paste(img, (pad, bar))
    return out


# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--size", default="170x50", help="terminal size, COLSxROWS")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--font-size", type=int, default=13)
    parser.add_argument("--out", default=str(ROOT / "docs" / "assets" / "showcase.gif"))
    args = parser.parse_args()
    cols, rows = map(int, args.size.split("x"))

    scenes = [("terminal", 6.0), ("tokyo-night", 2.2), ("catppuccin-mocha", 2.2),
              ("catppuccin-latte", 2.2), ("tokyo-night-day", 2.2), ("amber", 2.2)]
    t0 = time.perf_counter()
    frames = asyncio.run(record((cols, rows), args.fps, warmup=4.0, scenes=scenes))
    print(f"captured {len(frames)} frames in {time.perf_counter() - t0:.1f}s")

    painter = Painter(args.font_size)
    images, durations = [], []
    for frame, seconds in frames:
        first = frame[0][0].style if frame and frame[0] else None
        bg = rgb(first.bgcolor if first else None, (0, 0, 0))
        img = chrome(painter.paint(frame, (220, 220, 220), bg), "tui-z showcase")
        images.append(img.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations.append(max(20, round(seconds * 1000 / 10) * 10))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, save_all=True, append_images=images[1:], duration=durations, loop=0,
                   optimize=True, disposal=1)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {images[0].width}x{images[0].height}, "
          f"{sum(durations) / 1000:.1f}s) in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
