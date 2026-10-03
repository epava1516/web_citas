# CR-06 — Moderación y publicación, interfaz v1 en curso

Esta entrega todavía no está cerrada. Implementados: envío y congelación, comprobación de organización simulada, cola de anuncios, aprobación/rechazo motivado y ficha/derivados públicos de revisión aprobada. Implementadas también revisiones sensibles y resolución humana de coincidencias. Pendientes: revisión específica de transferencia, reclamaciones y recorrido completo de agencia hasta publicación.

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

Formulario: versión de revisión oculta, resultado passed/failed sin preseleccionar, motivo obligatorio máximo500 caracteres y referencia sintética máxima80. No adjuntar documentos ni introducir identificadores reales en desarrollo. POST inválido400, ajeno/sin permiso403, versión/estado cambiado409, éxito302 con decisión persistida. AgencyReview guarda revisor, resultado, motivo, referencia, procedimiento e instante; bloqueo de agencia impide dos decisiones simultáneas. El titular puede ver estado y motivo en su panel, no datos internos del revisor.

Procedimiento disponible: simulator-v1, explícito en interfaz. POST producción o proveedor distinto del simulador devuelve503 sin alterar estado: integración real pendiente. El envío impide usar simulator-v1 como comprobación real en producción. La decisión de organización no aprueba ninguno de sus anuncios ni las autorizaciones de personas. La decisión humana sobre anuncio está conectada; revisión específica de transferencias y reclamación permanecen pendientes antes de cerrar CR-06.

## Moderación de anuncios y exposición pública

- GET `/{es|en}/moderation/listings/`: cola privada de cien pendientes ordenados por envío.
- GET/POST `/{es|en}/moderation/listings/{revision}/`: permiso explícito `listings.review_listing`, MFA vigente. Sujeto, gestor independiente, titular y editor activo de agencia no revisan contenido propio. Formulario de versión, resultado approved/rejected seleccionado expresamente sin preseleccionar y motivo obligatorio máximo1000; éxito302, entrada/estado cambiado400, permiso/conflicto403. Decisión persiste revisor, revisión exacta, motivo e instante. El gestor ve motivo en su estado privado.
- GET `/{es|en}/moderation/photos/{photo}/`: derivados privados para revisión pendiente/aprobada; mismo permiso/MFA, restricción de conflicto de interés, no-store. Nunca devuelve originales.
- GET `/{es|en}/listing/{listing}/`: ficha inicial de la versión aprobada exacta; no campos de cuenta, email de sujeto o evidencias privadas. Admite ES/EN con refinamiento pendiente CR-07.
- GET `/{es|en}/listing/{listing}/photo/{photo}/`: solo derivado aprobado y perteneciente a esa versión. Borradores, originales, otros anuncios o versiones retiradas no se exponen.

Aprobar vuelve a validar requisitos actuales del envío, incluyendo gestor/sujeto y condiciones, teléfono, catálogo y fotos. Coincidencias sin resolver bloquean aprobación en ambas direcciones, sin suspender cuentas ni asignar propiedad al primer uploader. La resolución humana se registra con motivos/evidencia; un conflicto confirmado sigue bloqueando hasta corregir o revisar de nuevo la decisión.

Bloqueos Agency → Person → Listing → Revision. Una segunda decisión sobre una revisión terminal falla sin crear evidencia ni renovar vigencia. La aprobación fija treinta días de vigencia. Rechazar una revisión no sustituye la versión aprobada anterior. Los cambios sensibles crean otra revisión sin modificar esa versión, conforme al flujo descrito más abajo.

La exposición revalida elegibilidad y caducidad en cada petición, tanto HTML como imágenes, y usa no-store mientras se prepara invalidación/optimización en B-B. Estados no públicos responden404. Revocar representación o transferir gestor pausa atómicamente anuncios publicados y borra disponible-ahora; las rutas públicas vuelven a comprobar gestor/autorización incluso si hubiera estado atrasado. Los recursos entregados antes de revocar no pueden recuperarse de una copia externa.

Wireframe moderador: cola → texto primario/alternativo, campos/catálogos, tarifas y fotos → aviso de coincidencias → resultado/motivo → decisión persistida. Visitante: UUID de anuncio → revisión aprobada y fotos autorizadas. Descubrimiento/filtros/SEO y botones de contacto completos continúan en CR-07.

## Revisiones de cambios sensibles

POST listing_start reutiliza el borrador vigente o crea uno bajo bloqueo de persona/listing, máximo tres borradores/revisiones pendientes. Copia la versión aprobada del gestor vigente o una corrección pendiente/rechazada posterior; conserva source_revision. Así no pierde el contenido que el usuario necesita corregir. No copia una revisión de gestor obsoleto.

Datos/catálogos/tarifas se copian a filas propias; Photo nuevo comparte Blob privado sin copiar bytes. Aprobación de fotos, comparación, teléfono, exposición y aceptación de publicación se reinician. El worker vuelve a comparar globalmente, también SHA exacto de bytes reutilizados. Se requiere confirmar contacto y declaración de la nueva revisión. Tarifas cuyo ID pertenezca a otra revisión producen400 y no modifican la versión anterior.

Submission guarda approved_base, la versión pública vigente al enviar. Una aprobación pendiente no puede reemplazar una publicación que ya ha cambiado: error400, sin renovar vigencia ni mover la ficha atrás. Al aprobar, otras revisiones pendientes de esa publicación pasan a obsolete con motivo trazado, dejan de consumir cuota y muestran acción para crear un borrador actual. Crear otra revisión desde el estado actual permite resolverlo. El rechazo deja la ficha anterior expuesta si conserva elegibilidad; las fotos nuevas permanecen privadas hasta aprobarse.

Wireframe: estado privado → crear/retomar borrador revisado → campos precargados → contactos/derechos → fotos reutilizadas procesadas → declaración/envío → revisión humana → nueva versión pública. Durante todo el tramo pendiente se muestra la versión pública anterior.

## Resolución humana de coincidencias

- GET `/{es|en}/moderation/matches/`: cola de señales activas sin resolver o con conflicto confirmado.
- GET/POST `/{es|en}/moderation/matches/{id}/`: permiso listings.review_listing/MFA, sin conflicto de interés con ninguna de las dos personas. Formulario: versión, resultado explícito sin preseleccionar, motivo obligatorio máximo1000 y referencia de revisión máxima80. Éxito302; inválido/versión cambiada400; sin permiso o contenido propio403.
- GET `/{es|en}/moderation/matches/{id}/{photo|candidate}/image/`: derivados privados de las dos fotos ligadas a esa señal, incluso si una sigue en borrador, con iguales permisos/conflicto de interés; no-store. No originales ni fotos retiradas.

Resultados: false_positive solo para similitud visual, rechazado para bytes exactos; distinct_people requiere dos sujetos distintos y edad/autorización/contacto vigentes, más juicio humano registrado y referencia de ambas comprobaciones; conflict mantiene bloqueo y pausa anuncios publicados de las personas afectadas. Hashes y cuentas distintas no acreditan identidad ni propiedad: la revisión humana y las integraciones externas válidas siguen siendo necesarias.

MatchResolution mantiene historia de revisor, resultado, motivo, referencia e instante. Se bloquean agencias/personas/listings en orden estable y señales de la pareja; la versión impide dos resoluciones simultáneas. Una decisión cubre las señales recíprocas existentes de las mismas dos fotos; un cambio de fotos o nuevas coincidencias requieren revisión propia. Señal sha256 también se recupera al clonar sin depender de una nueva carga de bytes.

Un conflicto resuelto como conflict permanece bloqueante aunque tenga resolved_at; no confundir «decisión registrada» con «publicación permitida». Retirar una foto quita esa pareja de la cola activa, conservando evidencias conforme a retención pendiente B-B. Limpiar el conflicto no republica automáticamente un anuncio pausado. Las cuentas siguen activas; no existe suspensión automática por estas señales. Fotos nuevas y referencias retenidas no conceden prioridad al primer uploader.
