# Contributing

## Smoke Checks

Run these before committing orchestrator changes:

```bash
python3 -m pytest
python3 scripts/sanitize-check.py --self-test
python3 scripts/smoke-check.py
```

`scripts/smoke-check.py` runs the report-generation smoke check against a temporary copy of `tests/fixtures/cases/pattern2-basic`, so it does not leave `case-report.md` inside the tracked fixture directory.

For manual debugging only, the underlying report command is:

```bash
python3 scripts/generate-case-report.py tests/fixtures/cases/pattern2-basic
```

That direct command writes into the fixture directory; prefer `scripts/smoke-check.py` for routine checks.
