"""Real PostgreSQL/medium restore in a disposable database, with synthetic identities."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from cryptography.fernet import Fernet
from django.db import connection
from django.test import Client
from psycopg import sql
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken
from apps.listings.models import Revision
from apps.mediafiles.erasure import erase_due_media
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import canonical
from apps.safety.models import RecoveryOutbox
from apps.safety.recovery_ledger_export import export_batch
from apps.safety.recovery_ledger_producer import prepare_batch
from scripts.recovery_ledger import RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def media_inventory(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            with path.open("rb") as stream:
                result[path.relative_to(root).as_posix()] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
    return result


def postgres_command(tool, database):
    """Use the test connection's own server, never the normal Compose service."""
    db = connection.settings_dict
    container = os.environ.get("LOCAL_CI_POSTGRES_CONTAINER")
    if container:
        assert re.fullmatch(r"web-modelos-ci-pg-\d{8}-\d{6}-[0-9a-f]{8}", container)
        mapped = subprocess.check_output(["docker", "port", container, "5432"], text=True).strip()
        assert mapped == f"{db['HOST']}:{db['PORT']}"
        return ["docker", "exec", "-i", container, tool, "-U", db["USER"], "-d", database]
    assert shutil.which(tool), "Use local CI or install matching PostgreSQL client tools"
    return [tool, "-h", db["HOST"], "-p", str(db["PORT"]), "-U", db["USER"], "-d", database]


def postgres_environment():
    return os.environ | {"PGPASSWORD": connection.settings_dict["PASSWORD"]}


CHILD = r"""
import hashlib,json,sys,os
from pathlib import Path
os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
import django
django.setup()
from django.conf import settings
from django.test import Client,override_settings
from apps.core.models import User,Person,AccountToken,RecoveryCode
from apps.listings.models import Favorite,Revision,Listing,PublicationDirty,PublicationState
from apps.listings.publication_state import mark_all,refresh_all,all_state_current
from django.core.management import call_command
from django.db import connection
from apps.mediafiles.models import Blob
from apps.safety.erasure_inventory import canonical
from apps.safety.models import RecoveryApplication
from apps.safety.recovery_apply import reconcile
from apps.safety.recovery_media import destroy_due
from scripts.recovery_ledger import Checkpoint,RecoveryLedger,LedgerIntegrityError
from scripts.recovery_store import RecoveryStore
config=json.loads(sys.argv[1])
codec=RecoveryLedger(os.environ['RECOVERY_ENCRYPTION_KEY'].encode(),bytes.fromhex(os.environ['TEST_RECOVERY_SIGNING_HEX']))
start=Checkpoint(**config['start'])
expected=Checkpoint(**config['expected'])
assert expected.sequence > start.sequence
store=RecoveryStore(config['records'],config['authority'],codec,expected_checkpoint=expected)
with override_settings(MEDIA_ROOT=Path(config['media']),RECOVERY_MODE=True):
    subject=User.objects.get(pk=config['subject'])
    person=Person.objects.get(pk=config['person'])
    assert AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryApplication.objects.exists()
    for paths in config['paths']:
        assert Blob._meta.get_field('original').storage.exists(paths['original'])
        assert Blob._meta.get_field('derivative').storage.exists(paths['derivative'])
    assert Client().get('/en/').status_code==503
    refresh_all()
    assert PublicationState.objects.count()==Listing.objects.count()
    with connection.cursor() as cursor:
        cursor.execute('SET session_replication_role=replica')
        try:
            PublicationState.objects.update(eligible=True)
            PublicationDirty.objects.all().delete()
        finally:
            cursor.execute('SET session_replication_role=origin')
    assert not PublicationDirty.objects.exists()
    mark_all()
    assert set(PublicationDirty.objects.values_list('listing_id',flat=True))==set(Listing.objects.values_list('pk',flat=True))
    generation=PublicationDirty.objects.get(listing_id=person.listing.pk).generation
    wrong=RecoveryStore(config['records'],config['authority'],codec,expected_checkpoint=start)
    try:
        reconcile(wrong,start)
    except LedgerIntegrityError:
        pass
    else:
        raise AssertionError('Independent rollback reference must reject recovery')
    assert not RecoveryApplication.objects.exists()
    assert AccountToken.objects.filter(user=subject).exists()
    for paths in config['paths']:
        assert Blob._meta.get_field('original').storage.exists(paths['original'])
        assert Blob._meta.get_field('derivative').storage.exists(paths['derivative'])
    result=reconcile(store,start)
    assert result['applied']==1 and result['publication_authorized'] is False
    assert PublicationDirty.objects.get(listing_id=person.listing.pk).generation>generation
    assert not AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryCode.objects.filter(user=subject).exists()
    assert not Favorite.objects.filter(user=subject).exists()
    assert Favorite.objects.filter(user_id=config['outsider']).exists()
    person.refresh_from_db();subject.refresh_from_db()
    assert not person.alias and person.listing.status=='withdrawn'
    assert not Revision.objects.filter(listing__person=person).exclude(description='').exists()
    assert subject.session_version>=config['minimum_session']
    assert destroy_due(store,start)>=1
    for paths in config['paths']:
        assert not Blob._meta.get_field('original').storage.exists(paths['original'])
        assert not Blob._meta.get_field('derivative').storage.exists(paths['derivative'])

    deleted={paths[name] for paths in config['paths'] for name in ('original','derivative')}
    expected_media={path:digest for path,digest in config['media_manifest'].items() if path not in deleted}
    actual_media={}
    for path in sorted(Path(config['media']).rglob('*')):
        if path.is_file():
            with path.open('rb') as stream:
                actual_media[path.relative_to(config['media']).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
    assert actual_media==expected_media
    peer=list(Revision.objects.filter(listing__person_id=config['peer']).order_by('pk').values())
    assert hashlib.sha256(canonical(peer).encode()).hexdigest()==config['peer_digest']
    assert reconcile(store,start)['applied']==0
    assert destroy_due(store,start)==0
    call_command("refresh_publication_state", all=True)
    assert not PublicationDirty.objects.exists() and all_state_current()
    assert PublicationState.objects.get(listing_id=person.listing.pk).eligible is False
    with override_settings(RECOVERY_MODE=False):
        client=Client();client.cookies[settings.SESSION_COOKIE_NAME]=config['old_session']
        response=client.get('/en/')
        assert not response.wsgi_request.user.is_authenticated
        assert client.get('/en/listing/'+str(person.listing.pk)+'/').status_code==404
    print(json.dumps({'independent_authority_verified':True,'wrong_authority_rejected_without_effects':True,'real_restore':True,'effects_applied':True,'media_deleted':True,'peer_preserved':True,'old_session_rejected':True,'replay_idempotent':True,'publication_authorized':False}))
"""


def test_old_pg_dump_and_media_cannot_reintroduce_erased_data(
    request, settings, monkeypatch, tmp_path, record_property
):
    purposes = [
        "authentication",
        "account_preferences",
        "transient_copy",
        "media",
        "publication",
        "profile",
    ]
    case, actor, staff, client, receipt, person, plan, export, image, outsider = plan_fixture(
        request, settings, monkeypatch, selected_purposes=purposes
    )
    subject = person.subject
    from apps.core.models import Person

    peer = Person.objects.exclude(pk=person.pk).first()
    peer_rows = list(Revision.objects.filter(listing__person=peer).order_by("pk").values())
    old_client = Client()
    old_client.force_login(subject)
    session = old_client.session
    session["account_version"] = subject.session_version
    session.save()
    old_session = session.session_key
    source_database = connection.settings_dict["NAME"]
    assert source_database.startswith("test_")
    assert AccountToken.objects.filter(user=subject).exists()
    records, authority = tmp_path / "records", tmp_path / "authority"
    records.mkdir(mode=0o700)
    authority.mkdir(mode=0o700)
    encryption, signing = Fernet.generate_key(), b"z" * 32
    codec = RecoveryLedger(encryption, signing)
    start, _ = prepare_batch(codec)
    store = RecoveryStore(records, authority, codec)
    store.initialize(start)
    backup = tmp_path / "synthetic-before-erasure.dump"
    backup_media = tmp_path / "backup-media"
    backup_cutoff = time.time()
    backup_started = time.monotonic()
    media_manifest = media_inventory(settings.MEDIA_ROOT)
    shutil.copytree(settings.MEDIA_ROOT, backup_media)
    assert media_inventory(backup_media) == media_manifest
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        subprocess.run(
            postgres_command("pg_dump", source_database) + ["-Fc", "--no-owner", "--no-acl"],
            env=postgres_environment(),
            timeout=120,
            stdout=output,
            stderr=subprocess.PIPE,
            check=True,
        )
    backup_seconds = time.monotonic() - backup_started
    backup_sha256 = hashlib.sha256(backup.read_bytes()).hexdigest()
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": purposes}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    assert export_batch(store) == 1
    assert erase_due_media() >= 1
    restored_at = time.monotonic()
    restored_media = tmp_path / "restored-media"
    shutil.copytree(backup_media, restored_media)
    assert media_inventory(restored_media) == media_manifest
    database = "recovery_restore_" + uuid4().hex[:12]
    db = connection.settings_dict
    admin = psycopg.connect(
        dbname="postgres",
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        autocommit=True,
    )
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    try:
        subprocess.run(
            postgres_command("pg_restore", database)
            + ["--no-owner", "--no-acl", "--exit-on-error"],
            env=postgres_environment(),
            timeout=120,
            input=backup.read_bytes(),
            capture_output=True,
            check=True,
        )
        expected = store.checkpoint()
        config = {
            "expected": {
                "ledger": expected.ledger,
                "sequence": expected.sequence,
                "head": expected.head,
            },
            "records": str(records),
            "authority": str(authority),
            "start": {"ledger": start.ledger, "sequence": start.sequence, "head": start.head},
            "media": str(restored_media),
            "media_manifest": media_manifest,
            "subject": subject.pk,
            "person": str(person.pk),
            "peer": str(peer.pk),
            "peer_digest": hashlib.sha256(canonical(peer_rows).encode()).hexdigest(),
            "outsider": outsider.pk,
            "old_session": old_session,
            "minimum_session": event["references"]["account"]["minimum_session_version"],
            "paths": [item["paths"] for item in event["references"]["media_jobs"]],
        }
        environment = os.environ.copy()
        environment.update(
            POSTGRES_DB=database,
            DB_HOST=db["HOST"],
            DB_PORT=str(db["PORT"]),
            POSTGRES_USER=db["USER"],
            POSTGRES_PASSWORD=db["PASSWORD"],
            DJANGO_SECRET_KEY=settings.SECRET_KEY,
            SAFETY_ENCRYPTION_KEY=settings.SAFETY_ENCRYPTION_KEY,
            RECOVERY_MODE="1",
            RECOVERY_ENCRYPTION_KEY=encryption.decode(),
            TEST_RECOVERY_SIGNING_HEX=signing.hex(),
        )
        result = subprocess.run(
            [sys.executable, "-c", CHILD, json.dumps(config)],
            env=environment,
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stderr[-4000:]
        proof = json.loads(result.stdout.strip().splitlines()[-1])
        assert proof["real_restore"] and not proof["publication_authorized"]
        assert proof["independent_authority_verified"]
        assert proof["wrong_authority_rejected_without_effects"]
        proof.update(
            backup_bytes=backup.stat().st_size,
            backup_sha256=backup_sha256,
            backup_cutoff_unix=backup_cutoff,
            backup_media_manifest=canonical(media_manifest),
            media_manifest_sha256=hashlib.sha256(canonical(media_manifest).encode()).hexdigest(),
            restored_media_integrity_verified=True,
            backup_seconds=backup_seconds,
            restore_and_reconcile_seconds=time.monotonic() - restored_at,
            backup_age_upper_bound_seconds=time.time() - backup_cutoff,
            mod05_stale_state_invalidated=True,
            mod05_restored_triggers_active=True,
            mod05_required_refresh_command_verified=True,
        )
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == backup_sha256
        assert proof["restore_and_reconcile_seconds"] <= 28800
        assert proof["backup_age_upper_bound_seconds"] <= 3600
        for name, value in proof.items():
            record_property(name, value)
        (tmp_path / "restore-result.json").write_text(json.dumps(proof))
    finally:
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
        assert not admin.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", (database,)
        ).fetchone()
        record_property("restored_database_name", database)
        record_property("restored_database_removed", True)
        admin.close()
