"""The layering rule: styling -> core -> components -> app.

A module may import only from its own layer or the layers before it, and only
`_textual.py` may touch Textual's private API.
"""

import ast
from pathlib import Path

import pytest

import tui_z

ROOT = Path(tui_z.__file__).parent
LAYERS = ["_textual", "styling", "core", "components", "app"]
SKIP = {"__init__"}  # the package init re-exports everything


def layer_of(module: str) -> int | None:
    """'tui_z.core.tw' -> index of 'core' in LAYERS."""
    parts = module.split(".")
    if parts[0] != "tui_z" or len(parts) < 2:
        return None
    return LAYERS.index(parts[1]) if parts[1] in LAYERS else None


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT.parent).with_suffix("")
    return ".".join(p for p in rel.parts if p != "__init__") if rel.name == "__init__" else ".".join(rel.parts)


def imports(path: Path) -> list[tuple[str, int]]:
    """Absolute module names imported by a file, with line numbers."""
    tree = ast.parse(path.read_text())
    package = module_name(path) if path.name == "__init__.py" else module_name(path).rpartition(".")[0]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                base = base[: len(base) - (node.level - 1)]
                name = ".".join([*base, node.module] if node.module else base)
            else:
                name = node.module or ""
            out.append((name, node.lineno))
            out += [(f"{name}.{a.name}", node.lineno) for a in node.names]
        elif isinstance(node, ast.Import):
            out += [(a.name, node.lineno) for a in node.names]
    return out


SOURCES = [p for p in ROOT.rglob("*.py") if p.stem not in SKIP or p.parent != ROOT]


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(ROOT)))
def test_imports_only_from_lower_layers(path):
    own = layer_of(module_name(path))
    assert own is not None, f"{path} is outside the known layers {LAYERS}"
    for name, line in imports(path):
        other = layer_of(name)
        if other is not None:
            assert other <= own, f"{path.name}:{line} imports {name} (layer {LAYERS[other]} > {LAYERS[own]})"


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(ROOT)))
def test_private_textual_api_only_in_compat_module(path):
    if path.stem == "_textual":
        return
    for name, line in imports(path):
        parts = name.split(".")
        if parts[0] == "textual":
            assert not any(p.startswith("_") for p in parts), f"{path.name}:{line} imports {name}"
