"""Recalculate prefixed membership intervention criteria from original TCP samples."""
import json
import statistics
import sys
from pathlib import Path

source=Path(sys.argv[1]);destination=Path(sys.argv[2]);raw_root=Path(sys.argv[3])
r=json.loads(source.read_text());cases=[]
for case in r['cases']:
 d=case['properties']['tcp_matrix'];rows=d['samples'];events={e['id']:e for e in d['wsgi_events']}
 assert len(events)==len(rows)==len({s['id'] for s in rows})==240
 raw=[]
 for raw_file in (raw_root/f"order-tcp-{d['fixture']}-10000").glob('worker-*.jsonl'):
  for line in raw_file.read_text().splitlines():
   event=json.loads(line);assert event['pid']==int(raw_file.stem.split('-')[1]);raw.append(event)
 assert len(raw)==len({e['id'] for e in raw})==240
 assert sorted(raw,key=lambda e:e['id'])==sorted(d['wsgi_events'],key=lambda e:e['id'])
 assert d['membership_contrast'] and d['controls_per_route_per_block']==10 and d['workers']==4
 def family(path):return 'detail' if '/listing/' in path else 'search' if '?' in path else 'listing'
 for s in rows:
  e=events[s['id']];assert s['status']==200 and e['order_variant']==s['phase']
  assert s['emission']<=e['entry']<=e['exit'] and s['end']>=e['entry']
  if family(s['path'])!='detail':assert e['route']=={'route':'state','reason':'trusted_state','native_unknown':1}
 for pid in {e['pid'] for e in events.values()}:assert not Path(f'/proc/{pid}').exists()
 def mean(metric,f,phase=None,block=None):
  pop=[s for s in rows if family(s['path'])==f and (phase is None or s['phase']==phase) and (block is None or s['block']==block)]
  assert len(pop)==(20 if block is not None else 40)
  return statistics.mean(s['end']-s['emission'] if metric=='http' else events[s['id']]['exit']-events[s['id']]['entry'] for s in pop)
 families={f:{'population_per_variant':40,**{v+'_'+m+'_mean_seconds':mean(m,f,v) for v in ['before','after'] for m in ['http','wsgi']},'observed_wsgi_delta_seconds':mean('wsgi',f,'before')-mean('wsgi',f,'after')} for f in ['listing','search','detail']}
 pairs=[]
 for b,a in [(0,1),(3,2)]:
  for f in ['listing','search','detail']:
   old=mean('http',f,block=b);new=mean('http',f,block=a);delta=old-new;target=d['fixture']=='diverse' and f=='search'
   met=delta>=.02 and delta/old>=.05 if target else new-old<=max(.01,.05*old)
   pairs.append({'before_block':b,'after_block':a,'family':f,'population_per_cell':20,'target':target,'before_mean_seconds':old,'after_mean_seconds':new,'improvement_seconds':delta,'improvement_fraction':delta/old,'allowed_regression_seconds':None if target else max(.01,.05*old),'criterion_met':met})
 plans=[];mechanism_after=None;before_state_loops=None
 for p in case['properties']['order_plans']:
  plan=p['plan'];plan=plan[0] if isinstance(plan,list) else plan
  sql=p['normalized'];operation='count' if sql.startswith('SELECT COUNT') else 'unknown' if sql.startswith('SELECT DISTINCT') else 'page'
  scans=[]
  def walk(node):
   if node.get('Relation Name')=='listings_publicationstate':scans.append({k:node.get(k,'not_measured') for k in ['Node Type','Actual Rows','Actual Loops','Shared Hit Blocks','Shared Read Blocks','Parent Relationship','Subplan Name']})
   for child in node.get('Plans',[]):walk(child)
  walk(plan['Plan'])
  if d['fixture']=='diverse' and operation=='page':
   if p['variant']=='before':before_state_loops=max(s['Actual Loops'] for s in scans)
   else:mechanism_after=bool(scans) and all(not ('Index' in s['Node Type'] and s['Actual Loops']>1) for s in scans)
  plans.append({'variant':p['variant'],'operation':operation,'normalized':sql,'driver_execute_seconds':p['driver_execute_seconds'],'jit':p['jit'],'planning_ms':plan.get('Planning Time','not_measured'),'execution_ms':plan.get('Execution Time','not_measured'),'state_scans':scans,'root_actual_rows':plan['Plan'].get('Actual Rows','not_measured'),'root_shared_hits':plan['Plan'].get('Shared Hit Blocks','not_measured'),'root_shared_reads':plan['Plan'].get('Shared Read Blocks','not_measured')})
 assert sorted((p['variant'],p['operation']) for p in plans)==sorted((v,o) for v in ['before','after'] for o in ['unknown','count','page'])
 delta=sum(x['observed_wsgi_delta_seconds'] for x in families.values())/3
 cases.append({'fixture':d['fixture'],'families':families,'pairs':pairs,'effect_criteria_met':all(p['criterion_met'] for p in pairs),'diverse_before_state_loops':before_state_loops,'diverse_after_no_repeated_state_index_probe':mechanism_after,'observed_delta_D_seconds':delta,'observed_20delta_D_worker_seconds_per_second':20*delta,'plans':plans,'wsgi_exit_after_client_end':{'count':sum(events[s['id']]['exit']>s['end'] for s in rows),'max_seconds':max(0,max(events[s['id']]['exit']-s['end'] for s in rows))}})
mechanism=all(c['diverse_after_no_repeated_state_index_probe'] for c in cases if c['fixture']=='diverse')
keep=mechanism and all(c['effect_criteria_met'] for c in cases)
output={'raw_worker_logs_match_junit':True,'cases':cases,'sql_mechanism_demonstrated':mechanism,'effect_pass':keep,'decision':'retain' if keep else 'withdraw','scope':'480 sequential TCP controls, 4 sync workers, repeated/diverse10000; no load/capacity. Mean per-family and balanced pairs. Common implementation/route/WSGI middleware no intrusive profiler; overhead not_measured. Separate matched SQL/EXPLAIN probes warm caches before controls; actual JIT observed. Driver execute is neither CPU nor planning, includes waits/receipt and not all lazy conversions. Actual Rows/Loops describe individual plan nodes, not global rows_scanned or ORM objects. DeltaD descriptive includes detail fluctuation not causally assigned to unchanged detail path. Upload/DeltaU not_measured. CPU/resource/competition causality not_measured; no savings extrapolated to loaded cohorts.'}
destination.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'decision':output['decision'],'mechanism':mechanism,'cases':[{k:v for k,v in c.items() if k!='plans'} for c in cases]},indent=2))
