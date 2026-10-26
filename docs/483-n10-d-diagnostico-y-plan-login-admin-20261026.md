# N10D — diagnóstico y plan de corrección de login Admin

Diagnóstico original20261026-220301-837183f9: **1PASS/1FAIL,0ERROR/SKIP,59,198sJUnitQA/1794huellas estables**. [Prerregistro482](482-n10-d-prerregistro-login-admin-epoch-20261026.md). N10abierto77/9de13, alpha/noindex.

Ambos POST de contraseña/CSRF auténticos devolvieron302 con autenticación válida y una única Session propia. Ninguno guardó account_version ni concedió MFA. El control0 fue enlazado por la compatibilidad inicial del middleware y llegó a MFA con sesión conservada. Para version1, el GETindex eliminó exactamente esa Session y redirigió a Adminlogin; los demás modelos y ocho archivos permanecieron intactos. El FAIL queda conservado, no es fallo de fixture ni prueba de acceso indebido.

La auditoría root comparó XML/propiedades/efectos, fuentes completas y vendor/config/documento/grafo congelados, IDs de imágenes antes/durante, limpieza propia y reciboTelegramERROR. XML SHAffb1690b7fd409c88f4295cddc216c6221618dcfa045d48be06da87619a28d05. Instrumento originalSHA58e145185d18ef3d1f9e37290b7872d51385ca828a463fd055257e4131d48524, guardado byte a byte para la candidata. Los segundos son QA, no latencia de autenticación.

## Decisión de diseño anterior a la candidata

Root selecciona un receptor de user_logged_in exclusivamente para POST resuelto en namespaceadmin/url_namelogin y senderUser. La señal se emite después del flush/cycle de auth.login y de las claves nativas de autenticación; el orden relativo al receptor last_login no es relevante. Se escribe account_version del objeto User que acaba de superar autenticación, sin recarga que adopte una revocación posterior y sin escribir mfa_version. Ubicación: apps/core/admin.py, ya autodetectado por Admin. dispatch_uid estable evita duplicación de registro.

No se modifica AccountGate ni su compatibilidad sólo0; no se añaden settings, migraciones, servicios, plantilla, backend o proveedor. No se sustituye AdminSite/LoginView ni se altera formulario/CSRF/next. El receptor no actúa sobre signin propio, Client.force_login o señales de otros namespaces/métodos. La carga del módulo ya ocurre por autodiscovery; la prueba real candidata debe acreditar el registro, no una llamada manual al helper.

Alternativas descartadas: enlazar automáticamente cualquier versión ausente en AccountGate debilitaría revocación; recargar User al terminar passwordcheck podría adoptar un epoch revocado; un receptor global alteraría otros flujos; un AdminSite/LoginView personalizado añade sustitución de configuración y superficie sin necesidad para este punto. La selección es root, informada por revisión nativa de sólo lectura; la propuesta no es aceptación ni prueba.

## Validación seleccionada

Dos casos originales idénticos más ocho casos nuevos, diez en total: ceremonia TOTP completa ES/EN tras loginAdminversion1; tres rechazos —contraseña, CSRF, nonstaff—; revocación interpuesta después del passwordcheck real sin alterar su resultado, que debe mantener epochadmitidoantiguo y cerrar sesión en la siguiente petición; dos controles de alcance con force_login y signinpropio, observando señal real sin modificar sus efectos. El signin propio debe seguir enlazando su versión por su código y llegar a MFA.

Oráculos de estado completo/archivos por fase, sesiones explícitas, last_login y consumoTOTP exactos; no excluir tablas ni ocultar efectos de la intervención intencionada. La interposición no es una nueva espera SQL ni revocación concurrente medida. Contraseñas/códigos/cookies/IDs no salen a propiedades o Telegram. El prerregistro detallado de candidata se fija antes de ejecutar; diezPASSsinomisiones, fuentes estables, limpieza yTelegram exigidos, no todavía acreditados.

Revisión propia de diff, blastradius e historia: AccountGate versión introducida en9acfc481 para no autoenlazar sesiones revocadas; se preserva. Dos entradas de contraseña reales localizadas —signinpropio yAdminLoginView—, más emisores de prueba/terceros no habilitados por el receptor. La clase CurrentGroupAdmin y todas sus guardas deben permanecer ASTidénticas. No repetir16casos de esperas/CRUD ni56GET por rutina si se demuestra esa identidad y los controles de alcance pasan. N11 conserva regresión integrada final.

Retorno de481 sólo aplica a la pareja de fuentes37ccaaa/ae33175: esta corrección la supera. Ningún retorno a una versión anterior al arreglo queda autorizado por aquella igualdad; mantener aislamiento y seleccionar/contrastar destino cuando corresponda, sin fabricar imagen o switchactual. N11/N15pendientes, N02residualend y N12–N14condicionados; contrato/objetivo activos.
