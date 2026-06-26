"""Test response schema correctness."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_REQUEST = {
    "ticket_id": "TKT-SCHEMA-01",
    "complaint": "I sent 5000 taka to a wrong number.",
    "language": "en",
    "channel": "in_app_chat",
    "user_type": "customer",
    "transaction_history": [
        {
            "transaction_id": "TXN-TEST-01",
            "timestamp": "2026-04-14T14:08:22Z",
            "type": "transfer",
            "amount": 5000,
            "counterparty": "+8801719876543",
            "status": "completed",
        }
    ],
}

REQUIRED_FIELDS = [
    "ticket_id",
    "relevant_transaction_id",
    "evidence_verdict",
    "case_type",
    "severity",
    "department",
    "agent_summary",
    "recommended_next_action",
    "customer_reply",
    "human_review_required",
]

VALID_ENUMS = {
    "evidence_verdict": ["consistent", "inconsistent", "insufficient_data"],
    "case_type": [
        "wrong_transfer", "payment_failed", "refund_request",
        "duplicate_payment", "merchant_settlement_delay",
        "agent_cash_in_issue", "phishing_or_social_engineering", "other",
    ],
    "severity": ["low", "medium", "high", "critical"],
    "department": [
        "customer_support", "dispute_resolution", "payments_ops",
        "merchant_operations", "agent_operations", "fraud_risk",
    ],
}


def test_response_has_all_required_fields():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    result = response.json()
    for field in REQUIRED_FIELDS:
        assert field in result, f"Missing required field: {field}"


def test_ticket_id_echoed():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    assert response.json()["ticket_id"] == "TKT-SCHEMA-01"


def test_enum_values_valid():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    result = response.json()
    for field, valid_values in VALID_ENUMS.items():
        assert result[field] in valid_values, (
            f"{field}={result[field]} not in {valid_values}"
        )


def test_human_review_is_boolean():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    assert isinstance(response.json()["human_review_required"], bool)


def test_relevant_transaction_id_is_string_or_null():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    val = response.json()["relevant_transaction_id"]
    assert val is None or isinstance(val, str)


def test_confidence_is_float_if_present():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    result = response.json()
    if "confidence" in result and result["confidence"] is not None:
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1


def test_reason_codes_is_list_if_present():
    response = client.post("/analyze-ticket", json=VALID_REQUEST)
    assert response.status_code == 200
    result = response.json()
    if "reason_codes" in result and result["reason_codes"] is not None:
        assert isinstance(result["reason_codes"], list)
