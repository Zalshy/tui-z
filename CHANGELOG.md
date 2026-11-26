# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Notifications: `app.toast(...)` shows a `Toast` in a corner (`TW_TOASTS`), with variants, a countdown that pauses on hover, an action button and a `×N` count for repeats. Textual's `notify()` goes through it too (`TW_TOASTS = None` keeps Textual's). `NotificationCenter` lists every toast with an unread count.
- Feedback: `Alert`, `Progress` (including indeterminate), `Spinner`, `Dialog`.
- Controls: `Checkbox`, `Switch`, `RadioGroup`, and restyled `Input` and `Select`.
- Navigation: `TabView` / `TabPane` / `Tabs`, `KeyHints`.
- Content: `KeyValue`, `Kbd`.
- Charts: `BarChart` (with `BarChart.histogram`), `Heatmap`.
- `normal-case` undoes a default `uppercase` / `lowercase` / `capitalize` (as `tracking-normal` already did for tracking). Within each group, the last transform wins.
- Opacity on arbitrary colors: `bg-[#102030]/50`.
- `widget.applied_cls`: the full class string compiled onto a component (its `DEFAULT_CLS` plus yours), for debugging.

### Changed

- The package is split into layers: `tui_z.styling` (the class compiler, inline styles and themes), `tui_z.core` (the `Tw` mixin, registry and stylesheet sync), `tui_z.components` and `tui_z.app`. Everything exported from `tui_z` is unchanged. Code that imported internal modules directly needs new paths: `tui_z.engine` → `tui_z.styling.engine` (utility tables in `tui_z.styling.utilities`), `tui_z.inline` → `tui_z.styling.inline`, `tui_z.theme` → `tui_z.styling.themes`, `tui_z.registry` → `tui_z.core.registry`.
- All use of Textual's private API now lives in `tui_z._textual`.
- Tests mirror the source layout. Every component passes shared contract checks, there are snapshot tests per component family in three themes, property-based tests for the class compiler, and CI requires 95% coverage.

### Fixed

- `Sidebar.cls` returned the full internal string (border and width included) instead of your class string, and a `set_cls()` on a sidebar was lost at the next toggle.
- `add_cls()` on a `Sidebar` merged onto the internal string.
- Clicking a `Button` no longer also counts as a click on the widget that contains it.

## [0.1.0] - unreleased

The first public alpha.

### Added

- A class-string engine: utility class strings compiled to Textual CSS. One generated class per unique string, the last utility wins, and errors are loud (`TailError`).
- Variants (`hover:`, `focus:`, `focus-within:`, `disabled:`, `first:`, `last:`, `odd:`, `even:`, `dark:`, `light:`, `group-hover:`) and breakpoints (`sm:`, `md:`, `lg:`, `xl:`).
- `TwApp`, with incremental stylesheet updates and theme cycling.
- Components: `Box`, `Row`, `Col`, `Grid`, `Scroll`, `Spacer`, `Divider`, `Sidebar`, `Text`, `Label`, `Badge`, `Stat`, `Panel`, `Ticker`, `Button`, `ThemeSwitcher`.
- Line-API data components: `Table` and `LogView` (virtualized, with line caching).
- Charts: `Bar`, `Sparkline`, `LineChart` (braille, multi-series, marks, streaming).
- Themes: `terminal`, `amber`, the four Catppuccin flavors and the four Tokyo Night styles, plus `make_theme`.
- The showcase and markets demos, and the benchmarks.
