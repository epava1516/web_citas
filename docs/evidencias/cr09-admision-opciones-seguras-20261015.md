# CR09: opciones seguras de admisión, revisión acotada 2026-10-15

Propuesta independiente sobre base `1e325e9`, pendiente de verificación de Codex. Sólo lectura de fuentes/recibos y escritura de este documento; sin pruebas, carga, servicios, cambios de dependencias ni aceptación CR09/N3.

## Decisión priorizada

**No se justifica todavía una intervención de configuración/carga en admisión.** Mantener gthread experimental rechazado y el foco ya documentado en población/conteo/joins (`docs/17-seguimiento-desarrollo.md:2113`). La identificación de una cola desequilibrada merece una corrección segura, pero no convierte un límite de conexiones en límite seguro de trabajo ni invalida el FAIL de ocho sync. No ejecutar otro barrido de procesos/hilos/conexiones.

Si se abre un trabajo específico de admisión, su siguiente paso mínimo será revisión fijada a commit de una corrección upstream del bucle, con contrato de liveness y pruebas pequeñas adversariales antes de implementar o medir. No se propone copiar master, actualizar Gunicorn ni escribir un servidor propio. Falta demostrar una solución compatible con Gunicorn23 que conserve progreso al límite y acote admisión sin bloquear el selector; es el desconocido concreto que impide recomendar un cambio ejecutable ahora.

## Hechos y límites

El recibo `cr09-gthread-admision-diagnostico-terminal-20261015.json` concilia1200 peticiones sintéticas: p95 emisión→creación1.558ms, creación→enqueue1.492ms, enqueue→handler21.369s, servicio0.879s. Dos procesos quedan sin WSGI dinámico en últimos10s mientras otros siguen ocupados; distribución359/217/252/372. Prueba desequilibrio local de despacho en esa ejecución, no causalidad exclusiva del executor: `scripts/benchmark_gthread_observer.py:24-38` mide antes de inicializar/submit y al entrar en handle. Percentiles no son sumables. El limpio gthread21.694s frente4sync21.846s sigue FAIL (`cr09-gthread-http-terminal-20261015.json:37-39,1195`).

PG ejecuta0.949CPU de una CPU fijada durante llegadas, sin CFS throttling; controlador1.827CPU incluye generador/Celery/aplicación/observador. Cerca de capacidad asignada no significa throttling. Corregir cola no elimina esa restricción ni el servicio p95 observado0.879s, ya superior al objetivo end-to-end0.8s; el instrumento no proporciona un límite causal limpio de servicio.

## Camino real Gunicorn23

Fuente instalada inspeccionada: `/home/felidae/proyectos/web_modelos_mod08_vps/.venv/lib/python3.12/site-packages/gunicorn/workers/gthread.py` (en adelante `gthread.py`). `accept` incrementa `nr_conns` y registra socket aún no legible (`119-129`); readiness llama `enqueue_req` (`135-149`), que inicializa conexión y hace submit (`113-117`). Pool por proceso con `max_workers=threads` (`96-98`), sin admisión por slots. [CPython3.12.15 thread.py:140-165](https://github.com/python/cpython/blob/v3.12.15/Lib/concurrent/futures/thread.py#L140-L165) usa SimpleQueue y put sin cota propia. Son dos límites distintos: executor sin cota propia, conexiones limitadas por worker; no una cola global compartida.

La configuración oficial define1000 clientes por defecto, no dos trabajos, y no ofrece límite separado de futures pendientes. [Gunicorn23 settings:1607-1617](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/settings.rst#L1607-L1617).

**Contraejemplo fuente, no ensayo ejecutado:** con `worker_connections=threads=2`, aceptar dos TCP sin enviar bytes deja `nr_conns=2`, sockets en selector y cero futures. `gthread.py:207-221` deja de llamar select y espera futures vacíos; no se dispara readiness aunque luego lleguen bytes. Los clientes iniciales no están en `_keep`; `murder_keepalived` (`151-184`) no los rescata. El worker sigue notify (`203-205`), por lo que no se puede confiar en timeout del árbitro para liberar esa situación. Un límite mayor conserva la misma clase de riesgo al llenarse de sockets sin datos. Desactivar keepalive no corrige conexiones iniciales. Un submit bloqueante para acotar pool también puede bloquear el hilo del selector. Ninguna de esas variantes es recomendación segura.

## Alternativas contrastadas

| Opción | Juicio |
|---|---|
| Ocho sync estándar, threads1 | `workers/sync.py:27-31,59-73` maneja cada conexión antes de aceptar otra; elimina executor local y deja pendientes en listener compartido. No garantiza justicia global ni SLO. Históricos12.070s/12.751s FAIL preceden eliminación del join redundante; no comparación actual equivalente. Más procesos aumentan memoria/conexiones DB. Pico histórico app1,263,939,584bytes y PG428,158,976bytes incluyó preparación; evidencia pasada, no garantía actual. PG histórico≈0.941CPU, cero throttling. No repetir sólo por nueva explicación de cola. |
| gthread23 con cap pequeño | Riesgo de liveness anterior; no opción segura demostrada. Cambiar backlog/reuse-port no redistribuye futuros ya aceptados. |
| Corrección upstream | Master inspeccionado separa activación de listeners del polling (`set_accept_enabled`, bucle siempre poll) y añade cola de callbacks/gestión de conexiones pendientes. Sigue ThreadPoolExecutor sin cota propia. Es pista concreta de solución al bucle, no prueba de balance/SLO ni backport mínimo validado. |

Fuentes primarias: [sync23:27-73](https://github.com/benoitc/gunicorn/blob/23.0.0/gunicorn/workers/sync.py#L27-L73), [gthread23:193-231](https://github.com/benoitc/gunicorn/blob/23.0.0/gunicorn/workers/gthread.py#L193-L231), [master inspeccionado](https://github.com/benoitc/gunicorn/blob/master/gunicorn/workers/gthread.py#L267-L388). Master es mutable: no se identificó aquí commit/release/backport probado. Dependencias congeladas23 permanecen obligatorias. [Diseño oficial23](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/design.rst#L72-L84) exige proxy con buffering para sync ante clientes lentos; ocho sync tampoco es protección general frente a TCP o cabeceras lentas.

## Evidencia exigible antes de cualquier ensayo nuevo

1. Fijar fuente exacta y revisar contrato de admisión: listener desactivado al cap, selector sigue atendiendo conexiones existentes y completados; contadores/cierre/excepciones sin fugas; rechazo explícito de dependencia nueva implícita.
2. Controles funcionales pequeños: dos slots ocupados más petición lista; cap completo con TCP inicialmente sin bytes y luego solicitud válida; cabeceras parciales; desconexión antes/después de enqueue; keepalive al cap; expiración; SIGTERM/graceful/reinicio. Demostrar progreso finito sin busy-spin, cierre recuperable y cero trabajo perdido. No ejecutados aquí.
3. Si supera revisión/controles, prerregistrar un único diagnóstico que pruebe reducción del tramo enqueue→handler, ausencia de procesos inactivos mientras quedan colas locales y bound real de pendientes. Conservar errores/timeouts y accounting completo, sin confundir el diagnóstico instrumentado con p95 limpio.
4. Sólo después considerar comparación limpia sobre mismo código/dataset/cuotas: app4CPU/3584MiB/pids512, PG1CPU/1536MiB/pids128, Redis0.2CPU/128MiB/pids64. Mantener objetivos, población y carga contractual. Si no mejora, cerrar hipótesis sin serie de parámetros; PG/servicio requieren evidencia independiente.

## Verificación de integración por Codex

Codex contrastó el bucle instalado de Gunicorn23: registro inicial de sockets, submit por proceso y rama al alcanzar worker_connections sin polling. El contraejemplo descrito es una deducción de fuente, no una prueba ejecutada. La inspección confirma que reducir ese límite no tiene una garantía de progreso demostrada; se conserva el rechazo de gthread y no se inicia otra carga. Las referencias de master siguen siendo investigación del autor, sin fijación/revalidación independiente ni autorización de backport. Documento integrado como análisis acotado, sin aceptación CR09/N3.
