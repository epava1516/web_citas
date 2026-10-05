# Calendario operativo de restricciones por finalidad

Estado: entrega técnica local0071 verificada mediante49 pruebas conjuntas PostgreSQL/Chromium, móvilESEN, carreras reales, historial/paginación y Docker. Migración comprobada sobre base PostgreSQL aislada no vacía. No acepta CR09 completo ni preparación de producción. Depende de restricciones0069 y levantamiento0070; no autoriza tratamiento ni amplía conservación.

## Alcance y efectos

Cola privada global de medidas activas: revisión vencida, próximos siete días y todas; filtros de finalidad/modo. Datos mínimos de medida, expediente, responsable asignado y fecha. Excluir conflictos y ejecutor original; no exponer mensajes, teléfonos, favoritos, fundamentos o identidad del interesado. Acceso MFA/sesión vigentes y permiso dedicado de seguimiento. Conservar navegación desde expediente y enlace al procedimiento de levantamiento autorizado.

Paginación con recorrido acotado de candidatos y cursor estable, aplicando autorización antes de entregar cada fila. No cargar el ledger completo para filtrar conflictos en memoria. Un lote sin filas visibles todavía debe permitir avanzar al siguiente cursor si quedan candidatos.

Registrar seguimiento motivado y próxima revisión operativa, conservando fecha original, versión de medida, actor, fecha y motivo cifrado inmutable. Fecha futura limitada técnicamente para evitar abandono indefinido; el límite técnico no constituye plazo jurídico. Clave idempotente y versiones optimistas, conflicto409 sin cambios parciales. Consulta de motivos únicamente POST auditado; GET sin fundamentos. Historial paginado con auditoría previa, sin sobrescribir revisiones anteriores.

No cambiar active, mode, sujeto, favoritos, plazos del expediente, scope_status, pruebas, comunicaciones ni conservación. Una medida vencida continúa activa. El seguimiento no sustituye el recorrido de propuesta/comunicación/recepción/comprobación/levantamiento de docs60. Cambiar fecha/version debe invalidar propuestas que dependan de una fuente anterior; no permitir ejecutar una propuesta antigua tras seguimiento.

## Integridad y concurrencia

Locks canónicos de expediente/ámbito → medida; autoridad vigente y COI después de todas las esperas. Revalidar frente a cambio de gestor, permiso, sesión/MFA y levantamiento simultáneo. No admitir seguimiento nuevo de medida ya inactiva; replay exacto devuelve evento original sin otra mutación. Conservar trabajo/procedimientos anteriores. El calendario operativo no exige contratar un verificador externo ni simular entrega de avisos.

## Verificación y entrega

Recorrido frontend/backend ES/EN y móvil: cola → registro → recarga → historial auditado. PostgreSQL real para carreras de dos seguimientos, misma clave entre medidas, levantamiento durante espera y permisos revocados. Fechas inválidas/medida ajena/ejecutor original/no permiso/versiones antiguas sin cambios. Demostrar que favoritos siguen bloqueados y que los plazos/estado del expediente permanecen intactos.

Migración y Docker app/worker/Beat; regresión común con preparación/revisión/ejecución/levantamiento. Registrar evidencia por fuente y commit. No aceptar calendario por un cron vacío, fecha vencida o contador de tests. Tras este bloque siguen excepciones acotadas, otras finalidades, conservación histórica integral y demás pendientes de CR09.


85348 terminal0:2 servicio35,34s PostgreSQL sin fallos/errores/skips (/tmp/purpose-calendar-service.xml). Seguimiento fecha/version+replay snapshot inmutable, fecha original conservada, expediente/version/scope/plazos intactos, favoritos409 preservados e historial auditado; fechas hoy/>90/version obsoleta/ejecutor original rechazan sin eventos. Servicio parcial verificado, no recorrido frontend/backend ni calendario aceptado. Cola/pantallas/backfill/motivos históricos dañados/carreras/móvil/runtime0071/regresión con levantamiento pendientes.


7433 terminal0:4 calendario52,16s PostgreSQL sin fallos/errores/skips (/tmp/purpose-calendar-http.xml). Seguimiento HTTP200/recarga GET oculta motivo/private-no-store/consulta POST auditada muestra historial/permiso revocado403, snapshot de replay dañado ValidationError sin cambio ni evento extra; casos de servicio/version/fecha/independencia previos pasan.52199 check/makemigrations terminal0/no cambios, Ruff/diff limpios. No móvil ni cola global ni runtime0071; calendario/CR09 abiertos.


69751 terminal0:1 seleccionada28,96s PostgreSQL,5 deselected por -k (no skips). Primer lote100 excluidas entrega cero filas visibles y continuación cifrada; segundo lote muestra solo medida autorizada, sin siguiente cursor. Cambio de filtro400/permiso revocado403, sin persistir autorizaciones del cursor. Fixture de101 medidas prueba paginación/acceso, no creación de101 workflows. Cinco comunes anteriores56,59s y esta ejecución separadas; no sumar como suite común. Carreras/móvil/runtime0071 y regresión con levantamiento pendientes.


14896 terminal0:4 carreras52,25s PostgreSQL sin fallos/errores/skips (/tmp/purpose-calendar-races.xml). Dos conexiones bloqueadas observadas: misma key un evento/replay; keys distintas un ganador/conflicto/version2; permiso revocado ambas denegadas; inactive concurrente ambas denegadas sin evento/fecha/version nuevos. En todos los escenarios caso/version/scope/plazos/favoritos preservados. Inactive es fixture de estado concurrente, no levanta medida por procedimiento ni acredita carrera integrada con release. Clave entre medidas/carrera real release/móvil/runtime0071/regresión conjunta siguen pendientes. Ruff/diff limpios.


74395 terminal1:2 móvil fallidas46,91s. Tras consulta auditada, page.reload conserva historial porque recarga POST/replay, no GET; la prueba asumía GET incorrectamente. Sin alterar regla servidor ni quitar persistencia: comprobar método de reloadPOST/resultado idempotente y luego page.goto URLGET oculta motivo. Conteo final2 eventos exige que reload no duplique seguimiento/consulta. Nueva batería móvil en verificación.


99384 terminal0:2 móvilESEN47,02s PostgreSQL/Chromium sin fallos/errores/skips (/tmp/purpose-calendar-mobile-final.xml). Login/MFA→cola→seguimiento→reload→consulta auditada→reloadPOST observado/idempotente→GET explícito oculta motivos/viewport390. Dos eventos finales (un seguimiento/una consulta), restricción activa/versión2/fecha original, caso/scope/plazos/sesión/favoritos preservados. Primera expectativa de reloadGET corregida, no cambiar regla de autorización ni ocultar fallo inicial. Carrera integrada release/clave entre medidas/historial amplio/runtime0071/regresión conjunta todavía pendientes; CR09 abierto.


24174 terminal0:7 carreras71,30s PostgreSQL sin fallos/errores/skips (/tmp/purpose-calendar-scope-races.xml). Casos de replay/version/permiso/inactive y dos órdenes release real/seguimiento pasan; cambio de referencia de expediente durante espera observada denegado con medida/version intactas y sin evento. Destino/cambioFK sintéticos prueban binding/COI, no flujo de traslado. Ruff/diff limpios. Clave entre medidas, historial amplio, runtime0071 y regresión conjunta pendientes; CR09 abierto y CI ccb78bd todavía in_progress confirmado.


74460 terminal0:1 seleccionada28,28s PostgreSQL,7 deselected (no skips). Misma key en dos medidas bajo bloqueo observado deja un evento/versión2 y medida perdedora versión1, ambas activas; segunda fila sintética solo fixture de key/version. Historial amplio y key entre medidas completados, iniciar regresión común calendario/levantamiento/ejecución antes de runtime/commit; no sumar baterías anteriores.


33017 terminal0:49 comunes416,82s PostgreSQL/Chromium sin fallos/errores/skips; evidencia calendario-restricciones-regresion.json. Build69732/migrate75632/recreate40639/runtime11948 terminal0:0071 aplicada,10 hashes host/app/worker/Beat iguales, UID10001/check/migrate--check/providersdisabled/health200. Probe35548 falló por case_version omitida en fixture histórico antes de comprobar0071; corregida,29927 terminal0:base aislada PostgreSQL no vacía0070→0071 conserva fecha original/review_on/active/version1; base temporal eliminada/ausencia verificada. Evidencias runtime/migracion en docs/evidencias. Entrega calendario local pendiente commit/push; CR09 íntegro/otras finalidades/excepciones/conservación integral/acceso/comunicaciones finales pendientes. Estimación orientativa anterior70% CR09/50%contrato no recalculada, sin fórmula.
