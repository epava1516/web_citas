# CR09: lectura por lotes de pendientes y primera página

Run `20261016-081246-01e6b6a8`, base `ded6727`: **1 PASS, 220,46 s**, 288 requests medidas. **Elegible para pasar a N2**: ahorro superior al umbral previo en ambas rutas. No se ha integrado en producto ni medido un p95 HTTP nuevo.

## Cambio experimental

La ruta con marcas pendientes construía dos PublicationContext: uno para validar los IDs pendientes y otro para hidratar/revalidar los 24 seleccionados. El diagnóstico anterior observó 21 SQL por constructor.

Sólo en primera página, RR propio, censo/versionado vigente y protocolo proyectable sin checked: se preleen los primeros 24 IDs fiables sin marcas con el mismo orden/filtro/fecha. Se hidratan junto con los pendientes (≤48), en un lote de ≤72. La validación nativa de pendientes decide pertenencia; la población, el recuento y la selección originales no cambian. La guardia nativa de página sigue ejecutándose sobre el contexto ya leído. Si algún ID seleccionado no está en el lote, se hidrata por el camino original. No se adopta el UNION anterior ni se cambian triggers, bloqueos o semántica de escritura; no hay caché entre requests.

## Paridad y ROI

N1 previo `081003-e2de0632`: 40 comparaciones de cuerpos, IDs ordenados, count y páginas inicial/intermedia/última en cuatro transiciones, ES/EN y listado/búsqueda. Diez activaciones, diez reutilizaciones, lotes de 1 o 25 IDs, 0 fallback por seleccionado ausente; páginas posteriores sin batching. Es cobertura parcial y no sustituye N2 de negativas, límites y concurrencia.

El ROI conserva el método anterior: 10.000 anuncios sintéticos, PostgreSQL real propio, WSGIHandler sin Client/captura de contexto. A/B código actual idéntico y C candidato; ABC/BCA/CAB × dos rutas × seis warmups + 16 medidas = 288 medidas. Conexión calentada con PID constante por brazo; planes fuera de reloj. GC normal en requests, colección explícita sólo antes del warmup para aislar basura del brazo anterior. Sin perfiladores.

| Ruta con Dirty1 | Actual A/B, wall medio | Candidato | Reducción wall | Reducción CPU |
|---|---:|---:|---:|---:|
| Listado ES | 296,93 ms | 215,40 ms | 27,46 % | 25,91 % |
| Búsqueda EN | 356,18 ms | 287,29 ms | 19,34 % | 22,23 % |
| SQL por request, ambas rutas | 64 | 44 | 31,25 % menos consultas | — |

A/A se mantiene bajo la cota de discrepancia del 10 % en wall/CPU por ruta. C supera el ahorro wall ≥10 %, no regresa CPU y mejora wall en los tres bloques de cada ruta. No se han cambiado umbrales después de observar. Los 132 lotes se reutilizan, máximo 25 IDs en este fixture y 0 fallback ausente. Cuerpos/200/no-store/ruta native_query y marcas/generaciones permanecen. Las 288 muestras completas están en el artefacto local `first-page-batch-roi.json`; el recibo conserva resumen, preparación y contadores.

## Límites y siguiente paso

Se mantiene una marca controlada durante toda la comparación, sin el calendario real de upload/Beat: puede exagerar el peso temporal de la ruta frente a la carga contractual. Estas cifras son tiempos medios secuenciales y no p95 ni predicción de cola concurrente. El máximo 72 del algoritmo aún requiere frontera con 48 pendientes; el máximo ejercitado fue 25. Tampoco se ha verificado aquí concurrencia, fallback forzado, normalización no canónica o PRODUCTION.

Siguiente N2: negativas de elegibilidad y nativa repetida, catálogo/autoridad/normalización pertinentes, límite/bypass/fallback y escritura concurrente dentro de RR; después integración y matriz comparable, corto limpio y contractual sólo tras PASS. CR09/N3 siguen abiertos; último p95 limpio permanece 1,013029795 s.

Fuentes congeladas y JUnit 1/0/0/0 comprobados independientemente. PIDs/start_ticks terminados, temporal eliminado, contenedores ausentes y cgroup vacío. Controlador afinidad0–3/3584 MiB/swap0/512 tareas; PostgreSQL 1 CPU/1536 MiB y Redis propio, sin otra carga propia. Puertas de dependencias congeladas, Ruff/docs/Django/migraciones y kernel native-sealed pasaron. Sin producción, proveedores ni invocaciones Claude nuevas.
