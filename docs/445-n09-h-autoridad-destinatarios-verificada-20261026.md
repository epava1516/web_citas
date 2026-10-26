# N09H — autoridad de evaluación y revisión verificada localmente

Estado: aceptado localmente en cuatro operaciones y fronteras seleccionadas de dos rutas; N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex, datos sintéticos. Basef95b301; [prerregistro442](442-n09-h-prerregistro-autoridad-evaluacion-destinatarios-20261026.md), [original443](443-n09-h-diagnostico-y-plan-autoridad-destinatarios-20261026.md), [candidata444](444-n09-h-prerregistro-validacion-autoridad-destinatarios-20261026.md).

Original: run20261026-130546-cab2ce39,8casos4PASS4FAIL/0ERROR/SKIP,178,931sJUnit/1776huellasestables/limpiezaTelegram comprobados. Cuatro controles legítimos y cuatro éxitos con retorno del target privado/efectos tras revocar el permiso durante espera PostgreSQL. Fallos originales conservados; no se convierten enPASS.

Candidata: run20261026-132335-26da47b4,22PASS/0FAIL/ERROR/SKIP,374,255sJUnit/1779huellasestables. Runner oficialfocused serial, parser nativo, PostgreSQL/Redis propios. Auditoría independiente propiaPASS:4VALID_NATIVE_CONTROL y4DENIED_BEFORE_SELECTED_PRIVATE_BOUNDARY_NO_REPRODUCTION, más8variantes y6originales verificados. Limpieza de contenedores/redes/volúmenes/temporal, archivos y recibosTelegram terminalPASS/auditoríaPASS comprobados. No pruebas activas pendientes de esta selección.

Cambio: tres módulos recipient_assessments.py,recipient_review.py,rectification_authority.py. Captura PK/epochs originales y todos los roles requeridos al entrar, User nuevo tras locks canónicos y de Inventory/Assessment, antes de privados/efectos y al retornar replay. current comparte captura original; callbacks se propagan por scope/snapshot. Flagkeywordrecipient_review=False mantiene los defaults anteriores; AST restante del helperidéntico tras retirar sólo ese keyword y su rama. Firmas de cuatro servicios, permission público, validadores y stamps conservados; sin lock de operador, cambios de esquema, vistas, settings, servicios o proveedores.

## Antes y después

| Operación tras revocar | Antes | Después | QA antes, s | QA después, s |
| --- | --- | --- | ---: | ---: |
| assessment_inspect | éxito,1retorno privado y efectos | PermissionDenied,0retornos y efectos | 16.236 | 15.543 |
| assessment_propose | éxito,1retorno privado y efectos | PermissionDenied,0retornos y efectos | 16.179 | 17.703 |
| review_inspect | éxito,1retorno privado y efectos | PermissionDenied,0retornos y efectos | 19.131 | 16.368 |
| review_review | éxito,1retorno privado y efectos | PermissionDenied,0retornos y efectos | 16.479 | 18.020 |

Tiempos: cuerpo de cada caso con saga nativa, espera inducida, snapshots y limpieza; no latencia de aplicación ni mejora causal de rendimiento. Original8total frente a candidata22total no es comparación homogénea. Rendimiento normal de app antes/después: no medido por esta corrección, mejora atribuible no evaluable. Consultas frescas adicionales tienen coste; no se presenta su seguridad como optimización temporal.

Oráculos: controles con efectos exactos previstos. Inspecciones añaden sólo Action; propuesta añade Assessment/Action y actualiza Request; revisión añade Review/Action y actualiza Request, versión+1/scopeunverified sin mutar perfil/publicación. Los cuatro negativos deniegan antes de entrada/retorno del target privado, con dominio/through/archivos/estado mínimo intactos, excluyendo sólo la concesión retirada. Espera PostgreSQL real con Lock/blocking_pids/holder distinto y permiso retirado confirmado por User nuevo antes de liberar.

Variantes: cuatro replays sobre propuestas/revisiones completadas, válido/revocado por operación. Proposal esperaInventory;review esperaRightsRequestcanónico. Válidos devuelven mismoPK sin efecto ni descifrado activo, negativos deniegan; versión original del argumento conservada pese a refresh. Cuatro staleactors de sesión/MFA/inactivo/MFAdesactivado precargan roles antes de cambio persistido; snapshot posterior a la mutación intencionada y todos los grants incluidos. Denegación/privadoscero/dominioarchivosintactos; no afirman espera concurrente.

Originales: dos cierres finales de cuenta pendingTrue/False, dos formularios/denegación ESEN y dos validadores de evidencia/recepción. Se seleccionaron por dependencias modificadas; F75/E38/G18completos se conservan sin repetir. Diagnóstico original8 SHA6a0999b8ba9c55161f57e71bb13a43271598d65b806b871a44d1912bb17cadb9 idéntico antes/después; variantes en archivo distinto.

Revisión: propia Django/acceso/diferencial sobre tres módulos, callers e historia831bbbcf/02210aa/98c66a6/helper28a02db, informe persistido en artifacts/recorridos-n09-h-20261026/DIFFERENTIAL_REVIEW_CANDIDATE.md. RuffPASS. Sin hallazgo adicional confirmado en este diff; no certificación global. Se conserva el fallo de configuración inicial del verificador del grafo: listaba2docspara3cambios; corregido a tres, preservación ajenaPASS sin repetirAST/runtime.

Grafo: antes del original4422078fuentes SHA95579ae0d45537c65b05fe24cd8fcc0cc06f42eda0711909d729bcdeea3013b1; antes de candidata4442081fuentes20246nodos84384relaciones980comunidades SHAbeac34f70ddcb52157ebfc3a2e1febc78f3add68821127dcea0588142bcc4c3d. Cierre semántico445/17selectivo root, no reconstrucciónN15 ni semántica exhaustiva;111 preservado.

Límites: native/exactunsealseleccionado, sin exhaustividad de proyecciones privadas ni nueva evidencia HTTP/worker/proveedor real. Reconsultas de prueba activa después de snapshot se conservan, sin acreditar un diagnósticoHdedicado de caducidad durante espera no medido aquí. A–Gcorrecciones locales retenidas; Hcuatrooperaciones/dosrutas y ocho variantes, sin sumar casos/IDs/bloques como causas independientes. Otros139IDs/ramastardías/purgas/outbox/jobs siguen abiertos; N02restante al final/N10N11N15pendientes/N12–N14condicionados.15laterales preservados fuera de la entrega propia.
