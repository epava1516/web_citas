# N10E — prerregistro de POST auxiliares de cuenta Admin

Referencia actual preparada, sin ejecución/aceptación. Base0dcf89f, [login corregido486](486-n10-d-login-admin-epoch-verificado-20261026.md). N10abierto77/9de13, alpha/noindex. El corte previo2144fuentes/21319nodos/86780relaciones/1038comunidades, SHAb4b71657ffd56d462cb1c40fb9d5da40ef6cf51153448264e6727d2f87f6f3fe, fue contrastado antes de la conciliación. No reconstrucciónN15.

## Selección fundada

La matriz final conserva dieciséis patrones Admin y una acciónglobal; N10A/C/D aportan escriturasGroup, GETauxiliares y login/MFA. POSTpassword_change y POSTlogout siguen como ramas heredadas sin ejecución propia observada. Se elige un único recorrido por idioma ES/EN en tests/test_owned_admin_account_post_reference.py, dos casos, sin cambiar producto ni repetir login/MFA.

Preparación: actorstaff sintético no superusuario, activo/verificado/MFAhabilitado, session_version1, contraseña actualreal, dos ClientCSRF nativos con sesión admitida explícita mediante force_login y epochs vigentes. No acredita ceremonia nueva de contraseñaLogin/TOTP; sí se verifica contraseña antigua y nueva por los formularios reales de cambio. El segundoClient representa una sesión previa del mismo usuario, no otra identidad.

Por idioma: GETformpassword200; POSTsinCSRF403 y contraseñaantiguaerrónea200 sin efectos; POSTválido302 a password_change_done; únicamente cambia password del propioUser y se rota su propiaSession con authhashactual y epochsconservados. GETdone/index200 sin escrituras. La sesiónpeer con hashviejo debe cerrarse en su siguienteGETindex302 haciaAdminlogin, eliminando exactamente su fila. GETlogout405 y POSTlogoutsinCSRF403 no cambianestado. POSTlogoutválido302 al home del idioma elimina exactamente la Sessionactual y sus datosMFA; GETindexanónimo posterior302 sin crear otra sesión.

Las comparaciones abarcan173modelos/through y ocho archivos, sin excluir tablas. last_login de ambas preparaciones queda antes del baseline; el cambio de contraseña no debe actualizarlo ni modificar epoch/mfa/permisos. NativePasswordChangeView/LogoutView no llaman accounts.limited ni crean RateWindow; se conserva su oráculo completo. Los datos/tokens/cookies/hashpassword/sessionkeys permanecen locales, nunca propiedades/Telegram.

## Mediciones y protocolo

Tres observaciones por idioma: POSTcambiopassword, GETpeerrechazado y POSTlogout, cada una con wallinstrumentado, SQLejecuciones/tiempo y bytes. Status y no-store exactos; respuestas cerradas. Son una muestra por etapa/idioma con datasetfijo, no p95, capacidad, backendTCP o mejora causal. La contraseña se hashea/verifica realmente; QA/setup/oráculos se separan del reloj de petición.

Runner oficialfocused, serial, PG17/Redis7.4 propios, parsernativo y timeout600s; no build/carga/proveedor/servicios normales/DBMCP. Guardas de propiedad de contenedor/puerto/usuario/base, no producción/recovery. Antes de medir: grafofocal del instrumento/prerregistro, fuentes completas/vendor/config/docs e IDs de imágenes congelados; observar imágenesruntime vinculadas al PID/start_ticks exacto. Exigir2PASSsinomisiones/fallos/errores, todos los efectos exactos, fuentes estables, limpieza yTelegramterminal y auditoríaoriginal.

Sin candidata de optimización ni parche anticipado; si hayfallo se diagnostica y conserva. Se revisó fuenteDjango/seguridad del instrumento y primitives nativos. No se reejecutan N10A16/N10B2/N10C2/N10D10únicos ni runbooks válidos por rutina. Tras estas referencias, completar matriz77 y aceptarN10 sólo si salida contractual probada. N11/N15pendientes, N02residualend por usuario y N12–N14condicionados.
