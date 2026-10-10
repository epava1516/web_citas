"""Finite real owned topology gate; no target fixture, concurrency load or percentile."""

import hashlib
import io
import json
import time
import urllib.error
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from capacity_delivery_http import open_client, post
from capacity_gunicorn import server
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared, url

from apps.safety.models import RightsExportDownload
from apps.safety.object_storage.factory import repository
from apps.safety.rights_object_delivery import _signed_url
from apps.safety.rights_object_models import RightsObjectDelivery

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_object_proxy_and_purge_worker_gate(request, settings, record_property):
    assert settings.CAPACITY_PREFLIGHT_ONLY and settings.CAPACITY_OBJECT_DELIVERY
    assert settings.RIGHTS_OBJECT_STORAGE_ENABLED and settings.RIGHTS_PROXY_DELIVERY_ENABLED
    assert settings.RIGHTS_DELIVERY_ROOT == Path("/srv/delivery")
    proof = {}
    try:
        repo = repository()
        content = b"synthetic-own-object-preflight" * 128
        ref = repo.write(io.BytesIO(content), b"preflight/own/v1")
        output = io.BytesIO()
        assert repo.read(ref, output, b"preflight/own/v1") == len(content)
        assert output.getvalue() == content
        proof["s3_aead"] = True
        key = repo.descriptor(ref)["key"]
        repo.purge(ref)
        with pytest.raises(ClientError) as gone:
            repo.client.head_object(Bucket=repo.bucket, Key=key)
        assert gone.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404
        proof["s3_purge"] = True
        # directory/photo_environment uses eager tasks for fixture construction.
        case, author, _, browser, receipt, _ = prepared(request, settings)
        settings.CELERY_TASK_ALWAYS_EAGER = False
        export = make_copy(case, author)
        # Existing direct contract supplies the expected whole-body bytes once.
        settings.RIGHTS_PROXY_DELIVERY_ENABLED = False
        expected = browser.post(url(receipt, export), {"key": uuid4()})
        assert expected.status_code == 200
        settings.RIGHTS_PROXY_DELIVERY_ENABLED = True
        download = RightsExportDownload.objects.get(export=export)
        with server(settings, record_property) as endpoint:
            client = open_client(settings, endpoint, receipt)
            delivered = post(
                client.client,
                endpoint.url + url(receipt, export),
                client.csrf,
                {"key": str(download.key)},
            )
            assert [stage["status"] for stage in delivered.stages] == [303, 200]
            assert delivered.body == expected.content
            assert delivered.stages[-1]["sha256"] == hashlib.sha256(expected.content).hexdigest()
            assert "no-store" in delivered.headers["Cache-Control"]
            assert RightsExportDownload.objects.filter(export=export).count() == 1
            proof["caddy_bytes"] = True
            grant = RightsObjectDelivery.objects.get(download=download)
            # Opaque URL never persisted in metrics or access logs.
            with pytest.raises(urllib.error.HTTPError) as replay:
                client.client.private_delivery.open(endpoint.url + _signed_url(grant), timeout=10)
            assert replay.value.code == 404
            replay.value.close()
            proof["caddy_replay_denied"] = True
            RightsObjectDelivery.objects.filter(pk=grant.pk).update(
                expires_at=timezone.now() - timedelta(seconds=1)
            )
            # Actual Beat publishes periodic purge to the real broker/worker in app cgroup.
            from celery import current_app

            assert current_app.conf.task_always_eager is False
            until = time.monotonic() + 30
            while True:
                grant.refresh_from_db()
                if grant.purged_at:
                    break
                assert time.monotonic() < until, "Own worker did not complete finite purge gate"
                time.sleep(0.1)
            assert not (settings.RIGHTS_DELIVERY_ROOT / grant.object_name).exists()
            proof["worker_purge"] = True
            proof["beat_purge"] = True
        proof["scope"] = (
            "Finite synthetic PG/S3/Caddy/worker topology only; no target1500 fixture or capacity"
        )
    finally:
        record_property("object_delivery_preflight", json.dumps(proof))
