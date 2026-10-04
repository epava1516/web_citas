# Alertas internas persistentes de denuncias urgentes

REQ-CR09-URGENT-ALERT-01. Implementación en curso, 2026-10-04. No aceptación de CR-09 ni acreditación de entrega externa.

Una denuncia con prioridad0 crea UrgentReportAlert en la misma transacción que Report y su acuse, incluso sin contacto. OneToOne/PROTECT evita duplicados por reintento y conserva el vínculo. La alerta guarda solo referencia, fecha y reconocimiento atribuido; nunca texto, email, identidad, fotos ni motivo descifrado. No significa que la denuncia sea cierta ni activa restricciones automáticamente.

La tarea reconcile_urgent_report_alerts toma hasta100 denuncias urgentes sin alerta por ejecución, con bloqueo PostgreSQL SKIP LOCKED/of self y get_or_create. Beat programa la conciliación cada60s. Recupera datos antiguos o una ausencia de alerta sin emitir mensajes, cambiar versiones o resolver casos. Su ejecución real por worker/Beat todavía debe verificarse; invocar la función en pytest no es esa evidencia.

GET/POST `/es|en/moderation/reports/urgent-alerts/` exige review_report, MFA vigente y ausencia de conflicto actual/histórico conforme a permitted. GET pagina50 alertas sin reconocimiento después de autorizar; no presenta totales de casos excluidos ni descifra evidencia. Sigue mostrando alertas no reconocidas aunque el expediente haya terminado. La exploración completa de permisos se optimizará/medirá en B-B.

POST solo recibe report_id(UUID) y CSRF. Bajo bloqueos Agency histórica/actual→Person→Report→Alert revalida conflicto/gestión y estampa el primer acknowledged_by/acknowledged_at. Repetición autorizada conserva el primer reconocimiento; un segundo actor no lo reemplaza. Transferencia de agencia durante espera409, falta de alerta409, ID inválido400, caso inexistente404, falta de permiso/COI403 (middleware puede redirigir a MFA). El par actor/fecha se protege por constraint PostgreSQL.

Reconocer atención no registra lectura de evidencia, no asigna responsable del expediente, no cambia Report.version/status, no resuelve ni levanta/restringe publicación. El expediente sigue en su cola habitual. Solo una consulta auditada habilita lectura y las decisiones siguen sus reglas independientes. Un click registrado no acredita comprensión humana o cumplimiento del procedimiento.

Cabeceras private/no-store/noindex y protección de logs heredadas de moderation/reports. Enlace desde cola de denuncias y navegación ES/EN/móvil. No destinatarios ni proveedores reales configurados; avisos externos, escalado y confirmación de recepción son pendientes operativos. La cola persistente y su reconocimiento son un canal interno real, no una simulación de correo entregado.

Pruebas iniciales17 passed86.30s y finales6 passed42.14s, PostgreSQL/Chromium sin skips, registradas separadamente en docs/18. Verificación runtime/worker/Beat y migración principal pendientes. Claude3/3; desarrollo local Codex.
