# B07 — Liberación de tareas terminadas del generador

Estado: corrección del cliente verificada por11casos locales; no capacidad, calibración PostgreSQL ni repetición900s. B07 abierto,8/18cerrados.

## Evidencia y alcance

El grafo enlaza run_async_open_loop en scripts/benchmark_async_transport.py con el transporte y sus pruebas. La lectura del código confirma lista acumulativa de Task hasta el gather final. La regresión con referencias débiles reproduce antes del cambio cero tareas liberadas de las diez primeras cuando se emite d-15; falla como esperado. Tras corregir, las diez ya se han liberado y se conservan todos los resultados y uploads.

El [terminal189](189-protocolo-beta-http-900s-b07-20261021.md) sigue INVALID. En su evidencia existente, los dos retrasos superiores100ms a776,65/776,70s solapan un GCgeneración2 entre776,601291y776,792400s:191,111mswall y167,768msCPU, cero objetos recogidos. La coincidencia no demuestra causalidad ni cuantifica mejora. Los ledgers y el heap de Django también siguen vivos; liberar Task no garantiza evitar otra pausa. No desactivar GC, congelarlo ni alterar umbrales.

## Corrección y validación

El conjunto tasks retiene sólo tareas en curso; callback elimina terminadas y consume excepciones como el gather anterior. No limitar concurrencia ni borrar resultados del ledger. Mantener timeout por petición, ventana fija, drain y clasificación terminal. Manejar también conjunto vacío al terminar.

[Auditoría](evidencias/b07-client-task-release-20261021-audit.json):11PASS/0FAIL/0ERROR/0SKIP en transporte y contabilidad; incluye96peticiones simultáneas sin cap, timeout/drain separados, HTTPchunked/POST302/sinredirect, fases y timeout parcial, payload, liberación con upload, errores dinámicos/upload y cancelación por recurso con contabilidad. El primer corte7PASS fue preliminar; no representa los archivos finales. Reproducción negativa preservada. Avisos Telegram de cada ejecución confirmados. Son pruebas de cliente, no sustituyen el runtime nativo.

La siguiente validación requiere protocolo nuevo y calibración nativa afectada antes de plantear un nuevo corto o900s. No repetir la secuencia inválida automáticamente ni cambiar sus criterios; conservar comparabilidad y fuentes. Ningún código de producto cambia por esta corrección.
