# Diagnóstico actual: espera acumulada y pico inicial dentro del worker

Run223005-7347b70d, SHA35babb0, producto3ba2ec4, **FAIL185.50s instrumentado**. [Recibo](cr09-query-structure-ingress-terminal-20261015.json). Mismascondiciones nominales/cuotas propias, ingresssinimportshandlers yWSGI/SQL/GC, CPUcgroups1Hz.1200IDs cliente/WSGI/servicio emparejadosexactos,0parseerrors,1200status200,0errores/timeouts/omisiones,1subida302. Fuentes congeladas exactas,7PIDsworker/Celery ausentes yroot/child/temporal/contenedorespropiosretirados; unidadMainPID0/ControlGroupvacío. Consumoobservadores/heapoverhead no cuantificados.

p95instrumentado1.123788s, no ganancia/regresión comparable con limpio1.218890s.152casos>=0.8s:93emitidos0–5s,59entre5–10s,ningunodespués. Workers289/282/319/310requests, cuatroprimerasentradas antes0.102s; no worker ausente durante todoarranque.

|Media de las mismasrequests por emisión|0–5s,100|15–60s,900|
|---|---:|---:|
|HTTPcompleto|1102.264ms|215.361ms|
|Emisión→WSGI|872.166ms|31.272ms|
|WSGIwall|230.298ms|184.289ms|
|CPUthread|110.022ms|99.954ms|
|SQLwall,inclusivo|105.755ms|73.613ms|
|CPUclienteSQL,inclusiva|8.078ms|7.295ms|
|GCwallsolapado|7.123ms|7.123ms|

No sumar particiones inclusivas ni restarp95. Residuo posterior ligeramente negativo porcloseWSGI despuésde recepción/cierreaccesslog, conservado. Emisión→WSGI incluyecliente/transporte/admisión/parseo/scheduling, no cola exclusiva. Las152lentas tienenmediaHTTP1061.565ms,preWSGI847.698ms yWSGI214.061ms.

|CPU ejecutada cgroupspropios, coresmedios|0–5s|15–60s|
|---|---:|---:|
|PostgreSQL|0.6030|0.4658|
|Controllercompleto|2.1099|2.0470|
|PGperiodosthrottled|0|0|

No prueba que másCPUsolucione; controllerincluyegenerador/Celery/observador yningúncounterdepresión/steal delhipervisor enestacaptura. SQLwall no es CPUbackend. No hostexclusivo supuesto, no cambiosgovernor/sysctls ni serviciosnormales.

## Pico que requiere atribución antes de otro cambio

Una deprimeraspeticiones, d-1, atiende1.208s dentrodelworker3006598:CPUthread0.602s,SQLwall0.513s,GCsolapado0.093s. Otra d-3 WSGI0.705s/CPU0.177s/SQL0.480s. Primertramo concentra ramasgenerales dedirty(caller388/446), no sólolecturasdeproyección. Valoresinclusivos, no descomposición exacta ni pruebaúnicacausal.

Subida u-0 ocupa otro worker0.468596s,CPU0.300078s,SQL0.125556s,GCsolapado0.112586s,devuelve302. Taskrealmedia empieza0.464s ytermina1.408s:0.944112swall/0.598033sCPUthread. Por tanto cargaHTTPsubida yprocesamientodefondosondistintos. No sustituircon subida falsa ni sacarladelescenario.

El GCmedio inicial no excede alestable; sus picos estánlocalizados,por loque nojustificadesactivarGC,congelarheap ni retomarcollectstartup ya descartado. Delmismomodo, no atribuirCPUdelpicoaORMsóloporperfilaisladoprevio: aúnfaltanstacks delworkerreal duranteeseintervalo. Instrumentación interna puede alterarheap/arranque; el ingresscorrigeimportsanticipadosdelhookanterior pero no demuestraoverheadcero.

Siguientecontraste finito: muestreo externo py-spy0.4.2 deGunicornpropio y4workers,acotado alarranque/coldprobes yprimerossegundos, sin importar wrappersenlaapp. Comprobación depropiedad/ancestry/startticks/cgroup/PIDs antes deadjuntar, capturas sinlocals,hash/versionherramientas, sinotrosperfiladores ylimpieza propia. Registrarinstantes decaptura/ventana yerroresdemuestreo; no llamarloCPUexacta ni mediciónlimpia,ni usarunflamegraph paraexplicarlacola. [Documentación primaria py-spy](https://github.com/benfred/py-spy):--subprocesses incluyeworkers, --idle cambia población y--nonblocking admiteerroresmuestrales. No ejecutarotro candidato antesde atribución.

Producto3ba2ec4conservadoporsuahorroaislado/frescura; sinpruebadegananciaHTTP. Último limpio1.218890sFAIL. CR09/N3/objetivoíntegroabiertos.
