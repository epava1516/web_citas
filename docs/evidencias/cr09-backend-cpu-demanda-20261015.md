# CPU del backend exacto de PostgreSQL: diagnóstico CR09

Run `132246-f67bbb9c`, base `c708c31` más instrumentos:1PASS/101.29s y3controles puros PASS.72peticiones secuenciales, seis casos×12 después de control caliente; datos sintéticos10k y cuotas propias previas. Fuentes intactas; PIDs raíz/hijo/backends, temporal y PG/Redis ausentes verificados independientemente. [Contadores y sentencias](cr09-backend-cpu-demanda-terminal-20261015.json).

El PID SQL se traduce a PID del host enumerando únicamente `docker top` del contenedor de nombre/etiqueta/PID ya verificados. Comprueba cgroup, NSpid y starttime antes/después; rechaza reutilización o cambio de backend. No enumera /proc global ni toca servicios normales. [Docker top](https://docs.docker.com/reference/cli/docker/container/top/), [campos utime/stime/starttime de Linux](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html). CPU propia utime+stime, no cutime/cstime de hijos. Resolución100Hz: no precisión submilisegundo por consulta.

| Caso | CPUbackend por petición | CPU instanciaPG por petición | CPU clienteDjango por petición |
|---|---:|---:|---:|
| ListadoES |59.167ms|59.948ms|172.462ms|
| ListadoEN |50.833ms|62.298ms|141.159ms|
| BúsquedaES |91.667ms|91.427ms|173.699ms|
| BúsquedaEN |96.667ms|97.223ms|181.951ms|
| FichaES |24.167ms|24.856ms|64.317ms|
| FichaEN |27.500ms|28.289ms|71.213ms|

Diferencias pequeñas CPUbackend>cgroup pueden venir de ventanas de lectura y cuantización; no restarlas como tiempo negativo de mantenimiento. La media igualmente ponderada de backend58.333ms implicaría1.167CPU a20rps SI fuera representativa de esa carga. No es prueba de imposibilidad: instrumentación pg_stat_statements/track_planning activa, muestra secuencial, otros backends/trabajadores paralelos y fondo no incluidos en el proceso medido. CPU cliente incluye transporte de test/ORM/render, no equivale al worker WSGI. Sin inferencia causal desde diferencias entre idiomas.

Se conserva último p95 limpio16.572804s FAIL y candidato de cobertura provisional. Hallazgo: búsqueda gasta mucho más CPUbackend que ficha y sigue siendo prioridad, con reutilización de conexión confirmada. Antes de cambiar workers/cuotas, separar demanda por familia SQL sin seguimiento de planificación; los tiempos plan/exec actuales no son CPU por sentencia. No cadena automática de cargas, aceptación CR09/N3 ni cambio de producto desde este diagnóstico.
