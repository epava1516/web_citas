# ruff: noqa: F811 -- imported real fixtures are requested by parameter name
"""Finite real PostgreSQL/media/S3 diagnostic restore; never acceptance evidence."""
import base64
import errno
import io
import json
import os
import tarfile
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import psycopg
import pytest
from django.core.management import call_command
from django.db import connection, connections, transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_object_store import object_store  # noqa: F401
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.object_storage.codec import Keyring
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_coverage_use import consume_approved_coverage
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


def test_actual_original_approval_roundtrip_and_config_rejection(request, settings, monkeypatch, object_store, tmp_path):
    import diagnostic_baseline as baseline

    from apps.safety.object_storage import factory

    secret = os.urandom(32)
    settings.RIGHTS_OBJECT_KEYS = json.dumps({'v1': base64.b64encode(secret).decode()})
    settings.RIGHTS_OBJECT_ACTIVE_KEY = 'v1'
    object_store.ring = Keyring({'v1': secret}, 'v1')
    monkeypatch.setattr(factory, 'repository', lambda: object_store)
    case, author, selection, selected, _, _, receipt = prepared_covered_selection(request, settings, monkeypatch, False, True)
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    facts = dict(status='excluded', basis='other', origin='inferred', automated=True,
                 subject_related=True, third_party_reviewed=True,
                 reason='Synthetic finite diagnostic exclusion', evidence='Synthetic documented exclusion')
    chosen = unseal(selection.encrypted_selection)
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        for index, item in enumerate(reader(source)):
            reference = row_reference(dataset, index, item)
            fields = next((set(row['fields']) for row in chosen['selection'][dataset] if row['row'] == reference), set())
            if any(field['path'] not in fields for field in scalar_fields(item)):
                omissions[dataset][reference] = {'all': facts}
    included = {image['photo'] for image in chosen.get('images', [])}
    images = {image['photo']: facts for revision in source['revisions'] for image in revision['images'] if image['photo'] not in included}
    reason = 'Inspect every original finite coverage page before diagnostic capture'
    row = save_coverage(author, case.pk, case.version, selected.pk, uuid4(), 0, reason, omissions, images)
    reviewer = User.objects.get(pk=selected.action.actor_id)
    for dataset, index, page, binary in required_pages(source):
        inspect_page(reviewer, case.pk, case.version, row.pk, uuid4(), reason, dataset, index, page, binary=binary)
    review = record(reviewer, case.pk, case.version, row.pk, uuid4(), reason, 'approved')
    descriptor = {name: str(value) for name, value in dict(case=case.pk, author=author.pk, reviewer=reviewer.pk,
                  selection_review=selected.pk, coverage_review=review.pk, receipt=receipt).items()}
    original_expiry = row.expires_at
    key = tmp_path / 'key'
    key.write_bytes(os.urandom(32))
    key.chmod(0o600)
    encrypted = tmp_path / 'baseline.bin'
    baseline.capture(descriptor, encrypted, key)
    # The same indexed encrypted artifact format is consumed by the controller.
    archive = tmp_path / 'artifacts.tar'
    value = encrypted.read_bytes()
    with tarfile.open(archive, 'w') as tar:
        for name, data in [('baseline.index.json', json.dumps({'parts': ['baseline.0000.bin']}).encode()), ('baseline.0000.bin', value)]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    call_command('flush', interactive=False, verbosity=0)
    observed, roles, fresh_login = [], [], baseline._fresh_login
    @contextmanager
    def checked_login(config, scratch):
        with fresh_login(config, scratch):
            with connection.cursor() as cursor:
                cursor.execute('SELECT current_user=session_user,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user')
                observed.append(cursor.fetchone())
                roles.append(config['USER'])
            yield
    monkeypatch.setattr(baseline, '_fresh_login', checked_login)
    original_config = deepcopy(connection.settings_dict)
    restored = baseline.restore(archive, key)
    assert observed == [(True, True, False, False, False, False)]
    assert bool(connection.settings_dict == original_config)
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user,session_user')
        assert cursor.fetchone() == ('ci', 'ci')
        # Restored evidence inserts are enforced and native FK triggers were
        # never disabled to evade deferred-event checks during COPY.
        cursor.execute("SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relname=ANY(%s) AND t.tgname='rights_evidence_record' AND t.tgenabled='O'", [list(baseline.TABLES)])
        assert cursor.fetchone()[0] == len(baseline.TABLES)
        cursor.execute("SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relname=ANY(%s) AND t.tgisinternal AND t.tgenabled NOT IN ('O','A')", [list(baseline.TABLES)])
        assert cursor.fetchone()[0] == 0
    assert bool(restored == descriptor)
    row.refresh_from_db()
    assert row.expires_at == original_expiry
    with transaction.atomic():
        actual, _ = consume_approved_coverage(User.objects.get(pk=author.pk), case.pk, case.version,
                                             review.pk, uuid4(), reason)
        assert actual.pk == review.pk
        transaction.set_rollback(True)
    # Existing current authority is never overwritten by diagnostic restore.
    User.objects.filter(pk=author.pk).update(is_active=False)
    with pytest.raises(ValueError, match='overwrite existing'):
        baseline.restore(archive, key)
    assert not User.objects.get(pk=author.pk).is_active
    call_command('flush', interactive=False, verbosity=0)
    settings.RIGHTS_EVIDENCE_ENFORCED = not settings.RIGHTS_EVIDENCE_ENFORCED
    with pytest.raises(ValueError, match='CACHE_REJECTED'):
        baseline.restore(archive, key)
    assert not User.objects.exists()
    settings.RIGHTS_EVIDENCE_ENFORCED = not settings.RIGHTS_EVIDENCE_ENFORCED
    actual_native = baseline._native
    def fail_copy(config, name, autocommit=False):
        if '_baseline_' in name and not autocommit:
            raise psycopg.OperationalError('Synthetic transport fault after actual scratch CREATE')
        return actual_native(config, name, autocommit)
    stage_before = set(baseline.Path(settings.MEDIA_ROOT).parent.glob('baseline-media-*'))
    monkeypatch.setattr(baseline, '_native', fail_copy)
    with pytest.raises(ValueError) as copy_failure:
        baseline.restore(archive, key)
    cause = copy_failure.value.__cause__
    safe_cause = str(cause) if isinstance(cause, ValueError) else type(cause).__name__
    assert str(copy_failure.value) == 'CACHE_REJECTED: OperationalError', safe_cause
    assert bool(connection.settings_dict == original_config)
    with connection.cursor() as cursor:
        cursor.execute("SELECT datname FROM pg_database WHERE datname LIKE %s", [original_config['NAME'] + '_baseline_%'])
        assert not cursor.fetchall()
        cursor.execute('SELECT current_user,session_user')
        assert cursor.fetchone() == ('ci', 'ci')
    assert set(baseline.Path(settings.MEDIA_ROOT).parent.glob('baseline-media-*')) == stage_before
    monkeypatch.setattr(baseline, '_native', actual_native)
    original_create = baseline._create_database
    def ambiguous_create(cursor, scratch, original):
        original_create(cursor, scratch, original)
        raise psycopg.OperationalError('Synthetic lost response after committed real CREATE')
    monkeypatch.setattr(baseline, '_create_database', ambiguous_create)
    with pytest.raises(ValueError, match='CACHE_REJECTED: OperationalError'):
        baseline.restore(archive, key)
    monkeypatch.setattr(baseline, '_create_database', original_create)
    with connection.cursor() as cursor:
        cursor.execute("SELECT datname FROM pg_database WHERE datname LIKE %s", [original_config['NAME'] + '_baseline_%'])
        assert not cursor.fetchall()
    original_login_create = baseline._create_login
    def ambiguous_login(cursor, role, secret):
        original_login_create(cursor, role, secret)
        roles.append(role)
        raise psycopg.OperationalError('Synthetic lost response after committed real LOGIN CREATE')
    monkeypatch.setattr(baseline, '_create_login', ambiguous_login)
    with pytest.raises(ValueError, match='CACHE_REJECTED: OperationalError'):
        baseline.restore(archive, key)
    monkeypatch.setattr(baseline, '_create_login', original_login_create)
    with connection.cursor() as cursor:
        cursor.execute('SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)', [roles])
        assert not cursor.fetchall()
    with monkeypatch.context() as changed:
        changed.setattr(timezone, 'now', lambda: original_expiry + timedelta(days=1))
        with pytest.raises(ValueError, match='CACHE_REJECTED'):
            baseline.restore(archive, key)
    inventory_key = 'diagnostic-rejection-' + uuid4().hex
    object_store.client.put_object(Bucket=object_store.bucket, Key=inventory_key, Body=b'synthetic')
    try:
        with pytest.raises(ValueError, match='CACHE_REJECTED'):
            baseline.restore(archive, key)
    finally:
        object_store.client.delete_object(Bucket=object_store.bucket, Key=inventory_key)
    with monkeypatch.context() as changed:
        options = deepcopy(connection.settings_dict['OPTIONS'])
        options['application_name'] = 'changed-diagnostic-config'
        changed.setitem(connection.settings_dict, 'OPTIONS', options)
        changed.setitem(settings.DATABASES['default'], 'OPTIONS', options)
        with pytest.raises(ValueError, match='CACHE_REJECTED'):
            baseline.restore(archive, key)
    @contextmanager
    def expired_proof(config, name, autocommit=False):
        with actual_native(config, name, autocommit) as database:
            yield database
            if '_baseline_' in name and not autocommit:
                with database.cursor() as cursor:
                    cursor.execute("UPDATE safety_rightsproof SET expires_at=now()-interval '1 second'")
    monkeypatch.setattr(baseline, '_native', expired_proof)
    with pytest.raises(ValueError, match='CACHE_REJECTED'):
        baseline.restore(archive, key)
    monkeypatch.setattr(baseline, '_native', actual_native)
    assert bool(connection.settings_dict == original_config)
    with connection.cursor() as cursor:
        cursor.execute('SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)', [roles])
        assert not cursor.fetchall()
        cursor.execute("SELECT datname FROM pg_database WHERE datname LIKE %s", [original_config['NAME'] + '_baseline_%'])
        assert not cursor.fetchall()
    original_copy = baseline.shutil.copytree
    def disk_full(*args, **kwargs):
        original_copy(*args, **kwargs)
        raise OSError(errno.ENOSPC, 'Synthetic staging fault after copy')
    monkeypatch.setattr(baseline.shutil, 'copytree', disk_full)
    with pytest.raises(ValueError, match='CACHE_REJECTED: OSError'):
        baseline.restore(archive, key)
    assert set(baseline.Path(settings.MEDIA_ROOT).parent.glob('baseline-media-*')) == stage_before
    assert not User.objects.exists()
    monkeypatch.setattr(baseline.shutil, 'copytree', original_copy)
    original_drop_login = baseline._drop_login
    def refused_cleanup(*args):
        raise psycopg.OperationalError('Synthetic LOGIN cleanup transport failure')
    monkeypatch.setattr(baseline, '_drop_login', refused_cleanup)
    with pytest.raises(baseline.BaselineCleanupError, match='LOGIN cleanup failed'):
        baseline.restore(archive, key)
    monkeypatch.setattr(baseline, '_drop_login', original_drop_login)
    assert bool(connection.settings_dict == original_config)
    assert not User.objects.exists()
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user,session_user')
        assert cursor.fetchone() == ('ci', 'ci')
        cursor.execute("SELECT datname FROM pg_database WHERE datname LIKE %s", [original_config['NAME'] + '_baseline_%'])
        assert not cursor.fetchall()
        cursor.execute('SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)', [roles])
        remaining = [row[0] for row in cursor.fetchall()]
    try:
        assert len(remaining) == 1
    finally:
        # Own runtime identity was recorded from its actual session before the
        # injected cleanup fault; scratch was removed, including its grants.
        with baseline._admin(original_config) as admin, admin.cursor() as cursor:
            for role in remaining:
                cursor.execute(baseline.sql.SQL('DROP ROLE {}').format(baseline.sql.Identifier(role)))
    assert set(baseline.Path(settings.MEDIA_ROOT).parent.glob('baseline-media-*')) == stage_before
    connections.close_all()
