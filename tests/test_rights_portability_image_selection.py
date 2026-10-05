"""Guided private image preparation preserves scalar and other binary selections."""

from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.mediafiles.models import Photo
from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsPortabilitySelection

pytestmark = pytest.mark.django_db(transaction=True)


def test_guided_binary_page_requires_current_token_and_preserves_other_choices(
    request, settings, monkeypatch
):
    original_ready = fixtures.ready

    def ready_with_history(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        person = result[-1]
        first = person.listing.revisions.first().photos.first()
        Photo.objects.create(
            revision=first.revision, blob=first.blob, position=1, removed_at=timezone.now()
        )
        return result

    monkeypatch.setattr(fixtures, "ready", ready_with_history)
    case, author, baseline, _, _, _, _ = fixtures.prepared_selection(
        request, settings, monkeypatch, False
    )
    initial = unseal(baseline.encrypted_selection)
    client = Client()
    client.force_login(author)
    session = client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    path = reverse("rights_portability_images", args=[case.pk])
    assert client.get(path).status_code == 200
    assert b"data:image/webp;base64," not in client.get(path).content
    before = RightsAction.objects.filter(request=case).count()
    protected = Client(enforce_csrf_checks=True)
    protected.cookies = client.cookies.copy()
    assert protected.get(path).status_code == 200
    assert protected.post(path, {}).status_code == 403
    assert RightsAction.objects.filter(request=case).count() == before

    def catalog(number):
        result = client.post(
            path,
            {
                "operation": "catalog",
                "key": uuid4(),
                "version": case.version,
                "review": baseline.assessment_review_id,
                "revision_number": 1,
                "image_number": number,
                "purpose": "Inspect synthetic image content for guided eligibility",
            },
        )
        assert result.status_code == 200 and b"data:image/webp;base64," in result.content
        form = result.context["save_form"]
        facts = result.context["facts_form"]
        return {
            "operation": "save",
            "key": uuid4(),
            "token": form.initial["token"],
            "include": "on",
            "reason": "Preserve other choices while changing this image",
            "image-path": facts.initial["path"],
            "image-basis": "contract",
            "image-origin": "provided",
            "image-automated": "yes",
            "image-subject_related": "yes",
            "image-third_party_reviewed": "yes",
            "image-reason": "Synthetic reviewed binary provenance",
            "image-evidence": "PRIVATE_GUIDED_BINARY_ELIGIBILITY_EVIDENCE",
        }

    first = catalog(1)
    before = RightsAction.objects.count()
    assert client.post(path, {**first, "image-origin": "third_party"}).status_code == 400
    assert client.post(path, {**first, "image-path": "/images/99/photo"}).status_code == 409
    assert RightsAction.objects.count() == before
    result = client.post(path, first)
    assert (
        result.status_code == 200
        and b"PRIVATE_GUIDED_BINARY_ELIGIBILITY_EVIDENCE" not in result.content
    )
    assert client.post(path, first).status_code == 200
    row = (
        RightsPortabilitySelection.objects.filter(request=case, actor=author)
        .order_by("-version")
        .first()
    )
    first_body = unseal(row.encrypted_selection)
    assert len(first_body["images"]) == 1
    assert first_body["selection"] == initial["selection"]
    assert first_body["field_evidence"] == initial["field_evidence"]
    second = catalog(2)
    assert client.post(path, second).status_code == 200
    row = (
        RightsPortabilitySelection.objects.filter(request=case, actor=author)
        .order_by("-version")
        .first()
    )
    both = unseal(row.encrypted_selection)
    assert len(both["images"]) == 2 and both["images"][0] == first_body["images"][0]
    assert client.post(path, {**first, "key": uuid4()}).status_code == 409
    removed = catalog(1)
    removed.pop("include")
    assert client.post(path, removed).status_code == 200
    row = (
        RightsPortabilitySelection.objects.filter(request=case, actor=author)
        .order_by("-version")
        .first()
    )
    final = unseal(row.encrypted_selection)
    assert final["images"] == [both["images"][1]]
    assert final["selection"] == initial["selection"]
    assert b"PRIVATE_GUIDED_BINARY_ELIGIBILITY_EVIDENCE" not in client.get(path).content
