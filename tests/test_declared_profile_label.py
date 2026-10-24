"""Explicit public display option preserves type, legacy corrections and scoped erasure."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from test_discovery import directory  # noqa: F401
from test_drafts import details, scenario  # noqa: F401
from test_erasure_execution import REASON, plan_fixture
from test_erasure_final import material
from test_listing_moderation import decision, pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_recovery_apply import stored_receipt
from test_submissions import prepared  # noqa: F401

from apps.core.models import Person
from apps.listings.publication_state import refresh_all
from apps.safety import rectification_details
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryOutbox
from apps.safety.recovery_apply import reconcile

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("selected", [False, True])
def test_declared_label_is_optional_and_does_not_replace_profile_type(request, selected):
    _, _, client, revision = request.getfixturevalue("prepared")
    data = details(revision)
    if selected:
        data["show_trans_label"] = "on"
    assert client.post(f"/es/draft/{revision.pk}/1/", data).status_code == 302
    revision.refresh_from_db()
    assert revision.profile_type == "woman" and revision.show_trans_label is selected
    person, _, current, _, reviewer = request.getfixturevalue("pending")
    assert reviewer.post(f"/es/moderation/listings/{current.pk}/", decision(current)).status_code == 302
    for language, label in [("es", "Mujer"), ("en", "Woman")]:
        response = client.get(f"/{language}/listing/{person.listing.pk}/")
        assert response.status_code == 200
        assert response.context["public"]["profile_type"] == label
        assert response.context["public"]["trans_label"] is selected
        assert (" · Trans</p>" in response.content.decode()) is selected


def test_label_filter_keeps_declared_woman_and_unknown_types_distinct(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    assert revision.profile_type == "woman" and not revision.show_trans_label
    assert client.get("/es/", {"profile": ["trans"]}).context["page"].paginator.count == 0
    revision.show_trans_label = True
    revision.save(update_fields=["show_trans_label"])
    for refresh in [False, True]:
        if refresh:
            refresh_all()
        assert client.get("/es/", {"profile": ["woman"]}).context["page"].paginator.count == 2
        result = client.get("/es/", {"profile": ["trans"]})
        assert [row.pk for row in result.context["page"].object_list] == [person.listing.pk]
    revision.profile_type = ""
    revision.save(update_fields=["profile_type"])
    assert client.get("/es/", {"profile": ["woman"]}).context["page"].paginator.count == 1
    assert client.get("/es/", {"profile": ["trans"]}).context["page"].paginator.count == 1


def test_legacy_details_do_not_implicitly_select_or_clear_new_display_option(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    revision.show_trans_label = True
    revision.save(update_fields=["show_trans_label"])
    current = rectification_details.source(revision)
    assert rectification_details.validate(current)["show_trans_label"] is True
    legacy = {key: value for key, value in current.items() if key != "show_trans_label"}
    assert "show_trans_label" not in rectification_details.validate(legacy)
    assert "Show trans label" not in rectification_details.display(legacy, "en")
    with pytest.raises(ValidationError):
        rectification_details.validate({**current, "show_trans_label": "yes"})
    revision.refresh_from_db()
    assert revision.show_trans_label is True


def test_publication_erasure_and_recovery_clear_label_without_touching_peer(
    request, settings, monkeypatch, tmp_path
):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    source = person.listing.approved_revision
    source.show_trans_label = True
    source.save(update_fields=["show_trans_label"])
    peer = Person.objects.get(individual__username="fixture-v1-individual")
    peer_revision = peer.listing.approved_revision
    peer_revision.show_trans_label = True
    peer_revision.save(update_fields=["show_trans_label"])
    peer_before = list(peer.listing.revisions.values())
    selected = ["profile", "publication"]
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=selected
    )
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, selected, REASON, True)
    assert not person.listing.revisions.filter(show_trans_label=True).exists()
    case.refresh_from_db()
    assert "publication" in material(case, execution)["completed_purposes"]
    source.refresh_from_db()
    source.show_trans_label = True  # A restored stale value must remain outstanding until reconciled.
    source.save(update_fields=["show_trans_label"])
    assert "publication" in material(case, execution)["pending_execution_purposes"]
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)["applied"] == 1
    assert not person.listing.revisions.filter(show_trans_label=True).exists()
    assert list(peer.listing.revisions.values()) == peer_before


def test_schema_rollback_cannot_discard_a_selected_label(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    revision.show_trans_label = True
    revision.save(update_fields=["show_trans_label"])
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    target = [node for node in latest if node[0] != "listings"] + [
        ("listings", "0024_optional_profile_type")
    ]
    try:
        with pytest.raises(IrreversibleError, match="must be preserved"):
            executor.migrate(target)
        revision.refresh_from_db()
        assert revision.show_trans_label and revision.profile_type == "woman"
    finally:
        MigrationExecutor(connection).migrate(latest)
