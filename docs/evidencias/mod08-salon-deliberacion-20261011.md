# MOD08 — Primera sala local de deliberación — 2026-10-11

Sala creada y deliberación terminada. Participantes reales: Codex coordinador, dos
intervenciones de Claude CLI y una de NotebookLM. La segunda solicitud a NotebookLM
(cuarto turno externo) falló; no se reintentó. No hubo cambios productivos, nuevos
benchmarks ni reanudación de capacidad general.

[Manual de la sala](../salon-deliberacion-local.md),
[transcripción completa](../../.ai/rooms/mod08-20261011/transcript.md),
[manifiesto de las fuentes contrastadas](../../.ai/rooms/mod08-20261011/source-manifest.json).

## Base de la deliberación

El [diagnóstico previo](mod08-source-construction-profile-20261011.md) terminó con
5 PASS sobre PostgreSQL/TCP reales, sin cambio productivo. Los controles TCP fueron
812 y 797ms; la muestra con profiler, 1883ms. La candidata de valores primitivos para
Category/Service/Municipality no quedó justificada en ese fixture. La actividad de
`scalar_fields` y `pointer_value` es una pista, no una medida limpia de ahorro.

Se compartieron resultados, código actual, alternativas y opinión propia de Codex.
Claude recibió el código relevante en la primera ronda; en la segunda recibió el
contexto seleccionado y la respuesta íntegra del notebook, sin persistencia propia.
NotebookLM recibió la propuesta y las objeciones de Claude y Codex en la conversación
de esta sala. No se añadieron fuentes al notebook.

## Lo que aporta el contraste

- El recorrido no es exclusivo de `compile_coverage`: hay seis archivos consumidores,
  con ocho sitios externos de llamada y dos llamadas recursivas internas. Ese censo
  estático no identifica qué sitios se ejecutan en el request medido.
- El informe previo conserva los 100 mayores `getstats`, sin grafo de llamadores.
  No se puede recuperar una atribución exacta a partir de ese artefacto.
- Las 101755 entradas/reanudaciones no equivalen a hojas ni a diccionarios creados.
  Los tiempos inclusivos agregados de generadores tampoco se suman para reconstruir
  costes por consumidor. No hay evidencia de 147ms ahorrables.
- Un timer alrededor de la creación del generador no mide su ejecución. Cronometrar
  cada `next` añade eventos; medir toda su vida puede incluir procesamiento del consumidor
  entre yields. Cualquier diagnóstico debe declarar ese perímetro.
- Una función privada para rutas, utilizada sólo donde no se consume `value`, tiene
  menor alcance que cambiar el generador público. Su beneficio y equivalencia siguen
  pendientes; no se ha escrito una candidata.

## Correcciones y desacuerdos preservados

NotebookLM presentó como exacta la atribución con wrappers, volvió a confundir
reanudaciones con diccionarios, introdujo un umbral del 70% y confundió LIFO/FIFO con
el orden real de recorrido. También atribuyó al memo puro de segmentos el riesgo de
reutilizar un valor resuelto: son operaciones distintas. Codex rechazó esas afirmaciones;
Claude coincidió en la segunda ronda. El notebook no confirmó las correcciones finales,
porque su turno de cierre falló.

Claude pidió inicialmente un grafo de llamadores inexistente en el artefacto y sugirió
inconsistencia entre totales inclusivos. Codex corrigió la inferencia: hay dos llamadas
globales a `project_selected` y no conocemos su distribución interna. En la segunda
ronda Claude dijo no tener código para confirmar `deepcopy`; sí se suministró en la
primera ronda y Codex lo verificó directamente. La falta de contexto de ese turno no
invalida la comprobación de la fuente.

El plan de Claude también proponía descontar una cota de intrusión y comparar el coste
absoluto del consumidor con ruido TCP. Codex no acepta esas inferencias: los controles
observan diferencias y dispersión, no un overhead causal por fase que pueda restarse.
El ruido de una comparación de variantes debe medirse con perímetros comparables.

## Decisión de Codex y siguiente experimento propuesto

Se prioriza **diagnóstico de consumidores más coste base de recorrido puro**, sin
optimización productiva todavía. El bloque siguiente se propone como una campaña finita:

1. Fijar fuentes, fixture sintético, perímetros y número de muestras antes de arrancar.
   Reutilizar el método de clones con historial idéntico y dos workers calientes.
2. Obtener conteos estructurales en una pasada independiente de los tiempos: sitios
   activos, filas, hojas, contenedores, profundidad, escapes y longitud de rutas.
3. Hacer control/instrumentada/control con pocos spans wall/CPU de hilo por consumidor
   completo; declarar anidación y trabajo incluido. Registrar GC fuera del cronometraje.
   No parchear indiscriminadamente todos los sitios encontrados por `rg`.
4. Preparar un corpus representativo y casos de borde fuera del tiempo medido. No
   normalizar mediante JSON las subclases, tuplas u objetos que forman contraejemplos.
   Medir el coste base puro sin profiler y con controles A/A alternados; no inferir
   latencia contractual a partir de ese microbenchmark.
5. Sólo si aparece un patrón de coste interpretable y repetible, preparar una candidata
   privada de rutas para un consumidor que únicamente necesite rutas. Antes de adoptarla:
   equivalencia, comparación A/A y A/B intercalada y HTTP en clones equivalentes.

La campaña termina con una tabla de perímetros, conteos, tiempos y limitaciones, incluso
si es negativa o no concluyente. Se descarta la candidata ante divergencias de resultados,
tipos, mensajes, orden del primer error o profundidad; también si el diferencial no se
separa del ruido de controles comparables. No se adopta un corte arbitrario en ms o %.

Se mantienen fuera de esta vía: reescritura iterativa pública, caché de autoridad/cadena,
omisión de validaciones frescas, eliminación de `deepcopy`, nuevos workers o código nativo.
Un diagnóstico posterior no sustituye los objetivos contractuales 2s/5s ni las pruebas
completas de dos casos. **Este experimento no se ejecutó al crear la sala.**

## Ejecución y verificación de la sala

El usuario autorizó expresamente la excepción al adaptador ausente, sólo para deliberar
con Claude sin herramientas ni edición. El consumo anterior permanece intacto en
[desarrollo](../../.ai/tasks/desarrollo.md). El CLI declaró `claude-opus-5-5` en ambos
turnos, una iteración por turno y cero llamadas servidor de búsqueda/fetch. Se conservaron
usage/modelUsage y coste de lista declarado; no se presenta como facturación. NotebookLM
no expone el modelo usado mediante este CLI.

| Turno | Participante | Resultado | Duración local |
| --- | --- | --- | ---: |
| 1 | Claude | Opinión recibida | 74.467s |
| 2 | NotebookLM | Opinión recibida | 45.843s |
| 3 | Claude | Opinión recibida | 46.593s |
| 4 | NotebookLM | Error `query request is invalid` | 2.944s |

El error no permite atribuir la causa a longitud, notebook o conversación. Consulta y
respuesta originales quedan preservadas. No hubo retry ni supuesto consenso final.

Controles del orquestador: **9 tests unitarios PASS**, con dobles para servicios externos
y un subprocess local real para verificar timeout/recolección. Cubren autorización,
límites incluso en fallos, conservación de respuestas, flags sin herramientas, consumo
previo, bloqueo de escritores, cierre y timeout. Las conexiones reales se acreditan por
los tres turnos recibidos, no por esos dobles. Ruff y documentación verificados por separado.
