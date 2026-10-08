import json,os,time,sys
from pathlib import Path
sys.path.insert(0,'/home/felidae/proyectos/web_modelos')
from scripts.benchmark_resource_probe import optional_text,process_snapshot,cgroup_chain

def snap():
 procs=[p for x in Path('/proc').iterdir() if x.name.isdigit() and (p:=process_snapshot(int(x.name)))]
 groups={p['cgroup'] for p in procs if p['cgroup']!='not_measured'}
 return {'monotonic':time.monotonic(),'host_cpu_ticks':[int(x) for x in optional_text('/proc/stat').splitlines()[0].split()[1:9]],'processes':procs,'cgroups':{g:cgroup_chain(g) for g in groups},'meminfo':optional_text('/proc/meminfo'),'vmstat':optional_text('/proc/vmstat'),'diskstats':optional_text('/proc/diskstats'),'pressure':{k:optional_text('/proc/pressure/'+k) for k in ['cpu','memory','io']}}
wall=time.monotonic();cpu=time.process_time();first=snap();time.sleep(15);last=snap();dt=last['monotonic']-first['monotonic'];hz=os.sysconf('SC_CLK_TCK');old={p['pid']:p for p in first['processes']};cost=[]
for p in last['processes']:
 b=old.get(p['pid'])
 if b and b['start_ticks']==p['start_ticks']:
  cost.append({'pid':p['pid'],'comm':p['comm'],'cgroup':p['cgroup'],'cpu_cores_observed':(p['cpu_ticks']-b['cpu_ticks'])/hz/dt})
host=sum(last['host_cpu_ticks'][i]-first['host_cpu_ticks'][i] for i in [0,1,2,5,6])/hz/dt
result={'scope':'Two endpoint read-only snapshots, no synthetic load; current idle observation is not historical gate baseline','seconds':dt,'clock_ticks_hz':hz,'cpu_visible':os.cpu_count(),'cpu_affinity':sorted(os.sched_getaffinity(0)),'host_execution_cpu_cores':host,'top_stable_process_cpu':sorted(cost,key=lambda x:x['cpu_cores_observed'],reverse=True)[:20],'first':first,'last':last,'collector_cpu_seconds':time.process_time()-cpu,'collector_elapsed_seconds':time.monotonic()-wall,'not_measured':['CPU during prior gate','causal contention attribution','PostgreSQL waits during prior gate','loaded D/W','sampling overhead causal effect']}
Path('docs/evidencias/mod05-vps-host-reposo0110.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['first','last','cpu_affinity']}))
