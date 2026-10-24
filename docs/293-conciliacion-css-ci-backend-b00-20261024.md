# B00-334 — CSS, CI y referencias de backend

Fecha: 2026-10-24. Lectura de capturas técnicas y contraste estático acotado.

B00-334: 284 de 295 fuentes únicas conciliadas; quedan 11 de arquitectura. Incorporadas referencias de CSS, GitHub Actions, S3, orjson y Celery, con contraste estático de configuración, serialización y objetos. Sin cambios de aplicación o pruebas, defecto funcional nuevo demostrado ni nueva aceptación. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Procedencia y disposición

Ocho lectores nativos nuevos de sólo lectura cubrieron 590.130 caracteres en ocho partes, máximo tres simultáneos. Se emitieron y leyeron 52 intervalos contiguos de hasta 12.000 caracteres Unicode por salida; sin truncamientos declarados. Se conservaron los intervalos efectivamente informados, incluidos los últimos bloques agrupados, sin reconstruirlos suponiendo un tamaño uniforme. Los informes persistidos son extractos seleccionados del principal, no transcripciones completas. Cero nuevas invocaciones Claude V1; ocho históricas y consumo anterior preservados, sin estimación nativa.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| css | `source:w587pne7x17n5i5nvbwv` | 155094 | [0,77547), [77547,155094) |
| actions | `source:sutnt6tbtpcxc4bjjrca` | 246338 | [0,82112), [82112,164225), [164225,246338) |
| s3 | `source:p9wxlyfhv27ax7lgtdw3` | 87467 | [0,87467) |
| orjson | `source:y6t2yg3obk4eaotaimmr` | 44716 | [0,44716) |
| celery | `source:ybaxrvkn0ixg76v1qavc` | 56515 | [0,56515) |

SHA256 completos cotejados:

- `source:w587pne7x17n5i5nvbwv`: `c58b67eac4c77fc84edf0608bad9ca1a5750b8bea6559b36bb171f08d3c51966`.
- `source:sutnt6tbtpcxc4bjjrca`: `618ab375a3a210b6dd9abca5ae8db8cedf837dad25b53e7ce846f011fde9e07c`.
- `source:p9wxlyfhv27ax7lgtdw3`: `dd4873501bebc1e024a65594c7bb98d48cc87025b6535623dc3bdf5f90a149c0`.
- `source:y6t2yg3obk4eaotaimmr`: `f1a36aab2baa8ffd82c0256cae7d3e3dd03168c2a852a306dc0aeb05cf60e2fc`.
- `source:ybaxrvkn0ixg76v1qavc`: `663a126f65493dc73a3de7f1fdf17da2697666747234408968018e073174a5ad`.

El principal comprobó las ocho huellas declaradas y dieciséis citas con sus contextos/fronteras. El verificador realiza veintiún cotejos sobre esos dieciséis intervalos, verifica cinco uniones completas y revalida integridad de las 295 capturas. Cuatro lectores informaron un cwd antiguo, pero usaron la ruta absoluta designada; huellas y citas coinciden con el original vigente. Esa procedencia no requiere inventar una reparación o una lectura nueva.

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 279 a 284 disposiciones y de 16 a 11 pendientes. Base279 fijada por SHA256, reemplazo atómico y permisos conservados. Las particiones no cuentan como nuevas fuentes; no ejecutar este verificador sobre un ledger futuro. Artefactos `artifacts/beta-promotion-fix-20261020/b00-334-*`. Una lectura de navegación o bibliografía no incorpora las páginas enlazadas.

## CSS: norma, ejemplos e implementación

La captura identifica CSS Custom Properties Level1 como Candidate Recommendation Snapshot de16Jun2022. Esa fecha y estado no acreditan la revisión actual, soporte de navegadores o conformidad del proyecto. El texto diferencia requisitos normativos de introducción, notas, ejemplos y bloques Tests informativos; enlaces WPT no son resultados ejecutados. La extracción pierde parte del marcado gramatical, por lo que no se reconstruyen metavariables ausentes.

Se conservan nombres por secuencia de puntos de código y caso, herencia/cascada, valores iniciales garantizados inválidos frente a valores vacíos, dependencias/fallbacks y ciclos por elemento. var() sustituye valores, no nombres de propiedad o selectores. La invalidez en tiempo de cómputo no recupera automáticamente una declaración anterior; la concatenación de tokens no equivale a construir una longitud y el ejemplo calc() tiene un propósito acotado. Serialización CSSOM, shorthands pendientes y límites de expansión definidos por el navegador no se convierten en nuevos umbrales contractuales del producto.

El [stylesheet actual seleccionado](../static/app.css) define tokens en :root, variantes de tema y referencias var() en valores. Su objetivo declarado de contraste y las reglas de foco no demuestran conformidad WCAG o todos los estados de navegador. No se cambió CSS, ejecutó Chromium o repitió accesibilidad por esta lectura. Los criterios de beta y sus comprobaciones propias se mantienen.

## Actions: configuración frente a ejecución

La guía capturada combina navegación, sintaxis, recomendaciones, ejemplos y afirmaciones de servicio no fijadas a un release preciso. Cubre triggers, filtros ordenados, permisos por ámbito y eventos de baja confianza, env/defaults, dependencias/condiciones, concurrencia, runners, outputs, matrices, contenedores, servicios y workflows reutilizables. Conserva tensiones textuales sobre cancelación por grupo y contextos en defaults; no se resuelven inventando una regla nueva para el proyecto.

Los ejemplos de background, wait, wait-all, cancel, parallel, referencias $/, cache y snapshots no acreditan soporte actual o una ejecución local. Las cifras, imágenes de runners, tags de acciones, disponibilidad y facturación permanecen datos de la captura. La recomendación de fijar SHA no demuestra que los tags actuales sean inmutables. Mencionar permisos o herencia de secretos tampoco verifica sus valores efectivos en GitHub.

El [workflow del repositorio](../.github/workflows/ci.yml) declara workflow_dispatch y conserva servicios PostgreSQL17/Redis7.4, checks y artefactos. Esto es configuración estática; no se activó GitHub Actions, contrataron minutos ni aceptó CI externo. El [CI local](ci-local.md) sigue siendo el entorno autorizado; el perfil checks no ejecuta pruebas y pytest paralelo no se usa para mediciones de capacidad. La sincronización ilustrada por una plataforma no reemplaza el protocolo completo de pruebas largas, avisos, proceso persistente y reactivación verificada.

## Objetos y serialización

Welcome de S3 contiene principalmente nombres de operaciones/tipos y navegación, más una introducción corta. Identifica la versión de API2006-03-01, sin congelar el catálogo del servicio. Autenticación, firma, campos, errores y ejemplos se remiten a documentos no leídos. Las descripciones AWS de Control, Files, Tables, Vectors y Outposts no son capacidades demostradas de un endpoint compatible con S3 ni un contrato con AWS.

En el [repositorio de objetos seleccionado](../apps/safety/object_storage/repository.py) se observan escritura condicional, referencias autenticadas, verificación física de tamaño/digest, comprobación de tombstones y cierre de cuerpos. El borrado verifica estado administrativo y rechaza versionado/Object Lock incompatibles. Sus tests distinguen dobles GuardClient de escenarios con RustFS local; leerlos no acredita que corrieran en este corte. Los casos NotImplemented y demás respuestas administrativas requieren evaluación en el proveedor efectivo antes de cualquier aceptación externa. No se modifica esa política ni se afirma cobertura de todas las operaciones S3.

La captura orjson corresponde a página3.13.0, mientras sus tablas de reproducción identifican rueda3.10.11 y entorno propio; no son mediciones de esta web. dumps produce bytes UTF-8 y soporta conversiones que no definen automáticamente el contrato canónico. Las opciones de claves no textuales, Fragment, fechas, subclases y dataclasses tienen límites diferentes; Fragment no implica validación JSON completa. La codificación de no finitos a null y su rechazo en loads no son una misma semántica.

El [wrapper actual](../apps/safety/fast_canonical.py) valida valores/tipos/números finitos antes de dumps con OPT_SORT_KEYS; las referencias de contenido sin clave no autorizan acciones. Los tests de JSON canónico expresan rechazo de tipos/no finitos y límites de enteros; los diferenciales nativos requieren un kernel validado y no convierten fallback en evidencia nativa. Son aserciones estáticas leídas, no resultados nuevos. No se agregaron opciones de serialización, normalización o passthrough a partir del README.

## Workers y contraste actual

La guía de Celery muestra título5.6.2, enlaces/footer5.6.3 y descripción stable5.6. Esa identidad mezclada se conserva; no se toma como versión del worker real. Shutdown warm/soft/cold/hard, señales, heartbeat, reconexión, prefetch, revocación y límites dependen de broker, pool, plataforma y configuración. El log de restauración tras hard shutdown no garantiza redelivery. Terminate afecta al proceso y puede alcanzar otra tarea; la guía lo limita a último recurso administrativo. Una respuesta tardía de inspect no prueba muerte y scheduled no significa tareas periódicas.

La configuración seleccionada mantiene mensajes JSON, límites de tarea, worker/Beat diferenciados y dos procesos de concurrencia en Compose. El [guard de recuperación](../config/celery.py) evita ejecutar negocio cuando RECOVERY_MODE está activo. La prueba de recuperación prefork declara simulador local y separa outbox/reintento de entrega externa. Leer estos archivos no ensaya señales, supervisor, recuperación o entrega exactamente una vez; las garantías deben apoyarse en persistencia e idempotencia de dominio y en sus ejecuciones propias.

Catorce archivos actuales y veintiocho literales seleccionados: stylesheet, workflow, dependencias, Compose/settings, Celery, serialización, objetos, documentación de CI y tests de canónico/kernel/objetos/reintento. La selección no es auditoría completa de esos subsistemas. Sin cambios de aplicación o pruebas, defecto funcional nuevo demostrado, contratación/proveedor o nueva ejecución funcional. Las correctivas anteriores y B07 mantienen su corte; no se repiten baterías sin cambio, fallo o incertidumbre real.

## Grafo y continuidad

Grafo387 revalidado antes del análisis; integración semántica dirigida388 de esta conciliación y seguimiento. Sin nuevo AST global, semántica exhaustiva o HTML global; el sello y sus límites no acreditan fuentes todavía pendientes, exactitud de toda inferencia o aceptación beta.

Quedan 11 fuentes y 18,728,358 caracteres: ECMAScript, Settings de Django y nueve capturas grandes del grafo. Los conteos no son porcentaje de esfuerzo. B00 sigue abierto, nueve de18puntos beta cerrados y B15 opcional, con dirección de almacenamiento ya documentada y diseño/garantías pendientes. Sin publicación, gasto o datos reales. Corte previo: [conciliación292](292-conciliacion-referencias-herramientas-b00-20261024.md).
