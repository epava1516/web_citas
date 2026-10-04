# Procesamiento de avisos privados — CR-09

Estado: implementación local parcial; no entrega a canales reales ni cierre de CR-09.

## Contrato de tarea

`apps.safety.tasks.deliver_safety_notices` procesa como máximo100 avisos por ejecución. Beat la programa cada60 segundos. Alterna `ReportNotice` y `ComplaintNotice`; selecciona avisos queued/retry cuyo objetivo de reintento ha vencido, con menos de cinco intentos. PostgreSQL `FOR UPDATE SKIP LOCKED` permite workers concurrentes sin esperar por una fila ocupada.

Cada aviso se procesa en una transacción independiente. Un savepoint revierte cambios parciales del adaptador si falla. El resultado contiene exclusivamente contadores processed/simulated/retry/failed y disabled. Nunca devuelve destinatario, contenido ni texto de excepción.

## Estados y reintentos

- queued: pendiente, sin confirmación de entrega.
- retry: reintento previsto tras60/120/240/480 segundos según número de intento.
- failed: quinto intento fallido, sin nuevos reintentos automáticos.
- simulated: ejecución del simulador local, sin correo ni comunicación real.

Se conservan attempts, next_attempt_at y error_code genérico adapter_failure. Los registros de simulación son únicos por aviso. Una ejecución repetida no vuelve a procesar simulated/failed. La migración safety0028 incorpora estos campos sin reinterpretar la historia previa: las simulaciones del helper antiguo pueden tener attempts=0.

## Adaptador y privacidad

Por defecto `SAFETY_NOTICE_BACKEND=disabled`. En producción esta tarea está desactivada incluso si se configura simulator. El simulador comprueba el sobre cifrado y registra una entrega simulada; no usa red, SMTP ni salida de mensajes a consola. El acuse de reclamación distingue pendiente/reintento/fallo/simulación y conserva la respuesta privada disponible. No muestra destinatario ni errores internos. La simulación no acredita canal, identidad, conocimiento del mensaje ni cumplimiento del deber de comunicación.

Una integración futura con proveedor deberá definir confirmación de canal, idempotencia externa, lease y reconciliación tras interrupciones. La atomicidad del simulador sobre PostgreSQL no demuestra atomicidad frente a un envío externo.

## Reproducción de comprobaciones

```bash
uv run pytest tests/test_notice_delivery.py tests/test_report_notices.py tests/test_complaint_resolutions.py -q
docker compose build app worker beat
uv run python -m scripts.probe_safety_notice_worker launch
```

El script usa PostgreSQL y Redis reales con base y cola únicas temporales, worker Celery y Beat en contenedores separados. Configura backend de resultados únicamente en estos procesos de prueba; la aplicación mantiene CELERY_TASK_IGNORE_RESULT=True. Comprueba una tarea, repetición idempotente y la ejecución programada de Beat sin despacho manual para esa segunda tanda. Todos los avisos son sintéticos y el envío sigue simulado. El bloque finally elimina base y contenedores temporales; no modifica expedientes de la aplicación. El resultado terminal, no solo el arranque de contenedores, determina aceptación.

## Pendientes

Recuperación autorizada de failed con historia, alertas operativas, política de avisos caducados, comunicación de derechos y afectados, revisión del contenido y canal confirmado, adaptador externo y pruebas reales cuando exista proveedor autorizado. No se incluye aquí copia integral, supresión ni retención definitiva. Evidencias de ejecución en docs/18; seguimiento en docs/17.

## Evidencia aceptada localmente

20 pruebas afectadas pasan104.77s, PostgreSQL/Chromium sin skips. Probe real terminal: worker10.264s y Beat66.579s; cuatro simulaciones únicas, segunda tanda disparada automáticamente, limpieza confirmada. Docker principal actualizado hasta safety0028, salud200 y backend disabled. Historial de correcciones del probe y UUID de tareas en docs/18. No correo real ni cierre de CR-09.
