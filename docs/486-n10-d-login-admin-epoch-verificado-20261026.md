# N10D — login nativo Admin con epoch vigente verificado

Aceptación local de la corrección de disponibilidad del login Admin, **sin cerrar N10**. [Original482](482-n10-d-prerregistro-login-admin-epoch-20261026.md), [diagnóstico/decisión483](483-n10-d-diagnostico-y-plan-login-admin-20261026.md), [candidata484](484-n10-d-prerregistro-validacion-login-admin-20261026.md) y [correctiva del oráculo485](485-n10-d-correctiva-oraculo-y-validacion-focal-20261026.md). Base8589acd; continúan9/13bloques obligatorios aceptados, alpha/noindex.

## Defecto y cambio

Antes, una cuenta staff activa/verificada con contraseña correcta y session_version1 obtenía la sesión nativa, pero el GETindex la eliminaba por carecer de account_version y devolvía al login. El control0 llegaba a MFA mediante compatibilidad del middleware. Original `20261026-220301-837183f9`:1PASS/1FAIL59,198sJUnitQA/1794huellas. Fallo de acceso legítimo tras revocación/recuperación previa; no se observó acceso indebido o MFA omitido.

Único archivo de aplicación modificado: apps/core/admin.py. Receptor user_logged_in de senderUser, limitado al POST resuelto namespaceadmin/url_namelogin, enlaza user.session_version del objeto admitido después del flush/cycle nativo. No consulta un User nuevo, no adopta revocación posterior, no escribe mfa_version y no sustituye formulario/CSRF/next. dispatch_uid estable. AccountGate, cuentas, MFA, vendor, settings, modelos y migraciones intactos. CurrentGroupAdmin/current_group_actor ASTidénticos, sin alterar las guardas ya aceptadas.

Historia y revisión propia: AccountGate9acfc481 conserva la restricción de autoenlace sólo0. Dos entradas reales de contraseña localizadas —signinpropio yAdminLoginView—; controles de alcance prueban que el receptor no enlaza force_login ni el signin propio. Revisión nativa de sólo lectura con task14/reporte10 y decisión root independiente; revisión diferencial de auth/epochs/sesión con trazas, riesgo y blast-radius, no escaneo activo ni garantía global de seguridad.

## Evidencia conciliada: diez casos únicos entre dos cortes

La primera candidata `20261026-221408-152c67fe` conserva **7PASS/3FAIL,126.993sJUnitQA/1795huellas**. Los dos originales ya pasan. Los tres fallos de nuevos tests ocurrieron al exigir una transición sin la fila RateWindow creada legítimamente por MFA/signin. Error propio del oráculo: corregido enumerando claveHMAC exacta, attempts1 y starts_at dentro de la petición; ninguna tabla excluida, ninguna modificación adicional de app.

Focal `20261026-222154-ba06d23e`: **4PASS,0FAIL/ERROR/SKIP,76.644sJUnitQA/1795huellas**. DosTOTP ES/EN y dos controles de alcance reejecutados. Seis casos de la primera candidata se reutilizan por identidad completa de aplicación/config/vendor y AST de funciones/helpers de test; dos originales son byteidénticos al diagnóstico. Resultado: **diez casos únicos válidos**, no una suiteúnica10PASS; force_login repetido no añade un undécimo.

| Comprobación | Antes | Candidata actual |
| --- | --- | --- |
| Loginpassword+CSRF epoch0 | Sesión conservada y MFA pendiente por compatibilidad0 | Sesión conservada, epoch0 enlazado explícitamente y MFA pendiente |
| Loginpassword+CSRF epoch1 | Contraseña válida, luego logout y vuelta al login | Sesión conservada y redirección a MFA, sin MFA implícito |
| TOTPreal ES/EN tras epoch1 | No medido por el diagnóstico anterior | Código real consumido una vez, Sessionrotada, epochsvigentes y Admin200 |
| Contraseña/CSRF/nonstaff | Sin crédito nuevo del diagnóstico | Rechazos200/403/200, sin sesión/grants/epoch o efectos de dominio |
| EpochDB incrementado después de passwordcheck real | Sin muestra anterior | Receptor conserva admitido1 frenteDB2; siguienteAccountGate cierra sesión |
| force_login y signin propio | Alcance previo separado | Observer de señal confirma ausencia de bindingAdmin; signin enlaza por su código y llega aMFA; force_login ausente sigue cerrado |

Los tiempos anteriores son QA total por ejecución, no latencia de login o mejora causal. No se suman como benchmark ni se afirma reducción de coste. Diezcasos se concilian individualmente con XMLoriginales/propiedades y hashes, sin borrar negativos.

## Integridad, reproducción y límites

Todos los casos protegen173modelos/through y ocho archivos de la fixture. Login sólo admite last_login y Sessionpropia; MFA, consumo exacto del contador y rotación de esa Session, más el único bucketRateWindow delimitado; intervenciónepoch se enumera aparte. Los demás usuarios, sesiones, permisos, dominio y archivos quedan intactos. Seis casos reutilizados no dependen del helper nuevoRateWindow; sus funciones/helpers/decoradores y fuentes de app son equivalentes. El selectorfocal incluye ambos parámetros de la función de alcance modificada, conservadoramente.

Guardas de PG17/Redis7.4 propios, fuentes/instrumentos/vendor/docs/grafo congelados, imágenes cacheadas observadas con PID/start_ticks del runner, limpieza de contenedores y temporal y recibosTelegram terminales confirmados. No build/carga ni servicios normales/proveedor/DBMCP. Focal XMLSHA `18004dc16f4da6d9cd9f6860c0704ce9c78c56e90893d9c8d37feb220d97e51f`; originalSHA `ffb1690b7fd409c88f4295cddc216c6221618dcfa045d48be06da87619a28d05`; primera candidataSHA `f73bbf6eea23223c824c1f73a4f216aec14d388753a2e7872ec1d33369bc4b30`.

La prueba de epoch tardío reenvía check_password real e interpone una actualización sintética; no es una nueva espera SQL ni serialización universal tras la última comprobación. Dos ceremonias TOTP reales no acreditan otros backends, proveedores o todos los flujos de recuperación. N11 conserva regresión integrada final. No repetir16Group/56GET o120testigos por esta adición cuando AST/consumidores y controles de alcance preservan su significado.

La igualdad de fuentes37ccaaa/ae33175 documentada481 precede al receptor; no concede retorno automático de esta candidata ni prepara imágenes/switch. Cualquier destino posterior requiere su contraste; las imágenes históricas726 no se autorizan por esta aceptación. No despliegue/apertura.

Evidencia compacta: [archivoN10D](evidencias/n10-d-login-admin-epoch-20261026.tar.gz), 34miembros/288623bytes, SHA `b185b9e0e28ee92a8f211a8d0176339e64e95749667d4581349d21c5066a83ab`. Fuentes exactas de instrumentos y app, preregistros, congelaciones, auditorías sanitizadas, registros de propiedades y resúmenes/recibos originales. No trazas de error, logs, claves de Session/cookies/códigos o secretos. Los XMLraw con trazas se mantienen sólo en artifacts con hash duradero; su pérdida prevista en la purga final no cambia los negativos resumidos.

Siguiente: completar matriz trazable77 y aceptación de N10; después N11/N15. N02residualend por usuario, N12–N14condicionados. Contrato y objetivo activos, alpha/noindex.
