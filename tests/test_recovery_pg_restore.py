"""Real PostgreSQL/medium restore in a disposable database, with synthetic identities."""

import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pyotp
import pytest
from cryptography.fernet import Fernet, InvalidToken
from django.contrib.sessions.models import Session
from django.db import connection, transaction
from django.test import Client
from psycopg import sql
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy as access_copy
from test_rights_exports import prepared as access_prepared
from test_rights_exports import url as access_url

from apps.core.mfa import encrypt as encrypt_mfa
from apps.core.models import AccountToken, Person
from apps.listings.models import Revision
from apps.mediafiles.erasure import erase_due_media
from apps.safety.crypto import digest, unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import canonical
from apps.safety.models import RecoveryOutbox, RightsExportDownload
from apps.safety.recovery_ledger_export import export_batch
from apps.safety.recovery_ledger_producer import prepare_batch
from apps.safety.rights import fingerprint
from apps.safety.rights_object_delivery import stage_delivery
from apps.safety.rights_object_models import RightsObjectDelivery
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
import hashlib,json,sys,os,io
from pathlib import Path
os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
import django
django.setup()
from django.conf import settings
from django.test import Client,override_settings
from django.contrib.sessions.models import Session
from apps.core.models import User,Person,AccountToken,RecoveryCode
from apps.core.mfa import decrypt as decrypt_mfa
from apps.safety.crypto import digest, unseal
from apps.listings.profile_contract import CURRENT_CONTRACT
from apps.safety.rights import fingerprint
from apps.safety.rights_object_models import RightsObjectDelivery
from apps.listings.models import Favorite,Revision,Listing,PublicationDirty,PublicationState
from apps.listings.publication_state import mark_all,refresh_all,all_state_current
from django.core.management import call_command
from django.db import connection
from apps.mediafiles.models import Blob
from apps.safety.erasure_inventory import canonical
from apps.safety.models import RecoveryApplication,RightsExport,RightsExportImage,RightsExportPart
from apps.safety.recovery_apply import reconcile
from apps.safety.recovery_media import destroy_due
from scripts.recovery_ledger import Checkpoint,RecoveryLedger,LedgerIntegrityError
from scripts.recovery_store import RecoveryStore
config=json.loads(sys.argv[1])
assert settings.MEDIA_STORAGE_PROVIDER=='local' and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
assert settings.TASK_QUEUE_GENERATION==config['fresh_queue_generation']
assert settings.TASK_QUEUE_GENERATION!=config['old_queue_generation']
assert bool(settings.SAFETY_ENCRYPTION_KEY_FALLBACKS)==config['key_transition']
assert bool(settings.MFA_ENCRYPTION_KEY_FALLBACKS)==config['key_transition']
assert bool(settings.SAFETY_HMAC_KEY)==config['key_transition']
if config['key_transition']:assert settings.SAFETY_HMAC_KEY!=settings.SECRET_KEY
assert digest('synthetic-restore-domain-witness')==config['domain_witness']['report']
assert fingerprint('synthetic-restore-domain-witness')==config['domain_witness']['rights']

# A dump/restore after corrective0022 must preserve the current conservative
# invalidation definitions, not just django_migrations rows or trigger names.
from importlib import import_module
base=import_module('apps.listings.migrations.0015_publication_state')
current=import_module('apps.listings.migrations.0020_publication_match_counterparts')
rejected=import_module('apps.listings.migrations.0021_private_draft_publication_dependencies')
with connection.cursor() as cursor:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM django_migrations WHERE app='listings' AND name='0022_restore_conservative_publication_invalidation')")
    assert cursor.fetchone()[0]
    cursor.execute("SELECT to_regprocedure('listings_publication_private_draft(uuid)'),to_regprocedure('listings_publication_lock(uuid[])')")
    assert cursor.fetchone()==(None,None)
    definitions={'listings_publication_mark(uuid[])':current.MARK}
    definitions.update({f'lpd_{table}()':base.trigger_sql(table,base.DEPENDENCIES[table])[0] for table in rejected.TRIGGERS})
    for name,source in definitions.items():
        cursor.execute('SELECT prosrc FROM pg_proc WHERE oid=%s::regprocedure',[name])
        assert cursor.fetchone()[0]==source.split('$$')[1]
codec=RecoveryLedger(os.environ['RECOVERY_ENCRYPTION_KEY'].encode(),bytes.fromhex(os.environ['TEST_RECOVERY_SIGNING_HEX']))
start=Checkpoint(**config['start'])
expected=Checkpoint(**config['expected'])
assert expected.sequence > start.sequence
store=RecoveryStore(config['records'],config['authority'],codec,expected_checkpoint=expected)
with override_settings(MEDIA_ROOT=Path(config['media']),RIGHTS_DELIVERY_ROOT=Path(config['media'])/'delivery-cache',RECOVERY_MODE=True):
    subject=User.objects.get(pk=config['subject'])
    person=Person.objects.get(pk=config['person'])
    assert AccountToken.objects.filter(user=subject).exists()
    peer_person=Person.objects.get(pk=config['peer'])
    assert hashlib.sha256(decrypt_mfa(peer_person.subject.mfa_secret_encrypted).encode()).hexdigest()==config['peer_seed_digest']
    cached=RightsObjectDelivery.objects.get(pk=config['peer_delivery'])
    assert cached.purged_at is None and cached.consumed_at is None
    cache_path=Path(settings.RIGHTS_DELIVERY_ROOT)/cached.object_name
    assert cache_path.is_file()

    assert not RecoveryApplication.objects.exists()
    restored_export=RightsExport.objects.get(pk=config['export'])
    export_audit=(restored_export.action_id,restored_export.proof_id)
    assert restored_export.encrypted_payload and restored_export.purged_at is None
    assert unseal(restored_export.encrypted_payload)=={'synthetic_snapshot':True}
    restored_images=list(RightsExportImage.objects.filter(export=restored_export).values_list('pk',flat=True))
    restored_parts=list(RightsExportPart.objects.filter(export=restored_export).values_list('pk',flat=True))
    assert restored_images and restored_parts
    assert all(RightsExportImage.objects.get(pk=pk).encrypted_content for pk in restored_images)
    assert all(RightsExportPart.objects.get(pk=pk).encrypted_content for pk in restored_parts)
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
    assert not PublicationState.objects.filter(listing_id=person.listing.pk).exists()
    restored_export.refresh_from_db()
    assert not restored_export.encrypted_payload and restored_export.purged_at is not None
    assert (restored_export.action_id,restored_export.proof_id)==export_audit
    assert set(RightsExportImage.objects.filter(export=restored_export).values_list('pk',flat=True))==set(restored_images)
    assert set(RightsExportPart.objects.filter(export=restored_export).values_list('pk',flat=True))==set(restored_parts)
    assert not RightsExportImage.objects.filter(pk__in=restored_images).exclude(encrypted_content='').exists()
    assert not RightsExportPart.objects.filter(pk__in=restored_parts).exclude(encrypted_content='').exists()
    assert subject.session_version>=config['minimum_session']
    # Finish the actual administrative command after the typed DB reconciliation.
    # Its replay must also invalidate unrelated restored grants and private bytes.
    output=io.StringIO()
    call_command('apply_recovery_ledger',records_directory=config['records'],checkpoint_directory=config['authority'],
                 backup_ledger=start.ledger,backup_sequence=start.sequence,backup_head=start.head,
                 expected_ledger=expected.ledger,expected_sequence=expected.sequence,expected_head=expected.head,
                 stdout=output)
    completed=json.loads(output.getvalue())
    assert completed['applied']==0 and completed['media_completed']>=1
    assert completed['publication_authorized'] is False
    cached.refresh_from_db()
    assert cached.purged_at is not None and not cache_path.exists()
    assert not RightsObjectDelivery.objects.filter(purged_at__isnull=True).exists()
    assert cached.download_id and cached.download.export.purged_at is None
    assert unseal(cached.download.export.encrypted_payload)
    assert destroy_due(store,start)==0

    for paths in config['paths']:
        assert not Blob._meta.get_field('original').storage.exists(paths['original'])
        assert not Blob._meta.get_field('derivative').storage.exists(paths['derivative'])

    deleted={paths[name] for paths in config['paths'] for name in ('original','derivative')}
    deleted.add(config['peer_cache_relative'])
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
    sessions_before=Session.objects.count()
    assert sessions_before>0
    session_output=io.StringIO()
    call_command('clear_recovery_sessions',records_directory=config['records'],checkpoint_directory=config['authority'],
                 backup_ledger=start.ledger,backup_sequence=start.sequence,backup_head=start.head,
                 expected_ledger=expected.ledger,expected_sequence=expected.sequence,expected_head=expected.head,
                 stdout=session_output)
    assert json.loads(session_output.getvalue())['sessions_deleted']==sessions_before
    assert not Session.objects.exists()

    assert PublicationState.objects.get(listing_id=person.listing.pk).eligible is False
    rebuilt=PublicationState.objects.get(listing_id=person.listing.pk)
    assert rebuilt.search_document is rebuilt.published_at is rebuilt.expires_at is None
    with override_settings(RECOVERY_MODE=False):
        client=Client();client.cookies[settings.SESSION_COOKIE_NAME]=config['old_session']
        response=client.get('/en/')
        assert not response.wsgi_request.user.is_authenticated
        assert client.get('/en/listing/'+str(person.listing.pk)+'/').status_code==404
        assert peer_person.listing.approved_revision.content_contract==CURRENT_CONTRACT
        assert client.get('/en/listing/'+str(peer_person.listing.pk)+'/').status_code==200
        receipt_response=Client().get(os.environ['TEST_RESTORE_PEER_RECEIPT'])
        assert receipt_response.status_code==200
        assert receipt_response['Cache-Control']=='private, no-store'
        assert client.get('/en/listing/'+str(person.listing.pk)+'/photo/'+config['erased_photo']+'/').status_code==404

    # RECOVERY_EXTENSION_ASSERTIONS
    print(json.dumps({'restored_transient_copy_cleared_audit_retained':True,'conservative_schema_restored':True,'rejected_helpers_absent':True,'independent_authority_verified':True,'wrong_authority_rejected_without_effects':True,'real_restore':True,'effects_applied':True,'media_deleted':True,'peer_preserved':True,'old_session_rejected':True,'replay_idempotent':True,'publication_authorized':False,'restored_grants_invalidated':True,'peer_export_audit_and_content_preserved':True,'fresh_queue_namespace':True,'retained_mfa_seed_readable':True,'peer_beta_profile_visible':True,'all_restored_sessions_destroyed':True,'domain_hmac_witness_preserved':True,'original_peer_receipt_accessible':True,'domain_key_pinned_after_signing_rotation':config['key_transition']}))
"""


@pytest.mark.parametrize("key_transition", [False, True], ids=["same-key", "retained-key-read"])
@pytest.mark.parametrize("encrypted_backup", [False, True], ids=["plain-local", "encrypted-local"])
def test_old_pg_dump_and_media_cannot_reintroduce_erased_data(
    request, settings, monkeypatch, tmp_path, record_property, encrypted_backup, key_transition
):
    # Every source key is synthetic and explicit before fixture creation.
    original_signing_key = 'synthetic-restore-original-signing-' + 'a' * 64
    settings.SECRET_KEY = original_signing_key
    settings.SECRET_KEY_FALLBACKS = []
    settings.SAFETY_HMAC_KEY = ''
    domain_witness = {'report': digest('synthetic-restore-domain-witness'),
                      'rights': fingerprint('synthetic-restore-domain-witness')}
    # Explicit independent cipher keys; no implicit dev-key transition.
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = ''
    settings.MFA_ENCRYPTION_KEY_FALLBACKS = ''
    request.getfixturevalue('directory')
    peer = Person.objects.get(subject__username='fixture-v1-individual')
    peer_seed = pyotp.random_base32()
    peer.subject.mfa_secret_encrypted = encrypt_mfa(peer_seed)
    peer.subject.save(update_fields=['mfa_secret_encrypted'])
    peer_case, peer_actor, _, peer_client, peer_receipt, _ = access_prepared(
        request, settings, subject_username=peer.subject.username)
    peer_export = access_copy(peer_case, peer_actor)
    response = peer_client.post(access_url(peer_receipt, peer_export), {'key': uuid4()})
    assert response.status_code == 200
    peer_download = RightsExportDownload.objects.get(export=peer_export)
    settings.RIGHTS_DELIVERY_ROOT = Path(settings.MEDIA_ROOT) / 'delivery-cache'
    settings.RIGHTS_DELIVERY_PROXY_SECRET = 'synthetic-restore-proxy-' + 's' * 40
    settings.RIGHTS_PROXY_DELIVERY_ENABLED = True
    with transaction.atomic():
        assert stage_delivery(peer_export, peer_download, response.content,
                              response['Content-Type'], 'synthetic-peer.json')
    settings.RIGHTS_PROXY_DELIVERY_ENABLED = False
    peer_delivery = RightsObjectDelivery.objects.get(download=peer_download)
    peer_cache = settings.RIGHTS_DELIVERY_ROOT / peer_delivery.object_name
    assert peer_cache.is_file() and peer_delivery.consumed_at is None
    peer_cache_relative = peer_cache.relative_to(settings.MEDIA_ROOT).as_posix()
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
    assert peer.pk != person.pk
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
    backup_sha256 = hashlib.sha256(backup.read_bytes()).hexdigest()
    encrypted_copy = None
    backup_cipher = None
    if encrypted_backup:
        # This bounded synthetic fixture encrypts the complete dump/media set.
        # The independent ledger and its keys are deliberately not in the copy.
        archive_bytes = io.BytesIO()
        with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
            archive.add(backup, arcname="database.dump")
            archive.add(backup_media, arcname="media")
        backup_cipher = Fernet(Fernet.generate_key())
        encrypted_copy = tmp_path / "complete-synthetic-backup.fernet"
        encrypted_fd = os.open(encrypted_copy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(encrypted_fd, "wb") as output:
            output.write(backup_cipher.encrypt(archive_bytes.getvalue()))
        backup.unlink()
        shutil.rmtree(backup_media)
        assert not backup.exists() and not backup_media.exists()
        assert encrypted_copy.stat().st_mode & 0o777 == 0o600
    backup_seconds = time.monotonic() - backup_started
    if key_transition:
        settings.SAFETY_HMAC_KEY = original_signing_key
        settings.SECRET_KEY = 'synthetic-restore-new-signing-' + 'b' * 64
        settings.SAFETY_ENCRYPTION_KEY_FALLBACKS = settings.SAFETY_ENCRYPTION_KEY
        settings.MFA_ENCRYPTION_KEY_FALLBACKS = settings.MFA_ENCRYPTION_KEY
        settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
        settings.MFA_ENCRYPTION_KEY = Fernet.generate_key().decode()
    assert digest('synthetic-restore-domain-witness') == domain_witness['report']
    assert fingerprint('synthetic-restore-domain-witness') == domain_witness['rights']
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": purposes}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    assert export_batch(store) == 1
    assert erase_due_media() >= 1
    restored_at = time.monotonic()
    if encrypted_backup:
        ciphertext = encrypted_copy.read_bytes()
        staging = tmp_path / "decrypted-backup"
        # Authentication failures must occur before materializing any files.
        with pytest.raises(InvalidToken):
            Fernet(Fernet.generate_key()).decrypt(ciphertext)
        altered = bytearray(ciphertext)
        altered[len(altered) // 2] = ord("A") if altered[len(altered) // 2] != ord("A") else ord("B")
        with pytest.raises(InvalidToken):
            backup_cipher.decrypt(bytes(altered))
        assert not staging.exists()
        plaintext = backup_cipher.decrypt(ciphertext)
        with tarfile.open(fileobj=io.BytesIO(plaintext), mode="r:") as archive:
            members = archive.getmembers()
            assert all(member.isfile() or member.isdir() for member in members)
            assert {member.name for member in members if member.isfile()} == {
                "database.dump", *{f"media/{name}" for name in media_manifest}
            }
            staging.mkdir(mode=0o700)
            archive.extractall(staging, filter="data")
        backup = staging / "database.dump"
        backup_media = staging / "media"
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == backup_sha256
        assert media_inventory(backup_media) == media_manifest
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
        fresh_generation = "r" + uuid4().hex[:31]
        config = {
            "fresh_queue_generation": fresh_generation,
            "old_queue_generation": settings.TASK_QUEUE_GENERATION,
            "key_transition": key_transition,
            "domain_witness": domain_witness,
            "peer_seed_digest": hashlib.sha256(peer_seed.encode()).hexdigest(),
            "peer_delivery": str(peer_delivery.pk),
            "peer_cache_relative": peer_cache_relative,
            "erased_photo": str(image.photo_id),
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
            "export": str(export.pk),
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
            SAFETY_HMAC_KEY=settings.SAFETY_HMAC_KEY,
            TEST_RESTORE_PEER_RECEIPT=peer_receipt,
            SAFETY_ENCRYPTION_KEY=settings.SAFETY_ENCRYPTION_KEY,
            SAFETY_ENCRYPTION_KEY_FALLBACKS=settings.SAFETY_ENCRYPTION_KEY_FALLBACKS,
            MFA_ENCRYPTION_KEY=settings.MFA_ENCRYPTION_KEY,
            MFA_ENCRYPTION_KEY_FALLBACKS=settings.MFA_ENCRYPTION_KEY_FALLBACKS,
            TASK_QUEUE_GENERATION=fresh_generation,
            RIGHTS_DELIVERY_GENERATION=settings.RIGHTS_DELIVERY_GENERATION,
            RIGHTS_PROXY_DELIVERY_ENABLED='0',
            MEDIA_STORAGE_PROVIDER='local',
            RIGHTS_OBJECT_STORAGE_ENABLED='0',
            RECOVERY_SIGNING_KEY=base64.urlsafe_b64encode(signing).decode(),
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
        assert proof['restored_grants_invalidated'] and proof['peer_export_audit_and_content_preserved']
        assert proof['fresh_queue_namespace'] and proof['retained_mfa_seed_readable'] and proof['peer_beta_profile_visible']
        assert proof['all_restored_sessions_destroyed']
        assert proof['domain_hmac_witness_preserved'] and proof['original_peer_receipt_accessible']
        assert proof['domain_key_pinned_after_signing_rotation'] is key_transition
        assert Session.objects.filter(session_key=old_session).exists()
        peer_delivery.refresh_from_db()
        assert peer_delivery.purged_at is None and peer_cache.is_file()
        proof.update(source_peer_cache_preserved=True, retained_key_transition=key_transition)
        assert proof["conservative_schema_restored"] and proof["rejected_helpers_absent"]
        assert proof["restored_transient_copy_cleared_audit_retained"]
        assert proof["independent_authority_verified"]
        assert proof["wrong_authority_rejected_without_effects"]
        proof.update(
            complete_backup_encrypted=encrypted_backup,
            encrypted_copy_bytes=encrypted_copy.stat().st_size if encrypted_backup else 0,
            encrypted_copy_sha256=(
                hashlib.sha256(encrypted_copy.read_bytes()).hexdigest() if encrypted_backup else ""
            ),
            invalid_backup_key_and_tampering_rejected=encrypted_backup,
            plaintext_backup_removed_before_recovery=encrypted_backup,
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
