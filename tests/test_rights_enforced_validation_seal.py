"""Full historical validation/replay through an actual nonowner PostgreSQL LOGIN.

Identity verification in the original fixture is explicitly synthetic. No
approval/read is invented; the complete covered binary export uses real services.
Execute only in the root-coordinated PostgreSQL/S3 window.
"""

import json
from contextlib import contextmanager
from datetime import timedelta

import psycopg
import pytest
from capacity_runtime_role import runtime_role_environment
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.utils import timezone
from psycopg import sql
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_object_store import object_store  # noqa: F401
from test_rights_validation_seal import check, generated

from apps.safety import rights_object_content, rights_portability_export, rights_validation_seal
from apps.safety.evidence_chain import _runtime_is_trusted, record_tombstone
from apps.safety.evidence_chain_bulk_sql_v1 import SOURCE_FUNCTIONS
from apps.safety.evidence_chain_sql_v1 import TABLES
from apps.safety.models import RightsExportValidationSeal, RightsPortabilityCoverageRead

pytestmark = pytest.mark.django_db(transaction=True)


@contextmanager
def login(settings):
    """Actual TCP authentication, not SET ROLE; restore migrator before cleanup."""
    database = connection.settings_dict
    original_database = dict(database)
    original_settings = dict(settings.DATABASES["default"])
    enforced = settings.RIGHTS_EVIDENCE_ENFORCED
    with runtime_role_environment() as environment:
        with open(environment["RIGHTS_EVIDENCE_RUNTIME_CONFIG"]) as source:
            credentials = json.load(source)
        connections.close_all()
        database.update(credentials)
        settings.DATABASES["default"].update(credentials)
        settings.RIGHTS_EVIDENCE_ENFORCED = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_user,session_user,current_database()")
                assert cursor.fetchone() == (credentials["USER"], credentials["USER"], credentials["NAME"])
                assert _runtime_is_trusted(cursor)
            # Keep the administrative connection independently authenticated; no
            # role switch or security-setting relaxation in the runtime connection.
            with psycopg.connect(dbname=original_database["NAME"], user=original_database["USER"],
                                 password=original_database["PASSWORD"], host=original_database["HOST"],
                                 port=original_database["PORT"], autocommit=True) as admin:
                yield admin, credentials["USER"]
        finally:
            connections.close_all()
            database.clear()
            database.update(original_database)
            settings.DATABASES["default"].clear()
            settings.DATABASES["default"].update(original_settings)
            settings.RIGHTS_EVIDENCE_ENFORCED = enforced


def observe(monkeypatch):
    """Observe full validation/recording without replacing either implementation."""
    states, full_calls = [], []
    native_recording = rights_validation_seal.recording
    native_full = rights_portability_export._validate_export_binding
    native_holds = rights_validation_seal.holds
    native_replay = rights_validation_seal._replay

    def replay(statements):
        actual = native_replay(statements)
        if states:
            states[-1]["replay_mismatches"] = [
                index for index, (recorded, replayed) in enumerate(
                    zip(states[-1]["digests"], actual, strict=True)
                ) if recorded != replayed
            ]
        return actual

    def holds(export, caller):
        if states:
            candidate = RightsExportValidationSeal.objects.filter(export=export).latest("pk")
            states[-1]["reuse_inputs"] = {
                "rule_matches": candidate.rule_version == rights_validation_seal.rule_version(),
                "caller_matches": candidate.caller_digest == rights_validation_seal.caller_digest(
                    *caller.values()
                ),
                "unexpired": candidate.valid_until > timezone.now(),
            }
        return native_holds(export, caller)

    @contextmanager
    def recording():
        with native_recording() as state:
            yield state
        states.append(state)

    def full(*args, **kwargs):
        full_calls.append(True)
        return native_full(*args, **kwargs)

    monkeypatch.setattr(rights_validation_seal, "recording", recording)
    monkeypatch.setattr(rights_validation_seal, "holds", holds)
    monkeypatch.setattr(rights_validation_seal, "_replay", replay)
    monkeypatch.setattr(rights_portability_export, "_validate_export_binding", full)
    return states, full_calls


def warm(case, author, export, states, calls):
    assert check(case, author, export) is False
    assert len(calls) == 1 and len(states) == 1
    state = states[0]
    assert state["supported"] is True
    assert len(state["statements"]) == len(state["digests"]) > len(TABLES)
    for function in SOURCE_FUNCTIONS:
        assert any(f'FROM public.{function}(' in statement
                   for statement, _ in state["statements"])
    seal = RightsExportValidationSeal.objects.get(export=export)
    assert len(seal.result_digests) == len(state["digests"])
    assert seal.valid_until > timezone.now()
    assert check(case, author, export) is True, {
        "reuse_inputs": state.get("reuse_inputs"),
        "replay_mismatches": state.get("replay_mismatches"),
    }
    assert len(calls) == len(states) == 1
    return seal


def test_complete_enforced_login_validation_creates_and_replays_seal(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    RightsExportValidationSeal.objects.filter(export=export).delete()
    with login(settings):
        states, calls = observe(monkeypatch)
        seal = warm(case, author, export, states, calls)
        assert seal.rule_version == rights_validation_seal.rule_version()
        assert seal.valid_until <= export.expires_at


def test_current_chain_append_declines_old_seal_and_fully_revalidates(request, settings, monkeypatch):
    case, author, export, _ = generated(request, settings, monkeypatch)
    RightsExportValidationSeal.objects.filter(export=export).delete()
    with login(settings):
        states, calls = observe(monkeypatch)
        previous = warm(case, author, export, states, calls)
        record_tombstone(case, "expired_payload_purged")
        assert check(case, author, export) is False
        assert len(calls) == len(states) == 2
        assert RightsExportValidationSeal.objects.filter(export=export).count() == 2
        assert RightsExportValidationSeal.objects.filter(export=export).latest("pk").pk != previous.pk
        assert check(case, author, export) is True


@pytest.mark.parametrize("mutation", ["metadata_tamper", "acl", "proof_expiry"])
def test_current_tamper_acl_or_proof_expiry_cannot_use_enforced_seal(
    request, settings, monkeypatch, mutation
):
    case, author, export, _ = generated(request, settings, monkeypatch)
    RightsExportValidationSeal.objects.filter(export=export).delete()
    with login(settings) as (admin, role):
        states, calls = observe(monkeypatch)
        warm(case, author, export, states, calls)
        with admin.cursor() as cursor:
            if mutation == "metadata_tamper":
                row = RightsPortabilityCoverageRead.objects.filter(action__request=case).first()
                table = row._meta.db_table
                with admin.transaction():
                    cursor.execute(sql.SQL("ALTER TABLE public.{} DISABLE TRIGGER rights_evidence_no_modify")
                                   .format(sql.Identifier(table)))
                    cursor.execute(sql.SQL("UPDATE public.{} SET page_digest=%s WHERE id=%s")
                                   .format(sql.Identifier(table)), ["0" * 64, row.pk])
                    cursor.execute(sql.SQL("ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_no_modify")
                                   .format(sql.Identifier(table)))
            elif mutation == "acl":
                cursor.execute(sql.SQL("GRANT UPDATE(source_digest) ON public.{} TO {}")
                               .format(sql.Identifier(TABLES[0]), sql.Identifier(role)))
            else:
                cursor.execute(sql.SQL("UPDATE public.{} SET expires_at=%s WHERE id=%s")
                               .format(sql.Identifier(export.proof._meta.db_table)),
                               [timezone.now() - timedelta(seconds=1), export.proof_id])
        with pytest.raises(ValidationError):
            check(case, author, export)
        assert len(calls) == 2
        assert RightsExportValidationSeal.objects.filter(export=export).count() == 1


def test_enforced_held_seal_still_rejects_real_external_object_corruption(
    request, settings, monkeypatch, object_store  # noqa: F811
):
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
    monkeypatch.setattr(rights_object_content, "repository", lambda: object_store)
    case, author, export, _ = generated(request, settings, monkeypatch)
    RightsExportValidationSeal.objects.filter(export=export).delete()
    with login(settings):
        states, calls = observe(monkeypatch)
        warm(case, author, export, states, calls)
        snapshot = export.images.first()
        key = object_store.descriptor(snapshot.encrypted_content)["key"]
        object_store.client.put_object(Bucket=object_store.bucket, Key=key, Body=b"corrupt ciphertext")
        with pytest.raises(ValidationError, match="External export object"):
            check(case, author, export)
        # SQL seal still matched: physical verification rejects independently.
        assert len(calls) == len(states) == 1
