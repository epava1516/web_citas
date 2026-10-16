# Contraste aislado de pertenencia mediante UNION

Run `20261016-004909-87f1581a`, base `ced95b1`, test explícito `tests/test_owned_population_union.py`: **1 PASS en 106,68 s**, 108 lecturas completas con igualdad de resultados, conteo y página en el fixture. La transformación sólo existe dentro del test; no se modifica la aplicación. Datos sintéticos, PostgreSQL propio y límites del adaptador conservados.

| Caso con una entrada dirty | Actual, media ms | UNION, media ms |
| --- | ---: | ---: |
| Listado | 226,667 | 275,497 |
| Búsqueda | 344,859 | 371,979 |
| Sin coincidencias | 86,566 | 82,592 |

**Descartado:** listado y búsqueda empeoran; no hay beneficio consistente. Las ramas limpias ejecutan el mismo código y sus diferencias muestran variación ambiental, no una optimización. No se infiere significación estadística ni p95 HTTP desde estas medias. No integración, barrido de parámetros ni nueva carga HTTP.

[Recibo independiente](cr09-population-union-terminal-20261016.json): hashes originales iguales antes de escribir esta documentación; controlador/hijo ausentes, temporal eliminado y ambos contenedores propios ausentes. Unidad terminal sin MainPID. Resultado bruto y 108 registros conservados en `artifacts/local-ci/20261016-004909-87f1581a/pytest.xml`.

La revisión lógica previa de un agente nativo sólo justificó el contraste bajo RR propio; no acreditaba rendimiento ni paridad general. CR09, reproducibilidad, carga larga y N3 común siguen pendientes. Siguiente trabajo: consolidar la aplicabilidad de pruebas de conservación por finalidad y sus excepciones, sin reutilizar este candidato rechazado.
