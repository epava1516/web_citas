# Preparación inmediata con planes automáticos

Run `20261015-193403-c3bad199`, base `f8c1286` más parametrización del instrumento: **1PASS122.33s**, sin omisiones. Fuentes idénticas y limpieza verificadas independientemente; unidad terminal/MainPID0, raíz/pytest/temporal/PG/Redis propios ausentes. [180observaciones y recibo](cr09-preparacion-inmediata-auto-cpu-terminal-20261015.json).

Mismo experimento frío finito anterior, pero candidato threshold0 y plan_cache_mode=auto: no se fuerza plan genérico. Tres bloques alternos,30peticiones×6conexiones, igualdad de respuestas/canonicalización firmada. Base tambiénauto conthreshold5 durante el helper; no calentamiento ni peticiones descartadas. Python/bufferscompartidos no fríos; no reproduce Gunicorn/carga concurrente.

| Media por petición | Umbral5/auto | Umbral0/auto |
|---|---:|---:|
| CPU PG primeras6porconexión |56.667ms|52.778ms|
| CPU PG peticiones7–18 |47.500ms|38.611ms|
| CPU PG peticiones19–30 |36.944ms|30.000ms|
| CPU PG todas30 |45.111ms|38.000ms|
| CPU app todas30 |133.711ms|115.823ms|
| Tiempo secuencial todas30 |216.208ms|181.555ms|

CPU PG por bloque actual41.333/46.000/48.000ms frente35.333/35.667/43.000ms candidato. Diferencias pareadas6.000/10.333/5.000ms; rangosglobalesse solapan y cuantización100Hz: no prometer porcentaje causal/p95. Primerbloque actual incluye calentamientoPython, no aislarCPUappcausal.

Planes finales actuales42,240genéricos/200custom frente82,490genéricos/200custom del candidato, iguales cada bloque. Primera petición candidato21planes,4genéricos/17custom; actual0. Elimina periodo previo del driver, **no elimina** primeras ejecuciones custom dePGauto. Cache driver acotada100, candidato mayorocupación82 requiere considerar shapesvariables/evicción. ClientCursor no prepara fuera del helper.

Fuentes primarias contrastadas: [Psycopg preparación](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html), página consultada corresponde3.3.7.dev1; se contrastó implementación local3.3.6 (`PrepareManager`,ClientCursor._get_prepared). [PostgreSQL17 PREPARE](https://www.postgresql.org/docs/17/sql-prepare.html): auto comienza con cinco custom y compara costeestimado genérico. No confundir los dosumbrales ni cache de planes con resultados.

Decisión: material suficiente para candidato acotado threshold0 sólo en `_prepared_page_binding` cuando previaNone. No tocar plan_cache_mode, factory/restauración/valorpreexistente ni otras lecturas/escrituras. Validación del candidato separada: restauración real tras SQLerror anidado, paridad fresca/guardia, parámetrosanchos y proyección/ciclo; después único corto limpio si controles pasan. No nueva aceptación, p95vigente1.361793FAIL.

Candidato validado: [17PASS134.29s](cr09-preparacion-inmediata-controles-terminal-20261015.json), archivos completos de binding, guardia detalle, proyección y ciclo. Fuentes/limpieza independientes. Incluye errorPGreal/nesting/rollback/conexiónusable, preservaciónumbralexplícito, HTMLfresco, revocación, lectura65536parámetros, upgrade/expiración/carreras. No ampliada92enestaversiónniN3. Después de verificar fuentes se fijó explícitamentethreshold5 del brazo histórico del instrumento para mantener significado tras cambio de default; ClientCursor externo no prepara. Sólo modificación de instrumento, no altera evidencia ya congelada ni producto validado.
