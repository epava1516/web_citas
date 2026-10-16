# Conteo por conjuntos disjuntos: contraste rechazado

Producto basebaeb062, aplicación sin cambios. Test explícito `tests/test_owned_count_partition.py` sustituye sólo el conteo de `_state_page` dentro de su namespace de prueba. Mantiene íntegra la consulta original de selección/página y su guardia final. Con RRpropio,dirtyynativeno vacíos, divide el count entrepopulation_query.filter(trusted_visible) ypopulation_query.filter(pk__in=native).exclude(trusted_visible), conservando las reglas de DISTINCT de cada brazo. El segundo brazo excluye explícitamente solapamientos. Inherited,limpio,nativevacío yproyección siguen originales.

Motivo del contraste: diagnóstico actual004422-7ee64fc7 observó58–114ms de count en tres ocupantes iniciales. Revisión lógica independiente nativa no encontró contraejemplo bajo esas condiciones, pero recomendó controles ampliados de multiplicidad/checked/orden/solapamiento/vacío/rango antes de cualquier adopción. No es aceptación ni ejecución atribuible al agente.

Django5.2 usa un [count separado en Paginator](https://docs.djangoproject.com/en/5.2/ref/paginator/); la implementación instalada se inspeccionó antes de precargar su cached_property. PostgreSQL puede [combinar condiciones OR mediante índices](https://www.postgresql.org/docs/17/indexes-bitmap-scans.html); separar consultas no garantiza un plan mejor. Esas fuentes justifican el análisis, no un resultado de rendimiento.

Primer run012245-4af75967:1PASS108,19s/108lecturas, con actividad propia de actualización del grafo solapada. Fue un error de aislamiento del experimento; se conserva como condicionado y no se usa como única base para decidir. Recursos/fuentes verificados antes de una única confirmación.

Confirmación aislada012540-47dda797: **1PASS108,13s**,108lecturas completas sobre10000anuncios sintéticos, limpio/dirty1 × listado/búsqueda/sincoincidencias ×3bloques AB/BA ×3repeticiones por brazo. Sin perfiladores ni otra tarea propia en paralelo. [Recibo de ambos runs](cr09-count-partition-terminal-20261016.json).

| Dirty1, media state_page | Actual ms | Separado ms | CPU actual ms | CPU separado ms |
| --- | ---: | ---: | ---: | ---: |
| Listado | 283,596 | 305,622 | 139,777 | 157,990 |
| Búsqueda | 338,769 | 366,946 | 155,206 | 173,481 |
| Sin coincidencias | 72,922 | 70,199 | 34,444 | 34,228 |

| Bloque dirty, media de3casos | Actual ms | Separado ms |
| --- | ---: | ---: |
| 0 | 269,714 | 249,235 |
| 1 | 229,597 | 260,178 |
| 2 | 195,977 | 233,354 |

**Rechazado:** listado/búsqueda yCPU empeoran en agregado, dos bloques de tres empeoran; no hay beneficio consistente. Igualdad de conteo e IDs ordenados en el fixture, no paridad integral de todos los límites. No implementar el prototipo ni gastar nuevas pruebas de frontera en un cambio sin beneficio. Las variaciones limpias son ruido: ambas ramas ejecutan código idéntico allí. No p95 extrapolado ni causalidad cuantificada desde estas medias secuenciales.

Ambos runs con PostgreSQL/Redis propios, kernel native-sealed, mismas cuotas del adaptador acotado y datos sintéticos. Hashes exactos originales y controlador/hijo/temporal/contenedores ausentes verificados independientemente; unidades terminalesMainPID0. Test y resultados se conservan; ninguna carga HTTP nueva. Último limpio de directorio continúa0,904873942sFAIL. CR09/N3 y el resto del contrato permanecen abiertos.
