# CR09: diagnóstico sin preparación por variable filtrada

Run030723-4573e1c9,SHAf4607db,1FAIL188,76s. p95instrumentado0,929214190s,1200éxitos0errores/omisiones,invalid_reasons HTTPvacío. NO diagnóstico válido de preparaciónactiva: cuatroarchivosworker contienen0static_ready. systemd recibió PREPARE_STATIC=1 pero run_local_ci construye entorno permitidoydescartaesa variable. Captura preservada como variante sinhook; no atribuirmejoría a startup ni comparar causalmenteconclean1,013029795FAIL.

Medias0–5s:HTTP913,617ms/preWSGI689,444ms/WSGI223,378ms/CPU104,618ms/SQL105,372ms. Medias15–60:HTTP248,422/preWSGI62,118/WSGI185,608/CPU99,413/SQL74,655ms. Sin causalidad exclusiva ni medida aceptación;SQL/GCsolapados. Datoscohorts-parsed.json/load-summary-parsed.json/worker-events-rawen artifacts/local-ci/20261016-030723-4573e1c9. No valoresutilizadosparadecidirproducto.

Causa localizada en entorno explícito de runner. Corregir con flagCLIvalidado y transmisiónexplícita,exigir4marcasstartupantesdeanalizarotrodiagnóstico. No modificarcriteriosni repetircleanFAIL/900s. Fuentescongeladas idénticas;runner/hijo/temp/contenedoresausentes;unidadfailed/MainPID0/ControlGroupvacío. Sinproducción/datosreales/Claude/proveedores,consumopreviointacto. CR09/N3/goalcompletoabiertos.
