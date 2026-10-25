# N01 — aceptación técnica local de bases, criterios y planificación

25 de octubre de 2026. Codex acepta N01 como bloque de planificación y criterios anteriores a los candidatos, según la salida de roadmap341: base comparable o razón concreta de nueva medición, y ficha de cada lote antes de ejecutarlo. **N00 y N01 aceptados:2/13bloques obligatorios.** N02–N11/N15 continúan pendientes; N12–N14 condicionados. Proyecto en alfa.

No se acepta rendimiento de todos los recorridos ni se elimina una medición pendiente. [Criterios354](354-n01-f-criterios-comparacion-escenarios-20261025.md) fija el presupuesto comparativo antes de cualquier candidato de aplicación, conserva objetivos absolutos y exige congelar la referencia faltante antes de construir/comparar ese candidato. [Matriz individual](evidencias/n01-f-criterios-escenarios-20261025.json) preserva19escenarios S02–S09 y S01 conserva sus protocolos/resultados. Las28familias mantienen la disposición deN00.

## Evidencia y alcance de aceptación

| Requisito N01 | Evidencia y decisión |
| --- | --- |
| Escenarios, fuentes, datos, roles, modalidad, oráculos y límites | Matrices352/354 con19fichas,49referencias de acción válidas del censo, selectores/parametrizaciones y SHA;93citas revalidadas en352. S01:344/346/348 y resultados345/347/349. No se confunde representación de familia con cada acción probada. |
| Criterio anterior al candidato y base o motivo concreto |354selecciona costes por etapa `candidato≤referencia equivalente`, reducción estricta para afirmar optimización y no empeorar tiempo de etapa; incertidumbre temporal es inconclusión. Tabla individual de354identifica referencia o razón de medir cada escenario; nunca se acepta por fuente un coste no ejecutado. |
| Presupuestos heredados preservados | Mezcla pública p95<800ms/errores<1% sólo en su protocolo; MOD09 cobertura p95≤2s y JSON/binario por paquete p95≤5s, FAIL y excepción provisional sin ampliación. No se adoptan automáticamente números de111/338. |
| Fichas por lote previas a ejecución y separación QA/servicio |344/346/348/350/352, congelaciones y auditoríasA–E: PostgreSQL propio, fuentes/recursos/selección declarados, muestras instrumentadas separadas de preparación/pytest y limpieza/Telegram verificadas. Los siguientes lotes deben completar esa misma ficha antes de medir. |
| Muestreo y límites | A:2peticiones;B:60;C:120;D:109HTTP;E:18servicios. Poblaciones, etapas y condiciones distintas, sin sumar sus tiempos ni inventar percentiles/capacidad. S01y19fichas mantienen huecos explícitos de carga, navegador, colas, cardinalidad y operación. |
| Revisión independiente y decisión primaria | Revisión documental preservada en evidencia: salida técnica suficiente; único hallazgo de cierre era tabla global antes/después. Esta acta la completa. Codex contrastó criterio contractual, acciones/familias, SHA y reportes originales; revisión de tercero no sustituye auditoría ni autoridad primaria. |

Las frases «N01abierto» en345–354 y sus evidencias identifican cortes anteriores; esta decisión posterior resuelve el bloque de planificación. Sus límites de medición y sus pendientes de ejecución siguen vigentes. No se reescribe ningún FAIL ni se contabiliza una fila de documentación como prueba de producto.

## Antes y después del bloque N01

Base documental:343/N00 y las propuestas previas a cada lote. Final: criterios354, evidenciaA–E y esta acta. Las versiones instrumentales se identifican por sus congelaciones: A ed16134;B72c5514;C0d2ade5;D745b0a6;E568ab46. Son instrumentos sobre la misma aplicación, no cinco candidatos de optimización.

| Escenario | Antes de N01 | Después de N01 | Medida/evidencia y límite |
| --- | --- | --- | --- |
| S01/N04 | Listado agregado y segmentos por concretar | FichasA/B/C; referencia de crecimiento, segmentos ES/EN y preparación state | A2HTTP10/100;B60HTTP;C120HTTP100publicados. Preparación incluyeVACUUM/ANALYZE; sin causalidad de código ni carga pública acreditada |
| S02-A/N07 | Lifecycle como propuesta sin observación actual por operación | BaseHTTPD, criterio comparativo, cola/Beat separados |12+6operaciones de disponibilidad/renovación; reintento no equivale a mutación |
| S02-B/N07 | Estados/worker propuestos | PreparaciónC como base parcial y ficha de mutaciones/retraso por concretar en su lote | No todas las mutaciones ni worker medidos; motivo y presupuesto comparativo fijados antes del candidato |
| S03-A/N09 | Oráculos de revisión independiente | Ficha y criterio de snapshot/validación/transacción | Sin base temporal comparable; medir etapa, excluir duración humana |
| S03-B/N09 | Outbox/simulador/recuperación como propuesta | Etapas enqueue/claim/adapter/commit, criterio y negativos conservados | Sin base temporal comparable; simulador no acredita entrega real |
| S03-C/N09 | Purga acotada propuesta | Ficha de expirados/frescos/evidencia emitida y continuación | Sin base comparable actual; medir lote útil sin cronómetro global de QA |
| S04-A/N06 | Alta/login/CSRF con fuentes de QA | BaseHTTPD y criterio por rama/estado |2signup negativos+10activación/login+10CSRF/throttle; no agregar éxitos/denegaciones como misma operación |
| S04-B/N06 | Edición/revisión y rechazo como propuestas | BaseHTTPD y señal de coste para atribuir antes de candidato |11+8operaciones;listing_start116/124SQL en estados distintos, no N+1 demostrado |
| S04-C/N06 | Representación por fuente funcional | Ficha específica de agencia/asignación/MFA/revocación | Sin base temporal comparable; no extrapolar titular individual |
| S05-A/N05 | Diagnóstico de galería disponible como fuente | Modalidad navegador, contexto/versiones y criterio de bytes/requests identificados |8fotos,ES/EN,móvil/escritorio en fuente; reutilizar sólo testigo equivalente o medir; no latencia actual inventada |
| S05-B/N05 | Flujo de subida/previsualización por fuente | Ficha de navegador y retiro propio | Sin base comparable actual; Client no prueba interacción navegador |
| S06-A/N02 | DeudaMOD09 y excepción temporal | Mismos objetivos/FAIL, etapas y paquete>64MiB diferenciados | Sin ahorro causal demostrado; medir/atribuir escenario exacto y conservar excepción sin ampliación |
| S06-B/N02 | Autorización/consumo por fuente | Ficha que separa permiso de proxy/entrega | Sin base comparable actual de ese desglose; no trasladar SLO a otro endpoint |
| S07-A/N03 | Detector/densidad como propuestas | Cohortes distintos1000/densos100, referencia exhaustiva y criterios | Reutilización condicionada a identidad o nueva base; no80000ni cola real |
| S07-B/N03 | Subida eager funcional | Ficha receive→cola→process→ready con modalidad real requerida | Sin base comparable de cola/worker; eager no la sustituye |
| S08-A/N08 | Favoritos por fuente | BaseHTTPD y criterio de pertenencia/retirada/idempotencia |11operaciones; crecimiento1/10/100pendiente de manifiesto propio |
| S08-B/N08 | SEO/sitemap por fuente | BaseHTTPD por rama/idioma/retirada |17operaciones; no crecimiento grande acreditado |
| S08-C/N08 | Pedido simulado por fuente | BaseHTTPD por idioma y criterio de efecto único |11operacionesES+11EN; sin cobros/proveedores reales |
| S09-A/N10 | Diagnóstico vacío como propuesta | BaseE y presupuesto≤50SQLpor llamada en escenario exacto |18servicios,0/10/100PublicationDirty. Primera/mediana5/rango en353; no otras tablas/restore/capacidad |
| S09-B/N10 | Fuente de restauración2×2 | Ficha de backup/clave y no resurrección | Sin base temporal comparable actual; restaurar o justificar testigo equivalente antes de candidato |

No hay cambio de aplicación ni un porcentaje global de mejora. Las diferencias de esta tabla son cobertura, conocimiento y criterios. Donde no existe referencia equivalente, se declara «sin base comparable» y se exige obtenerla antes del candidato. Las observaciones temporales/SQL individuales permanecen en345/347/349/351/353; no se convierten en antes/después de código por esta aceptación.

## Siguiente ejecución

N02–N10 pueden preparar lotes independientes una vez satisfechas sus fichas y referencias, según impacto/riesgo y coste. Primera señal cuantificada para analizar: S04-B/N06, coste de iniciar revisión publicada y de corrección, preservando instantánea/bytes/autoridad. Completar su atribución y presupuesto exacto antes de modificar la aplicación; no asignar prioridad por centralidad ni frecuencia inventada. Los restantes bloques y sus familias continúan obligatorios.

Antes del siguiente hito: integrar semántica de354/esta acta y seguimiento, verificar fuentes y grafo; emitir prerregistro focal del candidato/medición correspondiente. N11 y N15 mantienen conciliación, reconstrucción final del grafo y diferencial del inventario, con sus tablas al cierre.
