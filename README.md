# Cognitive Orchestrator — Reference Implementation

> **Version:** 0.1.0  
> **Python:** 3.11+  
> **License:** MIT

A bounded-recall, insight-spiking cognitive architecture that mimics human **System 1 → System 2** reasoning. This repository is the executable proof-of-concept referenced in the acquisition PDF.

---

## Architecture Overview

```
User Input
    │
    ▼
┌─────────────────┐     150ms timeout
│  Orchestrator   │◄────────────────────┐
│   (asyncio)     │                     │
└────────┬────────┘                     │
         │                              │
    ┌────┴────┬────┬────┬────┐         │
    ▼         ▼    ▼    ▼    ▼         │
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Logic │ │Empath│ │Create│ │Cautio│ │Oppor │
│ 0.9  │ │ 0.7  │ │ 0.6  │ │ 0.8  │ │ 0.5  │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   └─────────┴────────┴────────┴────────┘
              │
              ▼
      ┌───────────────┐
      │    Pruner     │  priority = (α·urgency) + (β·risk) − (γ·novelty)
      │  heapq.nlargest(2) │
      └───────┬───────┘
              │
         ┌────┴────┐
         ▼         ▼
    ┌────────┐ ┌────────┐
    │Option A│ │Option B│
    └────┬───┘ └───┬────┘
         │         │
         └────┬────┘
              ▼
      ┌───────────────┐
      │Dialectic Council│  max_tokens=256, stop="|"
      │  Constrained    │
      │   Debate        │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ Recency Buffer │  deque(maxlen=3)
      │  + Compression │  (intentional forgetting)
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │ Insight Spike │  z ~ N(0, 0.1²)
      │  Noise Injection│
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │Articulation   │  temp(i) = 1.2 − 0.9/(1+e^(0.5(i−5)))
      │   Cortex      │  + human pause @ chunk 3
      └───────────────┘
```

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/Mourad-Soltani/cognitive-orchestrator.git
cd cognitive-orchestrator

# 2. Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install
pip install -e ".[dev]"

# 4. Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 5. Run tests
pytest tests/ -v --cov=src

# 6. Run validation harness
python validate.py

# 7. Start API server
python -m src.main
# Open http://localhost:8000/docs
```

---

## Mathematical Formula → Code Mapping

| Concept | Formula | PDF Ref | Source File |
|---------|---------|---------|-------------|
| **Priority Loss** | `priority = (α·urgency) + (β·risk) − (γ·novelty)` | §3.2 | `src/pruner.py:compute_priority()` |
| **Logistic Decay** | `temp(i) = Tₛ − (Tₛ−Tₑ) / (1 + e^(0.5(i−5)))` | §3.6 | `src/articulation_cortex.py:_compute_temperature()` |
| **Insight Noise** | `z ~ 𝒩(0, σ²), σ = 0.1` | §3.5 | `src/insight_spike.py:generate_noise()` |
| **Bounded Recall** | `deque(maxlen=3)` | §3.4 | `src/recency_buffer.py` |
| **Timeout Guard** | `asyncio.timeout(0.15)` | §3.1 | `src/orchestrator.py:_run_arbiter()` |
| **Constrained Gen** | `max_tokens=256, stop=["\|"]` | §3.3 | `src/dialectic_council.py` |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/orchestrate` | Full pipeline (sync response) |
| `POST` | `/orchestrate/stream` | Chunked streaming output |

### Example Request

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Should I pivot my startup?"}'
```

### Example Response

```json
{
  "final_output": "Pivoting is a high-stakes decision...",
  "top_intuitions": [
    {
      "intuition": {"mode": "Cautious", "score": 0.85, "one_liner": "..."},
      "priority": 0.72
    }
  ],
  "dialectic_summary": "Balance speed with validated learning...",
  "insight_event": {
    "triggered": true,
    "noise_vector_sample": [0.02, -0.08, 0.11, -0.03, 0.05],
    "first_token_prob": 0.25
  },
  "session_id": "sess-uuid",
  "latency_ms": 342.5,
  "log_id": "log-uuid"
}
```

---

## Testing

```bash
# Unit + property-based tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Hypothesis property tests (pruner monotonicity)
pytest tests/test_pruner.py -v
```

---

## Validation Harness

The `validate.py` script is your **closing weapon**. It:

1. Runs **50 curated test cases** through the Orchestrator
2. Scores each on **5 dimensions** of Human-Likeness
3. Compares against **baseline GPT-4o**
4. Generates a **10-page Markdown report** with mathematical cross-references

```bash
# Live validation (~$40 in API credits)
python validate.py

# Mock validation (CI/CD, no API calls)
python validate.py --mock
```

---

## Project Structure

```
cognitive-orchestrator/
├── src/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Pydantic settings
│   ├── models.py               # Strict I/O schemas
│   ├── orchestrator.py         # 150ms clock + pipeline
│   ├── somatic_arbiter.py      # Batched 5-intuition LLM call
│   ├── pruner.py               # Deterministic loss function
│   ├── dialectic_council.py    # Constrained debate (256 tokens)
│   ├── recency_buffer.py       # deque(maxlen=3) + compression
│   ├── insight_spike.py        # Gaussian noise injection
│   ├── articulation_cortex.py  # Logistic temp decay + pauses
│   └── telemetry.py            # Structured JSON logging
├── tests/
│   ├── test_pruner.py          # Property-based proofs
│   ├── test_orchestrator.py    # Integration tests
│   ├── test_dialectic.py       # Parsing + API contract
│   ├── test_buffer.py          # Bounded recall eviction
│   ├── test_insight.py         # Noise statistics
│   └── test_articulation.py    # Temperature curve
├── validate.py                 # 50-case validation harness
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Behavioral Black Box

Every decision emits structured JSON logs via `structlog`. Example:

```json
{
  "event": "pruner_complete",
  "log_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T09:23:11Z",
  "payload": {
    "top_k": 2,
    "pruned": [
      {"intuition": {"mode": "Cautious", ...}, "priority": 0.72},
      {"intuition": {"mode": "Logical", ...}, "priority": 0.68}
    ]
  }
}
```

When buyers ask *"Does it hallucinate?"* — show them the exact `memory_forgotten` logs proving bounded recall is intentional.

---

## Theory Document

The complete mathematical foundation of this architecture is available in [theory.pdf](theory.pdf).

This 40+ page document includes:
- Formal definitions of all 7 subsystems
- 3 theorems with mathematical proofs
- Formula-to-code cross-reference tables
- Telemetry schema and Behavioral Black Box specification
- Acquisition value proposition and pricing tiers

Every formula in the PDF has a corresponding, tested line of Python in this repository.

## License

MIT — See acquisition materials for commercial licensing terms.
