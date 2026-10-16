# Planes actuales de población dirty

Run110032-209b058a, fuente8a5e894:1PASS88,00s. Cuatro rutas/10ksintéticos/un dirty; ocho planes posteriores a requests. Fuentes originales y limpieza comprobadas; dos archivos de prototipo se añadieron sólo después del terminal. [Recibo y planes](cr09-detail-dirty-plans-20261016.json).

| Ruta | Recuento ejecución(ms) | Selección ejecución(ms) |
|---|---:|---:|
| /es/ | 16.942 | 9.909 |
| /en/ | 21.421 | 18.121 |
| /es/?q=photography | 31.427 | 32.927 |
| /en/?q=synthetic | 26.007 | 27.794 |

Sin JIT ni SharedReadBlocks en estos planes; búsqueda recorreListing/PublicationState/Revision para recuento y vuelve a recorrerlos para selección y orden. No afirmar ausencia deIO/JIT en la carga original. PlanningTime0,162–3,348ms en este control, no cuello dominante aquí. SQL node times son inclusivos, no sumables. [PostgreSQL17 explica estos límites](https://www.postgresql.org/docs/17/using-explain.html).

Hipótesis nueva: conservar íntegra la población y ordenar como antes, pero obtener primera página y recuento exacto mediante COUNT(*) OVER() en un únicoSELECT. Prototipo sólo tests, limitado a RRpropio/censo vigente/proyecciónoriginal/sinchecked/sin joinsmultiplicadores/primera página/ruta general. Proyección limpia, páginas posteriores, filtros especializados, RCheredado y guards conservan camino previo. Población vacía primera página tienecount0; ninguna caché de resultados ni unión nueva. Antes de ROI, paridad de40comparaciones reutiliza cuatro transiciones, listado/búsquedaESEN/páginas inicial-intermedia-final, con contador de entrada a nueva rama. ROI posterior requiere umbrales anteriores sin relajación; aún no ejecutado.
