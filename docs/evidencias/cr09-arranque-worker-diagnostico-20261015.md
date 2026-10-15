# Atribución del arranque en procesos web reales

Run `20261015-194749-a0cface7`, SHA `8724a6b`: diagnóstico instrumentado **FAIL185.91s**. [Recibo](cr09-arranque-worker-diagnostico-terminal-20261015.json), [preparación y límites](cr09-arranque-worker-diagnostico-preparacion-20261015.json). Producto intacto desde3594311; sólo se añadióGC al observadorexistente y se verificó11PASS0.76s. Misma mezcla/carga/cuotas; sinprofiler niPGstatementtracker.

Fuentes idénticas, raíz/pytest/4Gunicorn/4CeleryBeat ausentes, temporal yPGRedis propios retirados, unidad terminal/MainPID0/ControlGroupvacío. CollectorCPUsummary sinerror; parseobserver0errores. Se emparejan1200IDs dinámicos únicos completos conWSGIstart/end y200cada caso, todos200; subida302separada. Distribución4procesos286/313/307/294.

Instrumentación: context/validation/render inclusivos, SQLexecute wall/threadCPU con fingerprints ycallerssinpayload; GCcallbacks sinpolicy/forcedcollect; contadores1Hz cgroupspropiosPG/controller. Estos tiempos **no son particiones aditivas**. GC se solapa concontext/render/SQL; SQLwallnoesCPUbackend, controller incluyegenerador/Celery/app/collector. EntradaWSGI noesTCPaccept, lapsoemisión→WSGIincluyeTCP/scheduling/admisión,no colaexclusiva. Callback/wrapperoverhead no medido causalmente.

| Media por petición en mismo diagnóstico | Emisión0–5s | Emisión15–60s |
|---|---:|---:|
| N |100|900|
| WSGIwall |236.21ms|191.53ms|
| CPUthreadapp |115.73ms|107.40ms|
| SQLwall |103.25ms|74.21ms|
| GCwallsolapado |12.35ms|8.64ms|
| CPUrender |21.87ms|22.11ms|

| Cgroup, ejecuciónmedia encores (1Hz porpunto medio) |0–5s,5muestras|15–60s,45muestras|
|---|---:|---:|
| PostgreSQLpropio |0.7903|0.4715|
| Controllercompleto |1.9427|2.1971|

AntesWSGI medio0–2s=.850235s,2–5s=1.050029s,5–15s=.435800s,15–60s=.118172s. Se observa cola previa alWSGI durantearranque, no inferir que sea trabajoPython dentro de esaspeticiones. SQL del caller `read_publication_values`L239 pasa45.47ms/req emisiones0–2s a16.78ms emisiones15–60s, con número de consultas ymezcla porcohorte distintos; no atribuciónexclusiva dehidratar/planning. Búsqueda/count/page yotraslecturas contribuyen.

GCgeneration2 observadoenprimeraspáginas: d-7=.1455s, d-9≈.13s,d-13=.115s,d-18=.1657s (intervaloswall incluyen scheduling); mayorGCtotalporrequest.17036s. También d-1050=.1508s y d-891=.1488s gen2; no mecanismoexclusivamentefrío. CPUgcgeneración2ronda.09–.12s enestoscasos. Explica trabajo material dentrodealgunaspeticiones, no causaúnicadeltransitorio. RenderCPUmedio no aumenta de forma material encohortes; no hayevidenciapara primarplantillas oañadircalentamientodeprueba.

p95 instrumentado1.218724517s,0errores/timeouts/omisiones y1200finales; no compararlo como regresión conp95limpio.897765506s porque añade observadores. El FAIL se conserva, noaceptaCR09/N3ni15min. No repetirloadsinintervenciónprobada. MetadatosPGshared/textonormalstack heredados preservados ycontrastadosconnombre/label/adaptador propios; noaccesoaserviciosnormales.

Decisión: queda evidencia de planificación/hidratación fría y pausasGC periódicas, sin único culpable demostrado. Siguiente prueba finita: medir planificación genérica **sólo de la hidratación de la página seleccionada**, usandoelGUCtransactionallocalyaacotadoconjit/join, manteniendoautoenpoblación/búsquedas/otraslecturas. Contrastar coste de SET/restauración y semántica real, nested/SQLerror/transacciónheredada antes deotrocleanload. Si no ahorra coste temprano, descartarlo; no forzarglobal ni barrerumbrales/workers. No cambiarGCahora sólo porque hayaeventosgrandessolapados. ObjetivoíntegroCR09→CR10→GS01→BF/BB→Csigueabierto.
