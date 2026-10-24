# B12 — Observabilidad operativa de beta

Estado: primera unidad verificada localmente con seis casos PostgreSQL; resto de B12 pendiente. No cierra B12 ni modifica el FAIL de capacidad. Depende del [roadmap103](103-roadmap-beta-clasificados-20261020.md); operación puede avanzar independientemente de las optimizaciones de lectura. Corte previo: grafo64, SHA84b9b00456f678ccaf37acaefe7426ac499e381df930a97b1106165530ebba30, actualización semántica dirigida, sin reconstrucción global.

## Fuentes y carencias comprobadas

`apps/listings/discovery.py` entrega un diccionario request-local `_publication_route`; `publication_state.state_page` registra ruta y motivo del fallback. Los consumidores encontrados son instrumentos de benchmark y pruebas, no un recolector operativo continuo. No confundir la existencia de observación con frecuencia medida en servicio.

`publication_state.sweep` emite `publication_state_divergence` con cantidad agregada. `PublicationDirty.marked_at` conserva la primera marca desde el último recálculo, útil para medir atraso, sin leer IDs al emitir métricas. El task de refresco dura como máximo50s por invocación por defecto, Beat programa refresco cada30s y barrido cada3600s. Son configuración, no garantía de ejecución puntual ni plazo contractual de vaciado.

`notice_delivery.process_outbox` entrega contadores locales processed/simulated/retry/failed y procesa ReportNotice, ComplaintNotice y RightsNotice. Reintenta hasta cinco intentos; su salida no prueba entrega externa. PRODUCTION o backend distinto de simulator deshabilitan ese procesador. La supervisión debe conservar explícitamente esta diferencia.

Las purgas periódicas de safety.tasks filtran expires_at vencido y purged_at ausente. El acceso lógico vencido no acredita que se haya vaciado contenido físico; una fila marcada tampoco prueba ausencia de objetos huérfanos. Exportaciones y objetos requieren comprobar sus mecanismos propios. RightsPortabilityExportJob tiene estado durable, available_at y lease_until; no deducir antigüedad de Redis contando sólo mensajes.

## Entrega prevista y límites

Primera unidad: recolector administrativo de sólo lectura, sin endpoint público, que produzca JSON de esquema versionado con contadores y edades. Ejecutarlo explícitamente; no instalar cron, conectar proveedor o modificar servicios normales. Una instantánea de base de datos representa trabajo durable pendiente, no profundidad exacta de broker, heartbeat ni éxito del worker.

Usar agregados SQL Count/Min con filtros explícitos por estado y un instante común. No leer payloads cifrados, nombres, UUID, filtros de búsqueda, preferencias, URLs, excepciones libres ni contactos. Fallos de base de datos deben producir salida terminal distinta de cero y mensaje fijo; nunca un snapshot vacío aparentemente sano. Excluir los objetos privados de la salida, incluso en errores. Antes de fijar aislamiento, revisar compatibilidad de conexiones heredadas y no alterar sesiones del llamador.

Primera cobertura: backlog de publicación y edad desde marked_at; avisos queued/retry/failed con separación de reintentos aún no exigibles; export jobs queued/running/failed y leases vencidos; temporales vencidos pendientes de purga con registro explícito de modelos y tareas. Sin umbrales inventados: emitir medidas y comprobar después cadencia/coste real antes de adoptar presupuestos de alerta. Desconocido, deshabilitado y cero deben distinguirse.

Segunda unidad: frecuencia de rutas/fallback y errores de tareas, con nombres de evento y valores acotados por allowlist. Evitar contadores en memoria por proceso presentados como globales y evitar añadir escritura o consultas por petición sin medir coste. Elegir destino y ciclo de retención local después de verificar instrumentación existente y límites de logs. No adoptar un proveedor ni enviar telemetría externa.

Tercera unidad: runbook que relacione señales con inspección de Beat/worker/broker, recuperación y retirada segura. Los responsables reales para apertura quedan en G01–G08. No dar por detectada una caída sólo porque quedan filas pendientes.

## Verificación necesaria

Pruebas PostgreSQL sintéticas deben distinguir cola futura/exigible, expiración en el límite, cola vacía, lease activo/vencido y error de lectura. Verificar que recolectar no muta filas, dispara tareas ni descifra contenido, y que la salida tiene sólo campos permitidos. Comprobar completitud del registro de purgas frente a las tareas concretas; no asumir que todos los modelos con expires_at son purgables.

Después, inyectar fallo de entrega y retraso de procesamiento en recursos propios; recoger señal antes y después de ejecutar el worker real y conciliarlos. Hacer controles de retirada y expiración independientes del recálculo: la observabilidad no sustituye autoridad nativa. Las pruebas irán notificadas y con fuentes congeladas. Medir coste del recolector antes de elegir intervalo; no ejecutar una batería de capacidad por este diseño.

Salida de B12: señales integradas con umbrales justificados y respuesta documentada, fallos inyectados detectados y recuperación conciliada, sin datos personales. Este documento por sí solo no satisface esa salida. B13 continuidad y B14 adaptadores reales conservan sus criterios separados.

## Unidad1 — implementación preparada

`apps/core/operational_snapshot.py` y el comando `manage.py operational_snapshot` implementan el primer snapshot explícito. Requieren PostgreSQL y transacción propia, rechazan transacciones heredadas/autocommit desactivado, usan REPEATABLE READ READ ONLY y timeout SQL5s local. Sólo se devuelven agregados y configuración acotada; no se instala monitor continuo. Verificación posterior: seis casos PASS auditados; alcance y límites al final.

`available_queued` clasifica trabajos queued por available_at, sin validar autoridad, caducidad ni intentos para generar; puede incluir trabajos que reconciliación debe rechazar. `expired_lease` y `missing_lease` son subconjuntos de `running`, no sumandos. La edad usa marked_at en publicación, created_at en avisos/colas futuras/running/failed, available_at en queued disponible y lease_until en leases vencidos. En purgas simples usa expires_at; en borradores finales usa created_at, no la demora sobre24h.

Cobertura explícita:11modelos de temporales de safety.tasks más borradores finales no emitidos. No acredita purga de objetos físicos, confirmaciones de cuenta, medios ni profundidad Redis/vida del worker/frecuenciafallback. Los campos not_measured de la salida conservan estas carencias. Los fallos de consultas se convierten en error fijo sin JSON parcial; no se acepta cero como sustituto de un error.

Pruebas ejecutadas: seis casos con PostgreSQL, incluyendo snapshot vacío/alcance SQL, avisos futuros/exigibles/agotados y privacidad, rechazo de transacción heredada, error saneado sin salida parcial, registro de purgas frente AST de tareas y export job real con leases/fechas junto a selección futura/vencida/purgada. Revisión readonly inicial solicitó esta última cobertura; se añadió antes ejecutar. El resultado auditado se registra a continuación.

## Resultado terminal de unidad1

Ejecución224828-eb4d76fa:6PASS/0FAIL/0ERROR/0SKIP,53,709sJUnit. [Auditoría terminal](evidencias/b12-snapshot-terminal-audit-20261020.json): fuentes congeladas y comparación fresca, seis nodeids únicos, PostgreSQL/Redis propios eliminados, temporal y procesos ausentes y Telegram terminal confirmado. Se mantienen idénticas las fuentes de producto preexistentes respecto129; se añaden sólo módulo recolector y comando administrativo. No se modifican rutas públicas, tareas ni esquema.

Se comprobaron filas reales de avisos, export job y selección de portabilidad: límite ahora/futuro, leases activo/vencido/ausente, expiración y exclusión al marcar purga. Los fallos inyectados aquí son de consulta, no caída de worker ni entrega externa. El estado purged_at no acredita borrado físico de objetos. La unidad1 está verificada en ese alcance; B12 continúa abierto.

Pendientes antes de cerrar B12: medir coste/cadencia del recolector, integrar frecuenciafallback y errores de tareas con destino local acotado, establecer umbrales justificados y respuestas, inyectar fallo de entrega/retraso con worker real y conciliar recuperación. B07 sigueFAIL; no se ejecuta nueva capacidad por esta unidad.
