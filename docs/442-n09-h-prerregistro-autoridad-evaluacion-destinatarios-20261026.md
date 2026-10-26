# N09H — prerregistro de autoridad en evaluación de destinatarios

Estado: propuesta diagnóstica de8casos sin ejecución; no hay nuevoFAIL/PASS ni corrección de aplicación. Base masterf95b301, [N09G441](441-n09-g-evidencia-final-rectificacion-verificada-20261026.md) entregado. N09 completo139IDs abierto,8/13bloques obligatorios aceptados, alpha/noindex. F75/E38/G18 conservados sin repetir.

Corte previo: grafo4412076fuentes20196nodos84290relaciones976comunidades, SHA526b3e9bed9157fbf9482af83677579044357bfda5b95952765755823735f3aa. Todas las fuentes del manifiesto contrastadas. Consulta focal5módulos51nodos442relaciones incidentes; no reconstrucciónN15 ni nueva semántica exhaustiva.

Hipótesis: recipient_assessments.inspect/propose comprueban tres permisos sobre el User inicial antes de Inventory; recipient_review.inspect/review añaden review_recipient_assessment antes de Assessment/current. Después materializan inventario o decisiones con unseal. No hay captura explícita de epochs ni User nuevo tras la espera en esos consumidores. La autenticación de vistas no acredita autorización actual. Es análisis de fuente, no vulnerabilidad runtime confirmada.

| Operación nativa | Fila retenida | Target privado exacto | Permiso retirado |
| --- | --- | --- | --- |
| recipient_assessments.inspect | Inventory | unseal(encrypted_inventory) | review_rectification |
| recipient_assessments.propose | Inventory | unseal(encrypted_inventory) | review_rectification |
| recipient_review.inspect | Assessment | unseal(encrypted_decisions) | review_recipient_assessment |
| recipient_review.review | Assessment en current | unseal(encrypted_decisions) | review_recipient_assessment |

Selección: cuatro controles válidos y cuatro negativos, uno de cada por operación,8previstos. Son cuatro operaciones de dos rutas, no ocho bugs/IDs/bloques. Instrumento nuevo tests/test_recipient_assessment_authority_wait.py, escritor nativo aislado en /tmp/web-modelos-n09h-recipient-20261026 con propiedad sólo de ese archivo y reporte ignorado. No ejecuta herramientas de prueba ni corrige app. Root integra tras revisar alcance, imports, fixtures, snapshots y efectos; su complete no acredita aceptación.

Fixture: reutilizar la saga nativa ejecutada F/G, crear inventario por servicio; propuesta requiere inspección auditada. Revisión usa autor distinto, desasignación/claim, prueba y lecturas frescas; revisar requiere inspección propia anterior. No fabricar filas cifradas, no cambiar reloj ni caducidad como parte de estos ocho casos. Mantener permisos adicionales de preparación separados del contrato real.

Espera: PostgreSQL propio serial, primer FOR UPDATE pertinente, backendPID distinto y pg_stat_activity wait_event_typeLock con holder en blocking_pids antes de retirar permiso. User nuevo confirma revocación; commit del holder libera la fila. Observer reenvía exactamente ciphertext y cuenta entrada/retorno del target sin registrar contenido. Snapshots de dominio/through salvo sólo concesión retirada, estado mínimo y archivos; timeout/cancelación/finally y conexiones cerradas obligatorios.

Oráculos: control produce exactamente Action en inspecciones; propuesta añade Assessment y actualiza Request; revisión añade Review y actualiza Request. Validar conteos, versión+1/scopeunverified donde corresponda y perfil/publicación intactos. Negativo PermissionDenied antes de target y sin efectos persistidos/físicos. Un fallo de fixture/espera/control no es bug del producto. Rollback posterior no borra un procesamiento privado anterior. Son fronteras seleccionadas, no toda materialización interna.

Antes del runner: revisión propia, Ruff notificado, deltaAST del instrumento y semántica442/17 selectiva, manifiesto y congelación. Runner oficial focused serial con parser nativo/PostgreSQLRedis propios y timeout1800. Telegram inicio/terminal y auditoría de originales/huellas/limpieza antes de corregir. Tiempos cuerpoQA separados de latencia de app; no objetivo de acelerar esta batería ni porcentaje causal.

Pendientes: replays y epochs del llamador requieren revisión si se confirma y corrige el consumidor; preservar replay legítimo sin exigir prueba activa fuera de su estado. APIs F permiten propagar callback por execution_scope_matches/snapshot a esperas internas de cuenta: validar consumidores, no dar cobertura universal por un lock. Otros139IDs/ramastardías/purgas/outbox/jobs siguen abiertos; N02restante al final/N10N11N15pendientes/N12–N14condicionados. Sin servicios, migraciones, proveedores, escaneos activos o ampliación de producto.
