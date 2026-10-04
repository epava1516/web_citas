import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.utils import timezone
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data

from apps.safety.models import RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


def test_representation_is_prioritized_without_resetting_deadline_or_hiding_overdue(request):
    request.getfixturevalue("directory")
    client = Client()
    client.post("/en/safety/rights/", data(client, kind="access"))
    normal = RightsRequest.objects.get()
    RightsRequest.objects.filter(pk=normal.pk).update(
        initial_due_at=timezone.now() - timedelta(days=1)
    )
    submitted = data(client, kind="representation")
    response = client.post("/en/safety/rights/", submitted)
    represented = RightsRequest.objects.get(kind="representation")
    due = represented.initial_due_at
    assert represented.priority == 0 and represented.status == "received"
    assert client.post("/en/safety/rights/", submitted).url == response.url
    represented.refresh_from_db()
    assert represented.initial_due_at == due
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    response = staff.get("/en/moderation/rights/")
    assert [item.pk for item in response.context["cases"]] == [represented.pk, normal.pk]
    assert b"Priority representation review" in response.content
    assert b"Internal target overdue" in response.content
    assert b"rights-private@example.invalid" not in response.content


def test_existing_representation_migration_preserves_original_deadline_and_payload():
    old = [("safety", "0007_rightsrequest_rightsaccess")]
    # Reversing safety also reverses dependent migrations in other applications.
    # Restore the complete original graph so subsequent tests keep their schema.
    current = MigrationExecutor(connection).loader.graph.leaf_nodes()
    tables_before = set(connection.introspection.table_names())
    executor = MigrationExecutor(connection)
    executor.migrate(old)
    try:
        model = executor.loader.project_state(old).apps.get_model("safety", "RightsRequest")
        now = timezone.now()
        due = now + timedelta(days=29)
        row = model.objects.create(
            submission_key=uuid.uuid4(),
            receipt_digest="a" * 64,
            payload_digest="b" * 64,
            encrypted_payload="synthetic historical ciphertext preserved verbatim",
            kind="representation",
            received_at=now,
            initial_due_at=due,
            receipt_expires_at=now + timedelta(days=180),
        )
        executor = MigrationExecutor(connection)
        executor.migrate(current)
        row = RightsRequest.objects.get(pk=row.pk)
        assert row.priority == 0 and row.initial_due_at == due
        assert row.received_at == now
        assert row.encrypted_payload == "synthetic historical ciphertext preserved verbatim"
    finally:
        MigrationExecutor(connection).migrate(current)
        assert set(connection.introspection.table_names()) == tables_before
