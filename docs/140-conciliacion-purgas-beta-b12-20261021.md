# B12 — Conciliación de purgas e inventario opcional, 2026-10-21

Estado: extensión verificada y B12 aceptado técnicamente en local por [acta14](actas/14-beta-b12-aceptacion-local-20261021.md). Sin aceptación beta global.

## Conciliación literal

Dieciséis tareas periódicas de purga o limpieza de config/settings.py conciliadas con señales y respuestas. Todas figuran en la allowlist de errores de tareas. Esto no prueba ejecución puntual de Beat ni vida del worker. [Auditoría estática](evidencias/b12-purge-task-reconciliation-20261021.json).

| Tarea | Cadencia s | Señal | Alcance |
| --- | ---: | --- | --- |
| apps.mediafiles.tasks.cleanup_prepared_media | 60 | media.physical_jobs.MediaPreparationCleanup | durable_physical_jobs_not_universal_absence |
| apps.mediafiles.tasks.erase_media_files | 60 | media.physical_jobs.MediaErasure | durable_physical_jobs_not_universal_absence |
| apps.safety.rights_object_content.purge_orphan_export_objects | 3600 | object_storage.orphan_inventory | explicitly_unmeasured_inventory_with_failure_events |
| apps.safety.rights_object_delivery.purge_object_deliveries | 10 | private_delivery_cache | durable_delivery_eligibility |
| apps.safety.tasks.purge_expired_access_coverage | 60 | expired_temporaries.RightsAccessCoverage | durable_expiry |
| apps.safety.tasks.purge_expired_access_field_decision | 60 | expired_temporaries.RightsAccessFieldDecision | durable_expiry |
| apps.safety.tasks.purge_expired_access_response_drafts | 60 | expired_temporaries.RightsAccessResponseDraft | durable_expiry |
| apps.safety.tasks.purge_expired_access_scope_inventory | 60 | expired_temporaries.RightsAccessScopeInventory | durable_expiry |
| apps.safety.tasks.purge_expired_account_confirmation_delivery | 60 | expired_account_confirmation_delivery | durable_payload_expiry |
| apps.safety.tasks.purge_expired_copy_information | 60 | expired_temporaries.RightsCopyInformation | durable_expiry |
| apps.safety.tasks.purge_expired_copy_page_reviews | 60 | expired_temporaries.RightsCopyPageReview | durable_expiry |
| apps.safety.tasks.purge_expired_exports | 60 | expired_temporaries.RightsExport | durable_expiry |
| apps.safety.tasks.purge_expired_portability_assessments | 60 | expired_temporaries.RightsPortabilityAssessment | durable_expiry |
| apps.safety.tasks.purge_expired_portability_coverage | 60 | expired_temporaries.RightsPortabilityCoverage | durable_expiry |
| apps.safety.tasks.purge_expired_portability_response_drafts | 60 | expired_temporaries.RightsPortabilityResponseDraft | durable_expiry |
| apps.safety.tasks.purge_expired_portability_selections | 60 | expired_temporaries.RightsPortabilitySelection | durable_expiry |

La tarea de borradores de acceso también limpia borradores finales no emitidos a24h; se supervisan mediante unissued_final_drafts. La limpieza de medios distingue candidatos, trabajo exigible, fallos y retención protegida. Caché privada y confirmación se verificaron en [139](139-retencion-privada-cierre-beta-b12-20261021.md).

## Backend de objetos opcional

El snapshot añade enabled, recovery_mode y orphan_inventory=unmeasured sin consultas SQL adicionales, sin inventario de rutas, sin descifrado y sin contacto con almacenamiento. export_orphan_inventory permanece explícito en not_measured también cuando el backend está deshabilitado: deshabilitar escrituras no prueba ausencia de objetos anteriores.

Con backend habilitado, el evaluador avisa object_orphan_inventory_unmeasured. Durante recuperación informa además object_orphan_cleanup_suspended. No se inventa edad de huérfanos ni se sustituye inventario por recuento de referencias. Los errores de la tarea se observan en task_failed_observed; un resultado succeeded no acredita que el inventario completo esté sano.

Ingeniería atiende en local inspect_object_inventory_in_authorized_storage: revisar ejecución de la tarea, configuración e inventario sólo en el almacén autorizado; distinguir objetos referenciados, huérfanos todavía dentro de gracia24h y huérfanos antiguos. Usar la tarea normal, conservar tombstones y comprobar ausencia con la API del almacenamiento. No borrar referencias para forzar elegibilidad ni desactivar recuperación para silenciar un aviso. keep_recovery_isolation_until_reconciled conserva aislamiento; exposición tras recuperación requiere B13. Responsables y guardias reales, B17.

## Verificación preparada

Ampliar el test PostgreSQL/RustFS existente: objeto huérfano y otro referenciado, gracia24h con reloj sintético explícito, recuperación/deshabilitado impiden limpieza, fallo local inyectado en eliminación sin borrar bytes, hook real de tarea genera evento fijo y evaluación detecta fallo, siguiente ejecución elimina físicamente sólo el huérfano y conserva referencia/lectura. Ejecución eager explícita para este test; no afirma consumo por worker. El testigo de worker auténtico de caché privada permanece separado.

Selección prevista60casos funcionales:58del corte139, una frontera nueva de configuración/inventario y una integración de huérfanos ampliada. Cuatro workers con bases/medios/broker aislados; coste posterior serial sobre las mismas fuentes,48SELECT esperados y presupuesto p95<1s intacto. Primera revisión Ruff falló por import de fixture redefinido; corregido sin ejecutar casos, recibo terminal conservado.

## Criterio de cierre pendiente

Este incremento conserva desconocido el inventario universal y añade una respuesta explícita cuando el backend opcional está habilitado. El cierre local B12 debe conciliar esta limitación con el requisito de supervisión separado de vencimiento lógico y purga física, usando pruebas físicas delimitadas y errores observados. No declarar cumplimiento de apertura, guardia o proveedores por esta evidencia. B00 residual y B07–B17 siguen pendientes.

## Resultado y conciliación vigentes

022632-91e875b1:60PASS/0FAIL/0ERROR/0SKIP con4workers,157,414sJUnit. RustFS local real: fallo inyectado antes de eliminar, objeto todavía presente, evento failed detectado; recuperación con succeeded, huérfano ausente por API404 y objeto referenciado legible. Los hooks se ejecutaron en eager explícito, sin atribuir consumo por worker a este test. La purga de caché sí mantiene testigo separado de worker real.

023008-a83a296a:1PASS serial de coste; fuentes idénticas al corte funcional. 48SELECT, p95 vacío149,731ms y con50kfilas224,161ms, presupuesto p95<1s cumplido. Treinta muestras por estado y cinco calentamientos; tablas nuevas no representan todas las cardinalidades productivas.

[Auditoría funcional](evidencias/b12-optional-storage-functional-terminal-audit-20261021.json), [coste y conciliación](evidencias/b12-optional-storage-combined-terminal-audit-20261021.json) y [muestras](evidencias/b12-optional-storage-snapshot-cost-20261021.json). Fuentes, limpieza y Telegram terminal confirmados.61casos únicos entre dos ejecuciones, sin afirmar una ejecución única61PASS.

[Auditoría de aceptación B12](evidencias/b12-local-requirement-acceptance-matrix-20261021.json): doce requisitos contrastados;60funcionales actuales+1diagnóstico serial+41testigos reutilizados=102únicos entre varios cortes, no una ejecución única102PASS. Los41casos conservan fuentes y fixtures idénticas; el único producto existente cambiado desde ese corte es el snapshot, que no importan esos testigos. Documentación original de cada corte conserva sus límites y negativos. Cierre local por acta14; inventario universal y preparación real de apertura continúan sin acreditarse.
