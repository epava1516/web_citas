# Aplicabilidad de los ocho fallos diagnósticos restantes

Auditoría estática sobre 7ea0e266e1ce09fb831e932c083ca8b82af1540b. [Recibo y huellas](cr09-diagnostic-applicability-20261016.json). No se ha ejecutado una nueva batería ni cambiado producto o criterios. Los ocho FAIL de 183556-91e03d27 permanecen FAIL.

| Prueba | Clasificación | Hallazgo y trabajo pendiente |
|---|---|---|
|test_owned_wsgi_close_release.py|Prototipo negativo conservado|El cleanup de modelos no elimina el ciclo ancestro RequestContext/ContextDict. El prototipo posterior sí libera modelos; ROI insuficiente, descartado sin integración.|
|test_owned_dirty_unknown_census.py|Experimento superado por implementación|Injerta mediante literal una optimización ya presente con cobertura y snapshot; no volver a inyectarla. Conservar contraejemplos y pruebas productivas de paridad/límites.|
|test_owned_context_duplicate_reads.py|Expectativa diagnóstica anterior al batching|Espera contextos 1+24; versión actual hidrata lote25 para este caso. Requiere adaptar medición a algoritmo actual y comprobar guardas; no asumir regresión funcional ni relajar controles de contenido.|
|test_owned_backend_cpu_families.py|Clasificación diagnóstica anterior al detalle RR|Prohíbe hidratación en detalle; detalle actual usa PublicationContext/DetailQuery y consulta correlacionada. Requiere actualizar clasificación y preservar identidad backend/atribución acotada.|
|test_owned_public_projection_cpu.py|DDL experimental incompatible con esquema actual|CREATE TEMP TABLE SELECT s.*, l.expires_at repite columna ya incorporada. No es migración ni tabla productiva fallida; no reactivar diseño experimental sin hipótesis nueva.|
|test_owned_pg_statement_diagnostic.py|Controlador de instrumentación ausente|Runner común no precarga pg_stat_statements; prueba exige controlador específico. Existen capturas separadas reales. No modificar PostgreSQL normal para hacerla pasar.|
|test_owned_retention_topology.py|Wiring explícito de broker ausente|Guardia own Redis rechaza override ausente; no fallback externo. Hay evidencia previa Beat/worker real, pero no sustituye validación actual ni política por finalidad.|
|test_owned_detail_pyspy.py|Fallo de lifecycle de herramienta|stderr exacto No child process (os error 10); hijo completó240 sinerror y DEBUGfalse. Captura sigue FAIL: no convertir en PASS por datos parciales. Duración controlada/attach ya empleados en otros diagnósticos, sin probar aquí su correctiva.|

La continuación focused activó diagnósticos por nombre de archivo, incluidos prototipos negativos conservados y herramientas que requieren su propio controlador. Por ello ocho fallos de esa selección no equivalen a ocho defectos de producto demostrados. Tampoco se pueden omitir para declarar aceptación: la selección integrada debe distinguir regresión obligatoria y experimentos históricos, mantener su trazabilidad y conciliar los criterios con evidencia vigente.

No volver a perseguir el cleanup WSGI descartado por ROI ni reinyectar el censo integrado. Próximo trabajo: mantener controles productivos correspondientes, actualizar los dos diagnósticos de geometría SQL/contextos si son necesarios para la investigación, comprobar runtime Docker tras RateForm y preparar selección común con omisiones explícitas. Siguen pendientes prueba contractual limpia válida, regresión integrada, CR09 y fases posteriores.
