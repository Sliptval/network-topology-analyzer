# Contributing

Thanks for taking the time to help. This is a small, focused project and
patches of any size are welcome.

## Getting set up

```bash
git clone https://github.com/Sliptval/network-topology-analyzer.git
cd network-topology-analyzer
python3 -m pip install -e ".[dev]"
pytest
```

The tool runs on the Python standard library alone; the `dev` extra only adds
`pytest` and `pyyaml`.

## Ground rules

- **Keep dependencies minimal.** If the standard library can do it, use the
  standard library. New runtime dependencies need a good reason.
- **Fail clearly.** Expected problems (no privileges, missing nmap, unreachable
  network) should produce a one-line message, never a traceback. Raise
  `CommandError` for user-facing errors in the CLI layer.
- **Test the pure logic.** Parsers, exporters, the diff engine, alert rules and
  address handling all have unit tests. Add tests when you change them.
- **Match the layout.** Scanning, traffic, storage, export, daemon and CLI each
  live in their own package. New code should follow the existing separation.

## Before opening a pull request

1. `pytest` passes.
2. New behaviour has a test.
3. User-visible changes are noted in `CHANGELOG.md` under *Unreleased*.
4. Commits are small and have a clear message.

## Scope

nettop is deliberately **CLI-first**: no web UI, no heavyweight framework. Ideas
that keep it a fast, scriptable terminal tool are the ones most likely to be
merged.

## Responsible use

Only scan networks you own or are explicitly authorised to test. See
[docs/legal.md](docs/legal.md).
