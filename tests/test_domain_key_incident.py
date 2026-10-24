"""Revoking an explicit domain key must not revive old channels or rewrite cases."""

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth.models import Permission
from django.test import Client
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_reports import payload as report_payload
from test_rights_intake import data as rights_payload

from apps.listings.publication_state import rules_version
from apps.safety.crypto import unseal
from apps.safety.models import Report, ReportAccess, RightsAccess, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("domain", ["report", "rights"])
@pytest.mark.parametrize("framework_fallback", [False, True])
def test_explicit_domain_key_revocation_preserves_evidence_but_closes_old_channels(
    request, settings, record_property, domain, framework_fallback,
):
    framework_key = "synthetic-unaffected-framework-" + "s" * 64
    original_domain = "synthetic-domain-before-incident-" + "a" * 64
    settings.SECRET_KEY = framework_key
    settings.SECRET_KEY_FALLBACKS = []
    settings.SAFETY_HMAC_KEY = original_domain
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ""
    request.getfixturevalue("directory")
    client = Client()
    form, model, access = (
        (report_payload, Report, ReportAccess) if domain == "report"
        else (rights_payload, RightsRequest, RightsAccess)
    )
    path = "/en/safety/" + ("report/" if domain == "report" else "rights/")
    private_marker = "Private synthetic incident evidence requires a fresh audited purpose."
    data = form(client, explanation=private_marker)
    submitted = client.post(path, data)
    assert submitted.status_code == 302
    case = model.objects.get()
    original = model.objects.filter(pk=case.pk).values().get()
    plaintext = unseal(original["encrypted_payload"])
    for language in ("es", "en"):
        assert client.get(submitted.url.replace("/en/", "/" + language + "/", 1)).status_code == 200
    user, staff = reviewer()
    if domain == "rights":
        user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    inspection = "/en/moderation/" + ("reports/" if domain == "report" else "rights/") + str(case.pk) + "/"
    assert staff.post(inspection, {"purpose": "Inspect original evidence before domain key incident"}).status_code == 200
    assert access.objects.count() == 1
    original_access = list(access.objects.order_by("pk").values())
    old_rules = rules_version()

    settings.SAFETY_HMAC_KEY = "synthetic-domain-after-incident-" + "b" * 64
    # Any retained Django key belongs to an unaffected family. Never keep the
    # compromised domain value as an accepted framework fallback.
    settings.SECRET_KEY_FALLBACKS = ["synthetic-unaffected-prior-framework-" + "p" * 64] if framework_fallback else []
    assert settings.SECRET_KEY == framework_key and original_domain not in settings.SECRET_KEY_FALLBACKS
    assert rules_version() != old_rules
    for language in ("es", "en"):
        assert client.get(submitted.url.replace("/en/", "/" + language + "/", 1)).status_code == 404
    assert client.post(path, data).status_code == 409
    assert model.objects.count() == 1
    assert model.objects.filter(pk=case.pk).values().get() == original
    assert list(access.objects.order_by("pk").values()) == original_access
    fresh = client.post(path, form(client))
    assert fresh.status_code == 302 and client.get(fresh.url).status_code == 200
    assert model.objects.count() == 2

    # The unaffected staff session remains valid. Reading again requires a new
    # explicit purpose and a new audit record, not reuse of an earlier access.
    metadata = staff.get(inspection)
    assert metadata.status_code == 200 and access.objects.count() == 1
    assert private_marker.encode() not in metadata.content
    viewed = staff.post(inspection, {"purpose": "Inspect original evidence anew after domain key revocation"})
    assert viewed.status_code == 200 and viewed["Cache-Control"] == "private, no-store"
    assert private_marker.encode() in viewed.content
    assert access.objects.count() == 2
    assert list(access.objects.order_by("pk").values())[:1] == original_access
    assert model.objects.filter(pk=case.pk).values().get() == original
    assert unseal(model.objects.get(pk=case.pk).encrypted_payload) == plaintext
    for name in (
        "explicit_domain_rotation_revokes_original_receipts_es_en",
        "original_submission_conflicts_without_rebinding",
        "fresh_intake_after_rotation_remains_available",
        "old_ciphertext_rows_deadlines_and_access_record_unchanged",
        "new_staff_read_requires_new_purpose_and_audit",
        "compromised_domain_key_not_retained_as_framework_fallback",
        "publication_rules_version_invalidated",
    ):
        record_property(name, True)
