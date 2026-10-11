# Contributing to Gamma

Thanks for your interest in Gamma! Any help is welcome: bug reports, feature ideas, documentation and translations.

## Getting the code running

```bash
git clone https://github.com/i-voron/gamma-color-temperature.git
cd gamma-color-temperature
./gamma.py --help
```

Requirements: **Python 3.10+** and **xrandr** (`xrandr --version`).

You can also use the Makefile: `make run`, `make test`, `make clean`.

## Test environment — please read this first

Gamma is developed and tested **only on X11**. It cannot control gamma on Wayland,
because `xrandr` has no access there. This is an X11/Wayland limitation, not a project bug.

Before reporting a problem, check your session type:

```bash
echo $XDG_SESSION_TYPE    # should print "x11"
```

If you are on Wayland, the report will be closed — please use Gammastep or your
compositor's built-in Night Light instead. PRs that only add Wayland support cannot be merged.

## Reporting a bug

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml) — it asks for everything needed:

1. What you expected and what actually happened
2. Steps to reproduce
3. Environment: distribution, desktop environment/window manager, Gamma version,
   Python version, X11 or Wayland, monitor model
4. Output of `gamma.py --list-monitors`
5. A fragment of `gamma.log` (or the whole file — it contains no personal data)

Please search existing issues first to avoid duplicates.

## Suggesting a feature

Open an issue describing **your use case**, not only the implementation.
Features that add dependencies, background daemons or automatic time/location-based
switching are out of scope — Gamma is deliberately manual, portable and dependency-free.

## Code conventions

- Docstrings and comments in English
- PEP 8, type hints with built-in generics (`list[str]`, `str | None`, not `typing.List`/`Optional`)
- Keep the single-file design: no new mandatory dependencies
- Atomic commits with a clear message
- Do not reformat unrelated lines — it hides real changes in the diff

## Localization

New user-visible strings must be added to **both** language dictionaries (`en` and `ru`).

## License

By contributing you agree that your code is distributed under the project's
[MIT License](LICENSE).
