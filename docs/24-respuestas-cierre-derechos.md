# Respuestas y cierre de derechos — CR-09

Estado: verificada localmente. No cierre general de CR-09 ni cumplimiento jurídico acreditado.

## Fundamento y límites

El artículo12.4 del RGPD exige explicar la no actuación e informar de reclamación ante una autoridad de control y tutela judicial. La mera disponibilidad de una respuesta en un acuse no demuestra que se haya comunicado efectivamente. Fuentes consultadas: [RGPD en EUR-Lex](https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX%3A32016R0679), [AEPD: derechos](https://www.aepd.es/en/rights-and-duties/know-your-rights). Esto orienta el mecanismo técnico; no sustituye revisión jurídica de motivos, políticas, destinatarios o comunicación.

## Tipos de respuesta

progress registra una respuesta de progreso y conserva la solicitud abierta. No equivale a estimación, denegación, resolución completa ni prórroga; no modifica fecha de recepción, objetivo o versión de evidencia y conserva las autorizaciones de copias existentes. Cambia únicamente la secuencia de respuestas.

representation_complete solo cierra una reclamación de representación ya retirada. Exige RightsWithdrawal vinculado a la misma solicitud y perfil, prueba sintética aprobada del alcance, sujeto/canal/gestor concordantes, consentimiento revocado y publicación retirada. La respuesta indica simulación, puesto que el adaptador actual no comprueba identidad real. Una solicitud recibida o una casilla no sustituyen la ejecución de retirada. Este cierre no suprime íntegramente datos ni resuelve otros tipos de derecho.

Acceso, portabilidad, rectificación, supresión, limitación y oposición requieren todavía evidencia de ejecución y revisión por tipo antes de ofrecer otros cierres. No se habilita una opción genérica cumplido o denegado que pueda ocultar desarrollo pendiente o una comprobación insuficiente de identidad.

## Permisos, evidencia y auditoría

POST /moderation/rights/{case}/response/ requiere review_rights_request, respond_rights_request, MFA actual, ausencia de conflicto, responsable asignado y consulta completa del expediente vigente. Cierre de representación añade execute_rights_request. Motivo interno20–2000 y respuesta50–4000 se cifran por separado; el acuse solo muestra la respuesta. Revisión humana de datos de terceros obligatoria, con rechazo adicional de contactos/URLs/números largos en el cuerpo. Los textos fijos de AEPD y tutela judicial se añaden fuera del texto del operador.

RightsRequest.response_version es independiente de version de evidencia. RightsResponse conserva key única global, actor, versiones, tipo y digest; la secuencia es única por solicitud. Replay exacto no duplica respuesta ni avisos; clave incompatible o versión/ciclo anterior produce409. Las operaciones toman locks canónicos y revalidan ámbito. Un cierre incrementa también la versión de evidencia, invalida scope y pasa a resolved.

RightsAccess registra response_version/response_before. Consulta POST del expediente muestra respuestas previas junto al resto de evidencia; GET oculta cuerpos. Todas las páginas50+cursor de la secuencia actual deben consultarse antes de emitir otra respuesta. Auditorías antiguas null no se reinterpretan como consulta de respuestas actuales. Una respuesta saliente no invalida una copia ya entregada, pero sí exige una nueva consulta de historial antes de responder de nuevo.

## Acuse y avisos

Acuse privado sin cuenta muestra respuestas paginadas50+cursor, sin motivos internos, revisores ni identidades ajenas. Incluye fecha/tipo y orientación de reclamación ante AEPD/tutela judicial. Se conserva no-store/noindex y minimización de logs.

Con contacto propio opcional del formulario original se crea RightsNotice cifrado transaccionalmente, uno por respuesta. El mensaje del aviso es fijo y mínimo: disponibilidad en el acuse; no copia cuerpo, motivo, datos de perfil, tipo del derecho o secreto del enlace. La outbox existente procesa también derechos con límites/reintentos/simulación; producción y backend disabled siguen inertes. SimulatedRightsNoticeDelivery es único por aviso. Operación y recuperación aplican review_rights_request y conflicto del caso; la constraint de NoticeRecovery exige exactamente una fuente entre report/complaint/rights. Simulación nunca acredita correo real, canal o conocimiento de la respuesta.

## Pendientes

Respuestas y ejecución completas por tipos restantes, denegación jurídicamente fundada con evidencia y posibilidad de nueva comprobación, comunicación real y confirmación de canal, avisos de ampliación/acuse, respuestas personalizadas ES/EN, conservación/supresión y revisión jurídica externa. Probar nueva purga de imágenes con registros sintéticos aislados; pruebas locales de funciones no equivalen a esos ensayos operativos. La regla de un mes y la ampliación mantienen los mecanismos previos; cerrar técnicamente no acredita cumplimiento del deber de comunicar.

## Evidencia local

26 pruebas afectadas pasan147.05s con PostgreSQL/Chromium sin skips; incluyen navegador móvil, concurrencia, copia conservada, cierre con retirada/procedencia real de las filas sintéticas, historial paginado y recuperación/función de outbox. Migraciones0031/0032 aplicadas. No revisión jurídica ni integración real de identidad/envío. Probe operativo aceptado separadamente:3 tipos de aviso, worker10.315s/Beat66.338s,6 simulaciones únicas, recursos temporales eliminados. Redis/worker/Beat reales; envío simulado. UUID de tareas y alcance en docs/18.
