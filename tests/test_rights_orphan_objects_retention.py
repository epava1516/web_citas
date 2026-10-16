"""Real PostgreSQL/RustFS orphan cleanup with an explicit synthetic clock."""
import io
from datetime import timedelta

import pytest
from botocore.exceptions import ClientError
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared
from test_rights_object_store import object_store as real_object_store

from apps.safety import rights_object_content
from apps.safety.models import RightsExportPart

object_store = real_object_store

pytestmark = pytest.mark.django_db(transaction=True)


def test_orphan_object_grace_live_reference_and_idempotent_physical_removal(
    request, settings, monkeypatch, object_store,
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
    assert rights_object_content.purge_orphan_export_objects() == 1
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
