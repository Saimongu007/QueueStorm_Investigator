"""Classification regression tests — guards phishing precision.

Phishing must NOT trigger on a bare credential mention (that misroutes legitimate
payment/refund complaints to fraud_risk), but MUST trigger on social-engineering
reports even when no credential noun is present.
"""

import pytest
from app.rules import classify_case
from app.models import CaseType

P = CaseType.phishing_or_social_engineering


@pytest.mark.parametrize("text", [
    "I entered my PIN and the payment failed but money was deducted",
    "I changed my password and now want a refund for my purchase",
    "I forgot my OTP so the transfer did not go through",
])
def test_bare_credential_mention_is_not_phishing(text):
    """A credential noun without a social-engineering signal is NOT phishing."""
    assert classify_case(text, [], "en") != P


@pytest.mark.parametrize("text", [
    "Someone called me from bKash and asked for my OTP, said my account will be blocked",
    "someone called pretending to be from bKash and told me to install an app",
    "I got a fake SMS with a link claiming to be from bKash",
    "a fraudster called and tried to trick me into sharing my pin",
])
def test_social_engineering_is_phishing(text):
    """Scam phrasing or credential+social-signal co-occurrence IS phishing."""
    assert classify_case(text, [], "en") == P


def test_merchant_pretending_is_not_phishing():
    """'pretending' in a non-impersonation sense must not misfire."""
    text = "the merchant is pretending he never received my settlement"
    assert classify_case(text, [], "en") != P
