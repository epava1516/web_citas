# Contraste fijo8sync del producto actual dentro de4CPU

Prototipoaislado web_modelos_cr09_eight_sync_current_20261015, base6332348, commits60c8e26/ddf2d19. Sin integración ni cambioDocker/servicionormal. SóloselectorCI explícitoSYNC8 exclusivo aPGpropio ytests; default4sync permanece. No gthread ni cambio worker_connections, dependencias, CPU/memoria/PG/Redis/tasks/swap.8procesos **no son8CPU**.

Justificación previa: actualingress PG≈0.603coresinitial/0.466steady sinthrottle, controller≈2.11/2.05deafinidad4, WSGImedio0.230/0.184s yCPUthread0.110/0.100. Las pilasexternasobservanesperaSQL. Con4sync cada petición ocupaunslot duranteIO; secontrasta unúnico8syncestándar, cuyo dispatch comparte socketkernel yno colaThreadPoolporproceso. [FuenteGunicorn23](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/design.rst). No garantíadebeneficio nibypassproxy/defensasnecesarias. HistóricoFAIL8sync conproductomuchomáscostoso se conserva, noextrapolarcapacidadactual. No barrido deparámetros.

Prechecks7PASS0.18s: default4 intacto, SYNC8sólo1/PGpropio, rechaza gthreadmezclado yservicionormal; preservareferenciafirmadadeorden. Primercomando con --no-cov fue rechazado antesdetests(pluginnoinstalado); retiradoargumento, sininstalardependencias.

[Paridad real](cr09-eight-sync-current-parity-terminal-20261015.json):230607FAIL60.26s por404distinto (mismostatus404, DEBUG1runtimeCI vsDEBUGFalsepytest), fuente/limpiezaverificadas. FixtureTCP corregidaexplícitamenteDJANGO_DEBUG0 como elbenchlimpioyausaba; no cambiaappoaflojaasserthash. Reejecución230849-565d78b5SHA ddf2d19 **1PASS60.99s**.54positivas(30secuenciales/24paralelas)ESENlist/search/detail conhashbodyexactoyfirma/vínculodenuncia comprobados;24negativastrasrevocarconsentimiento(16listas200sinexposición/8fichas404), cuerposnativos exactos. Los8PIDssirven, pico8WSGIactivos,nooverlapenunmismoprocesosync. Fuentecongeladaexacta, root/UVchild/8workersausentes,temporal/containerspropiosretirados,MainPID0/ControlGroupvacío.

## Ensayo preregistrado

Uncorto60s/20rps/10k/1subida/Celery2+Beat, reglas existentes deBeat5s/generadorfreeze/seisprobes sin cambios,8sync con mismos4CPUafinidad0–3/controller3584MiBswap0pids512;PG1CPUafinidad4/1536MiBsinwap/pids128;Redis0.2CPUafinidad5/128MiBsinwap/pids64. MismoPy3.12.15/Django5.2.17/Gunicorn23/PG17.11/kernel; sinperfiladores/observadoresworkers. SiFAILpreservar/separardiagnóstico,norepetirciego. SiPASSrepetiruna vez sin cambios antesdelcontrato15min. No aceptarCR09/N3porpuertasdedelivery. RuntimeDocker2predeterminado vsbenchmark4/8requierecoherencia antesdeaceptaciónreal; aun noresuelto por estetexto.

## Resultado inicial y corrección del entorno

Ensayo `20261015-231207-2cdf7e03`, SHA `ddf2d19`: FAIL, p95 HTTP 0,844573358 s; 1200 solicitudes completas, cero errores, omisiones o timeouts. La referencia de cuatro procesos `20261015-222515-91a6b5da` obtuvo 1,218890056 s, también FAIL. **La comparación está condicionada:** una auditoría posterior de hashes encontró que el worktree de ocho procesos carecía del kernel canónico compilado y el loader utilizaba `python-reference`; la referencia de cuatro tenía `native-sealed`. No atribuir la diferencia a la topología ni declarar reproducibilidad. La paridad anterior también se ejecutó antes de esta corrección.

Se conservan el fallo y los artefactos. Se construyó el kernel con Python 3.12.15 / Cython 3.0.12 / GCC 11.5.0 mediante el builder existente, sin sobrescribir un directorio previo. Unidad `cr09-eight-sync-native-build-20261015` terminada. Identidad verificada `native-sealed`, fuente SHA256 `9cecbd34c3b8286c4bdfd35708a8c2f935b96457d57ce8b9cbfc9d94614afaf9`, binario SHA256 `40e0d739839f0b56f9057b15685b363e2963493a6822bf45bba48e4215b60d19`. El binario depende de la ruta de compilación; no se afirma igualdad binaria entre worktrees.

Commit aislado `3a88118` registra la identidad del kernel en los resultados TCP/HTTP. El adaptador propio comprueba obligatoriamente `native-sealed` antes de crear recursos y escribe `canonical-environment.json`. La comprobación funcional nativa está iniciada en `cr09-eight-sync-native-parity-20261015`; aún sin resultado. Sólo tras PASS y limpieza verificada procede un ensayo limpio con este requisito corregido. No cambia código de aplicación, dependencias, límites ni umbrales.

## Paridad funcional con kernel nativo

`20261015-232113-3ba2c291`, SHA completo `3a881187bc5510096e106851a5e84d9ddbf0f960`: **1 PASS / 59,97 s**, kernel `native-sealed` registrado en `tcp_matrix`. 54 muestras positivas y controles negativos de revocación conservados por el mismo test. Los ocho procesos sirvieron peticiones y sus PID quedaron ausentes al terminar. Verificación independiente: hashes iguales a `source-hashes.json`, controlador y pytest hijo ausentes, temporal eliminado, ambos contenedores propios ausentes; unidad MainPID=0, ControlGroup vacío. Ruff pasó para ambos tests modificados.

Iniciada medición corta limpia nativa en `cr09-eight-sync-native-clean-20261015`: mismo SHA, ocho sync dentro de afinidad 0–3 y límites ya descritos, `--benchmark-normal-refresh --benchmark-generator-freeze`, sin instrumentación de workers ni perfiladores. Resultado pendiente.

## Resultado corto nativo: FAIL conservado

[Recibo terminal](cr09-eight-sync-native-clean-terminal-20261015.json), ejecución `20261015-232322-b808066f`, SHA `3a881187bc5510096e106851a5e84d9ddbf0f960`: **1 FAIL / 183,52 s**. Generador válido, 1200 programadas/emitidas/completadas, cero errores, timeouts, omisiones y pendientes finales. Subida 302. Sin perfiladores ni observadores de workers; kernel `native-sealed` registrado.

| Ejecución | Procesos | Kernel | p95 HTTP s | Estado |
| --- | ---: | --- | ---: | --- |
| 222515-91a6b5da | 4 | nativo | 1,218890056 | FAIL |
| 231207-2cdf7e03 | 8 | Python de referencia | 0,844573358 | FAIL; entorno condicionado |
| 232322-b808066f | 8 | nativo | 1,792941386 | FAIL |

Por caso (400 peticiones cada uno): listado 1,833467318 s; búsqueda 1,916174902 s; ficha 1,577638230 s. p95 de servicio Gunicorn 0,401420 s; no equivale a latencia HTTP ni mide por sí solo la cola. Generador p95 1,952 ms / p99 3,297 ms / máximo 5,299 ms.

125 respuestas >=0,8 s: 95 emitidas en segundos 0–5 y 30 en 5–10. Ninguna después. Cohortes p95: 0–5=2,417398 s, 5–10=1,280170 s, 10–15=0,317695 s, 15–60=0,365643 s. El arranque sigue dominando el fallo; no prueba su causa. Ni el efecto del kernel ni el de los procesos quedan causalmente aislados por ensayos únicos en tiempos distintos. No se integra 8sync ni se repite ciegamente o se inicia la carga de 15 minutos. El siguiente diagnóstico debe separar arranque/espera pre-WSGI y servicio en este entorno correcto.

Fuentes comprobadas independientemente contra el recibo inicial; controlador, pytest hijo y PID Celery ausentes; temporal y contenedores propios retirados; unidad terminal fallida con MainPID=0/ControlGroup vacío. Los flags heredados `pg_server_shared` del JSON son incorrectos para este adaptador: PostgreSQL/Redis fueron propios y limitados. Se conserva el JSON original, sin corregir retroactivamente sus campos. CR09/N3 abiertos.
