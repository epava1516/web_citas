"""Indirect conflict readers survive edge changes, history and concurrent refresh."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from threading import Event
from uuid import uuid4

import pytest
from django.db import connections, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photo_disposition_authority import ledger
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision
from apps.listings.moderation import publicly_visible
from apps.mediafiles.models import Match, Photo
from apps.safety.models import RightsAction, RightsRectificationPhotoUpload
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def setup(request, monkeypatch, *, three=False, orientation=0):
    client = request.getfixturevalue("directory")
    from apps.listings.tasks import refresh_publication_state

    monkeypatch.setattr(refresh_publication_state, "delay", lambda: None)
    if three:
        populate(3)
    rows = list(Listing.objects.filter(status="published").order_by("pk")[: 3 if three else 2])
    assert len(rows) == (3 if three else 2)
    photos = [row.approved_revision.photos.filter(removed_at__isnull=True).first() for row in rows]
    match = Match.objects.create(
        photo=photos[orientation],
        candidate=photos[1 - orientation],
        method="sha256",
        decision="conflict",
        resolved_at=timezone.now(),
    )
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    return client, rows, photos, match


def equivalent(client, monkeypatch, target, visible):
    assert publicly_visible(Listing.objects.get(pk=target.pk)) is visible
    assert PublicationDirty.objects.filter(listing_id=target.pk).exists()
    for language in ("es", "en"):
        actual = client.get("/" + language + "/")
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
            native = client.get("/" + language + "/")
        assert actual.status_code == native.status_code == 200
        assert actual.content == native.content
        assert (target.pk in [r.pk for r in actual.context["page"]]) is visible


@pytest.mark.parametrize("orientation", [0, 1])
def test_photo_delete_marks_surviving_match_reader(request, monkeypatch, orientation):
    client, rows, photos, _ = setup(request, monkeypatch, orientation=orientation)
    photos[0].delete()
    equivalent(client, monkeypatch, rows[1], True)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    assert PublicationState.objects.get(listing_id=rows[1].pk).eligible


@pytest.mark.parametrize("orientation", [0, 1])
def test_photo_move_marks_old_new_and_opposite_owners(request, monkeypatch, orientation):
    client, rows, photos, _ = setup(request, monkeypatch, three=True, orientation=orientation)
    stage = Revision.objects.create(
        listing=rows[2], manager_version=rows[2].person.manager_version, status="rights-stage"
    )
    publication_state.refresh_all()
    Photo.objects.filter(pk=photos[0].pk).update(revision=stage)
    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) >= {
        r.pk for r in rows
    }
    equivalent(client, monkeypatch, rows[1], True)


def test_match_endpoint_move_keeps_old_and_new_readers_exact(request, monkeypatch):
    client, rows, photos, match = setup(request, monkeypatch, three=True)
    Match.objects.filter(pk=match.pk).update(candidate=photos[2])
    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) >= {
        r.pk for r in rows
    }
    equivalent(client, monkeypatch, rows[1], True)
    equivalent(client, monkeypatch, rows[2], False)


def test_fanout_is_one_hop_preserves_age_rolls_back_and_drains(request, monkeypatch):
    _, rows, photos, _ = setup(request, monkeypatch, three=True)
    Match.objects.create(photo=photos[1], candidate=photos[2], method="sha256", decision="conflict")
    publication_state.refresh_all()
    publication_state.mark([rows[0].pk])
    before = {r.listing_id: (r.generation, r.marked_at) for r in PublicationDirty.objects.all()}
    assert set(before) == {r.pk for r in rows[:2]}
    publication_state.mark([rows[0].pk])
    current = {r.listing_id: (r.generation, r.marked_at) for r in PublicationDirty.objects.all()}
    assert set(current) == set(before)
    assert all(current[k][0] > before[k][0] and current[k][1] == before[k][1] for k in before)

    class Rollback(Exception):
        pass

    with pytest.raises(Rollback), transaction.atomic():
        publication_state.mark([rows[2].pk])
        assert PublicationDirty.objects.filter(listing_id=rows[2].pk).exists()
        raise Rollback
    assert {
        r.listing_id: (r.generation, r.marked_at) for r in PublicationDirty.objects.all()
    } == current
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()


def test_history_create_change_delete_invalidates_opposite_reader(request, monkeypatch):
    client, rows, _, _ = setup(request, monkeypatch)
    execution = ledger(rows[0].person)  # Synthetic valid-FK ledger, not human approval evidence.
    equivalent(client, monkeypatch, rows[1], True)
    publication_state.refresh_all()
    type(execution).objects.filter(pk=execution.pk).update(
        corrected_revision_id=rows[0].approved_revision_id
    )
    equivalent(client, monkeypatch, rows[1], False)
    publication_state.refresh_all()
    type(execution).objects.filter(pk=execution.pk).update(corrected_revision=None)
    equivalent(client, monkeypatch, rows[1], True)
    publication_state.refresh_all()
    execution.delete()
    equivalent(client, monkeypatch, rows[1], False)


def test_rights_upload_relation_invalidates_opposite_reader(request, monkeypatch):
    client, rows, photos, _ = setup(request, monkeypatch)
    execution = ledger(rows[0].person)
    type(execution).objects.filter(pk=execution.pk).update(
        corrected_revision_id=rows[0].approved_revision_id
    )
    publication_state.refresh_all()
    action = RightsAction.objects.create(
        key=uuid4(),
        request=execution.action.request,
        actor=rows[0].person.subject,
        expected_version=1,
        operation="rectify_upload",
        encrypted_reason="synthetic",
    )
    upload = RightsRectificationPhotoUpload.objects.create(
        action=action,
        proof=execution.proof,
        photo=photos[0],
        source_digest="0" * 64,
        person_rights_version=rows[0].person.rights_version,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    equivalent(client, monkeypatch, rows[1], True)
    publication_state.refresh_all()
    upload.delete()
    equivalent(client, monkeypatch, rows[1], False)


def test_counterpart_generation_survives_observed_refresh_wait(request, monkeypatch):
    client, rows, photos, _ = setup(request, monkeypatch)
    target = rows[1]
    publication_state.mark([target.pk])
    before = PublicationDirty.objects.get(listing_id=target.pk).generation
    ready, release = Event(), Event()
    holder, waiter = Queue(), Queue()
    original = publication_state.expected_states

    def slow(ids, version):
        result = original(ids, version)
        assert target.pk in result
        ready.set()
        assert release.wait(10)
        return result

    def refresh():
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder.put(cursor.fetchone()[0])
            return publication_state.refresh(10)
        finally:
            connections.close_all()

    def write():
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                waiter.put(cursor.fetchone()[0])
            return Photo.objects.filter(pk=photos[0].pk).update(removed_at=timezone.now())
        finally:
            connections.close_all()

    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "expected_states", slow)
        with ThreadPoolExecutor(max_workers=2) as pool:
            refreshing = pool.submit(refresh)
            try:
                assert ready.wait(10)
                writing = pool.submit(write)
                observe_blocked(waiter.get(timeout=5), holder.get(timeout=5))
            finally:
                release.set()
            assert refreshing.result(timeout=15) > 0
            assert writing.result(timeout=15) == 1
    assert PublicationDirty.objects.get(listing_id=target.pk).generation > before
    equivalent(client, monkeypatch, target, True)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    assert PublicationState.objects.get(listing_id=target.pk).eligible


def test_upgrade_invalidates_preexisting_negative_counterpart_state(request, monkeypatch):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    client, rows, photos, _ = setup(request, monkeypatch)
    old = [("listings", "0019_publicationstate_public_read_projection")]
    new = [("listings", "0020_publication_match_counterparts")]
    leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
    try:
        MigrationExecutor(connection).migrate(old)
        publication_state.refresh_all()
        Photo.objects.filter(pk=photos[0].pk).update(removed_at=timezone.now())
        assert not PublicationDirty.objects.filter(listing_id=rows[1].pk).exists()
        assert not PublicationState.objects.get(listing_id=rows[1].pk).eligible
        assert publicly_visible(Listing.objects.get(pk=rows[1].pk))
        old_page = client.get("/en/")
        assert rows[1].pk not in [r.pk for r in old_page.context["page"]]
        MigrationExecutor(connection).migrate(new)
        equivalent(client, monkeypatch, rows[1], True)
        publication_state.refresh_all()
        assert PublicationState.objects.get(listing_id=rows[1].pk).eligible
        assert not PublicationDirty.objects.exists()
    finally:
        MigrationExecutor(connection).migrate(leaves)


@pytest.mark.parametrize("orientation", [0, 1])
def test_revision_delete_marks_surviving_match_reader(request, monkeypatch, orientation):
    from django.db.models.deletion import ProtectedError

    client, rows, photos, match = setup(request, monkeypatch, orientation=orientation)
    approved_id = rows[0].approved_revision_id
    with pytest.raises(ProtectedError):
        Revision.objects.get(pk=approved_id).delete()
    assert Listing.objects.get(pk=rows[0].pk).approved_revision_id == approved_id
    assert not PublicationDirty.objects.exists()
    draft = Revision.objects.create(
        listing=rows[0], manager_version=rows[0].person.manager_version
    )
    draft_photo = Photo.objects.create(
        revision=draft, blob=photos[0].blob, comparison_complete=True
    )
    Match.objects.filter(pk=match.pk).update(
        **{("photo" if orientation == 0 else "candidate"): draft_photo}
    )
    publication_state.refresh_all()
    assert not publicly_visible(Listing.objects.get(pk=rows[1].pk))
    draft.delete()
    equivalent(client, monkeypatch, rows[1], True)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()


def test_revision_move_invalidates_history_reader_and_both_owners(request, monkeypatch):
    client, rows, _, _ = setup(request, monkeypatch, three=True)
    ledger(rows[0].person)
    publication_state.refresh_all()
    assert PublicationState.objects.get(listing_id=rows[1].pk).eligible
    # A raw FK move must not keep a cached classification from the former owner.
    Revision.objects.filter(pk=rows[0].approved_revision_id).update(listing=rows[2])
    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) >= {
        r.pk for r in rows
    }
    equivalent(client, monkeypatch, rows[1], False)


def test_concurrent_opposite_photo_writes_drain_without_losing_marks(request, monkeypatch):
    from threading import Barrier

    _, rows, photos, _ = setup(request, monkeypatch)
    start = Barrier(2)

    def write(photo_id):
        try:
            with transaction.atomic():
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '5s'")
                start.wait(timeout=5)
                return Photo.objects.filter(pk=photo_id).update(removed_at=timezone.now())
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(write, photo.pk) for photo in photos]
        assert [future.result(timeout=15) for future in futures] == [1, 1]
    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) >= {
        row.pk for row in rows
    }
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    assert all(not publicly_visible(Listing.objects.get(pk=row.pk)) for row in rows)
    assert not PublicationState.objects.filter(listing_id__in=[r.pk for r in rows], eligible=True).exists()
