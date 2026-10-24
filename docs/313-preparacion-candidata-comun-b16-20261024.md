# B16-352 — Preparación de candidata común

B16 permanece abierto y13/18puntos cerrados. La candidata actual contiene638rutas de producto/estáticos. Frente a195459-bacfc549 hay16rutas nuevas y20modificadas; sus3460nodeids únicos históricos y sus siete fallos no aceptan esta candidata. El último focal090124-aaa54693 coincide por fuentes de producto, pero sólo ejecuta12casos.

## Diferencia respecto a evidencias previas

Se conserva el [historial118](118-correctivas-regresion-amplia-beta-20261020.md): original3331PASSúnicos/7FAIL/122SKIP, seguido del correctivo126de15casos y reutilización auditada en aquel corte. No convertir errores/subreportes en pruebas únicas ni trasladar esa conciliación a un árbol posterior distinto. Las candidatas comunes de perfil034242 y exposición043105 también difieren de producto; no sumarlas como B16. El puente de fuentes preparado registra archivos y huellas de cada corte, no equivalencia funcional.

Se preparará un inventario de colección pytest, sin ejecución de tests ni fixtures de base de datos, para identificar alcance común, omisiones declaradas y recorridos largos. Se usará un plugin de observación que sólo guarda nodeids, marcadores y nombres de fixtures; resultado de colección no es PASS funcional. No iniciar baterías de horas por esta preparación.

B10 conserva deuda P2 y MOD09 provisional; hace falta disposición individual explícita antes del acta beta. B14 mantiene la pregunta de proveedores y sus permisos externos; sus simuladores no se consideran integración real. B15 continúa opcional, sin autorizar implementación por esta matriz. B17 y G01–G08 reales no se cierran por preparar la candidata local.

El perfil regression conserva sus exclusiones oficiales; se revisará si hay otros recorridos largos no excluidos, sin retirar pruebas para conseguir un PASS. Las pruebas de carga excluidas necesitan evidencia pertinente o ejecución separada justificada. Los SKIP deberán clasificarse individualmente y no contarán como PASS. Producto, dependencias, migraciones, dataset e instrumentos se versionarán antes de la ejecución común que se decida.

## Resultado de preparación y alcance propuesto

Colección corregida:4146nodeids en677archivos, salida0, cero reportes de ejecución y cero omisiones/errores de colección. El primer intento salió4 por la ausencia de la imagen RustFSfijada; se preservan sus4146elementos parciales y terminal, sin presentarlo como colección válida o ejecución. Repuesta exactamente sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c, con espacio disponible, sin modificar almacenamiento o aplicación.

La partición propuesta conserva3829casos funcionales y306de capacidad, más11exclusiones oficiales sin contarlas como PASS. El recorrido test_portability_large_closed_flow de1500revisiones permanece incluido. Se registran77archivos/83llamadas skip/importorskip y68archivos con posible guardia de selección explícita: clasificación estática heurística, no omisiones ejecutadas.

| Exclusión oficial existente | Casos recogidos | Disposición para B16 |
|---|---:|---|
| Equivalencia territorial1000/10000 | 2 | Evidencia separada vigente o ejecución justificada |
| HTTPshort/measured | 2 | Capacidad aplicable separada, sin trasladar FAIL a PASS |
| Historial aprobado con transporte8MiB | 1 | Integridad/transporte separado de historia mayormente excluida |
| Matriz TCP100/1000/10000repeated/diverse | 6 | Conservar cortes y criterios, justificar prueba/reuso |

La lista oficial no se cambia. Una colección exitosa no acepta esas exclusiones ni hace opcional una obligación del contrato. Los15marcadores skipif recogidos tampoco son15omisiones: la condición y resultado se conocerán durante ejecución. Se mantiene la revisión individual de cada SKIP terminal.

[Matriz propuesta](evidencias/b16-candidate-test-plan-20261024.json), [puente de identidad](evidencias/b16-source-identity-bridge-20261024.json), [inventario estático de omisiones](evidencias/b16-static-skip-inventory-20261024.json) y [dependencia repuesta](evidencias/b16-restored-test-image-20261024.json). Las filas AD01–AD11 contienen criterio, archivos con SHA, evidencia histórica, archivos de prueba propuestos y nodeids recogidos; AD08 queda opcional/no implementado, no PASS. El mapeo es una propuesta del agente: que un test se llame apropiadamente no demuestra por sí solo cobertura semántica ni aprobación del requisito.

Se añaden grupos de autoridad privada B00, cola/galería/observación B09, formularios B11, guardia B14, observabilidad B12 y cifrado/recuperación B13. La selección completa sigue incluyendo el resto de los carriles; estos grupos no sustituyen todas las regresiones. Inventariadas178fuentes de migración, pyproject/uv.lock, generador de datos e instrumentos; los datasets de ejecución y servicios propios se fijarán al congelar la candidata. El manifiesto previo al bookkeeping es inventario, no una congelación final.

## Condiciones antes de aceptar

No hay acta B16, candidata congelada ni nuevas pruebas funcionales acreditadas. Las aceptaciones locales previas permanecen en su corte. La nueva batería común se justifica por cambios actuales de autoridad, recuperación, cifrado, exposición y los dos últimos cambios focalizados, no sólo por este documento. Preparar ejecución persistente, avisos, relevo y procedimiento autorizado de espera si el alcance requiere horas; no ejecutar cargas adicionales hasta revisar resultados y necesidad. Los criterios de recursos y capacidad no se reducen para acelerar las pruebas.

B10 conserva pendiente su disposición no crítica individual, B14 la elección/autorización/integración real, B15 diseño opcional y B17 apertura/G01–G08. Ninguno se convierte en PASS por la colección o la matriz. Se mantienen13/18puntos cerrados; objetivo completo activo.
