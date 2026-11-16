# Contributing

## Scope

This repository is source-available under **Business Source License 1.1** (see `LICENSE`).
Production use requires a commercial agreement. Contributions are welcome for evaluation,
documentation, tests, and non-production improvements.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export OPENAI_API_KEY=sk-dummy   # unit tests use mocks
pytest tests/ -v
```

## Expectations

1. **Tests** — add or update tests for behavior changes. CI runs pytest on every push.
2. **Style** — keep changes focused; prefer small PRs.
3. **Security** — never commit API keys, tokens, or customer data.
4. **Architecture** — the commercial product surface is the governed decision gateway
   (`src/gateway.py`, `/decisions/vendor`, `/audit/export`). Cognitive stages support
   that surface; do not expand scope without discussion.

## Review

Open a pull request against `main`. Describe the problem, the change, and how you tested it.
External reviewers and part-time contributors are welcome.

## License of contributions

By submitting a contribution, you agree it is licensed to the Licensor under the same
terms as the Licensed Work (BSL 1.1), and may be included in commercial distributions.
