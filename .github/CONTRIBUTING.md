# Contributing

Thanks for contributing to AAS-Holo-Shard.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install
pytest
```

## Pull requests

- Keep changes focused and explain the security impact.
- Add tests for cryptographic behavior and edge cases.
- Ensure `pytest` passes with >= 90% coverage for crypto modules.

## Reporting security issues

Please see `SECURITY.md` for reporting instructions.
