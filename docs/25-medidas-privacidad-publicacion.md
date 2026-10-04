# Medidas de privacidad sobre publicación

Estado: operación verificada localmente; CR-09 continúa abierto. Datos sintéticos y comprobación de identidad mediante adaptador de desarrollo; no acreditan identidad real ni cumplimiento jurídico. Requisito REQ-CR09-PRIVACY-PUBLICATION-01.

## Finalidad y límites

La medida cautelar retira la exposición pública de un perfil y evita su republicación mientras se revisa una solicitud de rectificación, oposición o limitación. Es una medida sobre la finalidad de publicación, no ejecución completa del derecho de limitación ni supresión. Conserva el origen, las pruebas y la solicitud abierta. No considera resuelto un derecho por pausar un anuncio.

La [AEPD](https://www.aepd.es/derechos-y-deberes/conoce-tus-derechos/derecho-la-limitacion-del-tratamiento) identifica supuestos de suspensión por exactitud u oposición pendiente y de conservación ante tratamiento ilícito o necesidad de reclamaciones. Referencia normativa: [RGPD, artículos 18, 19 y 21](https://eur-lex.europa.eu/legal-content/ES-EN/ALL/?uri=CELEX%3A32016R0679). Fuentes consultadas el 2026-10-04; el acceso monolingüe de EUR-Lex devolvió comprobación de navegador, pero el bilingüe permitió verificar los artículos 18, 19 y 21. Clasificar un supuesto técnico no demuestra que concurra el fundamento jurídico.

Siguen pendientes para ejecutar y cerrar el derecho completo: inventario de finalidades/bases, límites sobre carga, modificación, generación de derivados, coincidencias y demás tratamiento; almacenamiento y usos permitidos bajo conservación; destinatarios y comunicaciones; levantamiento revisado con información previa cuando proceda; resolución motivada y comunicación acreditada. La medida actual no impide esos otros tratamientos. No confundirla con bloqueo de datos de la legislación española.

## Operación y evidencia

PrivacyPublicationHold pertenece a Person, conserva RightsAction, RightsProof y snapshots del sujeto/versión del gestor, fundamento y estado/versión de publicación anteriores. Relaciones protegidas evitan borrar esa evidencia por cascada. No caduca ni se levanta automáticamente; trasladar el perfil o cambiar el gestor no elimina la medida. No se atribuye titularidad de fotografías al solicitante.

El revisor necesita review_rights_request y execute_rights_request, MFA, independencia respecto del solicitante y gestores/sujetos históricos y actuales, asignación, estado reviewing y lectura auditada de todas las páginas de entrada y respuestas emitidas en sus versiones actuales. El proof aprobado debe corresponder al tipo del derecho, persona, sujeto, canal, gestor, versión y plazo vigentes. El único adaptador disponible sigue siendo simulación no habilitada en producción.

Fundamentos técnicos: accuracy para exactitud; preservation para conservación solicitada; claims para reclamaciones; objection_pending para oposición en revisión. Rectify admite únicamente accuracy; object únicamente objection_pending. Restriction permite seleccionar el supuesto tras revisión. Motivo interno cifrado, 20–2000 caracteres, sin mostrarse en acuse público.

Transacción y locks: ámbito de agencia → Person → Listing → RightsRequest, compartidos con publicación y revisión. UUID de acción global con firma de los campos; replay exacto devuelve la misma medida, otra utilización de la clave falla. Una medida por solicitud; las medidas de distintas solicitudes pueden coexistir sin liberarse mutuamente.

Published pasa a paused; los otros estados se conservan. Se vacía available_until y aumenta lifecycle_version, invalidando acciones antiguas. Se incrementa la versión de la solicitud y se consume su autorización de ámbito, sin cerrar el expediente, prorrogar fechas ni enviar automáticamente una respuesta. La respuesta de progreso sigue siendo una operación independiente.

validate_submission comprueba cualquier medida activa de Person antes de validar identidad, condiciones y contenido. La utilizan envío, aprobación, exposición pública y acciones de ciclo de vida. Incluso forzar status=published no habilita ficha, fotografías públicas, resultados o renovación. El anuncio de otra persona de la misma agencia no recibe la medida.

## Contrato HTML

GET/POST /{es|en}/moderation/rights/{caseUUID}/publication-hold/, nombre privacy_publication_hold. GET no ejecuta acciones. POST exige CSRF y campos key UUID, version entero positivo, ground del catálogo y reason 20–2000. Éxito/replay:302 a consulta; formulario inválido:400; estado/versión/lectura/evidencia/clave incompatible:409; permiso/conflicto de interés:403; sesión MFA ausente u obsoleta:302 a comprobación MFA por middleware (o403 si alcanza la guarda de vista); solicitud inexistente:404. Cabeceras y logs privados comunes, incluidos errores tempranos.

Tipos de solicitud no compatibles devuelven409 y no muestran el enlace. Una medida ya registrada se muestra con fecha, sin ofrecer otro formulario. La pantalla explica la conservación y que la solicitud permanece abierta. No muestra datos del solicitante ni motivo interno. El acuse no recibe automáticamente una respuesta o una afirmación de cumplimiento; debe emitirse una comunicación motivada independiente.

## Verificación y pendientes

Resultados terminales en docs/18 y seguimiento docs/17: inicial10 passed64.09s; ampliada1 failed/24 passed144.17s por expectativa MFA corregida; caso afectado final1 passed15.96s. PostgreSQL y Chromium reales, datos sintéticos; ejecuciones separadas, no suite común25. La migración safety0033 crea la medida e índice Person/active. La aceptación de esta operación no cierra CR-09: siguen pendientes los demás tratamientos, derechos, retención y regresión común, seguidos de CR-10 y las fases posteriores del contrato.
