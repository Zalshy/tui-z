import pytest
from helpers import plain

from tui_z import LineChart


async def test_linechart_stream_scrolls_without_reshaping(mount):
    # step=2 -> one point per cell, so a push shifts by exactly one cell
    chart = LineChart([float(i % 7) for i in range(100)], "w-40 h-4", axis=False, step=2, lo=0, hi=6)
    async with mount(chart) as (app, pilot):
        before = plain(chart).split("\n")
        chart.push(3.0)
        await pilot.pause()
        after = plain(chart).split("\n")
        for b, a in zip(before, after):
            assert a[:-1] == b[1:]  # old part moved left one cell, unchanged


async def test_linechart_axis_labels_marks_and_series(mount):
    chart = LineChart([1.0, 2.0, 3.0], "w-30 h-6", mode="fit", lo=0, hi=4,
                      series=[([3.0, 2.0, 1.0], "purple")], marks=[(2.0, "success", "TP")])
    async with mount(chart) as (app, pilot):
        lines = plain(chart).split("\n")
        assert lines[0].startswith("4 ") and lines[-1].startswith("0 ")
        assert lines[3].startswith("2 ")  # middle label
        mark_row = next(line for line in lines if line.endswith("TP"))
        assert "╌" in mark_row
        chart.push(4.0, 0.0)
        assert list(chart.series[0][0])[-1] == 0.0
        chart.set_series([])
        assert chart.series == []


async def test_linechart_area_fill_reaches_the_bottom(mount):
    line = LineChart([2.0] * 30, "w-10 h-3", axis=False, mode="fit", lo=0, hi=4)
    area = LineChart([2.0] * 30, "w-10 h-3", axis=False, mode="fit", lo=0, hi=4, fill=True)
    async with mount(line, area):
        assert plain(line).split("\n")[-1].strip() == ""
        assert plain(area).split("\n")[-1].strip() != ""


async def test_linechart_empty_and_too_small(mount):
    empty, tiny = LineChart([], "w-20 h-3"), LineChart([1.0, 2.0], "w-3 h-3")
    async with mount(empty, tiny):
        assert plain(empty) == "" and plain(tiny) == ""
        empty.data = [1.0, 2.0]
        assert list(empty.data) == [1.0, 2.0]


def test_linechart_rejects_unknown_mode():
    with pytest.raises(ValueError, match="mode"):
        LineChart([], mode="bars")
