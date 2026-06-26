"""Test all 10 sample cases from SUST_Preli_Sample_Cases.json.

Validates: ticket_id, relevant_transaction_id, evidence_verdict,
case_type, department, and safety on customer_reply.
"""

import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Load sample cases
SAMPLE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "SUST_Preli_Sample_Cases.json",
)

with open(SAMPLE_FILE) as f:
    sample_data = json.load(f)

CASES = sample_data["cases"]


def case_id(case):
    return case["id"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_status_200(case):
    """Every sample case should return 200."""
    response = client.post("/analyze-ticket", json=case["input"])
    assert response.status_code == 200, (
        f"{case['id']}: got {response.status_code}, body={response.text}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_ticket_id(case):
    """ticket_id must echo back."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["ticket_id"] == expected["ticket_id"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_relevant_transaction_id(case):
    """relevant_transaction_id must match expected."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["relevant_transaction_id"] == expected["relevant_transaction_id"], (
        f"{case['id']}: got txn_id={result['relevant_transaction_id']}, "
        f"expected={expected['relevant_transaction_id']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_evidence_verdict(case):
    """evidence_verdict must match expected."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["evidence_verdict"] == expected["evidence_verdict"], (
        f"{case['id']}: got verdict={result['evidence_verdict']}, "
        f"expected={expected['evidence_verdict']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_case_type(case):
    """case_type must match expected."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["case_type"] == expected["case_type"], (
        f"{case['id']}: got case_type={result['case_type']}, "
        f"expected={expected['case_type']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_department(case):
    """department must match expected."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["department"] == expected["department"], (
        f"{case['id']}: got department={result['department']}, "
        f"expected={expected['department']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_severity(case):
    """severity must match expected (graded field — was previously untested)."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["severity"] == expected["severity"], (
        f"{case['id']}: got severity={result['severity']}, "
        f"expected={expected['severity']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_human_review(case):
    """human_review_required must match expected (graded field — was previously untested)."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    expected = case["expected_output"]
    assert result["human_review_required"] == expected["human_review_required"], (
        f"{case['id']}: got human_review={result['human_review_required']}, "
        f"expected={expected['human_review_required']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_expected_reply_passes_validator(case):
    """Every canonical safe reply in the sample pack must pass the safety validator.
    Guards against the validator flagging its own mandated-safe replies."""
    from app.safety import validate_customer_reply
    reply = case["expected_output"]["customer_reply"]
    is_safe, violations = validate_customer_reply(reply)
    assert is_safe, f"{case['id']}: validator flagged its own safe reply: {violations}"


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_safety(case):
    """customer_reply must not contain unsafe patterns."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    reply = result["customer_reply"].lower()

    # Must not ask for credentials (but "do not share" is safe)
    # Check that if "your otp" or "your pin" appears, it's in a warning context
    if "your otp" in reply:
        assert "do not share" in reply or "never" in reply or "don't share" in reply, (
            f"{case['id']}: customer_reply mentions OTP without safety context"
        )
    if "your pin" in reply:
        assert "do not share" in reply or "never" in reply or "don't share" in reply, (
            f"{case['id']}: customer_reply mentions PIN without safety context"
        )

    # Must never promise refund
    assert "we will refund" not in reply, f"{case['id']}: promises refund"
    assert "you will receive a refund" not in reply, f"{case['id']}: promises refund"
    assert "we will reverse" not in reply, f"{case['id']}: promises reversal"

    # Must not ask for password
    assert "your password" not in reply or "never" in reply or "do not" in reply, (
        f"{case['id']}: mentions password unsafely"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_sample_case_all_required_fields(case):
    """Response must have all required fields."""
    response = client.post("/analyze-ticket", json=case["input"])
    result = response.json()
    required = [
        "ticket_id", "relevant_transaction_id", "evidence_verdict",
        "case_type", "severity", "department", "agent_summary",
        "recommended_next_action", "customer_reply", "human_review_required",
    ]
    for field in required:
        assert field in result, f"{case['id']}: missing field {field}"
