# How it works and performance

## The class compiler

1. **Parse.** `compile_cls("border bg-surface hover:bg-boost")` splits the string into utilities, resolves their variants and maps each one to Textual CSS declarations. For the same property, the last utility wins.
2. **One class per string.** The whole string becomes **one** generated class, `tw-<hash>`, whose name is a hash of the normalized string. The same string anywhere in the app reuses the same class.
3. **Register.** The compiled CSS goes into an append-only registry. Compilation is pure and cached (`lru_cache`): a new string costs about 35 µs, and after that it's a cache hit.
4. **Flush before styling.** `TwApp` adds the new CSS to the stylesheet just before Textual styles newly mounted widgets, so there's no unstyled first frame. On a live app, only the new chunk of CSS is parsed (about 0.4 ms), not the whole stylesheet.
5. **Validate.** Theme colors used by the new CSS are checked against the active theme's variables. A typo raises `TailError` and lists the available colors.

Colors compile to theme variables (`$success`, `$panel 40%`), so a theme switch costs a single stylesheet refresh. tui-z doesn't recompile anything.

Variants map to Textual pseudo-classes and selectors:

| Variant | Textual selector |
|---|---|
| `hover:` | `:hover` |
| `focus:` | `:focus` |
| `odd:` / `first:` | `:odd` / `:first-child` |
| `dark:` | `:dark` |
| `group-hover:` | `.group:hover .tw-…` |
| `md:` | `Screen.-tw-md .tw-…` |

`TwApp` sets the breakpoint classes on the screen through Textual's `HORIZONTAL_BREAKPOINTS`.

### Content transforms

Textual CSS can't change text, so `uppercase`, `tracking-wide` and the other content transforms are carried in the compiled result and applied by tui-z's text components. They skip markup tags.

## The line API: Table and LogView

A naive table mounts one widget per cell. A 200-row, 5-column table becomes 1,000 widgets, each laid out and styled separately.

tui-z's `Table` and `LogView` are **one widget each**, built on Textual's Line API (`ScrollView.render_line`):

- Only **visible** lines render, so a 10,000-line log costs the same to draw as a 10-line one.
- Each rendered line is **cached** by `(row identity, width)` and reused until its data, the width or the theme changes.
- Adding a row is a list append plus a refresh, not a mount plus a layout pass.

Per-cell and per-line `cls` is interpreted as an **inline style** (`tui_z.inline`). That's why only text-level utilities are allowed there.

## Streaming charts

- Every point has a **fixed slot**, with the newest on the right. Pushing scrolls the existing drawing left without reshaping it.
- One extra point beyond the left edge is kept, so the segment entering the view is drawn correctly.
- The y-range is **sticky**: it grows to fit new extremes but doesn't shrink on every frame, so the chart doesn't jitter.
- Series are trimmed in bulk, so `push()` is amortized O(1).
- Rendering merges runs of same-styled cells into single segments.

## Benchmarks

Measured on a laptop with Python 3.14 and Textual 8.2:

| Operation | Cost |
|---|---|
| Compile a new class string | ~35 µs (then cached) |
| New class on a live widget | ~0.4 ms |
| `LogView.write` | ~0.2 ms |
| `Table.add_row` | ~0.25 ms |
| `Table.set_rows` (20 rows) | ~0.5 ms |
| `Stat.update` (changed value and color) | ~0.18 ms |
| `LineChart` render (100×12, 3 series) | ~1 ms |
| Theme switch (full showcase) | ~95 ms |
| Showcase startup | ~0.8 s |

Steady-state CPU for the showcase dashboard, with every panel updating four times a second, is about 9% of one core. Almost all of it is Textual's compositor, and tui-z's own code is under 1%.

Run the benchmarks yourself:

```bash
uv run python benchmarks/bench.py    # per-operation costs
uv run python benchmarks/cpu.py      # startup time and steady-state CPU
```

## Keeping your app fast

- **Bound the number of distinct class strings.** Reuse named constants and switch between a few states (`"text-success"` / `"text-error"`). Don't generate `f"w-{n}"` from data.
- **Put data in content.** `Text.update`, `Stat.update`, `Table` rows and chart `push()` are the fast paths.
- **Unchanged updates are free.** `set_cls`, `Text.update` and `Stat.update` return early, so updating on every tick is fine.
- **Pause what isn't visible.** Updating widgets in a hidden tab still costs layout work. Stop or slow those timers.
