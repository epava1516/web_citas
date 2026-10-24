# B00-333 — Referencias de documentación y herramientas

Fecha: 2026-10-24. Lectura de capturas históricas, contraste local y aclaración documental.

B00-333: 279 de 295 fuentes únicas conciliadas; quedan 16 de arquitectura. Incorporados el catálogo de documentación y cuatro referencias de herramientas; aclarado el inventario tecnológico histórico y contrastada la instalación local de Graphify. Sin cambios de aplicación o pruebas, defecto funcional nuevo demostrado ni nueva aceptación. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Lectura y procedencia

Cinco lectores nativos nuevos de sólo lectura cubrieron 211.121 caracteres, una captura completa por lector, máximo tres simultáneos. Veintiún intervalos contiguos de hasta 12.000 caracteres Unicode por salida; sin truncamientos declarados. Los informes persistidos son extractos seleccionados del principal, no transcripciones completas. Cero nuevas invocaciones Claude V1; se conservan las ocho históricas y su consumo, sin estimación de tokens nativos.

| Captura | Fuente | Caracteres | SHA256 de full_text |
| --- | --- | ---: | --- |
| catalog | `source:0nf769h6lf4rytwcjtib` | 38411 | `03a0ba153e7d095aec58da59dd067424ef945cd07f20550e8d721143c5af7584` |
| claude | `source:9srtoizn1jnnh83qg3kd` | 21829 | `f95c9a6d78e7fd0c6600f49a43f6d104735346c8e0b98d5bc4a3050fbf6c94cf` |
| notebook | `source:aia2mbd0hduz6rmj8jvr` | 36910 | `10d7156a8792fedb27c90619ac701116a36e5a3c605d8f761646fb4d86b4dc08` |
| graphify | `source:f7fdu243hz1rv2o1tbhm` | 50373 | `66a3c21f5a63babd1abb10673dbdf64b4e2893dc92e8fd34dc6121849900a573` |
| mcp | `source:k48rj1bih8rw9jwx58to` | 63598 | `b7585a888515e6e362c70264f911427775559eb2d8d131dfcc9595959f2fbdf7` |

El principal cotejó las cinco huellas declaradas, diez citas y sus contextos/fronteras. El verificador efectúa quince cotejos sobre esos diez intervalos, verifica cinco uniones completas y revalida integridad de las 295 capturas. Dos lectores informaron un cwd antiguo, pero todas sus lecturas usaron la ruta absoluta designada; las huellas y citas coinciden con el original vigente. Se conserva esa procedencia sin atribuir reparaciones o nuevas lecturas.

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) avanza de 274 a 279 disposiciones y de 21 a 16 pendientes. Base274 fijada por SHA256, escritura atómica y permisos conservados; el verificador no sobrescribe otro corte. Un catálogo de enlaces es una fuente, no centenares de documentos leídos. Referencias, navegación, imports y licencias solamente enlazadas no reciben crédito de lectura. Artefactos `artifacts/beta-promotion-fix-20261020/b00-333-*`.

## Catálogo y guías externas

El catálogo describe comprobación HTTP/título de 176 URLs y 43 áreas en el corte 2026-10-11/base7e04016. Advierte que acceso no acredita compatibilidad, disponibilidad futura o contenido completo incorporado al cuaderno. Conserva diferencias entre patch solicitado y título servido, documentación stable/latest/main, tags y guías fallback; distingue versiones del host, imagen, paquete cliente y servicio. Los ejemplos de Celery, boto3, psycopg y SciPy son observaciones históricas, no una consulta actual ni defectos demostrados. S3 describe un protocolo, no contratación de AWS o equivalencia total con RustFS. Este bloque no revalidó URLs online.

La guía de Claude Code trata síntomas, memoria heap frente a nativa, tablas, compacción, terminal, portapapeles/SSH y búsqueda. Su mención v2.1.208 es un límite histórico específico; no identifica el cliente instalado. Diagnósticos, heap dumps, instalación, reset, envío a soporte y cambios de configuración permanecen instrucciones externas no ejecutadas. Una etiqueta de navegación sobre goals, agentes, skills o programación no demuestra que esa capacidad esté disponible o autorizada en este proyecto. No se generaron diagnósticos ni se contactó con soporte.

La referencia de notebooklm-mcp-cli v0.15.4 es un README de tercero, con navegación GitHub y ejemplos de versiones anteriores. Describe CLI/MCP/skills, autenticación por cookies y funciones de consulta, importación, estudio, investigación y compartición. Declara APIs internas no documentadas, protección de credenciales opcional y Enterprise experimental con validación del autor acotada. Esas afirmaciones y advertencias no son auditoría, revisión jurídica o prueba de integración local. No se instaló, autenticó, importó, compartió ni borró contenido en un servicio externo; los ejemplos no conceden esos permisos.

La captura Graphify identifica Graphify-Labs/graphify y el paquete graphifyy, con comando graphify. La rama v8 no significa versión8; el README muestra release0.9.85 y metadatos de commit0.9.84, distintos del entorno inspeccionado. Las descripciones de AST, inferencias, comunidades, esquema y ejemplos ayudan a localizar conceptos, pero EXTRACTED/INFERRED no equivalen a corrección verificada. Sus benchmarks apuntan a un harness no leído. Graphify Cloud, sus métricas de ahorro y expresiones de verificación formal o servicio continuo son promoción separada del CLI local; no acreditan esos resultados para este proyecto. Instrucciones de instalación, hooks o delegación no sustituyen AGENTS ni el contrato de ejecución.

La captura MCP de ChatGPT Learn es extensa en navegación y no fija versión del cliente. Separa expresamente servidores configurados en un host de herramientas alojadas por plugins; los ejemplos de STDIO/HTTP/OAuth, configuración y proveedores no demuestran instalaciones, autenticación, capacidades actuales o permisos concedidos. Sus referencias RFC y páginas de producto siguen fuera de lectura. No se adoptó configuración, conectó un servidor o hizo login. Este informe conserva lo que dice una captura; no ofrece instrucciones actuales de uso de Codex ni valida su implementación.

## Contraste local y aclaración

Diez archivos del repositorio y un módulo instalado externo, veintidós literales seleccionados: dependencias declaradas, imagen, Compose, límites de CI, procedimiento del grafo, inventario/catálogo, sala de revisión y sus dobles de prueba, exclusiones Git y código local de registro de consultas. Las pruebas de sala se leyeron como código, sin ejecutarlas; opiniones externas siguen marcadas como no verificadas y no autorizan ejecución. Esto no constituye una auditoría completa de esa herramienta o de MCP.

Los metadatos de la distribución instalada identifican graphifyy0.9.74 en su intérprete uv, fuera de las dependencias de aplicación; se conserva ruta y SHA256 de METADATA y su identidad de repositorio. No se consultó cuál es el release upstream vigente. El extracto estructurado de uv.lock liga cinco versiones resueltas a la huella del fichero; no las presenta como versiones de procesos activos. Dockerfile declara Python3.12.15, cuatro workers y timeout60; esa configuración estática no demuestra un nuevo despliegue o capacidad medida.

La captura Graphify combina la afirmación de ausencia de telemetría con una descripción posterior de registro local de consultas. El código local examinado, identificado por SHA256, exige activación expresa del registro; en las variables observadas no estaban activados enable, ruta alternativa, respuestas o disable. Esa diferencia se conserva sin deducir comportamiento por el número de versión. No se abrieron registros de consultas, cambiaron variables o borraron ficheros. La observación de ese código y entorno no acredita ausencia global de registros en otras versiones, procesos o backends.

Se añadió a [tecnologías](tecnologias.md) una nota de vigencia: las menciones inferiores a MOD-08 pausado, Graphify0.9.64 y procesos/versiones pertenecen al inventario del11Oct; el estado actual se consulta en seguimiento17 y el sello del grafo. Se conserva byte a byte el texto anterior, reconstruible eliminando sólo la nota, con copia y huellas antes/después verificadas. No se reescribe la tabla antigua como si midiera el presente. El archivo no estaba seleccionado en el manifiesto semántico; no se declara una extracción completa nueva de su contenido por esta nota.

Sin cambios de aplicación o pruebas, defecto funcional nuevo demostrado o nueva ejecución funcional. La aclaración documental y el contraste de herramientas no amplían las aceptaciones previas, no activan proveedores ni prueban cumplimiento jurídico. Las correctivas anteriores y B07 mantienen sus cortes, sin repetir baterías por esta lectura.

## Grafo y continuación

Grafo386 revalidado antes del análisis; integración semántica dirigida387 de esta conciliación y seguimiento. Sin nuevo AST global, semántica exhaustiva o HTML global. La coherencia de hashes/extremos del sello no prueba lectura de fuentes pendientes, exactitud de inferencias, seguridad o aceptación beta.

Quedan 16 fuentes, 19,318,488 caracteres: siete referencias técnicas y nueve grandes capturas de grafo. Los conteos no expresan porcentaje de esfuerzo. B00 sigue abierto; nueve de18puntos beta cerrados y B15 opcional, con dirección de almacenamiento ya documentada y diseño/garantías pendientes. Sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación291](291-conciliacion-interfaz-operacion-b00-20261024.md).
