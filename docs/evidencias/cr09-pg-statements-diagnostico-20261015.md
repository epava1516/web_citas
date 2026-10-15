# CR09: clasificación de sentencias en PostgreSQL propio

Base `14186a3` más diagnóstico explícito. Sólo instancia efímera validada por nombre/etiqueta/PID/cgroup, cuotas previas intactas. Adaptador aislado añade shared_preload_libraries=pg_stat_statements al arranque de ese contenedor; no modifica servicios normales. Reset específico de la base de prueba, planificación habilitada/restaurada en su sesión. No exporta SQL ni parámetros; normalización de pg_stat_statements puede conservar literales, por eso clasifica dentro de PostgreSQL. [Semántica oficial PostgreSQL17](https://www.postgresql.org/docs/17/pgstatstatements.html).

Primera ejecución `125341-6176c5b1` pytest1PASS, pero clasificador defectuoso: SELECT de ficha con columna search_document etiquetado como búsqueda. Se conserva sin aceptar esa clasificación. Correctiva exige operador@@ para página de búsqueda y añade aserciones por tipo. Run `125636-6ce78a00`:1PASS/89.89s,18peticiones secuenciales, seis casos con control caliente y tres muestras cada uno; fuentes intactas y limpieza independiente de raíz/hijo, temporal y PG/Redis. [Inicial](cr09-pg-statements-inicial-terminal-20261015.json), [correctiva completa](cr09-pg-statements-correctiva-terminal-20261015.json).

| Por petición instrumentada | ListadoES/EN | BúsquedaES/EN |
|---|---:|---:|
| Ejecución conteo |8.213/11.423ms|22.118/20.557ms|
| Ejecución selección página |0.129/0.242ms|28.211/24.284ms|
| Ejecución estado global vigente |13.215/11.538ms|9.190/15.660ms|
| Planificación hidratación |5.857/11.584ms|8.900/8.471ms|
| Ejecución hidratación |2.657/3.897ms|4.856/4.699ms|

Ficha ES/EN: otras sentencias planificación12.280/16.272ms y ejecución1.170/1.741ms por petición. Identificador de backend sin cambios en los seis casos: reutilización de conexión observada, no justifica activar persistencia ya configurada.

| CPU agregada PostgreSQL por petición, instrumentada | Inicial | Correctiva |
|---|---:|---:|
| ListadoES |58.035ms|48.940ms|
| ListadoEN |47.670ms|57.001ms|
| BúsquedaES |94.762ms|98.179ms|
| BúsquedaEN |103.878ms|94.476ms|
| FichaES |27.245ms|95.921ms|
| FichaEN |23.349ms|27.650ms|

Estos contadores incluyen mantenimiento de la instancia propia y overhead de planificación instrumentada. El outlier de fichaES no se explica con las duraciones SQL exportadas y NO demuestra demanda causal95.9ms de esa ficha. Muestra demasiado pequeña para declarar techo20rps o imposibilidad presupuestaria. No comparar con p95 limpio ni sumar CPU e intervalos SQL. Las llamadas del servidor incluyen comandos utilitarios/transaccionales internos, diferentes de contar únicamente cursor.execute del wrapper Django.

Prioridades justificadas: búsqueda repite trabajo significativo entre conteo y página, pero la candidata window previa fue retirada y no se reactiva desde este diagnóstico. El escaneo global all_state_current cuesta9–16ms además del conteo; examinar una equivalencia exacta aprovechando unicidad/FK de estado, con instantánea propia de sólo lectura y sin alterar transacciones heredadas. La planificación de hidratación sigue presente pero no es una explosión de ejecución. No habilitar kernel de valores ni modificar cuotas/concurrencia sin prueba adicional concreta.

Último p95 limpio conserva19.666012s y FAIL; diagnóstico no acepta CR09/N3 ni es ensayo de15min. No CPU por sentencia, presión bajo carga ni atribución de mantenimiento medidas.
