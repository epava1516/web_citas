# B07 — Integración y calibración del observador kernel

Estado: integración206 y calibración207 terminadas; instrumento funcional auditado, sin aceptación de capacidad.

B07-206: observador host integrado sólo en calibración funcional; 62 guardas y Ruff PASS. Inventario de procesos por cgroup propio incluye docker exec; identidad del launcher y de seis contenedores verificada. Calibración207 prevista con 10 perfiles, sin capacidad ni cierre B07; 8 de 18.

## Alcance y presupuesto previo

La opción `--service-resources` de run_vps_capacity y `--beta-http-service-resources` del controlador sólo admiten modo funcional, sin calibración de quince uploads. Se rechazan short, contractual y preflight. No cambian cuotas, trabajadores ni aplicación. El observador es un hilo del lanzador host, fuera de las cuotas8CPU/8GiB del runtime: sus datos son diagnósticos instrumentados, nunca una medición limpia de capacidad. Registrar su CPU de hilo, CPU/RSS de proceso host e intervalo; no atribuir todo el proceso al colector ni afirmar overhead causal.

Los seis contenedores conservan8CPU/8GiB/swap0 y la imagen local inmutable sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede. El lector comprueba launcher-started con PID/startticks propios y conjunto exacto de recursos; después inspecciona únicamente seis nombres de la ejecución. No enumera procesos del host: lee cgroup.procs de hojas verificadas, máximo256PID por servicio, y revalida cada pertenencia. Así incluye procesos docker exec que no sean descendientes del init. Procesos desaparecidos quedan no observados, nunca CPU cero. Contadores por hoja y procesos incluyen toda actividad del servicio, preparación y observación; las lecturas son secuenciales, RSS puede contar páginas compartidas dos veces y memory.peak es acumulado.

Máximo600s y600muestras, 8MiB de salida JSONL propia; periodo nominal0,5s tras señal, inspección Docker acotada10s por intento sólo hasta identificar la topología. La señal privada de hasta2048bytes conserva tres límites monotónicos. Cada muestra registra señal antes/después e inicio/fin: excluir del cálculo por ventana muestras que crucen límites. Cerrar el hilo antes de la limpieza del lanzador; cualquier error de observación invalida el resultado de su calibración sin impedir limpieza ni convertirlo en PASS.

## Calibración207 preregistrada

Una sola ejecución funcional territorial:10perfiles publicados7/3,2derechos nativos,18slots14URLs,60dinámicas en3s a20RPS y1upload302persistido. Misma preparación nativa, estadísticas, cuatro Gunicorn sync/un hilo, worker/Beat reales y fase+5s. Fases: before_arrivals después de arrancar servidor y antes de sondas; arrivals_and_drain inmediatamente antes del generador; idle_after después de su terminal. Pausa funcional de2s tras esa transición para permitir muestra final; no se añade al intervalo del generador.

Aceptar sólo calibración del instrumento si: un caso nativo PASS; tres fases observadas y límites ordenados que encierren origen/fin del ledger; muestras antes/durante/después, identificadas con la misma ejecución; 60peticiones y mezcla20porcategoría/30poridioma,18sondas200 y upload persistido; controles kernel y políticaGC/Beat intactos; JSONL acotado y summary terminal coherente; fuentes/protocolo congelados,628producto intactas, recibos Telegram y limpieza fresca. Conservar ERROR/FAIL sin repetición automática. Si el observador no puede leer /proc o cgroups, resolver desde evidencia del fallo; no elevar permisos ni atribuir simulación a Docker.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración observador kernel207' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-functional --territorial --service-resources --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Congelar fuentes durante ejecución. Auditoría posterior antes de editar este protocolo. Estimación2–4min, no lanzar otras baterías. No short, confirmación ni900automáticos. Estados/backlog/PRODUCTIONchecked y recursos a volumen grande permanecen pendientes de [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md). [Lector y canal previos](203-lector-recursos-kernel-b07-20261022.md). Los primeros avisos I001 de imports se conservan; correcciones de orden sin cambio de comportamiento verificadas por Ruff final.

## Resultado207

B07-207: calibración Docker del observador auditada 1PASS/93,336sJUnit, 10perfiles7/3 y2derechos,60éxitos20porcategoría/30poridioma y1upload.69muestras:62previas/6carga/1posterior completamente dentro de sus fases; fuentes628producto, cuotas y limpieza confirmadas. Observador host fuera de presupuesto, sin capacidad grande ni cierre B07;8de18.

Corrida `20261022-003814-d8291aba`, entorno VPS `20261022-003814-0431e93e`. [Auditoría terminal](evidencias/b07-resources207-kernel-functional-20261022-audit.json). Protocolo original, SHA y mapa congelado archivados antes del lanzamiento. Prueba nativa 1PASS/0FAIL/0ERROR/0SKIP;18sondas200,18slots14URLs,mezcla y orden conciliados. Generador p95/p99/máximo2,991/17,279/17,279ms, memoria superior runtime1347985408bytes, storage4865392640bytes,8CPU8GiBswap0 comprobados.628fuentes apps/config/templates iguales. GC y Beat/worker reales preservados; limpieza exacta Docker y ausencia de recursos etiquetados revisadas de nuevo tras salida real del launcher.

El historial de tres límites concuerda con el ledger: origen después de arrivals_and_drain y terminal antes de idle_after.69muestras completamente incluidas:62before_arrivals,6arrivals_and_drain y1idle_after. El intervalo CPU entre las seis muestras de carga cubre aproximadamente2,57s, no toda la ventana: app≈2,008cores, PostgreSQL≈0,732cores; son ejecución de servicio, no CPU por petición ni prueba de causa de latencia. La única muestra idle_after no permite deltaCPU posterior. RSS puede duplicar memoria compartida, memory.peak acumulado no es pico sincronizado. No se ha medido edad de colas.

El hilo observador consume1,654sCPU en172,894s de vida completa (incluida espera de preparación); RSS del proceso host al cierre23252992bytes, no memoria exclusiva del hilo ni pico. El proceso host sigue fuera de las cuotas del runtime y se declara separado; no extrapolar estos datos a una medición limpia o al volumen10000. El lector verificó ID/cgroup/PID en ejecución; no se archivó una copia íntegra de Docker inspect para revalidar después identidades de contenedores ya retirados. Persistir un manifiesto mínimo de identidad antes de ampliar alcance.

Primer auditor EXIT1 por ModuleNotFoundError al importar helper scripts después de verificar ledger; corregida sólo ruta del auditor ignorado, segundo intento PASS. No se repitió TCP ni se cambiaron fuentes del ensayo. Recibos de ambos resultados conservados y Telegram terminal confirmado. Estados/backlog, recursos a escala y PRODUCTION/checked siguen pendientes.

Actualización posterior: la identidad mínima archivada y el intervalo posterior se verifican en [209](205-identidad-reposo-observador-b07-20261022.md). La limitación histórica de207 permanece; no se añade retroactivamente evidencia a esa corrida.
