# Measured latency report

Date: 2026-10-06  
Commit under test: local working tree after the 0.3.0 pipeline fixes  
Harness: `python demo.py` (50 iterations)

## What was measured

Offline live demo of the real `CognitiveOrchestrator.process()` path:

- mocked somatic arbiter (no network)
- mocked dialectic council (no network)
- mocked articulation cortex (no network)
- in-memory recency buffer
- real pruner, insight-spike sampling, telemetry, and response assembly

This is orchestration overhead. It is **not** end-to-end provider latency. A live OpenAI or Groq call will dominate the budget.

## Result

| Stat | Latency (ms) |
|---|---|
| min | 0.098 |
| median | 0.109 |
| mean | 0.319 |
| p95 | 0.347 |
| p99 | 9.527 |
| max | 9.527 |

Sample output for “Should I pivot my startup?”:

- top modes: Logical, Cautious
- output: “Ship the narrowest reversible version and measure it.”
- reported pipeline latency on first sample: 9.44 ms (includes first-call import/setup noise)

## Reading the 150 ms claim

Local pipeline overhead is well under 1 ms at the median and under 1 ms at p95 on this host. The 150 ms figure is only plausible as a **provider budget**, not as something the orchestrator itself consumes. With Groq or OpenAI, expect the full request to be provider latency plus about 0.1–1 ms of local work after warmup.

Raw samples: `reports/latency.json`.
