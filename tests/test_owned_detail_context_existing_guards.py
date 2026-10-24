"""Exercise existing user-facing guard controls with the integrated RR detail endpoint."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
import test_discovery as discovery_controls
import test_privacy_publication_holds as privacy_controls
from django.core import signing
from django.db import connections, transaction
from django.utils import timezone
from owned_detail_context import build_detail_context_prototype, patch_detail_view
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings import moderation_views
from apps.listings.models import Revision
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "scenario", ["localization_catalog", "production_provenance", "privacy_hold"]
)
def test_existing_controls_under_rr_detail(request, monkeypatch, settings, scenario):
    prototype = build_detail_context_prototype()
    with monkeypatch.context() as patch:
        patch_detail_view(patch, prototype)
        if scenario == "localization_catalog":
            client = request.getfixturevalue("directory")
            discovery_controls.test_public_detail_localizes_profile_and_selected_contacts(client)
        elif scenario == "production_provenance":
            client = request.getfixturevalue("directory")
            discovery_controls.test_simulation_provenance_survives_provider_switch_and_blocks_production(
                client, settings
            )
        else:
            privacy_controls.test_hold_removes_exposure_and_blocks_forced_status_and_manager_lifecycle(
                request, settings, monkeypatch
            )


def test_render_uses_same_snapshot_then_fresh_request_denies(request, monkeypatch):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    path = f"/en/listing/{person.listing.pk}/"
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, "timestamp", lambda self: stamp)
    reference = client.get(path)
    assert reference.status_code == 200
    prototype = build_detail_context_prototype()
    render = moderation_views.render
    committed = []

    def writer():
        try:
            with transaction.atomic():
                Revision.objects.filter(pk=revision.pk).update(
                    title="Synthetic committed after guard"
                )
                Photo.objects.filter(revision=revision).update(comparison_complete=False)
            return True
        finally:
            connections.close_all()

    def after_guard(*args, **kwargs):
        with ThreadPoolExecutor(max_workers=1) as pool:
            committed.append(pool.submit(writer).result(timeout=15))
        return render(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch_detail_view(patch, prototype)
        patch.setitem(prototype.__globals__, "render", after_guard)
        candidate = client.get(path)
    assert committed == [True]
    assert candidate.status_code == 200
    assert candidate.content == reference.content
    assert b"Synthetic committed after guard" not in candidate.content
    with monkeypatch.context() as patch:
        patch_detail_view(patch, prototype)
        assert client.get(path).status_code == 404


def test_expiry_clock_not_frozen_by_rr(request, monkeypatch):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    listing = person.listing
    now = timezone.now()
    type(listing).objects.filter(pk=listing.pk).update(expires_at=now + timedelta(seconds=1))
    clock = [now]
    monkeypatch.setattr(timezone, "now", lambda: clock[0])
    prototype = build_detail_context_prototype()
    native_guard = prototype.__globals__["publicly_visible"]
    called = []

    def after_hydration(*args, **kwargs):
        called.append(True)
        clock[0] = now + timedelta(seconds=2)
        return native_guard(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch_detail_view(patch, prototype)
        patch.setitem(prototype.__globals__, "publicly_visible", after_hydration)
        assert client.get(f"/es/listing/{listing.pk}/").status_code == 404
    assert called == [True]


def test_authenticated_render_keeps_session_middleware_outside_rr(request, monkeypatch):
    client = request.getfixturevalue("directory")
    client.force_login(User.objects.get(username="fixture-v1-visitor"))
    person = Person.objects.get(individual__username="fixture-v1-individual")
    prototype = build_detail_context_prototype()
    render = moderation_views.render
    authenticated = []

    def observed_render(request, *args, **kwargs):
        authenticated.append(request.user.is_authenticated)
        return render(request, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch_detail_view(patch, prototype)
        patch.setitem(prototype.__globals__, "render", observed_render)
        response = client.get(f"/en/listing/{person.listing.pk}/")
    assert response.status_code == 200 and authenticated == [True]
    assert b"Save private favorite" in response.content
    assert "_auth_user_id" in client.session
