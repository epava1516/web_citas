# B00-336 — Informe del grafo histórico y fidelidad de sus capturas

Fecha: 2026-10-24. Conciliación documental y contraste estático seleccionado.

B00-336: 287 de 295 fuentes únicas conciliadas; quedan ocho fragmentos históricos de nodos y relaciones. Incorporado el informe Graphify del11/10 y contrastada la estructura de sus48.401registros, sin acreditar aún su lectura semántica. Cuatro fragmentos no son JSON estricto por controles dentro de cadenas; originales preservados. Sin cambios funcionales ni nueva aceptación. B00 sigue abierto; nueve de18puntos beta cerrados y B15 opcional.

## Informe leído y alcance

Una lectura nativa nueva de sólo lectura cubrió los95.499caracteres del informe `source:uv1i1nge55jfsomsga3x` en ocho intervalos contiguos de hasta12.000caracteres Unicode por salida, sin truncamiento declarado. SHA256 del texto `fd21ecd46d3b5354a50948848afe7ca3df417fc598fc833678e2e50c7a150356`; raw `81f556537d14d59d750928255735b86ea93ee91481e80f23cdbf5cd1c81ce1bd`. El principal contrastó dos citas con sus posiciones/contextos y revalidó integridad de las295capturas. Se conserva un extracto seleccionado del informe del lector, no su transcripción completa.

La tarea del principal conservó por error una huella de Django en el ejemplo REPORT_FORMAT, aunque CONTEXT.assigned_part y los metadatos de fuente eran correctos. El lector señaló la discrepancia y devolvió la huella real, que coincide con el original. Se conserva la tarea y la nota de errata; no se alteró un campo reportado ni se exigió repetir lectura.

El informe corresponde a web_citas,11/10/2026 y base7e04016d. Sus9.171nodos,39.230relaciones,314comunidades y5.401relaciones inferidas son cifras históricas. Leer el informe no equivale a leer todos los registros del grafo. Sólo muestra262comunidades y omite52pequeñas; sus listas de nodos están abreviadas. El modo cluster-only no proporciona estadísticas de archivos. La fecha, el título y la referencia de commit no prueban frescura actual ni identidad byte a byte del productor.

Describe publicación, derechos, huellas, portabilidad, recuperación, borrado, avisos privados, tareas, pruebas de capacidad y documentación acumulada. Títulos de pendientes, actas y estados de fechas diferentes no crean una cola vigente ni demuestran contradicción funcional actual. Sus propuestas e índices no incorporan los documentos citados a la cobertura de lectura.

## Qué dicen y qué no dicen las métricas

User, Photo y RightsAction aparecen como puentes de revisión; PublicationContext tiene cohesión0.0250155183116077. Centralidad o baja cohesión no son defectos ni órdenes de refactorización. El reporte enumera1.154símbolos con cero/una conexión y3.183al incluir archivos/conceptos/rationales; son preguntas sobre cobertura, no3.183funciones rotas.

Las5.401relaciones INFERRED coinciden con los fragmentos y su confianza media0.9253008702092206redondea a0.93. EXTRACTED e INFERRED son clasificaciones de extracción, no ejecución ni autorización demostrada. Todas las relaciones de esos fragmentos declaran origen ast, incluso las inferidas; no se atribuyen automáticamente a razonamiento de un LLM. Ausencia de ciclos detectados no prueba ausencia de acoplamiento dinámico. Los ceros de coste del informe no borran consumo anterior ni miden el coste nativo actual.

## Ocho fragmentos: inventario estructural, no aceptación semántica

Se analizaron estructuralmente17.857.641caracteres: dos capturas de nodos y seis de relaciones. La combinación contiene9.171IDs de nodo únicos y39.230relaciones,314comunidades,122autorrelaciones, cero extremos ausentes y cero duplicados exactos de relación. Son propiedades de la representación capturada; no prueban conservación de todas las relaciones extraídas originalmente o corrección de la aplicación.

| Captura | ID | Registros | JSON estricto |
| --- | --- | ---: | --- |
| Nodos1/2 | `source:gbdn3ox1asszgxe8nytq` | 5000 | Falla en carácter224101 |
| Nodos2/2 | `source:a3xmiqi2izexc6m6pgni` | 4171 | Falla en carácter14897 |
| Relaciones1/6 | `source:xuawvq62yt440dmn8fbo` | 7000 | Válido |
| Relaciones2/6 | `source:4kdylefbew2cj0asrzsm` | 7000 | Falla en carácter1458397 |
| Relaciones3/6 | `source:85qbqz8zf80db1h5p6dn` | 7000 | Válido |
| Relaciones4/6 | `source:0cyo4xbdbok9a93yvxvl` | 7000 | Válido |
| Relaciones5/6 | `source:18xdl1s69ma44vpy12vz` | 7000 | Falla en carácter1884423 |
| Relaciones6/6 | `source:g0i02979iw5jxwwamybk` | 4230 | Válido |

Posiciones Unicode absolutas en full_text. El encabezado de los fragmentos dice «sin perdida de atributos», pero cuatro contienen controles sin escapar dentro de cadenas. Se identifican442campos en202registros, entre ellos rutas y etiquetas con saltos de línea en nombres init. No se reconstruye un supuesto __init__ ni se corrigen atributos por intuición. Los originales capturados permanecen intactos; no se acredita que sean los bytes canónicos del graph.json eliminado anteriormente.

El parser estricto rechaza esos cuatro textos. Un decoder acotado permite conservar literalmente sus controles para inventariarlos: rechaza claves duplicadas/constantes no JSON y no ejecuta datos. No convierte los originales en JSON estricto ni certifica fidelidad al grafo productor. El [análisis19](19-graphify-analisis-local.md) incorpora una aclaración reversible que conserva íntegro su texto anterior y continúa fuera de la selección semántica activa.

Se preparó una proyección con diccionarios de valores y esquemas por registro:4.406.180bytes en conjunto. Conserva todos los atributos escalares decodificados, tipos, orden de campos y campos ausentes; un mapa conserva posición y SHA de cada registro y permite recuperar el texto original. El principal verificó independientemente los48.401registros, huecos/prefijos/sufijos y reconstrucción de cada atributo. La proyección reversible es preparación, no lectura semántica ni restitución de los bytes originales del productor. Sus ocho fuentes permanecen SEMANTIC_REVIEW_PENDING; tampoco recibe crédito la proyección parcial antigua del corte303.

## Contraste actual seleccionado

Nueve archivos actuales y diecinueve literales contrastados; sin ejecutar aplicación, SQL o pruebas funcionales. [PublicationContext](../apps/listings/public_validation.py) y [visibilidad](../apps/listings/moderation.py) siguen siendo puntos de integración; el grado del nodo no justifica dividirlos. La guarda llama la [validación de envío](../apps/listings/submissions.py), que aplica el [contrato romántico](../apps/listings/profile_contract.py). La revisión legacy profesional no adquiere publicación por aparecer en el grafo histórico.

La [autoridad de denuncias](../apps/safety/report_authority.py) relee cuenta, permiso, sesión y MFA; la [consulta privada](../apps/safety/views.py) la invoca tras el bloqueo y antes de devolver información. La [prueba existente](../tests/test_report_inspection_authority.py) declara variantes de revocación y respuestas403. Son comprobaciones de código/aserciones, no una nueva ejecución ni demostración de seguridad global. La corrección del corte322 conserva su evidencia propia.

La cola de denuncias materializa candidatos y aplica permitted después; permanece como candidato de optimización de B08, sin cambio ni coste nuevo medido en este corte. Se distingue de la cola de reclamaciones acotada a100candidatos. No se cambian permisos, conflictos de interés, orden o paginación a partir de una métrica histórica.

El [acta16](actas/16-beta-b07-aceptacion-local-20261023.md) conserva aceptación local B07 y límites; las métricas antiguas del grafo no sustituyen esos resultados ni amplían su capacidad. [Contrato14](14-contrato-funcional-v1.md) mantiene el producto romántico y B15 opcional con decisiones de privacidad separadas. No se implementan recomendaciones ni se decide base de datos frente a objetos desde esta revisión.

## Integración y continuación

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa286a287disposiciones por el informe, no por los ocho fragmentos inventariados. Verificador fijado a base286SHA210c0f78a43810df8edc64a628ac796cd1c7411ea8e114d19741baf74b143d29, escritura atómica y permisos conservados; no sobrescribe otro corte. Artefactos `artifacts/beta-promotion-fix-20261020/b00-336-*`, scripts de inventario y verificación336. Se preservan fallos exploratorios de lectura JSON estricta como hallazgos de representación, no fallos funcionales ni reparaciones silenciosas.

Grafo389 revalidado antes del análisis; semántica dirigida390 integra los conceptos de este documento y citas al código actual. No se importa el grafo antiguo ni se restaura una copia retirada por el usuario. Sin nuevo AST global, detección global de comunidades, semántica exhaustiva o HTML global. El grafo actual es JSON estricto y no contiene controles en rutas/etiquetas; ello no acredita todos sus valores o completitud dinámica.

Quedan ocho fuentes y17.857.641caracteres con disposición semántica pendiente. Continuar con sus atributos/relaciones y procedencia mediante rangos y contexto verificables; usar la proyección sólo si se demuestra cobertura semántica contextual completa, sin convertir un parseo o una muestra en lectura total. B00 sigue abierto hasta conciliación y consolidación requeridas. Nueve de18puntos beta cerrados; B15 opcional. Cero nuevas invocaciones ClaudeV1; ocho históricas y consumo conservados, sin estimación nativa. Sin publicación, contratación, gasto o datos reales. Corte anterior: [conciliación294](294-conciliacion-ecmascript-django-b00-20261024.md).
