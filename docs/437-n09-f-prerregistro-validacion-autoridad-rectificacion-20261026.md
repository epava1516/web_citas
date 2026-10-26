# N09F — prerregistro de validación de autoridad de rectificación

Estado: candidata integrada para validación, sin aceptación runtime. Base master `6d4c288`. El [diagnóstico436](436-n09-f-diagnostico-y-plan-correccion-rectificacion-20261026.md) conserva veinte casos originales: diez controles válidos y diez fallos de revocación,236,664sJUnit. Alpha/noindex; N09 completo139IDs abierto,8/13bloques aceptados. N09E38PASS retenidos.

## Candidata y revisión

Siete fuentes: seis módulos de rectificación y nuevo rectification_authority.py. Helper explícito captura pk/session/MFA originales antes de los bloqueos y comprueba User fresco activo/no suprimido, MFA, epochs, permisos y ámbito. No bloquea al operador. Base review+execute; review_rectification para revisión/inventario; respond adicional para notify/execute, conservado al delegar en current y en los callbacks de fuente.

Guardas después de los bloqueos canónicos, Proposal/Review/Notification/Upload/Blob y antes de efectos/replays. Callback explícito después de User objetivo antes de la proyección de cuenta y después de bloqueos internos de fuente. Upload/Blob/Rate/Photo se bloquean por identificadores ordenados y se materializan después de comprobar autoridad; se conserva su orden y representación. PhoneClaim se prebloquea por PK justo en el punto previo a binding. Account.apply revalida tras EmailConfirmation; execute revalida tras contacts.claim antes de guardar Person. No se han eliminado checks de proof, auditoría, independencia, asignación, versiones o idempotencia.

La revisión root de diferencias, callers y roles precede a esta selección. Se eliminó un check consecutivo redundante de execute sin una nueva espera entre ambos. Original del escritor y matriz de revisión conservados en artifacts/recorridos-n09-f-20261026. Complete del escritor no equivale a aceptación. Los veinte diagnósticos originales mantienen íntegramente sus527líneas/SHA2358c9317c343c55378d1dea6596777c612c844a6122443ff581bab032c83a0d. Once variantes nuevas tienen RuffPASS y recibo Telegram confirmado; lint de candidata informó PASS y su recibo se comprobará antes de congelar.

## Selección fija prevista:75casos

| Selección | Casos previstos |
| --- | --- |
| Archivo completo test_rectification_authority_wait.py, íntegro |20|
| Archivo completo test_rectification_authority_variants.py |11|
| test_rights_rectification.py: doce funciones originales no móviles |18|
| test_rectification_account.py: cuatro funciones originales no móviles |4|
| test_rectification_uploads.py: siete funciones originales |8|
| test_rectification_review.py: independent_audited_review y reviewed_correction_communication |10|
| test_account_only_rectification.py: ambas funciones originales |2|
| test_account_only_execution.py: account_recipient_flow |2|

Los28selectores originales exactos y sus44casos por listas AST quedan en proposed-original-validation.json; se incluirán literalmente en la selección congelada del runner. El conteo estático no sustituye colección ni resultado runtime. Los dos nombres abreviados de review corresponden a test_independent_audited_review_needs_fresh_source_and_preserves_publication y test_reviewed_correction_communication_requires_new_proof_and_is_idempotent; account_recipient_flow corresponde a test_account_recipient_flow_does_not_require_or_modify_owned_agency_profiles.

Los veinte casos originales repiten exactamente sus esperas reales/control/retirada. Negativos exigen denegación, cero retornos privados después de revocar, cero intentos de delay, cero bytes y snapshots de dominio/archivos íntegros. Controles conservan los efectos propios, versiones, filas y contenido esperados. Para source_photo se requiere HTTP403 y respuesta cerrada, frente al HTTP200/9558bytes del diagnóstico. Los restantes servicios no acreditan transporte HTTP.

Once regresiones nuevas: preview con instancia admitida original ante cambio persistido de session_version, mfa_version, is_active o mfa_enabled; siete replays tras primera operación legítima y retirada de permiso, conservando su clave/payload/version originales (propose/upload/discard/review/notify/execute/recipients). Se exigen PermissionDenied, cero helpers privados/callbacks y snapshots íntegros. Estas once variantes no simulan ni acreditan espera PostgreSQL y no son once fallos baseline adicionales.

Los44originales contrastan forma y digest de fuente, fuente de cuenta/orden User→medios, drift de Blob, subida/procesamiento/descarte/replay/proof expiry, campos y límites de edición, revisión/aprobación/rechazo/comunicación/acuse/ejecución y flujo de cuenta sin perfil con/sin email. Sus pruebas de reloj interpuesto no pasan a ser evidencia de revocación real del operador. No se repiten N09E ni baterías generales válidas.

## Gates y decisión

Antes del runner: Ruff, revisión propia y de alcance, AST de ocho fuentes nuevas/modificadas (siete de app y once variantes), semántica selectiva436/437/17, validación del manifiesto y congelación. Preservar el grafo anterior y el inventario111. No reconstrucción completa N15 ni semántica exhaustiva por denominarlo delta.

Runner oficial focused serial, PostgreSQL/Redis propios, parser nativo `/tmp/web-modelos-librdb-v2.4.0`, workers1, timeout3600. Selección exacta de dos archivos nuevos y28selectores originales. Durante la ejecución no modificar app/tests/docs/seguimiento/worklog/grafo congelados. Auditar los75casos, cada control/negativo, fuentes antes/durante/después, cleanup independiente y recibos Telegram antes de aceptar.

No prometer mejora temporal: estas guardas añaden consultas. Tabla final antes/después distinguirá bloqueo/procesamiento/efecto y duración QA del caso;75frente20no es comparación de rendimiento de app. Conservar todos los fallos originales y de instrumento si apareciesen, corregir sólo la causa probada sin rebajar criterios.

Mantener pendientes con disposición propia rectification_final.evidence, cuenta sin perfil y ramas tardías no observadas en las20esperas, replays/epochs fuera de las once variantes, purgas/outbox/jobs y conciliación139IDs. Proteger una rama por código no acredita automáticamente su reproducción concurrente. N02restante al final/N10N11N15pendientes/N12–14condicionados; objetivo completo activo.
