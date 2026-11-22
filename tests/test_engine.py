import pytest

from tui_z.engine import TailError, apply_transforms, compile_cls


def decls(cls: str) -> str:
    return compile_cls(cls).css


def test_same_string_same_class():
    assert compile_cls("p-1 bold").name == compile_cls("p-1   bold").name
    assert compile_cls("p-1 bold").name != compile_cls("p-2 bold").name


def test_colors_resolve_to_theme_vars_with_alpha():
    css = decls("text-success bg-panel/40")
    assert "color: $success;" in css
    assert "background: $panel 40%;" in css
    assert dict(compile_cls("text-success").variables) == {"success": "text-success"}


def test_color_aliases_and_literals():
    assert "color: $error;" in decls("text-danger")
    assert "color: $red;" in decls("text-red")  # themeable palette
    assert "color: red;" in decls("text-[red]")
    assert "color: ansi_bright_green;" in decls("text-ansi_bright_green")
    assert "background: #1a2b3c;" in decls("bg-[#1a2b3c]")


def test_last_utility_wins():
    css = decls("text-success text-error")
    assert "color: $error;" in css and "$success" not in css


def test_border_merges_type_color_and_sides():
    assert "border: heavy $success;" in decls("border-heavy border-success")
    assert "border: solid $line;" in decls("border")
    css = decls("border-b border-error")
    assert "border-bottom: solid $error;" in css and "border:" not in css
    assert "border: none;" in decls("border border-none")


def test_text_style_combines():
    assert "text-style: bold italic;" in decls("bold italic")
    assert "text-style: italic;" in decls("bold italic font-normal")
    assert "text-style: none;" in decls("bold style-none")


def test_spacing_and_sizes():
    css = decls("p-1 px-2 -mt-1 w-1/2 h-fr max-w-[40]")
    for expected in ("padding-top: 1;", "padding-left: 2;", "padding-right: 2;",
                     "margin-top: -1;", "width: 50%;", "height: 1fr;", "max-width: 40;"):
        assert expected in css


def test_grid():
    css = decls("grid-cols-3 gap-1 col-span-2")
    assert "layout: grid;" in css and "grid-size: 3;" in css
    assert "grid-gutter: 1 1;" in css and "column-span: 2;" in css
    assert "grid-columns: 1fr 2fr;" in decls("grid-cols-[1fr_2fr]")


def test_variants():
    c = compile_cls("bg-panel hover:bg-boost focus:border-primary md:grid-cols-3")
    assert f".{c.name}:hover {{" in c.css
    assert f".{c.name}:focus {{" in c.css
    assert f"Screen.-tw-md .{c.name}, Screen.-tw-lg .{c.name}, Screen.-tw-xl .{c.name}" in c.css


def test_transforms_are_not_css():
    c = compile_cls("uppercase tracking-wide text-muted")
    assert c.transforms == ("uppercase", "tracking-wide")
    assert apply_transforms("live", c.transforms) == "L I V E"


@pytest.mark.parametrize("bad", ["nope", "p-x", "-p-1", "opacity-200", "text-[", "wat:bold", "w-1/0"])
def test_errors(bad):
    with pytest.raises(TailError):
        compile_cls(bad)


def test_arbitrary_grid_rows_do_not_fix_row_count():
    css = decls("grid-cols-2 grid-rows-[auto]")
    assert "grid-rows: auto;" in css and "grid-size: 2;" in css
    assert "grid-size: 3;" in decls("grid-cols-[1fr_2fr_1fr]")
