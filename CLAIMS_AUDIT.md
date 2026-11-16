# Claims audit (2026-11-16)

Response to external suggestions. Verified against repo after v0.4.1 and this commit.

| Suggestion | Verdict | Action |
|------------|---------|--------|
| Paid pilot is highest leverage | **True** | Business action, not code |
| Add CI + coverage badge workflow | **True gap** | Added `.github/workflows/ci.yml` |
| Version 0.4.0 vs 0.4.1 drift | **Was real on remote** | Code is **0.4.1**; health test aligned |
| 62 tests / ~85% coverage | **Understated; docs lagged** | **64 passed**, **~89% coverage** measured 2026-11-16 after v0.4.1 + integration test. README updated. |
| Full pipeline integration test | **Present** | `tests/test_pipeline_integration.py` is on `main` (stub LLM, no network) |
| Publish 50-case ≥15% GPT-4o results | **Overstated as proven** | `validate.py` exists; treat ≥15% as **unverified** until committed JSON from a real key run |
| CONTRIBUTING.md / key-person risk | **Fair** | Added `CONTRIBUTING.md` |
| BSL missing Change Date / Additional Use Grant | **False** | Already present in `LICENSE` |
| Dual-license AGPL + commercial | **Not required** | BSL is coherent for sale; AGPL often deters enterprise buyers |
| Streamlit/Gradio demo | **Nice-to-have** | Deferred; gateway API + audit export is the product surface |
| Hash-chain verification | **Already improved in v0.4.1** | SHA-256, durable ledger, `verify_chain()`, `/audit/verify` |
| $1.1M–$1.5M ask without pilot | **Optimistic** | Without a paid pilot, clearing price stays roughly **$120k–$600k** exclusive/strategic |
| Position as governed-decision layer | **True** | Matches product; not a CrewAI competitor |

## Bottom line

Diligence hygiene improved (CI, CONTRIBUTING, integration test). Valuation still hinges on **one paid pilot**.

## Independent verification (2026-11-16)

```text
pytest tests/ -q --cov=src --cov-report=term
→ 64 passed
→ TOTAL coverage ~89% (833 statements, 91 missed)
```

`tests/test_pipeline_integration.py` is tracked in git. Public README metrics aligned to these numbers.
The ≥15% GPT-4o claim remains **unverified** (no committed validate.py JSON from a live key run).
