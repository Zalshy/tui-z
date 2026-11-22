"""Startup time + steady-state CPU of the showcase (headless).

    uv run python benchmarks/cpu.py [seconds]

CPU% = process CPU time / wall time while the app runs its live timers.
Headless: Textual still lays out and composites every frame, but does not
write to a real terminal, so a real terminal adds some output cost on top.
"""

from __future__ import annotations

import asyncio
import cProfile
import pstats
import resource
import sys
import time

sys.path.insert(0, "demos")
from showcase import Showcase


def cpu() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


async def main(seconds: float) -> None:
    t0, c0 = time.perf_counter(), cpu()
    app = Showcase()
    async with app.run_test(size=(200, 60)) as pilot:
        await pilot.pause()
        t1, c1 = time.perf_counter(), cpu()
        print(f"startup to first frame: {t1 - t0:.2f}s wall, {c1 - c0:.2f}s CPU")

        for tab in ("dashboard", "components"):
            app.action_tab(tab)
            await pilot.pause(1.0)
            w0, k0 = time.perf_counter(), cpu()
            await asyncio.sleep(seconds)
            w1, k1 = time.perf_counter(), cpu()
            print(f"steady state, {tab:10} tab: {100 * (k1 - k0) / (w1 - w0):5.1f}% of one core "
                  f"over {w1 - w0:.0f}s")

        app.action_tab("dashboard")
        await pilot.pause(1.0)
        prof = cProfile.Profile()
        prof.enable()
        await asyncio.sleep(seconds)
        prof.disable()
        stats = pstats.Stats(prof)
        total = stats.total_tt
        ours = sum(v[2] for k, v in stats.stats.items() if "tui_z" in k[0] or "showcase" in k[0])
        print(f"\nprofile of {seconds:.0f}s on dashboard: {total:.2f}s CPU in Python; "
              f"tui-z + demo code (own time): {ours:.2f}s ({100 * ours / total:.0f}%)")
        print("top 12 by own time:")
        stats.sort_stats("tottime").print_stats(12)


if __name__ == "__main__":
    asyncio.run(main(float(sys.argv[1]) if len(sys.argv) > 1 else 10.0))
