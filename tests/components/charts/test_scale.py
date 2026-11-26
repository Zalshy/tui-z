import pytest

from tui_z.components.charts._scale import Range, Series, fmt, resample, runs, token_style


def test_series_trims_in_bulk_and_keeps_the_newest():
    s = Series(range(10), keep=4)
    assert list(s) == [6, 7, 8, 9]
    for v in range(10, 13):
        s.push(v)
    assert len(s) == 7 and s.tail(4) == [9, 10, 11, 12]
    s.push(13)  # reaches 2x keep -> trimmed back to keep
    assert list(s) == [10, 11, 12, 13]
    assert s.tail(0) == []


def test_resample():
    assert resample([], 5) == [] and resample([1.0], 0) == []
    assert resample([2.0], 3) == [2.0, 2.0, 2.0]
    assert resample([0.0, 10.0], 3) == [0.0, 5.0, 10.0]
    assert resample([0.0, 1.0, 2.0, 3.0], 2) == [0.0, 3.0]


def test_runs_merge_same_style_cells():
    cells = [("a", "x"), ("b", "x"), ("c", "y"), ("d", "x")]
    assert runs(cells) == [("ab", "x"), ("c", "y"), ("d", "x")]
    assert runs([]) == []


@pytest.mark.parametrize(("value", "text"), [
    (0.5, "0.5"), (1.0, "1"), (12.34, "12.3"), (150.4, "150"), (12_345, "12k"), (2_500_000, "2.5M"), (-0.25, "-0.25"),
])
def test_fmt(value, text):
    assert fmt(value) == text


def test_token_style():
    assert token_style("success") == "$success" and token_style("") == ""


def test_range_fixed_and_empty():
    assert Range(0, 10)([3, 4]) == (0, 10)
    assert Range(None, None)([]) == (0.0, 1.0)
    assert Range(5, 5)([5]) == (4, 6)  # degenerate range is widened


def test_range_is_sticky_until_data_shrinks_a_lot():
    r = Range(None, None, headroom=0.0)
    assert r([0, 10]) == (0, 10)
    assert r([2, 8]) == (0, 10)  # inside: unchanged
    assert r([0, 12]) == (0, 12)  # grows to a new extreme
    assert r([5, 6]) == (5, 6)  # uses < 40% of the range: shrinks


def test_range_not_sticky_follows_data():
    r = Range(None, None, sticky=False)
    assert r([1, 3]) == (1, 3)
    assert r([2, 2.5]) == (2, 2.5)
    assert Range(None, None, sticky=False)([4, 4]) == (3, 5)
