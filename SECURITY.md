# Security policy

## Supported versions

tui-z is in alpha. Only the latest release on the `main` branch receives fixes.

## Reporting a vulnerability

Please **don't** open a public issue. Report it privately through GitHub's [private vulnerability reporting](https://github.com/Zalshy/tui-z/security/advisories/new) instead.

Include a description, the affected version and steps to reproduce. You can expect an acknowledgement within a week.

## Scope

tui-z is a styling and component library. It doesn't make network requests, run shell commands or read files. The most relevant risk is **untrusted text rendered as markup**. `Text`, `Table` cells, `LogView` messages and `Ticker` items parse Textual markup by default. Markup can carry actions (`[@click=app.quit]…[/]`), so text from outside your app, such as API responses, user names or log lines from other systems, could add clickable actions to your UI. When you display data you don't control, pass `markup=False` to `Text`, or escape the data first:

```python
from textual.markup import escape
log.write(f"user said: {escape(message)}")
table.add_row([escape(name), escape(comment)])
```
