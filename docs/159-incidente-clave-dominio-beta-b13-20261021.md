# B13 — Revocación de la clave HMAC de dominio

Estado: revocación explícita de canales y revisión posterior verificadas localmente. B13 abierto7/18. Deriva de [OP005](12-operacion-seguridad.md), [separación151](151-clave-hmac-dominio-beta-b13-20261021.md) y [matriz155](155-matriz-vigente-b13-beta-20261021.md).

El pin151 conserva bindings cuando cambia la firma Django sin compromiso de ese valor. No es el procedimiento para una clave de dominio comprometida: no conservar canales comprometidos por comodidad. Los ensayos previos demostraban cambio efectivo de memo/reglas y modos heredados, pero faltaba combinar clave de dominio explícita, revocación del recibo y revisión auditada posterior del expediente original.

## Procedimiento local y alcance

1. Aislar ingreso/tareas/canales afectados y preservar evidencia mínima; determinar familias afectadas, no copiar claves a logs. Si el valor se usó antes como SECRET_KEY, retirar también su aceptación por fallbacks Django y aplicar revocación de sesiones/tokens según alcance. La prueba mantiene una firma Django independiente no comprometida; no acredita que una sesión afectada pueda conservarse.
2. Provisionar una nueva SAFETY_HMAC_KEY explícita y coordinar reinicio de todos los productores, lectores, workers y Beat que la usan. No mantener una lectura HMAC antigua ni devolver a SECRET_KEY heredada para reabrir el canal comprometido. No se declara hot reload de un despliegue real.
3. Verificar que los recibos anteriores fallan y el reenvío con nonce antiguo no reescribe ni reasigna el expediente; abrir nueva entrada con nonce y clave nuevos. Mantener el material original cifrado y sus huellas históricas. No rehash ni reescribir evidencia inmutable para aparentar continuidad.
4. El acceso del personal exige autoridad/MFA vigente y nueva finalidad auditada. Un acceso anterior no es una revisión nueva ni revalida decisiones/copies/exportaciones anteriores. Clasificar bindings derivados y revisar/reconstruir su autoridad antes de cualquier operación que dependa de ellos. No se promete migración transparente o recuperación automática de canales anónimos antiguos.
5. No retirar claves de cifrado por esta rotación HMAC. Mantener aislamiento de componentes no verificados; ledger usa claves propias y no recibe un nuevo checkpoint fabricado. Rollover de ledger, recuperación de claves perdidas, custodia/guardia y apertura real conservan sus límites separados. El ensayo no los convierte en PASS.

## Ensayo preparado

Cuatro casos PostgreSQL: denuncia/derechos × ausencia/presencia de fallback Django no afectado. Clave HMAC explícita e independiente desde el inicio; cifrado MFA/safety explícito. Crear expediente y un acceso auditado anterior, capturar todas las columnas y plaintext, rotar sólo SAFETY_HMAC_KEY y comprobar regla de publicación nueva,404 de recibos ES/EN,409 de replay sin rebind, nueva entrada200 y nueva lectura por personal con propósito/auditoría adicional. La fila original/ciphertext/plazos y el acceso anterior deben permanecer iguales.

La clave de dominio revocada no se incorpora a SECRET_KEY_FALLBACKS. La variante con fallback usa otra clave de firma no afectada: no es una recomendación de retener secretos comprometidos. No envíos externos ni prueba de identidad real.

Selección focal prevista21casos:4nuevos,9del proveedor de clave y8de modos de recibo anteriores. Cuatro workers, PostgreSQL/Redis propios y fuentes congeladas. Conservar resultado, omisiones/advertencias, limpieza/PIDs y Telegram terminal; no modificar producto para forzar verde. Si una operación posterior sigue bloqueada por un binding antiguo, documentarla como pendiente y no atribuirla a cobertura humana de B17.

## Resultado verificado

085523-2ef768af:21PASS/0FAIL/0ERROR/0SKIP, sin advertencias,4workers. [Auditoría terminal](evidencias/b13-domain-key-incident-terminal-audit-20261021.json): cuatro casos nuevos y diecisiete del proveedor/modos previos. Clave explícita nueva invalida recibos ES/EN y la versión de reglas; replay original409 sin rebind; entrada nueva200. Filas/ciphertext/plaintext/plazos y registro de acceso anterior conservados. GET de personal no revela el marcador privado; nuevo POST con propósito crea otro acceso auditado y permite leerlo. Clave revocada ausente de los fallbacks Django; sesión de personal de otra familia no afectada permanece válida.

726fuentes runtime iguales a la candidata de correo/retorno, freeze/fresh/limpieza/PIDs y Telegram terminal comprobados. No se modificó producto por esta comprobación. No se acredita migración de bindings, revalidación de todas las decisiones derivadas, rollover de ledger ni recuperación de claves perdidas. Operaciones que dependan de una autoridad antigua deben seguir bloqueadas hasta su revisión específica. B13 permanece pendiente de conciliación final.

Conciliación final posterior: [acta15](actas/15-beta-b13-aceptacion-local-20261021.md) acepta los ensayos/runbooks locales B13; no acepta migración transparente ni revalidación de decisiones derivadas antiguas por estos21casos.
