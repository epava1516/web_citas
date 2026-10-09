# MOD05: reconciliación del escenario experimental con el refresco

**Propuesta 4/6 ajustada y preparada; no ejecutada. Sin cargas nuevas y sin adoptar seis workers.** Instrucción directa del usuario, 2026-10-08. Trabajo de Claude Code (Claude Opus 5.5).

## Qué hacían los arneses anteriores

Todos los arneses de carga usados con MOD05 escriben settings propios con `CELERY_TASK_ALWAYS_EAGER = True` y `CELERY_BEAT_SCHEDULE = {}`, sin arrancar ningún worker: `test_contract_http_load.py`, `test_resource_service_checkpoint.py` y `test_worker_capacity_comparison.py`. La [comprobación funcional](mod05-refresco-escenarios-funcional0110.json), con un único upload sintético y sin carga, muestra que en esa configuración:

1. Las señales `on_commit` de MOD05 ejecutan `refresh_publication_state` **dentro del proceso web** que atiende la escritura: tres pasadas, con 1 procesado cada una y después 0.
2. `process_blob` también corre dentro de la petición.
3. Su última escritura, `Photo.objects…update(comparison_complete=True)` (`apps/mediafiles/services.py:266`), no emite señal. El trigger vuelve a marcar el anuncio y la respuesta termina con **1 sucio residual que nada refresca**.

Esto es compatible con la línea temporal archivada del [diagnóstico de recursos](mod05-recursos-informe0110.md): `native_unknown=1` desde 0,8 s tras empezar el upload y en todas las lecturas desde el final del upload (5,67 s) hasta el cierre del bloque (346/400). No es una medida directa de aquella ejecución.

## Dos escenarios

| Escenario | Definición | Resultados |
|---|---|---|
| `without_worker_beat_eager_signal` | Celery eager, Beat vacío, sin worker. Refresco y procesado de imagen por señal dentro del web; marcas sin señal persisten | Con MOD05: R5 intento 2 y R6 PASS de portátil (upload eager registrado), gate VPS 60 s VALID/FAIL, diagnóstico 30 s VALID/FAIL, controles de matriz/contrastes. **Conservados sin reinterpretar**; solo se etiqueta su escenario |
| `normal_worker_beat` | Topología desplegada: worker (`--concurrency=2`) y Beat de compose, calendario completo, tareas no eager | Ninguno todavía. Es el escenario de la nueva propuesta |

Los resultados anteriores a MOD05 no tenían estado almacenado y no reciben ninguna etiqueta: comparación 4/6 histórica, contractual INVALID, FAIL cortos y post-limpieza. La clasificación queda en los [criterios de revisión](../criterios-revision-benchmark-carga.md#escenarios-de-refresco-mod05-2026-10-08).

## Propuesta ajustada

[Propuesta](mod05-capacidad-4-vs-6-refresco-propuesta0110.json) y [runner](mod05-capacidad-4-vs-6-refresco-runner0110.py). La [anterior](mod05-capacidad-4-vs-6-propuesta0110.json) se conserva marcada como sustituida. Su runner sigue sin poder ejecutarse.

- **Refresco presente, aislado e idéntico en ambos brazos:**
  - Por bloque: clon PostgreSQL propio; worker y Beat propios con los comandos de `compose.yaml`; broker en Redis db 15 del contenedor del proyecto, verificada vacía antes y vaciada después (el runtime normal usa db 0 y no se toca); prefijo de cola único.
  - PIDs propios registrados y verificados ausentes.
  - Arranque de la carga fijado 5 s después de un tick observado de Beat del refresco de 30 s.
  - Solo varía `--workers` de Gunicorn.
- **Registro del refresco** con el mismo instrumento en todos los bloques:
  - [observador de tareas](../../scripts/benchmark_celery_observer.py): publicaciones por rol web/beat, ejecuciones con wall, CPU de hilo y resultado, marcas limpiadas y cota superior de la demora marca→limpieza;
  - [muestreador a 1 Hz](../../scripts/benchmark_publication_sampler.py): sucios pendientes, antigüedad de la marca más antigua y secuencia de marcas;
  - fracción de lecturas `native_unknown` desde los eventos WSGI;
  - CPU de los procesos worker/Beat desde ResourceProbe.
- **Contabilidad:** D y W siguen siendo de Gunicorn. El trabajo del worker Celery se informa aparte. U no es comparable con el escenario eager (`process_blob` pasa al worker). No se comparan causalmente escenarios distintos.
- **Validez añadida:** el bloque es INVALID si worker o Beat no están listos, si no se observa un tick antes de la carga, si el broker propio no está vacío o si un proceso propio termina durante el bloque.
- **Fuentes:** `tests/test_worker_capacity_comparison.py` con `refresh_mode`. Sin `refresh_mode`, el valor por defecto conserva la configuración Celery del escenario anterior y añade los mismos observador y muestreador (registra las ejecuciones eager en el web). Se añaden `scripts/benchmark_celery_observer.py`, `scripts/benchmark_publication_sampler.py` y la comprobación opt-in `tests/test_owned_refresh_topology.py`.

## Verificación sin carga

- Ruff y `py_compile` del arnés, el runner, el observador y el muestreador.
- Los dos tests opt-in se saltan sin variables de entorno.
- [Cableado normal](mod05-refresco-escenarios-funcional0110.json):
  - Beat publica el refresco a los ~30 s del arranque y el worker limpia 1 marca: demora 31,7 s, 325 ms de pared, 129 ms de CPU de hilo.
  - El origen beat/worker se correlaciona por id.
  - PIDs ausentes, Redis propio vacío y base retirada.
- El observador también registra las ejecuciones eager en el web.
- El experimento completo no se ha ejecutado.

Limpieza propia verificada en cada comprobación: bases `promotion_gate_cr09diag_*` ausentes, `pytest-temp` eliminado, PIDs de worker/Beat ausentes y Redis db 15 vacía.

## Corrección de la marca sin señal

Dentro del cambio mínimo local autorizado en CR09: tras el `update` final de `Photo.comparison_complete`, `process()` llama a `schedule_refresh(Photo)` si actualizó filas ([diff](mod05-marca-sin-senal-correccion0110.diff)). Es el mismo encolado de latencia que hacen las señales; la exactitud no dependía de él.

- **Antes:** 1 sucio residual tras el upload.
- **Después:** 0 sucios. Se ejecuta una pasada más de refresco: dentro del web en eager, encolada al worker en la topología normal.
- **Pruebas:** la regresión `tests/test_publication_state_upload.py` PASS. `test_state_route_matches_native_before_and_after_refresh` presuponía sucios tras montar el fixture; ahora los marca explícitamente con `mark_all()`, conservando su intención.
- **Regresión:** pertenencia, condicional, inventario, upgrade, matriz (repeated-100), descubrimiento, presentación, dependencias de validación pública, prueba SQL de búsqueda y borradores. 93 PASS en total, más los 2 fallos de precondición previos al ajuste. [Detalle](mod05-refresco-escenarios-funcional0110.json).

Los resultados anteriores del escenario eager se obtuvieron con la fuente previa y conservan su comportamiento y su etiqueta. En la topología normal, el refresco tras el procesado ya no espera al tick de Beat (hasta 30 s).

## Decisiones pendientes del usuario

1. Autorización expresa para los cuatro bloques de 30 s en `normal_worker_beat`, con el alcance que fija la propuesta (worker/Beat propios, Redis db 15). Sin 60/900 s ni adopción.
2. Si el gate de 60 s y el contractual de 900 s deben evaluar la topología normal. Hoy usan el escenario sin worker/Beat, y esta propuesta no cambia esa definición.

CR09 y GS01 abiertos; contrato, umbrales, porcentajes y veredictos históricos intactos.
