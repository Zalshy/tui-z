"""Property-based tests for the pure styling layer."""

import re

from hypothesis import given
from hypothesis import strategies as st

from tui_z import compile_cls, merge
from tui_z.styling.inline import ColumnSpec, column, layout_columns

COLORS = ["success", "error", "warning", "panel", "primary", "muted", "[#123456]", "red"]
UTILITIES = (
    [f"{p}-{n}" for p in ("p", "px", "py", "m", "mt", "w", "h") for n in range(4)]
    + [f"text-{c}" for c in COLORS] + [f"bg-{c}" for c in COLORS] + [f"bg-{c}/30" for c in COLORS[:4]]
    + ["bold", "italic", "underline", "border", "border-heavy", "border-b", "uppercase", "row", "col",
       "hidden", "grow", "truncate", "w-fr", "h-auto", "grid-cols-3", "gap-1"]
)
VARIANTS = ["", "hover:", "focus:", "md:", "odd:"]
TRANSFORMS = {"uppercase"}  # content transforms can't take variants
tokens = st.builds(lambda v, u: u if u in TRANSFORMS else v + u, st.sampled_from(VARIANTS), st.sampled_from(UTILITIES))
class_strings = st.lists(tokens, max_size=12).map(" ".join)


@given(class_strings, st.integers(1, 3))
def test_whitespace_never_changes_the_class(cls, spaces):
    assert compile_cls(cls).name == compile_cls((" " * spaces).join(cls.split())).name


@given(class_strings)
def test_compiling_is_deterministic(cls):
    a, b = compile_cls(cls), compile_cls(" ".join(cls.split()))
    assert (a.name, a.css, a.transforms) == (b.name, b.css, b.transforms)


@given(class_strings, st.sampled_from(COLORS), st.sampled_from(COLORS))
def test_last_text_color_wins(prefix, first, last):
    compiled = compile_cls(merge(prefix, f"text-{first}", f"text-{last}"))
    base = re.split(rf"(?m)^\.{compiled.name} \{{", compiled.css)[1].split("}")[0]  # the block without variants
    expected = compile_cls(f"text-{last}").css.split("color: ")[1].split(";")[0]
    assert f"    color: {expected};" in base


specs = st.lists(
    st.one_of(st.integers(0, 30).map(lambda n: column(f"w-{n}")),
              st.integers(1, 4).map(lambda n: column(f"w-{n}fr"))),
    min_size=1, max_size=8,
)


@given(specs, st.integers(0, 300), st.integers(0, 3))
def test_columns_fill_the_width_exactly(columns: list[ColumnSpec], width, gap):
    widths = layout_columns(columns, width, gap)
    assert len(widths) == len(columns)
    assert all(w >= 0 for w in widths)
    for spec, w in zip(columns, widths):
        if spec.width is not None:
            assert w == spec.width
    fixed = sum(s.width for s in columns if s.width is not None)
    gaps = gap * (len(columns) - 1)
    has_fr = any(s.width is None for s in columns)
    if has_fr and width >= fixed + gaps:
        assert sum(widths) + gaps == width
