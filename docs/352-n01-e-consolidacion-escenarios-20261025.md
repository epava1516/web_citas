# N01E — conciliación primaria de fichas y siguiente base operativa

25deoctubrede2026. N00aceptado1/13; N01abierto. La [matriz primaria](evidencias/n01-e-consolidacion-fichas-20261025.json) conserva las19propuestas, revalida93citas y verifica cada selector/parametrización en AST. Integra el alcance parcial de N01D para seis escenarios, sin convertirlo en aceptación de rendimiento ni cobertura completa de sus familias. No hay cambios de aplicación.

La semántica de351/README/vista17 y el AST anterior están conciliados:1941fuentes,18105nodos,80141relaciones,859comunidades; [verificación](evidencias/n01-d-resultado-grafo-verificacion-20261025.json). Refresco focal sobre base preservada, no reconstrucción completa; consumo nativo desconocido. Las otras1506fuentes ejecutables originales siguen intactas, con runner de medición como variante explícita.

## Criterios que la matriz separa

| Grupo | Modalidad propia | Presupuesto/límite que se conserva | Hueco de medición |
| --- | --- | --- | --- |
| S01/N04 | Discovery y mezcla pública | p95<800ms y errores<1% sólo con protocolo original de mezcla | Los diagnósticos A/B/C no prueban esa carga |
| S02/N07 | HTTP, estado y trabajo asíncrono | Autoridad fresca, retirada inmediata, idempotencia | Tiempo del worker/Beat separado de servicio directo |
| S03/N09 | Transacción privada, outbox y purga | Cero exposición/duplicado; retención y lotes correctos | No sustituir etapas por duración de pytest o revisión humana |
| S04/N06 | Cuenta, revisión y representación | CSRF/MFA/sesión, titularidad y versión aprobada | Techo por operación comparable antes del candidato; agencias sin base actual |
| S05/N05 | Red y navegador | Primera imagen, hashes/dimensiones finales, retirada404 | Bytes iniciales/finales e interacción separados; sin LCP inventado |
| S06/N02 | Cobertura y entrega por paquete | p95≤2s cobertura, p95≤5s JSON/binario en protocolo MOD09 | No trasladar ese límite a generación ni ampliar excepción provisional |
| S07/N03 | Detector y recepción→cola→ready | Paridad exhaustiva sin cap oculto;128MiB/1GiB/1200s son seguridad | Densidad100/distintos1000 no prueban80000 ni cola real |
| S08/N08 | Favoritos, sitemap, pedido simulado | Privacidad/retirada, pertenencia e idempotencia | Cohortes de crecimiento y compra real no probadas por N01D |
| S09/N10 | Agregados y restauración local | Sólo lectura, no datos privados y no resurrección tras borrado | Vacío no representa crecimiento; restore es otro escenario |

No se inventa un SLO universal para endpoints sin objetivo acordado. Cada comparación debe fijar por anticipado el escenario y su presupuesto técnico sobre una base equivalente. Los valores pendientes continúan pendientes, con requisito explícito antes de modificar el candidato. Esta conciliación aún no aceptaN01.

## Siguiente medición: S09-A, agregados de backlog de publicación

Instrumento nuevo `tests/test_operational_snapshot_baseline.py::test_snapshot_publication_backlog_baseline`: tres casos,0/10/100filas PublicationDirty sintéticas, UUID determinista y generation1. Sólo esa tabla varía; las otras tablas de trabajo empiezan vacías en la base de prueba. Fecha lógica fijada y edad240s, seis llamadas por caso: primera separada y cinco posteriores con proceso/conexión reutilizados. No se llama «fría» a la primera petición.

Se mide exclusivamente `apps.core.operational_snapshot.collect_snapshot`: pared instrumentada, número de consultas y ejecución SQL; creación/lectura de fixtures y aserciones quedan fuera del intervalo. No se guarda SQL, parámetros o UUID en propiedades. Oráculos: cuenta/edad exactas, alcance durable_database_work_only, inventario físico explícitamente no medido, conexión fuera de transacción al volver y filas idénticas antes/después de cada llamada. No prueba crecimiento de avisos/exportaciones, broker/worker, almacenamiento físico ni restauración.

Ejecución prevista, después de integrar AST/semántica y congelar fuentes: runner oficial serial focused, PostgreSQL17/Redis7.4 propios y dependencias bloqueadas; timeout900s como techo de ejecución, sin cuotas dedicadas ni carga concurrente. Seleccionar además `tests/test_operational_snapshot.py::test_empty_snapshot_has_explicit_scope_and_read_only_aggregates` para conservar el oráculo original de configuración de sólo lectura. Cuatro casos esperados,18muestras de servicio; no ejecución acreditada todavía.

Es base diagnóstica, no candidato. Sin presupuesto de latencia de servicio inventado: el statement_timeout5s interno es protección por sentencia, no SLO del colector. Para una futura corrección, congelar previamente referencia/candidato con misma población/orden/recursos y objetivo de consultas o tiempo justificado; la falta de comparabilidad produce resultado inconcluso. No se acepta rendimientoN10 con tres cardinalidades de una sola tabla.

Auditar selección real,18muestras finitas, oráculos, identidad completa de fuentes/imágenes, limpieza y recibos Telegram. El informe conservará primera llamada y mediana/rango de cinco posteriores por cardinalidad; sin p95/p99. Al cerrar cada bloque se publicará la tabla antes/después obligatoria; este lote aún no cierra un bloque.
