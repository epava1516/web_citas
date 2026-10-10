"""Actual approved-state diagnostic snapshots, consumed by the diagnostic profile.

Native PostgreSQL COPY and original media bytes; no fabricated approvals.
"""
import hashlib
import os
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import psycopg
from capacity_runtime_role import _owned_database
from django.conf import settings
from django.db import connection, connections, transaction
from django.test import override_settings
from django.utils import timezone
from psycopg import sql

from apps.core.models import User
from apps.safety.evidence_chain import _runtime_is_trusted, configure_role, validate_chain
from apps.safety.evidence_chain_sql_v1 import TABLES
from apps.safety.models import (
    RightsPortabilityCoverageReview,
    RightsPortabilitySelectionReview,
    RightsRequest,
)
from apps.safety.rights_portability_coverage_use import consume_approved_coverage

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 'mod08-approved-diagnostic-v1'


def codec():
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import diagnostic_baseline_codec
    return diagnostic_baseline_codec


def policy():
    source = hashlib.sha256()
    for folder in ('apps', 'config', 'scripts', 'tests'):
        for path in sorted((ROOT / folder).rglob('*.py')):
            source.update(str(path.relative_to(ROOT)).encode())
            source.update(path.read_bytes())
    # Transport varies across owned runs; these exact exclusions never cover
    # domain policies, cryptographic material or authority/session settings.
    excluded = {'DATABASES', 'MEDIA_ROOT', 'SETTINGS_MODULE', 'BASE_DIR', 'RIGHTS_DELIVERY_GENERATION'}
    values = [(name, repr(getattr(settings, name))) for name in dir(settings)
              if name.isupper() and name not in excluded and not name.startswith('CAPACITY_')]
    config = hashlib.sha256(repr(sorted(values)).encode()).hexdigest()
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position")
        schema_data = cursor.fetchall()
        cursor.execute("SELECT pg_get_functiondef(p.oid) FROM pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.prokind IN ('f','p') ORDER BY p.proname,p.oid::regprocedure::text")
        schema_data.extend(cursor.fetchall())
        cursor.execute("SELECT c.relname,t.tgname,pg_get_triggerdef(t.oid),t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal ORDER BY c.relname,t.tgname")
        schema_data.extend(cursor.fetchall())
        cursor.execute("SELECT c.relname,k.conname,pg_get_constraintdef(k.oid) FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid WHERE c.relnamespace='public'::regnamespace ORDER BY c.relname,k.conname")
        schema_data.extend(cursor.fetchall())
        schema = hashlib.sha256(repr(schema_data).encode()).hexdigest()
        cursor.execute('SHOW server_version')
        version = cursor.fetchone()[0]
    return {'code': source.hexdigest(), 'config': config, 'schema': schema, 'postgres': version}


def _guard():
    _owned_database()
    connections.close_all()
    config = connection.settings_dict
    with psycopg.connect(dbname='postgres', user=config['USER'], password=config['PASSWORD'],
                         host=config['HOST'], port=config['PORT'], autocommit=True) as admin:
        with admin.cursor() as cursor:
            cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s', [config['NAME']])
            if cursor.fetchone()[0]:
                raise ValueError('Baseline database occupied; no backends terminated')
    return config


def _object_inventory():
    from apps.safety.object_storage.factory import repository
    repo = repository()
    repo.validate_bucket()
    found = []
    for page in repo.client.get_paginator('list_objects_v2').paginate(Bucket=repo.bucket):
        found.extend(item['Key'] for item in page.get('Contents', []))
    # This boundary is before generation; exported objects/deliveries are forbidden.
    if found:
        raise ValueError('Pre-generation baseline S3 namespace is not empty')
    return {'bucket': repo.bucket, 'keys': [], 'keyring': settings.RIGHTS_OBJECT_KEYS,
            'active_key': settings.RIGHTS_OBJECT_ACTIVE_KEY}


def capture(descriptor, destination, key_file):
    _guard()
    case = RightsRequest.objects.get(pk=descriptor['case'])
    coverage = RightsPortabilityCoverageReview.objects.select_related('coverage__proof', 'coverage__selection_review__selection__assessment_review__assessment').get(pk=descriptor['coverage_review'])
    row, selection = coverage.coverage, coverage.coverage.selection_review.selection
    from apps.safety.rights_exports import reviewer_case, source_copy
    from apps.safety.rights_portability_coverage_read_gate import required_pages
    with transaction.atomic():
        locked, person, listing = reviewer_case(User.objects.get(pk=descriptor['author']), case.pk)
        source = source_copy(person, listing, locked)
    if len(coverage.read_ids) != len(required_pages(source)):
        raise ValueError('Baseline capture did not complete all original target readings')
    expiry = min(case.receipt_expires_at, row.expires_at, selection.expires_at,
                 selection.assessment_review.assessment.expires_at, row.proof.expires_at)
    if expiry <= timezone.now():
        raise ValueError('Baseline original evidence already expired')
    # A captured baseline is a pre-generation state, never a exported authority ticket.
    from django.apps import apps
    for model in apps.get_app_config('safety').get_models():
        if model.__name__ in ('RightsExport', 'RightsPortabilityExportJob', 'RightsExportValidationSeal', 'RightsObjectDelivery') and model.objects.exists():
            raise ValueError('Baseline contains generated export/job/seal/delivery')
    with transaction.atomic():
        validate_chain(case)
        consume_approved_coverage(User.objects.get(pk=descriptor['author']), case.pk,
                                  case.version, descriptor['coverage_review'], uuid4(),
                                  'Revalidate real approved evidence before diagnostic capture')
        transaction.set_rollback(True)
    manifest = {'format': FORMAT, 'policy': policy(), 'descriptor': descriptor,
                'valid_until': expiry.isoformat(), 'objects': _object_inventory()}
    with tempfile.TemporaryDirectory(prefix='baseline-capture-', dir='/tmp') as temporary:
        root = Path(temporary)
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            tables = [item[0] for item in cursor.fetchall()]
        manifest['tables'] = tables
        manifest['hashes'] = {}
        with transaction.atomic(), connection.connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            for table in tables:
                file = root / (table + '.copy')
                with file.open('wb') as target, cursor.copy(sql.SQL('COPY public.{} TO STDOUT').format(sql.Identifier(table))) as copy:
                    for block in copy:
                        target.write(block)
                manifest['hashes'][file.name] = _hash(file)
            cursor.execute("SELECT sequencename,last_value FROM pg_sequences WHERE schemaname='public'")
            manifest['sequences'] = cursor.fetchall()
        media = Path(settings.MEDIA_ROOT)
        paths = [path for path in media.rglob('*') if path.is_file()]
        for path in paths:
            if path.is_symlink():
                raise ValueError('Baseline media symlink forbidden')
            manifest['hashes']['media/' + str(path.relative_to(media))] = _hash(path)
        tar = root / 'payload.tar.gz'
        plaintext_bytes = sum((root / (table + '.copy')).stat().st_size for table in tables) + sum(path.stat().st_size for path in paths)
        if plaintext_bytes > codec().PLAINTEXT_LIMIT:
            raise ValueError('Baseline plaintext exceeds512MiB quota')
        with tarfile.open(tar, 'w:gz') as archive:
            for table in tables:
                archive.add(root / (table + '.copy'), arcname=table + '.copy')
            for path in paths:
                archive.add(path, arcname='media/' + str(path.relative_to(media)))
        with tar.open('rb') as source, open(destination, 'wb') as target:
            os.chmod(destination, 0o600)
            codec().encode(source, target, manifest, codec().key(key_file))
    return {'event': 'BASELINE_CAPTURED_DIAGNOSTIC_ONLY', 'bytes': Path(destination).stat().st_size}


def _hash(path):
    value = hashlib.sha256()
    with open(path, 'rb') as file:
        while block := file.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def restore(source_file, key_file):
    config = _guard()
    from directory_snapshot import _empty_fixture_database
    if not _empty_fixture_database():
        raise ValueError('Baseline restore would overwrite existing current test authority/setup')
    with tempfile.TemporaryDirectory(prefix='baseline-restore-', dir='/tmp') as temporary:
        root = Path(temporary)
        payload = root / 'payload.tar.gz'
        codec()
        from diagnostic_baseline_archive import Reader
        with Reader(source_file) as source, payload.open('wb') as target:
            manifest = codec().decode(source, target, codec().key(key_file))
        if manifest['format'] != FORMAT or manifest['policy'] != policy():
            raise ValueError('Baseline code/config/schema/keyversion changed')
        cutoff = datetime.fromisoformat(manifest['valid_until'])
        if cutoff.tzinfo is None or timezone.now() >= cutoff:
            raise ValueError('Baseline original evidence expired')
        objects = _object_inventory()
        if objects != manifest['objects']:
            raise ValueError('Baseline object keyring/namespace changed')
        with tarfile.open(payload, 'r:gz') as archive:
            names, extracted_bytes = set(), 0
            for member in archive:
                path = Path(member.name)
                if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name not in manifest['hashes'] or member.name in names:
                    raise ValueError('Baseline archive entry invalid')
                extracted_bytes += member.size
                if extracted_bytes > codec().PLAINTEXT_LIMIT:
                    raise ValueError('Baseline plaintext exceeds quota')
                names.add(member.name)
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as stream, destination.open('wb') as output:
                    shutil.copyfileobj(stream, output, 1024 * 1024)
                if _hash(destination) != manifest['hashes'][member.name]:
                    raise ValueError('Baseline data integrity changed')
            if names != set(manifest['hashes']):
                raise ValueError('Baseline members missing')
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            if manifest['tables'] != [item[0] for item in cursor.fetchall()]:
                raise ValueError('Baseline table set changed')
        # Scratch DB is a clone of the empty/current worker schema, never a normal DB.
        media = Path(settings.MEDIA_ROOT)
        media.parent.mkdir(parents=True, exist_ok=True)
        staged_media = Path(tempfile.mkdtemp(prefix='baseline-media-', dir=media.parent))
        shutil.rmtree(staged_media)
        shutil.copytree(root / 'media', staged_media)
        media_backup = staged_media.with_name(staged_media.name + '-previous')
        scratch = config['NAME'] + '_baseline_' + uuid4().hex[:8]
        database_backup = config['NAME'] + '_previous_' + uuid4().hex[:8]
        original_database = config['NAME']
        connections.close_all()
        with psycopg.connect(dbname='postgres', user=config['USER'], password=config['PASSWORD'],
                             host=config['HOST'], port=config['PORT'], autocommit=True) as admin:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(scratch), sql.Identifier(config['NAME'])))
            try:
                with psycopg.connect(dbname=scratch, user=config['USER'], password=config['PASSWORD'], host=config['HOST'], port=config['PORT']) as copied:
                    with copied.cursor() as cursor:
                        tables = manifest['tables']
                        cursor.execute(sql.SQL('TRUNCATE {} RESTART IDENTITY CASCADE').format(sql.SQL(',').join(sql.Identifier('public', table) for table in tables)))
                        cursor.execute('SET CONSTRAINTS ALL DEFERRED')
                        for table in TABLES:
                            cursor.execute(sql.SQL('ALTER TABLE public.{} DISABLE TRIGGER rights_evidence_record').format(sql.Identifier(table)))
                        for table in tables:
                            with cursor.copy(sql.SQL('COPY public.{} FROM STDIN').format(sql.Identifier(table))) as copy, (root / (table + '.copy')).open('rb') as file:
                                while block := file.read(1024 * 1024):
                                    copy.write(block)
                        for name, value in manifest['sequences']:
                            if value is not None:
                                cursor.execute('SELECT setval(%s,%s,true)', ['public.' + name, value])
                        for table in TABLES:
                            cursor.execute(sql.SQL('ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_record').format(sql.Identifier(table)))
                # Full validation in scratch under a real restricted role; rollback
                # audit intents so validation does not fabricate approved evidence.
                config['NAME'] = scratch
                role = 'baseline_check_' + uuid4().hex[:16]
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql.SQL('CREATE ROLE {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT').format(sql.Identifier(role)))
                        cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
                        cursor.execute(sql.SQL('GRANT ALL ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(role)))
                        cursor.execute(sql.SQL('GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(role)))
                    configure_role(role)
                    with override_settings(MEDIA_ROOT=str(staged_media)), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
                        if not _runtime_is_trusted(cursor):
                            raise ValueError('Fresh diagnostic runtime ACL/trigger trust rejected')
                        descriptor = manifest['descriptor']
                        user = User.objects.get(pk=descriptor['author'])
                        case = RightsRequest.objects.get(pk=descriptor['case'])
                        restored_review = RightsPortabilityCoverageReview.objects.select_related('coverage__proof', 'coverage__selection_review__selection__assessment_review__assessment').get(pk=descriptor['coverage_review'])
                        restored_selection = restored_review.coverage.selection_review.selection
                        original_limit = min(case.receipt_expires_at, restored_review.coverage.expires_at,
                                             restored_selection.expires_at,
                                             restored_selection.assessment_review.assessment.expires_at,
                                             restored_review.coverage.proof.expires_at)
                        if original_limit != cutoff or original_limit <= timezone.now():
                            raise ValueError('Baseline original expirations changed')
                        validate_chain(case)
                        consume_approved_coverage(user, case.pk, case.version, descriptor['coverage_review'], uuid4(), 'Revalidate original diagnostic baseline authority and evidence')
                        transaction.set_rollback(True)
                finally:
                    with connection.cursor() as cursor:
                        cursor.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
                        cursor.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
                    connections.close_all()
                    config['NAME'] = original_database
                # Adopt only after every check. Zero external connections checked
                # again, and scratch is renamed to the exact owned worker name.
                _guard()
                adopted_database = False
                previous_media = False
                try:
                    with admin.cursor() as cursor:
                        cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(config['NAME']), sql.Identifier(database_backup)))
                        try:
                            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(scratch), sql.Identifier(config['NAME'])))
                        except Exception:
                            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(database_backup), sql.Identifier(config['NAME'])))
                            raise
                    adopted_database = True
                    if media.exists():
                        os.replace(media, media_backup)
                        previous_media = True
                    os.replace(staged_media, media)
                except Exception as error:
                    if previous_media:
                        os.replace(media_backup, media)
                    if adopted_database:
                        with admin.cursor() as cursor:
                            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(config['NAME']), sql.Identifier(scratch)))
                            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(database_backup), sql.Identifier(config['NAME'])))
                    raise ValueError('Baseline adoption rejected; original empty database/media restored') from error
                with admin.cursor() as cursor:
                    cursor.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(database_backup)))
                if previous_media:
                    shutil.rmtree(media_backup)
                return manifest['descriptor']
            finally:
                if staged_media.exists():
                    shutil.rmtree(staged_media)
                with admin.cursor() as cursor:
                    cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', [scratch])
                    if cursor.fetchone():
                        cursor.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(scratch)))


def resume(descriptor, endpoint, configuration, metrics):
    from threading import Barrier

    from capacity_delivery_flow import finish

    from apps.safety.crypto import unseal
    from apps.safety.rights_exports import reviewer_case, source_copy
    from apps.safety.rights_portability_selection import project_selected

    case = RightsRequest.objects.get(pk=descriptor["case"])
    author, reviewer = (User.objects.get(pk=descriptor[name]) for name in ("author", "reviewer"))
    selected = RightsPortabilitySelectionReview.objects.select_related("selection__assessment_review__assessment").get(pk=descriptor["selection_review"])
    coverage = RightsPortabilityCoverageReview.objects.get(pk=descriptor["coverage_review"])
    selection = selected.selection
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    facts = unseal(selection.encrypted_selection)
    expected = project_selected(source, unseal(selection.assessment_review.assessment.encrypted_assessment),
                                facts["selection"], field_evidence=facts.get("field_evidence"))
    metrics["diagnostic"] = True
    finish(0, case, author, reviewer, selection, selected, coverage,
           descriptor["receipt"], endpoint, configuration, Barrier(1), metrics, expected)
