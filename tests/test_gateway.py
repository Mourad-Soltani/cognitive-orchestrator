"""Policy and evidence-pack tests for the commercial gateway."""

from src.gateway import DecisionLedger, VendorDecisionRequest


def test_auto_approve_under_threshold():
    ledger = DecisionLedger()
    request = VendorDecisionRequest(
        vendor_name="Northline Studio",
        spend_usd=12000,
        data_classification="internal",
        country="US",
        business_owner="A. Chen",
    )
    status, _ = ledger.evaluate(request)
    pack = ledger.record(request, status, "ok")
    assert status == "approved"
    assert pack.pack_hash
    assert ledger.spend_usd == 12000


def test_restricted_data_is_rejected():
    ledger = DecisionLedger()
    request = VendorDecisionRequest(
        vendor_name="Shadow AI",
        spend_usd=1000,
        data_classification="restricted",
        country="DE",
        business_owner="M. Soltani",
    )
    status, reason = ledger.evaluate(request)
    assert status == "rejected"
    assert "Restricted" in reason


def test_spend_above_threshold_needs_human():
    ledger = DecisionLedger()
    request = VendorDecisionRequest(
        vendor_name="BigCloud",
        spend_usd=80000,
        data_classification="confidential",
        country="US",
        business_owner="CFO",
    )
    status, _ = ledger.evaluate(request)
    assert status == "needs_human"


def test_chain_links_packs():
    ledger = DecisionLedger()
    first = VendorDecisionRequest(
        vendor_name="A", spend_usd=1000, data_classification="public", country="US", business_owner="x"
    )
    second = VendorDecisionRequest(
        vendor_name="B", spend_usd=2000, data_classification="public", country="US", business_owner="x"
    )
    p1 = ledger.record(first, "approved", "ok")
    p2 = ledger.record(second, "approved", "ok")
    assert p2.prev_hash == p1.pack_hash
    exported = ledger.export()
    assert exported["decisions"] == 2
    assert exported["chain_head"] == p2.pack_hash
