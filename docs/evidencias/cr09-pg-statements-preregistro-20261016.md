# Diagnóstico de planificación y ejecución en PostgreSQL

Objetivo: resolver si el tiempo inicial observado por el cursor se corresponde principalmente con planificación/ejecución del servidor, o si queda una diferencia importante fuera de esos contadores. No es una prueba causal deCPU/espera ni aceptación de rendimiento.

Instrumentación de [PostgreSQL17](https://www.postgresql.org/docs/17/pgstatstatements.html): pg_stat_statements cargada al crear exclusivamente el contenedor desechable propio; track_planningon ytracktop. Mantiene1CPU/1536MiB/CPU4/swap0/pids128/WAL256/80. Controller0–3/3584MiB/swap0/tasks512, RedisCPU5/.2CPU/128MiB, Gunicorn4sync yCelery2+Beat,20rps60s/10ksintéticos/1upload. No cambios del producto.

Activación explícita --benchmark-pg-statements requiere SQLshapes/ingressonly yelcorto enfocusedserial. Verificar label/nombre/containerID/puertopropio yDBtest, preload ytrackplanning antes de crear extensión enesaDB. Biblioteca nunca se activa en servicio normal. El monitor abre conexión readonlycontracknone/timeout2s/connect5s; resetea sólo estadísticas de laDBpropia antes del origen del generador. Muestrea1Hzdurante arrivals/drain, límite140s/5000identidades, registra dealloc ystats_reset. SQLnormalizadosintético queda sólo en artefactosignorados; evidencia versionada debe usar huellas/contadores.

Las estadísticas agrupan backends del mismo servidor/base, incluyendo aplicación/subida/refresco, ypuedenagruparvalores distintos. No equivalen a CPU, espera exacta, ni atribuciónporID. La extensión ytrackplanning añadenoverhead no cuantificado; sus tiemposHTTP no se comparan causalmente con limpios. Se preservan errores/expulsiones/estadísticas faltantes sin convertirlos enahorro.

Verificaciónprevia:11pruebas de protocolo/privacidad/rechazo sinDB,0,55s, yCLIrechaza modo noacotado antesderecursos. PostgreSQLreal aún pendiente: el propio ensayo debe probar librería, extensión ycontadoresreales. Producto conserva p95limpio0,675688PASS/0,880357FAIL;sinreproducibilidad/900/N3/CR09.
