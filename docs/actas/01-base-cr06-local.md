# Acta BASE y CR-06 — aceptación técnica local

Fecha UTC: 2026-10-03T20:32:22.624889+00:00
Código: aeb9d80; ajuste de roles del fixture: de81dbc. No es acta GS-01 ni preparación de producción.

## BASE

ADR-001, uv.lock, Django/PostgreSQL/Redis/Celery, Docker/Compose no-root, configuración de ejemplo, migraciones/bootstrap, salud, SSR ES/EN y CI versionada. Wireframes/rutas/formularios/actores/estados en contratos00…06. Muestra completa y comandos en contratos07/README: particular, agencia con dos sujetos/editor, moderador, visitante, pending/published/withdrawn y patrones geométricos propios. Instalación realizada en volumen privado Docker; credenciales0600 y fuera Git/imagen, sin impresión de secretos.

## CR-06

Envío valida datos, contactos, geografía, tarifas, fotos, autorización/edad y documento actual; congela revisión y declaración. Revisión de organización y transferencia independientes y versionadas. Moderación con permiso/MFA, conflicto de interés, evidencia/fotos privadas, decisión motivada y revalidación al aprobar. Ficha/derivados corresponden a la revisión aprobada exacta, no al borrador nuevo.

Clonación/corrección conserva la versión pública, congela base al enviar, evita reemplazo por una aprobación obsoleta y protege campos/contactos/fotos de gestores anteriores. Cuotas vigentes y altas/traslados a agencias serializados. SHA/huellas/recortes y coincidencias entre cuentas/agencias; resolución humana en ambos sentidos sin prioridad automática al primer usuario ni suspensión por similitud.

Reclamaciones de rechazo de anuncio/gestor/agencia y restricción de foto conectadas con estado privado, otro revisor/MFA, historia y control de versión/repetición/concurrencia. Aviso de foto no revela contraparte ni comentarios/evidencia internos. Reabrir foto mantiene comparación pendiente y no republica. Reabrir organización exige una comprobación nueva.

## Evidencia

- Regresión común sobre aeb9d80:135 passed en299.22s, PostgreSQL/Chromium, sin skips.
- Ajuste exclusivo del rol de particular en seed_demo, de81dbc:3 passed en12.44s; código web/servicios de publicación sin cambios respecto de la regresión común.
- Ruff/check/migraciones/diff-check limpios; Docker sin migraciones pendientes. app/worker/beat reconstruidos y activos con UID10001; PostgreSQL/Redis healthy.
- Chromium contra Caddy/Gunicorn Docker: dos fichas publicadas con derivados reales, pending/withdrawn404; acceso de propietario por contraseña/TOTP y panel; credenciales privadas404. El primer probe buscó el nombre de agencia en cuenta en vez de entrar al panel; navegación corregida y probe completo superado.
- Worker Docker real, sin eager: clonación y foto nueva listas/comparadas en2.803s; revisión queda draft, fotos no aprobadas y derivado público404; publicación previa sigue200 y mantiene approved_revision.

Fuente detallada: docs/18-evidencias-desarrollo.md y pruebas tests/. CI remoto no ejecutado; workflow versionado y comandos correspondientes comprobados localmente. El caso retirado es preparación de fixture, no aceptación de ciclo de vida CR-08.

## Matriz resumida de acceso vigente

| Operación | Actor permitido |
| --- | --- |
| Ficha/derivado público | Cualquiera, solo revisión aprobada vigente/elegible |
| Cuenta/aceptaciones/MFA | Titular de cuenta |
| Equipo/cuota/asignación de agencia | Propietario con MFA |
| Borrador/contacto/foto privada | Gestor vigente: particular, propietario o editor activo asignado |
| Edad/autorización/revocación/transferencia | Sujeto de la persona; invitación ligada a email/gestor |
| Aviso/reclamación de foto o gestor | Sujeto o gestor vigente, sin revelar contraparte |
| Reclamación de agencia | Propietario |
| Moderación de anuncio/gestor/foto | Permiso review_listing y MFA, sin conflicto de interés |
| Comprobación/reclamación de agencia | Permiso review_agency y MFA, sin conflicto de interés |
| Resolución de reclamación | Revisor distinto del autor; exclusiones específicas en contrato06 |

GET no sustituye autorizaciones POST; CSRF y comprobación servidor/transacciones siguen obligatorios. Permisos/estados completos por operación en contratos01…06.

## Límites y continuación

BASE y CR-06 verificados localmente. Próximo CR-07 descubrimiento/filtros/fichas ES/EN. GS-01 no satisfecho y áreas no separadas. Edad/contacto/comprobación organizativa simulados; textos/geografía de muestra. No producción, proveedor real, verificación jurídica, precios/cobros ni difusión externa acreditados. Dependencias externas y fases CR-07…CR-10/B-F/B-B/C permanecen pendientes según contrato16. No se reduce el objetivo completo.
