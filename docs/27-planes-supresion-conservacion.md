# Decisiones por finalidad de supresión y conservación

REQ-CR09-ERASURE-PLAN-01. Estado: preparación local verificada. Preparación de decisiones; ejecución, bloqueo legal y resolución del derecho todavía pendientes. Vincula docs/26 y contratos/10.

## Distinciones jurídicas y técnicas

El [RGPD, artículo17](https://eur-lex.europa.eu/legal-content/ES-EN/ALL/?uri=CELEX%3A32016R0679) contempla supresión y excepciones; el motivo de conservación requiere análisis del caso, no una FK protegida. [LOPDGDD, artículo32](https://www.boe.es/buscar/act.php?id=BOE-A-2018-16673#a32) exige, cuando proceda, reservar los datos e impedir su tratamiento y visualización salvo los fines/autoridades previstos, con destrucción tras el plazo aplicable. Consulta2026-10-04 de fuentes primarias; BOE indica actualización consolidada27/12/2025 y carácter informativo del consolidado. Registrar un plan no acredita aplicación correcta de esas normas.

Conservar, limitar una publicación y bloquear legalmente datos son operaciones distintas. Ni el inventario ni este plan impiden por sí solos acceso a originales, búsquedas internas, derivados o tratamiento por workers. No utilizar una decisión retain como autorización genérica para seguir tratando datos.

El campo review_on es una fecha de nueva revisión, no plazo de prescripción, fecha de borrado o duración legal aprobada. Retain/review exigen fecha posterior a hoy y dentro de365 días: límite operativo para que una propuesta no quede sin revisión programada durante más de un año. No se deriva ese límite de la ley. No activa purga automática ni amplía plazos de respuesta de la solicitud. El plazo definitivo y los disparadores de destrucción deben definirse por finalidad y fundamento antes de ejecutar conservación real.

## Artefacto y validación

ErasurePlan vincula ErasureInventory y RightsAction con relaciones protegidas, digest de fuente, decisiones cifradas y fecha de revisión más temprana indexada. La acción registra clave global UUID, actor, versión y firma del inventario/decisiones. Es inmutable por acción: replay exacto devuelve el mismo plan; cambiar los campos con la misma clave falla. No añade aprobación jurídica, ejecución o estado resolved. execution_ready=false persiste en el documento cifrado.

Cada finalidad presente en el inventario debe aparecer exactamente una vez, sin finalidades ajenas ni omisiones. Campos:

| Campo | Validación |
| --- | --- |
| purpose | Identificador del inventario actual, una vez por finalidad |
| operation | erase, redact, retain o review; sin selección automática |
| scope | Datos incluidos/excluidos,20–1000 caracteres |
| basis | Fundamento del caso,20–1000 caracteres |
| reason | Motivo minimizado,20–2000 caracteres |
| review_on | Obligatorio para retain/review; futuro<=365d; vacío para erase/redact |

Las finalidades cubren perfil/publicación/archivos/cuenta/tokens-recuperación/preferencias/contacto/representación y evidencia/copia, según el inventario. Con recursos compartidos, erase global se rechaza para media, shared_contact_review y account con otras responsabilidades. Se puede documentar una redacción de ámbito o revisión pendiente; no se elimina por ello el archivo común, el teléfono de agencia ni los datos de otros modelos. La ejecución futura deberá revisar el alcance concreto y dependencias, no inferir una autorización de borrado de un texto libre.

Permisos review_rights_request+execute_rights_request, MFA actual, independencia, solicitud erase asignada/reviewing, lectura integral auditada de entrada y respuestas y proof erase vigente. El inventario debe pertenecer al mismo caso/persona/actor/versión/proof actual. Se compara su manifest cifrado con digest almacenado y un censo actual; drift bloquea incluso replay. Comprobación siempre simulada y rechazada en producción; no identidad real acreditada.

Locks Agency→Person→Listing→RightsRequest. Guardar plan no cambia estado/fechas/versión de solicitud, disponibilidad, consentimiento, favoritos, credenciales o archivos; no consume proof. La preparación no es un snapshot serializable de todos los recursos: la ejecución debe revalidar y bloquear fuentes con los demás procesos. Nuevas revisiones, cambio de teléfono, gestor, datos de cuenta o referencias compartidas invalidan la vinculación vigente cuando alteran el manifest.

## Contrato HTML y privacidad

GET/POST /{es|en}/moderation/rights/{caseUUID}/erasure-plan/{inventoryUUID}/, nombre erasure_plan. Enlace después de preparar inventario por POST. GET exige evidencia/inventario actuales y muestra formularios sin decisiones previas ni fundamentos guardados. POST usa key/version y formset decisions con management fields y las seis columnas anteriores. Máximo de formularios esperado por inventario y límite absoluto20; no se reservan miles de formularios con TOTAL_FORMS manipulado.

Éxito/replay200 con mensaje Plan registrado; ejecución pendiente. Formulario400, evidencia/fuente/clave/esquema/fecha/compartidos409, permiso/COI403, caso/inventario no correspondiente404; sesión MFA obsoleta puede302 a comprobación. POST CSRF, cabeceras y logs privados también en errores. Todos los campos POST marcados sensibles. El acuse anónimo no recibe plan/fundamentos, y un GET posterior no revela automáticamente el contenido de un POST anterior.

## Trabajo posterior necesario

Revisión independiente de decisiones y política jurídica, ampliación de dependencias/datos físicos y volúmenes, ejecutor local idempotente con bloqueo/revalidación, retirada/revocación, redacción o borrado por alcance, repositorio reservado/acceso separado para datos bloqueados, destrucción por plazo/disparador y revisión vencida, tombstones/restore/backups/destinatarios y respuesta/cierre con evidencia. No derivar de prepared que el derecho está atendido. CR09 y fases CR10→GS01→BF/BB→C siguen pendientes.

Resultados terminales de pruebas y Docker se registran en docs/18 y seguimiento docs/17.


## Evidencia local

Migration safety0035 aplicada. Inicial9 passed71.39s; ampliada11 passed79.94s en PostgreSQL/Chromium, sin skips y ejecuciones separadas. Incluyen decisiones mixtas, compartidos, invariancia, carrera y recorrido móvil; no ejecución de borrado ni suite común CR09. Detalles en docs/18.
