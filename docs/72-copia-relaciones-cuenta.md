# Relaciones de la propia cuenta con agencias

Estado: entrega técnica parcial verificada localmente con73 pruebas conjuntas y Docker. Complementa docs71 y la auditoría CR09. No amplía permisos de cuenta ni acredita acceso/portabilidad completos.

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

Implementación: helper agency_relationships común a perfil/cuenta; selecciona Agency.owner y AgencyMember.user por titular, con orden estable de propietario y membresías por agencia/PK. account_activity.agency_relationships y sección paginada inmutable participan en huella, inspección, decisiones y compilación completa.85178 terminal0:3 correctas48,07s PostgreSQL, /tmp/copy-agency-relationships.xml: perfil/cuenta, propiedad+membresía simultánea, inactiva, exclusión de roster/nombre, inyección rechazada, entrega privada y deriva de membresía. Ausencia de sujeto es comprobación solo de proyección, no nuevo procedimiento de enlace.16440 activa4 casos con21 membresías sintéticas/HTTP/paginación, /tmp/copy-agency-relationships-pages.xml/log; fuente congelada hasta terminal. Runtime todavía6a550ea sin esta ampliación.

16440 terminal0:4 correctas54,46s PostgreSQL, /tmp/copy-agency-relationships-pages.xml.21 relaciones sintéticas distribuidas en páginas10/10/1 cubiertas sin duplicados, POST HTTP privado y GET sin referencias. Fixtures prueban scope/paginación, no aceptación de21 agencias o workflows de invitación. Fuente descongelada; módulo de relaciones verificado parcialmente, móvil/regresión conjunta/Docker pendientes.

36307 terminal0:2 móviles ESEN correctas47,97s PostgreSQL/Chromium, /tmp/copy-agency-relationships-mobile.xml. Login/MFA→consultar agency_relationships→guardar confirmación inmutable→GET limpio→generar desde decisiones→descarga anónima con propiedad/membresía inactiva y sin nombre/roster; teléfono redactado conserva prueba anterior.28732 regresión conjunta activa /tmp/copy-agency-relationships-final-common.xml/log; fuente congelada hasta terminal.11747 build Docker en curso. Recuperar mismo handle, no reiniciar por timeout.

28732 terminal0:73 conjuntas correctas558,13s PostgreSQL/Chromium, XML contrastado73/0fallos/0errores/0skips;2 warnings históricos record_property/xunit2. Evidencia copia-relaciones-cuenta-regresion.json. Relaciones/contactos/aislamiento/compilación/generación/carreras/móvil/decisiones/inspección/exports/cuenta. Docker verificado con5 hashes app/worker/Beat iguales/UID10001/check/migraciones/health200. Fuente descongelada; entrega técnica parcial verificada, sin aceptación integral CR09 ni nueva CI acreditada. Siguiente docs73 información adicional/distinción de derechos, sin reducir cobertura integral/volumen/conservación/cierres restantes.
