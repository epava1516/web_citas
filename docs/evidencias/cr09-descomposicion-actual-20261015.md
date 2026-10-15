# Descomposición del estado actual: qué falta medir antes de optimizar

Solicitud posterior del usuario: volver a analizar/despiezar e investigar el estado actual. Producto de referencia392c2c8; último corto limpio FAIL0.919813976s, no aceptación CR09/N3. [Resultados completos](cr09-memo-lifetime-http-20261015.md). Grafo renovado primero al corte documentalcb622dd:11122nodos/44269aristas/476comunidades; semántica actualizada en seguimiento17, matriz83 y dos evidencias. Lectura/consulta limitada y contraste directo de fuentes; el grafo no es un perfil de rendimiento. Tercer lote semántico nativo en el mismo agente graph_update_docs_1, consumo no reportado, historial preservado.

## Presupuesto y población

|Dato derivado del mismo corto limpio,1200requests|Actual|Condición de paso|
|---|---:|---:|
|p95 completo|0.919813976s|<0.8s|
|Requests >=0.8s|79|Como máximo60 para ese percentil/rango yN|
|Ranking nearest-rank del p95|1140|La posición1140 debe quedar<0.8s|

Eso exige desplazar al menos19requests actualmente lentas bajo el umbral manteniendo población y cero omisiones; no significa que una reducción uniforme de19requests o120ms garantice nada. No cambiar algoritmo/denominador ni omitir arranque. La media, los p95 por caso y el p95 de servicio no se suman/restan como si fueran particiones.

Cadena temporal: programación→emisión→conexión/transporte/admisión/parseoHTTP→WSGI→middleware/ruta→validación de filtros→snapshot/dirty/cobertura→conteo/selección→hidratación/guardia nativa→presentación/render→respuesta/transporte→recepción. Ficha y subida tienen rutas diferentes. SQL y GC pueden estar dentro de varias etapas; no sumarlos dos veces.

|Tramo|Qué sabemos actualmente|Hueco que impide atribución|
|---|---|---|
|Generador|1200emitidas/completadas,0omisiones/timeouts/errores; timestamps conservados|No confundir retraso de emisión con tiempo del servidor|
|Antes de WSGI|79lentas se emitieron0–5s; ninguna después|No hay entradaWSGI emparejada porID en el último limpio; no separar TCP/scheduling/admisión desde p95 agregados|
|Servicio Gunicorn|p95 agregado0.314390s frente0.313512s anterior|Filas individuales no conservadas, no se pueden emparejar retrospectivamente con cliente|
|Python/GC|Ciclo añadido por memoizador demostrado y corregido;18controlesPASS|Diagnóstico real de GC anterior corresponde a otra versión y otro arranque de instrumentación|
|SQL|Proyección/preparación acotadas, paridad/guardas y estadísticas de fixture acreditadas en sus alcances|MediasCPU de replays históricos no son demanda actual de los workers bajo concurrencia|
|Render|Antes no se observaba aumento temprano material|Dato histórico, no demuestra coste exacto en392c2c8|
|Fondo|Worker/Beat y subida reales propios se mantuvieron|Su interferencia no debe confundirse con CPU exclusiva de una request|

4sync a20rps ofrecen un presupuesto medio ideal de0.2s de ocupación por worker/request sin acumulación; p95servicio0.314s no permite calcular utilización porque falta la media correspondiente. Afinidad4CPU no demuestra exclusividad del host ni cuatroCPU útiles para cada worker. No concluir hardware, GIL oPGsaturado sin datos de demanda/cgroup actuales. No atribuir diferencias del portátil al código: cambiaba energía al alternar cargador.

## Dos límites de observabilidad encontrados por lectura de código

1. `tests/test_contract_http_load.py` escribe acceso Gunicorn en `tmp_path`, calcula sólo p95 y luego el runner elimina el temporal. Conserva ledger de cliente, pero se pierde el servicio porID. No recuperar ni inventar esos datos ahora.
2. `scripts/benchmark_worker_observer.py:post_worker_init` importa discovery, moderation, moderation_views y PublicationContext antes de atender tráfico. Permite wrappers de fase, pero puede adelantar imports y modificar el heap/arranque que se pretende atribuir. No descartar el diagnóstico histórico: conserva su alcance instrumentado, no demuestra identidad con el arranque limpio.

Gunicorn23 [sync.py](https://github.com/benoitc/gunicorn/blob/23.0.0/gunicorn/workers/sync.py) y fuente instalada: `request_start` se toma dentro de handle_request tras pre_request, después de aceptar/parsear la petición; `%L` no cubre la espera completa del cliente. [Hooks oficiales](https://gunicorn.org/reference/settings/) contrastados con versión instalada. No restar p95cliente−p95Gunicorn para obtener cola.

## Instrumentación correctiva y un diagnóstico definido

Conservar sólo ID sintético, estado y duración de cada acceso dinámico, sin URI/headers/SQL; errores de parser/duplicados explícitos y archivo duradero. No cambiar cronómetro ni aceptación. Nuevo hook opt-in `benchmark_ingress_observer`: entrada/salidaWSGI+CPUthread, executeSQLwall/CPUthread yGC sin importar handlers de aplicación ni envolver reglas/render. Capturar sólo DBs test_promotion_gate_ propias. SelectorCLI explícito --benchmark-ingress-only exige el diagnóstico corto existente con --benchmark-observe-workers; no hereda switches del entorno ni afecta configuración normal.

[8controlesPASS0.55s](cr09-ingress-controls-terminal-20261015.json) verifican imports, privacidad/duplicados/no finitos y protocolo del observador existente. Sin datos reales. Fuentes/limpieza independientes. No son aceptación ni mejora de rendimiento.

Único diagnóstico siguiente: misma mezcla/datos/cuotas/workerBeat/subida de392c2c8, modo ingress y cgroups propios1Hz. Emparejar1200IDs cliente↔WSGI↔servicio, comprobar cuerpos/estados/completitud y clocks. Comparar cohortes0–5,5–10,10–15,15–60; distinguir espera preWSGI, WSGIwall, CPUapp, SQLwall yGCsolapado. No atribuir todo el residuo al socket ni tratar SQLwall como CPUbackend. Instrumentación puede alterar coste y heap marginalmente; no publicar su p95 como una mejora/regresión limpia.

Decisión posterior dependiente del resultado: si domina espera previa, localizar qué crea el atasco inicial y capacidad de despacho; si domina Python/GC, tomar stacks/asignaciones sólo de esos procesos/intervalos; si domina SQL, volver a planes/CPUbackend de familias concretas actuales. Ninguna de estas ramas queda seleccionada por intuición. Sin barridos workers/threads, más hardware, cambioGC o nueva consulta antes del resultado.

[py-spy oficial](https://github.com/benfred/py-spy) permite seguir subprocesses Gunicorn y `--idle` incluye hilos que normalmente excluye; `--gil` omite actividad de extensiones que liberan GIL. `--nonblocking` evita pausar procesos pero admite muestras parciales/errores. Por eso un flamegraph por sí solo no mide la espera previa al worker ni sustituye el emparejamiento temporal; queda como herramienta de segunda fase si CPU resulta dominante. No se solicitan capacidades de producción ni se instala instrumentación en dependencias de la app.
