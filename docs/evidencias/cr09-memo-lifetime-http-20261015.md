# Correctiva del memoizador: carga limpia

Run `20261015-211213-04ef9338`, SHA `392c2c8`: **FAIL184.09s**. [Terminal, versiones, casos y limpieza](cr09-memo-lifetime-http-terminal-20261015.json), [preparación](cr09-memo-lifetime-http-preparacion-20261015.json), [correctiva y18controles](cr09-grafo-recorrido-solucion-20261015.md).

4sync/20rps60s/10k sintéticos/Celery2+Beat/una subida; generador freeze anterior. Sin observadores de workers, perfiladores ni pg_stat_statements. Python3.12.15/Django5.2.17/Gunicorn23.0.0/PG17.11. Controller4CPU/3584MiB/swap0/Tasks512; PG1CPU/1536MiB/swap0/pids128; Redis0.2CPU/128MiB/swap0/pids64. Watchdog exterior300s frente900s anterior, ninguno alcanzado; deadline65s/drain70s del tráfico intactos.

Fuentes congeladas idénticas; raíz/hijo/Celery ausentes; temporal/contenedores propios retirados; Gunicorn detenido; unidad MainPID0/ControlGroup vacío. Metadata pg_server_shared/stack normal heredada incorrecta, contrastada con nombres/label/adaptador propios. Ningún servicio normal ni datos reales.

|Métrica|Anterior1dd8041|Actual392c2c8|
|---|---:|---:|
|p95 completo|1.126775899s|0.919813976s|
|p50 completo|0.232267147s|0.262637643s|
|p95 servicio Gunicorn, excluye espera anterior|0.313512s|0.314390s|
|Pendientes al60s|3|3|
|Completadas finales|1200|1200|
|Errores/timeouts/omisiones|0/0/0|0/0/0|
|Peticiones >=0.8s|106|79|

Reducción observada p95 **18.37%**, sin atribución causal ni reproducibilidad; p50 empeora. Sólo falla latencia, demás checks cortos pasan. No repetir FAIL/15min/N3.

|Caso,200peticiones por ejecución|p95 anterior|p95 actual|
|---|---:|---:|
|es:listing|1.148124193s|0.919813976s|
|en:listing|1.154844674s|0.990497685s|
|es:search|1.117647413s|0.943729301s|
|en:search|1.154643680s|0.924010417s|
|es:detail|1.042584209s|0.806286531s|
|en:detail|1.033814534s|0.804293420s|

|Cohorte por emisión|p95 anterior|p95 actual|Lentas anterior→actual|
|---|---:|---:|---:|
|0–5s,100|1.376427054s|1.207005312s|89→79|
|5–10s,100|0.953755005s|0.709047809s|17→0|
|10–15s,100|0.454106778s|0.454853713s|0→0|
|15–60s,900|0.461336160s|0.599949569s|0→0|

Todas las79 lentas se emitieron0–5s; no excluirlas ni usar régimen posterior como aceptación. Cola inicial persiste; servicio Gunicorn casi igual no demuestra identidad causal del trabajo interno. Ciclo del campo demostrado rojo/verde y18controles; no es prueba de cuello único ni mejora p95 exclusivamente debida a él. No atribuir diferencias del portátil al código: cambiaba el perfil energético al alternar cargador.

Retener correctiva por defecto reproducible/controles funcionales, no como optimización p95 aceptada. Usuario solicita reanalizar/descomponer e investigar antes de otra intervención: refrescar grafo, presupuesto por tramo y diagnóstico separado sólo para huecos necesarios. CR09→CR10→GS01→BF/BB→C y N3 abiertos.
