"""Unconfigured adapters must fail before simulator challenge/mail side effects."""

import pytest
from django.core import mail
from test_verification import account, ready_accounts  # noqa: F401

from apps.core.models import Person

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("provider", ["future-provider", "", "simulator "])
@pytest.mark.parametrize("method", ["get", "post"])
def test_unintegrated_phone_start_preserves_existing_challenge(
    request, settings, provider, method,
):
    request.getfixturevalue("ready_accounts")
    settings.PRODUCTION = False
    settings.VERIFICATION_PROVIDER = "simulator"
    user, client = account("synthetic-adapter-gate")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic")
    path = f"/es/person/{person.pk}/phone/"
    first = client.post(path, {"phone": "600123876"})
    assert first.status_code == 302
    original = person.phonechallenge_set.get()
    mail_count = len(mail.outbox)
    settings.VERIFICATION_PROVIDER = provider
    response = getattr(client, method)(path, {"phone": "600123877"})
    original.refresh_from_db()
    person.refresh_from_db()
    assert (response.status_code, person.phonechallenge_set.count(), original.used_at,
            len(mail.outbox), person.phone_claim_id) == (503, 1, None, mail_count, None)
