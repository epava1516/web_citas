# Diagnóstico con cardinalidades activo

Run112242-c81528ae, fuente2e2c239:FAILinstrumentado/188,94s;1200dinámicas emparejadas porID, cuatro workers declaran SQLshapes activo, cero errores deparseo, **0llamadasoverflow/0bucketsdeformasmixtas**,744grupos comparables. Fuentes y limpieza verificadas independientemente. [Recibo](cr09-cold-shapes-20261016.json).

| Medición | p95(s) | Alcance |
|---|---:|---|
| Primer corto limpio | 0,675688 | PASSaislado |
| Repetición limpia | 0,880357 | FAIL;no reproducible |
| Diagnóstico ampliado actual | 1,118985 | Instrumentado;no comparable como aceptación |

| SQLhidratación mismoPID/ruta/huella/cardinalidad | Primera(ms) | Media posterior(ms) | Ya vista estructura/tamaño enworker |
|---|---:|---:|---|
| /es/ /PID3693833 /43parámetros | 88.406 | 7.779 | False |
| /en/ /PID3693832 /43parámetros | 72.401 | 9.230 | True |

La primera fila nunca había visto esa estructura/tamaño en ese worker; la segunda sí. No todo el coste inicial se explica por primer uso. Tres workers recibieron preámbulos de rutas públicas; otro sólo empieza a observarse en carga. Las huellas ahora permiten identificar rutas de preámbulo sin exponerquerystrings.

Igualdad de cardinalidad no demuestra valores, estado dirty, plan o carga concurrente iguales. Los744grupos no son744experimentos aleatorizados; el recibo versiona sólo los20con mayor diferencia observada y conserva población total en artefactos ignorados. SQLwall sigue mezclando servidor/protocolo/cliente; no equivaleCPUPostgreSQL. No inferir una regresión del producto desde el p95instrumentado más alto.

Se recibió [revisión algebraica acotada](cr09-native-membership-subset-review-20261016.json):si NsonIDs ya validados yEes la membresía elegible, (E−D)∪N = E−(D−N) sólo bajo N⊆E en mismoRR. Codex contrastó la identidad y el contraejemplo N={a},E=∅; no hay código ni plan del candidato. El SELECTextra y el beneficio posiblemente pequeño impiden recomendar ROI/carga. No se adopta por ser una propuesta distinta.

Siguiente evidencia necesaria: separar tiempo original del backend PostgreSQL de lo observado por el cursor, antes de elegir otro tratamiento. Las extensiones/contadores de diagnóstico deben aislarse del gate limpio y de recursos normales. No se ha iniciado otro ensayo ni se autoriza900por este diagnóstico. Producto, recursos y criterios intactos; CR09/N3 abiertos.
