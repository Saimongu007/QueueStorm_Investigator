from pydantic import BaseModel, field_validator
from typing import Optional, List
from enum import Enum


# --- Request Enums ---

class Language(str, Enum):
    en = "en"
    bn = "bn"
    mixed = "mixed"


class Channel(str, Enum):
    in_app_chat = "in_app_chat"
    call_center = "call_center"
    email = "email"
    merchant_portal = "merchant_portal"
    field_agent = "field_agent"


class UserType(str, Enum):
    customer = "customer"
    merchant = "merchant"
    agent = "agent"
    unknown = "unknown"


class TransactionType(str, Enum):
    transfer = "transfer"
    payment = "payment"
    cash_in = "cash_in"
    cash_out = "cash_out"
    settlement = "settlement"
    refund = "refund"


class TransactionStatus(str, Enum):
    completed = "completed"
    failed = "failed"
    pending = "pending"
    reversed = "reversed"


# --- Request Models ---

class TransactionEntry(BaseModel):
    transaction_id: str
    timestamp: str
    type: TransactionType
    amount: float
    counterparty: str
    status: TransactionStatus


class TicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Optional[Language] = None
    channel: Optional[Channel] = None
    user_type: Optional[UserType] = None
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[TransactionEntry]] = []
    metadata: Optional[dict] = None

    @field_validator("language", "channel", "user_type", mode="before")
    @classmethod
    def _coerce_unknown_optional_enum(cls, v, info):
        """Lenient parsing: an unknown/invalid optional enum value becomes None
        rather than rejecting the whole request. Maximizes 'handles unusual input'
        reliability without ever shipping an invalid value downstream."""
        if v is None:
            return None
        valid = {
            "language": {e.value for e in Language},
            "channel": {e.value for e in Channel},
            "user_type": {e.value for e in UserType},
        }[info.field_name]
        return v if isinstance(v, str) and v in valid else None


# --- Response Enums ---

class EvidenceVerdict(str, Enum):
    consistent = "consistent"
    inconsistent = "inconsistent"
    insufficient_data = "insufficient_data"


class CaseType(str, Enum):
    wrong_transfer = "wrong_transfer"
    payment_failed = "payment_failed"
    refund_request = "refund_request"
    duplicate_payment = "duplicate_payment"
    merchant_settlement_delay = "merchant_settlement_delay"
    agent_cash_in_issue = "agent_cash_in_issue"
    phishing_or_social_engineering = "phishing_or_social_engineering"
    other = "other"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Department(str, Enum):
    customer_support = "customer_support"
    dispute_resolution = "dispute_resolution"
    payments_ops = "payments_ops"
    merchant_operations = "merchant_operations"
    agent_operations = "agent_operations"
    fraud_risk = "fraud_risk"


# --- Response Model ---

class TicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: Optional[str] = None
    evidence_verdict: EvidenceVerdict
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: Optional[float] = None
    reason_codes: Optional[List[str]] = None
