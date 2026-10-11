# Experimento runtime SQL: diseño rechazado

PostgreSQL17 real:8PASS,0fallos/errores/skips,50.183s;1155 hashes de fuentes y retirada PG/Redis comprobados. El helper fue sustituido entre atestación y ejecución y devolvió confianza falsificada. Por ello se rechaza para producción aunque tenga menor coste en este experimento.

| Modo | Referencia mediana (ms) | Helper atestado mediana (ms) | Reducción de coste | Muestras por variante |
|---|---:|---:|---:|---:|
| plain | 13.482495 | 8.173336 | 39.38% | 20 |
| recorded | 17.066960 | 10.206525 | 40.20% | 20 |

Dos rondas de warmup descartadas; veinte parejas con orden alternado por modo. Incluye atestación, y en recorded grabación de filas. Medición aislada sin cuotas originales: no representa mejora del request ni aceptación dos casos/N3.

Comprobados traza estable, cortocircuito por grant, cambios true→true invalidan sello, grant concurrente observado por consulta interna, una llamada bajo grabación/replay y rollback. Limitaciones: concurrencia memberships/triggers y equivalencia total de errores/NULL no verificados; el fallo de seguridad ya impide integración.

Fuentes experimentales preservadas en worktree codex/mod08-runtime-sql-probe; apps de producción intactas.
