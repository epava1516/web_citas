# CR09 — agrupación de primera página integrada

La implementación productiva conserva una sola hidratación para unknown y el prefijo limpio en la primera página cuando el propio snapshot RR/censo/protocolo permiten hacerlo. La población, el total y la selección siguen siendo nativos; se valida la pertenencia unknown antes de incluirlos y cada seleccionado mantiene el guard final. Si los seleccionados no quedan cubiertos, se utiliza la hidratación anterior. No cambian aislamiento, reglas, límites, invalidación, workers ni recursos.

El helper devuelve como máximo24IDs limpios ordenados igual que la población. Con hasta48unknown, el contexto tiene como máximo72padres; no es una cota de hijos/bytes. La sobrelectura fuera de página se conserva como limitación explícita. [ROI heterogéneo](cr09-first-page-batch-fanout-roi-20261016.md) supera criterios en el escenario128municipios, sin acreditar toda distribución posible.

Se conserva en tests la fuente anterior al cambio como referencia independiente; comparte las reglas auxiliares vigentes, no congela todo el dominio. El adaptador instrumental ejecuta ahora la fuente de la función productiva con contadores, en lugar de construir otro algoritmo. Orden/fanout, expiración y edges se incorporan a colección normal. Orden y expiración comprueban también entrada productiva sin instrumentar.

## Verificación

- Expiración previa a integrar, `090217-0cb7756b`:2PASS. Reloj adelantado en el guard, caso pending y limpio; ambos rechazan el vencido, marcan igual y recurren al camino nativo con idéntico cuerpo.
- Integración `090613-d2b145a2`:**32PASS/0fallos/0errores/0omisiones**,353,57s de pytest. Incluye paridad40comparaciones, límites1/24/48/49, filtros/protocolo/RC heredado/censo, commits concurrentes después de preview, stale simulado, orden y NULL, relaciones fuera de página, expiración, revisiones ajenas, descubrimiento público y restauración del ámbito de consulta.
- Dependencias bloqueadas, Ruff, docs, Django y migraciones:PASS. PostgreSQL propio real, Python3.12.15/kernel native-sealed, datos sintéticos y presupuestos anteriores; sin producción ni proveedores.
- Fuentes congeladas contrastadas independientemente antes de documentar. PID/start_ticks de controlador e hijo ausentes, temporal retirado, contenedores propios ausentes y cgroup terminal vacío. [Recibo con hashes](cr09-first-page-batch-integration-20261016.json).

La matriz focal no sustituye regresión integral/N3 sobre versión común. No hay un nuevo p95. El próximo paso es imagen identificada de estas fuentes y su comprobación real, seguida del corto limpio sin perfiladores; una aprobación del corto requiere repetición para reproducibilidad. Un fallo debe conservarse y diagnosticarse por separado.
