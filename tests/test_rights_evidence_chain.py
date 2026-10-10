"""PostgreSQL runtime-role enforcement, not synthetic guards or head-only acceptance."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, close_old_connections, connection, connections, transaction
from django.utils import timezone
from psycopg import sql

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Blob, Photo
from apps.safety.evidence_chain import (
    backfill_missing,
    configure_role,
    record_tombstone,
    validate_chain,
)
from apps.safety.evidence_chain_sql_v1 import EVENT, HEAD, TABLES
from apps.safety.models import (
    RightsAction,
    RightsEvidenceEvent,
    RightsEvidenceHead,
    RightsPortabilityAssessment,
    RightsPortabilityCoverage,
    RightsPortabilityCoverageRead,
    RightsPortabilityCoverageReview,
    RightsPortabilityImageRead,
    RightsPortabilityRead,
    RightsPortabilityReview,
    RightsPortabilitySelection,
    RightsPortabilitySelectionRead,
    RightsPortabilitySelectionReview,
    RightsProof,
    RightsRequest,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def base():
    now = timezone.now()
    user = User.objects.create(username="synthetic-chain-owner")
    person = Person.objects.create(individual=user)
    case = RightsRequest.objects.create(
        submission_key=uuid4(),
        kind="portability",
        receipt_digest="a" * 64,
        payload_digest="b" * 64,
        encrypted_payload="synthetic",
        actor=user,
        account_subject=user,
        received_at=now,
        initial_due_at=now,
        receipt_expires_at=now,
    )
    proof = RightsProof.objects.create(
        key=uuid4(),
        request=case,
        account_subject=user,
        initiated_by=user,
        case_version=1,
        scope="account",
        channel_digest="a" * 64,
        provider="simulator",
        procedure="synthetic",
        payload_digest="b" * 64,
        encrypted_reason="synthetic",
        expires_at=now,
    )

    def action():
        return RightsAction.objects.create(
            key=uuid4(),
            request=case,
            actor=user,
            expected_version=1,
            operation="synthetic",
            payload_digest="c" * 64,
            encrypted_reason="synthetic",
        )

    common = dict(
        proof=proof, source_digest="d" * 64, original_session_version=1, original_mfa_version=1
    )
    assessment = RightsPortabilityAssessment.objects.create(
        request=case,
        actor=user,
        action=action(),
        version=1,
        encrypted_assessment="synthetic",
        expires_at=now,
        **common,
    )
    read = RightsPortabilityRead.objects.create(
        action=action(), assessment=assessment, assessment_digest="e" * 64, **common
    )
    review = RightsPortabilityReview.objects.create(
        action=action(),
        assessment=assessment,
        read=read,
        assessment_digest="e" * 64,
        outcome="approved",
        **common,
    )
    selection = RightsPortabilitySelection.objects.create(
        request=case,
        actor=user,
        action=action(),
        assessment_review=review,
        version=1,
        encrypted_selection="synthetic",
        expires_at=now,
        selection_digest="f" * 64,
        assessment_digest="e" * 64,
        inspection_digest="1" * 64,
        decision_digest="2" * 64,
        **common,
    )
    selected_read = RightsPortabilitySelectionRead.objects.create(
        action=action(), selection=selection, selection_digest="f" * 64, **common
    )
    selected_review = RightsPortabilitySelectionReview.objects.create(
        action=action(),
        selection=selection,
        read=selected_read,
        selection_digest="f" * 64,
        outcome="approved",
        **common,
    )
    listing = Listing.objects.create(person=person)
    revision = Revision.objects.create(listing=listing, manager_version=1)
    blob = Blob.objects.create(sha256="3" * 64)
    photo = Photo.objects.create(revision=revision, blob=blob)
    image_read = RightsPortabilityImageRead.objects.create(
        action=action(),
        selection=selection,
        selection_read=selected_read,
        photo=photo,
        selection_digest="f" * 64,
        content_digest="3" * 64,
        **common,
    )
    coverage = RightsPortabilityCoverage.objects.create(
        request=case,
        actor=user,
        action=action(),
        selection_review=selected_review,
        version=1,
        encrypted_coverage="synthetic",
        expires_at=now,
        selection_digest="f" * 64,
        coverage_digest="4" * 64,
        **common,
    )
    coverage_read = RightsPortabilityCoverageRead.objects.create(
        action=action(),
        coverage=coverage,
        coverage_digest="4" * 64,
        dataset="subject_account",
        row_index=0,
        field_page=1,
        page_digest="5" * 64,
        **common,
    )
    coverage_review = RightsPortabilityCoverageReview.objects.create(
        action=action(), coverage=coverage, coverage_digest="4" * 64, outcome="approved", **common
    )
    return (
        case,
        assessment,
        common,
        action,
        [read, review, selected_read, selected_review, image_read, coverage_read, coverage_review],
    )


@pytest.fixture
def runtime():
    # Role is cluster-wide: random identifier avoids collisions across xdist DBs.
    role = "chain_runtime_" + uuid4().hex[:16]
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE ROLE {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOLOGIN").format(
                sql.Identifier(role)
            )
        )
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
        cursor.execute(
            sql.SQL("GRANT ALL ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(role))
        )
        cursor.execute(
            sql.SQL("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {}").format(
                sql.Identifier(role)
            )
        )
    configure_role(role)
    try:
        yield role
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def set_role(role):
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_runtime_rejects_every_source_and_chain_mutation(base, runtime, operation):
    case, _, _, _, _ = base
    ticket = validate_chain(case)
    set_role(runtime)
    for table in (*TABLES, HEAD, EVENT):
        if operation == "UPDATE":
            column = "digest" if table in (HEAD, EVENT) else "source_digest"
            query = sql.SQL("UPDATE public.{} SET {}=%s").format(
                sql.Identifier(table), sql.Identifier(column)
            )
            args = ["0" * 64]
        else:
            query = sql.SQL(
                operation + (" FROM " if operation == "DELETE" else " ") + "public.{}"
            ).format(sql.Identifier(table))
            args = []
        with pytest.raises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query, args)
    assert validate_chain(case, ticket=ticket, count=7) == ticket
    # Even an accidental GRANT cannot bypass the row/statement triggers.
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
        cursor.execute(
            sql.SQL("GRANT UPDATE,DELETE,TRUNCATE ON public.{} TO {}").format(
                sql.Identifier(TABLES[0]), sql.Identifier(runtime)
            )
        )
    set_role(runtime)
    with pytest.raises(DatabaseError, match="Immutable"), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("UPDATE public.{} SET source_digest=%s").format(sql.Identifier(TABLES[0])),
                ["0" * 64],
            )


def test_owner_drift_detected_even_when_ticket_and_head_unchanged(base):
    case, _, _, _, rows = base
    ticket = validate_chain(case)
    RightsPortabilityRead.objects.filter(pk=rows[0].pk).update(source_digest="0" * 64)
    assert RightsEvidenceHead.objects.get(request=case).digest == ticket.digest
    with pytest.raises(ValidationError, match="source rows"):
        validate_chain(case, ticket=ticket)


def test_concurrent_runtime_inserts_and_rollback_share_head(base, runtime):
    case, assessment, common, action, _ = base
    actions = [action(), action()]
    gate = Barrier(2)

    def insert(action_id):
        close_old_connections()
        try:
            set_role(runtime)
            gate.wait(timeout=10)
            with transaction.atomic():
                return RightsPortabilityRead.objects.create(
                    action_id=action_id, assessment=assessment, assessment_digest="e" * 64, **common
                ).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(insert, item.pk) for item in actions]
        assert len({future.result(timeout=30) for future in futures}) == 2
    ticket = validate_chain(case)
    assert ticket.count == 9
    with pytest.raises(RuntimeError, match="rollback"), transaction.atomic():
        RightsPortabilityRead.objects.create(
            action=action(), assessment=assessment, assessment_digest="e" * 64, **common
        )
        raise RuntimeError("rollback")
    assert validate_chain(case) == ticket


def test_backfill_restored_rows_preserves_existing_links_and_detects_drift(base):
    case, assessment, common, action, _ = base
    original = validate_chain(case)
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("ALTER TABLE public.{} DISABLE TRIGGER rights_evidence_record").format(
                sql.Identifier(TABLES[0])
            )
        )
    try:
        RightsPortabilityRead.objects.create(
            action=action(), assessment=assessment, assessment_digest="e" * 64, **common
        )
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_record").format(
                    sql.Identifier(TABLES[0])
                )
            )
    with pytest.raises(ValidationError, match="source rows"):
        validate_chain(case)
    backfill_missing()
    assert validate_chain(case).count == original.count + 1
    first = list(
        RightsEvidenceEvent.objects.filter(request=case)
        .order_by("sequence")
        .values_list("digest", flat=True)
    )
    backfill_missing()
    assert first == list(
        RightsEvidenceEvent.objects.filter(request=case)
        .order_by("sequence")
        .values_list("digest", flat=True)
    )


def test_tombstone_is_bounded_minimized_and_runtime_cannot_insert_chain_directly(base, runtime):
    case, _, _, _, _ = base
    set_role(runtime)
    key = uuid4()
    ticket = record_tombstone(case, "expired_payload_purged", key=key)
    assert record_tombstone(case, "expired_payload_purged", key=key) == ticket
    with pytest.raises(DatabaseError, match="Conflicting"), transaction.atomic():
        record_tombstone(case, "legal_erasure_recorded", key=key)
    assert ticket.count == 8
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT kind,source_table,source_pk,payload_digest FROM safety_rightsevidenceevent WHERE request_id=%s AND sequence=8",
            [case.pk],
        )
        kind, source, pk, digest = cursor.fetchone()
    assert (kind, source) == ("tombstone", "rights_payload_purge")
    assert len(pk) == 36 and len(digest) == 64
    with pytest.raises(DatabaseError), transaction.atomic():
        record_tombstone(case, "unbounded private reason forbidden")
    with pytest.raises(DatabaseError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO safety_rightsevidencehead(request_id,sequence,digest) VALUES(%s,99,%s)",
                [uuid4(), "0" * 64],
            )


def test_rollback_of_first_event_leaves_no_head(base):
    case, assessment, common, action, _ = base
    newcase = RightsRequest.objects.get(pk=case.pk)
    newcase.pk = uuid4()
    newcase.submission_key = uuid4()
    newcase.save(force_insert=True)
    newaction = action()
    newaction.request = newcase
    newaction.save(update_fields=["request"])
    with pytest.raises(RuntimeError), transaction.atomic():
        RightsPortabilityRead.objects.create(
            action=newaction, assessment=assessment, assessment_digest="e" * 64, **common
        )
        raise RuntimeError("rollback")
    assert not RightsEvidenceHead.objects.filter(request=newcase).exists()
    assert not RightsEvidenceEvent.objects.filter(request=newcase).exists()


@pytest.mark.parametrize("field", ["payload_digest", "source_pk", "created_at"])
def test_owner_event_link_mutation_rejected_and_ticket_count_strict(base, field):
    from datetime import timedelta

    case, _, _, _, _ = base
    ticket = validate_chain(case)
    with pytest.raises(ValidationError, match="count changed"):
        validate_chain(case, ticket=ticket, count=True)
    event = RightsEvidenceEvent.objects.filter(request=case).order_by("sequence").first()
    replacement = event.created_at + timedelta(seconds=1) if field == "created_at" else "0" * 64
    RightsEvidenceEvent.objects.filter(pk=event.pk).update(**{field: replacement})
    with pytest.raises(ValidationError, match="link changed"):
        validate_chain(case, ticket=ticket)


@pytest.mark.parametrize(
    "field", ["request_id", "actor_id", "operation", "expected_version", "key"]
)
def test_runtime_cannot_move_parent_action_scope_but_payload_remains_mutable(base, runtime, field):
    case, _, _, _, rows = base
    ticket = validate_chain(case)
    actor = User.objects.create(
        username="synthetic-other-chain-actor", email="other-chain-actor@example.invalid"
    )
    action = rows[0].action
    changes = {
        "request_id": uuid4(),
        "actor_id": actor.pk,
        "operation": "changed",
        "expected_version": 999,
        "key": uuid4(),
    }
    set_role(runtime)
    with pytest.raises(DatabaseError, match="action scope"), transaction.atomic():
        RightsAction.objects.filter(pk=action.pk).update(**{field: changes[field]})
    RightsAction.objects.filter(pk=action.pk).update(
        payload_digest="0" * 64, encrypted_reason="synthetic changed payload"
    )
    assert validate_chain(case, ticket=ticket) == ticket
    action.refresh_from_db()
    assert action.payload_digest == "0" * 64
    assert action.request_id == case.pk
