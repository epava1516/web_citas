# Purga de entrega de confirmación — worker y Beat

Estado: ensayo operativo verificado localmente; CR-09 permanece abierto. Complementa docs/49. Comando: `uv run python -m scripts.probe_account_delivery_worker launch`.

El script exige entorno no productivo y crea PostgreSQL `account_delivery_probe_<id>` y cola exclusiva. Inicia contenedores temporales worker/Beat; verifica que identidad, avisos y confirmación de correo están desactivados y que Celery no ejecuta tareas eager. Los fixtures contienen comprobación pendiente y ninguna aprobación de identidad. No crean anuncios, no ejecutan cambios de cuenta ni envían enlaces externos.

Se preparan entregas cifradas caducadas y vigentes. La tarea real debe vaciar solo el contenido caducado; estado posterior compara huellas internas de cuentas, perfiles, caso, propuesta, acciones, pruebas y metadatos de confirmación, junto con bytes cifrados de entregas vigentes. No imprime contenido de entrega, destino, contraseña o secreto.

Primera fase: envío por Redis a worker, resultado1, repetición resultado0 y evidencia/auditoría intactas. Segunda fase: nuevos fixtures, Beat conserva tarea e intervalo60s de la aplicación y envía automáticamente a cola aislada, sin dispatch manual. Correlacionar IDs recibidos/completados en logs de worker con programación de Beat. Cleanup elimina solo contenedores, cola y base de ensayo creados por este script; conserva aplicación normal.

Una purga técnica de contenido transitorio no acredita identidad real, entrega externa ni conservación jurídica integral, y no elimina backups/WAL. El ensayo tampoco sustituye carreras PostgreSQL y pruebas HTTP/móviles de docs/49.

## Resultado observado

Worker procesó una entrega caducada y la repetición devolvió cero, en 13,047 s. Beat ejecutó automáticamente la siguiente purga: dos entregas caducadas vacías en total y dos vigentes conservadas, en 64,555 s. Las huellas de cuentas, ámbito, propuestas, pruebas, acciones y metadatos permanecieron iguales. [Evidencia normalizada](evidencias/purga-entrega-confirmacion-worker.json).

El proceso terminó y no quedan contenedores ni bases `account_delivery_probe_`. Consulta de pg_database con usuario configurado del servicio: cero filas; primera consulta con usuario supuesto `modelos` falló por rol inexistente y no constituye evidencia. Ruff y formato pasan. No se modificó fuente funcional de la aplicación.
