"""Expose original agency fixture HTTP to the opt-in call-phase observer."""

import pytest
from test_agency_publication import (
    agency_publication,  # noqa: F401
    photo_environment,  # noqa: F401
    ready_accounts,  # noqa: F401
)
from test_agency_publication import (
    test_agency_two_people_shared_phone_editor_publication_and_revoke as publication_oracle,
)
from test_lifecycle import (
    directory,  # noqa: F401
)
from test_lifecycle import (
    test_agency_editor_assignment_mfa_and_revocation as lifecycle_oracle,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_agency_publication_authority_reference(request):
    """Keep every original setup/assertion; include setup requests in observation."""
    publication_oracle(request.getfixturevalue("agency_publication"))


def test_agency_editor_revocation_reference(request):
    """Reuse the complete original MFA/assignment/revocation oracle."""
    lifecycle_oracle(request)
