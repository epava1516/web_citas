# N09F — preparación de diagnósticos de autoridad en rectificación

Estado: instrumento revisado e integrado como candidato; prerregistro de veinte diagnósticos, sin ejecución runtime nueva ni defecto confirmado. Base `6d4c288` en master. [N09E/434](434-n09-e-fronteras-descifrado-verificadas-20261026.md) conserva sus 38 PASS; N09 sigue abierto con 139 IDs y el contrato mantiene ocho de trece bloques obligatorios aceptados. Alpha/noindex, datos sintéticos, sin proveedores reales.

## Corte de fuentes y alcance

Se conserva el corte publicado tras N09E: 2.065 fuentes, 20.032 nodos, 84.222 relaciones, 966 comunidades; SHA256 del grafo `9f61528455a8d49029ac14d6989c6c569b73725e11ef02dcc85d94f36e002aa2`. El corte focal previo se registra en `artifacts/recorridos-n09-f-20261026/pre-source-cut.json`. La revisión se contrasta con seis módulos actuales: rights_rectification, rectification_uploads, rectification_review, rectification_execution, rectification_recipients y rectification_account. Las identidades y dos precisiones de bloqueos quedan en `source-boundaries-corrected.json` del mismo directorio.

Esta lectura no equivale a una nueva extracción semántica completa. Antes de congelar o medir se requiere el delta del instrumento y la semántica selectiva de este documento y del seguimiento. No se reconstruye el grafo completo: ese trabajo corresponde a N15 antes de la diferencia del inventario preservado.

La pregunta es si cada operación conserva autoridad vigente después de una espera PostgreSQL y antes de procesar datos privados o producir su efecto. Repetir checks con el mismo objeto User no demuestra recarga de permisos; comprobar de nuevo el proof del sujeto tampoco demuestra autoridad vigente del operador.

## Matriz propuesta de preparación

La selección definitiva depende de la revisión del instrumento y de sus precondiciones nativas. Se proponen veinte casos: control y retirada de permiso por cada operación. No hay resultados ni tiempos nuevos que completar en una tabla antes/después.

| Operación | Fila propuesta para sostener | Permiso retirado | Frontera que debe observarse |
| --- | --- | --- | --- |
| preview | User del sujeto | execute_rights_request | Proyección privada y creación de SourceRead |
| propose | RightsRequest | execute_rights_request | Propuesta, Action y cambio de versión |
| source_photo | Blob de foto elegible | execute_rights_request | Captura de fuente y entrega real de bytes por GET |
| upload | Blob existente con el mismo SHA | execute_rights_request | Captura de fuente, referencias, archivo y callback de procesamiento |
| discard | Upload activo del expediente | execute_rights_request | Captura de fuente, discarded_at y Action |
| inspect | Proposal | review_rectification | Descifrado y auditoría de lectura de propuesta |
| review | Proposal | review_rectification | Descifrado, Review, Action y versión |
| notify | Review aprobada | review_rectification | Notification, respuesta y versión |
| execute | Notification | review_rectification | Corrección, Execution, respuesta y versiones |
| recipients | RightsRequest | review_rectification | Captura de destinatarios y creación del inventario |

Los permisos de la tabla pertenecen a safety. Para notify/execute se escoge review_rectification porque la emisión posterior de progress recarga review_rights_request y respond_rights_request; retirar solamente respond podría ocultar el hueco específico con una denegación tardía. Esto debe comprobarse en cada diagnóstico, sin inferir el resultado de la fuente.

Dos precisiones sustituyen interpretaciones demasiado amplias del informe previo de fuente. En upload, el Blob existente se incluye mediante additional_blob_ids y puede esperar primero dentro de source_snapshot, antes del get_or_create y del bloqueo explícito final. En discard, una fila activa se bloquea primero al recopilar uploads dentro de source_snapshot. Esos escenarios no acreditan aisladamente los últimos bloqueos explícitos. Las ramas con cargas no elegibles, creación concurrente de Blob o confirmación de email conservan su disposición pendiente; no se dan por representadas automáticamente.

## Instrumento y revisión previa a ejecución

Escritor nativo aislado `/root/n09f_rectification_diagnostics`, worktree `/tmp/web-modelos-n09f-rectification-20261026`, base aceptada `6d4c288`. Propiedad exclusiva del archivo nuevo tests/test_rectification_authority_wait.py y su informe ignorado artifacts/n09f-diagnostics/report.json. Sin permisos para ejecutar pruebas, editar aplicación, documentos, grafo, servicios o commits. Codex revisará e integrará el resultado antes del prerregistro definitivo y del runner. Un informe complete del escritor no será aceptación técnica.

Preparación mediante los fixtures y servicios nativos existentes: expediente de rectificación real dentro del entorno sintético, asignación, autor/revisor independientes, source audit, proof y versiones vigentes. Alias simple para las etapas de propuesta/aprobación/acuse/ejecución, sin introducir cambio de email ni selección de fotos en esa saga. Cada control debe probar admisión y efecto propios. Una preparación inválida se registrará como fallo del instrumento, no del producto.

Conexiones PostgreSQL propias, guard serial y selección explícita. Antes de retirar permiso deben observarse el PID efectivo del trabajador, wait_event_type=Lock y el PID del holder en pg_blocking_pids. Retirada comprobada mediante User nuevo y confirmada al liberar el lock. Hilos, eventos, transacciones y limpieza acotados incluso ante error. No sustituir ORM, guards, reloj, cifrado o espera por simulaciones.

Las llamadas directas a servicios no acreditan transporte HTTP, middleware ni divulgación de respuesta. source_photo sí requiere GET real, lectura acotada y cierre de FileResponse; sólo contadores/hashes, nunca contenido ni rutas privadas en evidencias. Los observadores de procesamiento deben reenviar siempre al callable original. Una entrada a source_snapshot anterior a la espera es legítima: distinguir entradas de retornos privados satisfactorios después de revocar. Los wrappers de retorno por sí solos no prueban ausencia de toda materialización interna anterior; esa limitación debe permanecer explícita y la posición de las guardas se revisará en fuente.

Snapshots completos de valores escalares mediante conteos y hashes, excluyendo sólo la modificación deliberada del operador/permisos. Negativos: PermissionDenied o 403 según interfaz, sin efecto propio ni alteración de expediente/fuentes. Upload requiere oráculo de archivo y publicación de tarea; capturar delay no acredita broker ni worker real. No registrar plaintext, ciphertext, contactos, motivos privados o credenciales.

## Pendientes y límites

Selección fijada tras revisión de la entrega: archivo completo `tests/test_rectification_authority_wait.py`, función `test_native_rectification_authority_after_owned_wait`, diez familias de la tabla por `change=valid/permission`: veinte casos propuestos, sin colección runtime previa. Candidato de 527 líneas SHA256 `2358c9317c343c55378d1dea6596777c612c844a6122443ff581bab032c83a0d`; informe original del escritor y revisión root conservados en artifacts/recorridos-n09-f-20261026. Trece fuentes de aplicación/fixtures contrastadas por hash. La primera comprobación Ruff informó All checks passed; su recibo terminal debe verificarse separadamente. No confundir lint con QA de producto.

Runner previsto: perfil focused oficial, parser nativo `/tmp/web-modelos-librdb-v2.4.0`, workers1 y timeout3600, sólo ese archivo. Se requiere grafo focal actualizado y congelación antes de lanzarlo. El tiempo incluye preparación de saga, snapshots, espera inducida y limpieza; no es latencia normal de aplicación. No se conoce aún la duración total ni hay tabla de mejora. Los controles notify/execute esperan una RightsResponse y una RightsNotice adicionales; cada operación escritora comprueba su Action con clave propia, sin suponer que issue genere otra Action.

El llamador adicional rectification_final.evidence utiliza rectification_account.source. Su presencia se registra para la conciliación individual posterior; no forma parte de estas diez operaciones ni queda aceptado por semejanza. Tampoco se cierran las ramas de cuenta sin perfil, replays o bloqueos tardíos distintos sin evidencia propia o justificación verificable.

Antes de ejecutar: revisar propuesta, selección, oráculos y alcance; completar prerregistro, grafo focal y congelación. Después: auditar resultados, integridad de fuentes, limpieza y recibos Telegram. Sólo entonces decidir corrección y validación. No repetir N09E ni otras baterías válidas por instalar skills/MCP.

Se aplican las skills Django, revisión y seguridad, incluyendo rutas autenticadas y revocación tras esperas. Las herramientas de instalación y el kit aislado no sustituyen QA del producto ni amplían el contrato. N02 restante sigue diferido al final del desarrollo; N10, N11 y N15 pendientes, N12–N14 condicionados. El objetivo completo permanece activo.
