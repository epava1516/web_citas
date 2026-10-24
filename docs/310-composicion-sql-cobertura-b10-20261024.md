# B10-349 — Composición SQL de cobertura

B10 sigue abierto; doce de18puntos cerrados. Tras309 se observan106consultas por página de cobertura. Se prerregistra clasificación del mismo recorrido con100revisiones retenidas, sin cambio de aplicación, para localizar funciones/tablas/operaciones antes de proponer una optimización.

## Instrumento previo

Se amplía sólo el diagnóstico existente con un contador durante coverage_page_intake. Cada ejecución de SQL se asigna una vez a operación, conjunto de tablas registradas en modelos Django y primera función apps.safety de la pila. Se conserva únicamente ese vocabulario estático y el contador: sin sentencia, parámetros, valores, identificadores de casos o sujetos. Las tablas que coaparecen en una consulta se agrupan; no contar cada tabla como una consulta independiente. Los frames se liberan al terminar la observación.

La suma de categorías debe coincidir con las consultas del tramo medido; esa consistencia no demuestra redundancia ni seguridad de eliminarlas. Se mantienen flujo, oráculos, lectura real de WebP y todos los cuerpos originales. La inspección de frames añade coste: no comparar latencias como mejora antes/después ni inferir SLO de este perfil.

Se selecciona únicamente tests/test_export_flow_stage_cost.py::test_native_closed_flow_cost[100], un caso, PostgreSQL/Redis propios, un worker, timeout1200s y RSS Python menor de1GiB. Las cuatro guardas de cierre del corte348 permanecen como testigos anteriores y no se presentan como ejecutadas de nuevo.

Se verificará fuente congelada, resultado sin omisiones, integridad de manifiesto/WebP/ZIP, limpieza y Telegram. La clasificación orientará la siguiente revisión; no autoriza caches de autoridad ni retirar auditorías. MOD09 mantiene sus criterios y aceptación provisional original.

## Resultado y atribución

Ejecución20261024-082841-bba147e0:1PASS/0FAIL/0ERROR/0SKIP,97.753sJUnit,1720fuentes congeladas verificadas y637rutas de producto/estáticos idénticas al corte348. Limpieza de contenedores/directorio/PID y Telegram confirmados; sin cambio de aplicación.

[Auditoría durable](evidencias/b10-coverage-sql-composition-20261024.json).

Las111páginas conservan11766consultas:10212SELECT(92/página),444INSERT(4/página),555SAVEPOINT y555RELEASE(5pares/página). El recorrido completo conserva18110consultas, igual que el diagnóstico anterior. La suma de todas las categorías coincide con la observación original.

| Primera función safety en pila | Total en111páginas | Por página |
|---|---:|---:|
| apps.safety.rights_scope.permitted | 2220 | 20 |
| apps.safety.rights_scope.agency_conflict | 1554 | 14 |
| apps.safety.rights_portability_coverage_inspection.inspect_page | 1332 | 12 |
| apps.safety.rights_scope.locked_case | 1332 | 12 |
| apps.safety.rights_portability_review.<genexpr> | 1110 | 10 |
| apps.safety.rights_portability_selection_review.record | 777 | 7 |
| apps.safety.rights_portability_review.authorize | 555 | 5 |
| apps.safety.rights_portability_selection_store.validate_selection_evidence | 555 | 5 |
| apps.safety.rights_verification.authorized_proof | 555 | 5 |
| apps.safety.rights_exports.image_contents | 333 | 3 |
| apps.safety.rights_portability_coverage_batch.inspect_batch | 222 | 2 |
| apps.safety.rights_responses.complete_response_read | 222 | 2 |
| apps.safety.rights_verification.complete_read | 222 | 2 |
| apps.safety.rights_portability_review.validate_approved_assessment | 222 | 2 |
| apps.safety.rights_portability_selection_review.validate_approved_selection | 222 | 2 |
| apps.safety.rights_portability_image_read.required_reads | 111 | 1 |
| apps.safety.rights_portability_selection_review.validate_evidence | 111 | 1 |
| apps.safety.rights_portability_images.audited_images | 111 | 1 |

La clasificación permitted incluye consultas de funciones anidadas de otros módulos, como transfer_conflict; no afirma que todas estén escritas directamente en ese cuerpo. Los joins se cuentan una vez por sentencia, no por tabla; no se guardan parámetros o sentencias. La sonda añade inspección de pila: los tiempos no son un antes/después de optimización. Las cuatro guardas de cierre siguen acreditadas en348, sin presentarlas como parte de este caso.

## Contraste de código y decisión

rights_scope.agency_conflict ya hace una sola sentencia fresca con EXISTS de membresía y propietario; incluye membresía inactiva/histórica. No hay una segunda consulta por llamada que retirar. permitted revisa actor, sujeto, agencia, transferencia y aceptación. rights_portability_review.authorize recarga User y contrasta actividad, MFA, versiones, permisos y ámbito; las dos consultas de permisos por usuario fresco corresponden a las rutas de permisos Django observadas. Reutilizar un usuario retenido o una autorización memorizada alteraría la garantía de revocación, sin evidencia de seguridad o mejora que lo justifique.

Los34SELECT/página de permitted+agency_conflict y los15SELECT/página de authorize y su generador identifican coste en rutas de autoridad; no prueban redundancia. Los bloqueos de locked_case se adquieren de nuevo en operaciones anidadas: suprimirlos requiere demostrar orden y validación tras esperas. Los cuatroINSERT y savepoints incluyen evidencia nativa de inspección/selección; no se retiran para obtener un contador menor. No se adopta cache entre peticiones, índice, cambio de criptografía o relajación de controles.

B10 continúa abierto: esta medición localiza composición del coste, no acepta el extremo MOD09, un índice de similitud, capacidad o beta. Queda justificar el extremo aplicable de similitud y conciliar la deuda separada y salida de etapa3. Se mantienen12/18puntos cerrados y objetivo completo activo.
