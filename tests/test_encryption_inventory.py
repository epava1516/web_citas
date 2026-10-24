"""Actual PostgreSQL bounded cipher census; no storage or retirement authority."""
import io
import json
from datetime import timedelta
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared

from apps.core import encryption_inventory as census
from apps.core.models import User
from apps.mediafiles.models import Blob, MediaPreparationCleanup
from apps.safety.models import Report, RightsExportPart
from apps.safety.object_storage.repository import PREFIX

pytestmark = pytest.mark.django_db(transaction=True)


def keys(settings):
    old, active = Fernet.generate_key(), Fernet.generate_key()
    settings.SAFETY_ENCRYPTION_KEY = active.decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = old.decode()
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = Fernet.generate_key().decode()
    return old, active


def report(value):
    return Report.objects.create(submission_key=uuid4(), receipt_digest=uuid4().hex * 2,
                                 payload_digest=uuid4().hex * 2, encrypted_payload=value,
                                 mode='listing', reason='other', receipt_expires_at=timezone.now() + timedelta(days=1))


def metric(result, model, field):
    return next(row for row in result['fields'] if row['model'] == model and row['field'] == field)


def test_empty_registry_is_complete_read_only_and_never_authorizes_retirement():
    with CaptureQueriesContext(connection) as captured:
        result = census.collect_inventory()
    assert len(result['fields']) == len(census.ENCRYPTED_COLUMNS) == 54
    assert result['totals']['nonempty'] == 0 and result['database_scan_complete']
    assert result['retirement_authorized'] is False and result['external_scopes_unmeasured']
    sql = [q['sql'] for q in captured.captured_queries]
    assert 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY' in sql
    assert all(s.startswith(('BEGIN', 'SET ', 'SELECT ', 'COMMIT')) for s in sql)
    assert connection.get_autocommit() and not connection.in_atomic_block
    with connection.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        assert cursor.fetchone()[0] == 'off'


def test_current_previous_corrupt_and_media_cells_are_counted_without_export_or_mutation(settings, monkeypatch):
    from apps.safety.object_storage import factory
    def no_storage(*args, **kwargs):
        raise AssertionError('Cipher census must not contact storage')
    monkeypatch.setattr(factory, 'repository', no_storage)
    old, active = keys(settings)
    rows = [report(Fernet(key).encrypt(b'PRIVATE_RETAINED_BODY').decode()) for key in (old, active)]
    report('PRIVATE_BROKEN_CIPHER')
    mfa_keys = (settings.MFA_ENCRYPTION_KEY_FALLBACKS.encode(), settings.MFA_ENCRYPTION_KEY.encode())
    for index, key in enumerate(mfa_keys):
        User.objects.create(username=f'inventory-{index}', email=f'inventory-{index}@example.invalid',
                            mfa_secret_encrypted=Fernet(key).encrypt(b'PRIVATE_MFA_SEED').decode())
    blob = Blob.objects.create(sha256=uuid4().hex * 2, status='purging')
    MediaPreparationCleanup.objects.create(blob=blob, encrypted_paths=Fernet(old).encrypt(b'PRIVATE_PATH').decode())
    before = list(Report.objects.order_by('pk').values())
    result = census.collect_inventory()
    assert result['totals'] == {'nonempty': 6, 'sampled': 6, 'active': 2, 'previous': 3,
                                'unreadable': 1, 'oversized_unmeasured': 0, 'not_sampled': 0}
    assert metric(result, 'safety.Report', 'encrypted_payload')['roles'] == {'active': 1, 'previous_1': 1, 'unreadable': 1}
    assert metric(result, 'core.User', 'mfa_secret_encrypted')['roles']['previous_1'] == 1
    assert list(Report.objects.order_by('pk').values()) == before
    encoded = json.dumps(result)
    assert 'PRIVATE_' not in encoded and old.decode() not in encoded and active.decode() not in encoded
    assert all(str(r.pk) not in encoded and r.encrypted_payload not in encoded for r in rows)
    assert result['retirement_authorized'] is False


def test_budget_and_oversized_values_remain_unmeasured(settings):
    _, active = keys(settings)
    for _ in range(3):
        report(Fernet(active).encrypt(b'synthetic small').decode())
    report('x' * (census.MAX_CIPHER_BYTES + 1))
    result = census.collect_inventory(max_cells=1)
    assert result['totals']['sampled'] == 1 and result['totals']['not_sampled'] == 2
    assert result['totals']['oversized_unmeasured'] == 1
    assert not result['database_scan_complete'] and result['retirement_authorized'] is False
    broader = census.collect_inventory(max_cells=1000)
    assert broader['totals']['sampled'] == broader['totals']['active'] == 3
    assert broader['totals']['not_sampled'] == 0 and broader['totals']['oversized_unmeasured'] == 1
    assert broader['totals']['unreadable'] == 0


def test_object_reference_outer_cipher_is_counted_without_claiming_object_inventory(request, settings):
    old = Fernet.generate_key()
    settings.SAFETY_ENCRYPTION_KEY = old.decode()
    case, user, *_ = prepared(request, settings)
    export = make_copy(case, user)
    value = PREFIX + Fernet(old).encrypt(b'PRIVATE_DESCRIPTOR_BYTES').decode()
    part = RightsExportPart.objects.create(export=export, position=987, encrypted_content=value)
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = old.decode()
    result = census.collect_inventory()
    row = metric(result, 'safety.RightsExportPart', 'encrypted_content')
    nonempty_parts = RightsExportPart.objects.exclude(encrypted_content='').count()
    assert row['roles']['previous_1'] == row['sampled'] == nonempty_parts
    part.refresh_from_db()
    assert part.encrypted_content == value
    assert 'object_bytes_and_tombstones' in result['external_scopes_unmeasured']
    assert result['retirement_authorized'] is False


def test_schema_drift_is_rejected_before_reading_private_cells(monkeypatch):
    monkeypatch.setattr(census, 'ENCRYPTED_COLUMNS', census.ENCRYPTED_COLUMNS[:-1])
    with pytest.raises(census.InventoryUnavailable, match='registry differs'):
        census.collect_inventory()


def test_inherited_transaction_is_rejected_without_changing_it():
    with transaction.atomic():
        with pytest.raises(census.InventoryUnavailable, match='own PostgreSQL transaction'):
            census.collect_inventory()
        assert connection.in_atomic_block
    assert connection.get_autocommit()


def test_configuration_drift_does_not_return_a_mixed_report(settings, monkeypatch):
    _, active = keys(settings)
    report(Fernet(active).encrypt(b'synthetic').decode())
    original = census._classify
    def drift(*args, **kwargs):
        value = original(*args, **kwargs)
        settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
        return value
    monkeypatch.setattr(census, '_classify', drift)
    with pytest.raises(census.InventoryUnavailable, match='configuration changed'):
        census.collect_inventory()


def test_database_error_has_no_partial_command_output_or_private_diagnostic(monkeypatch):
    output = io.StringIO()
    def broken(*args, **kwargs):
        raise DatabaseError('PRIVATE_DATABASE_DIAGNOSTIC')
    with monkeypatch.context() as patch:
        patch.setattr(connection, 'cursor', broken)
        with pytest.raises(CommandError) as rejected:
            call_command('encryption_key_inventory', inspect_ciphertext=True, stdout=output)
    assert output.getvalue() == '' and str(rejected.value) == 'Key inventory could not read its configured scope'
    assert connection.get_autocommit()


def test_command_requires_explicit_inspection_and_outputs_only_report():
    with pytest.raises(CommandError, match='Explicit --inspect-ciphertext'):
        call_command('encryption_key_inventory')
    output = io.StringIO()
    call_command('encryption_key_inventory', inspect_ciphertext=True, max_cells=1, stdout=output)
    result = json.loads(output.getvalue())
    assert result['cell_budget'] == 1 and result['retirement_authorized'] is False


@pytest.mark.parametrize('budget', [0, 10001, True])
def test_invalid_budget_cannot_start_inspection(budget):
    with pytest.raises(census.InventoryUnavailable, match='Cell budget'):
        census.collect_inventory(budget)


def test_invalid_key_configuration_is_sanitized_without_partial_output(settings):
    settings.SAFETY_ENCRYPTION_KEY = 'PRIVATE_INVALID_KEY'
    output = io.StringIO()
    with pytest.raises(CommandError) as rejected:
        call_command('encryption_key_inventory', inspect_ciphertext=True, stdout=output)
    assert str(rejected.value) == 'Key inventory could not read its configured scope'
    assert output.getvalue() == ''


def test_connection_failure_before_transaction_is_also_sanitized(monkeypatch):
    def fail():
        raise DatabaseError('PRIVATE_CONNECTION_DETAIL')
    with monkeypatch.context() as patch:
        patch.setattr(connection, 'get_autocommit', fail)
        with pytest.raises(census.InventoryUnavailable) as rejected:
            census.collect_inventory()
    assert str(rejected.value) == 'Key inventory could not read its configured scope'
