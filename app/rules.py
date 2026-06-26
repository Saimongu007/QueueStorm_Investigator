"""Rule-based classification, routing, and fallback text generation.

This module has ZERO external dependencies (no LLM, no network calls).
It handles all deterministic decisions and serves as the text generation
fallback when the LLM is unavailable.
"""

from typing import Optional
from app.models import CaseType, Severity, Department


# --- Case type classification by keyword matching ---

# Phishing detection is handled separately (see is_phishing) — a bare mention of
# "pin"/"otp"/"password" is NOT phishing (a customer can legitimately mention their
# PIN in a payment_failed or refund complaint). Phishing requires either an explicit
# scam phrase OR a credential noun co-occurring with a social-engineering signal.

# Explicit scam phrases — phishing on their own (no credential noun required).
PHISHING_STRONG = [
    "fraud call", "phishing", "scam", "impersonat", "social engineering",
    "pretending to be", "claiming to be from", "claims to be from",
    "pretending to be from", "fake call", "fake sms", "fraudster",
    "প্রতারণা", "জালিয়াতি", "ভুয়া কল",
]

# Social-engineering signals — an unsolicited third party contacting/pressuring the user.
SOCIAL_ENG_SIGNALS = [
    "called me", "they called", "phoned", "someone called", "got a call",
    "sms", "text message", "asked for my", "asked me for", "asked for the",
    "share your", "give your", "send your", "tell us your", "claiming to be",
    "claims to be", "pretending", "verify your account", "account will be blocked",
    "account block", "click", "link", "stranger", "unknown number",
    "ফোন করেছে", "কল করেছে", "চেয়েছে", "ব্লক",
]

# Credential nouns.
CREDENTIAL_NOUNS = [
    "otp", "pin", "password", "one-time password", "one time password",
    "ওটিপি", "পিন", "পাসওয়ার্ড",
]


def is_phishing(complaint_lower: str) -> bool:
    """Detect social engineering / phishing without over-matching bare credentials."""
    if any(p in complaint_lower for p in PHISHING_STRONG):
        return True
    has_credential = any(c in complaint_lower for c in CREDENTIAL_NOUNS)
    has_social = any(s in complaint_lower for s in SOCIAL_ENG_SIGNALS)
    return has_credential and has_social


# Promotional/cashback complaints have no dedicated case_type in the official 8-value
# taxonomy, so they map to `other` (spec-compliant). We still detect them so the text
# layer can produce a cashback-aware reply (see text_variant in generate_text_fields).
PROMO_KEYWORDS = [
    "cashback", "campaign", "offer", "discount", "promot", "bonus",
    "ক্যাশব্যাক", "অফার", "বোনাস",
]


def is_promotional(complaint_lower: str) -> bool:
    """Detect a cashback/campaign/offer complaint (classified as `other`)."""
    return any(k in complaint_lower for k in PROMO_KEYWORDS)


# Priority order: phishing > promotional(->other) > duplicate > wrong_transfer
#   > payment_failed > agent_cash_in > merchant_settlement > refund > other
CASE_KEYWORDS: list[tuple[CaseType, list[str]]] = [
    (CaseType.duplicate_payment, [
        "twice", "double", "duplicate", "charged twice", "deducted twice",
        "two times", "2 times", "দুইবার", "দুবার কাটা",
    ]),
    (CaseType.wrong_transfer, [
        "wrong number", "wrong person", "wrong transfer", "wrong recipient",
        "sent to wrong", "typed wrong", "mistaken", "accidental transfer",
        "didn't get it", "not received",
        "ভুল নম্বর", "ভুল ট্রান্সফার", "ভুল ব্যক্তি",
    ]),
    (CaseType.payment_failed, [
        "payment failed", "failed", "showed failed", "balance deducted",
        "not processed", "not successful", "transaction failed",
        "পেমেন্ট ফেইল", "ব্যালেন্স কাটা", "ফেইল",
    ]),
    (CaseType.agent_cash_in_issue, [
        "cash in", "agent", "deposit", "not reflected", "balance not updated",
        "ক্যাশ ইন", "এজেন্ট", "ব্যালেন্সে আসেনি", "জমা",
    ]),
    (CaseType.merchant_settlement_delay, [
        "settlement", "not settled", "sales not received",
        "settlement delay", "সেটেলমেন্ট", "পেমেন্ট আসেনি",
    ]),
    (CaseType.refund_request, [
        "refund", "return my money", "want my money back", "cancel",
        "money back", "get back", "রিফান্ড", "টাকা ফেরত",
    ]),
]


def classify_case(complaint: str, transaction_history: list, language: Optional[str]) -> CaseType:
    """Classify the complaint using keyword matching with priority ordering."""
    complaint_lower = complaint.lower()

    # Phishing has top priority but uses co-occurrence (not bare credential nouns).
    if is_phishing(complaint_lower):
        return CaseType.phishing_or_social_engineering

    # Cashback/campaign complaints -> `other` (no promo case_type in the spec).
    # Checked before duplicate_payment so "cashed out twice ... no cashback" is not
    # misread as a duplicate charge.
    if is_promotional(complaint_lower):
        return CaseType.other

    for case_type, keywords in CASE_KEYWORDS:
        for keyword in keywords:
            if keyword.lower() in complaint_lower:
                return case_type

    return CaseType.other


# --- Severity determination ---

def determine_severity(
    case_type: CaseType,
    amount: Optional[float],
    evidence_verdict: str,
) -> Severity:
    """Determine severity based on case type, amount, and evidence."""
    if case_type == CaseType.phishing_or_social_engineering:
        return Severity.critical
    if case_type == CaseType.wrong_transfer and amount is not None and amount >= 5000:
        return Severity.high
    if case_type == CaseType.duplicate_payment:
        return Severity.high
    if case_type == CaseType.payment_failed and evidence_verdict == "consistent":
        return Severity.high
    if case_type == CaseType.agent_cash_in_issue:
        return Severity.high
    if case_type == CaseType.merchant_settlement_delay:
        return Severity.medium
    if case_type == CaseType.wrong_transfer and evidence_verdict == "inconsistent":
        return Severity.medium
    if case_type == CaseType.refund_request:
        return Severity.low
    if case_type == CaseType.other:
        return Severity.low  # vague/other cases are low severity (SAMPLE-06)
    return Severity.medium


# --- Department routing ---

DEPARTMENT_MAP = {
    CaseType.wrong_transfer: Department.dispute_resolution,
    CaseType.payment_failed: Department.payments_ops,
    CaseType.duplicate_payment: Department.payments_ops,
    CaseType.refund_request: Department.customer_support,
    CaseType.merchant_settlement_delay: Department.merchant_operations,
    CaseType.agent_cash_in_issue: Department.agent_operations,
    CaseType.phishing_or_social_engineering: Department.fraud_risk,
    CaseType.other: Department.customer_support,
}


def route_department(
    case_type: CaseType,
    evidence_verdict: str,
    user_type: Optional[str] = None,
) -> Department:
    """Route to the correct department.

    Case-type routing wins first (so phishing->fraud_risk, wrong_transfer->dispute,
    etc. are never overridden). Special case: a contested refund goes to dispute
    resolution. Only for an otherwise-uncategorised `other` complaint do we fall back
    to the reporter's role — the spec lists "merchant side complaints" ->
    merchant_operations and "agent side complaints" -> agent_operations.
    """
    if case_type == CaseType.refund_request and evidence_verdict == "inconsistent":
        return Department.dispute_resolution
    if case_type == CaseType.other:
        if user_type == "merchant":
            return Department.merchant_operations
        if user_type == "agent":
            return Department.agent_operations
    return DEPARTMENT_MAP.get(case_type, Department.customer_support)


# --- Human review rules ---

def requires_human_review(
    case_type: CaseType,
    evidence_verdict: str,
    relevant_txn_id: Optional[str],
    amount: Optional[float],
) -> bool:
    """Determine whether a human agent must review this case.

    Spec: "True for disputes, suspicious cases, high-value cases, or ambiguous
    evidence." Keyed off semantics, NOT severity — SAMPLE-03 (payment_failed,
    high) and SAMPLE-09 (settlement, 15000) are both False, while SAMPLE-07
    (agent_cash_in, high) is True. The dispute set only triggers once a specific
    transaction has actually been identified (SAMPLE-08 stays False).
    """
    if case_type == CaseType.phishing_or_social_engineering:  # suspicious
        return True
    if evidence_verdict == "inconsistent":                    # ambiguous / contested
        return True
    if case_type in (
        CaseType.wrong_transfer,
        CaseType.duplicate_payment,
        CaseType.agent_cash_in_issue,
    ) and relevant_txn_id is not None:                        # disputes (txn identified)
        return True
    if amount is not None and amount >= 25000:                # high value
        return True
    return False


# --- Rule-based text generation (LLM fallback) ---

TEMPLATES_EN = {
    CaseType.wrong_transfer: {
        "agent_summary": (
            "Customer reports sending {amount} BDT via {txn_id} to {counterparty}, "
            "which they believe was the wrong recipient."
        ),
        "recommended_next_action": (
            "Verify {txn_id} details with the customer and initiate the "
            "wrong-transfer dispute workflow per policy."
        ),
        "customer_reply": (
            "We have noted your concern about transaction {txn_id}. "
            "Please do not share your PIN or OTP with anyone. "
            "Our dispute team will review the case and contact you "
            "through official support channels."
        ),
    },
    CaseType.payment_failed: {
        "agent_summary": (
            "Customer reports a payment of {amount} BDT ({txn_id}) that failed "
            "but balance may have been deducted. Requires payments operations investigation."
        ),
        "recommended_next_action": (
            "Investigate {txn_id} ledger status. If balance was deducted on a failed "
            "payment, initiate the automatic reversal flow within standard SLA."
        ),
        "customer_reply": (
            "We have noted that transaction {txn_id} may have caused an unexpected "
            "balance deduction. Our payments team will review the case and any eligible "
            "amount will be returned through official channels. "
            "Please do not share your PIN or OTP with anyone."
        ),
    },
    CaseType.refund_request: {
        "agent_summary": (
            "Customer requests refund of {amount} BDT for {txn_id} "
            "(merchant payment). Not a service failure."
        ),
        "recommended_next_action": (
            "Inform the customer that refund eligibility depends on the merchant's "
            "own policy. Provide guidance on contacting the merchant directly for a refund."
        ),
        "customer_reply": (
            "Thank you for reaching out. Refunds for completed merchant payments "
            "depend on the merchant's own policy. We recommend contacting the merchant "
            "directly. If you need help reaching them, please reply and we will guide you. "
            "Please do not share your PIN or OTP with anyone."
        ),
    },
    CaseType.duplicate_payment: {
        "agent_summary": (
            "Customer reports duplicate payment of {amount} BDT to {counterparty}. "
            "Two identical transactions found: {txn_id}."
        ),
        "recommended_next_action": (
            "Verify the duplicate with payments_ops. If the biller confirms only one "
            "payment was received, initiate reversal of the duplicate transaction."
        ),
        "customer_reply": (
            "We have noted the possible duplicate payment for transaction {txn_id}. "
            "Our payments team will verify with the biller and any eligible amount will "
            "be returned through official channels. "
            "Please do not share your PIN or OTP with anyone."
        ),
    },
    CaseType.merchant_settlement_delay: {
        "agent_summary": (
            "Merchant reports settlement of {amount} BDT ({txn_id}) is delayed "
            "beyond the standard window. Settlement status is pending."
        ),
        "recommended_next_action": (
            "Route to merchant_operations to verify settlement batch status. "
            "If the batch is delayed, communicate a revised ETA to the merchant."
        ),
        "customer_reply": (
            "We have noted your concern about settlement {txn_id}. "
            "Our merchant operations team will check the batch status and update you "
            "on the expected settlement time through official channels."
        ),
    },
    CaseType.agent_cash_in_issue: {
        "agent_summary": (
            "Customer reports {amount} BDT cash-in via {counterparty} ({txn_id}) "
            "not reflected in balance. Transaction status is pending."
        ),
        "recommended_next_action": (
            "Investigate {txn_id} pending status with agent operations. "
            "Confirm settlement state and resolve within the standard cash-in SLA."
        ),
        "customer_reply": (
            "We have noted your concern about transaction {txn_id}. "
            "Our agent operations team will investigate and update you "
            "through official channels. "
            "Please do not share your PIN or OTP with anyone."
        ),
    },
    CaseType.phishing_or_social_engineering: {
        "agent_summary": (
            "Customer reports a suspicious contact requesting credentials. "
            "Likely social engineering attempt."
        ),
        "recommended_next_action": (
            "Escalate to fraud_risk team immediately. Confirm to customer that "
            "the company never asks for OTP. Log the reported contact details "
            "for fraud pattern analysis."
        ),
        "customer_reply": (
            "Thank you for reaching out before sharing any information. "
            "We never ask for your PIN, OTP, or password under any circumstances. "
            "Please do not share these with anyone, even if they claim to be from us. "
            "Our fraud team has been notified of this incident."
        ),
    },
    CaseType.other: {
        "agent_summary": (
            "Customer reports a concern that does not match a specific category. "
            "Further information may be needed."
        ),
        "recommended_next_action": (
            "Reply to customer asking for specific details: which transaction, "
            "what amount, what went wrong, and approximate time."
        ),
        "customer_reply": (
            "Thank you for reaching out. To help you faster, please share the "
            "transaction ID, the amount involved, and a short description of what "
            "went wrong. Please do not share your PIN or OTP with anyone."
        ),
    },
}

TEMPLATES_BN = {
    CaseType.wrong_transfer: {
        "agent_summary": (
            "গ্রাহক {counterparty}-এ {amount} টাকা ভুল ট্রান্সফারের অভিযোগ করেছেন। "
            "লেনদেন: {txn_id}।"
        ),
        "recommended_next_action": (
            "{txn_id} এর বিবরণ যাচাই করুন এবং ভুল-ট্রান্সফার বিরোধ কর্মপ্রবাহ শুরু করুন।"
        ),
        "customer_reply": (
            "আপনার লেনদেন {txn_id} এর বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের বিরোধ নিষ্পত্তি দল এটি পর্যালোচনা করবে এবং "
            "অফিসিয়াল চ্যানেলে আপনাকে জানাবে। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
    CaseType.payment_failed: {
        "agent_summary": (
            "গ্রাহক {amount} টাকার পেমেন্ট ({txn_id}) ফেইল হওয়ার অভিযোগ করেছেন "
            "কিন্তু ব্যালেন্স কেটে নেওয়া হয়েছে।"
        ),
        "recommended_next_action": (
            "{txn_id} লেজার স্থিতি তদন্ত করুন। ফেইল পেমেন্টে ব্যালেন্স কাটা হলে "
            "স্বয়ংক্রিয় রিভার্সাল প্রক্রিয়া শুরু করুন।"
        ),
        "customer_reply": (
            "আপনার লেনদেন {txn_id} এর বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের পেমেন্ট দল বিষয়টি পর্যালোচনা করবে এবং "
            "যোগ্য পরিমাণ অফিসিয়াল চ্যানেলে ফেরত দেওয়া হবে। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
    CaseType.agent_cash_in_issue: {
        "agent_summary": (
            "গ্রাহক {counterparty} এর মাধ্যমে {amount} টাকা ক্যাশ ইন ({txn_id}) "
            "ব্যালেন্সে প্রতিফলিত না হওয়ার অভিযোগ করেছেন।"
        ),
        "recommended_next_action": (
            "{txn_id} পেন্ডিং স্থিতি এজেন্ট অপারেশনের সাথে তদন্ত করুন। "
            "সেটেলমেন্ট অবস্থা নিশ্চিত করুন।"
        ),
        "customer_reply": (
            "আপনার লেনদেন {txn_id} এর বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের এজেন্ট অপারেশন্স দল এটি দ্রুত যাচাই করবে এবং "
            "অফিসিয়াল চ্যানেলে আপনাকে জানাবে। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
    CaseType.phishing_or_social_engineering: {
        "agent_summary": (
            "গ্রাহক সন্দেহজনক যোগাযোগের রিপোর্ট করেছেন যেখানে "
            "তথ্য চাওয়া হয়েছে। সম্ভবত সোশ্যাল ইঞ্জিনিয়ারিং প্রচেষ্টা।"
        ),
        "recommended_next_action": (
            "অবিলম্বে fraud_risk দলে এস্কেলেট করুন। "
            "রিপোর্ট করা যোগাযোগের বিবরণ লগ করুন।"
        ),
        "customer_reply": (
            "তথ্য শেয়ার করার আগে আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। "
            "আমরা কখনোই আপনার পিন, ওটিপি বা পাসওয়ার্ড চাই না। "
            "অনুগ্রহ করে কারো সাথে এগুলো শেয়ার করবেন না। "
            "আমাদের জালিয়াতি দলকে অবহিত করা হয়েছে।"
        ),
    },
    CaseType.duplicate_payment: {
        "agent_summary": (
            "গ্রাহক {counterparty}-এ {amount} টাকার ডুপ্লিকেট পেমেন্টের অভিযোগ করেছেন। "
            "লেনদেন: {txn_id}।"
        ),
        "recommended_next_action": (
            "payments_ops এর সাথে ডুপ্লিকেট যাচাই করুন। "
            "বিলার নিশ্চিত করলে ডুপ্লিকেট লেনদেনের রিভার্সাল শুরু করুন।"
        ),
        "customer_reply": (
            "আপনার লেনদেন {txn_id} এর সম্ভাব্য ডুপ্লিকেট পেমেন্টের বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের পেমেন্ট দল বিলারের সাথে যাচাই করবে এবং যোগ্য পরিমাণ "
            "অফিসিয়াল চ্যানেলে ফেরত দেওয়া হবে। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
    CaseType.merchant_settlement_delay: {
        "agent_summary": (
            "মার্চেন্ট {amount} টাকার সেটেলমেন্ট ({txn_id}) বিলম্বের অভিযোগ করেছেন।"
        ),
        "recommended_next_action": (
            "merchant_operations এ রাউট করুন। সেটেলমেন্ট ব্যাচ স্ট্যাটাস যাচাই করুন।"
        ),
        "customer_reply": (
            "আপনার সেটেলমেন্ট {txn_id} এর বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের মার্চেন্ট অপারেশন্স দল ব্যাচ স্ট্যাটাস যাচাই করবে এবং "
            "অফিসিয়াল চ্যানেলে আপডেট জানাবে।"
        ),
    },
    CaseType.refund_request: {
        "agent_summary": (
            "গ্রাহক {txn_id} এর জন্য {amount} টাকা রিফান্ডের অনুরোধ করেছেন।"
        ),
        "recommended_next_action": (
            "গ্রাহককে জানান যে রিফান্ড মার্চেন্টের নীতির উপর নির্ভরশীল।"
        ),
        "customer_reply": (
            "আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। সম্পন্ন মার্চেন্ট পেমেন্টের "
            "রিফান্ড মার্চেন্টের নীতির উপর নির্ভরশীল। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
    CaseType.other: {
        "agent_summary": (
            "গ্রাহক একটি অভিযোগ জানিয়েছেন যা নির্দিষ্ট বিভাগে পড়ে না। "
            "আরো তথ্য প্রয়োজন।"
        ),
        "recommended_next_action": (
            "গ্রাহককে নির্দিষ্ট বিবরণ জানাতে বলুন: কোন লেনদেন, কত টাকা, "
            "কী সমস্যা হয়েছে।"
        ),
        "customer_reply": (
            "আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। আপনাকে দ্রুত সাহায্য করতে, "
            "অনুগ্রহ করে লেনদেন আইডি, পরিমাণ এবং সমস্যার বিবরণ জানান। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
}


# Cashback/campaign complaints (classified as `other`) — case_type stays spec-legal,
# but the wording is promo-aware. Selected via context["text_variant"] == "promotional".
PROMO_TEXT = {
    "en": {
        "agent_summary": (
            "Customer reports a promotional/cashback concern tied to the campaign. "
            "No transaction dispute — verify campaign eligibility."
        ),
        "recommended_next_action": (
            "Check the customer's eligibility against the campaign terms and timing, "
            "then communicate the eligibility outcome through official channels."
        ),
        "customer_reply": (
            "Thank you for reaching out about the campaign. We have noted your cashback "
            "concern and our support team will review your eligibility and update you "
            "through official channels. Please do not share your PIN or OTP with anyone."
        ),
    },
    "bn": {
        "agent_summary": (
            "গ্রাহক ক্যাম্পেইন সংক্রান্ত একটি ক্যাশব্যাক সমস্যার কথা জানিয়েছেন। "
            "কোনো লেনদেন বিরোধ নয় — ক্যাম্পেইন যোগ্যতা যাচাই করুন।"
        ),
        "recommended_next_action": (
            "ক্যাম্পেইনের শর্ত ও সময় অনুযায়ী গ্রাহকের যোগ্যতা যাচাই করুন এবং "
            "অফিসিয়াল চ্যানেলে ফলাফল জানান।"
        ),
        "customer_reply": (
            "ক্যাম্পেইন সম্পর্কে যোগাযোগ করার জন্য ধন্যবাদ। আপনার ক্যাশব্যাক সংক্রান্ত "
            "বিষয়টি আমরা অবগত হয়েছি এবং আমাদের দল যোগ্যতা যাচাই করে অফিসিয়াল চ্যানেলে "
            "জানাবে। অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
}

# Used whenever no specific transaction could be identified (insufficient_data /
# ambiguous). Avoids leaking placeholders like "N/A" into a case-specific template.
NO_MATCH_TEXT = {
    "en": {
        "agent_summary": (
            "Customer reports an issue, but no single matching transaction could be "
            "confirmed from the provided history. More detail is needed to identify it."
        ),
        "recommended_next_action": (
            "Ask the customer for the transaction ID, exact amount, and approximate time, "
            "then locate the relevant transaction and proceed per policy."
        ),
        "customer_reply": (
            "Thank you for reaching out. To help you faster, please share the transaction "
            "ID, the amount involved, and a short description of what went wrong. "
            "Please do not share your PIN or OTP with anyone."
        ),
    },
    "bn": {
        "agent_summary": (
            "গ্রাহক একটি সমস্যার কথা জানিয়েছেন, তবে প্রদত্ত ইতিহাস থেকে নির্দিষ্ট কোনো "
            "লেনদেন শনাক্ত করা যায়নি। আরও তথ্য প্রয়োজন।"
        ),
        "recommended_next_action": (
            "গ্রাহকের কাছ থেকে লেনদেন আইডি, সঠিক পরিমাণ এবং আনুমানিক সময় জেনে নিন, "
            "তারপর সংশ্লিষ্ট লেনদেন শনাক্ত করে নীতি অনুযায়ী এগিয়ে যান।"
        ),
        "customer_reply": (
            "আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। আপনাকে দ্রুত সাহায্য করতে, অনুগ্রহ করে "
            "লেনদেন আইডি, পরিমাণ এবং সমস্যার সংক্ষিপ্ত বিবরণ জানান। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        ),
    },
}


def generate_text_fields(context: dict) -> dict:
    """Generate the three text fields using rule-based templates.

    Selection order:
      1. Promotional/cashback complaints -> promo-aware text (case_type stays `other`).
      2. No matched transaction          -> clean generic text (never leak placeholders).
      3. Otherwise                        -> the case-specific template with txn details.
    """
    case_type_str = context.get("case_type", "other")
    lang = "bn" if context.get("language") == "bn" else "en"

    # 1) Promotional / cashback
    if context.get("text_variant") == "promotional":
        return dict(PROMO_TEXT[lang])

    # 2) No specific transaction identified
    txn_id = context.get("relevant_transaction_id")
    txn_details = context.get("transaction_details") or {}
    if not (txn_id and txn_details):
        return dict(NO_MATCH_TEXT[lang])

    # 3) Case-specific template, with real transaction details
    try:
        case_type = CaseType(case_type_str) if isinstance(case_type_str, str) else case_type_str
    except ValueError:
        case_type = CaseType.other

    table = TEMPLATES_BN if lang == "bn" else TEMPLATES_EN
    templates = table.get(case_type) or table.get(CaseType.other) or TEMPLATES_EN[CaseType.other]

    amt = txn_details.get("amount")
    if isinstance(amt, (int, float)) and float(amt).is_integer():
        amt_str = str(int(amt))           # 5000.0 -> "5000"
    elif amt is not None:
        amt_str = str(amt)                # keep fractional amounts as-is
    else:
        amt_str = ""
    fmt = {
        "txn_id": txn_id,
        "amount": amt_str,
        "counterparty": txn_details.get("counterparty", ""),
    }

    result = {}
    for field in ("agent_summary", "recommended_next_action", "customer_reply"):
        template = templates.get(field, TEMPLATES_EN[CaseType.other][field])
        try:
            result[field] = template.format(**fmt)
        except (KeyError, IndexError):
            result[field] = template

    return result
