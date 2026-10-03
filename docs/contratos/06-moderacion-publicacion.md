# CR-06 — Moderación y publicación, interfaz v1 en curso

Esta entrega todavía no está cerrada. Implementado: envío de particular a revisión y congelación de la revisión. Pendientes: comprobación de organización/transferencia, cola humana, decisiones y reclamaciones, resolución de coincidencias, clonación de revisiones sensibles, ficha pública y derivados públicos autorizados. No existe aún una operación que publique anuncios.

## Envío y estados privados

- POST `/{es|en}/draft/{revision}/submit/`: gestor vigente, sesión y aceptación legal actual, CSRF. Campos `edit_version` entero y `declaration` obligatorio sin premarcar. La declaración confirma veracidad y derechos de publicación de textos/fotos, versión `truth-and-rights-v1`.
- Éxito: 302 a `revision_status`; una Submission por revisión, actor/documento/version/instante persistidos. Reintento de revisión ya pendiente devuelve el mismo estado sin duplicar evidencias. No modifica la versión pública anterior.
- Entrada/requisitos inválidos: 400 con formulario y errores; ajeno: 404; sin sesión: 302 al acceso; GET al envío: 405. La edición, retirada, orden y cargas de fotos quedan bloqueadas después de enviar.
- GET `/{es|en}/draft/{revision}/status/`: gestor autorizado, estado persistido, respuesta privada no-store; ajeno 404 y visitante 302. No revela datos de cuentas coincidentes.

Wireframe: paso4, resumen → declaración explícita → enviar → estado pendiente al recargar. Error → explicación y enlace al borrador. Envío no equivale a aprobación ni publicación.

## Validación servidor

Revalida ubicación/catálogo activo, texto/contactos y tarifas con los mismos formularios del borrador. Exige al menos una foto y máximo ocho, derivados listos y comparación terminada. Una coincidencia no suspende la cuenta ni rechaza por sí sola el envío: la revisión humana resolverá conflictos antes de publicar.

Edad aprobada mediante última comprobación del sujeto/gestor vigente, consentimiento directo registrado con condiciones de publicación vigentes, teléfono verificado del gestor coincidente con la revisión y exposición aceptada. Cambiar condiciones exige renovar aceptación y autorización directa; una traducción antigua no elude la validación del envío. Renovar consentimiento del mismo gestor no obliga a crear otra persona.

Bloqueos transaccionales: gestor/persona → Listing → Revision; la fila Submission única protege reintentos. La revisión pendiente deja de ser editable en las operaciones existentes. Todavía falta la aprobación que compruebe de nuevo todas estas condiciones y las coincidencias actuales.

Las agencias quedan temporalmente bloqueadas para envío con mensaje de comprobación pendiente hasta conectar su revisión: MFA no acredita la organización. No sustituir este estado por una casilla ni considerar CR-06 completado con solo particular. Los simuladores de edad/contacto siguen identificados y no acreditan integraciones reales.

## Próxima integración requerida

Moderador con permiso explícito y MFA, sin autoaprobación; revisión de organización y transferencias; decisiones motivadas y canal de reclamación. Resolver coincidencias en ambas direcciones sin atribuir propiedad al primer uploader. Publicar exactamente la versión revisada, preservar la anterior ante cambios sensibles y retirar exposición al revocar representación o perder elegibilidad. Probar recorrido humano particular/agencia y recursos públicos/privados antes de cerrar CR-06.
