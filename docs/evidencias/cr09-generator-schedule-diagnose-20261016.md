# Diagnóstico del generador: no reproducción

[Recibo](cr09-generator-schedule-diagnose-20261016.json). Correctiva155052-580f4c0c, fuente2ed5cae: diagnóstico completo, CI1PASS1034,71s; ambos controladores0/MainPID0. Emisor/app/criterios/límites sin cambios. Plugin explícito; no aceptar carga desde instrumentación.

| Ensayo largo | p95observable | Máximo demora generador | Validez |
|---|---:|---:|---|
|152034 limpio|0,351628515s|113,546613ms|INVALID preservado|
|155052 diagnóstico|0,384197934s|32,837605ms|PASS instrumentado, no aceptación|

18.000éxitos/0errores-timeouts-noemitidas-pendientesfinales y15subidas correctas. Generadorp952,782ms/p994,141ms. Recibo incluye p95 ended−emitted de seis rutas,3000lecturas cada una. No comparación causal con corrida previa: observador y sin A/A.

184388iteraciones;13intervalos significativos,11durante llegadas y2posteriores. Peor emisión d13264,t663,2→663,232837605s: selector79,171ms frente timeout solicitado47,044ms,overshoot32,127ms; CPUselector0,223ms/callback0,149ms;deltaesperarunqueue0,675ms. Esta muestra coincide principalmente con duración del selector; no demuestra la causa de113,55ms original ni reproduce dicho fallo.

Lecturas de schedstat y relojes secuenciales: hay deltas runqueue superiores al wall de un intervalo y no son partes exclusivas sumables. Dos intervalos más costosos están después de900s:5,341sCPU no es bloqueo de emisión. Sobrecoste no medido causalmente. Sin callbackrepr/headers/cuerpos/credenciales; retención acotada≤256intervalos.

Kernel native-sealed/dependencias/Python3.12.15,4sync/10k/20rps900s,normalworkerBeat,GCappnormal. Controlador4CPU3584MiB/PG1CPU1536MiB/Redis0,2CPU128MiB/swap0. Fuentes congeladas y PIDs/start_ticks/temporal/PG/Redis ausentes comprobados independientemente. Intento TypeError154618 preservado, sin llegadas.

No repetir diagnóstico o carga limpia por no reproducción. Contractual sigueINVALID por máximo113,55ms, sin relajar100ms ni atribuir hardware/cargador. Próximo paso: auditar selección y condiciones de N3 común actual, reutilizando cierres locales y explicitando lo pendiente. CR09 abierto.
