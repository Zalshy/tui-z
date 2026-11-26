from helpers import plain

from tui_z import Sparkline


async def test_sparkline_stream_scrolls(mount):
    s = Sparkline([float(i % 5) for i in range(50)], "w-20 h-2", lo=0, hi=4)
    async with mount(s) as (app, pilot):
        before = plain(s).split("\n")
        s.push(2.0)
        await pilot.pause()
        after = plain(s).split("\n")
        for b, a in zip(before, after):
            assert a[:-1] == b[1:]


async def test_sparkline_stretch_fits_the_width(mount):
    s = Sparkline([0.0, 1.0], "w-8 h-1", stretch=True)
    async with mount(s):
        assert plain(s) == "▁▂▃▄▅▆▇█"


async def test_sparkline_short_data_is_right_aligned_and_replaceable(mount):
    s = Sparkline([1.0, 1.0], "w-6 h-1", lo=0, hi=1)
    empty = Sparkline([], "w-6")
    async with mount(s, empty):
        assert plain(s) == "    ██"
        assert plain(empty) == ""
        s.data = [0.0]
        assert list(s.data) == [0.0] and plain(s) == "     ▁"
