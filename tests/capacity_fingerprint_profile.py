"""Real SQL diagnostic only: old/new fingerprints in one restricted runtime snapshot."""

import json
import os
import stat
import time
from pathlib import Path

import psycopg
from django.views.decorators.debug import sensitive_variables

from apps.safety.rights_source_fingerprint import _parts, _union

OLD_MUNICIPALITY = (
    "SELECT DISTINCT m.id::text, m.xmin::text || ':' || m.ctid::text FROM catalog_municipality m "
    "JOIN listings_revision r ON r.listing_id = %(listing)s AND (r.municipality_id = m.id "
    "OR EXISTS (SELECT 1 FROM listings_revision_travel_areas rt "
    "WHERE rt.revision_id = r.id AND rt.municipality_id = m.id))"
)


def aggregate(parts):
    return (
        "SELECT encode(sha256(convert_to(coalesce(string_agg(tag || ':' || id || ':' || version, ',' "
        f"ORDER BY tag, id), ''), 'UTF8')), 'hex'), count(*) FROM ({_union(parts)}) AS rows"
    )


@sensitive_variables()
def private_credentials(filename):
    path = Path(filename)
    if not path.is_absolute() or path.parent.parent != Path('/tmp'):
        raise RuntimeError("Runtime diagnostic requires the own private config")
    parent = path.parent.stat()
    if stat.S_IMODE(parent.st_mode) != 0o700 or parent.st_uid != os.geteuid():
        raise RuntimeError("Runtime config directory is not private")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as file:
        facts = os.fstat(file.fileno())
        if (not stat.S_ISREG(facts.st_mode) or stat.S_IMODE(facts.st_mode) != 0o600
                or facts.st_uid != os.geteuid() or facts.st_size > 4096):
            raise RuntimeError("Runtime config must be a private regular file <=4KiB")
        credentials = json.loads(file.read(4097))
    if (set(credentials) != {'NAME', 'HOST', 'PORT', 'USER', 'PASSWORD'}
            or credentials['NAME'] != 'test_capacity_ci'
            or credentials['HOST'] != 'pg' or str(credentials['PORT']) != '5432'
            or not credentials['USER'].startswith('capacity_runtime_')
            or not isinstance(credentials['PASSWORD'], str) or not credentials['PASSWORD']):
        raise RuntimeError("Runtime config differs from the verified capacity topology")
    return credentials


def scrub(value, forbidden):
    if isinstance(value, dict):
        return {key: scrub(item, forbidden) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub(item, forbidden) for item in value]
    if isinstance(value, str):
        for secret in forbidden:
            value = value.replace(secret, '[private]')
    return value


@sensitive_variables()
def fingerprint_profile(settings, endpoint, person, case):
    if not (settings.CAPACITY_ENVIRONMENT_VERIFIED and settings.CAPACITY_DELIVERY_PROFILE
            and settings.CAPACITY_DELIVERY_PROFILE_FULL):
        raise RuntimeError("Fingerprint SQL profiling requires verified full diagnostic mode")
    credentials = private_credentials(endpoint.runtime_config)
    actual_parts, bindings = _parts(person, person.listing, case)
    old_parts = [(tag, OLD_MUNICIPALITY if tag == 'municipality' else sql)
                 for tag, sql in actual_parts]
    new_municipality = dict(actual_parts)['municipality']
    queries = {'old': aggregate(old_parts), 'new': aggregate(actual_parts)}
    result = {'scope': 'Real restricted runtime PostgreSQL; one REPEATABLE READ READ ONLY snapshot; '
                       'diagnostic only, not a capacity sample or acceptance', 'samples': [], 'plans': {}}
    try:
        with psycopg.connect(dbname=credentials['NAME'], host=credentials['HOST'],
                             port=credentials['PORT'], user=credentials['USER'],
                             password=credentials['PASSWORD'], connect_timeout=10) as database:
            with database.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                cursor.execute('SELECT current_user,current_database(),rolsuper,rolcreatedb,rolcreaterole,rolbypassrls '
                               'FROM pg_roles WHERE rolname=current_user')
                if cursor.fetchone() != (credentials['USER'], credentials['NAME'], False, False, False, False):
                    raise RuntimeError('Fingerprint diagnostic is not the restricted runtime identity')
                cursor.execute("SELECT bool_or(pg_has_role(current_user,pg_get_userbyid(relowner),'MEMBER')) "
                               "FROM pg_class WHERE oid IN ('public.core_user'::regclass, "
                               "'public.listings_revision'::regclass,'public.safety_rightsevidencehead'::regclass)")
                if cursor.fetchone()[0]:
                    raise RuntimeError('Fingerprint runtime inherits relation ownership')
                cursor.execute('SHOW transaction_isolation')
                assert cursor.fetchone() == ('repeatable read',)
                cursor.execute('SHOW transaction_read_only')
                assert cursor.fetchone() == ('on',)
                result['identity'] = {'restricted_runtime': True, 'relation_owner': False,
                                      'isolation': 'repeatable read', 'read_only': True}
                cursor.execute('SELECT (SELECT count(*) FROM catalog_municipality), '
                               '(SELECT count(*) FROM listings_revision WHERE listing_id=%(listing)s), '
                               '(SELECT count(*) FROM listings_revision_travel_areas rt JOIN listings_revision r '
                               'ON r.id=rt.revision_id WHERE r.listing_id=%(listing)s), '
                               f'(SELECT count(*) FROM ({new_municipality}) AS selected_municipalities)', bindings)
                municipality, revisions, through, selected_municipalities = cursor.fetchone()
                result['counts'] = {'municipalities_total': municipality,
                                    'municipalities_scoped': selected_municipalities,
                                    'revisions_scoped': revisions, 'travel_through_scoped': through}
                fingerprints = []
                for round_index, order in enumerate([('old', 'new'), ('new', 'old')]):
                    for label in order:
                        begin = time.perf_counter()
                        cursor.execute(queries[label], bindings)
                        digest, count = cursor.fetchone()
                        elapsed = time.perf_counter() - begin
                        fingerprints.append((digest, count))
                        result['samples'].append({'round': round_index, 'variant': label,
                                                  'seconds': elapsed, 'digest': digest, 'count': count})
                assert len(set(fingerprints)) == 1, 'Old/new fingerprint digest or row count differs'
                result['equal_digest_and_count'] = True
                plans = {**queries, 'municipality_old': OLD_MUNICIPALITY,
                         'municipality_new': new_municipality}
                for label, query in plans.items():
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) ' + query, bindings)
                    # Keep full trees: loops, rows, buffers, JIT and planning/execution remain intact.
                    result['plans'][label] = cursor.fetchone()[0]
        return scrub(result, [credentials['PASSWORD'], credentials['USER'], endpoint.runtime_config])
    except psycopg.Error:
        # A driver error must never turn credentials/connection details into profile evidence.
        raise RuntimeError('Owned runtime fingerprint SQL diagnostic failed') from None
