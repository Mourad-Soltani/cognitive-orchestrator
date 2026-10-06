"""Governed-decision gateway.

The commercial product is not the cognitive demo. It is a gate in front of a
decision: policy, budget, human override, and a hash-chained evidence pack.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from src.models import OrchestratorResponse


DecisionStatus = Literal["approved", "needs_human", "rejected", "budget_blocked"]


class VendorDecisionRequest(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=200)
    spend_usd: float = Field(..., ge=0)
    data_classification: Literal["public", "internal", "confidential", "restricted"]
    country: str = Field(..., min_length=2, max_length=80)
    business_owner: str = Field(..., min_length=1, max_length=120)
    notes: str = Field("", max_length=2000)
    session_id: str | None = None


class PolicyConfig(BaseModel):
    max_auto_approve_usd: float = 25000
    blocked_classifications: list[str] = Field(default_factory=lambda: ["restricted"])
    monthly_budget_usd: float = 250000


class EvidencePack(BaseModel):
    decision_id: str
    workflow: str
    created_at: str
    request: dict
    policy: dict
    status: DecisionStatus
    reason: str
    orchestrator: dict | None = None
    human_override: str | None = None
    prev_hash: str
    pack_hash: str


class DecisionLedger:
    def __init__(self, policy: PolicyConfig | None = None):
        self.policy = policy or PolicyConfig()
        self.packs: list[EvidencePack] = []
        self.spend_usd = 0.0
        self._prev_hash = "0" * 64

    def evaluate(self, request: VendorDecisionRequest) -> tuple[DecisionStatus, str]:
        if request.data_classification in self.policy.blocked_classifications:
            return "rejected", "Restricted data classification cannot be auto-approved."
        if self.spend_usd + request.spend_usd > self.policy.monthly_budget_usd:
            return "budget_blocked", "Monthly governed-decision budget would be exceeded."
        if request.spend_usd > self.policy.max_auto_approve_usd:
            return "needs_human", "Spend is above the auto-approve threshold."
        return "approved", "Within policy for automatic approval."

    def record(
        self,
        request: VendorDecisionRequest,
        status: DecisionStatus,
        reason: str,
        orchestrator: OrchestratorResponse | None = None,
        human_override: str | None = None,
    ) -> EvidencePack:
        body = {
            "workflow": "vendor_onboarding",
            "request": request.model_dump(),
            "policy": self.policy.model_dump(),
            "status": status,
            "reason": reason,
            "orchestrator": orchestrator.model_dump() if orchestrator else None,
            "human_override": human_override,
            "prev_hash": self._prev_hash,
        }
        pack_hash = hashlib.sha256(
            json.dumps(body, sort_keys=True, default=str).encode()
        ).hexdigest()
        pack = EvidencePack(
            decision_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            pack_hash=pack_hash,
            **body,
        )
        self.packs.append(pack)
        self._prev_hash = pack_hash
        if status == "approved":
            self.spend_usd += request.spend_usd
        return pack

    def export(self) -> dict:
        return {
            "workflow": "vendor_onboarding",
            "decisions": len(self.packs),
            "committed_spend_usd": round(self.spend_usd, 2),
            "chain_head": self._prev_hash,
            "packs": [p.model_dump() for p in self.packs],
        }
