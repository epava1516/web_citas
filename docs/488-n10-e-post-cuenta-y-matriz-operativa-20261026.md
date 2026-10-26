# N10E — POST de cuenta Admin y matriz operativa77

Referencias y disposiciones seleccionadas verificadas, **N10 aún abierto**. Base0dcf89f, [prerregistro487](487-n10-e-prerregistro-post-cuenta-admin-20261026.md), [login corregido486](486-n10-d-login-admin-epoch-verificado-20261026.md). Alpha/noindex;9/13bloques obligatorios aceptados.

## Referencias nativas actuales

Run `20261026-224102-607397ac`: **2PASS,0FAIL/ERROR/SKIP,64.880sJUnitQA/1796huellas estables**. Dos recorridos ES/EN y seis etapas instrumentadas. NativePasswordChangeForm verificó contraseña antigua, validó/hashó la nueva y rotó sólo la Sessionpropia con authhashactual y epochsconservados. La sesión anterior del mismo usuario se cerró al detectarse el hashviejo; no se interpreta como incremento de session_version o revocación universal de tokens/copies. El logout real eliminó exactamente su sesión y volvió al home del idioma.

Contraseñaantiguaerrónea200, CSRF403 en password/logout y GETlogout405 no causaron efecto. GETdone/index posteriores al cambio200; después del cierre, indexanónimo302. Las preparaciones usaron force_login con epochs vigentes explícitos, no otra ceremonia login/TOTP. Todos los173modelos/through y ocho archivos se compararon por fase, sin excluir tablas ni permitir cambios de permisos/MFA/last_login; sólo password/Sessionpropia y posterior retirada de sesiónpeer/propia. No RateWindow nuevo en estas vistas nativas.

| Etapa instrumentada | Antes | ES actual | EN actual | SQL ES/EN |
| --- | --- | ---: | ---: | --- |
| POSTcambiopassword | Sin referencia comparable |230.965ms|256.933ms|12/12|
| GETsesiónanteriorcerrada | Sin referencia comparable |10.036ms|15.265ms|4/4|
| POSTlogout | Sin referencia comparable |16.658ms|18.222ms|6/6|

Una muestra por etapa/idioma, incluye hash/verificación real en passwordchange; no p95, capacidad, TCP, speedup o SLA. Todos devolvieron302/0bytes y no-store; las respuestas se cerraron. QA incluye fixture/oráculos y no es latencia de aplicación.

Fuente de aplicación sin cambios desde486, revisiones propias focales, Ruff y prerregistro/grafo anteriores al ensayo. PG17/Redis7.4 propios, IDs de imágenes cacheadas congelados y observados con PID/start_ticks exacto, fuentes/vendor/documentos/instumento estables, contenedores/temporal ausentes y TelegramPASS confirmados. XMLoriginal SHA `b7c0c448698c113f467785e9c8b6ab8926774c5868a120d097246c0a080995fc`. No imagen/build, proveedor, migración persistente, conexiónMCP o servicio normal modificado.

## Matriz77 y alcance de evidencia

[Matriz trazable provisional77](evidencias/n10-e-matriz77-disposiciones-20261026.json), SHA `14ac63d2df6b6a5588d26a3923e12d839232aefa06a450b169c9bdb524bf1b0e`. Identidad exacta contra el censoN00 canónico, no un conjunto nuevo más pequeño; campos originales de familia/fuente/variantes preservados. Root contrastó140rutas de fuente actuales y las decisiones por modo/autoridad/efectos/reversión/replay/coste/límite.

| Unidad | IDs | Disposición actual |
| --- | ---: | --- |
| Comandos propios |15| Acciones nativas seleccionadas con testigos directos/servicios/nested explícitos; no15CLI completos inventados |
| Comandos Django |31| Tres utilidades en modos reales seleccionados; otras28 con razón de no selección o proveedor condicionado |
| Procedimientos operativos |11| Diez con primitiva/escenario y límites reutilizados; retorno actual seleccionado pendiente |
| Patrones Admin y acción global |16+1| GETauxiliares, GroupCRUD/esperas y accountPOST/login/MFA en su alcance verificado |
| Health |1| NormalTCP actual y cierreRecovery503 original con fuentes idénticas |
| IDsdispatch |2| Un productor real; fuente/casos originales conciliados, no dos tareas nuevas |

Hay **76 disposiciones acotadas verificadas y una pendiente**. No son76tests,76funcionalidades completas ni cierreN10. Se mantienen por separado PASS/FAIL/ERROR/SKIP y ejecución vs registro/source. La revalidación46comandos conserva83identidades,133PASSindividuales,18muestras collector/50SQL y cuatro restauraciones reales con relojes; la batería histórica global sigueERROR/3697PASS/129SKIP/3FAIL. La configuración de rol evidence tiene servicio/initializerreal equivalente, no nueva invocaciónCLIstandalone. La salida JSONpositiva de snapshot ya tiene evidencia479 separada. No sumar testigos superpuestos de comandos y runbooks como casos únicos adicionales.

Los31comandosDjango conservan pin5.2.17 y fuente instalada actual:32archivosvenv no tenían freeze histórico de bytes. No se infiere esa identidad ausente desde el pin. sendtestemail sigue condicionado a proveedorN12; shells/diffsettings/flush/etc no se ejecutan para fabricar crédito. Cada fila concreta los modos observados o no seleccionados; no se inventa un total de variantes posibles.

## Única salida pendiente elegida: retorno actual en aislamiento

La igualdad de753rutas Git de37ccaaa/ae33175 registrada481 ya no incluye el receptor añadido en0dcf89f. La comparación actual0dcf89f→8589acd confirma que la única diferencia de runtime es apps/core/admin.py; esquema/dependencias/tareas/plantillas y Groupguards se conservan, pero **todavía no acredita cambio de procesos actual**. No cierro esa salida con el ciclo histórico726 ni con sólo un par de hashes.

Próxima referencia finita: procesoGunicorn propio con fuente actual→anterior8589acd→actual sobre el mismo PostgreSQL de prueba, sin construir imágenes ni copiar docs/evidencias. Debe probar fuente efectivamente cargada, readiness, sesiones ya admitidas/lectura autorizada y todos los datos/archivos preservados, más cierre de cada proceso. El destino anterior pierde la corrección de loginAdminepoch1: alcance de mantenimiento controlado, no aprobación para apertura o retorno productivo; no se ocultará esa limitación. Los métodos/password/MFA actuales ya tienen evidencia486/487. El prerregistro del retorno y fuentes se fijará antes de ejecutar. No nuevo provider/CI/campaña de capacidad.

## Custodia y continuidad

[Archivo compactoN10E](evidencias/n10-e-matriz-y-post-cuenta-20261026.tar.gz), 16miembros/164581bytes, SHA `2b72ce3ecc198ce2484348198f1f571243d23c34bde11c4eb9c3cdf3f71d7508`. Contiene instrumento/prerregistro, fuentes congeladas, auditorías/propiedades saneadas, matriz77 exacta, propuesta46comandos con133testigos y revalidaciónactual, resúmenes/recibos. No rawtraces/XML/logs o secretos. Las referencias A–D mantienen sus archivos canónicos previos; el nuevo hash de matriz se actualizará explícitamente cuando se resuelva la fila pendiente.

Mantenimiento de disco del mismo contrato preservado: [registro](mantenimiento-disco-20261026.md),34,55GiBreales liberados por copias recuperables, contexto futuro excluye≈581MiB; no build ni reducción observada de imagen por esa cifra. La purga totalfinal deartifacts sólo corresponde al último pasoN15, no ahora.

Siguiente: retorno aislado actual y cierre77/N10 si la evidencia lo permite; después N11/N15. N02residualend por usuario, N12–N14condicionados. Contrato/objetivo activos; cambios laterales preservados.
