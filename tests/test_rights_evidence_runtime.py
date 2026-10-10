# ruff: noqa: F811 -- imported pytest fixtures are requested by parameter name
"""Real PostgreSQL nonowner locks, enforcement and validate-to-append concurrency."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, close_old_connections, connection, connections, transaction
from psycopg import sql
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_evidence_chain import base, runtime, set_role  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.evidence_chain import record_tombstone, require_runtime_chain, validate_chain
from apps.safety.evidence_chain_sql_v1 import TABLES

pytestmark = pytest.mark.django_db(transaction=True)


def test_real_runtime_can_lock_every_metadata_family_but_cannot_update_id(base, runtime):
    case, _, _, _, rows = base
    set_role(runtime)
    with transaction.atomic(), connection.cursor() as cursor:
        for table, row in zip(TABLES, rows):
            cursor.execute(
                sql.SQL("SELECT id FROM public.{} WHERE id=%s FOR UPDATE").format(
                    sql.Identifier(table)
                ),
                [row.pk],
            )
            assert cursor.fetchone() == (row.pk,)
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("UPDATE public.{} SET id=id WHERE id=%s").format(sql.Identifier(TABLES[0])),
            [rows[0].pk],
        )
    ticket = validate_chain(case)
    assert validate_chain(case, ticket=ticket) == ticket


def test_enforcement_rejects_owner_accepts_runtime_and_detects_owner_drift(base, runtime, settings):
    case, _, _, _, rows = base
    settings.RIGHTS_EVIDENCE_ENFORCED = True
    with pytest.raises(ValidationError, match="separate trusted runtime"):
        require_runtime_chain(case)
    set_role(runtime)
    assert require_runtime_chain(case).count == 7
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
    type(rows[0]).objects.filter(pk=rows[0].pk).update(source_digest="0" * 64)
    set_role(runtime)
    with pytest.raises(ValidationError, match="source rows"):
        require_runtime_chain(case)


def test_two_runtime_transactions_validate_then_append_without_case_lock(base, runtime):
    case, _, _, _, _ = base
    barrier = Barrier(2)

    def run():
        close_old_connections()
        try:
            set_role(runtime)
            barrier.wait(timeout=10)
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL statement_timeout='15s'")
                before = validate_chain(case)
                after = record_tombstone(case, "expired_payload_purged", uuid4())
                assert after.count == before.count + 1
                return after.count
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(run) for _ in range(2)]
        assert sorted(item.result(timeout=25) for item in results) == [8, 9]
    assert validate_chain(case).count == 9


def test_real_runtime_consumes_approved_domain_and_keeps_authority_guard(
    request, settings, monkeypatch, runtime
):
    from django.core.exceptions import PermissionDenied

    from apps.core.models import User
    from apps.safety.models import RightsPortabilityReview
    from apps.safety.rights_portability_use import consume_approved

    case, author, selection, _, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    review = RightsPortabilityReview.objects.get(pk=selection.assessment_review_id)
    settings.RIGHTS_EVIDENCE_ENFORCED = True
    set_role(runtime)
    result, body = consume_approved(
        author,
        case.pk,
        case.version,
        review.pk,
        uuid4(),
        "Consume actual approved synthetic assessment under runtime role",
    )
    assert result.pk == review.pk and body
    User.objects.filter(pk=author.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        consume_approved(
            author,
            case.pk,
            case.version,
            review.pk,
            uuid4(),
            "Reject fresh disabled actor despite immutable approved evidence",
        )


def test_extra_column_grant_is_not_trusted_for_enforcement(base, runtime, settings):
    case, _, _, _, _ = base
    settings.RIGHTS_EVIDENCE_ENFORCED = True
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("GRANT UPDATE(source_digest) ON public.{} TO {}").format(
                sql.Identifier(TABLES[0]), sql.Identifier(runtime)
            )
        )
    set_role(runtime)
    with pytest.raises(ValidationError, match="separate trusted runtime"):
        require_runtime_chain(case)


def test_migrator_command_provisions_actual_nonowner_login(base, monkeypatch):
    from django.core.management import call_command
    from psycopg import connect

    role = "chain_login_" + uuid4().hex[:16]
    secret = uuid4().hex
    monkeypatch.setenv("POSTGRES_RUNTIME_USER", role)
    monkeypatch.setenv("POSTGRES_RUNTIME_PASSWORD", secret)
    try:
        call_command("initialize_rights_runtime", verbosity=0)
        config = connection.settings_dict
        with connect(
            dbname=config["NAME"],
            user=role,
            password=secret,
            host=config["HOST"],
            port=config["PORT"],
        ) as login:
            with login.cursor() as cursor:
                cursor.execute("SELECT current_user")
                assert cursor.fetchone() == (role,)
                cursor.execute(
                    sql.SQL("SELECT id FROM public.{} LIMIT 1 FOR UPDATE").format(
                        sql.Identifier(TABLES[0])
                    )
                )
                assert cursor.fetchone()
                cursor.execute(
                    "SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user"
                )
                assert cursor.fetchone() == (False, False, False, False)
        set_role(role)
        assert validate_chain(base[0]).count == 7
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [role])
            if cursor.fetchone():
                cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
