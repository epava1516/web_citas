# B07 — Backlog nativo y tiempos de despacho

Estado: preparación210 y calibración211 terminadas; backlog pequeño y despacho nativo auditados, sin capacidad grande.

B07-210: escenario funcional de dos marcas nativas preparado: un retirado promocionado y un candidato aún elegible; señales/worker/Beat intactos.77guardas y Ruff PASS. Intervalos publicación–inicio y marca–limpieza separados; calibración211 preregistrada, sin capacidad ni cierre B07;8de18.

## Escenario y autoridad

Reutilizar la topología y el observador calibrado en [209](205-identidad-reposo-observador-b07-20261022.md). Una funcional territorial:10publicados preparados7/3 y2derechos nativos. Retirar mediante bulk update sintético un perfil con derecho, y modificar available_until de otro perfil orgánico que sigue siendo publicable. Ambas escrituras se hacen en una transacción y disparan los triggers reales; no llaman save ni señales Django por ser mutaciones bulk, comportamiento documentado de publication_signals. No afirmar que son acciones del panel. No sustituir ni bloquear ninguna señal, worker, Beat, refresh, regla o callback. READ_REPAIR debe estar desactivado. Dos casos distintos: retirado no elegible y candidato elegible con estado sucio; no confundir backlog con sólo retirada.

Excluir únicamente las dos fichas del ciclo dinámico, no toda la lista sample_ids (a10 contiene toda la cohorte). Conservar manifiesto preparado de10/7/3/2derechos y declarar por separado9visibles tras retirada; no reescribir la preparación como9. El derecho del retirado continúa emitido pero su autoridad de exposición debe denegarlo. No autosubida ni diversidad nacional.

## Calibración211 preregistrada

Una ejecución con --backlog, sólo permitida junto a functional/territorial/service-resources; rechazar short, contractual y upload-calibration. Misma imagen5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede y8CPU8GiBswap0/cuotas/memoria/storage originales,4Gunicornsync/unhilo/workerprefork2/Beat propios, GC intacto y observador host separado diagnóstico (no capacidad limpia). Cotas de observador600s/600muestras/8MiB y señal2048bytes vigentes, tres muestras posteriores.

Antes:18sondas200 originales y8páginas ciudad/conysinphotography/ESEN contrastadas por IDs ordenados con referencia comercial independiente que comparte autoridad nativa y relevancia PostgreSQL. Esperar un nuevo tick Beat real y su ejecución worker SUCCESS; sólo después introducir las dos marcas. Dentro de los5s hasta el inicio objetivo, comprobar otras8páginas HTTP:9visibles sumados por ambos municipios, retirado ausente y candidato elegible conservado; fichas del retirado404ESEN y las dos marcas todavía presentes. Si esas verificaciones exceden el slot, ERROR antes de la carga; no desplazar silenciosamente la fase ni cambiar el presupuesto.

Luego60dinámicas20porcategoría/30poridioma en3s,18slots14URLs y1upload302persistido. La subida normal puede encolar un refresco que repare antes del siguiente Beat: aceptar y registrar el publicador real, sin retrasarlo artificialmente. Tras terminal del generador, reposo funcional2s para las tres muestras y espera de hasta45s para limpieza por worker real; sin llamadas manuales refresh tras mutación. Exigir marcas vacías y una ejecución SUCCESS unida a publicación web/Beat posterior a la mutación con al menos2marcas limpiadas. Otras8páginas reparadas deben coincidir exactamente con las8del estado pendiente. Mantener retirado no visible y candidato publicable por regla nativa.

El analizador de eventos conserva IDs ambiguos/reintentos, publicaciones sin ejecución y ejecuciones sin publicación; no inventa uniones. Publicación–inicio incluye emisor, broker y despacho; no es residencia exclusiva en Redis. mark_to_clear del observador es límite superior según reloj de base de datos al consultar después, no instante exacto de borrado ni edad de una tarea pendiente. No inferir CPU PostgreSQL desde SQL ni causalidad de throttling. Esta funcional cubre corrección y observación pequeña, no coste de49desconocidos, backlog grande o PRODUCTION/checked.

Aceptar sólo si: caso integrado PASS;10preparados/9visibles declarados, dos generaciones explícitas,8páginas frescas+8pendientes+8reparadas y404ESEN conformes;60peticiones y upload persistido, generador válido; reparación worker nativa y métricas emparejadas sin error de snapshot en tarea acreditada; identidades/fases/recursos,GC/Beat/kernel y fuentes/protocolo/628producto/limpieza fresca/Telegram verificados. Conservar cualquier FAIL/ERROR sin repetir automáticamente. Estimación3–5min, ninguna batería adicional en paralelo.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración backlog nativo211' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-functional --territorial --service-resources --backlog --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Auditar terminal y protocolo original antes de editar. B07 sigue abierto8de18; sin short/900 nuevos, proveedores, publicación ni datos reales. Matriz completa: [180](180-matriz-cobertura-b07-censo-geografico-20261021.md).

## Resultado211

B07-211: backlog nativo auditado 1PASS/97,329sJUnit;10preparados/9visibles, dos marcas (retirado y elegible),24páginas HTTP equivalentes y404ESEN.60éxitos/1upload; worker real repara2marcas, despacho11,775ms y marca–limpieza≤5,505s observados.628producto, cuotas, limpieza y Telegram confirmados. Funcional pequeño, sin capacidad ni cierre B07;8de18.

Corrida `20261022-010450-2e928651`, entorno VPS `20261022-010450-8513fe75`. [Auditoría terminal](evidencias/b07-backlog211-native-dispatch-20261022-audit.json). Prerrequisito rehash de seis artefactos209, producto628intacto, delta declarado de ocho rutas de instrumento y77guardas/RuffPASS; protocolo original y SHA/mapa archivados antes de lanzar. Caso integrado1PASS/0FAIL/0ERROR/0SKIP,97,329sJUnit; no se suma como78casos con las guardas.

8páginas frescas10visibles; dos generaciones reales de PostgreSQL, retirado promocionado no elegible y orgánico todavía publicable con estado sucio;8páginas pendientes9visibles con IDs/orden nativos,404ESEN del retirado y ambas marcas aún presentes. Las comprobaciones concluyen antes del target Beat+5s.60dinámicas20porcategoría/30poridioma,18slots14URLs/18sondas200 y upload302persistido. Después,8páginas reparadas idénticas a las pendientes y ambas marcas limpiadas, sin refresco manual ni reemplazo de tareas.

La reparación acreditada fue publicada por web tras la mutación y ejecutada por worker real SUCCESS: dirty_before2/dirty_after0/cleared2. Publicación–inicio11,775ms, ejecución200,147ms; límites superiores marca–limpieza5,497/5,505s del observador en reloj de base de datos. No son residencia exclusiva en Redis ni instante exacto de borrado. El ledger final conserva2parejas y3ejecuciones sin publicación observada (captura parcial del emisor durante preparación), sin IDs ambiguos ni publicaciones sin ejecución; no se inventan las uniones faltantes. La tarea acreditada sí tiene pareja completa y no error de snapshot.

Generador p95/p99/máximo4,198/13,104/13,104ms;8CPU8GiBswap0, memoria superior runtime1352204288bytes/storage4865392640bytes.70muestras62previas/5carga/3reposo, identidades mínimas y deltaCPU posterior verificados. GC/Beat nativos y4Gunicornsync/unhilo se mantienen. Observador host fuera del presupuesto del runtime:1,882sCPU de hilo en172,970s de vida total yRSS de proceso23347200bytes al cierre (no pico ni exclusivo). Sin causalidad de CPU ni comparación de velocidad con otros cortes.

Fuentes/protocolo revisados antes de editar; launcher retirado por PID/startticks, inspección fresca sin contenedores/redes/volúmenes de esa etiqueta y recibos Telegram confirmados. Sin reintento de ensayo o auditor, ninguna prueba paralela. El resultado cubre dos marcas a10perfiles: no backlog de49candidatos desconocidos, recursos a10000, edad de todas las colas ni escenario PRODUCTION/checked. No capacidad general ni cierre B07.
