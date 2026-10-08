# Checkpoint posterior a limpieza del VPS — 2026-10-08

**VALID / COMPARABLE / FAIL.** La única carga autorizada de cuatro workers terminó y fue revisada. COMPARABLE permite una comparación descriptiva, no atribución causal exclusiva a los contenedores detenidos. CR09 continúa abierto, goal automático pausado, cuatro workers de referencia y seis candidata no adoptada. No se ejecutaron 60 ni 900 segundos, ni se modificó el backend.

Fuentes: [manifiesto previo](post-limpieza-recursos-manifiesto0110.json), [cálculos y poblaciones](post-limpieza-recursos-analisis0110.json), [revisión independiente de SHA y retirada](post-limpieza-recursos-ejecucion0110.json), [archivo de registros](post-limpieza-recursos-artefactos0110.json). Los artefactos originales y sus huellas permanecen congelados; las fuentes documentales se liberaron tras comprobar retirada y consistencia.

## Estado del entorno y reposo

Inventario seleccionado Docker estable antes/después de los casi 30 s de caracterización: 69 contenedores, 64 running. No se observó limpieza activa ni carga experimental ajena. Esto verifica estabilidad operativa; la finalización global de la limpieza, su fecha exacta, inventario de contenedores eliminados y recursos históricamente liberados son **not_measured**, sin acta fiable. El contexto posterior a limpieza procede de la instrucción del usuario.

Persisten contenedores detenidos: guacamole (2026-10-07 23:15:23 UTC), privatebin (2026-10-08 01:05:12), opengist (01:10:13), karakeep (01:10:17). opencode figura detenido desde julio. Estas fechas son FinishedAt, no fechas de retirada; todos siguen presentes. Los eventos Docker disponibles no reconstruyen la limpieza: retención acotada, sin inferir cero eliminaciones. No se deduce CPU/RAM liberada de contar contenedores.

Caracterización previa a preparar el fixture: 31 muestras, 29,957555 s, host **2,687469 CPU medias**, mínimo MemAvailable **10.211.614.720 bytes**, swap-in 3 páginas / swap-out 0; iowait 1,15 CPU-s y steal 0,05 CPU-s. El colector consumió 0,111747 CPU medias, incluido en el host. Servicios normales permanecieron activos; una conexión de metadatos a una base propia vacía. Este es el baseline de reposo observado; las CPU históricas bajo carga no lo sustituyen.

Se conservaron `/proc` diskstats e I/O por cgroup con sus ámbitos y ancestros; no sumar particiones, dispositivos virtuales y físicos ni grupos anidados. Cuotas/cpuset/memory.events/cpu.stat se guardan por nivel: user.slice admite `max 100000` y cpuset `0-7`; los interfaces ausentes figuran not_measured. Ocho CPU visibles no garantizan disponibilidad permanente. PSI CPU/memoria/I/O **not_measured**. No se vaciaron cachés ni se alteraron servicios ajenos. Cachés, calentamiento y actividad de almacenamiento son parte del estado experimental, no una condición causal controlada.

## Preparación y comparabilidad

Los 424 archivos apps/config coinciden byte a byte con la referencia histórica; HTTP, colector y fixture usan los mismos instrumentos. Declaraciones pyproject.toml/uv.lock idénticas; versiones instaladas actuales registradas. La referencia documenta Python 3.12.13, Django 5.2.17, Gunicorn 23.0.0 y PostgreSQL 17.10. Huella histórica completa de dependencias instaladas y huella directa del esquema: not_measured. Esquema actual tiene fingerprint de columnas, índices y ledger de migraciones, no imagen física completa ni volcado independiente de todas las restricciones.

Fixture generado de 10.000 anuncios con el mismo procedimiento, cardinalidades y datos sintéticos; UUID y fechas relativas son nuevos, no el antiguo snapshot eliminado. Warmup conservado: seis solicitudes frías y 30 seriales, cinco segundos de reposo en extremos; los cuatro PID observados. Cambios exclusivamente del ejecutor: orden autorizado `[4]`, caracterización previa y fingerprint de catálogo fuera del HTTP/warmup. Sin prepared statements ni cambios de consulta. Comparación funcional de cuerpos vigente; firma, vigencia y objetivo del token verificados antes de normalizarlo únicamente en el comparador.

## Ventana y cohorte

Una sola carga TCP, cuatro workers sync, 20 RPS durante 30 s, 600 dinámicas, ES/EN y 1/3 por familia; un upload separado. Timeout 65 s, drain máximo 70 s. Sin profiler intrusivo.

| Medida | Resultado |
| --- | ---: |
| Programadas / emitidas / no emitidas | 600 / 600 / 0 |
| Éxitos durante emisión, por familia | 92 listado / 92 búsqueda / 92 ficha |
| Throughput completado durante emisión | 9,2 peticiones/s |
| Pendientes al cerrar 30 s | 324 |
| Final cliente: éxitos / errores / pendientes | 600 / 0 / 0 |
| p95 observable cliente, N=600 | 31,047249 s |
| Drain efectivo | 32,389562 s |
| Demora generador p95 / p99 / máximo | 2,210 / 3,931 / 9,422 ms |
| Upload | 1 éxito, HTTP 302 |

Contabilidad reconciliada y generador conforme. FAIL por pendientes >20 y p95 ≥800 ms; no se convierte en PASS por éxitos finales. Los eventos correlacionan 600 dinámicas completas, 200 por familia. Emisión, deadline=emisión+65, timeout observado, entrada/salida WSGI se conservan independientes. Cero entradas y cero ocupación observada posteriores al deadline; cero timeouts cliente. No hay servicio cero imputado a ausencias. Pre-WSGI medio de toda la cohorte: **16,899880 s**, N=600; entradas dentro de emisión: **8,791813 s**, N=280. No identifica una cola concreta de socket/Gunicorn. Ocupación WSGI incluyendo upload: 99,55–99,91 % por worker, sin demostrar CPU saturada.

| Familia | N | Media WSGI, ms | CPU hilo directamente instrumentada, ms | Contribución D, ms | Fracción D |
| --- | ---: | ---: | ---: | ---: | ---: |
| Listado | 200 | 549,511 | 232,858 | 183,170 | 45,068 % |
| Búsqueda | 200 | 575,750 | 236,618 | 191,917 | 47,220 % |
| Ficha | 200 | 94,044 | 49,672 | 31,348 | 7,713 % |

D=Σ(1/3)·media WSGI=**0,406434898 sworker/request**. W=20D+U=**8,211818 sworker/s**; 20D=8,128698 y U=4,987206/60=0,083120. El upload único aporta una estimación N=1 bajo frecuencia contractual de uno/minuto; no se infieren dos/minuto ni precisión reproducible de esa demanda. W es ocupación, no CPU; estas medias bajo la concurrencia observada no son constantes garantizadas al cambiar tasa/recursos.

## Recursos observados

Durante el intervalo muestreado interno a emisión (28,999769 s): aplicación **1,645875 CPU**, PostgreSQL compartido **1,863574**, host **5,859357**, residual ajeno **2,233010**. Aplicación 47,73 CPU-s, PG 54,043229, host169,92. MemAvailable mínimo9.780.961.280 bytes; swap-in/out0/0 páginas; iowait0,98CPU-s. Máximo observado4 conexiones propias /9 compartidas. Estados propios activos:58 muestras sin wait_event y1 ClientRead; no convertir muestras en duración. Dockerd destaca entre procesos persistentes (28,35CPU-s); son cotas observadas, no atribución de todo el residual.

Cohorte cubierta por muestras desde −0,465 hasta +62,535 s: app105,09CPU-s y PG compartido114,677997CPU-s, incluidos márgenes. CPU de hilos dinámicos WSGI103,829602CPU-s es una observación distinta. El ratio CPU/emisión-éxitos usa270 éxitos del intervalo exacto y expresa eficiencia operativa, no coste individual. CPU PG individual/request, I/O proc PG no accesible, overhead causal, allocations y SQL normalizado/filas/reglas/render concurrentes: **not_measured**.

Colector:90 muestras/89,893913s,0,101172CPU medias,p95 de sondeo147,548ms, sin error fatal ni parada por límites. Instrumentación ligera no significa overhead cero; snapshots secuenciales y procesos transitorios limitan atribución. No atribuir execute a CPU PG ni total−SQL a validación; eventos lazy y tiempos internos históricos no se suman como desglose causal del HTTP actual.

## Comparación con los dos bloques históricos de cuatro workers

| Referencia | D histórico, ms | Diferencia D actual | Pre-WSGI medio: diferencia | Éxitos emisión: diferencia | CPU host: anterior → actual | Residual ajeno: anterior → actual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Primero 4W |427,814|−21,379 ms (−4,997 %)|−1,623 s|+12|6,438 →5,859|3,030 →2,233|
| Segundo 4W |418,046|−11,611 ms (−2,778 %)|−0,912 s|+12|5,948 →5,859|2,384 →2,233|

Cambian tanto servicio como demora previa y competencia del host. Un solo bloque posterior no establece causalidad de la limpieza. Comparación descriptiva COMPARABLE con límites explícitos; la comparación causal 4/6 histórica permanece INCONCLUSIVE y sus FAIL intactos. No hay una mejora nueva del backend: su código no cambió.

## Decisión y cierre

**No habilitar el gate de 60 s, no ejecutar 900 s y no adoptar seis workers.** La matriz actual concentra 92,287 % de D en listado+búsqueda (7,501738sworker/s a20RPS); ficha0,626959. Priorizar trabajo evitable de esas dos familias, reutilizando perfiles y planes SQL existentes para identificar un mecanismo con coste absoluto vigente antes de cambiar código. Este checkpoint no mide su reparto SQL/reglas/render y no decide un refactor por nombre. No atribuir ahorro a fichas ni encadenar variantes CASE descartadas. La competencia ajena sigue siendo medible y relevante; esta observación no autoriza cambiarla.

La revisión independiente confirmó huellas, artefactos y retirada de las tres bases propias, media temporal, master y cuatro workers. Se conservan registros; los servicios normales no se retiraron. Prueba PostgreSQL real: pytest correcto verifica ejecución diagnóstica, **no convierte FAIL de carga en PASS**. Contrato10000/20RPS900s/p95<800ms/errores<1%, uploads y todos los umbrales vigentes intactos; FAIL corto histórico e INVALID contractual anteriores conservados. Goal pausado, CR09 abierto y porcentajes sin cambios.
