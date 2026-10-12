"""Owned child LOGIN: finite plans and exact hash controls, no productive changes."""
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter_ns

UTC_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
EVENT_COLUMNS = 'sequence,kind,source_table,source_pk,payload_digest,previous_digest,digest,created_at'
VARIANTS = ('native_hash', 'whole_row', 'jsonb_payload', 'inline_hash')


def statements(case_id):
    from apps.safety.evidence_chain import _source_statements
    from apps.safety.evidence_chain_sql_v1 import EVENT, TABLES

    payload = (
        "pg_catalog.jsonb_build_array('rights-evidence-chain-v1',request_id::text,sequence,kind,"
        "source_table,source_pk,payload_digest,previous_digest,"
        f"pg_catalog.to_char(created_at AT TIME ZONE 'UTC','{UTC_FORMAT}'))::text")
    suffix = f' FROM public."{EVENT}" WHERE request_id=%s ORDER BY sequence'
    native = ('public.rights_evidence_link(request_id,sequence,kind,source_table,source_pk,'
              'payload_digest,previous_digest,created_at)')
    inline = f"pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to({payload},'UTF8')),'hex')"
    queries = [('events', {
        'native_hash': f'SELECT {EVENT_COLUMNS},{native}' + suffix,
        'whole_row': f'SELECT {EVENT_COLUMNS},NULL::text' + suffix,
        'jsonb_payload': f'SELECT {EVENT_COLUMNS},{payload}' + suffix,
        'inline_hash': f'SELECT {EVENT_COLUMNS},{inline}' + suffix,
    })]
    for table, (native, _) in zip(TABLES, _source_statements(case_id), strict=True):
        suffix = native[native.index(' FROM '):]
        normalized = (
            "pg_catalog.jsonb_set(pg_catalog.to_jsonb(s),'{created_at}',"
            f"pg_catalog.to_jsonb(pg_catalog.to_char(s.created_at AT TIME ZONE 'UTC','{UTC_FORMAT}')))::text")
        inline = f"pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to({normalized},'UTF8')),'hex')"
        queries.append((table, {
            'native_hash': 'SELECT s.id::text,public.rights_evidence_row_hash(to_jsonb(s))' + suffix,
            'whole_row': 'SELECT s.id::text,s' + suffix,
            'jsonb_payload': 'SELECT s.id::text,pg_catalog.to_jsonb(s)::text' + suffix,
            'inline_hash': f'SELECT s.id::text,{inline}' + suffix,
        }))
    return queries


def shape(node):
    """Executable structure/row counts, excluding differing target expressions/costs."""
    keys = ('Node Type', 'Join Type', 'Relation Name', 'Index Name', 'Scan Direction',
            'Actual Rows', 'Actual Loops', 'Parent Relationship')
    return {**{key: node[key] for key in keys if key in node},
            'Plans': [shape(child) for child in node.get('Plans', [])]}


def scrub(value, case_id):
    if isinstance(value, str):
        return value.replace(str(case_id), '<synthetic-case>')
    if isinstance(value, list):
        return [scrub(item, case_id) for item in value]
    if isinstance(value, dict):
        return {key: scrub(item, case_id) for key, item in value.items()}
    return value


def run(case_id):
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, transaction

    from apps.safety.evidence_chain import require_runtime_chain
    from apps.safety.evidence_chain_sql_v1 import EVENT, TABLES

    assert connection.vendor == 'postgresql' and settings.RIGHTS_EVIDENCE_ENFORCED
    report = {'scope': 'diagnostic_plans_not_request_p95', 'queries': [], 'variants': VARIANTS}
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '15s'")
        cursor.execute("SELECT current_user,session_user,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls "
                       "FROM pg_roles WHERE rolname=current_user")
        identity = cursor.fetchone()
        assert identity[0] == identity[1] and identity[0].startswith('capacity_runtime_')
        assert not any(identity[2:])
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE usename=current_user "
                       "AND pid<>pg_backend_pid() AND state='active'")
        assert cursor.fetchone() == (0,)
        report['other_active_connections_of_same_login'] = 0
        cursor.execute("SELECT pg_has_role(current_user,pg_get_userbyid(relowner),'MEMBER') "
                       "FROM pg_class WHERE oid='public.safety_rightsevidencehead'::regclass")
        assert cursor.fetchone() == (False,)
        # Fresh trust plus complete validation; this locks head before all probes.
        ticket = require_runtime_chain(case_id)
        report['head_count'] = ticket.count
        report['runtime_login_verified'] = True
        cursor.execute('SHOW server_version')
        report['postgres_version'] = cursor.fetchone()[0]
        cursor.execute('SHOW TimeZone')
        report['timezone'] = cursor.fetchone()[0]
        tables = [EVENT, 'safety_rightsaction', *TABLES]
        cursor.execute('SELECT tablename,indexname,indexdef FROM pg_indexes '
                       'WHERE schemaname=%s AND tablename=ANY(%s) ORDER BY tablename,indexname',
                       ['public', tables])
        report['indexes'] = cursor.fetchall()
        cursor.execute('SELECT relname,n_live_tup,n_dead_tup,analyze_count,autoanalyze_count '
                       'FROM pg_stat_all_tables WHERE schemaname=%s AND relname=ANY(%s) ORDER BY relname',
                       ['public', tables])
        report['statistics'] = cursor.fetchall()
        for name, variants in statements(case_id):
            value = {'name': name, 'samples': [], 'timed_native': None, 'serialized_native': None}
            # Equality is checked on fresh full SQL outputs before recording plans.
            # No payloads/IDs/hashes from these rows enter the report.
            started = perf_counter_ns()
            cursor.execute(variants['native_hash'], [case_id])
            executed = perf_counter_ns()
            original = cursor.fetchall()
            consumed = perf_counter_ns()
            value['native_driver'] = {'execute_ns': executed - started,
                                      'fetch_ns': consumed - executed,
                                      'total_ns': consumed - started,
                                      'scope': 'Single diagnostic query; includes driver/transport, not HTTP p95'}
            value['native_sql_sha256'] = hashlib.sha256(variants['native_hash'].encode()).hexdigest()
            cursor.execute(variants['inline_hash'], [case_id])
            inline = cursor.fetchall()
            assert (original == inline if name == 'events' else dict(original) == dict(inline))
            assert len(original) == len(inline)
            value.update(rows=len(original), inline_exact=True)

            def explain(statement, *, timing=False, serialize='NONE'):
                prefix = ('EXPLAIN (ANALYZE,BUFFERS,VERBOSE,SETTINGS,FORMAT JSON,'
                          f'TIMING {"ON" if timing else "OFF"},SERIALIZE {serialize}) ')
                wall = perf_counter_ns()
                cursor.execute(prefix + statement, [case_id])
                plan = cursor.fetchone()[0][0]
                return {'driver_wall_ns': perf_counter_ns() - wall, 'explain': scrub(plan, case_id)}

            # Warm each projection once. No manual ANALYZE/index/enable_* changes.
            for variant in VARIANTS:
                explain(variants[variant])
            # Four counterbalanced rounds, reducing node timer overhead uniformly.
            for round_number in range(4):
                order = VARIANTS[round_number:] + VARIANTS[:round_number]
                for variant in order:
                    sample = explain(variants[variant])
                    assert sample['explain']['Plan']['Actual Rows'] == len(original)
                    value['samples'].append(dict(variant=variant, round=round_number, **sample))
            value['timed_native'] = explain(variants['native_hash'], timing=True)
            value['serialized_native'] = explain(variants['native_hash'], timing=True, serialize='TEXT')
            value['same_executable_shape'] = {
                variant: all(shape(sample['explain']['Plan']) == shape(value['samples'][0]['explain']['Plan'])
                             for sample in value['samples'] if sample['variant'] == variant)
                for variant in VARIANTS}
            report['queries'].append(value)
        cursor.execute(f'SELECT count(*) FROM public."{EVENT}" WHERE request_id=%s', [case_id])
        assert cursor.fetchone() == (ticket.count,)
    connection.close()
    return report


if __name__ == '__main__':
    # Arguments contain only own synthetic case UUID and private output path.
    report = run(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(report))
