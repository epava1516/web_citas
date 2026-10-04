# Registro explícito de recepción de respuestas de derechos

REQ-CR09-RESPONSE-RECEIPT-01, 2026-10-04. Prerrequisito técnico para comunicar medidas revisadas; no cierre de derechos ni levantamiento de cautela.

RightsResponseAcknowledgement(safety0039) liga una respuesta inmutable mediante OneToOne/PROTECT a fecha y huella HMAC del canal privado. No añade identidad declarada, IP, email, texto de respuesta ni consentimiento. Una consulta GET, el envío a outbox o un aviso simulado nunca crean este registro.

POST `/es|en/safety/rights/{case_id}/{secret}/response/{response_id}/acknowledge/` exige CSRF, secreto43/HMAC y acuse no caducado, respuesta del mismo expediente y `received=yes` explícito. Bloqueo de expediente y get_or_create serializan concurrencia y preservan fecha inicial en reintentos. GET405, falta de confirmación400, secreto/caso/respuesta inexistente o caducado404. Cabeceras/logs privados heredados de safety. No login obligatorio; el secreto da acceso al canal, no demuestra identidad de la persona.

En cada respuesta paginada del acuse se ofrece la confirmación con texto ES/EN que distingue recepción de conformidad. Tras POST redirige al acuse y muestra fecha registrada; una recarga no repite ni modifica reconocimiento. No obliga a confirmar para consultar o descargar; no supone renuncia a reclamaciones.

No modifica RightsRequest.status/version/response_version/fechas/scope, comprobaciones, copias, outbox, responsable ni cautelas. No se marca aviso como entregado: el reconocimiento web y la entrega del proveedor son hechos distintos. Un tercero que posea el secreto puede usar el canal; no tratar esto como autenticación adicional ni verificación jurídica completa.

## Continuación del levantamiento revisado

El levantamiento local de PrivacyPublicationHold está implementado y verificado en [docs39](39-levantamiento-cautelas-privacidad.md), con alcance limitado a publicación. El contrato de continuación exige permiso independiente, ausencia de COI, revisor distinto del que aplicó la medida, caso/gestor/sujeto actuales, lectura completa y comprobación vigente. Preparar una propuesta motivada y respuesta previa específica ligada a esa propuesta; el presente reconocimiento genérico no habilita levantamiento. Solo el reconocimiento de esa respuesta vigente permitirá avanzar en el recorrido local; las alternativas de notificación/procedimiento reales son gates externos.

La ejecución se liga a la propuesta, prueba y comunicación actuales con UUID/replay, revisión de cambios intercalados y auditoría. Debe desactivar únicamente esa cautela, invalidar formularios/tareas anteriores y conservar publicación pausada/retirada; nunca republicar automáticamente ni cerrar todo el derecho por retirar una medida sobre publicación. Mantener otras cautelas/restricciones y conservación justificada. Cambio de alcance/identidad/gestor/prueba o nueva aportación obliga a nueva revisión.

Final16 passed102.56s PostgreSQL/Chromium sin skips, registrado en docs/18. No ensayo de proveedor ni aceptación CR09. Claude3/3; Codex continúa localmente.


Docker recepción de respuestas: app/worker/Beat reconstruidos/recreados, safety0039 aplicada en PostgreSQL principal; app confirma UID10001/rights y notice backends disabled/healthCaddy200. Hash rights_responses.py host/contenedor04ea08c81f471e9e43021b3dc7748c30e89d14d1459a12fc3ca29d4438053280 coincide. Sin cambios funcionales de tareas/schedule, no repetir ensayo de worker por esta operación HTTP. Levantamiento propuesto/notificado y revisado todavía pendiente; CR09/contrato/producción no completos.
