# Auditoría de alcance CR-09 antes de aceptación

Fecha: 2026-10-04. Referencia funcional: 14/15/16 y contratos/10. Código base de revisión: `35b1f53`, migraciones safety hasta0019. **CR-09 sigue en curso; GS-01 no satisfecho.** Esta matriz separa avances verificables de requisitos aún sin entrega completa. No sustituye las evidencias dirigidas de docs/18 ni una regresión común.

## Matriz de cobertura y siguiente trabajo

| Requisito | Implementación/evidencia actual | Trabajo pendiente antes de cerrar el flujo |
| --- | --- | --- |
| Denuncia pública general/formal sin cuenta, ES/EN y móvil | safety/forms/views, Report; test_reports, navegador/CSRF/acuse/HMAC/cifrado | Regresión común y recorrido Docker del estado final |
| Datos del denunciante privados y consultas auditadas | ReportAccess, permisos/MFA/COI y snapshots históricos; test_report_inspection | Versionar evidencia cuando se incorporen nuevas aportaciones/reclamaciones; audit legacy no equivale a lectura actual |
| Prioridad urgente y responsable efectivo | Cola prioriza menores/explotación/no consentimiento, asignación/recuperación versionada | Alertas internas duraderas/worker/adaptador explícito, destinatarios reales como gate externo; una cola ordenada no prueba recepción humana |
| Decisión restrictiva/desestimación motivada | ReportAction, Restriction y guardas comunes; test_report_decisions/assignment/linking | Motivo público minimizado independiente del privado, revisión de alcance/cierre y aviso a afectados sin identidad del denunciante |
| Restricción quita búsqueda/ficha/foto y bloquea publicación obsoleta | publicly_visible→validate_submission; tests de decisiones/restricciones/ciclo de vida | Caché/CDN/storage externos y conciliación transversal B-B/C; nuevo recurso no debe reabrir publicación automáticamente |
| Revisión independiente de restricción | uphold/lift, permiso separado, independencia y nueva consulta; test_restriction_review/history | Entrada pública de reclamación contra decisión para denunciante/representado sin cuenta, y acceso del anunciante por su propio permiso; notificación/trazabilidad completas |
| Acuse y comunicación de decisiones | ReportNotice transaccional/idempotente cifrado, simulator separado; test_report_notices | Worker/Beat/outbox, estados de reintento/fallo/entrega y aviso minimizado; no considerar fila simulated como correo real |
| Derechos separados de denuncia y de recurso | RightsRequest tipos acceso/rectificar/suprimir/portabilidad/restricción/oposición/representación; test_rights_intake/priority/assignment | Implementar ejecución/respuestas y estados finales para los tipos restantes; aceptar entrada no satisface el derecho |
| Aclaraciones y lectura de versión vigente | RightsMessage, RightsAccess.case_version/paginación; test_rights_messages/evidence_version/questions | Histórico completo de preguntas y respuesta personalizada minimizada; caducidad del acuse no debe cerrar automáticamente un caso abierto |
| Comprobación proporcionada por canal propio y alcance de una persona | RightsProof/Event, segundo revisor y proof ligado a caso/persona/gestor/canal/version; test_rights_verification | Adaptador/procedimiento real aprobado como gate externo. Localmente completar estados/respuestas y probar todos los consumidores; simulator nunca acredita identidad real |
| Retirada de representación sin cuenta de agencia | withdraw atómico, revoca consentimiento/contacto y retira exposición; test_rights_withdrawal/agency isolation | Resolución motivada/revisión/avisos; no confundir retirada con transferencia de propiedad o supresión integral |
| Copia privada de acceso/portabilidad | Preview y redacción humana, JSON cifrado/caducidad/descarga POST autorizada; test_rights_exports | Copia aún parcial: fotos y datos de cuenta dentro del alcance, información adicional de acceso y redacción de terceros; distinguir acceso de portabilidad y no prometer datos ajenos de agencia |
| Retención de copias transitorias | RightsExport purged_at/SKIP LOCKED; tests retention y Redis/worker/Beat real | Es vaciado de contenido de copia en DB activa; no supresión del perfil, WAL/backups/réplicas ni inventario completo |
| Supresión/retención/reconciliación por dependencias | Retirada de exposición y purga anterior únicamente | Inventario/plan por finalidad, ejecución local idempotente de cuenta/perfil/fotos/huellas/favoritos/evidencias, conservación restringida motivada, tareas pendientes y restore-tombstones; plazos jurídicos reales como gate externo |
| Un mes y posible ampliación motivada comunicada | initial_due inmutable, RightsExtension1–2meses/objetivo efectivo/alerta de aviso no confirmado; test_rights_extensions/priority | Entrega confirmada del aviso antes del objetivo original, calendario/procedimiento definitivo, respuestas y cierre; acuse disponible no demuestra comunicación real |
| Aislamiento de agencias/modelos y COI | Locks canónicos, gestor versionado, sujeto/equipo histórico y editor revocado | Conservar estas garantías en nuevos recursos/avisos/copia completa/supresión; identidad anónima no establecida requiere recusación humana |
| Aceptación común y Docker | Última común aceptada pertenece a CR-08; pruebas CR-09 dirigidas y Docker purga hasta0018 | Común35b1f53 terminó285 passed/1 failed969.51s; corregir/sincronizar el caso de navegador y verificar cobertura afectada; suite del CR-09 final, migración/docker/worker/navegador y acta final con limitaciones explícitas |

## Orden de continuación

1. Regresión35b1f53 terminada285 passed/1 failed969.51s: reload de Chromium sin página activa; reproducción original aislada1 passed15.84s. Espera observable del resultado antes de recarga incorporada; repetir cobertura de moderación/restricciones y mantener pendiente la nueva común completa. Nunca duplicar pytest sobre la misma BD.
2. Recurso público, evidencia versionada y aviso de decisión minimizado; probar la persona sin cuenta, denunciante y gestor sin cruzar datos.
3. Respuestas motivadas/estados de cierre, outbox y entrega simulada por worker con trazabilidad de fallos, sin correo ni terceros reales.
4. Completar copia y ejecución de derechos/retención local por alcance, con navegador e idempotencia; separar política jurídica externa de mecanismos técnicos pendientes.
5. Regresión/Docker del flujo completo y acta de aceptación CR-09; continuar CR-10 y todo el contrato. No separar B-F/B-B antes de GS-01.

Este orden puede ajustarse ante fallos o dependencias demostradas; no elimina filas pendientes. La instalación/consulta Graphify en docs/19 verifica herramientas y relaciones estructurales, no completa esta matriz. Claude3/3 consumidas, incluida incidencia de etiquetado automático; el resto continúa localmente.

Verificación afectada del punto1 finalizada:20 passed95.28s, PostgreSQL/Chromium sin skips. Nueva regresión común completa pendiente; continuar punto2 sin afirmar cierre.
