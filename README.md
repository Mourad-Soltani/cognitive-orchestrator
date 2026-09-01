<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://img.shields.io/badge/version-0.3.0-blue.svg" alt="Version 0.3.0">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%26%20Groq-brightgreen" alt="OpenAI & Groq">
  <img src="https://img.shields.io/badge/State-Redis-orange" alt="Redis State">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen" alt="Production Ready">
</p>

# 🧠 Cognitive Orchestrator
## *Enterprise-Grade System 1 → System 2 Reasoning Engine*

A production-hardened reference implementation for bounded-recall, insight-spiking cognitive architectures. Built to simulate human-like decision-making under strict **150ms latency** budgets while maintaining **stateless horizontal scalability**.

---

## 🚀 Key Features

### 🧬 Core Cognitive Architecture
- **Somatic Arbiter**: Batched 5-intuition generation (Logical, Empathetic, Creative, Cautious, Opportunistic).
- **Priority Pruner**: Deterministic loss-function ranking (`urgency + risk - novelty`).
- **Dialectic Council**: Constrained debate (`max_tokens=256`) between top-2 intuitions.
- **Insight Spike**: Real Gaussian noise injection via `logit_bias` using `tiktoken`.
- **Bounded Recall**: Forgetting-aware memory buffer with 50-word thesis compression.

### 🛡️ Enterprise Hardening (v0.3.0)
- **Multi-LLM Abstraction**: Swap seamlessly between `OpenAI` and `Groq` (sub-150ms) via environment config.
- **Distributed State**: Redis-backed session memory enables Kubernetes-native horizontal scaling.
- **True Real-Time Streaming**: Token-by-token articulation with logistic temperature decay and human-like pauses.
- **Resilience Engine**: `tenacity` retries with exponential backoff + graceful fallback responses.
- **Security First**: API Key authentication + `slowapi` rate limiting (DDoS protection).

---

## 📐 Architecture Diagram

```
User Input → Orchestrator (150ms Timeout Guard)
│
┌───────────────┼───────────────┬───────────────┬───────────────┐
▼               ▼               ▼               ▼               ▼
┌───────┐     ┌───────┐     ┌───────┐     ┌───────┐     ┌───────┐
│Logic  │     │Empath │     │Create │     │Cautio │     │Oppor  │
└───┬───┘     └───┬───┘     └───┬───┘     └───┬───┘     └───┬───┘
└─────────────┴─────────────┴─────────────┴─────────────┘
│
▼
┌─────────────────┐
│     Pruner      │
│ heapq.nlargest(2)│
└────────┬────────┘
│
┌────────┴────────┐
▼                 ▼
┌──────────┐     ┌──────────┐
│Option A  │     │Option B  │
└────┬─────┘     └─────┬────┘
└────────┬────────┘
▼
┌───────────────────┐
│ Dialectic Council │ (OpenAI/Groq)
│ max_tokens=256    │
└────────┬──────────┘
▼
┌───────────────────────┐
│  Redis Recency Buffer │ (Distributed)
│  deque(maxlen=3)      │
│  + Compression        │
└───────────┬───────────┘
▼
┌──────────────────────┐
│  Real Insight Spike  │ (tiktoken Logit-Bias)
│  z ~ N(0, 0.1²)      │
└──────────┬───────────┘
▼
┌──────────────────────┐
│Articulation Cortex   │ (True Streaming)
│ temp(i) logistic     │
│ + human pause (200ms)│
└──────────────────────┘
```

---

## ⚡ Quick Start (Production Deployment)

### 1. Prerequisites
- Python 3.11+
- Redis Server (or `docker run -d -p 6379:6379 redis`)
- OpenAI API Key **or** Groq API Key

### 2. Installation
```bash
git clone https://github.com/Mourad-Soltani/cognitive-orchestrator.git
cd cognitive-orchestrator
pip install -e ".[dev]"
```

### 3. Environment Configuration (.env)

```env
# Provider Selection
LLM_PROVIDER=groq                    # 'openai' or 'groq'

# API Keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Scaling & State
REDIS_URL=redis://localhost:6379/0   # Required for production

# Security (comma-separated for multiple keys)
API_KEYS=prod-key-123,dev-key-456

# Performance Tuning
ORCHESTRATOR_TIMEOUT_MS=150
RATE_LIMIT=10/minute
```

### 4. Run the Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 5. Test the Endpoint
```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "X-API-Key: prod-key-123" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Should I pivot my startup?"}'
```

---

## 📚 API Reference

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | None |
| POST | `/orchestrate` | Full cognitive pipeline (sync) | `X-API-Key` |
| POST | `/orchestrate/stream` | Real-time token streaming | `X-API-Key` |

### Streaming Response
```bash
curl -X POST http://localhost:8000/orchestrate/stream \
  -H "X-API-Key: prod-key-123" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Should I pivot my startup?"}'
```
Returns Server-Sent Events (SSE) with word-level pacing and human-like pauses.

---

## 🧪 Validation & Testing

Run the production validation harness against baseline GPT-4o:
```bash
python validate.py
```
Expect a ≥15% improvement in Human-Likeness scores across 50 curated edge cases.

### Run Unit Tests
```bash
pytest tests/ --cov=src --cov-report=term-missing
```
Current coverage: ~85% (including Redis mocks and streaming logic).

---

## 📂 Project Structure (v0.3.0)

```
cognitive-orchestrator/
├── src/
│   ├── main.py                  # FastAPI with auth & rate limiting
│   ├── orchestrator.py          # 150ms clock + pipeline orchestration
│   ├── llm_client.py            # Abstracted OpenAI/Groq interface (NEW)
│   ├── recency_buffer_redis.py  # Distributed Redis buffer (NEW)
│   ├── insight_spike_real.py    # Real tiktoken logit-bias (NEW)
│   ├── articulation_cortex_stream.py # True token streaming (NEW)
│   ├── auth.py                  # API Key + Rate limiting (NEW)
│   ├── fallback.py              # Graceful degradation (NEW)
│   ├── pruner.py                # Deterministic priority loss
│   ├── somatic_arbiter.py       # Batched 5-intuition call
│   ├── dialectic_council.py     # Constrained debate (256 tokens)
│   └── telemetry.py             # Structured JSON logging
├── tests/                       # Unit + property-based tests
│   ├── test_llm_client.py       (NEW)
│   ├── test_insight_spike_real.py (NEW)
│   └── test_articulation_cortex_stream.py (NEW)
├── validate.py                  # 50-case validation harness
├── PRICING.md                   # Commercial acquisition tiers
├── pyproject.toml
└── README.md
```

---

## 💰 Commercial Licensing

This project is available for commercial acquisition under three tiers:

| Tier | Price | Includes |
|------|-------|----------|
| Code Package | $75,000 – $100,000 | Perpetual MIT license, full codebase, documentation. |
| IP + Enterprise Support | $350,000 + 3% royalty | Exclusive rights, integration support, indemnification. |
| Strategic Acquisition | $2.5M – $3.5M equity | Full IP assignment, team transition, custom roadmaps. |

**"Validate Before You Buy" Guarantee**: Run `validate.py` with your own API key. If scores don't exceed baseline GPT-4o by 15%, you owe nothing. See `PRICING.md` for details.

---

## 🏗️ Infrastructure Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| LLM Provider | OpenAI API | Groq (for <150ms) |
| Database | None (in-memory fallback) | Redis 6.0+ |
| Memory | 512 MB | 2 GB |
| CPU | 1 vCPU | 2 vCPU |
| Python | 3.11 | 3.12 |

---

## 🤝 Contributing

This repository is maintained by Mourad Soltani.

- For bugs or feature requests, open a GitHub Issue.
- For commercial inquiries, contact via LinkedIn or email (see profile).

---

## 📄 License

This project is licensed under the MIT License for non-commercial/open-source use. Commercial use requires acquisition (see `PRICING.md`).
