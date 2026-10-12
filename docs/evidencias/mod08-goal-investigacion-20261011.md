# MOD08 — Goal de investigación: estabilidad y dictamen — 2026-10-11

Solicitud ejecutada: [prompt original](../../.ai/rooms/mod08-goal-gate-20261011/objective.txt).
Condiciones en [seguimiento](../17-seguimiento-desarrollo.md#contrato-del-próximo-goal-de-investigación-de-rendimiento--2026-10-11)
y [plan previo](mod08-siguiente-plan-20261011.md). [Muestras completas](mod08-stability-20261011.json)
y [deliberación íntegra](../../.ai/rooms/mod08-goal-gate-20261011/transcript.md).

## Resultado

**Investigación acotada terminada con dictamen; ninguna optimización productiva aplicada.**
El bloque de controles es válido, pero no supera la compuerta diagnóstica de estabilidad.
No se ha localizado una nueva candidata accionable sustentada por los datos disponibles.
No se alcanza ni se declara la aceptación de rendimiento de MOD08. La ausencia de candidata
no demuestra imposibilidad técnica de optimizar el proyecto.

| Indicador, 20 controles | Mediana | P10–P90 | Dispersión / mediana | Deriva primeras 5 / últimas 5 |
| --- | ---: | --- | ---: | ---: |
| TCP completo | 1556.081ms | 1493.947–1619.434ms | 8.064% | 1.381% |
| CPU del hilo WSGI | 877.342ms | 810.967–914.700ms | 11.824% | 1.684% |

Umbral predeclarado ≤10% para dispersión y deriva en ambos indicadores. **Compuerta FAIL
por CPU**. No cambiar el umbral, excluir muestras ni restar GC para convertirlo en PASS.
No son pruebas de hipótesis ni un p95 contractual.

## Ejecución y verificación

Runner `20261011-141107-bc244cec`: 4 PASS, 0 fallos/errores/skips, 216.066s JUnit.
Tres unitarios comprueban cuantiles/interpolación, deriva/dispersión y presupuesto exacto;
una integración PostgreSQL17/Redis propios y TCP real ejecuta el arnés. Fuente HEAD
`7e04016d8ece6cf52388e283eb06cf0a6040fd2b` con cambios locales preservados.
1231 entradas del mapa completo coinciden exactamente antes de escribir resultados.
Checks Ruff, documentación, Django, migraciones y construcción nativa correctos.

Dos warmups descartados y veinte POST medidos, todos con el mismo PID de un worker sync.
Kernel **canónico** native-sealed y manifest idéntico comprobados en el worker, fuera del
reloj WSGI; no confundirlo con un backend nativo de unseal, que aquí usa Fernet y JSON.
Fixture 1500 revisiones y selección 16777214 bytes; 64 POST de preparación generaron
548 eventos y 256 lecturas. Cada clon tenía esos mismos conteos antes, y se comprobó
independientemente el commit con 556 eventos y 260 lecturas después.

El backend de verificación de identidad del fixture es simulador; no se acredita ningún
proveedor externo real. PostgreSQL y el transporte HTTP sí son reales.

Sin cProfile, observadores SQL, callbacks GC, spans internos, GC forzado/deshabilitado,
transacciones externas con rollback, caché de autoridad ni cambios productivos. Sólo se
amplía el helper test-only clone_server con workers opcional, conservando el default 2.
No segunda tanda ni repeticiones para obtener una compuerta favorable.

TCP incluye telemetría previa del worker y puede terminar antes del cierre WSGI. WSGI
incluye consumo/cierre de respuesta y conexión; kernel/RSS/loadavg y estadísticas GC se
capturan fuera de ese reloj. Las estadísticas PG se leen por conexión owner independiente,
fuera del POST, antes/después de cada muestra. Esa conexión de comprobación puede calentar
algunas páginas: no se afirma identidad de buffers entre clones. GC no se modifica.
Un worker difiere del escenario anterior de dos y de la topología contractual; no atribuir
las diferencias absolutas entre ensayos a código. Otros servicios existentes del host
permanecen intactos; recursos propios no equivalen a aislamiento físico completo.

Inventario independiente por label del runner no muestra contenedores propios, y los
handles/PIDs de runner, pytest y Gunicorn ya no están presentes. No queda carga propia.

## Deliberación y decisión

Claude recibió datos, código relevante, hipótesis y negativas previas; propuso diagnosticar
GC. NotebookLM rechazó la consulta extensa como invalid request (negativa conservada) y
respondió a una reducción explícita; recomendó cierre. Claude revisó luego la evidencia
sobre construcción directa y también propuso cierre. La excepción permitió sólo revisión
sin herramientas ni edición; las dos invocaciones y su consumo declarado están registradas
en .ai/tasks/desarrollo.md. No se contrataron servicios ni se alteraron fuentes del notebook.
El CLI no identifica el modelo NotebookLM. El consenso no sustituye pruebas.

 el grupoGCgen2 correlacionaCPU903.394vs826.489ms(11vs9muestras), no mide duraciónGC ni demuestra causa del salto históricofactor2. Ningún modelo puede clasificar ese salto como entornoyaexplicado. Sourcecopyconstruccióndirectaobservada no revela dict→dictprescindible, pero no demuestra que todaasignación sea inevitable ni que estructuras alternativas cambienelpayload necesariamente. TimersGC seríanintrusivospero podríanmedir intervalos aproximados; rechazar aquí por falta de decisiónproductiva accionable, no por imposibilidaduniversal de instrumentar. No inferir ausenciafuga de derivatemporal pequeña/RSS ni detenerservicioshost. Cortes50%,8%,30ms de revisores son inventados, no adoptados;gc.disable/freeze/tuningglobal fuera alcance.

Vías con evidencia negativa previa y causa de no reabrir: SQLinlineHTTPbeneficiopequeño/colapeor;CategoryprimitiveCPU~5msfixture;recorridosescalarA/A23msy4501punteros6ms sinahorro; memoautoridad/lecturaspurgables prohibidas porcontrato, no propuestas válidas. No repetirprofiler intrusivo sinpreguntanueva. source_copy mayorentreconsumidoresobservados, no principalcuellodemostrado. Fases no cubiertas y factor2 son incertidumbres pendientes, no candidatasproductivaspor sísolas.

Criterios concretos para nueva ventana (no activarlaautomáticamente): reproducción independiente que identifique un cambio efectivo de fixture/versiones/configuración/backend entre regímenes; asignación/copia temporal redundante localizada y costeobservado significativo; errorfuncional/fuga demostrada porretención de objetos; o necesidad de cambiarcriterios/topologíacon autorizaciónexplícita. Reabrir con hipótesis, mecanismo y experimento predeclarados. No subirumbrales ni quitarfirmas/frescura ni modificarhostglobal paraobtenerPASS.

Entrega: originales y evidenciasnegativas preservados; sólo instrumentos test-onlyyworkersopcionaldefault2;ningunacandidataproducciónporrevertir. Goal cerrado por su objetivo explícito de investigación acotada ydictamen, no por aceptación de rendimiento. MOD08 completo continúa pendiente fuera de este goal.


[Auditoría de cierre por requisitos](../../.ai/rooms/mod08-goal-gate-20261011/completion-audit.json):
objetivo original conservado, fuentes de aplicación/tests intactas, muestras y revisores
comprobados, compuerta negativa preservada y procesos/recursos propios ausentes.
