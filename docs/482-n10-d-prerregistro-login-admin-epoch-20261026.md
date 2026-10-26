# N10D — prerregistro de login nativo Admin y versión de sesión

Diagnóstico preparado, sin fallo confirmado ni cambio de aplicación. Base8589acd; pregunta identificada en [481](481-n10-c-admin-operacion-dispatch-verificados-20261026.md). N10 sigue abierto77IDs/9de13, alpha/noindex.

Corte previo consultado y contrastado:2137fuentes,21206nodos,86584relaciones,1032comunidades; SHA02c3ec59785b08445230da21bf641c5401ade82c51430276a40369b8b14ad750. Semántica selectiva terminalN10C; no reconstrucciónN15. Antes de congelar/ejecutar se incorpora al grafo el instrumento nuevo y este prerregistro.

## Pregunta y criterio anterior al resultado

AdminSite usa LoginView/AdminAuthenticationForm del framework. auth.login guarda los tres campos normales de autenticación y emite user_logged_in; no se encontró un receptor propio que enlace account_version. El signin propio sí enlaza esa versión. AccountGate sólo enlaza automáticamente una versión ausente cuando User.session_version es0; para una versión mayor cierra la sesión. Esta secuencia sugiere un fallo de disponibilidad del login Admin tras recuperación/revocación previa; todavía no es evidencia runtime.

Instrumento tests/test_admin_login_epoch.py, exactamente dos casos seriales con un actor staff nativo sintético, no superusuario, activo/verificado/MFA habilitado y documentos vigentes:

| Caso | Datos | Resultado requerido |
| --- | --- | --- |
| initial_epoch | session_version0 | GETlogin200, contraseña+CSRFPOST302 hacia Admin, GETindex302 hacia MFA; sesión preservada conaccount_version0 y MFAno concedido |
| revoked_epoch | session_version1, contraseña actual correcta | Misma secuencia, preservando sesión yaccount_version1; una revocación previa no debe bloquear futuras autenticaciones legítimas |

No force_login ni mock de authenticate/login. Client enforce_csrf_checks=True obtiene token real del GET y lo envía al POST. La verificación de contraseña es real; no se entra códigoTOTP todavía. El caso controla admisión a MFA, sin crédito de ceremonia MFA completa ni de acceso final a datos privados. No hay revocación concurrente nueva.

Se conserva una fotografía de todos los modelos, incluidas tablas intermedias, y ocho archivos de fixture. POST sólo puede actualizar last_login del actor admitido y crear su única fila Session, con las claves nativas de autenticación y sin mfa_version. GETindex sólo puede actualizar esa fila o, como observación negativa, eliminarla por el logout real. Los demás usuarios, sesiones, grants, dominio y archivos permanecen idénticos. No se omite una tabla completa; la sesión se consulta sin crear otra mediante Client.session después de un posible logout.

La propiedad n10d_native_admin_login_epoch registra statusHTTP, destinoMFA/login como booleanos, persistencia de sesión y versión admitida, efectos exactos y estado de archivos antes de las aserciones finales. No exporta usuario, contraseña, ID, tokenCSRF, cookies, clave/cuerpo de sesión, SQLvalores o datos de sujetos. Si falla version1 y el control0 pasa, conservar FAIL y resultados originales antes de diseñar una corrección; si ambos pasan, cerrar la pregunta sin parche especulativo.

## Ejecución y límites

Runner oficial focused, PostgreSQL17/Redis7.4 propios, un workerpytest, parser nativo disponible y timeout600s, sin build/carga/cambio de servicios existentes. Guardas de propiedad real de contenedor/puerto/usuario/base y exclusión producción/recovery. Fuentes completas, vendor/config/instrumentos/documento/grafo y IDs de imágenes congelados antes; observar contenedores vinculados al PID/start_ticks real del runner. Verificar estabilidad, limpieza de recursos/temporal y reciboTelegram terminal incluso si hay FAIL.

Revisión propia focal Django/seguridad y Ruff antes de ejecutar. Tiempos del caso son QA, no benchmark ni mejora de app. DosPASS serían el comportamiento esperado; el diagnóstico no presupone que la candidata actual los cumpla. Los dos casos quedan congelados byte a byte para cualquier candidata posterior. No relajar AccountGate, autoadoptar epochs o marcar MFA por completar login.

N10A16/N10B2/N10C2 y runbooks120PASS2SKIP originales se preservan, sin repetir campañas. Si una corrección cambia aplicación, reexaminar el retorno por equivalencia de fuentes del corte481; las imágenes726 no son destino actual autorizado. N11/N15pendientes, N02residualend por usuario y N12–N14condicionados. Contrato/objetivo activos.
