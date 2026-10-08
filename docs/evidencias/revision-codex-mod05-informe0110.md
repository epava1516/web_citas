# Revisión independiente de CR09 / MOD-05

Fecha: 2026-10-08. Fuente revisada: `3f535c7`. Revisión de los cambios recibidos del portátil, sin modificar backend ni ejecutar otra carga de 30/60/900 segundos.

## Resultado

**Las cifras comunicadas cumplen 20 RPS en el portátil; CR09 no puede darse por cerrado debido a una divergencia funcional reproducida.** Los PASS históricos comunicados se conservan como resultados de aquellas ejecuciones, sin convertirlos en aceptación independiente de la semántica.

| Evidencia comunicada | Dinámicas | Duración | p95 HTTP | Errores |
| --- | ---: | ---: | ---: | ---: |
| R5 intento 2 | 1.200 | 60 s | 248,834 ms | 0 |
| R6 contractual | 18.000 | 900 s | 265,460 ms | 0 |

Los resúmenes registran 10.000 anuncios, mezcla contractual, 20 RPS, uploads separados y umbrales del generador conformes. La aritmética de los campos disponibles es consistente; el código actual no difiere del código funcional de los commits declarados para esos ensayos. El portátil (12 CPU visibles, 15 GiB, PostgreSQL 17.11) es otro entorno: no acredita esa capacidad en el VPS ni una mejora causal homogénea frente a sus versiones anteriores.

No llegaron las muestras completas, manifiestos y huellas originales, eventos por request, revisión de limpieza o drain observado necesarios para recalcular independientemente todos los criterios. Drain observado, competencia de recursos y medidas ausentes: **not_measured** en esta revisión. No se reclasifica el PASS comunicado como INVALID por esa ausencia; su aceptación independiente permanece pendiente de los artefactos originales.

## Verificación propia

[Revisión funcional](revision-codex-mod05-funcional0110.json): **54 PASS**, PostgreSQL real, incluyendo 3 casos Chromium. Estado almacenado, invalidación, carrera de refresco, reglas, rutas, filtros, orden, recuento, paginación, promociones y render comprobados dentro de las poblaciones de esas pruebas. No equivalen a cobertura exhaustiva de todas las ramas.

[Reproducción condicional](revision-codex-mod05-dependencia0110.json): **1 FAIL**, con dos observaciones. Fixture sintético de 25 anuncios; candidato afectado fuera de las 24 tarjetas de la primera página. Reintroducción de foto autorizada mediante inspect/decide nativos y refresco inicial correcto. Después se modificó mediante QuerySet.update primero la decisión a maintain y después, restaurando authorize, la prueba de derechos a failed. Son escrituras que el mecanismo de triggers pretende cubrir incluso sin señales Python.

| Dependencia modificada | Recuento estado | Recuento nativo | Dirty del candidato | Ruta observada |
| --- | ---: | ---: | --- | --- |
| Decisión de reintroducción | 25 | 24 | false | state / trusted_state |
| Estado de prueba de derechos | 25 | 24 | false | state / trusted_state |

La validación nativa rechaza el candidato en ambos casos. Las tablas `safety_rightsphotoreintroductiondecision` y `safety_rightsproof` no están cubiertas por DEPENDENCY_TABLES ni los triggers de la migración 0015, aunque publication_pending/source las leen. La comprobación nativa de las tarjetas seleccionadas no corrige el recuento de un candidato fuera de página. **Se demuestra incumplimiento del recuento exacto; no se afirma exposición indebida ni una respuesta concreta de la segunda página tras la mutación, que no se midió.** Las pruebas actuales de completitud no recorren esta rama condicional.

## Decisión y límite

No aceptar el cierre de CR09. La siguiente corrección concreta es completar la invalidación de esas dependencias y la regresión condicional fuera de primera página, incluyendo operaciones y asociaciones pertinentes; verificar equivalencia antes de aceptar el estado almacenado. La seguridad completa de la huella de código/configuración sigue requiriendo cobertura de dependencias condicionales; este ensayo no la demuestra.

Para auditar el rendimiento comunicado, recuperar los artefactos originales R5/R6 del portátil; otra carga larga no sustituye esa revisión. No se necesita reinterpretar FAIL/INVALID previos, cambiar SLO o aumentar recursos. No se adoptan seis workers ni se modifica el runtime normal. CR09 sigue abierto, porcentajes y demás requisitos intactos.

Ambas ejecuciones propias terminaron. Fuentes intactas hasta revisión terminal; ausencia de las dos bases y medios propios de cada ejecución comprobada independientemente. [Archivo reproducible y SHA](revision-codex-mod05-artefactos0110.json) conserva logs, XML, huellas y scripts, incluida la prueba negativa fuera del árbol de tests. Graphify se contrastó con las fuentes: conserva la arquitectura proyectada anterior y no se usa como prueba de MOD-05 vigente. No se ha regenerado el grafo en esta revisión.

## Actualización tras recibir los originales (`8342dbd`)

La falta de muestras indicada arriba queda resuelta por los archivos recibidos el 2026-10-08. [Auditoría independiente](revision-codex-mod05-auditoria-originales0110.json) y [script](revision-codex-mod05-auditoria-originales-script0110.py): SHA de ambos archivos e individual de sus nueve miembros correctos; IDs únicos, calendario a20RPS, mezcla/rutas y correlación íntegra con accesos comprobados. Resumen/JUnit coinciden. Sin nueva carga.

R5:1.200 éxitos, p95=248,834ms,3 pendientes al cierre/0 finales,drain75,787ms,1upload. R6:18.000 éxitos (6.000 por familia),p95=265,460ms,3 pendientes al cierre/0 finales,drain37,714ms,15uploads a60s. Cero errores/timeouts/noemitidas. Generador p95/p99/max cumple10/25/100ms. Manifiestos conservan timeout65s/drain70s y10.000 publicados. **Los PASS de los filtros de carga registrados quedan corroborados desde las muestras originales.** El p99 R6=1,402s no viola el SLO p95 vigente.

Siguen ausentes las huellas originales/árbol limpio al arranque, eventos WSGI entrada-salida/PID, consumo de recursos y limpieza contemporánea. No impiden recalcular los resultados anteriores, pero limitan la atribución a una fuente exacta y el diagnóstico: D/CPU/demora preWSGI permanecen not_measured en esta auditoría. No acredita VPS ni cierra CR09: el FAIL funcional de invalidación permanece abierto. Pendiente único de producto: corregir dependencias condicionales demostradas y comprobar equivalencia. Los originales ya no son una dependencia pendiente para verificar los números de carga.
