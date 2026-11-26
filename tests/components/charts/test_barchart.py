import pytest
from helpers import plain

from tui_z import BarChart


async def test_bars_scale_to_the_tallest_and_show_labels(mount):
    chart = BarChart([("a", 1), ("b", 2), ("c", 4, "error")], "w-11 h-5", bar_width=3)
    async with mount(chart):
        lines = plain(chart).split("\n")
        assert lines[-1] == " a   b   c "
        assert lines[0] == "        ███"  # only the tallest reaches the top
        assert lines[3] == "███ ███ ███"
        styles = [s.style for s in chart.render().spans]
        assert "$error" in styles and "$muted" in styles


async def test_bar_widths_share_the_space_and_values_sit_on_top(mount):
    chart = BarChart([2.0, 4.0], "w-9 h-4", labels=False, values=True, hi=8)
    async with mount(chart):
        assert plain(chart).split("\n") == [
            "         ",
            "      4  ",  # bars share the width: 4 cells each
            " 2   ████",  # each value sits just above its bar
            "████ ████",
        ]


async def test_bars_that_do_not_fit_are_cut(mount):
    chart = BarChart([1.0] * 20, "w-5 h-2", bar_width=1, labels=False)
    async with mount(chart):
        assert plain(chart).split("\n")[-1] == "█ █ █"


def test_histogram_counts_into_bins():
    chart = BarChart.histogram([0, 1, 1, 2, 9, 10], bins=5)
    assert [v for _, v, _ in chart.data] == [3.0, 1.0, 0.0, 0.0, 2.0]
    assert [label for label, _, _ in chart.data][:2] == ["0", "2"]
    assert BarChart.histogram([]).data == []
    with pytest.raises(ValueError, match="bins"):
        BarChart.histogram([1], bins=0)


async def test_empty_chart_and_set_data(mount):
    chart = BarChart([], "w-10 h-3")
    async with mount(chart):
        assert plain(chart) == ""
        chart.set_data([("x", 1)])
        assert plain(chart).split("\n")[-1].strip() == "x"
