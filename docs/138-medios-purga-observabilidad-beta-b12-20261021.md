# B12 — Supervisión de medios y trabajo de purga física

Estado:42funcionales paralelos+1diagnóstico serial verificados; cierre integral B12 pendiente.

Grafo previo86:70c249a4f6ce64d8dcc737725e5c8d5d39aa93efc1a729c6c17b3bb5da0fde97. Requisito B12 de [roadmap103](103-roadmap-beta-clasificados-20261020.md): supervisar por separado vencimiento lógico y purga física. [Evaluación137](137-evaluacion-runbook-beta-b12-20261021.md) ya detecta entrega/worker y publicación; este corte amplía medios. No cambios de modelos, autoridad, tareas de borrado ni proveedores.

## Señales separadas

Snapshotmedia agrega sólo SQL Count/Min: Blobqueued/failed, processing con started_at ausente o anterior a3minutos; dos colas físicas MediaErasure y MediaPreparationCleanup con due/scheduled/failed. Erasure tiene agotamiento desde5intentos; la limpieza de preparaciones no tiene ese límite y retained no equivale a failed. Retained y retained_due se observan sin forzar borrado ni leer motivos privados.

Due físico usa edad desde next_attempt_at, no antigüedad original del trabajo. Failed puede solaparse con due/scheduled/exhausted; no sumar esas categorías como archivos distintos. Los contadores representan trabajos, no inventario de archivos.

preparation_candidates cuenta blobs distintos con upload descartado o vencido y sin job de revisión, según selector de la tarea real. Edad desde descarte/vencimiento mediante Coalesce, no desde creación del blob. Dos uploads del mismo blob cuentan una vez. Esa selección no autoriza eliminación: las referencias compartidas, evidencia y uploads activos se revalidan en el servicio existente.

El snapshot no abre archivos, descifra rutas ni llama a storage.exists/delete. physical_object_absence continúa no medido; media_orphan_inventory también queda explícito. La supervisión durable de cola física se distingue tanto del vencimiento lógico como de una comprobación de almacenamiento. El antiguo marcador genérico media_retention se concreta en estas coberturas y el inventario no observado.

## Atención y respuesta

La evaluación conserva salud desconocida y cobertura no verificada. Medios en failed/startunknown producen error observado; processingstale atención según selector de recuperación de3minutos. Queued, candidatos sin revisar y cola física exigible usan2cadencias de su tarea (hoy120s); configuración desconocida no se sustituye por un número inventado. Retained informa de protección, no dispara un fallo físico. Una reevaluación retenida exigible que acumule2cadencias produce atención de revisión, nunca autorización de borrado.

inspect_media_processing: comprobar worker/recuperación y código del servicio bajo permisos vigentes, sin reactivar un blob erasing/erased/purging. inspect_retention_before_physical_cleanup: verificar referencias y vencimientos; conservar archivos protegidos. inspect_physical_media_job_without_forcing_delete: comprobar reintento programado o agotamiento, almacenamiento y comprobación de ausencia, conservar rutas cifradas mientras falle y usar las recuperaciones autorizadas. No borrar filas ni forzar un éxito para limpiar el monitor.

## Prerregistro

Funcional42casos con4workers:8assessment+8snapshot+9ventanas+5erasure+11preparationcleanup+1worker. Distribución por archivos completos y bases/medios/broker aislados; historial propio195459 sólo ordena duración, sin eliminar casos ni alterar orden interno. Un diagnóstico de coste se ejecuta después en serie y sin otra integración propia concurrente. Son42+1casos en dos cortes, no una ejecución única43.

El nuevo caso SQL prueba estados, límite temporal exacto y preparaciones con99intentos todavía seleccionables; storage.exists/delete se bloquean durante el recolector para probar ausencia de acceso físico. Caso adicional con dos uploads vencidos prueba Countdistinct por blob.

Los ensayos existentes de erasure y preparación se refuerzan: fallo controlado en la segunda eliminación sobre archivos reales, primer archivo ausente/segundo presente, señal media_physical_failure, backoff sin intento extra, recuperación con eliminación efectiva y ausencia de esa señal. La elegibilidad de reintento físico se adelanta explícitamente por fixture, no se afirma espera natural60s; el ensayo outbox conserva esa espera real. Verificar retained por upload activo y referencias compartidas sin clasificarlo como fallo de borrado.

Coste: primera llamada,5warmups y30medidas por estado. Vacío y después10kdirty+10knotices+20kBlobs+10kMediaPreparationCleanup sintéticos sin archivos:50kfilas, sólo diagnóstico de agregados, sin autorización o ejecución de borrado. MediaErasure y otras tablas permanecen vacías en el benchmark y se verifican funcionalmente con dominio real.45SELECT previstos frente31anteriores. Presupuesto local de p95<1s permanece; no relajar por aumentar consultas ni extrapolar CPU servidor.

Auditar colección/XML y huellas de ambos cortes, finales de procesos y contenedores, muestras crudas y recibos Telegram antes de declarar resultados. Mantener negativos. No B12completo, auditoría de inventario universal, B13 ni beta global por este protocolo; cierre integral requiere conciliación separada de requisitos y evidencias.

## Resultado terminal

012300-9149ce62:42PASS/0FAIL/0ERROR/0SKIP con4workers,132,868sJUnit. [Auditoría funcional](evidencias/b12-media-functional-terminal-audit-20261021.json):42casos únicos, seis archivos completos, dos módulos de producto modificados respecto004837 (snapshot y evaluación). Las tareas de dominio, modelos y autorización permanecen idénticos. Historial de tiempos sólo ordenó ejecución.

012908-de4d9b06:1PASS/0FAIL/0ERROR/0SKIP del diagnóstico serial,53,526sJUnit. [Muestras crudas](evidencias/b12-media-snapshot-cost-20261021.json) y [auditoría combinada](evidencias/b12-media-combined-terminal-audit-20261021.json): fuentes de ambos cortes idénticas,43casos únicos entre dos ejecuciones, sin convertirlos en una ejecución única43PASS.

| Estado medido | Mediana ms | p95 ms | Máximo ms | SELECT |
| --- | --- | --- | --- | --- |
| Vacío |66,331|110,948|111,454|45|
| 10kdirty+10kavisos+20kBlob+10kcleanup |156,051|251,026|252,184|45|

Treinta llamadas por estado tras cinco calentamientos; p95<1s cumplido sin ampliar presupuesto. No incremento RSS antes/después observado en estas muestras; no memoria exclusiva ni pico global de servidor. Otras tablas, incluida MediaErasure, vacías en el benchmark: no generalizar a todas las cardinalidades o tiempos fríos.

Verificados con PostgreSQL y filesystem local reales: fallo controlado en segunda eliminación, original ausente/derivado todavía presente, detección durable de media_physical_failure, recuperación con ausencia comprobada y contador failed0. Preparaciones protegidas permanecen retained y no se clasifican como fracaso de borrado; dos uploads vencidos del mismo blob producen un candidato. El nuevo caso SQL bloqueó acceso a storage y confirmó que99intentos de preparación no se confunden con agotamiento de supresión.

Ambos runners terminales, contenedores/temporales ausentes, TelegramPASS confirmado. Limpieza de ejecución paralela: PID/startticks del runner y su hijo comprobados, grupo pytest ausente y sin procesos del probe con el temporal propio en su línea de comando. No se capturaron identidades en vivo del prefork en este corte; no afirmar esa comprobación más fuerte.

Cobertura aceptada aquí: señales de procesamiento, cola física y protección, con respuesta local y ensayos de archivos concretos. physical_object_absence y media_orphan_inventory siguen desconocidos a escala global; account_confirmation_retention también permanece fuera del recolector. B12 sigue abierto para una matriz de cierre que concilie estas limitaciones con los requisitos y evidencias; B07 y beta global no se aceptan por este corte.
