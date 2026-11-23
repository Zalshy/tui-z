<div align="center">

# Tui-z

**Small class strings. Big terminal UIs.**

[![CI](https://github.com/Zalshy/tui-z/actions/workflows/ci.yml/badge.svg)](https://github.com/Zalshy/tui-z/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![Status](https://img.shields.io/badge/status-alpha-orange)

<img src="docs/assets/showcase.gif" alt="The tui-z showcase: a live dashboard with streaming charts, tables and a log, switching between themes" width="100%">

</div>

Tui-z lets you style terminal apps with short class strings: `"border bg-surface text-success bold"`.
It comes with ready-made components for dashboards, such as panels, tables, live charts and logs, and ten themes.
Built on [Textual](https://textual.textualize.io).

## Example

```python
from tui_z import TwApp, Panel, Row, Text, Badge, Bar, Button

class Demo(TwApp):
    def compose(self):
        yield Panel(
            Row(Text("Rates cut in Q1?", "bold grow"),
                Text("67¢", "w-6 text-right text-success bold")),
            Bar(0.67, "w-20 text-success"),
            Button("Buy yes", "text-success border-success"),
            title="Live markets",
            badge=Badge("Watching 47"),
            cls="w-60 m-1",
        )

Demo().run()
```

## Install

```bash
pip install git+https://github.com/Zalshy/tui-z
```

Python 3.12+. Not on PyPI yet.

## See it live

```bash
git clone https://github.com/Zalshy/tui-z && cd tui-z
uv run python demos/showcase.py
```

`[` `]` switch themes · `b` toggle the sidebar · `1`–`5` switch tabs · `q` quit

## What's inside

- **Layout**: `Row`, `Col`, `Grid`, `Panel`, `Sidebar` and more
- **Data**: `Table`, `LogView`, `Ticker`, `Stat`, `Badge`
- **Charts**: `Bar`, `Sparkline`, `LineChart`, all streaming live
- **Themes**: Catppuccin, Tokyo Night and two of our own. Switch anytime.
- **Responsive**: `md:grid-cols-2` adapts to the terminal width
- **Fast**: tables and logs only draw what's on screen

## Docs

[Getting started](docs/getting-started.md) ·
[Utilities](docs/utilities.md) ·
[Components](docs/components.md) ·
[Theming](docs/theming.md) ·
[Custom components](docs/custom-components.md) ·
[Internals](docs/internals.md)

## License

MIT © Zalshy
