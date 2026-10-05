# Relaciones de la propia cuenta con agencias

Estado: especificación del siguiente bloque de copia; sin implementación ni aceptación todavía. Complementa docs71 y la auditoría CR09. No amplía permisos de cuenta ni acredita acceso/portabilidad completos.

## Proyección propuesta

Función común para la cuenta titular del perfil o el account_subject explícito. Sin sujeto enlazado, devuelve lista vacía; no sustituye al gestor, editor o actor del expediente.

account_activity.agency_relationships contendrá:

- Propiedad: Agency.owner=cuenta, referencia de agencia, relación owner y created_at.
- Membresía: AgencyMember.user=cuenta, referencia de agencia, relación member, active y created_at. Incluye membresías desactivadas todavía presentes.

Se omiten nombre de agencia y datos de propietario/otros miembros; la referencia identifica exclusivamente la relación ya registrada del sujeto. No se incorporan modelos, contactos compartidos, invitaciones por coincidencia de email, reseñas de agencia, motivos de moderación, evidencias o permisos internos. Propiedad y membresía simultáneas se describen como relaciones separadas, sin inventar historial ni fechas de baja inexistentes.

## Integración y validación requeridas

Nueva sección paginada agency_relationships, inmutable salvo futuras reglas explícitas. Entra en huella de fuente, revisión cifrada, recuperación auditada y compilación obligatoria por todas las páginas. Cambios en active o eliminación de relación invalidan las decisiones antiguas.

Pruebas PostgreSQL por cuenta/perfil: usuario propietario, miembro activo/inactivo, relación simultánea; exclusión de relaciones del gestor/agencia ajena; sujeto no enlazado sin sustitución; rechazo de inyección, deriva de membresía y generación privada con referencias propias. Añadir recorrido HTTP/móvil proporcional y regresión común afectada; Docker con hashes coincidentes. No marcar como historial completo las relaciones borradas por cascada.

La entrega de contactos propios debe terminar su regresión77370 antes de modificar fuente. Posteriormente ejecutar este bloque sin reducir los pendientes de inventario integral, información adicional, distinción acceso/portabilidad, grandes volúmenes, conservación/restauración, comunicaciones y cierres del contrato.
