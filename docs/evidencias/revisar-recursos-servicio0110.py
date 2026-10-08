import collections,hashlib,json,math,statistics
from pathlib import Path
out=Path('/tmp/resource-service-checkpoint-0110')
canonical=Path('docs/evidencias/listado-recursos-capacidad0110.json')
j=json.loads(canonical.read_text()); summary=j['cases'][0]['properties']['load_summary']
ledger=json.loads((out/'benchmark-samples.json').read_text());events=json.loads((out/'benchmark-worker-events.json').read_text())
serial=json.loads((out/'serial-reference.json').read_text()); probe=json.loads((out/'resource-samples.jsonl.summary.json').read_text())
snapshots=[json.loads(l)for l in (out/'resource-samples.jsonl').read_text().splitlines()]
assert not events['parse_errors'];assert not probe['fatal_error']
starts={};ends={};routes={}
for event in events['events']:
 target=starts if event['event']=='wsgi_start' else ends if event['event']=='wsgi_end' else routes if event['event']=='publication_route' else None
 if target is not None:
  assert event['id']not in target
  target[event['id']]=event
assert set(starts)==set(ends)
origin=summary['monotonic_origin_seconds'];duration=30
rows=ledger['dynamic'];uploads=ledger['uploads'];assert len(rows)==600 and len({r['id']for r in rows})==600
assert len(uploads)==1 and uploads[0]['status']==302
assert all(r['emitted_at']is not None and r['ended_at']is not None for r in rows+uploads)
def family(path):return 'search'if'?q='in path else 'detail'if'/listing/'in path else 'listing'
def quantile(values,q):return sorted(values)[max(0,math.ceil(q*len(values))-1)]
records=[]
for row in rows+uploads:
 i=row['id'];entry=starts[i]['started']if i in starts else None
 exit_=entry+ends[i]['wall']if entry is not None else None
 if entry is not None:assert starts[i]['pid']==ends[i]['pid']and entry>=origin+row['emitted_at']
 records.append({'id':i,'family':'upload'if i.startswith('u-')else family(row['path']),
  'emission':origin+row['emitted_at'],'deadline':origin+row['emitted_at']+65,
  'client_timeout_observed':origin+row['ended_at']if row['timeout']else None,
  'client_terminal':origin+row['ended_at'],'client_success':not row['unexpected'],
  'entry':entry,'exit':exit_,'service':ends[i]['wall']if i in ends else None,
  'thread_cpu':ends[i]['thread_cpu']if i in ends else None,'pid':starts[i]['pid']if i in starts else None})
def means(groups):
 return {f:{'N':len(g),'mean_wsgi_seconds':statistics.mean(r['service']for r in g),
  'mean_thread_cpu_seconds':statistics.mean(r['thread_cpu']for r in g)}for f in ['listing','search','detail']
  if(g:=[r for r in groups if r['family']==f and r['service']is not None])}
complete=[r for r in records if r['family']!='upload'and r['service']is not None]
serialrows=[]
for r in serial:
 i=r['id'];assert i in starts and i in ends and not r['unexpected']
 serialrows.append({'family':family(r['path']),'service':ends[i]['wall'],'thread_cpu':ends[i]['thread_cpu'],
 'http_seconds':r['seconds'],'pre_wsgi':starts[i]['started']-r['emitted_monotonic']})
loadmeans=means(complete);serialmeans=means(serialrows)
for values in [loadmeans,serialmeans]:assert set(values)=={'listing','search','detail'}
occupancy={}
for pid in sorted({r['pid']for r in records if r['pid']is not None}):
 g=sorted([r for r in records if r['pid']==pid],key=lambda r:r['entry'])
 for a,b in zip(g,g[1:]):assert a['exit']<=b['entry']
 occupancy[str(pid)]={'worker_seconds':sum(max(0,min(origin+30,r['exit'])-max(origin,r['entry']))for r in g),
 'N':len(g)}
 assert occupancy[str(pid)]['worker_seconds']<=30
assert len(occupancy)==4
hz=probe['clock_ticks_per_second'];master=probe['app_master_pid'];pginit=probe['postgres_container_host_pid']
def numbers(text):
 if text=='not_measured':return {}
 return {l.split()[0]:int(l.split()[1])for l in text.splitlines()if len(l.split())==2}
# Use actual bracketing sample times, no uniform CPU allocation assumption.
window=[s for s in snapshots if origin<=s['monotonic']<=origin+30]
assert len(window)>=25
first,last=window[0],window[-1];dt=last['monotonic']-first['monotonic'];pairs=list(zip(window,window[1:]))
app_cpu=0;app_workers=set();own_pg_cpu=0;pg_hosts=set();other=collections.Counter();sample_active_waits=collections.Counter();other_pg_observations=0
for a,b in pairs:
 pa={p['pid']:p for p in a['processes']};pb={p['pid']:p for p in b['processes']}
 app={p['pid']for p in a['processes']if p['ppid']==master or p['pid']==master};app_workers|=app-{master}
 pg_group=pa[pginit]['cgroup']
 activity=[x for x in a['pg_activity']if x[2]and x[0]!=a['collector_pg_pid']]if isinstance(a['pg_activity'],list)else[]
 own_nspids={x[0]for x in activity}
 own_host={p['pid']for p in a['processes']if p['cgroup']==pg_group and p.get('namespace_pids',[None])[-1]in own_nspids}
 pg_hosts|=own_host
 for row in activity:
  if row[3]=='active':sample_active_waits[(row[4]or'none',row[5]or'none')]+=1
 if isinstance(a['pg_activity'],list):other_pg_observations+=sum(x[3]=='active'and not x[2]for x in a['pg_activity'])
 for pid,p in pa.items():
  q=pb.get(pid)
  if q is None or p['start_ticks']!=q['start_ticks']:continue
  delta=(q['cpu_ticks']-p['cpu_ticks'])/hz;assert delta>=0
  if pid in app:app_cpu+=delta
  elif pid in own_host:own_pg_cpu+=delta
  if pid not in app and p['cgroup']!=pg_group:
   other[(p['cgroup'],p['comm'])]+=delta

def group_cpu(record):
 chain=record['pg_cgroups'];leaf=next(iter(chain));return numbers(chain[leaf]['cpu.stat'])['usage_usec']/1e6
pg_cpu=group_cpu(last)-group_cpu(first)
host_delta=[b-a for a,b in zip(first['host_cpu_ticks'],last['host_cpu_ticks'],strict=True)]
host_execution=(host_delta[0]+host_delta[1]+host_delta[2]+host_delta[5]+host_delta[6])/hz
limits={}
for label,key in [('app','app_cgroups'),('postgres','pg_cgroups')]:
 limits[label]={}
 for group,v in first[key].items():
  end=last[key][group];before=numbers(v['cpu.stat']);after=numbers(end['cpu.stat'])
  limits[label][group]={'cpu.max':v['cpu.max'],'cpuset':v['cpuset.cpus.effective'],
   'cpu_weight':v['cpu.weight'],'memory.max':v['memory.max'],'memory.high':v['memory.high'],
   'cpu_stat_delta':{k:after[k]-value for k,value in before.items()if k in after},
   'memory_events_delta':{k:numbers(end['memory.events']).get(k,value)-value for k,value in numbers(v['memory.events']).items()},
   'PSI':{k:v[k]for k in ['cpu.pressure','memory.pressure','io.pressure']}}
resources={'sample_interval_seconds':dt,'sample_start_after_arrivals_seconds':first['monotonic']-origin,
 'sample_end_after_arrivals_seconds':last['monotonic']-origin,'samples_in_arrivals':len(window),
 'app_process_CPU_seconds':app_cpu,'app_average_CPU_cores_consumed':app_cpu/dt,'observed_workers':len(app_workers),
 'postgres_service_CPU_seconds':pg_cpu,'postgres_service_average_CPU_cores_consumed':pg_cpu/dt,
 'own_postgres_backend_CPU_seconds_lower_bound':own_pg_cpu,'own_postgres_average_CPU_lower_bound':own_pg_cpu/dt,'own_pg_host_processes':len(pg_hosts),
 'host_execution_CPU_seconds':host_execution,'host_average_CPU_cores_consumed':host_execution/dt,
 'host_steal_seconds':host_delta[7]/hz,'host_iowait_seconds':host_delta[4]/hz,
 'other_process_CPU_seconds_lower_bound':sum(other.values()),'other_top_groups_and_commands_CPU_seconds':[
  {'cgroup':k[0],'comm':k[1],'cpu_seconds':v}for k,v in other.most_common(10)],
 'pg_active_own_backend_wait_samples':[{'wait_event_type':k[0],'wait_event':k[1],'observations':v}for k,v in sample_active_waits.items()],
 'other_database_active_samples':other_pg_observations,'limits':limits,
 'host_mem_available_min_bytes':min(s['meminfo']['MemAvailable']for s in window),
 'host_swap_free_min_bytes':min(s['meminfo']['SwapFree']for s in window),
 'vmstat_deltas':{k:last['vmstat'].get(k,v)-v for k,v in first['vmstat'].items()},
 'host_PSI':first['host_pressure'],
 'app_sampled_RSS_max_bytes':max(sum(p['rss_bytes']for p in s['processes']if p['pid']in app_workers or p['pid']==master)for s in window),
 'pg_sampled_cgroup_memory_max_bytes':max(int(next(iter(s['pg_cgroups'].values()))['memory.current'])for s in window)}
D=sum(x['mean_wsgi_seconds']/3 for x in loadmeans.values());Dserial=sum(x['mean_wsgi_seconds']/3 for x in serialmeans.values())
delay=[r['emitted_at']-r['scheduled_at']for r in rows]
valid=len(rows)==600 and quantile(delay,.95)<=.01 and quantile(delay,.99)<=.025 and max(delay)<=.1
report={'source_artifact_sha256':j['artifact_sha256'],'diagnostic_only':True,'generator_valid_recomputed':valid,
 'delay_ms':{'p95':quantile(delay,.95)*1000,'p99':quantile(delay,.99)*1000,'max':max(delay)*1000},
 'client_counts':summary['counts'],'client_transport_verdict_only':summary['verdict'],
 'observed_dynamic_wsgi':len(complete),'missing_dynamic_wsgi':600-len(complete),
 'observed_serial_wsgi':len(serialrows),'mean_services_under_load':loadmeans,'mean_services_serial_reference':serialmeans,
 'D_worker_seconds_per_request_load_observed':D,'W_worker_seconds_per_second_at20_load_observed':20*D,
 'D_worker_seconds_per_request_serial_observed':Dserial,'W_worker_seconds_per_second_at20_serial_observed':20*Dserial,
 'upload':{k:records[-1][k]for k in ['service','thread_cpu','client_success']},
 'pre_wsgi_load_mean_seconds':statistics.mean(r['entry']-r['emission']for r in complete),
 'pre_wsgi_load_median_seconds':statistics.median(r['entry']-r['emission']for r in complete),
 'pre_wsgi_serial_mean_seconds':statistics.mean(r['pre_wsgi']for r in serialrows),
 'occupation_first30s_including_upload':occupancy,
 'client_successes_within30s':sum(r['client_success']and r['client_terminal']<=origin+30 for r in records if r['family']!='upload'),
 'entered_after_deadline':sum(r['entry']is not None and r['entry']>r['deadline']for r in records if r['family']!='upload'),
 'actual_routes':dict(collections.Counter(routes[r['id']]['route']for r in complete if r['id']in routes)),
 'resources':resources,'collector':probe,
 'collector_criteria':{'sample_coverage':len(snapshots)/probe['elapsed'],'p95_poll_seconds':quantile(probe['sample_durations'],.95),'CPU_seconds_per_second':probe['collector_thread_cpu']/probe['elapsed']},
 'limits':['Diagnostic30s not contractual60/900gate; originalhistoricalFAIL preserved','Process/cgroupCPU actualcounters over declared~29s samplinginterval, not cursor walltime; PGsharedservice includesbackground/otherdatabases','OwnPGCPU lowerbound due snapshot/processvisibility/churn; no uniform CPU allocation overWSGIwall','Waitobservations are sampled states, not durations; active with noevent may be runnable or executing','PSI absent not zero; RSSsamplemax not allocation or additive uniquephysicalmemory','D/W use means and equalcontractweights, completed populations declared; serial/load observationalcontrast sameversion but not controlledCPUscaling proof','CollectorCPU/poll duration measured; causalWSGI/PGquery observer overhead not_measured','No backendchange adopted inA; Ccannotbecreditedasbackendimprovement or fullcapacityPASS']}
assert resources['observed_workers']==4
Path('/tmp/resource-service-analysis0110.json').write_text(json.dumps(report,indent=2)+'\n')
Path('/tmp/resource-service-times0110.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k not in ['source_artifact_sha256','collector','resources']},indent=2))
print(json.dumps({k:v for k,v in resources.items()if k!='limits'},indent=2))
