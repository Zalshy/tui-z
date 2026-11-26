import pytest
from helpers import plain

from tui_z import Heatmap, TailError


async def test_heatmap_shades_by_value(mount):
    hm = Heatmap([[0, 5, 10]], color="success", row_labels=["Mon"], col_labels=["a", "b", "c"], steps=2)
    async with mount(hm):
        lines = plain(hm).split("\n")
        assert lines == ["    a b c ", "Mon       "]
        styles = [s.style for s in hm.render().spans]
        assert "on $success 50%" in styles and "on $success 100%" in styles and "on $panel" in styles


def test_shade_buckets():
    hm = Heatmap(steps=4)
    assert [hm.shade(v, 0, 8) for v in (0, 1, 2, 4, 8, 99)] == [-1, 0, 0, 1, 3, 3]


async def test_heatmap_data_setter_color_and_empty(mount):
    hm = Heatmap([], cell=1)
    async with mount(hm) as (app, pilot):
        assert plain(hm) == ""
        hm.data = [[1, 2], [3, 4]]
        hm.set_color("error")
        await pilot.pause()
        assert hm.data == [[1, 2], [3, 4]] and hm.outer_size == (2, 2)
        assert any("$error" in s.style for s in hm.render().spans)
        with pytest.raises(TailError, match="nope"):
            hm.set_color("nope")
        with pytest.raises(ValueError):
            Heatmap(cell=0)
