# Comparación experimental 4 frente a 6 workers — resultado revisado

Cierre2026-10-08, CR09-REND-LECTURA abierto y goal automático pausado. [Autorización/cola única](../17-seguimiento-desarrollo.md), [propuesta prefijada](propuesta-capacidad-4-vs-6-0110.json), [manifiesto](comparacion-capacidad-4-vs-6-manifiesto0110.json), [ejecución y revisión independiente](comparacion-capacidad-4-vs-6-ejecucion0110.json), [cálculo y poblaciones](comparacion-capacidad-4-vs-6-analisis0110.json), [artefactos y SHA](comparacion-capacidad-4-vs-6-artefactos0110.json).

**Comparación causal INCONCLUSIVE; filtro observado de efecto incumplido; cuatro bloques FAIL.** Seis completa más peticiones dentro de la emisión y reduce la demora previa, pero D aumenta más del10% permitido en ambos pares. La competencia externa difiere0,646410CPU entre bloques, superando0,5. No aceptar seis, ejecutar tasas inferiores automáticamente ni repetir por ruido. No se ejecutó el gate60s ni900s; permanecen FAIL corto e INVALID contractual anteriores, contrato/porcentajes intactos.

## Escenario y validez

Dos pares completos4→6 y6→4: una carga y un servidor experimental cada vez. Cada bloque20RPS30s,600dinámicas de10.000anuncios,200porfamilia/listado-búsqueda-ficha,100porcada rutaES/EN;1upload separado. Timeout cliente65s, drain máximo70s, todos los umbrales anteriores. Gunicorn sync conserva timeout servidor60s, configuración idéntica salvo4/6workers. Sin despliegue, cambiosPG, caché, preparedstatements ni modificaciones debackend. Reutilizadas equivalencia común21PG y matriz4PG; no repetidas.

Una sola preparación creó datos, draft privado, sesión y esquema; ANALYZE una vez antes de congelar. Cada bloque usó una copia de esa base y medios iniciales, conservando UUID/cuerpos y evitando que el upload anterior crease duplicados en el siguiente. Mismos bytes del upload. Puerto/mezcla/rutas/regimen de warmup constantes:6probes fríos y30seriales,5s de idle en extremos. Uploads separados135,759/112,086/111,481s, todos302. Cachés OS/PG compartidas no reiniciadas ni declaradas frías; la aplicación conserva DummyCache.

El [preflight inicial](comparacion-capacidad-preflight0110.json) terminó antes de emitir carga por un comparador literal incompatible con TimestampSigner de la ficha; fuentes/limpieza revisadas. El ejecutor corregido verifica firma, vigencia≤7200s y objetivo listing/revision exacto, y normaliza exclusivamente ese token en el comparador. Resto del cuerpo idéntico y SHA crudo/normalizado registrados; listado/búsqueda comparados byte a byte con recuento10.000. No se modifica respuesta, autoridad o ruta. Es una reparación de preflight, no repetición de un resultado de carga negativo.

Las cuatro ejecuciones tienen600emitidas/600terminales,0noemitidas,0errores/timeouts/finales pendientes; contabilidad reconciliada.2400paresWSGI dinámicos únicos,200porfamilia/bloque, sin solapamiento de intervalos por PID;400projection/200native porbloque. Todo el pool estaba inicializado antes del warmup. En las30referencias instrumentadas se observaron3/4,4/6,5/6 y4/4workers; los6probes sin ID no permiten completar esa cobertura. Warmup equivalente por calendario y solicitudes, sin afirmar que cada ruta calentó cadaworker; esta limitación no se convierte en un nuevo gate retrospectivo.

| Bloque / workers | Demora generador p95 / p99 / max,ms | Drain cliente,s | Veredicto30s |
| --- | ---: | ---: | --- |
|1 /4|3,579 /7,356 /13,508|35,693|FAIL|
|2 /6|3,973 /11,966 /34,014|20,015|FAIL|
|3 /6|4,552 /10,687 /26,013|21,322|FAIL|
|4 /4|2,138 /6,745 /30,805|34,182|FAIL|

Todos los generadores cumplen≤10/25/100ms. El FAIL de cada bloque procede de p95≥800ms y pendientesventana>20, con uploads/contabilidad/drain conformes. Pytest1PASS/520,448s solo significa diagnóstico completo.2pruebas sinDB verificaron antes el opt-in de parada/ledger parcial y5muestrasCPU/nuevoOOM,0,27s; no aceptación funcional nueva ni capacidad.

## Ventana de emisión — cliente y recursos

| Bloque / workers | Éxitos listado / búsqueda / ficha | Éxitos/s | Pendientes30s | App / PG / host CPU medias | Residual ajeno CPU medias |
| --- | ---: | ---: | ---: | ---: | ---: |
|1 /4|88 /88 /88|8,800|336|1,561 /1,719 /6,438|3,030|
|2 /6|116 /116 /117|11,633|251|2,091 /2,206 /7,183|2,759|
|3 /6|112 /110 /112|11,133|266|2,045 /2,167 /7,175|2,833|
|4 /4|88 /88 /88|8,800|336|1,638 /1,798 /5,948|2,384|

CPU procede de contadores, con intervalos interiores de≈29s y offsets explícitos enJSON; no se extiende uniformemente a30s. Residual=(CPUhost−CPUapp−CPUservicioPG−CPUpropia del cliente/colector/pytest/runner)/intervalo. Incluye kernel/actividad no observada y límites de muestreo; no es atribución individual a un servicio. Procesos persistentes/command-cgroup y sus CPU se conservan sinargv/env. Diferencia máxima3,030228−2,383817=0,646410>0,5: **comparación causal inconcluyente**, aunque las diferencias porpares0,271638/0,449456 estén bajo0,5. No restringir retrospectivamente el límite solo a pares favorables.

Las medias/percentiles emisión→entradaWSGI de quienes entran antes de30s, su N y ocupación porPID/upload figuran aparte enJSON. Esa población se selecciona por entrada dentro de ventana; las pendientes no son demora cero. OcupaciónWSGI no es CPU; el intervalo anterior aWSGI no localiza socket/Gunicorn.

CPUapp del intervalo dividida entre éxitos del mismo intervalo es eficiencia operativa de esa ventana, incluidos trabajos de pendientes. No coste individual/request. PostgreSQL compartido incluye backgrounds/otras bases; el subconjunto debackends propios mapeadosNSpid es límite inferior con churn. No derivar CPU desdeexecute.

## Cohorte completa y demanda de workers

Medias directamente observadas, N200 porfamilia en cada bloque. D=Σp_i·E[T_WSGI,i], p_i=1/3; segundos deworker/request. W20=20D+U, Ucontractual=serviciodelupload/60. Este W es cálculo condicionado a dichas medias y frecuencia; no capacidad niCPU. Udiagnóstico=serviciodelupload/30 se conserva separado; en la ocupación observada se integra el upload real.

| Bloque / workers | Listado / búsqueda / ficha medios,ms | D,s | W20+upload contractual,sworker/s | PreWSGI media cohorte,s | p95 cliente,s |
| --- | ---: | ---: | ---: | ---: | ---: |
|1 /4|577,942 /599,069 /106,432|0,427814|8,641950|18,523|34,238|
|2 /6|654,438 /674,889 /132,499|0,487275|9,842898|10,503|19,465|
|3 /6|671,708 /692,358 /136,402|0,500156|10,106363|11,228|20,523|
|4 /4|571,022 /585,215 /97,902|0,418046|8,446934|17,812|32,718|

Los valores exactos porfamilia enJSON prevalecen sobre el redondeo. UploadWSGI5,140/5,844/6,194/5,160s(N1/bloque); CPUhilo0,580/0,616/0,726/0,741s. Final:600éxitos cliente,0fallos/timeouts porbloque. Marcas independientes porID: t_emission, t_deadline=t_emission+65, t_client_timeout_observed, t_wsgi_entry, t_wsgi_exit. Cero entradas o trabajo observado después deldeadline; no reclassificación de respuestas tardías. La reconstrucción histórica79entradas tardías no cambia.

CPUapp directamente observada en intervalos que **envuelven** la cohorte:105,610/106,080/107,540/107,720CPU-s. ServicioPGcompartido110,001/107,803/109,370/113,496CPU-s. Intervalos respectivos≈67/51/53/65s; límites relativos alinicio−0,538→66,462/−0,289→50,711/−0,732→52,268/−0,536→64,464s. Incluyen márgenes de muestreo y actividad fuera delrequest, no CPUindividual; eventos de CPUhiloWSGI porfamilia son una medición distinta y se documentan enJSON. No atribuir la CPUcompartida a las600peticiones individuales ni sumar estos contadores conCPUhilo.

## Efecto, límites y decisión

Primerpar:6completa+32,197%, reducependientes85 y preWSGI8,020s, p95−14,773s; D+13,899% y W20+1,200949sworker/s. Parinverso: +26,515%, pendientes−70/preWSGI−6,584s/p95−12,195s; D+19,641%, W20+1,659429. Errores0ambos. Se cumplen los componentes de completaciones/p95/errores, **incumple D6≤1,10D4 en ambos**. Son diferencias observadas; el límite ajeno impide aceptarlas como efecto causal reproducible de workers. El p95 no está dominado por timeouts en estos bloques; se usan también completaciones/ocupación/servicio yCPU.

Se muestrearon cuotas/cpuset/throttling/memoria/PSI, conexiones/wait_event_type, IOdisponible y competencia. No cuotaCPUfinita encontrada eninterfaces/ancestros disponibles, cpuset0–7; ochoCPUvisibles no reservadas. Sin paradas por5muestras≥7,6CPU, MemAvailable<2GiB o nuevosOOM. SnapshotCPU puede superar7,6puntualmente; no se aflojó la condición sostenida. MínimosMemAvailable8,240/8,134/6,642/8,574GB; RSS baseline/máximo/final, eventos/throttling/VMstats y servicioPGcgroup enJSON. No ausencia universal de presión por estas observaciones. Colectores:94/79/81/93muestras, p95poll181/208/195/168ms y0,114/0,112/0,116/0,112CPU medias. Cobertura≥90% y controlesinstrumentalesprevios cumplidos.

PSIcpu/memoria/IO: **not_measured** porinterfacesausentes. ProcIO dePG: **not_measured** porlectura no disponible; procIOapp, io.stat ydiskstats disponibles tienen ámbito/snapshots propios, no filasSQL/IOporrequest. Conexiones propias máximas4/6/6/4excluyen elcolector1; estados deespera son **muestras**, no duraciones. SQLdominante/validación/render detallados deeste experimento, allocations yoverheadcausal deWSGI/GC/metadata: **not_measured**. Los perfiles/planes anteriores se reutilizan con sus escenarios/versiones; no validar como total−SQL ni atribuir execute aCPUPG.

**Decisión:** no conservar seis como una adopción ni habilitar60/900s; sigue candidata y cuatro referencia. La ampliación aislada no satisface el filtro ni elSLO en lo observado; no resuelveCR09. Priorizar eliminar trabajo absoluto nuevo demostrado enSQLprincipal/construcción de página, contrastando los planes/perfiles existentes antes de escoger mecanismo y sin encadenarCASEni alterar autoridad/elegibilidad. La causa exacta de inflación deD queda hipótesis; estos datos no autorizan atribuirla a planificación/colaCPU/PG concreto. Una eventual reevaluación deconcurrencia requeriría fuente nueva y host comparable; **no se encola una repetición ni escalera de tasas automática**. Sin aumento de recursosPG, caché, reescritura general o consistenciaeventual.

Retirados y comprobados master/20workers propios, las6bases propias (base, plantilla y4clones) y medios; procesos/servicios normales intactos. Fuentes congeladas durante toda la secuencia y revisión, luego liberadas para documentación/DAFO/Graphify. [Archivo íntegro9,53MB](comparacion-capacidad-4-vs-6-artefactos0110.tar.gz) conserva registros, huellas, código acotado e instrumentos/revisores ejecutados. Resultado experimental revisado; CR09, porcentajes, FAILcortos e INVALIDcontractual conservados.

Recalculo aritmético sinHTTP/DB ni nuevaspruebas: `.venv/bin/python docs/evidencias/recalcular-comparacion-capacidad0110.py /tmp/worker-capacity-4-vs-6-ready0110` (o directorio extraído delarchivo). CompruebaSHAraw y recalcula completaciones/p95/D/W/residualhost/filtro; confirmado idéntico aJSON. No vuelve a comprobar un estado vivo histórico ni sustituye su revisión independiente yaarchivada.
