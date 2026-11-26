from helpers import plain

from tui_z import Bar


async def test_bar_fills_its_share_and_clamps(mount):
    bar = Bar(0.5, "w-10")
    async with mount(bar) as (app, pilot):
        assert plain(bar) == "━" * 10
        filled = bar.render().spans[0]
        assert filled.end - filled.start == 5
        bar.value = 3
        assert bar.value == 1.0
        bar.value = -1
        assert bar.value == 0.0


async def test_bar_without_track(mount):
    bar = Bar(0.3, "w-10", track=False)
    async with mount(bar):
        assert plain(bar) == "━" * 3
