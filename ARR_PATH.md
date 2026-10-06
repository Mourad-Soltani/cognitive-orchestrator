# Path to $100M ARR

This is the product motion, not a forecast. The repository does not have this revenue.

## Offer

Governed vendor-onboarding decisions. A self-hosted gate writes a hash-chained evidence pack for every approve, escalate, or reject. Buyers pay for decisions their risk team will accept, not for a reasoning demo.

## Unit

- Pilot: $50k, 60 days, success = audit pack accepted by risk or finance.
- Platform: $250–500k per year once the pack is in the workflow.
- Usage: overage on governed decisions after the included volume.

$100M ARR is about 200 accounts at $500k, or 80 at $1.25M. It only happens if pilots convert and expand.

## Endpoints

- `POST /decisions/vendor` applies policy, optionally runs the orchestrator, and stores a pack.
- `GET /audit/export` returns the chain.

Policy defaults: auto-approve at or under $25k, human review above that, reject `restricted` data, monthly budget $250k.
