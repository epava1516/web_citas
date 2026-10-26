# N10D — correctiva del oráculo RateWindow y validación focal

Primera candidata20261026-221408-152c67fe: **7PASS/3FAIL,0ERROR/SKIP,126,993sJUnitQA/1795huellas estables**. Original de aplicación1PASS/1FAIL de483 preservado. N10abierto77/9de13, alpha/noindex. No se declara diezPASS en una ejecución.

Los dos diagnósticos originales de login ya pasan con el receptor. Los tres fallos son de los nuevos oráculos: los dos TOTP ES/EN y el signinpropio alcanzan la aserción de transición completa sin que el test hubiera enumerado la fila RateWindow que la limitación de intentos crea legítimamente. La función core.accounts.limited usa una tabla PostgreSQL, no sólo caché. El primer ensayo y el instrumento exacto quedan conservados, con fuentes, XML y TelegramERROR, antes de la correctiva. No se cambia aplicación para hacer pasar el test.

## Corrección acotada anterior a la repetición

Sólo tests/test_admin_login_guards.py: se añade un helper que calcula el bucket esperado mediante el HMAC nativo de action:127.0.0.1 y exige ausencia previa, clave exacta, attempts1 y starts_at dentro del intervalo de la petición real. Las transiciones admiten exclusivamente esa nueva fila junto con Session/last_login o consumoTOTP ya declarados. No se excluye RateWindow ni otra tabla; los demás buckets y modelos/archivos deben permanecer idénticos. Los tests positivos registran rate_window_exact, sin exportar claveHMAC o datos de sesión.

La aplicación permanece byteidéntica a la primera candidata, incluido el receptor de epoch. Los dos diagnósticos originales siguen byteidénticos al diagnóstico inicial. AST de _prepare/_csrf/_password/_login_delta/_same/_publish y funciones de los tres rechazos y de epochinterpuesto permanece idéntico; las nuevas importaciones no añaden efecto de ejecución al módulo. Se revisan fuente y Ruff antes de repetir.

## Selección focal y reutilización

Cuatro casos explícitos: test_native_admin_password_then_totp ES/EN y los dos parámetros de test_admin_epoch_receiver_does_not_bind_other_login_flows. Aunque force_login pasó antes, comparte función modificada con core_signin y se repite conservadoramente. No repetir los dos diagnósticos originales, los tres rechazos ni epochinterpuesto si se verifica su fuente/AST/helpers y aplicación idénticos: son seis casos válidos de la primera candidata.

Antes de lanzar: grafofocal del instrumento corregido y este documento, congelacióncompleta/vendor/config/documentos/instrumentos/imágenes antes/durante y proof de identidad de seis casos reutilizados. Runner oficialfocused, serial, PG17/Redis7.4 propios, parsernativo y timeout600s, sin build/carga/servicios ajenos. Dos selectores de función se expanden a cuatro casos, guardas de propiedadreal vigentes.

Aceptar sólo4PASSsinomisiones/fallos/errores, oráculos completos con RateWindow exacto y sesiones/TOTP; huellas estables, recursos/temporal retirados y Telegramterminal confirmado. La conciliación final debe contrastar los seisPASSreutilizados con su XML original y los cuatroPASSfocales con el nuevo: diez casos únicos entre dos cortes, no una suiteúnica10PASS, y no sumar once por el force_login repetido. Si aparecen otros efectos, diagnosticarlos sin ampliar el oráculo por comodidad.

Esta correctiva no altera484 ni sus fuentes congeladas retrospectivamente. QA no es latencia de aplicación. Las guardas AccountGate/MFA y Group permanecen; no publicación/beta/proveedor/migración o cambios de servicios. N11/N15pendientes, N02residualend por usuario y N12–N14condicionados. Objetivo/contrato activos.
