# B07 — Fases opcionales del cliente HTTP

Estado: seis casos y calibración TCP pequeña auditados; no capacidad ni ahorro causal. Ocho de18cerrados.

Tras171 se añade trace_phases=False a fetch_http. Sólo al activarlo captura loop.time relativo: inicio conexión, conexión completada, drain local, línea de estado recibida, cabeceras completas, cuerpo completo y terminal. No añade awaits ni cambia la política, parser, peticiones, datos de respuesta o emisor. _run y run_async_open_loop conservanAST idéntico. No denominar línea de estado primer byte ni drain entrega al servidor. Timeout conserva marcas parciales y resultado de error anterior.

--benchmark-client-phases exige focused/1worker y selector exacto functional o short. Se registra en result y manifest; measured, regression,2workers y archivo ajeno se rechazan antes de crear servicios. La bandera no es un observador de aplicación ni permite cuantificar admisión por sí sola. Coste causal del instrumento no medido; las comparaciones futuras deberán conservar esa limitación.

155336-bfb24854 se interrumpió tras detectar cierre circular en el servidor controlado: cuatro casos completos, no seisPASS. En la versión instalada, esperar server.close antes de liberar el handler retenido impide cerrar. Se corrigió liberando el evento y esperando el handler antes de salir del contexto del servidor. Resultado/artefacto inicial y aviso terminalERROR conservados, limpieza y fuentes congeladas verificadas.

155509-e88d2d17:6PASS/0omisiones,10,537sJUnit. Conserva tres casos anteriores y añade separación de retrasos de cabeceras/cuerpo, timeout parcial real y retención de payload por el emisor. TCP pequeño posterior155621-06ce6c50:1PASS/0omisiones,10perfiles/2derechos,60dinámicas200 y1subida302conpersistencia, cuatro Gunicornsync, worker/Beat y PostgreSQL/Redis propios. [Auditoría](evidencias/b07-client-phases-calibration-20261021-155621-06ce6c50-audit.json) comprueba61payloads completos/monótonos, tiempos terminales dentro del ledger, paridad de contabilidad, patrocinio, fuentes/limpieza/PIDs/Telegram. p95observable233,113ms es calibración, no aceptación de carga10000. [GuardasCLI](evidencias/b07-client-phases-cli-guards-20261021.json): cuatro rechazos esperados, cero runs nuevos.

628fuentes apps/config/templates idénticas a imagen5a075. Del mapa726,724idénticas y dos herramientas distintas: scripts/benchmark_async_transport.py y scripts/run_local_ci.py; no afirmar726runtime intactas. La primera auditoría conservó su rechazo al exigir igualdad726indebida, antes de corregir a esa diferencia explícita. Sólo runner y testHTTP cambiaron entre la batería de seis y la calibración; el instrumento y sus seis casos permanecen iguales.

Delta posterior a calibración, pendiente del corto173: impedir que un short con captura opcional habilite900s, aunque su veredicto numérico pase. diagnostic_continue_contract exige además captura desactivada; veredicto y asserts conservan todos los criterios. Esta rama short no se acredita con el escenario funcional pequeño.

Los FAIL válidos112359 y152807 siguen vigentes; B07 no se acepta y no se ejecuta900s. Siguiente173diagnostica límites de transporte con la población completa; no es repetición para perseguirPASS.
