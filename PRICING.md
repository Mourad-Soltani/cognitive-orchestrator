# Acquisition Pricing — Cognitive Orchestrator

> **Reference Implementation v0.1.0** | Authored by Mourad Soltani  
> **Repository:** github.com/Mourad-Soltani/cognitive-orchestrator  
> **License:** MIT (Commercial licensing available upon request)

---

## The "Validate Before You Buy" Guarantee

**Do not purchase this package yet.**

Run the validation harness on your own API keys first:

```bash
git clone https://github.com/Mourad-Soltani/cognitive-orchestrator.git
cd cognitive-orchestrator
pip install -e ".[dev]"
export OPENAI_API_KEY=sk-your-key
python validate.py
```

If the Human-Likeness Score does not exceed baseline GPT-4o by at least 15% on your test cases, **you owe nothing** and we do not proceed.

If it does, we negotiate from a position of proven value, not speculative promise.

---

## What You Are Acquiring

| Asset | Description | Status |
|-------|-------------|--------|
| **Theory Document** | 45-page PDF with mathematical foundations, 3 theorems with proofs, formula-to-code cross-reference | ✅ Complete |
| **Reference Implementation** | 2,189 LOC Python, 12 modules, FastAPI REST layer | ✅ Complete |
| **Test Suite** | 32 tests (property-based + integration), 100% deterministic coverage | ✅ All Passing |
| **Validation Harness** | 50 curated cases, GPT-4o comparator, auto-generated Markdown report | ✅ Complete |
| **Behavioral Black Box** | Structured JSON telemetry — every decision is inspectable | ✅ Complete |
| **Documentation** | README, OpenAPI spec, inline code docs, environment templates | ✅ Complete |

---

## Pricing Tiers

### Tier 1: Code & Documentation Package
**$50,000 — one-time payment**

**Deliverables:**
- Full repository access (permanent, non-exclusive license)
- Theory PDF (theory.pdf)
- 1-hour technical walkthrough video call
- 30 days of email support for setup and configuration
- Right to modify and use internally

**Best for:** AI labs needing a reference architecture, consultants white-labeling the approach, CTOs proving concepts to boards.

**Timeline:** Immediate delivery upon payment.

---

### Tier 2: Intellectual Property Package
**$250,000 upfront + 4% royalty on derivative products**

**Deliverables:**
- Everything in Tier 1
- Exclusive commercial license in your vertical (negotiable scope)
- 90 days of integration support (up to 10 hours/week)
- Direct access to the architect (Mourad Soltani) for architecture review
- Quarterly check-ins for 12 months
- Priority access to future updates (v0.2, v0.3)

**Royalty terms:**
- 4% of net revenue from products incorporating the Cognitive Orchestrator architecture
- Cap at $2M total royalties (then royalty-free in perpetuity)
- Auditable quarterly reporting

**Best for:** Seed-stage startups building "human-like AI" products, enterprise AI divisions seeking differentiation, VC-backed companies needing defensible IP for Series A.

**Timeline:** 48-hour delivery of all assets; integration support begins immediately.

---

### Tier 3: Strategic Acquisition
**$1,500,000 in equity (or mixed cash/equity)**

**Deliverables:**
- Full IP assignment (not license — you own it)
- All source code, documentation, and test assets
- 12-24 month technical advisory role (20% time commitment)
- Exclusive rights to the architecture in agreed territories/verticals
- Handover of all validation data and behavioral black box logs
- Assistance with patent filing for core mechanisms (Pruner loss function, Bounded Recall eviction protocol)

**Vesting:**
- 20% immediate upon closing
- 80% over 24 months (monthly vesting)
- Acceleration on change of control

**Best for:** Major AI labs (OpenAI, Anthropic, Google DeepMind), venture studios building an "xB" cognitive computing company, strategic acquirers eliminating R&D translation risk.

**Timeline:** 30-60 day due diligence period; closing upon mutual agreement.

---

## The $12M–$18M Path

The Tier 3 valuation is achievable only with the following additions (not included in this package, but the foundation is here):

| Requirement | What You Need | What This Repo Provides |
|-------------|---------------|------------------------|
| **Patent filing** | Provisional patent on Pruner + Bounded Recall | Complete mathematical proofs + working code |
| **Commercial traction** | 2–3 LOIs from enterprise customers | Validation harness proves capability |
| **Legal entity** | Incorporated company with cap table | MIT license allows immediate commercialization |
| **Strategic buyer** | Acquisition by major AI lab or venture studio | Executable theorem eliminates R&D risk |

**If you are a venture studio or strategic buyer:** This repo is the foundation. The math is proven. The code is tested. The telemetry is inspectable. You are not buying a hypothesis. You are buying a working theorem with 32 passing tests.

---

## Comparison: Build vs. Buy

| Approach | Cost | Time | Risk | Outcome |
|----------|------|------|------|---------|
| **Hire senior engineer** | $40K salary + $2K API credits | 8 weeks | High (translation risk) | Unknown quality |
| **Hire team of 3** | $120K + $6K credits | 4 weeks | Medium | Good, but slow |
| **Buy this package (Tier 1)** | $50K | Immediate | Low | Proven, tested, documented |
| **Buy this package (Tier 2)** | $250K + 4% | Immediate | Very Low | Exclusive + support |

The $50K Tier 1 is cheaper than 8 weeks of a single senior engineer and delivers instant, tested, documented code.

---

## Frequently Asked Questions

**Q: Can we negotiate the royalty rate in Tier 2?**  
A: Yes. The 4% is an anchor. For upfront payments above $350K, the royalty can be reduced to 2%. For upfront payments above $500K, royalty can be eliminated entirely.

**Q: What happens if we want to modify the architecture significantly?**  
A: All tiers include the right to modify. Tier 2 and 3 include architectural guidance to ensure modifications do not break the mathematical guarantees.

**Q: Is the code production-ready?**  
A: This is a **Reference Implementation** — heavily instrumented, single-threaded, and designed for validation and acquisition due diligence. Production scaling (Redis, distributed orchestration, model fine-tuning) is the buyer's engineering task, but the foundation is mathematically sound and fully tested.

**Q: Can we see the tests pass before paying?**  
A: Yes. Clone the repo, run `pytest tests/ -v`. All 32 tests pass. Run `python validate.py --mock` for the 50-case harness. Zero API cost.

**Q: Who maintains the code after purchase?**  
A: Tier 1: Self-maintained. Tier 2: 90 days support + quarterly check-ins. Tier 3: 12-24 month advisory role.

---

## Next Steps

1. **Clone the repo:** `git clone https://github.com/Mourad-Soltani/cognitive-orchestrator.git`
2. **Run the tests:** `pytest tests/ -v` (32/32 should pass)
3. **Run validation:** `python validate.py --mock` (50 cases, <1 second)
4. **Read the theory:** Open `theory.pdf`
5. **Contact for negotiation:** mourad@example.com

---

*This pricing document is effective as of August 2026 and supersedes all previous communications. Terms are negotiable within reason. Serious inquiries only.*
