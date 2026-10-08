"""Experimental scalar-read implementation, never installed into application code."""
import json
import psycopg
from psycopg import sql
from django.db import connection,transaction
from unittest.mock import patch
from test_sql_publication_bulk_cost import redact_plan

def prepared_iter(self):
    connection.ensure_connection()
    driver=connection.connection
    previous=driver.prepare_threshold
    driver.prepare_threshold=0
    try:
        with connection.wrap_database_errors, psycopg.Cursor(driver) as cursor:
            cursor.execute(self.sql,self.params,prepare=True)
            names=[column.name for column in cursor.description]
            for values in cursor.fetchall():
                yield dict(zip(names,values,strict=True))
    finally:
        driver.prepare_threshold=previous

def diagnose_session():
    from apps.listings import discovery,sql_publication as proof
    connection.ensure_connection();driver=connection.connection
    assert driver.prepare_threshold is None
    result={'backend_pid':driver.info.backend_pid,'initial_prepare_threshold':None,'prepared_max':driver.prepared_max,'families':{}}
    for family,data in [('listing',{}),('search',{'q':'photography'})]:
        captured=[]
        with patch.object(proof,'read_publication_values',lambda x:captured.append(x) or []):proof.SQLPublication(discovery.candidates(data))
        read=captured[0]
        with transaction.atomic(),connection.cursor() as c:
            c.execute('SET LOCAL jit=off')
            baseline=list(read)
            for _ in range(8):
                assert list(prepared_iter(read))==baseline
                assert driver.prepare_threshold is None
        with connection.cursor() as c:
            c.execute('SELECT name, statement, generic_plans, custom_plans FROM pg_prepared_statements')
            records=c.fetchall()
        current=next(r for r in records if '_publication_scalar_population' in r[1] and ('relevance' in r[1])==(family=='search'))
        plans={}
        for mode in ['force_custom_plan','force_generic_plan']:
            with transaction.atomic(),connection.cursor() as c:
                c.execute('SET LOCAL jit=off');c.execute("SET LOCAL statement_timeout='5000ms'")
                c.execute('SET LOCAL plan_cache_mode = '+mode)
                command=sql.SQL('EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) EXECUTE {} ({})').format(sql.Identifier(current[0]),sql.SQL(',').join(sql.Literal(v) for v in read.params))
                c.execute(command);plans[mode]=redact_plan(c.fetchone()[0])
        result['families'][family]={'named_statement':current[0],'generic_plans_before_forced_explain':current[2],'custom_plans_before_forced_explain':current[3],'rows_returned':len(baseline),'plans_separate':plans,'scope':'8 actual named prepared reads; forced custom/generic EXPLAIN separate, no forced mode in HTTP controls; values redacted. Client vs server bindings exact vector equality.'}
    assert driver.prepare_threshold is None and driver.info.backend_pid==result['backend_pid']
    # Failure must restore policy and propagate through Django error mapping.
    from django.db import ProgrammingError
    bad=proof.CapturedSQLRead('SELECT no_such_column_in_owned_synthetic_test',[])
    try:
        with transaction.atomic():list(prepared_iter(bad))
    except ProgrammingError:
        result['error_mapping_and_policy_restoration_verified']=True
    else:raise AssertionError('Invalid SELECT did not fail')
    assert driver.prepare_threshold is None
    return result
