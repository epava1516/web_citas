"""Read-only reconstruction; write derived redacted report only to /tmp."""
import collections,hashlib,json,statistics
from pathlib import Path
root=Path('/home/felidae/proyectos/web_modelos');out=Path('/tmp/reading-common-short-0110')
evidence=json.loads((root/'docs/evidencias/listado-lectura-comun-corta0110.json').read_text())
result=json.loads((out/'result.json').read_text())
for name in ['benchmark-samples.json','benchmark-worker-events.json']:
 assert hashlib.sha256((out/name).read_bytes()).hexdigest()==result['artifact_sha256'][name]
summary=evidence['cases'][0]['properties']['load_summary']
samples=json.loads((out/'benchmark-samples.json').read_text()); observed=json.loads((out/'benchmark-worker-events.json').read_text())
assert not observed['parse_errors']
origin=summary['monotonic_origin_seconds'];timeout=summary['policy']['request_timeout_seconds']
rows=samples['dynamic'];uploads=samples['uploads'];allrows=rows+uploads
assert len(rows)==1200 and len({r['id'] for r in allrows})==1201
starts={};ends={}
for e in observed['events']:
 if e['event'] in ['wsgi_start','wsgi_end']:
  dest=starts if e['event']=='wsgi_start' else ends
  assert e['id'] not in dest
  dest[e['id']]=e
assert set(starts)==set(ends)
assert set(starts)<={r['id'] for r in allrows}
def family(r):return 'upload' if r['id'].startswith('u-') else 'search' if '?q=' in r['path'] else 'detail' if '/listing/' in r['path'] else 'listing'
records=[]
for r in allrows:
 i=r['id'];entry=starts[i]['started']-origin if i in starts else None
 exit_=starts[i]['started']+ends[i]['wall']-origin if i in ends else None
 if entry is not None:
  assert starts[i]['pid']==ends[i]['pid'] and entry>=r['emitted_at'] and exit_>=entry
  assert abs(ends[i]['monotonic']-origin-exit_)<.01
 records.append({'id':i,'family':family(r),'t_emission':r['emitted_at'],'t_deadline':r['emitted_at']+timeout,
 't_client_timeout_observed':r['ended_at'] if r['timeout'] else None,
 't_client_terminal':r['ended_at'],'t_wsgi_entry':entry,'t_wsgi_exit':exit_,
 'service':ends[i]['wall'] if i in ends else None,'thread_cpu':ends[i]['thread_cpu'] if i in ends else None,
 'pid':starts[i]['pid'] if i in starts else None,'timeout':r['timeout'],'client_success':not r['unexpected']})
dynamic=[r for r in records if r['family']!='upload'];complete=[r for r in dynamic if r['service'] is not None]
means={f:{'observed_count':len(g),'mean_service_seconds':statistics.mean(r['service'] for r in g),
 'mean_thread_cpu_seconds':statistics.mean(r['thread_cpu'] for r in g)}
 for f in ['listing','search','detail'] if(g:=[r for r in complete if r['family']==f])}
D=sum(v['mean_service_seconds']/3 for v in means.values());W=20*D
intervals={};overlaps=[]
for pid in sorted({r['pid'] for r in records if r['pid'] is not None}):
 g=sorted((r for r in records if r['pid']==pid),key=lambda r:r['t_wsgi_entry'])
 for a,b in zip(g,g[1:]):assert a['t_wsgi_exit']<=b['t_wsgi_entry']
 occupancy=sum(max(0,min(60,r['t_wsgi_exit'])-max(0,r['t_wsgi_entry'])) for r in g)
 upload=sum(max(0,min(60,r['t_wsgi_exit'])-max(0,r['t_wsgi_entry'])) for r in g if r['family']=='upload')
 intervals[str(pid)]={'window_worker_seconds':occupancy,'utilization_including_upload':occupancy/60,'upload_worker_seconds':upload,'observed_intervals':len(g)}
failures=[r for r in dynamic if r['timeout']]
report={'source_artifact_sha256':{n:result['artifact_sha256'][n] for n in ['benchmark-samples.json','benchmark-worker-events.json']},
 'clock_origin':origin,'timeout_seconds':timeout,'scheduled':len(rows),'observed_wsgi_dynamic':len(complete),
 'completed_success_within_exact_60s':sum(r['client_success'] and r['t_client_terminal']<=60 for r in dynamic),
 'completed_failure_within_exact_60s':sum(not r['client_success'] and r['t_client_terminal']<=60 for r in dynamic),
 'pending_exact_60s':sum(r['t_client_terminal']>60 for r in dynamic),
 'observed_mean_service_seconds':statistics.mean(r['service'] for r in complete),'families':means,
 'contract_weights':{'listing':1/3,'search':1/3,'detail':1/3},'D_worker_seconds_per_request':D,'W_worker_seconds_per_second_at20RPS':W,
 'pre_wsgi_mean_seconds':statistics.mean(r['t_wsgi_entry']-r['t_emission'] for r in complete),
 'pre_wsgi_median_seconds':statistics.median(r['t_wsgi_entry']-r['t_emission'] for r in complete),
 'window_workers':intervals,'timeouts_final':len(failures),
 'timeouts_without_wsgi_entry':sum(r['t_wsgi_entry'] is None for r in failures),
 'timeouts_with_wsgi_entry':sum(r['t_wsgi_entry'] is not None for r in failures),
 'requests_entering_wsgi_after_client_deadline':sum(r['t_wsgi_entry'] is not None and r['t_wsgi_entry']>r['t_deadline'] for r in dynamic),
 'requests_entering_wsgi_after_observed_client_timeout':sum(r['t_wsgi_entry'] is not None and r['t_client_timeout_observed'] is not None and r['t_wsgi_entry']>r['t_client_timeout_observed'] for r in dynamic),
 'upload_observed_service_seconds':sum(r['service'] for r in records if r['family']=='upload'),
 'upload_observed_thread_cpu_seconds':sum(r['thread_cpu'] for r in records if r['family']=='upload'),
 'upload_worker_demand_per_second_at_one_per_minute':sum(r['service'] for r in records if r['family']=='upload')/60,
 'scope':'Means of1109 observed dynamicWSGI services through drain; missing91 notzero and selection/censoring bias possible. D uses equal contractual family weights, not median or completed family mix; W includes waiting occupancy not CPU. Throughput withinexact60s client terminal timestamps only. ObservedWSGIservice interval is [start.started,start.started+end.wall], end.monotonic checkedwithin10ms; intervals nonoverlapping perPID. Samehost monotonic origin from recorded runner; emission->WSGI spans client/transport/accept, not exact socket/Gunicornqueue. Upload included independently and inwindowoccupancy. No new load; late servercompletion never client success.'}
Path('/tmp/service-checkpoint-reconstruction0110.json').write_text(json.dumps(report,indent=2)+'\n')
Path('/tmp/service-checkpoint-timestamps0110.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(report,indent=2))
