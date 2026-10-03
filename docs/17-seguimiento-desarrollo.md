# Seguimiento de ejecución del contrato

Actualizado: 2026-10-03. Contrato: [ejecución v1](16-contrato-ejecucion-desarrollo.md).

## Estado actual

- Fase: BASE y CR-01 a CR-08 verificados localmente; implementación autorizada el 2026-10-03.
- Próximo paso: CR-09 (denuncias, derechos y reclamación sin cuenta).
- Frontend/backend: cuentas, documentos, agencias, asignaciones y MFA conectados; última regresión común166 pruebas pasan con PostgreSQL y Chromium (450.45s, sin skips), dos límites finales14.47s; Docker/worker/Beat de CR-08 verificados; verificación y representación conectadas con simuladores explícitos.
- GS-01: no satisfecho; no separar trabajo todavía.
- Producción: pendiente; ningún gate verificado.

## Backlog ordenado

| ID | Entrega | Estado | Evidencia |
| --- | --- | --- | --- |
| BASE | ADR, Docker, estructura, contratos y fixtures iniciales | Verificado local | ADR-001, Compose, uv.lock, seed_demo; acta01 |
| CR-01 | Registro, acceso y aceptación legal | Verificado local | 16 tests PostgreSQL/Chromium ES/EN; docs/18 y contratos/01 |
| CR-02 | Roles, agencias y MFA | Verificado local | 21 pruebas comunes; agencia/MFA navegador, aislamiento, revocación y recuperación concurrente |
| CR-03 | Verificación y representación | Verificado local | 27 pruebas comunes; SSR, identidad/edad simuladas, autorización directa, transferencia y teléfono concurrente |
| CR-04 | Borrador, campos, geografía, tarifas/contactos | Verificado local | 35 pruebas comunes PostgreSQL/Chromium; wizard, geografía, consult y concurrencia |
| CR-05 | Fotos y coincidencias | Verificado local | 58 pruebas comunes y dos de logs; worker/Beat Docker real; contratos/05 y docs/18 |
| CR-06 | Moderación/publicación | Verificado local | 135 comunes PostgreSQL/Chromium, reclamaciones/transferencias/agencia y Docker/worker; acta01 |
| CR-07 | Búsqueda y fichas ES/EN | Verificado local |149 comunes PostgreSQL/Chromium, pgFTS/paginación/geo/comprobaciones; Docker; acta02 |
| CR-08 | Favoritos y ciclo de vida | Verificado local |166 comunes+2 límites finales, PostgreSQL/Chromium, agencias y worker/Beat/Docker; acta03 |
| CR-09 | Denuncias, derechos y reclamaciones | En curso | Recepción/consulta auditada/asignación/enlace/restricción parcial verificados; avisos/revisión/derechos/exportación/supresión y cierre pendientes; recuperación de asignación verificada |
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

BASE y primeros ocho flujos están verificados localmente; todavía no existe entrega técnica completa. Separar su futura aceptación de preparación real de producción. No completar filas o gates sin evidencia.


CR-09 consulta privada auditada accepted local parcial: safety0002 aplicada, Report conserva gestor/agencia/sujeto de publicación y versión, ReportAccess registra responsable/motivo/fecha antes de entregar evidencia. GET oculta datos, POST válido los muestra solo en esa respuesta; permiso específico/MFA vigentes y exclusión de autor/sujeto/gestores/agencia original incluso editor revocado. Bloqueos Agency→Person→Report y revalidación; cambio intercalado exige409. Primer ensayo detectó2 fallos PostgreSQL por FOR UPDATE de joins opcionales; corregido con OF self,9 pruebas pasan42.47s. Ampliación13 passed23.70s. Última ampliación de MFA tuvo2 expectativas erróneas (middleware redirige a alta/desafío antes de la vista), corregidas conforme al flujo existente;18 finales PostgreSQL/Chromium/logs passed36.45s sin skips. Ruff/format/check/migraciones/diff-check limpios. Referencia manual sin perfil e identidad anónima requieren triage/recusación; auditoría/retención/seudonimización pendientes, no afirmar conflicto totalmente resuelto. Docker sigue CR-08. Próximo triage/asignación/decisiones/restricciones persistentes/avisos/revisión, derechos sin cuenta/exportación/supresión y cierre CR-09. GS-01/B-F/B-B/C y producción pendientes; Claude2/3.


CR-09 asignación/decisión/restricción accepted local parcial: safety0003 aplicada, Report.version/assigned_to, ReportAction key única/motivo cifrado y Restriction persistente. SSR ES/EN con versión/cabecera actual de publicación; asignarse→consultar evidencia auditada→restricción o desestimación motivada. Solo responsable, MFA/permisos/COI y head/gestor actuales; reintento exacto no duplica y conflictos409. Restricción limpia disponibilidad/invalida lifecycle y bloquea validador central (ficha/fotos/búsqueda, envío/aprobación, resume/renew/available), incluso con status forzado published; no suspende cuenta ni borra datos. Diez decisiones/consulta passed46.33s;24 decisiones/denuncias/ciclo de vida passed105.49s;13 finales decisiones/consulta passed65.29s, incluyendo móvil y concurrencia real PostgreSQL de dos moderadores y key idéntica entre casos (una acción/asignación, otra transacción íntegramente revertida). Límite final foto/búsqueda tras status forzado passed10.47s. Sin skips; no suite común completa CR-09 ni prueba de carga. Ruff/format/check/migraciones/diff-check limpios tras normalizar formato de migración generado. Próximo enlace manual/triage/reasignación/avisos/historia auditada/revisión independiente/levantamiento, derechos sin cuenta/exportación/supresión y cierre común/Docker CR-09. Docker todavía CR-08; GS-01/B-F/B-B/C y producción pendientes. Claude2/3.


CR-09 triage/enlace manual accepted local parcial: operación link y UUID destino en formulario SSR. Solo caso asignado/reviewing, versión vigente y evidencia consultada; enlaza revisión aprobada, conserva payload original y toma snapshots de aceptación/sujeto/gestor. Agencia actual/histórica→Person→Listing→Report y COI revalidado antes de escribir; propios/antiguo editor revocado403 con rollback íntegro. Destino desconocido/no aprobado/ya enlazado/versión obsoleta409; no fetch de URL ni restricción automática. Huella de link incorpora destino sin cambiar hashes de reintentos anteriores. Nueve iniciales linking/decisions passed43.06s;11 finales passed54.00s sin skips, incluyendo carrera real PostgreSQL de enlaces a destinos distintos y Chromium móvil desde caso genérico→asignación→consulta→link→restricción/ficha404. Ruff/format/check/migraciones/diff-check limpios; no migración nueva ni suite común/Docker CR-09. Recusación humana de identidad anónima, corrección/reasignación, avisos/historia/revisión independiente/levantamiento y derechos sin cuenta/exportación/supresión siguen pendientes. Claude2/3, Docker CR-08; GS-01/B-F/B-B/C y producción pendientes.


CR-09 recuperación de asignaciones accepted local parcial: safety0004 declara manage_report_assignment separado de review_report. Unassign exige ambos permisos/MFA/COI y reviewing/asignación activa; reason cifrado/key/version/historia, received sin responsable, sin consultar datos privados. Otro coordinador recupera caso tras pérdida de permiso del responsable, claim vuelve a asignar; autores no coordinan sus propios casos. Reintento antiguo no cancela nueva asignación; casos resueltos no se reabren ni se libera restricción. Ocho iniciales assignment/decisions passed42.26s;10 finales passed54.12s sin skips con Chromium móvil devolución/reclaim/consulta/link/restricción, autor403 y carrera real PostgreSQL unassign/restrict (solo una operación/version3, restricción ganadora persiste). Ruff/format/check/migraciones/diff-check limpios. No prueba de coordinador operativo real ni suite común/Docker CR-09. Próximo avisos/historia auditada/revisión independiente/levantamiento, derechos sin cuenta/exportación/supresión y cierre CR-09; GS-01/B-F/B-B/C y producción pendientes. Claude2/3, Docker CR-08.
