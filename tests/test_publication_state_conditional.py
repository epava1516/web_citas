"""Independent reproduction of conditional invalidation; synthetic persisted ledger."""

import json
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from test_discovery import directory, multipage_directory  # noqa: F401
from test_photo_disposition_authority import ledger
from test_photos import photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings import moderation, publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.safety.models import (
    RightsPhotoReintroduction,
    RightsPhotoReintroductionDecision,
    RightsRectificationPhotoDisposition,
)
from apps.safety.photo_reintroduction_review import decide, inspect

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("dependency", ["decision", "proof"])
def test_conditional_decision_write_preserves_exact_count(
    request, monkeypatch, record_property, dependency
):
    client = request.getfixturevalue("multipage_directory")
    while publication_state.refresh(500):
        pass
    before = client.get("/en/", {"q": "pagination"})
    assert before.status_code == 200 and before.context["page"].paginator.count == 25
    second = client.get("/en/", {"q": "pagination", "page": "2"})
    target = second.context["page"].object_list[0]
    execution = ledger(target.person)
    execution.corrected_revision = target.approved_revision
    execution.save(update_fields=["corrected_revision"])
    execution.proof.status = "passed"
    execution.proof.save(update_fields=["status"])
    photo = target.approved_revision.photos.first()
    disposition = RightsRectificationPhotoDisposition.objects.create(
        execution=execution, source_photo=photo, blob=photo.blob, outcome="withdrawn"
    )
    candidate = RightsPhotoReintroduction.objects.create(
        photo=photo, uploaded_blob=photo.blob, disposition=disposition, method="sha256"
    )
    reviewer = User.objects.create_user(
        username="synthetic-independent-mod05-review", mfa_enabled=True
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="review_photo_reintroduction"))
    read = inspect(
        reviewer, candidate.pk, uuid4(), 1, "Inspect synthetic current photo reuse permission"
    )
    decision = decide(
        reviewer,
        candidate.pk,
        read.pk,
        uuid4(),
        1,
        "authorize",
        "Synthetic independent current image permission assessment",
        "synthetic-reviewed-ref",
    )
    import sys
    from pathlib import Path

    from django.conf import settings

    root = Path(settings.BASE_DIR)
    executed = set()

    def tracer(frame, event, arg):
        name = frame.f_code.co_filename
        if event == "call" and name.startswith(str(root / "apps")):
            executed.add(str(Path(name).relative_to(root)))

    sys.setprofile(tracer)
    try:
        visible = moderation.publicly_visible(Listing.objects.get(pk=target.pk))
    finally:
        sys.setprofile(None)
    assert visible
    missing = sorted(executed - set(publication_state.RULE_SOURCES))
    record_property(
        "conditional_rule_sources", json.dumps({"executed": sorted(executed), "missing": missing})
    )
    assert not missing, missing
    while publication_state.refresh(500):
        pass
    assert not PublicationDirty.objects.filter(listing_id=target.pk).exists()
    # A write on a table actually read by the rule. QuerySet.update deliberately
    # bypasses signals, as MOD05 database invalidation promises to support.
    reports = []
    for dependency in [dependency]:
        RightsPhotoReintroductionDecision.objects.filter(pk=decision.pk).update(
            outcome="maintain" if dependency == "decision" else "authorize"
        )
        if dependency == "proof":
            type(execution.proof).objects.filter(pk=execution.proof_id).update(status="failed")
        assert PublicationDirty.objects.filter(listing_id=target.pk).exists()
        target = Listing.objects.get(pk=target.pk)
        assert not moderation.publicly_visible(target)
        stored = client.get("/en/", {"q": "pagination"})
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
            native = client.get("/en/", {"q": "pagination"})
        observed = {
            "dependency": dependency,
            "stored_count": stored.context["page"].paginator.count,
            "native_count": native.context["page"].paginator.count,
            "route": stored.wsgi_request._publication_route,
            "target_dirty": PublicationDirty.objects.filter(listing_id=target.pk).exists(),
            "target_off_first_page": target.pk
            not in [r.pk for r in stored.context["page"].object_list],
            "native_target_visible": False,
        }
        assert stored.content == native.content
        assert stored.context["page"].paginator.count == 24
        for language in ["es", "en"]:
            for page in ["1", "2"]:
                params = {"q": "pagination", "page": page}
                current = client.get(f"/{language}/", params)
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
                    oracle = client.get(f"/{language}/", params)
                assert current.status_code == oracle.status_code
                assert current.content == oracle.content
        reports.append(observed)
    record_property("conditional_dependency", json.dumps(reports))
    assert all(r["stored_count"] == r["native_count"] for r in reports), reports


def test_rules_version_changes_with_fingerprint_key(settings):
    publication_state.rules_version.cache_clear()
    before = publication_state.rules_version()
    settings.SECRET_KEY = "synthetic-mod05-rotated-fingerprint-key"
    publication_state.rules_version.cache_clear()
    try:
        assert publication_state.rules_version() != before
    finally:
        publication_state.rules_version.cache_clear()
