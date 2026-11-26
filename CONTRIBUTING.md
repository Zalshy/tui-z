# Contributing

Thanks for your interest in tui-z! Issues and pull requests are welcome.

## Setup

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.14 for you if needed.

```bash
git clone https://github.com/Zalshy/tui-z && cd tui-z
uv sync
uv run python demos/showcase.py   # check everything renders
```

## Before opening a pull request

```bash
uv run pytest          # all tests must pass
uvx ruff check .       # no lint errors
```

- **Add a test** for any new utility, component or bug fix. The tests in `tests/` run apps headlessly with `App.run_test()`.
- **Respect the layers.** `styling` → `core` → `components` → `app`: a module imports only from the layers before it (see [docs/internals.md](docs/internals.md#code-layout)). Textual private API goes in `_textual.py` only.
- **Keep the class-string design.** New styling features should be utilities (`cls="..."`), not new keyword arguments. Keyword arguments are for data and behavior.
- **Fail loudly.** An unsupported utility should raise `TailError` with a helpful message.
- **Mind performance.** If you change `styling/`, `core/`, `components/data.py` or `components/charts/`, run `uv run python benchmarks/bench.py` before and after, and include the numbers in the pull request.
- **Update the docs.** Add new utilities to `docs/utilities.md` and new components to `docs/components.md`, and note user-facing changes in `CHANGELOG.md`.
- **Regenerate the README GIF** after a visual change: `uv run python scripts/demo_gif.py`.

## Reporting bugs

Please include:

- your terminal, OS, Python version and Textual version
- a minimal app that reproduces the problem
- the full traceback, or a screenshot (`ctrl+p` → *Save screenshot* in any Textual app)

For security issues, see [SECURITY.md](SECURITY.md).
