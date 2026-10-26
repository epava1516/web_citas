# N09H — diagnóstico confirmado y plan de corrección

Estado: reproducción original aceptada localmente, candidata de aplicación aún no integrada ni validada. Basef95b301 y [prerregistro442](442-n09-h-prerregistro-autoridad-evaluacion-destinatarios-20261026.md). N09 completo139IDs abierto,8/13bloques; alpha/noindex. F75/E38/G18 conservados sin repetir.

Original: run20261026-130546-cab2ce39,8casos4PASS4FAIL/0ERROR/SKIP,178,931sJUnit;1776huellas estables. Cuatro controles nativos válidos con efectos exactos y cuatro reproducciones: éxito, retorno del target privado y efectos persistidos tras revocar el permiso requerido durante espera real Inventory/Assessment. Auditoría independiente propia confirma4VALID_NATIVE_CONTROL+4CONFIRMED_NATIVE_PRIVATE_RETURN_EFFECT_AFTER_PERMISSION_REVOCATION. Limpieza de contenedores/redes/volúmenes/temporal verificada, Telegram terminalERROR y auditoríaPASS enviados, recibos comprobados. No se transforma el originalFAIL enPASS.

| Operación | Resultado original tras revocar | Target privado tras revocar | Tablas con efecto | Cuerpo QA, s |
| --- | --- | ---: | --- | ---: |
| assessment_inspect | success | 1 | safety.RightsAction | 16.236 |
| assessment_propose | success | 1 | safety.RightsAction, safety.RightsRectificationRecipientAssessment, safety.RightsRequest | 16.179 |
| review_inspect | success | 1 | safety.RightsAction | 19.131 |
| review_review | success | 1 | safety.RightsAction, safety.RightsRectificationRecipientReview, safety.RightsRequest | 16.479 |

Alcance observado: cuatro operaciones nativas de dos rutas. Los tiempos son cuerpo de caso con saga, espera inducida, snapshots y limpieza, no latencia normal ni mejora de rendimiento. Observador exacto reenvía unseal de inventario/decisiones sin registrar contenido, no exhaustividad de toda proyección interna. Se preservan roles de preparación no retirados; no hay evidencia HTTP, worker o proveedor real. Control de identidad usa adaptador sintético permitido en alpha.

Plan acotado: recipient_assessments.py y recipient_review.py capturan llamador y epochs originales antes de locks, revalidan todos los permisos actuales después de case/Inventory/Assessment y antes de privados/efectos/replay. rectification_authority.capture_authority añade sólo flag keywordrecipient_review=False que incorpora el cuarto permiso cuando se pide. Defaults review/respond existentes conservados, sin lock del operador. Propagar callback a execution_scope_matches/snapshot para las esperas internas ya protegibles por F, sin sustituir el llamador por autor/revisor de evidencia.

Invariantes: conservar permitted/asignación/versiones/lecturas/proof/source/latest/integridad, independencia del revisor, decisiones motivadas y firmas públicas. current puede recibir autoridad original del review para no adoptar nuevos epochs tras esperar. Replay legítimo devuelve el mismoPK sin nuevo efecto; autoridad actual obligatoria, sin exigir una prueba activa nueva sobre un estado histórico que no la admite. Revisar vigencia tras esperas internas en caminos activos sin convertir un cambio de garantía no medido en aceptación universal.

Validación adicional propuesta: conservar8diagnósticos íntegros y añadir8variantes en archivo separado: replay válido/revocado para propose/review, con esperaInventory o RightsRequest según flujo real, y cuatro casos de epochs/activo/MFA con roles precargados antes del cambio. Positivo replay mismoPK/ceroefectos; negativos denegación/privadoscero/dominioarchivosintactos. Versiones originales de argumentos separadas del case refrescado. Selección final y originales pertinentes se fijarán antes de congelar; ningún PASS supuesto.

Escritor aislado continúa con propiedad explícita sólo de3módulos, nuevo archivo variantes y reporte ignorado; el diagnóstico8ya congelado no se modifica. Root revisa cada diff, callers, Ruff, deltaAST/semántica, huellas, selección y resultado; complete no es aceptación. Sin migraciones, cambios de servicios/vistas/URLs/settings/proveedores ni escaneos activos. N09/139IDs/otrasramastardías/purgas/outbox/jobs y N10/N11/N15 siguen pendientes; N02restante al final, N12–N14condicionados.
