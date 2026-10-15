# Estructura SQL integrada: corto limpio todavía FAIL

Run222515-91a6b5da, SHAe7e68cd, producto3ba2ec4; **FAIL186.21s**. [Recibo](cr09-query-structure-http-terminal-20261015.json). Mismos4sync/20rps/60s/10k/Celery2+Beat/subida/cuotas, sin perfiladores/observadoresworkers; generadorfreezeconservado. Python3.12.15/Django5.2.17/Gunicorn23/PG17.11. Fuentes congeladas exactas; root/UVchild/temporal/contenedorespropiosretirados, MainPID0/ControlGroupvacío. Legacyrawmanifest pg_server_shared/normalstack es texto incorrecto: adaptadorusaPG/Redispropios acotados yconlabelúnico, ningúnservicionormal.

|Métrica limpia|f9f404d anterior|3ba2ec4 estructura|
|---|---:|---:|
|p95completo|1.118772s|1.218890s|
|p50completo|0.234972s|0.228267s|
|p95servicioGunicorn|0.313042s|0.303526s|
|Completadasfinales|1200|1200|
|Errores/timeouts/omisiones|0/0/0|0/0/0|
|Requests>=0.8s|108|132|
|Taskfoto realwall|0.971466s|1.485950s|

p95+8.95%observado entre dosruns,no atribucióncausal/reproducibilidad. Se conserva cambio por reducción aisladademostrada de trabajoCPU/estructura,SQLparamsexactos y23controles, no poraceptaciónHTTP. Generadorp951.809ms/p993.225ms/max21.250ms cumplevalidez; subida1/1sinerror, checksfinal/drainPASS. Sólo latencia incumple.

|Cohorteemisión|p95 anterior|p95 actual|Lentas anterior→actual|
|---|---:|---:|---:|
|0–5s|1.281048s|1.441924s|91→95|
|5–10s|0.881254s|1.040717s|17→37|
|10–15s|0.383550s|0.368737s|0→0|
|15–60s|0.387142s|0.364126s|0→0|

|CasoHTTPactual|n|p95|
|---|---:|---:|
|Listado|400|1.267949s|
|Búsqueda|400|1.232933s|
|Ficha|400|1.149303s|

Servicio medio0–5s0.228865s vs15–60s0.180276s; residuocliente−servicio0.965716s vs0.029543s. No es colaexclusiva ni restadepercentiles. Las132lentas se concentran0–10s, ninguna después; atasco inicial sigue sin resolver. Tarea foto siguepor debajo deantiguos10s,pero su variación actual no demuestra causalidad delp95.

No repetirFAIL ni correr15min/N3. Siguiente diagnóstico separado deingress sobreproductoactual, mismascondiciones yobservadoresWSGI/SQL/GCsinimportshandlers,CPUcgroupspropios1Hz. Emparejar1200IDs para distinguir espera previa,spanWSGI,CPUthread,SQLwall yGC enel arranque. No interpretar sup95instrumentado como gananciadelimpio ni aplicarotro candidato antes delresultado. CR09/N3/objetivoíntegroabiertos.
