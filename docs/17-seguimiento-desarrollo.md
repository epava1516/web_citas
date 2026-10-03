# Seguimiento de ejecución del contrato

Actualizado: 2026-10-03. Contrato: [ejecución v1](16-contrato-ejecucion-desarrollo.md).

## Estado actual

- Fase: BASE parcial; CR-01 a CR-05 verificados localmente; implementación autorizada el 2026-10-03.
- Próximo paso: CR-06 (moderación, revisión inmutable y publicación).
- Frontend/backend: cuentas, documentos, agencias, asignaciones y MFA conectados; última regresión común85 pruebas; posteriores21 dirigidas pasan con PostgreSQL y Chromium; verificación y representación conectadas con simuladores explícitos.
- GS-01: no satisfecho; no separar trabajo todavía.
- Producción: pendiente; ningún gate verificado.

## Backlog ordenado

| ID | Entrega | Estado | Evidencia |
| --- | --- | --- | --- |
| BASE | ADR, Docker, estructura, contratos y fixtures iniciales | En curso | ADR-001, Compose, uv.lock; fixtures completos pendientes |
| CR-01 | Registro, acceso y aceptación legal | Verificado local | 16 tests PostgreSQL/Chromium ES/EN; docs/18 y contratos/01 |
| CR-02 | Roles, agencias y MFA | Verificado local | 21 pruebas comunes; agencia/MFA navegador, aislamiento, revocación y recuperación concurrente |
| CR-03 | Verificación y representación | Verificado local | 27 pruebas comunes; SSR, identidad/edad simuladas, autorización directa, transferencia y teléfono concurrente |
| CR-04 | Borrador, campos, geografía, tarifas/contactos | Verificado local | 35 pruebas comunes PostgreSQL/Chromium; wizard, geografía, consult y concurrencia |
| CR-05 | Fotos y coincidencias | Verificado local | 58 pruebas comunes y dos de logs; worker/Beat Docker real; contratos/05 y docs/18 |
| CR-06 | Moderación/publicación | En curso | Envío/congelación, organizaciones y aprobación/rechazo/ficha pública conectados; coincidencias y clonación conectadas; reclamación de rechazo conectada; transferencia móvil verificada; recorrido integrado de agencia con dos personas verificado; reclamación de gestor conectada; organización/coincidencias y cierre común/fixtures pendientes, contratos/06 |
| CR-07 | Búsqueda y fichas ES/EN | Pendiente | — |
| CR-08 | Favoritos y ciclo de vida | Pendiente | — |
| CR-09 | Denuncias, derechos y reclamaciones | Pendiente | — |
| CR-10 | Promociones preparadas sin venta real | Pendiente | — |
| GS-01 | Contratos estables y prueba de separación | Pendiente | — |
| B-F | Terminación frontend | Pendiente | — |
| B-B | Terminación backend/operación | Pendiente | — |
| C | Integración final, correcciones y entrega | Pendiente | — |

## Registro de una entrega

Para actualizar cada fila: commit/versión, fecha, requisitos cubiertos, flujos implementados, pruebas ejecutadas y resultado, diferencias entre simulado/real, incidencias abiertas y siguiente paso. «En curso» no significa verificado; no cerrar por un test aislado o por cantidad de código.

Estados: pendiente, en curso, corregir, verificado local o pendiente externo. Evidencias sin datos personales/secretos. Mantener actas y detalles en archivos específicos, enlazados desde aquí.

## Dependencias externas conocidas

Operador/dominio, contratos y credenciales reales, revisión jurídica/verificación, licencia/dataset geográfico, responsables humanos de moderación/incidentes y revisión independiente. No bloquean todo el desarrollo local: usar adaptadores/datos sintéticos y continuar tareas independientes. Sí condicionan producción.

Tarifas y pasarela condicionan futura venta, no lanzamiento gratuito. No realizar contrataciones ni envíos externos por el hecho de registrar estas tareas.

## Cierre

Existe scaffold inicial; no existe todavía entrega técnica completa. Separar su futura aceptación de preparación real de producción. No completar filas o gates sin evidencia.
