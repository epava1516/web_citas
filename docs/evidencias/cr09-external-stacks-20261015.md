# Muestreo externo de Gunicorn: ventana corregida, evidencia parcial

Producto vigente3ba2ec4; último limpio1.218890sFAIL. Este relevo añade instrumentos externos y un marcador de la alineación que la prueba ya calculaba; **no hay nueva optimización de producto ni aceptación CR09/N3**. [Recibo completo](cr09-external-stacks-terminal-20261015.json).

## Instrumento, intentos y validez

py-spy0.4.2 aislado, SHA256 9b4d1f39b2a47ae44f4c6a46f615dcc0287d7755beba5065f32391951e07d594. Adjunta sólo al Gunicorn descendiente del controller propio, comprueba run/PGpropio/startticks/cgroup/bindlocalhost. --subprocesses --idle --nonblocking --threads --rate100 --duration20 --format speedscope, sinlocals ni imports/wrappers nuevos en app. No otros perfiladores/observadores internos. Mismos límites, datos sintéticos y Celery2+Beat/subida reales propios. Python3.12.15/Django5.2.17/Gunicorn23/PG17.11.

1.223808-a88b1380: CI FAIL185.15s, sin stacks. El FileNotFound del contador opcional cpu.pressure se confundía con desaparición del target. La sospecha inicial de separadorNUL se descartó: AST confirma separador[0] correcto. Se conserva fuente inicial y recibo; no ocultar fallo de instrumento.
2.224224-07950cd5: cancelado mediante SIGTERM al runner propio y su ruta normal de limpieza, antes de target/captura. Se evita consumir otro ensayo cuya lecturaPSI fallaría. No es prueba completada ni resultado de rendimiento.
3.Probe acotado propio: captura Python3.12 durante1s PASS,99muestras/0errores, child retirado, PSI ausente explícito como null. No producción ni datos reales.
4.224418-767bdd30: captura externa válida de arranque, pero su intervalo quedó−33.745 a−13.956s respecto a llegadas.9756muestras/142errores. La espera existente de alineaciónBeat explicaba el desfase; no acredita stacks del atasco. CI FAIL184.65s instrumentado, no limpio.
5.224937-9792e0a6, SHA8898026: marcador benchmark-arrival-alignment.json persiste el targetBeat existente antes de sleep; no altera regla5s, preparación, warmup ni cronómetro. Captura lanzada1s antes del target, intervalo externo real−1.218 a+18.269s respecto a llegadas.9026muestras/965errores; master+4workers. CI FAIL185.98s instrumentado. Fuentes congeladas exactas y root/UVchild/sampler/master/4workers capturados (8PIDs), temporal/contenedores propios ausentes; unidad MainPID0/ControlGroupvacío. Target/sampler cgroup y startticks también se comprobaron independientemente mientras estaban vivos.

Se conservaron fuentes/limpieza de todos los intentos antes de modificar o repetir. No se tocaron servicios/Redis normales. Este kernel no expone PSI(cgroup cpu.pressure ni /proc/pressure/cpu); se registra **no disponible**, no cero. Ticks agregados host antes/después constan en recibos, sin atribuir presión/steal porproceso/CPU ni diferencias del portátil al código.

|Captura, contextos distintos|Muestras|Errores|Ventana respecto a llegadas|
|---|---:|---:|---|
|Arranque|9756|142|−33.745 a−13.956s, fuera del objetivo|
|Alineada|9026|965|−1.218 a+18.269s|

## Qué muestran los stacks y sus límites

|Grupo inclusivo en7027muestras de workers alineadas|Muestras|
|---|---:|
|ORM Django en algún nivel|4993|
|Driver psycopg en algún nivel|3483|
|Templates en algún nivel|1301|
|Espera de aceptación Gunicorn|342|

Grupos solapados; no sumar, no porcentajes de CPU.2654hojas muestran psycopg.connection.wait. También se observan compilación/resolución ORM, prefetch/hidratación, full_clean/validate_submission y renderizado SearchForm.as_p. Imports/traducción aparecen, pero no surge de esta evidencia un único algoritmo dominante que justifique Cython o precalentar todo. Esto respalda investigar demanda/roundtrips y ocupación, **no identifica causalmente el d-1 de otra ejecución**.

--idle incluye esperas y --nonblocking produce muestras parciales/errores;965errores no se omiten. Speedscope agrega pesos y no reconstruye exactamente timestamps porPID después de muestras perdidas. No atribuir porcentajes precisos ni asociar estas pilas a una petición concreta sin entradaWSGI/IDdel mismo proceso. El muestreo también perturba la ejecución; no interpretar sup95como mejora/regresión de producto. [Fuente primaria py-spy](https://github.com/benfred/py-spy).

|Métrica|Último limpio, referencia vigente|Diagnóstico alineado, no comparable|
|---|---:|---:|
|p95HTTPcompleto|1.218890sFAIL|1.856294sFAIL|
|Completadas/errores/timeouts|1200/0/0|1200/0/0|
|p95listado,400casos|1.267949s|1.860044s|
|p95búsqueda,400casos|1.232933s|1.887516s|
|p95ficha,400casos|1.149303s|1.749531s|

## Revisión del antecedente con hilos

[Revisión de admisión anterior](cr09-admision-opciones-seguras-20261015.md) y recibos originales: gthread4x2 y4sync daban≈21s de p95 entonces, con PG≈0.949cores y servicio observado0.879s. El producto cambió materialmente desde aquella población/SQL; no extrapolar ese throughput como capacidad actual. Pero la cola porproceso y el riesgo de liveness Gunicorn23 al llenar worker_connections siguen siendo hallazgos de fuente vigentes. **No reactivar configuración rechazada, no igualar worker_connections=threads, no barrer workers/hilos/conexiones.** Cualquier propuesta de concurrencia necesita revisar progreso/admisión segura y compatibilidad con dependencias congeladas, además de paridad funcional/recursos antes de una nueva carga.

Consulta del grafo histórico con vocabulario gthread/workers/threads:131nodos,30mostrados; truncada, completada con lectura directa. Grafo435bfeb no es perfil actual ni prueba de rendimiento del producto3ba2ec4.

## Decisión y reproducción

No otro cambio de app ni carga limpia encadenada a estos perfiles. Hay evidencia de trabajo repartido entre ORM/hidratación/validación/render y esperaSQL, además de la espera previa medida en ingress. Siguiente investigación acotada: contrastar reducción de roundtrips/construcción del contexto completo y alternativas de concurrencia **con progreso seguro**, sin relajar guardia final, frescura, derechos, cuotas ni dependencias. No hay todavía una solución aceptada al pico inicial; conservar FAIL y todos los artefactos.

Fuentes exactas del adaptador de esta captura, almacenadas como texto para revisión: [run.py](instrumentos-cr09-external-stacks-20261015/run.py.txt), [external_stacks.py](instrumentos-cr09-external-stacks-20261015/external_stacks.py.txt), [probe.py](instrumentos-cr09-external-stacks-20261015/probe.py.txt); hashes enrecibo. Son instrumentos del servidor, no código de app ni instalación en dependencias congeladas. Para reproducir, restaurar esos nombres en artifacts/vps-preparation/cr09-external-stacks-20261015 y usar el comando registrado en runner.json, con unidad propia cr09-external-stacks-* y los límites existentes; no ejecutar fuera del aislamiento ni en producción. Perfil Speedscope completo y logs permanecen en artifacts/local-ci/224937(runIDcompleto enrecibo).
