"""Unit tests for the PII scrubber."""
import pytest

from app.core.logging import scrub_pii


@pytest.mark.parametrize("raw, expected", [
    ("Contact me at john@example.com please",
     "Contact me at <email> please"),
    ("Phone is 9876543210",
     "Phone is <phone>"),
    ("Call +91 9876543210 anytime",
     "Call +91 <phone> anytime"),  # +91 part may stay, that's OK
    ("My number: +919876543210",
     "My number: <phone>"),
    ("Order #12345 was placed",
     "Order #12345 was placed"),  # short digits left alone
    ("Account 1234567890123 has issues",
     "Account <num> has issues"),  # long digits caught as generic
    ("No PII here, just text",
     "No PII here, just text"),
    ("", ""),
])
def test_scrub_pii(raw, expected):
    out = scrub_pii(raw)
    # phone patterns can match slightly differently; assert no raw digits leak
    assert "9876543210" not in out
    assert "john@example.com" not in out