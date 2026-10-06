import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_response_text import checked_response_text

REASON = "Reviewed public explanation of the requested rights outcome"
TEXT = "Your private copy is available through the protected receipt during its validity."


@pytest.mark.parametrize(
    "suffix", [" https://example.test", " www.example.test", " a@example.test", " +34 612 345 678"]
)
def test_public_response_rejects_contact_details(suffix):
    with pytest.raises(ValidationError, match="Remove contact"):
        checked_response_text(REASON, TEXT + suffix, True)


@pytest.mark.parametrize(
    "reason,text,confirmed",
    [
        (None, TEXT, True),
        (REASON, {}, True),
        (REASON, TEXT, "yes"),
        (REASON, TEXT, 1),
        (REASON, TEXT, False),
        ("short", TEXT, True),
        (REASON, "short", True),
    ],
)
def test_malformed_response_is_a_controlled_validation_error(reason, text, confirmed):
    with pytest.raises(ValidationError, match="Motivated"):
        checked_response_text(reason, text, confirmed)


def test_reviewed_explanation_preserves_the_exact_text():
    assert checked_response_text(REASON, TEXT, True) == TEXT
