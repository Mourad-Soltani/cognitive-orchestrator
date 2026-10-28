"""Governed-decision gateway.

The commercial product is a gate in front of a decision: policy, budget,
human override, and a hash-chained evidence pack. Packs persist to SQLite
by default so audit survives process restart.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
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
    """Hash-chained decision ledger with optional SQLite durability."""

    def __init__(
        self,
        policy: PolicyConfig | None = None,
        db_path: str | Path | None = "data/decisions.sqlite",
    ):
        self.policy = policy or PolicyConfig()
        self.packs: list[EvidencePack] = []
        self.spend_usd = 0.0
        self._prev_hash = "0" * 64
        self._lock = threading.Lock()
        self.db_path = Path(db_path) if db_path else None
        if self.db_path:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
            self._load()

    def _connect(self) -> sqlite3.Connection:
        assert self.db_path is not None
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS packs (
                    decision_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    pack_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    spend_usd REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _load(self) -> None:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM packs ORDER BY rowid ASC"
            ).fetchall()
            for row in rows:
                pack = EvidencePack.model_validate_json(row["payload"])
                self.packs.append(pack)
                if pack.status == "approved":
                    self.spend_usd += float(pack.request.get("spend_usd") or 0)
                self._prev_hash = pack.pack_hash
            meta = conn.execute(
                "SELECT value FROM meta WHERE key = 'chain_head'"
            ).fetchone()
            if meta:
                self._prev_hash = meta["value"]

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
        with self._lock:
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
            if self.db_path:
                with self._connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO packs (decision_id, created_at, payload, pack_hash, prev_hash, status, spend_usd)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            pack.decision_id,
                            pack.created_at,
                            pack.model_dump_json(),
                            pack.pack_hash,
                            pack.prev_hash,
                            pack.status,
                            request.spend_usd if status == "approved" else 0.0,
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO meta(key, value) VALUES('chain_head', ?)
                        ON CONFLICT(key) DO UPDATE SET value = excluded.value
                        """,
                        (self._prev_hash,),
                    )
                    conn.commit()
            return pack

    def export(self) -> dict:
        return {
            "workflow": "vendor_onboarding",
            "decisions": len(self.packs),
            "committed_spend_usd": round(self.spend_usd, 2),
            "chain_head": self._prev_hash,
            "durable": bool(self.db_path),
            "packs": [p.model_dump() for p in self.packs],
        }

    def verify_chain(self) -> dict:
        """Recompute hashes; return integrity report."""
        prev = "0" * 64
        checked = 0
        for pack in self.packs:
            body = {
                "workflow": pack.workflow,
                "request": pack.request,
                "policy": pack.policy,
                "status": pack.status,
                "reason": pack.reason,
                "orchestrator": pack.orchestrator,
                "human_override": pack.human_override,
                "prev_hash": prev,
            }
            expected = hashlib.sha256(
                json.dumps(body, sort_keys=True, default=str).encode()
            ).hexdigest()
            if pack.prev_hash != prev or pack.pack_hash != expected:
                return {
                    "ok": False,
                    "checked": checked,
                    "broken_at": pack.decision_id,
                    "expected_hash": expected,
                    "actual_hash": pack.pack_hash,
                }
            prev = pack.pack_hash
            checked += 1
        return {"ok": True, "checked": checked, "chain_head": prev}
