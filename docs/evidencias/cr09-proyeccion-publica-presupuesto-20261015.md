# Proyección pública: presupuesto con cobertura global

Run `20261015-151823-b6e2081d`, base `f3256f1` más ampliación de diagnóstico:1PASS96.53s. Fuentes y limpieza independiente verificadas. El diagnóstico anterior sólo midió conteo+página sobre copia compacta; faltaba coste de cobertura y ancho completo del estado. Este run incluye todos los campos de estado y las tres copias fuente, índices equivalentes de PK/FK más orden y GIN, y misma comprobación global antes de conteo+página en ambos brazos. No comparar ambas series como mejora de código: su alcance es distinto.

| Cobertura+conteo+página:CPU(ms) | Actual | Proyección |
|---|---:|---:|
| listado,página1 | 10.833 | 7.500 |
| listado,página2 | 8.750 | 5.417 |
| photography,página1 | 42.917 | 15.417 |
| photography,página2 | 45.833 | 12.500 |
| synthetic,página1 | 46.250 | 14.583 |
| synthetic,página2 | 45.000 | 15.000 |
| zzznomatchproof,página1 | 7.500 | 4.583 |

| Almacenamiento propio de10kdatos(bytes) | Actual | Proyección |
|---|---:|---:|
| Heap | 1417216 | 4718592 |
| Total con índices | 2301952 | 6815744 |

Ahorro se mantiene en336operaciones medidas,7casos,conteos/IDsordenados iguales. CPU100Hz, snapshotRR estático por caso,4calentamientos+3bloques alternos×8. Representación/índices/estadísticas diferentes: no atribución causal exclusiva al join. Mantenimiento/WAL/latencia HTTP/cambios concurrentes siguen sin medir; último p95limpio5.004966sFAIL intacto.

[Auditoría documental independiente](cr09-proyeccion-publica-mantenimiento-auditoria-20261015.md), escritor nativo en worktreeaislado basef3256f1, únicoMarkdown asignado; sin tests/cargas/Git/producto, no ClaudeV1. Principal contrastó fuentes de copia, upsert/IS DISTINCT FROM, generación/locks, sweep/hash, corte candidates y GeneratedField. Es entrada estática revisada, no prueba de frescura.

Decisión: implementar candidata acotada sobre PublicationState existente, con migración aditiva/versionado/marcas de existentes, copia exacta de fechas y vector persistido de revisión aprobada y vigilancia de sweep. Usar sólo con ownRR limpio/cobertura actual/candidatos originales de listado o q; filtros activos, clones, dirty, búsqueda calculada y transacciones heredadas retienen vía anterior. Mantener misma hora capturada, rank/orden, hidratación/guardia nativas y fallback. Probar persistencia, cambios de fuente, migración, igualdad de población y carreras dirigidas antes de carga. No aceptación global/CR09/N3 ni cambios de cuotas desde TEMP.
