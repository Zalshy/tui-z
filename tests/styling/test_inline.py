import pytest

from tui_z import TailError
from tui_z.styling.inline import column, inline, layout_columns, row_variants


def test_inline_styles():
    assert inline("bold text-success bg-panel/40").style == "bold $success on $panel 40%"
    assert inline("uppercase text-[#ff0000]").transforms == ("uppercase",)
    assert inline("text-success").variables == ("success",)
    with pytest.raises(TailError):
        inline("border")  # not a text-level utility


def test_inline_font_normal_and_truncate():
    assert inline("bold font-normal italic").style == "italic"
    assert inline("truncate text-muted").style == "$muted"  # cells always truncate


def test_column_spec_and_layout():
    a, b, c = column("w-4 text-muted"), column("w-fr text-right bold"), column("w-2fr")
    assert (a.width, b.width, b.align, c.fr) == (4, None, "right", 2)
    widths = layout_columns([a, b, c], 40, gap=1)
    assert widths[0] == 4
    assert sum(widths) + 2 == 40  # columns + 2 gaps fill the width exactly
    assert abs(widths[2] - 2 * widths[1]) <= 1  # 2fr is twice 1fr


def test_column_center_and_grow():
    spec = column("grow text-center")
    assert (spec.width, spec.fr, spec.align) == (None, 1, "center")
    with pytest.raises(TailError, match="column width"):
        column("w-1/2")


def test_layout_columns_never_negative():
    assert layout_columns([column("w-10"), column("w-fr")], 5) == [10, 0]


def test_row_variants():
    v = row_variants("odd:bg-panel hover:bg-boost text-muted")
    assert set(v) == {"", "odd", "hover"}
    with pytest.raises(TailError):
        row_variants("focus:bg-panel")
