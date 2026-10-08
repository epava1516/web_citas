"""Reconcile current matrix profiles and original lightweight TCP worker records."""
import json
import statistics
import sys
from pathlib import Path

review=json.loads(Path(sys.argv[1]).read_text());raw_root=Path(sys.argv[2]);destination=Path(sys.argv[3])
profiles={};controls={};pids=set()
for c in review['cases']:
 assert c['status']=='PASS'
 props=c['properties']
 if 'current_matrix' in props:
  d=props['current_matrix'];key=(d['fixture'],d['count']);assert key not in profiles
  for route in d['routes']:
   assert route['route']=={'route':'state','reason':'trusted_state','native_unknown':0}
   assert len(route['controls_seconds'])==5 and route['body_route_order_count_unchanged']
   assert route['queries']>=sum(q['calls'] for q in route['dominant_driver_events'])
   for q in route['dominant_driver_events']:
    assert abs(q['mean_time']*q['calls']-q['total_time'])<1e-8
    q['fraction_of_driver_execute_observed']=q['total_time']/route['driver_execute_seconds']
   route['dominant_driver_fraction_observed']=sum(q['total_time'] for q in route['dominant_driver_events'])/route['driver_execute_seconds']
   assert abs(statistics.mean(route['controls_seconds'])-route['control_mean_seconds'])<1e-8
  profiles[key]=d
 if 'tcp_matrix' in props:
  d=props['tcp_matrix'];key=(d['fixture'],d['count']);assert key not in controls
  rows=d['samples'];events={e['id']:e for e in d['wsgi_events']};assert len(rows)==len(events)==len({s['id'] for s in rows})==30
  assert not d['dirty_contrast'] and not d['order_contrast'] and not d['membership_contrast'] and d['workers']==4
  raw=[]
  for file in (raw_root/f"matrix-tcp-{d['fixture']}-{d['count']}").glob('worker-*.jsonl'):
   for line in file.read_text().splitlines():
    e=json.loads(line);assert e['pid']==int(file.stem.split('-')[1]);raw.append(e)
  assert len(raw)==len({e['id'] for e in raw})==30
  assert sorted(raw,key=lambda e:e['id'])==sorted(d['wsgi_events'],key=lambda e:e['id'])
  def family(path):return 'detail' if '/listing/' in path else 'search' if '?' in path else 'listing'
  for s in rows:
   e=events[s['id']];assert s['status']==200 and s['emission']<=e['entry']<=e['exit'] and s['end']>=e['entry']
   if family(s['path'])!='detail':assert e['route']=={'route':'state','reason':'trusted_state','native_unknown':0}
   pids.add(e['pid'])
  means={}
  for f in ['listing','search','detail']:
   pop=[s for s in rows if family(s['path'])==f];assert len(pop)==10
   means[f]={'population':10,'http_mean_seconds':statistics.mean(s['end']-s['emission'] for s in pop),'wsgi_mean_seconds':statistics.mean(events[s['id']]['exit']-events[s['id']]['entry'] for s in pop),'pre_wsgi_mean_seconds':statistics.mean(events[s['id']]['entry']-s['emission'] for s in pop)}
  for route in d['routes']:
   pop=[s for s in rows if s['path']==route['path']];assert len(pop)==route['population']==5
   assert abs(statistics.mean(s['end']-s['emission'] for s in pop)-route['http_mean_seconds'])<1e-8
  demand=sum(v['wsgi_mean_seconds'] for v in means.values())/3
  controls[key]={'fixture':d['fixture'],'count':d['count'],'family_means':means,'D_observed_sequential_seconds':demand,'20D_worker_seconds_per_second_arithmetic':20*demand,'U':'not_measured','total_W':'not_measured','routes':d['routes'],'raw_events_match':True,'wsgi_exit_after_client_end':{'count':sum(events[s['id']]['exit']>s['end'] for s in rows),'max_seconds':max(0,max(events[s['id']]['exit']-s['end'] for s in rows))}}
expected={(f,n) for f in ['repeated','diverse'] for n in [100,1000,10000]}
assert set(profiles)==set(controls)==expected
for pid in pids:assert not Path(f'/proc/{pid}').exists()
output={'source':'2dd4ca5 product plus tested original-log-preservation/manifest patch; exact hashes in review','cells':[{'control':controls[k],'profile':profiles[k]} for k in sorted(expected)],'case_count':12,'tcp_controls':180,'worker_pids_absent':sorted(pids),'scope':'Own isolated PostgreSQL, official refresh/VACUUM/ANALYZE, clean0 unknown, repeated/diverse100/1000/10000, Client profiles separate from5 no-profiler Client controls and5*6 TCP controls/cell. Current original route/worker records reconciled; source/hash/DB/media review independent. Current measurements do not establish causal improvement against old separate runs. D from means equal1/3 families, within family equalES/EN and explicit10 observations; sequential not load; U/totalW absent, no capacity acceptance. Profile SQL driver events exclude fetch/conversions outsideexecute and are not PG CPU/planning; model instance counts not rows. Rule inclusive/exclusive overlaps lazy SQL/render; exclusive subtracts only direct instrumented child intervals, not CPU. No total-minus-SQL validation. Overhead causal, CPU/resources, rows_returned/affected/scanned and construction/compilation not_measured. Shared photos/phone/catalog remain in diversefixture; no generaldiversity claim.'}
destination.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'case_count':12,'controls':180,'cells':[{'fixture':k[0],'count':k[1],'WSGI_means_ms':{f:round(v['wsgi_mean_seconds']*1000,3) for f,v in controls[k]['family_means'].items()},'D_ms':round(controls[k]['D_observed_sequential_seconds']*1000,3),'20D':controls[k]['20D_worker_seconds_per_second_arithmetic'],'profile_query_counts':[v['queries'] for v in profiles[k]['routes']]} for k in sorted(expected)]},indent=2))
