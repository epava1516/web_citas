# ruff: noqa: F811 -- imported real fixtures are requested by parameter name
"""Finite real PostgreSQL/media/S3 diagnostic restore; never acceptance evidence."""
import base64
import io
import json
import os
import tarfile
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import connections, transaction
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
    restored = baseline.restore(archive, key)
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
    with pytest.raises(ValueError, match='code/config/schema/keyversion'):
        baseline.restore(archive, key)
    assert not User.objects.exists()
    connections.close_all()
