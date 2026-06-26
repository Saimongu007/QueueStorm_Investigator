"""Post-generation safety validator and prompt injection defense.

Every response passes through this layer before leaving the service.
If any check fails, the field is replaced with a hardcoded safe fallback.
"""

import re
import logging

logger = logging.getLogger(__name__)

# --- Credential safety (allowlist inversion) ---
#
# In this domain, EVERY legitimate mention of a credential is a warning
# ("do not share your PIN"). So instead of trying to enumerate every way to
# *ask* for one (which both false-positives on greedy patterns and misses
# phrasings like "send me your OTP"), we flag credentials by default and allow
# them ONLY inside a warning context — evaluated per sentence so a request in
# one sentence isn't masked by a warning in another.
CREDENTIAL_RE = re.compile(
    r"(pin|otp|password|passcode|one[\s-]?time password|card number|cvv|"
    r"পিন|ওটিপি|পাসওয়ার্ড)",
    re.IGNORECASE,
)
CREDENTIAL_WARNING_RE = re.compile(
    r"(do not share|don't share|never share|do not reveal|never reveal|"
    r"never ask|do not ask|do not give|don't give|do not provide|"
    r"do not disclose|without sharing|before sharing|do not enter|"
    r"শেয়ার করবেন না|চাই না|দেবেন না|শেয়ার করা উচিত নয়)",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_RE = re.compile(r"[.!?।\n]+")


def _has_credential_request(text: str) -> bool:
    """True if any sentence mentions a credential WITHOUT a warning context."""
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        if CREDENTIAL_RE.search(sentence) and not CREDENTIAL_WARNING_RE.search(sentence):
            return True
    return False


# Unauthorized refund/reversal patterns
FORBIDDEN_REFUND_PATTERNS = [
    r"we will refund",
    r"we('ll| will) (process|initiate|complete).*refund",
    r"we('ll| will) (refund|credit|reimburse|return)\b",
    r"you will (receive|get).*(refund|credit|reimburse)",
    r"we are refunding",
    r"refund has been.*processed",
    r"your money.*will be returned",
    r"account.*will be (unblocked|unlocked|restored)",
    r"will be reversed",
    r"we have (initiated|processed|completed).*(refund|reversal)",
    r"আপনার টাকা ফেরত দেওয়া হবে",
]

# Third-party contact patterns
FORBIDDEN_THIRD_PARTY_PATTERNS = [
    r"contact\s+(?!official|our|support|the merchant)\S+\s+at\s+\+?\d",
    r"visit\s+(?!our)\S+\s+website",
    r"call\s+\+880\d{10}",
]

# --- Safe fallback replies ---

SAFE_FALLBACK_REPLIES = {
    "en": (
        "We have received your concern and our support team will review it. "
        "Any eligible amount will be returned through official channels. "
        "Please do not share your PIN or OTP with anyone."
    ),
    "bn": (
        "আমরা আপনার অভিযোগ পেয়েছি। আমাদের সাপোর্ট টিম এটি পর্যালোচনা করবে। "
        "যোগ্য পরিমাণ অফিসিয়াল চ্যানেলে ফেরত দেওয়া হবে। "
        "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
    ),
    "mixed": (
        "We have received your concern and our support team will review it. "
        "Any eligible amount will be returned through official channels. "
        "Please do not share your PIN or OTP with anyone."
    ),
}

SAFE_FALLBACK_ACTION = (
    "Route to the appropriate department for review per standard policy."
)


def validate_customer_reply(text: str) -> tuple[bool, list[str]]:
    """Check customer_reply for safety violations.

    Returns (is_safe, list_of_violations).
    """
    violations = []
    text_lower = text.lower()

    if _has_credential_request(text):
        violations.append("credential_request: credential mentioned outside a warning context")

    for pattern in FORBIDDEN_REFUND_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(f"unauthorized_refund: matched '{pattern}'")

    for pattern in FORBIDDEN_THIRD_PARTY_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(f"third_party_contact: matched '{pattern}'")

    return len(violations) == 0, violations


def validate_recommended_action(text: str) -> tuple[bool, list[str]]:
    """Check recommended_next_action for unauthorized refund language."""
    violations = []
    text_lower = text.lower()

    for pattern in FORBIDDEN_REFUND_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(f"unauthorized_refund_in_action: matched '{pattern}'")

    return len(violations) == 0, violations


def get_safe_reply(language: str) -> str:
    """Return a hardcoded safe fallback reply for the given language."""
    return SAFE_FALLBACK_REPLIES.get(language, SAFE_FALLBACK_REPLIES["en"])


def get_safe_action() -> str:
    """Return a hardcoded safe fallback next action."""
    return SAFE_FALLBACK_ACTION


# --- Prompt injection defense ---

INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all|prior)\s+instructions?",
    r"you are now",
    r"forget your",
    r"new instructions?:",
    r"system prompt",
    r"reveal.*prompt",
    r"act as",
    r"\bDAN\b",
    r"jailbreak",
    r"do not follow",
    r"override",
    r"disregard.*(?:rules|instructions|guidelines)",
]


def sanitize_complaint(complaint: str) -> str:
    """Detect injection attempts and return a safe version for LLM.

    The original complaint is still used for rule-based classification
    (which doesn't interpret instructions).
    """
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, complaint, re.IGNORECASE):
            logger.warning("Prompt injection attempt detected in ticket")
            return "[COMPLAINT TEXT SANITIZED - POSSIBLE INJECTION ATTEMPT]"

    # Truncate very long complaints to prevent context stuffing
    return complaint[:2000]
