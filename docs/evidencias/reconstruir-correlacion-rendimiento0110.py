import json,hashlib,math,statistics,collections
from pathlib import Path
base=Path('/tmp/projection-uuid-array-short0110')
r=json.loads(Path('docs/evidencias/listado-proyeccion-uuid-array-corta0110.json').read_text())
for name in ['benchmark-worker-events.json','benchmark-samples.json']:
 assert hashlib.sha256((base/name).read_bytes()).hexdigest()==r['runner']['artifact_sha256'][name]
worker=json.loads((base/'benchmark-worker-events.json').read_text()); assert not worker['parse_errors']
samples=json.loads((base/'benchmark-samples.json').read_text())
origin=r['summary']['monotonic_origin_seconds']; close=r['summary']['window_close']['observed_at_seconds']; final=r['summary']['actual_elapsed_seconds']
starts={e['id']:e for e in worker['events'] if e['event']=='wsgi_start'}
ends={e['id']:e for e in worker['events'] if e['event']=='wsgi_end'}
routes={e['id']:e for e in worker['events'] if e['event']=='publication_route'}
assert starts.keys()==ends.keys()==routes.keys()

def stats(values):
 v=sorted(values)
 return {'n':len(v),'min':v[0],'mean':statistics.mean(v),'p50':v[math.ceil(len(v)*.5)-1], 'p95':v[math.ceil(len(v)*.95)-1],'max':v[-1], 'sum':sum(v)} if v else {'n':0}
joined=[]
for row in samples['dynamic']:
 if row['id'] not in starts: continue
 st,en,rt=starts[row['id']],ends[row['id']],routes[row['id']]
 path=row['path'];family='detail' if '/listing/' in path else 'search' if '?' in path else 'listing'
 entry=st['started']-origin;end=en['monotonic']-origin
 assert entry>=row['emitted_at']-.001 and end>=entry
 assert abs(end-entry-en['wall'])<.003
 joined.append({'id':row['id'],'family':family,'route':rt['route'],'pid':st['pid'],'emission_to_wsgi_seconds':entry-row['emitted_at'],'wsgi_seconds':en['wall'],'sql_execute_seconds':en['sql']['wall'],'thread_cpu_seconds':en['thread_cpu'],'sql_thread_cpu_seconds':en['sql']['thread_cpu'],'render_seconds':en['stages'].get('render',{}).get('wall'), 'queries':en['sql']['calls'],'client_success':not row['unexpected'],'client_timeout':row['timeout'],'entry_after_client_end':entry>row['ended_at'],'server_end_after_timeout':row['timeout'] and end>row['ended_at'],'entry_relative_seconds':entry,'end_relative_seconds':end})
cohorts={}
for family in ['listing','search','detail','all']:
 rows=joined if family=='all' else [j for j in joined if j['family']==family]
 cohorts[family]={'metrics':{key:stats([j[key] for j in rows if j[key] is not None]) for key in ['emission_to_wsgi_seconds','wsgi_seconds','sql_execute_seconds','thread_cpu_seconds','sql_thread_cpu_seconds','render_seconds','queries']},'client_success':sum(j['client_success'] for j in rows),'client_timeout':sum(j['client_timeout'] for j in rows),'entry_after_client_end':sum(j['entry_after_client_end'] for j in rows),'server_end_after_timeout':sum(j['server_end_after_timeout'] for j in rows)}
# Union of intervals observed within WSGI on each pid, includes one upload.
busy={}
for pid in sorted({s['pid'] for s in starts.values()}):
 intervals=sorted((s['started']-origin,ends[k]['monotonic']-origin) for k,s in starts.items() if s['pid']==pid)
 assert all(intervals[i][1]<=intervals[i+1][0]+.001 for i in range(len(intervals)-1))
 busy[str(pid)]={'requests':len(intervals),'first_entry':intervals[0][0],'last_end':intervals[-1][1],'wsgi_overlap_window_seconds':sum(max(0,min(b,close)-max(0,a)) for a,b in intervals),'wsgi_overlap_full_seconds':sum(max(0,min(b,final)-max(0,a)) for a,b in intervals)}
out={'analysis':'Secondary analysis of frozen artifacts; no new requests, no reclassification of original FAIL','source_commit':r['runner']['source_commit'],'artifact_sha256':{n:r['runner']['artifact_sha256'][n] for n in ['benchmark-worker-events.json','benchmark-samples.json']},'clock':'Existing local asyncio default loop.time / time.monotonic, same host. Chronology and WSGI wall deltas reconciled; no independent clock calibration','population':{'scheduled_emitted':1200,'wsgi_dynamic_entries_and_ends':len(joined),'dynamic_without_captured_wsgi_entry':1200-len(joined),'upload_entries':len(starts)-len(joined)},'cohorts':cohorts,'worker_wsgi_intervals':busy,'limits':['Captured cohort is selected by server progress, not representative of all1200 requests','Emission-to-WSGI includes client connection/write, TCP/kernel backlog, acceptance/dispatch; exact queue attribution not_measured','WSGI intervals exclude accept/pre-WSGI and include waits; occupancy does not imply CPU saturation','Server completion does not imply client delivery; post-client-timeout WSGI work is observed only for matched requests','SQL cursor.execute wall and Python thread CPU do not measure PostgreSQL CPU','No causal benchmark before/after claim; originals retained']}
Path('/tmp/short-existing-correlation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'population':out['population'],'cohorts':{k:{n:v for n,v in c.items() if n!='metrics'} for k,c in out['cohorts'].items()}},indent=2))
