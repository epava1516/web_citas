# Consultas restantes: preparación de catálogos y medios

Run `20261015-143135-64079715`, base `d4580b9` más diagnóstico explícito:1PASS90.08s. PostgreSQL propio, datos sintéticos, límites intactos. Verificadas fuentes congeladas y limpieza independiente de raíz/pytest/backend/temporales/PG/Redis. No hay cambio de producto.

Consultas capturadas de dos páginas y dos fichas; replay en RR READONLY, filas raw iguales en cada operación. Tres variantes,8warmups y3bloques rotativos de12replays/familia/variante. No se exportan SQL/parámetros/resultados.

| CPU por replay de familia(ms) | Cliente | Servidor sin preparar | Preparado |
|---|---:|---:|---:|
| listing/catalog | 5.833 | 5.278 | 1.667 |
| listing/media | 1.389 | 1.389 | 1.111 |
| detail/catalog | 2.778 | 3.056 | 1.111 |
| detail/media | 7.222 | 9.167 | 1.111 |
| detail/rights | 1.111 | 1.944 | 0.000 |

36entradas preparadas,1747usos genéricos observados. CuantizaciónCPU100Hz: cero ticks no significa coste cero. Replay omite ORM/HTTP y no prueba validación completa, intercalaciones, invalidación o latencia de request. No sumar estos resultados a otros runs para prometer un p95. Último limpio7.423942sFAIL se mantiene.

Siguiente candidata justificada: ampliar sólo lecturas públicas explícitas de la página seleccionada y la ficha, restaurando atributos en finally. El valor predeterminado de publicly_visible debe conservarse para sus consumidores comerciales, favoritos, sitemap y otros flujos; no introducir preparación global ni cambiar transacciones. Antes de carga: controles PostgreSQL reales de planes, fábrica, HTML/destinos firmados, revocación entre requests, errores y fallback. No se acepta desde el replay ni se lanza carga automática.
