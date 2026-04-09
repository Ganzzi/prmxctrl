# Development Guide

> Last Updated: 2026-04-09

## Prerequisites

- Python >=3.10
- [uv](https://docs.astral.sh/uv/) package manager
- Proxmox VE API access (for integration/e2e tests)

## Setup

```bash
uv sync --all-groups --all-extras
```

## Unit Tests (PR Gate)

```bash
uv run pytest -m "not integration and not e2e" -q
```

## Integration / E2E Tests

```bash
uv run pytest -q                    # runs all tests
uv run pytest -m integration        # integration only
uv run pytest -m e2e                # e2e only
```

## Coverage

```bash
uv run pytest -m "not integration and not e2e" --cov --cov-report=term-missing
```

## Code Generation

The SDK is auto-generated from the Proxmox API schema:

```bash
python tools/generate.py    # generate the complete SDK
python tools/validate.py    # validate generated code
```

## Type Checking & Linting

```bash
uv run mypy --strict
uv run ruff check .
```

## CI Behavior

- PR-gated: lint + unit tests only (`pytest -m "not integration and not e2e"`)
- Integration/e2e: non-gating, run on manual dispatch
- Requires Python 3.10+ on ubuntu-latest

## Known Issues

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for tracked issues.
