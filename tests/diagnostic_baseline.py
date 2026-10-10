"""Actual approved-state diagnostic snapshots, consumed by the diagnostic profile.

Native PostgreSQL COPY and original media bytes; no fabricated approvals.
"""
import hashlib
import os
import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

import psycopg
from capacity_runtime_role import _owned_database
from django.conf import settings
from django.db import DatabaseError, connection, connections, transaction
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
    transport = {'NAME', 'HOST', 'PORT', 'USER', 'PASSWORD'}
    databases = {alias: {name: value for name, value in options.items() if name not in transport}
                 for alias, options in settings.DATABASES.items()}
    values.append(('DATABASES_NONTRANSPORT', repr(databases)))
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
        cursor.execute("SELECT c.relname,i.relname,pg_get_indexdef(k.indexrelid),k.indisvalid,k.indisready,k.indislive FROM pg_index k JOIN pg_class c ON c.oid=k.indrelid JOIN pg_class i ON i.oid=k.indexrelid WHERE c.relnamespace='public'::regnamespace ORDER BY c.relname,i.relname")
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


def _restore(source_file, key_file):
    config = _guard()
    from directory_snapshot import _empty_fixture_database
    if not _empty_fixture_database():
        raise ValueError('Baseline restore would overwrite existing current test authority/setup')
    with _private_stage('/tmp', 'baseline-restore-') as root:
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
        media = Path(settings.MEDIA_ROOT)
        media.parent.mkdir(parents=True, exist_ok=True)
        scratch = config['NAME'] + '_baseline_' + uuid4().hex[:8]
        backup = config['NAME'] + '_previous_' + uuid4().hex[:8]
        # Register filesystem cleanup before copy or CREATE can fail.
        with _private_stage(media.parent, 'baseline-media-') as stage:
            staged_media, previous_media = stage / 'media', stage / 'previous'
            if (root / 'media').exists():
                shutil.copytree(root / 'media', staged_media)
            else:
                staged_media.mkdir()
            connections.close_all()
            with _admin(config) as admin:
                create_attempted = False
                try:
                    with admin.cursor() as cursor:
                        cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', [scratch])
                        if cursor.fetchone():
                            raise ValueError('Diagnostic scratch name already exists')
                        create_attempted = True
                        _create_database(cursor, scratch, config['NAME'])
                    with _native(config, scratch) as copied:
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
                            # COPY does not restore PostgreSQL planner statistics.
                            for table in tables:
                                cursor.execute(sql.SQL('ANALYZE public.{}').format(sql.Identifier(table)))
                    with _fresh_login(config, scratch), override_settings(MEDIA_ROOT=str(staged_media)), transaction.atomic():
                        descriptor = manifest['descriptor']
                        user = User.objects.get(pk=descriptor['author'])
                        case = RightsRequest.objects.get(pk=descriptor['case'])
                        review = RightsPortabilityCoverageReview.objects.select_related('coverage__proof', 'coverage__selection_review__selection__assessment_review__assessment').get(pk=descriptor['coverage_review'])
                        selected = review.coverage.selection_review.selection
                        expiry = min(case.receipt_expires_at, review.coverage.expires_at, selected.expires_at,
                                     selected.assessment_review.assessment.expires_at, review.coverage.proof.expires_at)
                        if expiry != cutoff or expiry <= timezone.now():
                            raise ValueError('Baseline original expirations changed')
                        validate_chain(case)
                        consume_approved_coverage(user, case.pk, case.version, descriptor['coverage_review'], uuid4(), 'Revalidate original diagnostic baseline authority and evidence')
                        transaction.set_rollback(True)
                    _guard()
                    _adopt(admin, config['NAME'], scratch, backup, media, staged_media, previous_media)
                    return manifest['descriptor']
                finally:
                    connections.close_all()
                    if create_attempted:
                        _drop_scratch(admin, scratch)


class BaselineCleanupError(RuntimeError):
    """Cleanup/adoption not proved; must fail, never silently run fallback."""


def _native(config, name, autocommit=False):
    return psycopg.connect(dbname=name, user=config['USER'], password=config['PASSWORD'],
                           host=config['HOST'], port=config['PORT'], autocommit=autocommit)


def _admin(config):
    return _native(config, 'postgres', autocommit=True)


def _create_database(cursor, scratch, original):
    cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(scratch), sql.Identifier(original)))


def _create_login(cursor, role, secret):
    cursor.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT').format(sql.Identifier(role), sql.Literal(secret)))


@contextmanager
def _fresh_login(config, scratch):
    original = deepcopy(config)
    role, secret, create_attempted = 'baseline_check_' + uuid4().hex[:16], token_urlsafe(32), False
    try:
        # Password only travels through this private native connection, never
        # Django debug SQL, argv, environment, manifest or evidence output.
        with _native(original, scratch, autocommit=True) as owner:
            with owner.cursor() as cursor:
                # Suppress only this private migrator session's statement logs:
                # even an administrative DDL error must not emit its password.
                cursor.execute("SET log_statement='none'")
                cursor.execute('SET log_min_duration_statement=-1')
                cursor.execute("SET log_min_error_statement='panic'")
                cursor.execute('SET log_duration=off')
                cursor.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', [role])
                if cursor.fetchone():
                    raise ValueError('Diagnostic LOGIN name already exists')
                create_attempted = True
                _create_login(cursor, role, secret)
                cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
                cursor.execute(sql.SQL('GRANT ALL ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(role)))
                cursor.execute(sql.SQL('GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(role)))
        connections.close_all()
        config['NAME'] = scratch
        configure_role(role)
        connections.close_all()
        config.update(USER=role, PASSWORD=secret)
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_user,session_user,current_database(),rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user')
            if cursor.fetchone() != (role, role, scratch, True, False, False, False, False) or not _runtime_is_trusted(cursor):
                raise ValueError('Fresh actual diagnostic LOGIN trust rejected')
        yield
    finally:
        try:
            _restore_config(config, original)
        finally:
            try:
                if create_attempted:
                    try:
                        _drop_login(original, scratch, role)
                    except (psycopg.Error, OSError) as error:
                        raise BaselineCleanupError('Diagnostic LOGIN cleanup failed; fallback forbidden') from error
            finally:
                _restore_config(config, original)


def _drop_login(original, scratch, role):
    with _native(original, scratch, autocommit=True) as owner:
        with owner.cursor() as cursor:
            cursor.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', [role])
            if cursor.fetchone():
                cursor.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
                cursor.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
            cursor.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', [role])
            if cursor.fetchone():
                raise BaselineCleanupError('Diagnostic LOGIN cleanup not verified')


def _restore_config(config, original):
    try:
        connections.close_all()
    finally:
        config.clear()
        config.update(original)


@contextmanager
def _private_stage(directory, prefix):
    temporary = tempfile.TemporaryDirectory(prefix=prefix, dir=directory)
    root = Path(temporary.name)
    try:
        yield root
    finally:
        try:
            temporary.cleanup()
            if root.exists() or root.is_symlink():
                raise BaselineCleanupError('Diagnostic staging removal not verified')
        except OSError as error:
            raise BaselineCleanupError('Diagnostic staging cleanup failed; fallback forbidden') from error


def _drop_scratch(admin, scratch):
    try:
        with admin.cursor() as cursor:
            cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', [scratch])
            if cursor.fetchone():
                cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s', [scratch])
                if cursor.fetchone()[0]:
                    raise BaselineCleanupError('Diagnostic scratch occupied; no backends terminated')
                cursor.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(scratch)))
                cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', [scratch])
                if cursor.fetchone():
                    raise BaselineCleanupError('Diagnostic scratch deletion not verified')
    except psycopg.Error as error:
        raise BaselineCleanupError('Diagnostic scratch cleanup failed; fallback forbidden') from error


def _adopt(admin, original, scratch, backup, media, staged, previous):
    old_db, new_db, old_media, new_media = False, False, False, False
    try:
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(original), sql.Identifier(backup)))
            old_db = True
            cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(scratch), sql.Identifier(original)))
            new_db = True
        if media.exists():
            os.replace(media, previous)
            old_media = True
        os.replace(staged, media)
        new_media = True
    except Exception:
        try:
            if new_media:
                os.replace(media, staged)
            if old_media:
                os.replace(previous, media)
            with admin.cursor() as cursor:
                if new_db:
                    cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(original), sql.Identifier(scratch)))
                if old_db:
                    cursor.execute(sql.SQL('ALTER DATABASE {} RENAME TO {}').format(sql.Identifier(backup), sql.Identifier(original)))
        except Exception as error:
            raise BaselineCleanupError('Diagnostic adoption rollback failed; fallback forbidden') from error
        raise
    try:
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(backup)))
    except psycopg.Error as error:
        raise BaselineCleanupError('Diagnostic adoption backup cleanup failed; fallback forbidden') from error


def _media_state():
    media = Path(settings.MEDIA_ROOT)
    return media.exists(), {str(path.relative_to(media)): _hash(path) for path in sorted(media.rglob('*')) if path.is_file()}


def restore(source_file, key_file):
    from cryptography.exceptions import InvalidTag
    from directory_snapshot import _empty_fixture_database
    from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError

    config = _guard()
    original = deepcopy(config)
    if not _empty_fixture_database():
        raise ValueError('Baseline restore would overwrite existing current test authority/setup')
    media = _media_state()
    try:
        return _restore(source_file, key_file)
    except BaselineCleanupError:
        raise
    except (psycopg.Error, DatabaseError, ValueError, OSError, KeyError, TypeError, tarfile.TarError,
            InvalidTag, ObjectDoesNotExist, PermissionDenied, ValidationError) as rejected:
        # SQL failures become CACHE_REJECTED only after all cleanup callbacks
        # completed and the exact original empty DB/media are independently proved.
        try:
            connections.close_all()
            config.clear()
            config.update(original)
            _guard()
            if not _empty_fixture_database() or _media_state() != media:
                raise BaselineCleanupError('Original diagnostic DB/media not preserved; fallback forbidden')
        except BaselineCleanupError:
            raise
        except Exception as error:
            raise BaselineCleanupError('Original diagnostic cleanup not verified; fallback forbidden') from error
        raise ValueError('CACHE_REJECTED: ' + type(rejected).__name__) from rejected
    finally:
        try:
            connections.close_all()
        finally:
            config.clear()
            config.update(original)


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
