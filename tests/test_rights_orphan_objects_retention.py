"""Real PostgreSQL/RustFS orphan cleanup with an explicit synthetic clock."""
import io
import json
import time
from datetime import timedelta

import pytest
from botocore.exceptions import ClientError
from django.utils import timezone
from test_operational_events import recorded_events as operational_recorded_events
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared
from test_rights_object_store import object_store as real_object_store

from apps.core.operational_assessment import assess
from apps.core.operational_snapshot import collect_snapshot
from apps.core.operational_window import summarize_window
from apps.safety import rights_object_content
from apps.safety.models import RightsExportPart

object_store = real_object_store
recorded_events = operational_recorded_events

pytestmark = pytest.mark.django_db(transaction=True)


def test_orphan_object_grace_live_reference_and_idempotent_physical_removal(
    request, settings, monkeypatch, object_store, recorded_events,
):
    case, actor, _, _, _, _ = prepared(request, settings)
    export = make_copy(case, actor)
    repo = object_store
    orphan = repo.write(io.BytesIO(b'synthetic orphan bytes'), b'orphan')
    retained = repo.write(io.BytesIO(b'synthetic retained bytes'), b'retained')
    part = RightsExportPart.objects.create(export=export, position=987, encrypted_content=retained)
    orphan_key = repo.descriptor(orphan)['key']
    retained_key = repo.descriptor(retained)['key']
    monkeypatch.setattr(rights_object_content, 'repository', lambda: repo)
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
    settings.RECOVERY_MODE = False
    assert rights_object_content.purge_orphan_export_objects() == 0
    assert repo.client.head_object(Bucket=repo.bucket, Key=orphan_key)['ContentLength'] > 0
    future = timezone.now() + timedelta(days=2)
    monkeypatch.setattr(timezone, 'now', lambda: future)
    settings.RECOVERY_MODE = True
    assert rights_object_content.purge_orphan_export_objects() == 0
    settings.RECOVERY_MODE = False
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = False
    assert rights_object_content.purge_orphan_export_objects() == 0
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
    snapshot = collect_snapshot()
    assert snapshot['object_storage']['orphan_inventory'] == 'unmeasured'
    assert 'object_orphan_inventory_unmeasured' in {r['code'] for r in assess(snapshot)['findings']}
    original_delete = repo.delete_unreferenced
    failed_once = False
    def fail_once(key):
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            raise OSError('SYNTHETIC_STORAGE_FAILURE')
        return original_delete(key)
    monkeypatch.setattr(repo, 'delete_unreferenced', fail_once)
    # Explicit local eager execution exercises actual task hooks, not worker consumption.
    failed = rights_object_content.purge_orphan_export_objects.apply(throw=False)
    assert failed.failed()
    assert repo.client.head_object(Bucket=repo.bucket, Key=orphan_key)['ContentLength'] > 0
    rows = [r for r in recorded_events()
            if r.get('task') == rights_object_content.purge_orphan_export_objects.name]
    assert rows[-1]['outcome'] == 'failed'
    tick = int(time.time())
    window = summarize_window(io.BytesIO(b''.join(json.dumps(r).encode() + b'\n' for r in rows)), tick - 60, tick + 1)
    assert 'task_failed_observed' in {r['code'] for r in assess(snapshot, window)['findings']}
    assert 'SYNTHETIC_STORAGE_FAILURE' not in json.dumps(rows)
    recovered = rights_object_content.purge_orphan_export_objects.apply(throw=False)
    assert recovered.successful() and recovered.result == 1
    rows = [r for r in recorded_events()
            if r.get('task') == rights_object_content.purge_orphan_export_objects.name]
    assert [r['outcome'] for r in rows] == ['failed', 'succeeded']
    with pytest.raises(ClientError) as absent:
        repo.client.head_object(Bucket=repo.bucket, Key=orphan_key)
    assert absent.value.response['ResponseMetadata']['HTTPStatusCode'] == 404
    assert repo.client.head_object(Bucket=repo.bucket, Key=retained_key)['ContentLength'] > 0
    part.refresh_from_db()
    assert part.encrypted_content == retained
    output = io.BytesIO()
    repo.read(retained, output, b'retained')
    assert output.getvalue() == b'synthetic retained bytes'
    assert rights_object_content.purge_orphan_export_objects() == 0
