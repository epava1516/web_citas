# MOD-08 — Fases completas y adaptación de filas — 2026-10-11

Diagnóstico autorizado por «Procede con todo lo que haya que hacer». Producto intacto respecto a las dos mejoras ya conservadas. [Datos](mod08-full-wait-20261011.json).

Runner `20261011-164325-0f8daba0`: 3 PASS/0 errores/fallos/skips, 103,65 s. Auditoría independiente de 1323 fuentes sin diferencias antes de documentar. Primer intento `20261011-164311-29fd15f5` terminó ERROR en Ruff antes de pytest por imports; no pruebas acreditadas en ese intento.

Instrumento sólo tests: las 19 fases del inventario fijo, driver Cursor/ServerCursor y pipeline del diagnóstico anterior, más un proxy reversible de Transformer en ServerCursor._fetch_gen para medir load_rows y set_pgresult. Mismos generadores, argumentos, retorno y throw/close; sin profiler ni datos en el informe. Dos pruebas de forwarding/restauración y una integración real PostgreSQL/TCP. Cuatro controles alternados con cuatro observadas, un Gunicorn sync caliente, clones privados con 1500 revisiones/16 MiB, historial 548 EVENT/256 lecturas obtenido por 64 POST reales. Se comprueban +8 eventos/+4 lecturas después de cada commit por conexión owner independiente. Kernel nativo sellado en cada muestra.

| Medida en las cuatro peticiones instrumentadas | Intervalo wall |
| --- | ---: |
| Fuente completa | 151,226–195,469 ms |
| Fetch principal, tres llamadas [1000,500,0] | 74,660–91,396 ms |
| Adaptación load_rows, parte del fetch | 9,874–14,753 ms |
| authorize, 23 llamadas | 100,127–106,548 ms |
| SQL execute atribuido a authorize, 93 llamadas | 53,510–62,168 ms |
| record completo, cuatro llamadas | 262,145–281,842 ms |
| SQL execute atribuido a record, 80 llamadas | 50,295–54,354 ms |
| page completo, cuatro llamadas | 488,613–520,660 ms |
| pipeline.sync de fuentes de cadena, cuatro llamadas | 33,040–43,811 ms |
| canonical_bytes, 1705 llamadas | 45,699–47,639 ms |
| unseal, 193 llamadas | 29,650–32,560 ms |

Inclusivos se solapan y no se suman. Fetch menos adaptación no equivale a transporte TCP: incluye protocolo/libpq, ejecución PostgreSQL, sincronización y desplanificación. La hidratación tiene tres muestras alrededor de 16 ms y una de 50,851 ms; no se ha aislado causa del outlier. Cada getter observado conserva el trabajo original, pero temporizadores/proxy añaden overhead.

Controles TCP: 868,679 / 796,779 / 841,239 / 791,469 ms, frente a tandas previas de 1,6–1,8 s sin cambio productivo entre ellas. No se atribuye esa diferencia a una optimización ni se ajustan tiempos por resta de overhead. Las observadas son 802,709 / 824,552 / 851,124 / 873,297 ms. Población/scope distintos del histórico de 383 lotes acumulativos y sus binarios revisados/entregados; no explican por sí solos p95 3,753392 s ni aceptan 2 s. No medir adaptación bajo estas condiciones como cota del ahorro de una reescritura arquitectónica.

Resultado: adaptación pura no domina; no priorizar protocolo binario/reescritura de modelos para resolver segundos. El usuario dirigió la siguiente investigación a un cambio de enfoque y búsqueda web independiente: [brainstorming y prototipo](mod08-brainstorm-web-20261011.md). Procesos y contenedores propios retirados y comprobados; no publicación, gasto, proveedores o datos reales.
