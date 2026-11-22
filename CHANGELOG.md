# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - unreleased

The first public alpha.

### Added

- A class-string engine: Tailwind-style utilities compiled to Textual CSS. One generated class per unique string, the last utility wins, and errors are loud (`TailError`).
- Variants (`hover:`, `focus:`, `focus-within:`, `disabled:`, `first:`, `last:`, `odd:`, `even:`, `dark:`, `light:`, `group-hover:`) and breakpoints (`sm:`, `md:`, `lg:`, `xl:`).
- `TwApp`, with incremental stylesheet updates and theme cycling.
- Components: `Box`, `Row`, `Col`, `Grid`, `Scroll`, `Spacer`, `Divider`, `Sidebar`, `Text`, `Label`, `Badge`, `Stat`, `Panel`, `Ticker`, `Button`, `ThemeSwitcher`.
- Line-API data components: `Table` and `LogView` (virtualized, with line caching).
- Charts: `Bar`, `Sparkline`, `LineChart` (braille, multi-series, marks, streaming).
- Themes: `terminal`, `amber`, the four Catppuccin flavors and the four Tokyo Night styles, plus `make_theme`.
- The showcase and markets demos, and the benchmarks.
