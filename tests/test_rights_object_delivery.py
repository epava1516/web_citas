"""PG grants and actual Caddy byte transport, with fresh recipient authority."""

import hashlib
import os
import subprocess
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from wsgiref.simple_server import WSGIRequestHandler, make_server

import pytest
from django.core.wsgi import get_wsgi_application
from django.db import close_old_connections, connections, transaction
from django.http import Http404
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared, url

from apps.core.models import Person
from apps.safety.models import RightsExport, RightsExportDownload, RightsRequest
from apps.safety.rights_object_delivery import (
    authorize_token,
    invalidate_restored_deliveries,
    purge_object_deliveries,
    stage_delivery,
)
from apps.safety.rights_object_models import RightsObjectDelivery

pytestmark = pytest.mark.django_db(transaction=True)


def staged(request, settings, tmp_path, *, through_post=False):
    case, user, _, client, receipt, person = prepared(request, settings)
    export = make_copy(case, user)
    response = client.post(url(receipt, export), {"key": uuid4()})
    assert response.status_code == 200
    download = RightsExportDownload.objects.get(export=export)
    settings.RIGHTS_DELIVERY_ROOT = tmp_path
    settings.RIGHTS_PROXY_DELIVERY_ENABLED = True
    settings.RIGHTS_DELIVERY_GENERATION = "synthetic-v1"
    settings.RIGHTS_DELIVERY_PROXY_SECRET = "synthetic-proxy-secret-" + "x" * 40
    if through_post:
        redirected = client.post(url(receipt, export), {"key": download.key})
        assert redirected.status_code == 303
        assert "no-store" in redirected["Cache-Control"]
        path = redirected["Location"]
    else:
        with transaction.atomic():
            path = stage_delivery(
                export, download, response.content, response["Content-Type"], "rights-profile.json"
            )
    row = RightsObjectDelivery.objects.get(download=download)
    row._receipt, row._client = receipt, client
    return case, export, person, path, row, response.content


def test_one_use_and_original_audit_count(request, settings, tmp_path):
    _, _, _, path, row, content = staged(request, settings, tmp_path)
    value = authorize_token(path.rsplit("/", 1)[1])
    assert (tmp_path / value.object_name).read_bytes() == content
    assert hashlib.sha256(content).hexdigest() == value.content_sha256
    assert RightsExportDownload.objects.count() == 1
    row.refresh_from_db()
    assert row.consumed_at is not None
    with pytest.raises(Http404):
        authorize_token(path.rsplit("/", 1)[1])


@pytest.mark.parametrize(
    "change", ["receipt", "subject", "expires", "payload", "namespace", "grant", "file", "restore"]
)
def test_fresh_revocation_content_expiry_foreign_scope_and_restore(
    request, settings, tmp_path, change
):
    case, export, person, path, row, _ = staged(request, settings, tmp_path)
    if change == "receipt":
        RightsRequest.objects.filter(pk=case.pk).update(receipt_digest="f" * 64)
    elif change == "subject":
        Person.objects.filter(pk=person.pk).update(rights_version=person.rights_version + 1)
    elif change == "expires":
        RightsExport.objects.filter(pk=export.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
    elif change == "payload":
        RightsExport.objects.filter(pk=export.pk).update(encrypted_payload="changed")
    elif change == "namespace":
        settings.RIGHTS_DELIVERY_GENERATION = "synthetic-v2"
    elif change == "grant":
        RightsObjectDelivery.objects.filter(pk=row.pk).update(filename="different.json")
    elif change == "file":
        (tmp_path / row.object_name).write_bytes(b"changed")
    else:
        invalidate_restored_deliveries()
        assert not (tmp_path / row.object_name).exists()
    with pytest.raises(Http404):
        authorize_token(path.rsplit("/", 1)[1])
    row.refresh_from_db()
    assert row.consumed_at is None


def test_internal_auth_head_range_and_no_secret_are_denied_without_consumption(
    request, settings, tmp_path
):
    _, _, _, path, row, _ = staged(request, settings, tmp_path)
    client = Client()
    base = {
        "HTTP_X_RIGHTS_PROXY": settings.RIGHTS_DELIVERY_PROXY_SECRET,
        "HTTP_X_FORWARDED_URI": path,
        "HTTP_X_FORWARDED_METHOD": "GET",
    }
    assert (
        client.get(
            "/internal/rights-objects/authorize/", **{**base, "HTTP_X_RIGHTS_PROXY": "bad"}
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/internal/rights-objects/authorize/", **{**base, "HTTP_X_FORWARDED_METHOD": "HEAD"}
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/internal/rights-objects/authorize/",
            **{**base, "HTTP_X_FORWARDED_RANGE": "bytes=0-10"},
        ).status_code
        == 404
    )
    row.refresh_from_db()
    assert row.consumed_at is None
    assert client.get("/internal/rights-objects/authorize/", **base).status_code == 200


def test_concurrent_requests_only_one_consumes_pg_grant(request, settings, tmp_path):
    _, _, _, path, _, _ = staged(request, settings, tmp_path)

    def consume():
        close_old_connections()
        try:
            authorize_token(path.rsplit("/", 1)[1])
            return 200
        except Http404:
            return 404
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: consume(), range(2))) == [200, 404]
    assert RightsExportDownload.objects.count() == 1


def test_expiry_worker_removes_bytes_keeps_audit_and_orphan_cleanup(request, settings, tmp_path):
    _, _, _, _, row, _ = staged(request, settings, tmp_path)
    RightsObjectDelivery.objects.filter(pk=row.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    orphan = tmp_path / uuid4().hex
    orphan.write_bytes(b"orphaned synthetic private bytes")
    old = timezone.now().timestamp() - 60
    os.utime(orphan, (old, old))
    assert purge_object_deliveries() == 1
    assert purge_object_deliveries() == 0
    assert not (tmp_path / row.object_name).exists()
    assert not orphan.exists()
    assert (tmp_path / "private").exists()  # Preserve fixture media unrelated to delivery.
    assert RightsExportDownload.objects.count() == 1
    row.refresh_from_db()
    assert row.purged_at


def test_actual_caddy_serves_verified_bytes_and_blocks_replay_and_raw_path(
    request, settings, tmp_path
):
    _, _, _, path, row, content = staged(
        request, settings, tmp_path / "delivery", through_post=True
    )

    class QuietHandler(WSGIRequestHandler):
        def log_message(self, format, *args):
            pass

    server = make_server("0.0.0.0", 0, get_wsgi_application(), handler_class=QuietHandler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    config = tmp_path / "Caddyfile"
    config.write_text(
        Path("Caddyfile").read_text().replace("app:8000", f"app:{server.server_port}")
    )
    name = "web-modelos-caddy-test-" + uuid4().hex[:12]
    env = {**os.environ, "RIGHTS_DELIVERY_PROXY_SECRET": settings.RIGHTS_DELIVERY_PROXY_SECRET}
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--pull=never",
                "-d",
                "--name",
                name,
                "--label",
                "web-modelos-object-tests",
                "--cpus",
                "0.5",
                "--memory",
                "128m",
                "--memory-swap",
                "128m",
                "--log-driver",
                "none",
                "--add-host",
                "app:host-gateway",
                "-p",
                "127.0.0.1::80",
                "-v",
                f"{config}:/etc/caddy/Caddyfile:ro",
                "-v",
                f"{settings.RIGHTS_DELIVERY_ROOT}:/srv/delivery:ro",
                "-e",
                "RIGHTS_DELIVERY_PROXY_SECRET",
                "caddy:2-alpine",
            ],
            env=env,
            capture_output=True,
            check=True,
            timeout=30,
        )
        port = (
            subprocess.check_output(["docker", "port", name, "80"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        origin = f"http://127.0.0.1:{port}"
        # Wait for Caddy listener without consuming grant.
        import time

        for attempt in range(40):
            try:
                urllib.request.urlopen(origin + "/health/", timeout=1).close()
                break
            except (urllib.error.URLError, TimeoutError, ConnectionResetError):
                time.sleep(0.1)
        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(urllib.request.Request(origin + path, method="HEAD"), timeout=10)
        assert denied.value.code == 404
        with urllib.request.urlopen(origin + path, timeout=15) as delivered:
            assert delivered.read() == content
            assert "no-store" in delivered.headers["Cache-Control"]
            assert (
                delivered.headers["Content-Disposition"]
                == 'attachment; filename="rights-profile.json"'
            )
            assert delivered.headers["Content-Type"] == "application/json; charset=utf-8"
            assert "ETag" not in delivered.headers
        with pytest.raises(urllib.error.HTTPError) as replay:
            urllib.request.urlopen(origin + path, timeout=10)
        assert replay.value.code == 404
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(origin + "/private-deliveries/" + row.object_name, timeout=10)
        assert RightsExportDownload.objects.count() == 1
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", name], capture_output=True, timeout=30)
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        assert subprocess.run(["docker", "inspect", name], capture_output=True).returncode != 0


def test_actual_celery_worker_purges_expired_delivery(request, settings, tmp_path):
    import sys
    import time

    _, _, _, _, row, _ = staged(request, settings, tmp_path)
    RightsObjectDelivery.objects.filter(pk=row.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    module = tmp_path / "object_worker_settings.py"
    module.write_text(
        "from config.settings import *\n"
        + f"DATABASES['default']['NAME'] = {connections['default'].settings_dict['NAME']!r}\n"
        + f"RIGHTS_DELIVERY_ROOT = Path({str(tmp_path)!r})\n"
        + f"RIGHTS_DELIVERY_GENERATION = {settings.RIGHTS_DELIVERY_GENERATION!r}\n"
    )
    queue = "object-purge-" + uuid4().hex
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "object_worker_settings",
        "PYTHONPATH": str(tmp_path) + ":" + os.environ.get("PYTHONPATH", ""),
    }
    log = tmp_path / "worker.log"
    with log.open("wb") as output:
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "config",
                "worker",
                "--pool=solo",
                "--concurrency=1",
                "--loglevel=WARNING",
                "--without-gossip",
                "--without-mingle",
                "--without-heartbeat",
                "-Q",
                queue,
                "--hostname",
                queue,
            ],
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            purge_object_deliveries.apply_async(queue=queue)
            deadline = time.monotonic() + 30
            while True:
                row.refresh_from_db()
                if row.purged_at:
                    break
                if time.monotonic() > deadline or worker.poll() is not None:
                    pytest.fail("Real Celery purge did not finish: " + log.read_text()[-3000:])
                time.sleep(0.1)
            assert not (tmp_path / row.object_name).exists()
            assert RightsExportDownload.objects.count() == 1
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=5)
            assert worker.poll() is not None


def test_post_redirect_replay_retains_one_proxy_grant_and_direct_fallback(
    request, settings, tmp_path
):
    _, export, _, path, row, content = staged(request, settings, tmp_path, through_post=True)
    repeat = row._client.post(url(row._receipt, export), {"key": row.download.key})
    assert repeat.status_code == 303
    assert RightsObjectDelivery.objects.count() == RightsExportDownload.objects.count() == 1
    authorize_token(path.rsplit("/", 1)[1])
    replay = row._client.post(url(row._receipt, export), {"key": row.download.key})
    assert replay.status_code == 200 and replay.content == content
    assert RightsObjectDelivery.objects.count() == RightsExportDownload.objects.count() == 1


def test_export_purge_removes_proxy_plaintext_immediately_before_worker(
    request, settings, tmp_path
):
    from apps.safety.tasks import purge_expired_exports

    _, export, _, path, row, _ = staged(request, settings, tmp_path, through_post=True)
    RightsExport.objects.filter(pk=export.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_exports() == 1
    assert not (tmp_path / row.object_name).exists()
    row.refresh_from_db()
    assert row.purged_at is not None
    with pytest.raises(Http404):
        authorize_token(path.rsplit("/", 1)[1])


def test_grant_person_and_account_inventory_include_own_exclude_other_subject(
    request, settings, tmp_path
):
    from apps.core.models import User
    from apps.safety.account_erasure_inventory import source as account_source
    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest

    _, _, person, _, row, _ = staged(request, settings, tmp_path)
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    model = "safety.RightsObjectDelivery"

    def item(manifest):
        return next(entry for entry in manifest["entries"] if entry["model"] == model)

    assert item(source_manifest(person))["count"] == 1
    assert item(source_manifest(peer))["count"] == 0
    # Attribution of a recipient's own download activity to that account.
    RightsExportDownload.objects.filter(pk=row.download_id).update(actor=person.subject)
    with transaction.atomic():
        own = account_source(
            RightsRequest(account_subject=person.subject, actor=person.subject, kind="access")
        )
        other = account_source(
            RightsRequest(account_subject=peer.subject, actor=peer.subject, kind="access")
        )
    assert item(own)["count"] == 1 and item(other)["count"] == 0
    before = item(own)["state_digest"]
    RightsObjectDelivery.objects.filter(pk=row.pk).update(consumed_at=timezone.now())
    with transaction.atomic():
        changed = account_source(
            RightsRequest(account_subject=person.subject, actor=person.subject, kind="access")
        )
    assert item(changed)["state_digest"] != before
    assert row.object_name not in str(changed)
    assert User.objects.filter(pk=person.subject_id).exists()
