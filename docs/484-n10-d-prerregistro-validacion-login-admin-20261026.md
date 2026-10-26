# N10D — prerregistro de candidata de login Admin

Candidata preparada tras [diagnóstico483](483-n10-d-diagnostico-y-plan-login-admin-20261026.md), todavía sin ejecución ni aceptación. Original20261026-220301-837183f9 conserva1PASS/1FAIL59,198sQA/1794huellas. Base8589acd, N10abierto77/9de13, alpha/noindex.

Un cambio de aplicación: apps/core/admin.py registra bind_admin_login_epoch con senderUser, dispatch_uid estable y guardia POST/namespaceadmin/url_namelogin. Copia user.session_version admitido después de la sesión nativa, sin recargarUser ni otorgar MFA. Las guardas de Group y su helper son ASTidénticas aHEAD; AccountGate, cuentas, MFA, vendor, settings/modelos/migraciones no cambian. Revisiones Django/seguridad y diferencial acotadas, historia y alternativas en483; propuesta nativa no equivale a aceptación.

## Selección y criterios anteriores a la ejecución

Dos archivos explícitos, diez casos seriales:

| Casos | Cantidad | Oráculo requerido |
| --- | ---: | --- |
| test_admin_login_epoch.py original |2| Byteidénticos al diagnóstico: epoch0/1, password+CSRF nativos, sesión preservada y MFAno concedido al llegar a challenge |
| test_native_admin_password_then_totp ES/EN |2| Loginversion1, GETindex redirigeMFA, códigoTOTP real con CSRF, consumo de contador exacto, rotación de Session y accesoAdmin200 posterior |
| test_native_admin_login_rejects_invalid_admission |3| Contraseña errónea/nonstaff200 y CSRF403; cero filas/sesiones/epochs/MFA o archivos cambiados |
| test_revocation_after_real_password_check_is_not_adopted |1| Se reenvía passwordcheck real y después se incrementa epochDB1→2 por intervención sintética; sesión conserva admitido1, siguienteAccountGate la elimina y devuelve al login |
| test_admin_epoch_receiver_does_not_bind_other_login_flows |2| Observer de señal real ve ausencia de bindingAdmin para force_login/signinpropio. Force_login con epochausente sigue cerrado; signin enlaza por su código y llega a MFA |

Todos usan datos propios sintéticos y Client con CSRF real donde hay POSTHTTP. No passwords/códigos/cookies/IDs ni SQLvalores en propiedades. Los observers reenvían comportamiento original y se retiran al terminar; no simulación de autenticación o MFA. La interposición de epoch es orden controlado, no una nueva espera SQL.

Cada fase compara todos los modelos/through y ocho archivos. Login admite sólo last_login y una Sessionpropia; TOTP admite sólo mfa_last_counter exacto y rotación de esa Session; rechazos son sin efectos; la intervenciónDB de epoch se enumera aparte. Se valida actor/versión/ausenciaMFA antes y sesión/MFA vigentes después de la ceremonia. No se excluye una tabla completa ni se crea una sesión al inspeccionar un logout.

## Ejecución y aceptación

Runneroficialfocused, un workerpytest, PG17/Redis7.4 propios, parsernativo disponible, timeout900s. Sin build/carga/servicios normales/proveedor ni conexionesMCP. Antes: grafofocal con ASTdeapp+instrumentonuevo y semántica483/484, documentos e instrumentos/congelacióncompleta/vendor y IDs de imágenes cacheadas. Capturar IDsruntime de los contenedores vinculados al PID/start_ticks del runner.

Exigir10PASSsinFAIL/ERROR/SKIP, todos los efectos exactos y controles nativos, fuentes antes/durante/después iguales, oráculos/limpieza/Telegram terminal. Auditoría root del XML/propiedades y archivos originales, sin convertir propuesta/Ruff/grafo en QA. Conservar el negativo original incluso si pasa candidata. QA no es latencia ni mejora causal; tabla anterior/actual separa comportamiento, no speedup.

No repetir16casosGroup ni56GET ni procedimientos ya verificados por esta adición si se mantiene AST de Group y sus consumidores; N11 conserva regresión integrada. Reexaminar cualquier retorno antes de autorizarlo: la pareja idéntica37ccaaa/ae33175 de481 precede al fix y no lo incluye. No se fabrican imágenes ni ejecución de switch. N11/N15pendientes, N02residualend por usuario y N12–N14condicionados; objetivo/contrato activos.
