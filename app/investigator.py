"""Core investigation logic — the heart of evidence reasoning.

Implements the complaint investigator pipeline:
1. Sanitize → 2. Classify → 3. Transaction match → 4. Route →
5. LLM/fallback → 6. Safety validate → 7. Build response
"""

import re
import logging
from datetime import datetime
from typing import Optional

from app.models import (
    TicketRequest, TicketResponse, TransactionEntry,
    CaseType, Severity, Department, EvidenceVerdict,
)
from app import safety, rules

logger = logging.getLogger(__name__)


# --- Signal extraction from complaint text ---

def extract_amount(complaint: str) -> Optional[float]:
    """Extract monetary amount from complaint text."""
    # Match patterns like "5000 taka", "1200 tk", "850 BDT", or standalone large numbers
    patterns = [
        r"(\d[\d,]*(?:\.\d+)?)\s*(?:taka|tk|bdt|টাকা)",
        r"(?:sent|paid|transfer|payment|amount|of|deposit)\s+(\d[\d,]*(?:\.\d+)?)",
        r"(\d[\d,]*(?:\.\d+)?)\s*(?:sent|paid|transferred|deposited)",
    ]
    for pattern in patterns:
        match = re.search(pattern, complaint, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                if amount >= 1:  # Filter out trivially small numbers
                    return amount
            except ValueError:
                continue

    # Fallback: find standalone numbers >= 100 that could be amounts
    for match in re.finditer(r"\b(\d{3,})\b", complaint):
        try:
            val = float(match.group(1))
            if val >= 100:
                return val
        except ValueError:
            continue

    # Bangla digit extraction
    bangla_digits = {"০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
                     "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"}
    bangla_num_pattern = r"([০-৯]+)"
    for match in re.finditer(bangla_num_pattern, complaint):
        num_str = "".join(bangla_digits.get(c, c) for c in match.group(1))
        try:
            val = float(num_str)
            if val >= 100:
                return val
        except ValueError:
            continue

    return None


def extract_time_signals(complaint: str) -> list[str]:
    """Extract time-related signals from complaint text."""
    signals = []
    complaint_lower = complaint.lower()

    time_keywords = {
        "today": "today", "yesterday": "yesterday",
        "this morning": "morning", "this afternoon": "afternoon",
        "this evening": "evening", "tonight": "tonight",
        "আজ": "today", "গতকাল": "yesterday", "সকালে": "morning",
        "বিকেলে": "afternoon",
    }
    for keyword, signal in time_keywords.items():
        if keyword in complaint_lower:
            signals.append(signal)

    # Match specific times like "2pm", "around 3", "at 14:00"
    time_pattern = r"(?:around\s+|at\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:am|pm|AM|PM)?"
    for match in re.finditer(time_pattern, complaint):
        signals.append(f"hour_{match.group(1)}")

    return signals


def extract_type_signals(complaint: str) -> list[str]:
    """Extract transaction type signals from complaint."""
    complaint_lower = complaint.lower()
    signals = []

    type_map = {
        "transfer": ["sent", "transfer", "ট্রান্সফার", "পাঠিয়েছি"],
        "payment": ["paid", "payment", "bill", "recharge", "পেমেন্ট", "বিল"],
        "cash_in": ["cash in", "deposit", "ক্যাশ ইন", "জমা"],
        "cash_out": ["cash out", "withdraw", "ক্যাশ আউট"],
        "settlement": ["settlement", "সেটেলমেন্ট"],
    }

    for txn_type, keywords in type_map.items():
        for keyword in keywords:
            if keyword in complaint_lower:
                signals.append(txn_type)
                break

    return signals


def extract_counterparty(complaint: str) -> Optional[str]:
    """Extract counterparty identifiers (phone numbers, merchant/agent IDs)."""
    # Bangladesh phone numbers
    patterns = [
        r"\+880\d{10}",
        r"01[3-9]\d{8}",
        r"MERCHANT[-_]\w+",
        r"AGENT[-_]\w+",
    ]
    for pattern in patterns:
        match = re.search(pattern, complaint, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


# --- Transaction scoring and matching ---

def score_transaction(
    txn: TransactionEntry,
    amount: Optional[float],
    type_signals: list[str],
    time_signals: list[str],
    counterparty: Optional[str],
) -> int:
    """Score how well a transaction matches the complaint signals."""
    score = 0

    # Amount match (40 points)
    if amount is not None and abs(txn.amount - amount) < 1:
        score += 40

    # Type match (25 points)
    if txn.type.value in type_signals:
        score += 25

    # Time match (20 points)
    if time_signals:
        try:
            txn_time = datetime.fromisoformat(txn.timestamp.replace("Z", "+00:00"))
            for signal in time_signals:
                if signal == "today":
                    score += 20
                    break
                elif signal == "yesterday":
                    score += 20
                    break
                elif signal == "morning" and txn_time.hour < 12:
                    score += 20
                    break
                elif signal == "afternoon" and 12 <= txn_time.hour < 18:
                    score += 20
                    break
                elif signal.startswith("hour_"):
                    try:
                        hour = int(signal.split("_")[1])
                        if abs(txn_time.hour - hour) <= 1 or abs(txn_time.hour - (hour + 12)) <= 1:
                            score += 20
                            break
                    except ValueError:
                        pass
        except (ValueError, AttributeError):
            pass

    # Counterparty match (15 points)
    if counterparty and counterparty.lower() in txn.counterparty.lower():
        score += 15

    return score


def find_relevant_transaction(
    complaint: str,
    history: list[TransactionEntry],
    case_type: CaseType,
) -> tuple[Optional[str], str]:
    """Find the most relevant transaction and determine evidence verdict.

    Returns (transaction_id_or_none, evidence_verdict_string).
    """
    # No history → insufficient data
    if not history:
        return None, "insufficient_data"

    # Phishing cases don't involve a specific financial transaction
    if case_type == CaseType.phishing_or_social_engineering:
        return None, "insufficient_data"

    # Special handling for duplicate payments
    if case_type == CaseType.duplicate_payment:
        dup_txn = find_duplicate_transaction(history)
        if dup_txn:
            return dup_txn, "consistent"

    # Extract signals from complaint
    amount = extract_amount(complaint)
    type_signals = extract_type_signals(complaint)
    time_signals = extract_time_signals(complaint)
    counterparty_signal = extract_counterparty(complaint)

    # Score each transaction
    scored = []
    for txn in history:
        s = score_transaction(txn, amount, type_signals, time_signals, counterparty_signal)
        scored.append((s, txn))

    scored.sort(key=lambda x: x[0], reverse=True)

    # No scores above threshold
    if not scored or scored[0][0] <= 30:
        # If only one transaction exists and case_type matches, use it
        if len(history) == 1:
            txn = history[0]
            verdict = determine_evidence_verdict(complaint, txn, history, case_type)
            return txn.transaction_id, verdict
        return None, "insufficient_data"

    top_score = scored[0][0]

    # Ambiguous: 2+ transactions whose scores are within 15 points of the top.
    # When the evidence cannot single out one transaction, do not guess.
    candidates_within_15 = [s for s in scored if top_score - s[0] <= 15 and s[0] > 30]
    if len(candidates_within_15) >= 2:
        return None, "insufficient_data"

    # Clear winner
    best_txn = scored[0][1]
    verdict = determine_evidence_verdict(complaint, best_txn, history, case_type)
    return best_txn.transaction_id, verdict


def determine_evidence_verdict(
    complaint: str,
    txn: TransactionEntry,
    history: list[TransactionEntry],
    case_type: CaseType,
) -> str:
    """Determine whether evidence supports or contradicts the complaint."""
    # wrong_transfer + same counterparty seen 2+ more times = inconsistent
    if case_type == CaseType.wrong_transfer:
        same_counterparty_count = sum(
            1 for t in history
            if t.counterparty == txn.counterparty and t.transaction_id != txn.transaction_id
        )
        if same_counterparty_count >= 2:
            return "inconsistent"

    # payment_failed + status=failed + claims balance deducted = consistent
    # (this IS the payment_failed pattern — failed status + deduction is exactly
    # what the customer is reporting)
    if case_type == CaseType.payment_failed and txn.status.value == "failed":
        return "consistent"

    # agent_cash_in_issue + pending = consistent
    if case_type == CaseType.agent_cash_in_issue and txn.status.value == "pending":
        return "consistent"

    # merchant_settlement_delay + pending = consistent
    if case_type == CaseType.merchant_settlement_delay and txn.status.value == "pending":
        return "consistent"

    # duplicate_payment with two identical within 60s = consistent
    if case_type == CaseType.duplicate_payment:
        for other in history:
            if (other.transaction_id != txn.transaction_id
                    and other.amount == txn.amount
                    and other.counterparty == txn.counterparty
                    and other.status.value == "completed"
                    and txn.status.value == "completed"):
                try:
                    t1 = datetime.fromisoformat(txn.timestamp.replace("Z", "+00:00"))
                    t2 = datetime.fromisoformat(other.timestamp.replace("Z", "+00:00"))
                    if abs((t1 - t2).total_seconds()) <= 60:
                        return "consistent"
                except (ValueError, AttributeError):
                    pass

    # Default: if we found a matching transaction, it's consistent
    return "consistent"


def find_duplicate_transaction(history: list[TransactionEntry]) -> Optional[str]:
    """Find duplicate transactions (same amount, counterparty, within 60s).

    Returns the transaction_id of the SECOND (later) one.
    """
    for i, t1 in enumerate(history):
        for j, t2 in enumerate(history):
            if i >= j:
                continue
            if (t1.amount == t2.amount
                    and t1.counterparty == t2.counterparty
                    and t1.status.value == "completed"
                    and t2.status.value == "completed"):
                try:
                    time1 = datetime.fromisoformat(t1.timestamp.replace("Z", "+00:00"))
                    time2 = datetime.fromisoformat(t2.timestamp.replace("Z", "+00:00"))
                    if abs((time1 - time2).total_seconds()) <= 60:
                        # Return the later (second) transaction
                        return t2.transaction_id if time2 > time1 else t1.transaction_id
                except (ValueError, AttributeError):
                    pass
    return None


# --- Helper functions ---

def get_amount(history: list[TransactionEntry], txn_id: Optional[str]) -> Optional[float]:
    """Get the amount for a specific transaction ID."""
    if not txn_id or not history:
        return None
    for txn in history:
        if txn.transaction_id == txn_id:
            return txn.amount
    return None


def get_transaction(history: list[TransactionEntry], txn_id: Optional[str]) -> Optional[TransactionEntry]:
    """Get the full transaction object for a specific ID."""
    if not txn_id or not history:
        return None
    for txn in history:
        if txn.transaction_id == txn_id:
            return txn
    return None


def format_transaction(history: list[TransactionEntry], txn_id: Optional[str]) -> dict:
    """Format transaction details for LLM context."""
    txn = get_transaction(history, txn_id)
    if not txn:
        return {}
    return {
        "transaction_id": txn.transaction_id,
        "timestamp": txn.timestamp,
        "type": txn.type.value,
        "amount": txn.amount,
        "counterparty": txn.counterparty,
        "status": txn.status.value,
    }


def calculate_confidence(
    evidence_verdict: str,
    case_type: CaseType,
    relevant_txn_id: Optional[str],
) -> float:
    """Calculate confidence score for the verdict."""
    base = 0.7
    if evidence_verdict == "consistent":
        base += 0.15
    elif evidence_verdict == "insufficient_data":
        base -= 0.15
    elif evidence_verdict == "inconsistent":
        base -= 0.05
    if relevant_txn_id is not None:
        base += 0.05
    if case_type == CaseType.phishing_or_social_engineering:
        base = max(base, 0.9)
    return round(min(max(base, 0.5), 0.99), 2)


def build_reason_codes(
    case_type: CaseType,
    evidence_verdict: str,
    relevant_txn_id: Optional[str],
    severity: Severity,
) -> list[str]:
    """Build descriptive reason codes for the verdict."""
    codes = [case_type.value]

    if relevant_txn_id:
        codes.append("transaction_match")
    else:
        codes.append("no_transaction_match")

    if evidence_verdict == "consistent":
        codes.append("evidence_consistent")
    elif evidence_verdict == "inconsistent":
        codes.append("evidence_inconsistent")
    else:
        codes.append("insufficient_evidence")

    # Add specific reason codes based on case type
    reason_map = {
        CaseType.wrong_transfer: "dispute_initiated",
        CaseType.payment_failed: "potential_balance_deduction",
        CaseType.duplicate_payment: "biller_verification_required",
        CaseType.phishing_or_social_engineering: "critical_escalation",
        CaseType.agent_cash_in_issue: "agent_ops",
        CaseType.merchant_settlement_delay: "pending",
        CaseType.refund_request: "merchant_policy_dependent",
    }
    extra = reason_map.get(case_type)
    if extra:
        codes.append(extra)

    if severity == Severity.critical:
        if "critical_escalation" not in codes:
            codes.append("critical_escalation")

    return codes


# --- Main investigation pipeline ---

async def investigate(ticket: TicketRequest) -> TicketResponse:
    """Full investigation pipeline. This is the main entry point.

    Sequence:
    1. Sanitize complaint for injection
    2. Rule-based classification
    3. Transaction matching + evidence verdict
    4. Severity + department + human_review (pure rules)
    5. Build LLM context
    6. LLM text generation (with rule-based fallback)
    7. Post-generation safety validation
    8. Build confidence + reason codes
    9. Return TicketResponse
    """
    # Filter out null entries from transaction_history
    history = [t for t in (ticket.transaction_history or []) if t is not None]

    # 1. Sanitize complaint for injection (for LLM only)
    safe_complaint = safety.sanitize_complaint(ticket.complaint)

    # 2. Rule-based case classification (use original complaint, not sanitized)
    case_type = rules.classify_case(
        ticket.complaint, history, ticket.language
    )

    # 3. Transaction matching + evidence verdict
    relevant_txn_id, evidence_verdict = find_relevant_transaction(
        ticket.complaint, history, case_type
    )

    # 4. Determine severity, department, human review
    amount = get_amount(history, relevant_txn_id)
    user_type = ticket.user_type.value if ticket.user_type else "customer"

    severity = rules.determine_severity(case_type, amount, evidence_verdict)
    department = rules.route_department(case_type, evidence_verdict, user_type)
    human_review = rules.requires_human_review(
        case_type, evidence_verdict, relevant_txn_id, amount
    )

    # 5. Build context for text generation
    language = ticket.language.value if ticket.language else "en"
    # Promotional/cashback complaints stay case_type=`other` (spec-legal) but get
    # cashback-aware wording from the text layer.
    is_promo = rules.is_promotional(ticket.complaint.lower())
    context = {
        "ticket_id": ticket.ticket_id,
        "complaint": safe_complaint,
        "language": language,
        "user_type": user_type,
        "channel": ticket.channel.value if ticket.channel else None,
        "campaign_context": ticket.campaign_context,
        "case_type": case_type.value,
        "evidence_verdict": evidence_verdict,
        "relevant_transaction_id": relevant_txn_id,
        "severity": severity.value,
        "department": department.value,
        "human_review_required": human_review,
        "transaction_details": format_transaction(history, relevant_txn_id),
        "text_variant": "promotional" if is_promo else None,
    }

    # 6. LLM text generation (with rule-based fallback)
    try:
        from app import llm
        text_fields = await llm.generate_text_fields(context)
    except Exception as e:
        logger.warning(f"LLM module failed, using rule fallback: {e}")
        text_fields = rules.generate_text_fields(context)

    # 7. Post-generation safety validation on customer_reply
    is_safe, violations = safety.validate_customer_reply(text_fields["customer_reply"])
    if not is_safe:
        logger.warning(f"Safety violation in {ticket.ticket_id}: {violations}")
        text_fields["customer_reply"] = safety.get_safe_reply(language)

    # Also validate recommended_next_action
    is_action_safe, action_violations = safety.validate_recommended_action(
        text_fields["recommended_next_action"]
    )
    if not is_action_safe:
        logger.warning(f"Action safety violation in {ticket.ticket_id}: {action_violations}")
        text_fields["recommended_next_action"] = safety.get_safe_action()

    # 8. Build confidence + reason codes
    confidence = calculate_confidence(evidence_verdict, case_type, relevant_txn_id)
    reason_codes = build_reason_codes(case_type, evidence_verdict, relevant_txn_id, severity)

    # 9. Return response
    return TicketResponse(
        ticket_id=ticket.ticket_id,
        relevant_transaction_id=relevant_txn_id,
        evidence_verdict=EvidenceVerdict(evidence_verdict),
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=text_fields["agent_summary"],
        recommended_next_action=text_fields["recommended_next_action"],
        customer_reply=text_fields["customer_reply"],
        human_review_required=human_review,
        confidence=confidence,
        reason_codes=reason_codes,
    )
