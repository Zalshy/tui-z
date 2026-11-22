"""Micro/meso benchmarks for tui-z hot paths.

    uv run python benchmarks/bench.py

Each line: what was measured, total time, per-operation time.
"""

from __future__ import annotations

import asyncio
import random
import time
from contextlib import contextmanager

from textual.app import ComposeResult

from tui_z import (
    Badge,
    Bar,
    Box,
    LineChart,
    LogView,
    Row,
    Sparkline,
    Stat,
    Table,
    Text,
    Ticker,
    TwApp,
    registry,
)
from tui_z.engine import compile_cls

RESULTS: list[tuple[str, float, int]] = []


@contextmanager
def timed(label: str, n: int = 1):
    t0 = time.perf_counter()
    yield
    RESULTS.append((label, time.perf_counter() - t0, n))


def report() -> None:
    for label, total, n in RESULTS:
        per = total / n
        unit = f"{per * 1e6:8.1f} µs" if per < 1e-3 else f"{per * 1e3:8.2f} ms"
        print(f"{label:58} {total * 1e3:9.1f} ms total  {unit} / op  (n={n})")


def bench_engine() -> None:
    compile_cls.cache_clear()
    strings = [f"w-{i} h-auto px-1 text-success bg-panel/20 border-round hover:bg-boost md:grid-cols-3"
               for i in range(2000)]
    with timed("engine: compile 2000 unique class strings", 2000):
        for s in strings:
            compile_cls(s)
    with timed("engine: compile 2000 cached class strings", 2000):
        for s in strings:
            compile_cls(s)


class Many(TwApp):
    """Startup with lots of widgets / unique classes."""

    def __init__(self, n: int, unique: bool) -> None:
        super().__init__()
        self.n, self.unique = n, unique

    def compose(self) -> ComposeResult:
        for i in range(self.n):
            w = f"w-{i % 400 + 1}" if self.unique else "w-10"
            yield Row(Badge("TAG", cls="bg-info/20 text-info mr-1"), Text(f"row {i}", f"{w} text-muted"),
                      Bar(0.5, "w-10 text-success"), cls="h-1")


class Live(TwApp):
    def compose(self) -> ComposeResult:
        self.text = Text("0", "w-10 text-success")
        self.auto_text = Text("0", "text-success")
        self.stat = Stat("PnL", "0", cls="w-12", value_cls="text-success")
        self.chart = LineChart([random.random() for _ in range(500)], "w-100 h-12 text-success",
                               series=[([random.random() for _ in range(500)], "purple"),
                                       ([random.random() for _ in range(500)], "cyan")], lo=0, hi=1)
        self.area = LineChart([random.random() for _ in range(500)], "w-100 h-12 text-success", fill=True)
        self.spark = Sparkline([random.random() for _ in range(500)], "w-100 h-6 text-blue", lo=0, hi=1)
        self.ticker = Ticker([f"[$success]item {i}[/]" for i in range(30)], "w-100")
        self.logv = LogView(cls="h-20", max_lines=200)
        self.table = Table([("A", "w-10"), ("B", "w-10 text-right")], [], max_rows=20)
        yield Box(self.text, self.auto_text, self.stat, self.chart, self.area, self.spark,
                  self.ticker, self.logv, self.table)


async def bench_app() -> None:
    for n, unique in ((300, False), (300, True)):
        app = Many(n, unique)
        registry_before = registry.version()
        t0 = time.perf_counter()
        async with app.run_test(size=(200, 60)) as pilot:
            await pilot.pause()
            label = (f"startup: {n} rows ({'unique' if unique else 'shared'} classes, "
                     f"{registry.version() - registry_before} new)")
            RESULTS.append((label, time.perf_counter() - t0, 1))

    app = Live()
    async with app.run_test(size=(200, 80)) as pilot:
        await pilot.pause()

        # one new class on a live widget -> stylesheet flush
        with timed("set_cls: new class on live widget (flush)", 20):
            for i in range(20):
                app.text.set_cls(f"w-10 text-success mt-{i + 50}")
        with timed("set_cls: same class again (no-op path)", 2000):
            for _ in range(2000):
                app.text.set_cls("w-10 text-success mt-50")
        with timed("Text.update fixed-size widget", 2000):
            for i in range(2000):
                app.text.update(str(i))
        with timed("Text.update same value", 2000):
            for _ in range(2000):
                app.text.update("same")
        with timed("Stat.update(value, value_cls) alternating", 2000):
            for i in range(2000):
                app.stat.update(str(i), "text-success" if i % 2 else "text-error")
        await pilot.pause()

        with timed("LineChart.render 100x12, 3 series", 200):
            for _ in range(200):
                app.chart.render()
        with timed("LineChart.render 100x12 area fill", 200):
            for _ in range(200):
                app.area.render()
        with timed("LineChart.push (3 series)", 5000):
            for _ in range(5000):
                app.chart.push(random.random(), random.random(), random.random())
        with timed("Sparkline.render 100x6", 500):
            for _ in range(500):
                app.spark.render()
        with timed("Sparkline.push", 5000):
            for _ in range(5000):
                app.spark.push(random.random())
        with timed("Ticker.render (one frame)", 2000):
            for _ in range(2000):
                app.ticker._advance()
                app.ticker.render()
        await pilot.pause()

        t0 = time.perf_counter()
        for i in range(500):
            app.logv.write(f"message {i} [$muted]details[/]", tag="BUY", tag_cls="bg-success/20 text-success")
        await pilot.pause()
        RESULTS.append(("LogView.write x500 (+ settle)", time.perf_counter() - t0, 500))

        t0 = time.perf_counter()
        for i in range(200):
            app.table.add_row([str(i), (f"{i}.00", "text-success")], top=True)
        await pilot.pause()
        RESULTS.append(("Table.add_row(top, max_rows=20) x200 (+ settle)", time.perf_counter() - t0, 200))

        t0 = time.perf_counter()
        for i in range(50):
            app.table.set_rows([[str(i), str(j)] for j in range(20)])
        await pilot.pause()
        RESULTS.append(("Table.set_rows(20 rows) x50 (+ settle)", time.perf_counter() - t0, 50))

        t0 = time.perf_counter()
        for name in ("tokyo-night", "catppuccin-latte", "terminal", "amber"):
            app.theme = name
            await pilot.pause()
        RESULTS.append(("theme switch (+ settle)", time.perf_counter() - t0, 4))


if __name__ == "__main__":
    bench_engine()
    asyncio.run(bench_app())
    report()
