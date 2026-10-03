# CR-06 — Moderación y publicación, interfaz v1 en curso

Esta entrega todavía no está cerrada. Implementados: envío y congelación, comprobación de organización simulada, cola de anuncios, aprobación/rechazo motivado y ficha/derivados públicos de revisión aprobada. Pendientes: revisión específica de transferencia, reclamaciones, resolución de coincidencias, clonación de revisiones sensibles y recorrido completo de agencia hasta publicación.

## Envío y estados privados

- POST `/{es|en}/draft/{revision}/submit/`: gestor vigente, sesión y aceptación legal actual, CSRF. Campos `edit_version` entero y `declaration` obligatorio sin premarcar. La declaración confirma veracidad y derechos de publicación de textos/fotos, versión `truth-and-rights-v1`.
- Éxito: 302 a `revision_status`; una Submission por revisión, actor/documento/version/instante persistidos. Reintento de revisión ya pendiente devuelve el mismo estado sin duplicar evidencias. No modifica la versión pública anterior.
- Entrada/requisitos inválidos: 400 con formulario y errores; ajeno: 404; sin sesión: 302 al acceso; GET al envío: 405. La edición, retirada, orden y cargas de fotos quedan bloqueadas después de enviar.
- GET `/{es|en}/draft/{revision}/status/`: gestor autorizado, estado persistido, respuesta privada no-store; ajeno 404 y visitante 302. No revela datos de cuentas coincidentes.

Wireframe: paso4, resumen → declaración explícita → enviar → estado pendiente al recargar. Error → explicación y enlace al borrador. Envío no equivale a aprobación ni publicación.

## Validación servidor

Revalida ubicación/catálogo activo, texto/contactos y tarifas con los mismos formularios del borrador. Exige al menos una foto y máximo ocho, derivados listos y comparación terminada. Una coincidencia no suspende la cuenta ni rechaza por sí sola el envío: la revisión humana resolverá conflictos antes de publicar.

Edad aprobada mediante última comprobación del sujeto/gestor vigente, consentimiento directo registrado con condiciones de publicación vigentes, teléfono verificado del gestor coincidente con la revisión y exposición aceptada. Cambiar condiciones exige renovar aceptación y autorización directa; una traducción antigua no elude la validación del envío. Renovar consentimiento del mismo gestor no obliga a crear otra persona.

Bloqueos transaccionales: gestor/persona → Listing → Revision; la fila Submission única protege reintentos. La revisión pendiente deja de ser editable en las operaciones existentes. La aprobación humana comprueba de nuevo estas condiciones y las coincidencias actuales.

Las agencias pendientes/fallidas quedan bloqueadas para envío; una comprobación simulada aprobada habilita las demás validaciones únicamente en desarrollo: MFA no acredita la organización. No sustituir este estado por una casilla ni considerar CR-06 completado con solo particular. Los simuladores de edad/contacto siguen identificados y no acreditan integraciones reales.

## Próxima integración requerida

Moderador con permiso explícito y MFA, sin autoaprobación; revisión de organización y transferencias; decisiones motivadas y canal de reclamación. Resolver coincidencias en ambas direcciones sin atribuir propiedad al primer uploader. Publicar exactamente la versión revisada, preservar la anterior ante cambios sensibles y retirar exposición al revocar representación o perder elegibilidad. Probar recorrido humano particular/agencia y recursos públicos/privados antes de cerrar CR-06.

## Comprobación de organizaciones

GET `/{es|en}/moderation/organizations/` lista hasta cien pendientes por antigüedad. GET/POST `/{es|en}/moderation/organizations/{agency}/` requiere permiso explícito `core.review_agency` y MFA vigente, incluso sin bandera is_staff. Titular y editor activo de la propia organización tienen acceso denegado para esta revisión. Cola y evidencias son privadas no-store. Logs ocultan identificadores de moderación.

Formulario: versión de revisión oculta, resultado passed/failed, motivo obligatorio máximo500 caracteres y referencia sintética máxima80. No adjuntar documentos ni introducir identificadores reales en desarrollo. POST inválido400, ajeno/sin permiso403, versión/estado cambiado409, éxito302 con decisión persistida. AgencyReview guarda revisor, resultado, motivo, referencia, procedimiento e instante; bloqueo de agencia impide dos decisiones simultáneas. El titular puede ver estado y motivo en su panel, no datos internos del revisor.

Procedimiento disponible: simulator-v1, explícito en interfaz. POST producción o proveedor distinto del simulador devuelve503 sin alterar estado: integración real pendiente. El envío impide usar simulator-v1 como comprobación real en producción. La decisión de organización no aprueba ninguno de sus anuncios ni las autorizaciones de personas. La decisión humana sobre anuncio está conectada; revisión específica de transferencias y reclamación permanecen pendientes antes de cerrar CR-06.

## Moderación de anuncios y exposición pública

- GET `/{es|en}/moderation/listings/`: cola privada de cien pendientes ordenados por envío.
- GET/POST `/{es|en}/moderation/listings/{revision}/`: permiso explícito `listings.review_listing`, MFA vigente. Sujeto, gestor independiente, titular y editor activo de agencia no revisan contenido propio. Formulario de versión, resultado approved/rejected y motivo obligatorio máximo1000; éxito302, entrada/estado cambiado400, permiso/conflicto403. Decisión persiste revisor, revisión exacta, motivo e instante. El gestor ve motivo en su estado privado.
- GET `/{es|en}/moderation/photos/{photo}/`: derivados privados para revisión pendiente/aprobada; mismo permiso/MFA, restricción de conflicto de interés, no-store. Nunca devuelve originales.
- GET `/{es|en}/listing/{listing}/`: ficha inicial de la versión aprobada exacta; no campos de cuenta, email de sujeto o evidencias privadas. Admite ES/EN con refinamiento pendiente CR-07.
- GET `/{es|en}/listing/{listing}/photo/{photo}/`: solo derivado aprobado y perteneciente a esa versión. Borradores, originales, otros anuncios o versiones retiradas no se exponen.

Aprobar vuelve a validar requisitos actuales del envío, incluyendo gestor/sujeto y condiciones, teléfono, catálogo y fotos. Coincidencias sin resolver bloquean aprobación en ambas direcciones, sin suspender cuentas ni asignar propiedad al primer uploader. Esta fase todavía no tiene operación de resolución: un conflicto permanece pendiente.

Bloqueos Agency → Person → Listing → Revision. Una segunda decisión sobre una revisión terminal falla sin crear evidencia ni renovar vigencia. La aprobación fija treinta días de vigencia. Rechazar una revisión no sustituye la versión aprobada anterior. El mecanismo para clonar esa versión y reenviar cambios sensibles sigue pendiente; no marcarlo probado por este primer recorrido.

La exposición revalida elegibilidad y caducidad en cada petición, tanto HTML como imágenes, y usa no-store mientras se prepara invalidación/optimización en B-B. Estados no públicos responden404. Revocar representación o transferir gestor pausa atómicamente anuncios publicados y borra disponible-ahora; las rutas públicas vuelven a comprobar gestor/autorización incluso si hubiera estado atrasado. Los recursos entregados antes de revocar no pueden recuperarse de una copia externa.

Wireframe moderador: cola → texto primario/alternativo, campos/catálogos, tarifas y fotos → aviso de coincidencias → resultado/motivo → decisión persistida. Visitante: UUID de anuncio → revisión aprobada y fotos autorizadas. Descubrimiento/filtros/SEO y botones de contacto completos continúan en CR-07.
