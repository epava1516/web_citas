# B12 — Retención privada y auditoría de cobertura, 2026-10-21

Estado: ampliación local verificada; B12 cerrado posteriormente en su alcance técnico local por [acta14](actas/14-beta-b12-aceptacion-local-20261021.md) y [conciliación140](140-conciliacion-purgas-beta-b12-20261021.md). No aceptación beta global.

## Retención pendiente de supervisión

La confirmación de cuenta conserva auditoría y elimina únicamente encrypted_delivery cuando expires_at vence. El snapshot añade su contador y edad desde vencimiento; atención a dos cadencias de la tarea configurada, nominalmente120s. No modifica cuentas ni confirma enlaces.

La caché privada de entregas se purga por vencimiento propio o de la exportación, cambio de generación o exportación ya purgada. El snapshot cuenta filas pendientes con esos selectores. Para vencimientos usa la fecha más temprana entre entrega y exportación. La invalidación genera advertencia por presencia: created_at no permite fechar un cambio de generación. Ambos grupos pueden solaparse. No se leen rutas ni contenido ni se inventaría almacenamiento.

## Testigo de worker

El test test_actual_celery_worker_purges_expired_delivery publica con apply_async, mientras sus fixtures activan task_always_eager. Lanzar un proceso worker no demuestra que éste consuma la tarea. Se prepara una guarda que rechaza ejecutar run en pytest y una reproducción negativa focal antes de corregir el emisor. Resultado todavía pendiente; el testigo anterior no acredita por sí solo consumo externo.

## Matriz de cierre

| Requisito | Evidencia disponible | Pendiente |
| --- | --- | --- |
| Eventos fijos, privacidad y transporte acotado | Cortes130–135 y auditorías enlazadas en seguimiento17 | Conservar garantías en integración |
| Ventanas, umbrales y respuestas de atención | Corte137; healthunknown y coverageunverified | Verificar extensión de retención |
| Publicación y outbox con worker real | Corte137; backoff60s natural y reconciliación real | Sin proveedor real ni apertura |
| Medios: fallo parcial, retención y recuperación | Corte138:42PASS y coste serial1PASS | Conservar cobertura |
| Temporales y confirmación de cuenta | Registro explícito de tareas; nuevo selector SQL | Verificada en021432; cuenta y auditoría conservadas |
| Caché privada | Selectores SQL contrastados con la purga | Negativo020632 y worker auténtico021432 verificados |
| Presupuesto del snapshot | Corte138:p95251,026ms y45SELECT | Corte021807 verificado:48SELECT; presupuesto cumplido |
| Objetos huérfanos y ausencia física universal | No medidos por snapshot SQL | No inferir ausencia a partir de contadores vacíos |
| Operación externa, guardias y proveedores | B17 separado | Sin aceptación ni despliegue por esta matriz |

No se amplía el criterio B12 a una prueba imposible de ausencia universal. Se conserva la distinción entre supervisión de trabajo durable, pruebas físicas locales delimitadas e inventario externo no verificado. El siguiente corte debe verificar los selectores nuevos y revisar la tarea horaria de huérfanos del backend opcional antes de cerrar la matriz.

## Reproducción negativa auditada

Corte020632:1FAIL esperado por la guarda del proceso padre. La purga sí se ejecutaba dentro de pytest con eager. Auditoría de fuentes actuales, limpieza y Telegram terminal confirmada en evidencias/b12-delivery-worker-negative-terminal-audit-20261021.json. Se corrige el emisor a app.send_task, manteniendo la guarda; verificación positiva pendiente.

Revisión de la tarea horaria purge_orphan_export_objects: requiere backend de objetos habilitado y recuperación desactivada, enumera referencias vigentes y elimina objetos sin referencia mayores de24h. El snapshot SQL no ejecuta ese inventario ni contacta proveedores. Su señal debe distinguir inventario no medido de ausencia comprobada; no se acepta cobertura universal por esta revisión.

Corte021009:52PASS/6FAIL/0ERROR/0SKIP. Referencia de cadencia mal ubicada en el evaluador: buscaba apps.safety.tasks en vez del módulo real apps.safety.rights_object_delivery. Produjo avisos de cadencia desconocida y faltaron los de atraso; la prueba de worker no llegó a publicar. Corregida la referencia exacta; negativo y limpieza conservados. Repetición positiva pendiente.

## Resultado vigente

021432-cc448ccd:58PASS/0FAIL/0ERROR/0SKIP con4workers,157,011sJUnit. Las cinco pruebas seleccionadas de caché privada pasan, incluida la del worker con guarda contra ejecución en pytest. Verificados vencimiento propio, vencimiento de exportación, generación distinta, restauración y borrado físico local, conservando auditoría. Confirmación de cuenta: umbral120s, payload purgado sin modificar cuenta ni borrar auditoría.

021807-20821c08:1PASS serial del diagnóstico de coste. Fuentes idénticas entre ambos cortes;59casos únicos entre dos ejecuciones, no una ejecución única59PASS. Fuentes actuales, limpieza de contenedores/temporales/procesos y Telegram terminal confirmados.

48SELECT por snapshot. p95 vacío90.735826ms; con50kfilas sintéticas247.556783ms. Presupuesto p95<1s cumplido. Treinta muestras tras cinco calentamientos por estado; primera llamada separada. Las tablas nuevas de confirmación/caché permanecen vacías en este diagnóstico: no demuestra todas sus cardinalidades. No garantía de CPU de servidor ni entorno frío.

Auditorías: [funcional](evidencias/b12-private-retention-functional-terminal-audit-20261021.json), [coste y conciliación](evidencias/b12-private-retention-combined-terminal-audit-20261021.json), [muestras](evidencias/b12-private-retention-snapshot-cost-20261021.json), [negativo eager](evidencias/b12-delivery-worker-negative-terminal-audit-20261021.json) y [negativo cadencia](evidencias/b12-private-retention-first-negative-terminal-audit-20261021.json).

## Respuestas nuevas y pendiente de cierre

Ingeniería ejecuta la respuesta local; operación real y sustitutos requieren asignación en B17. inspect_confirmation_delivery_retention: comprobar tarea normal y backend deshabilitado, purgar sólo payload vencido por el servicio existente, conservar prueba/auditoría y no consumir ni confirmar enlaces. inspect_delivery_cache_cleanup: comprobar cadencia, generación y exportación padre; ejecutar la purga normal con sus guardas y comprobar archivos locales autorizados por separado. No cambiar generación, restaurar grants ni borrar filas de auditoría para silenciar alertas.

La política de caché usa20s nominales (dos cadencias de10s); invalidación visible de inmediato por presencia, sin atribuir edad de invalidación. La frecuencia de muestreo propuesta60s puede observar el aviso después de ese umbral; no es plazo garantizado de detección. Mantener healthunknown/coverageunverified incluso tras desaparecer el aviso.

Siguiente acción B12: conciliar todas las tareas de purga configuradas con señales y testigos, incluyendo el backend opcional de huérfanos; decidir explícitamente el alcance local de inventario no medido. No aceptar por ausencia de hallazgos. B00 residual y B07–B17 siguen abiertos; B01–B06 conservan su aceptación.
