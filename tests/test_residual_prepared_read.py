"""Bounded planning/session diagnosis of the current scalar SELECT only."""
import hashlib,json,os,statistics,time
from pathlib import Path
from unittest.mock import patch
import psycopg
import pytest
from django.db import connection,transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_sql_publication_bulk_cost import redact_plan
from apps.listings import discovery,projected_publication as projection,sql_publication as proof
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate
from scripts.query_pattern_redaction import query_pattern
pytestmark=[pytest.mark.django_db(transaction=True),pytest.mark.skipif(not os.getenv('RESIDUAL_PREPARED_OUTPUT'),reason='Explicit isolated prepared-read diagnosis')]

@pytest.mark.parametrize('variant',['contractual','diverse'])
def test_current_scalar_planning_and_sessions(request,record_property,variant):
 request.getfixturevalue('directory');populate(10000)
 if variant=='diverse':
  rows=list(Revision.objects.filter(status='approved').order_by('pk'))
  for i,row in enumerate(rows):
   suffix=alpha(i);row.description+=' '+suffix
   if row.description_alternative:row.description_alternative+=' '+suffix
   row.telegram='bench'+suffix
  Revision.objects.bulk_update(rows,['description','description_alternative','telegram'],batch_size=250)
 assert connection.vendor=='postgresql' and connection.settings_dict['NAME'].startswith('test_promotion_gate_')
 assert projection.supported()
 with connection.cursor() as c:
  for table in connection.introspection.table_names():c.execute('ANALYZE '+connection.ops.quote_name(table))
  c.execute('SELECT pg_backend_pid()');pid=c.fetchone()[0]
 report={'variant':variant,'stage':'prepared','backend_pid':pid,'source_digest':projection.definitions_digest(),'families':{},'scope':'Main scalar read only. Own synthetic PostgreSQL session; no HTTP/timing profiler. Prepared protocol on psycopg Cursor, baseline Django ClientCursor. Fresh params per constructor, no results reused. EXPLAIN separate. execute includes transport/driver/server; planning only from plans. rows_returned direct fetch length; scanned global not_measured.'}
 output=Path(os.environ['RESIDUAL_PREPARED_OUTPUT'],variant+'.json')
 def persist():output.write_text(json.dumps(report,indent=2)+'\n')
 for family,data in [('listing',{}),('search',{'q':'photography'})]:
  captured=[];start=time.perf_counter()
  with patch.object(proof,'read_publication_values',lambda x:captured.append(x) or []):proof.SQLPublication(discovery.candidates(data))
  construction_compilation=time.perf_counter()-start;assert len(captured)==1
  read=captured[0];sql,params=read.sql,read.params
  pattern=query_pattern(sql)
  def run(mode,explain=False):
   with transaction.atomic():
    with connection.cursor() as c:c.execute('SET LOCAL jit=off');c.execute("SET LOCAL statement_timeout='4000ms'")
    cursor=connection.cursor() if mode=='A' else psycopg.Cursor(connection.connection)
    with cursor as c:
     start=time.perf_counter()
     if mode=='A':c.execute(('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' if explain else '')+sql,params)
     else:c.execute(sql,params,prepare=True)
     executed=time.perf_counter()-start;start=time.perf_counter();values=c.fetchall();fetched=time.perf_counter()-start
     return (redact_plan(values[0][0]) if explain else values),{'execute_seconds':executed,'fetch_seconds':fetched,'read_seconds':executed+fetched}
  plan,_=run('A',True);base,_=run('A');other,_=run('B');assert other==base and len(base)==10000
  samples=[]
  for pair in range(8):
   for mode in ('AB' if pair%2==0 else 'BA'):
    rows,timing=run(mode);assert rows==base;samples.append({'pair':pair,'mode':mode,'rows_returned':len(rows),**timing})
  with connection.cursor() as c:
   c.execute('SELECT name, generic_plans, custom_plans, parameter_types::text FROM pg_prepared_statements');prepared=[{'name':r[0],'generic_plans':r[1],'custom_plans':r[2],'parameter_types':r[3]} for r in c.fetchall()]
   c.execute('SELECT pg_backend_pid()');assert c.fetchone()[0]==pid
  median={m:statistics.median(s['read_seconds'] for s in samples if s['mode']==m) for m in 'AB'}
  report['families'][family]={'query_pattern':pattern,'constructor_plus_compilation_seconds':construction_compilation,'baseline_separate_plan':plan,'samples':samples,'medians':median,'session_prepared_statements':prepared,'query_sha256':hashlib.sha256(sql.encode()).hexdigest(),'rows_affected':'not_measured','rows_scanned':'not_measured'};persist()
 report.update(stage='complete',application_changed=False);persist();record_property('prepared_read_diagnosis',report)
