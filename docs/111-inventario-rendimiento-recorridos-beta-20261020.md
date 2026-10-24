# Inventario de recorridos y mecanismos para medir y optimizar la beta

Fecha de revisión: 2026-10-20. Estado: inventario estructural inicial con propuesta de presupuestos temporales; medición integral y conciliación de evidencia pendientes.

## Propósito y ubicación

Inventariar las peticiones, subidas, interacciones y trabajos asociados para medir su coste, diagnosticar problemas y verificar las correcciones. La existencia de un mecanismo no implica que sea lento ni que deba modificarse.

Documento solicitado en una conversación lateral. Se guarda en `/home/felidae/proyectos/web_modelos/docs/` sin modificar la candidata activa de `/home/felidae/proyectos/web_modelos_mod08_vps`. Las fuentes inspeccionadas pertenecen a esa candidata. Su incorporación al seguimiento y al grafo de la candidata queda pendiente de integración en el hilo principal, fuera de una medición con fuentes congeladas. Este documento no cambia el contrato ni cierra puntos del roadmap.

## Método, recuento y límites

Revisión de solo lectura del grafo existente, declaraciones de rutas mediante AST, funciones decoradas con `shared_task`, configuración de Beat, formulario de búsqueda, servicios de fotografías y componentes de navegador. No se ejecutaron pruebas ni mediciones nuevas.

Se localizaron **170 rutas con nombre explícito**, **27 tareas Celery declaradas con `shared_task`** y **28 familias de recorridos**. Son unidades diferentes y no deben sumarse como total de funcionalidades.

| Archivo de rutas, relativo a la candidata inspeccionada | Rutas con nombre explícito |
| --- | ---: |
| `config/urls.py` | 6 |
| `apps/core/urls.py` | 67 |
| `apps/catalog/promotion_order_urls.py` | 2 |
| `apps/catalog/promotion_urls.py` | 4 |
| `apps/safety/rights_object_urls.py` | 1 |
| `apps/safety/urls.py` | 90 |
| Total | 170 |

El recuento excluye las rutas generadas automáticamente por Django Admin y las declaraciones de inclusión. No multiplica ES/EN ni distingue GET/POST o acciones dentro de una misma vista. Las familias siguientes agrupan mecanismos; todavía falta una matriz individual de endpoint, método, acción y escenario para acreditar exhaustividad operacional.

El grafo se utilizó como mapa de dependencias y se contrastó con código. Sus relaciones indirectas y referencias no resueltas no se toman como llamadas verificadas ni como defectos. Esta revisión no regenera ni incorpora semánticamente este documento al grafo.

## Inventario estructural

La columna de medición recoge únicamente lo conciliado en esta revisión. «Por conciliar» significa que no se ha auditado aquí la evidencia de rendimiento de esa familia; no afirma ausencia de pruebas o mediciones históricas.

| ID | Familia | Operaciones y costes que deben cubrirse | Medición conciliada en esta revisión |
| --- | --- | --- | --- |
| I01 | Listado orgánico | Selección, autoridad de visibilidad, orden, recuento y render | Diagnóstico local parcial |
| I02 | Listado promocionado | Derechos Top/Premium, prioridad, rotación, desempates y patrocinio | Diagnóstico, planes y calibración HTTP; capacidad a escala pendiente en el corte revisado |
| I03 | Búsquedas y filtros | Texto, perfil, geografía, idiomas, días, horario, contacto y verificaciones | Texto y ciudad+idioma medidos; combinaciones restantes por conciliar |
| I04 | Paginación | Primera, intermedias, última, páginas profundas, vacías e inválidas | Primera y última en diagnóstico; resto por conciliar |
| I05 | Ficha pública | Datos, autoridad de publicación, fotos y enlaces de contacto externo | Participa en mezcla HTTP; diagnóstico individual por conciliar |
| I06 | Entrega de imágenes | Lecturas públicas, privadas y de moderación; almacenamiento y transferencia | Por conciliar |
| I07 | Favoritos | Listar, añadir, quitar y comprobar perfiles que dejaron de ser visibles | Por conciliar |
| I08 | SEO y documentos públicos | Sitemaps paginados, robots y textos legales | Por conciliar |
| I09 | Cuenta y sesión | Registro, acceso, salida, recuperación, tokens y aceptación de condiciones | Por conciliar |
| I10 | Seguridad y verificación | MFA, edad, teléfono, confirmaciones y controles de contacto | Por conciliar |
| I11 | Panel del anunciante | Perfil propio, estado, borrador, avisos y acciones disponibles | Por conciliar |
| I12 | Edición del perfil | Inicio, lectura, guardado por pasos, validación y conflictos de versión | Por conciliar |
| I13 | Subida de fotografías | Recepción, límites, decodificación, persistencia, duplicados y reintentos | Calibración de una subida persistida; no rendimiento integral de procesamiento |
| I14 | Procesamiento fotográfico | Derivados, firmas, recuperación de candidatos y confirmación de similitud | Por conciliar |
| I15 | Gestión de fotografías | Previsualizar, reordenar, retirar, restricciones y reclamaciones | Por conciliar |
| I16 | Revisión y publicación | Envío, estado, colas, revisión de perfil/fotos y decisiones | Por conciliar |
| I17 | Ciclo de vida | Pausa, retirada, renovación y caducidad | Por conciliar |
| I18 | Agencias y representación | Paneles, invitaciones, asignaciones, consentimiento, revocación y transferencia | Por conciliar |
| I19 | Gestión comercial sintética | Catálogo, versiones, pedidos, eventos, derechos y autosubidas | Preparación de derechos real local observada; coste del recorrido comercial por conciliar |
| I20 | Denuncias y reclamaciones | Envío, consulta, mensajes, evidencias, decisiones y alertas urgentes | Por conciliar |
| I21 | Derechos y rectificación | Inventarios, revisiones, restricciones, correcciones y destinatarios | Por conciliar |
| I22 | Exportación y portabilidad | Preparación, generación, imágenes, partes y descarga autorizada | Por conciliar con evidencia histórica de MOD09 y trabajos posteriores |
| I23 | Avisos y comunicaciones | Bandejas, confirmaciones, entrega, recuperación y reintentos | Por conciliar |
| I24 | Publicación en segundo plano | Refresco, barridos, invalidación y acumulación de pendientes | Un tipo de backlog diagnosticado; candidatos desconocidos y carga restante pendientes |
| I25 | Limpieza y recuperación | Purgas, borrados físicos, trabajos huérfanos y recuperación de tareas | Por conciliar |
| I26 | Navegador y entrega web | HTML, CSS, JavaScript, selectores y peticiones periódicas | Por conciliar |
| I27 | Infraestructura transversal | Middleware, sesiones, permisos, transacciones, conexiones, Gunicorn, Redis y almacenamiento | Topología registrada en calibración; atribución completa de recursos pendiente |
| I28 | Operación administrativa | Django Admin, comandos de mantenimiento y comprobación de salud | Por conciliar; requiere expansión de rutas administrativas |

## Trabajo en segundo plano

Las 27 tareas identificadas se reparten así:

| Área | Cantidad | Funciones o grupos |
| --- | ---: | --- |
| Promociones | 1 | `bump_promotions` |
| Publicación | 3 | `expire_listings`, `refresh_publication_state`, `sweep_publication_state` |
| Fotografías | 4 | `process_blob`, `recover_media_jobs`, `erase_media_files`, `cleanup_prepared_media` |
| Objetos de derechos | 2 | `purge_orphan_export_objects`, `purge_object_deliveries` |
| Seguridad y derechos | 17 | Entrega de avisos, alertas urgentes, retención, purgas de exportaciones/confirmaciones/revisiones/borradores/inventarios, generación y reconciliación de exportaciones de portabilidad |

El número de tareas declaradas no es el número de entradas activas de Beat. La programación depende de configuración y modos. Para cada tarea deben localizarse disparadores, periodicidad aplicable, cola, tamaño del lote, reintentos, idempotencia y recuperación. También deben revisarse señales y callbacks de transacción que desencadenen trabajo sin un endpoint propio.

## Distinciones necesarias al medir

- **Subida:** separar recepción HTTP, aceptación persistida, espera en cola, procesamiento, comparación y disponibilidad de la foto. Un302 no demuestra por sí solo ingestión ni finalización asíncrona.
- **Publicación:** distinguir proyección actualizada, estado inválido o pendiente y fallback de comprobación directa. Retirar perfiles sin refrescar no representa todos los tipos de backlog.
- **Búsqueda:** variar selectividad y combinaciones, no sólo número de perfiles. Incluir resultados abundantes, escasos y vacíos, parámetros inválidos y filtros incompatibles.
- **Navegador:** los selectores geográficos manipulan opciones ya incluidas en la página. Medir tamaño de HTML, DOM y tiempo de interacción además de peticiones al servidor.
- **Sondeo:** el componente de exportación pendiente usa `hx-get` cada tres segundos. Medir multiplicación por sesiones simultáneas y duración de trabajos.
- **Imágenes y descargas:** medir bytes, lectura de almacenamiento, memoria y ocupación del worker; separar autorización y transferencia.
- **Autoridad:** atribuir el coste de permisos, visibilidad y revocación compartidos sin suprimir controles para obtener mejores cifras.
- **Tareas periódicas:** medir duración, retraso, edad de cola y acumulación, incluyendo superposición entre tareas y peticiones.

## Evidencia ya localizada y alcance

En la candidata inspeccionada, `docs/108-linea-base-beta-b07-20261020.md`, `docs/109-correccion-ruta-promocional-beta-b08-20261020.md` y `docs/110-contraste-tcp-beta-b07b08-20261020.md` documentan la investigación de listados.

El diagnóstico cubre100/1000/10000perfiles y combina orgánico, promociones y un backlog concreto con primera página ES, texto EN, última página ES y ciudad+idioma EN. La primera página promocionada de10000 pasó de160637,0ms/34026consultas a361,3ms/33consultas en el diagnóstico local. No extrapolar esa cifra a todas las rutas, filtros o niveles de concurrencia.

La calibración111928-b91538fc tiene auditoría de60dinámicas correctas y una subida con Photo y UploadAttempt aceptado persistidos. Usa10perfiles; verifica el instrumento, no capacidad a10000. El ensayo corto de escala figuraba pendiente en el corte documental revisado. Este inventario no sustituye un parte actualizado del hilo principal.

Antes de crear nuevas pruebas, conciliar evidencia previa del alfa, MOD09 y trabajos de capacidad posteriores: versión, escenario, datos, recursos y aplicabilidad a la candidata. La existencia de tests funcionales no acredita presupuesto de rendimiento; una medición histórica tampoco se descarta automáticamente si puede justificarse su reutilización.

## Matriz que debe completar cada recorrido

| Campo | Contenido exigido |
| --- | --- |
| Identidad | ID estable, familia, endpoint/método/acción o tarea, rol e idioma |
| Implementación | Vista, servicios, consultas, plantilla, almacenamiento, señales y tareas dependientes |
| Escenario | Población, fotos, distribución, selectividad, estado, concurrencia, ritmo y duración |
| Variantes | Éxito, vacío, inválido, denegado, reintento, conflicto, revocación y dependencia degradada, cuando apliquen |
| Recursos | Versión y huellas de fuentes, hardware/cuotas, topología y actividad concurrente conocida |
| Presupuesto previo | Límites aplicables de latencia, error, recursos, cola y finalización |
| Medición | Muestras, percentiles y errores; SQL/planes, CPU, memoria, bytes y colas pertinentes |
| Diagnóstico | Coste dominante demostrado, impacto, frecuencia y evidencia causal |
| Corrección | Cambio propuesto/aplicado, prioridad y comportamiento que debe conservarse |
| Verificación | Comparación equivalente, paridad funcional, autoridad, evidencia y límites |
| Seguimiento | Estado, responsable y siguiente acción |

No ejecutar el producto cartesiano de todas las variantes sin criterio. Seleccionar casos representativos y límites a partir de código, contrato, dependencias y riesgo; registrar qué combinaciones quedan fuera.

Estados recomendados: **inventariado → evidencia conciliada → medido → diagnosticado → corregido → verificado**. Puede terminar en **sin corrección necesaria** si cumple su presupuesto. Los bloqueos y mediciones inválidas se registran separados; no se convierten enPASS.

## Orden de trabajo propuesto

1. Integrar este documento y expandir la matriz endpoint/método/acción, tareas, señales, Admin y dependencias de entrega. Comprobar cobertura frente a rutas y disparadores.
2. Conciliar evidencia existente y fijar presupuestos antes de repetir o ampliar mediciones.
3. Completar listados/búsqueda/paginación/fallback y el contraste de carga ya iniciado, sin interferir con sus fuentes congeladas.
4. Medir el recorrido de perfil y fotografías completo, incluida espera y finalización asíncrona.
5. Cubrir autoridad, ciclo de vida, moderación, paneles y agencias; después derechos/exportaciones y operación según impacto y riesgos conocidos.
6. Corregir sólo costes demostrados, repetir escenarios equivalentes y verificar permisos, resultados, idempotencia y recuperación.

Relacionar esta matriz con B07–B12 y la aceptación B16 del roadmap existente; no crear una cola independiente ni declarar completos esos puntos desde este inventario. No autoriza publicación, datos reales, pagos ni contratación de proveedores.

## Presupuestos temporales propuestos

Petición posterior del usuario: estimar tiempos máximos razonables para los mecanismos inventariados. Esta sección se refiere a tiempos de respuesta y finalización del producto, no a horas de desarrollo para optimizarlo. Los valores nuevos son **objetivos iniciales de ingeniería pendientes de medición y de integración contractual**, no rendimiento observado ni garantías actuales. No modifican timeouts, configuración ni criterios de pruebas que estén ejecutándose.

### Cómo interpretar los límites

- **p95/p99:** el95%/99% de la población medida debe terminar dentro del límite correspondiente. Un percentil no es un máximo absoluto.
- **Umbral individual:** cada operación que lo supere requiere registro y diagnóstico. No implica que exista un temporizador que la cancele ni autoriza cambiar el timeout del benchmark. Una petición puede superar el umbral y el conjunto cumplir p95; ambos hechos deben quedar visibles.
- **HTTP:** medir desde emisión hasta respuesta completa en el cliente de pruebas, identificando esperas de conexión, transferencia y proxy. Registrar también tiempo de servidor cuando se mida, sin sustituir la latencia completa por ese dato.
- **Asíncrono:** medir desde aceptación persistida hasta estado terminal utilizable o fallo explícito, incluyendo espera en cola. Tiempo por intento y tiempo total con reintentos se registran separados.
- **Navegador:** medir desde acción hasta actualización perceptible/interactiva en un dispositivo y red fijados. La latencia HTTP no demuestra por sí sola fluidez de interfaz.
- **Máximo real:** es el observado en un ensayo finito. No prometer un máximo universal sin acotar datos, carga, recursos, red, dependencias y estados degradados.

### Criterios contractuales que permanecen

El contrato16§16 y `docs/criterios-revision-benchmark-carga.md` de la candidata mantienen10000anuncios,20RPS, mezcla en tercios de listado/búsqueda/ficha ES–EN, **p95 observable estrictamente inferior a800ms y errores inesperados inferiores al1%**. El corto dura60s/1200dinámicas y1upload; sólo un PASS completo habilita900s/18000dinámicas y15uploads separados. No convertir el objetivo en «≤800ms» ni usar sólo respuestas exitosas para ocultar fallos.

Siguen vigentes demora de emisión p95≤10ms/p99≤25ms/máximo≤100ms, noemitidas0, timeout65s, drain≤70s, pendientes al cierre≤20 y finales0. **65s es un timeout de observación, no un tiempo aceptable de respuesta.** El contrato no fija desde estos datos un nuevo p99 de1,5s ni un plazo de procesamiento fotográfico: los siguientes valores son propuestas adicionales.

Para promociones, filtros combinados, páginas profundas y fallback, B07 propone conservar<800ms y<1% como objetivosHTTP pendientes de contraste. Un buen agregado no basta para declarar resueltas todas las rutas: publicar también resultados por escenario, idioma y estado.

### Interacciones síncronas y navegador

Valores de la tabla en segundos, salvo indicación. Los límites contractuales más exigentes prevalecen si una operación forma parte de un escenario ya regulado. Proponer objetivos específicos no rebaja el límite de la mezcla contractual ni reabre aceptaciones históricas de otros módulos.

| Familia | Objetivo p95 | Objetivo p99 | Umbral individual para investigar | Alcance |
| --- | ---: | ---: | ---: | --- |
| I01–I04: listado, búsqueda, filtros y paginación | <0,8 | ≤1,5 | >3 | HTML completo; objetivos por escenario además del agregado; p99/umbral nuevos |
| I05: ficha pública | <0,8 | ≤1,5 | >3 | HTML; fotos medidas aparte |
| I06: autorización e inicio de entrega de imagen | <0,8 | ≤1,5 | >3 | Tiempo hasta primer byte, no transferencia completa; medir ésta aparte |
| I07: favoritos | ≤0,8 | ≤1,5 | >3 | Listado acotado y altas/bajas |
| I08: robots y documentos legales | ≤0,5 | ≤1 | >2 | Respuesta completa sin recursos adicionales |
| I08: página de sitemap | ≤0,8 | ≤1,5 | >3 | Fijar número de entradas/bytes por página |
| I09–I10: acceso, recuperación, MFA y comprobación local | ≤1,5 | ≤3 | >5 | Mantener parámetros de seguridad; no incluye entrega externa de email/SMS |
| I11: panel de cuenta | ≤1 | ≤2 | >4 | Fijar cardinalidad y paginar colecciones |
| I12: abrir/guardar un paso del perfil | ≤1 | ≤2 | >4 | Acuse después de persistir; sin esperar procesamiento de fotos |
| I13: aceptación de subida | ≤2 de backend | ≤4 de backend | >5 de backend | Más transferencia; fórmula y límites específicos abajo |
| I15: previsualización autorizada, reordenar y retirar foto | ≤1 | ≤2 | >4 | Autorización/acuse; borrado físico separado |
| I16: envío a revisión y consulta de estado | ≤1 | ≤2 | >4 | No incluye decisión humana |
| I16: cola y decisión de moderación | ≤2 | ≤4 | >8 | Página/lote acotados; compromiso de la decisión antes del acuse |
| I17: pausa, retirada y renovación | ≤1 | ≤2 | >4 | Autoridad efectiva al confirmar, sin depender del próximo barrido |
| I18: gestión de agencia y representación | ≤1,5 | ≤3 | >5 | Colecciones paginadas; consentimiento humano y entrega externa separados |
| I19: operaciones comerciales sintéticas | ≤1,5 | ≤3 | >5 | Catálogo/pedido/acuse local; cobros y proveedores reales fuera de alcance |
| I20: recepción de denuncia/reclamación | ≤1 | ≤2 | >4 | Acuse persistido; alertas y revisión separados |
| I20–I21: colas, inventarios y decisiones de derechos | ≤2 | ≤4 | >8 | Páginas/lotes acotados; medición de expedientes grandes separada |
| I22: solicitar trabajo o consultar su estado | ≤1 | ≤2 | >4 | Generación en segundo plano; respuestaHTTP de aceptación no acredita exportación lista |
| I22: autorizar e iniciar descarga | ≤1 | ≤2 | >4 | Transferencia del archivo separada |
| I23: bandejas y confirmaciones | ≤1 | ≤2 | >4 | Paginación y acuse local; entrega a proveedor separada |
| I26: cambio de selector geográfico en navegador | ≤100ms | ≤200ms | >500ms | Medición de acción a actualización local; fixture geográfica completa |
| I26: página principal utilizable | ≤2,5 | ≤4 | >5 | Objetivo de usuario con red/dispositivo fijados; incluye recursos críticos |
| I27–I28: salud local | ≤0,2 | ≤0,5 | >1 | Comprobación deDB incluida; registrar no disponibilidad como fallo |
| I28: operaciones administrativas interactivas | ≤2 | ≤4 | >8 | Listas paginadas; acciones masivas como trabajos separados |

I14, I24 e I25 se presupuestan principalmente en la tabla asíncrona. I27 es transversal: desglosar middleware/autoridad/DB/render/I/O cuando exista coste observado; no sumar tiempos inclusivos ni inventar asignaciones por componente para completar el total.

Los casos de expedientes grandes previamente aceptados provisionalmente conservan su ámbito. Si un inventario completo no cabe en interacción síncrona, evaluar paginación o trabajo asíncrono preservando completitud, autoridad y formatos. No declarar incumplimiento histórico aplicando retrospectivamente esta propuesta.

### Transferencia de imágenes, subidas y descargas

No fijar un máximo independiente del tamaño y del ancho de banda. Para una red estable y un caudal efectivo mínimo declarado, usar como **presupuesto inicial de ensayo**:

`T_transferencia_objetivo = 1,25 × (8 × bytes / bits_por_segundo_efectivos)`

Es una fórmula de planificación con25%de margen, no un límite físico garantizado ni una estimación del caudal real. Registrar el caudal observado, latencia de red y tamaño exacto; congelar el perfil de red antes de medir. Las pruebas de servidor local se presentan aparte de la experiencia con red limitada.

Para subir una foto, sumar2s de aceptación de backend como objetivo p95 y4s como objetivo p99. Con10MiB y10Mbit/s efectivos, la transferencia ideal es8,39s; el presupuesto con margen más backend es aproximadamente **12,5s p95 /14,5s p99**. Son objetivos propuestos, no cifras observadas. La subida admitida actualmente tiene límite10MiB/40millones de píxeles; cubrir ambos extremos sin aumentar esos límites.

Para entrega/descarga, sumar el presupuesto de autorización/inicio aplicable y la transferencia; evitar contar dos veces tramos solapados. Medir también un conjunto de imágenes de página y concurrencia, no sólo un archivo. El timeout65s del benchmark vigente sigue intacto; si el escenario de red de una prueba nueva lo hace incompatible, tratarlo como escenario separado con presupuesto previo, sin reinterpretar la carga contractual.

### Procesos asíncronos y tareas periódicas

Son objetivos iniciales para carga local sintética acotada. Antes de usarlos como gate, fijar número/tamaño de fotos, corpus de comparación, volumen de expediente o filas elegibles, tasa de entrada y recursos. Un corpus o lote sin cota impide sostener un máximo universal.

| Proceso | Objetivo p95 | Objetivo p99 | Umbral de investigación | Reloj y condiciones |
| --- | ---: | ---: | ---: | --- |
| I13–I14: foto aceptada → lista o fallo explícito | ≤30s | ≤60s | >120s | Incluye cola, derivados y comparación automática; no revisión humana; fijar corpus |
| I14: espera de un trabajo fotográfico listo para ejecutar | ≤5s | ≤15s | >30s | Separar espera y ejecución; diagnóstico de saturación |
| I22: exportación ordinaria aceptada → lista o fallo explícito | ≤60s | ≤180s | >300s | Provisional para expediente/volumen preregistrado; casos grandes por clase de tamaño |
| I23: aviso persistido → primer intento de entrega local | ≤90s | ≤120s | >180s | Compatible con despachadores periódicos de60s; no acredita recepción externa |
| I20: alerta urgente pendiente → intento local | ≤90s | ≤120s | >180s | Medir generación e intento separados; evaluar si la cadencia actual basta para urgencia de producto |
| I24: cambio pendiente → proyección de publicación actualizada | ≤60s | ≤90s | >120s | Incluye espera del refresco periódico de30s y procesamiento; autoridad inmediata separada |
| I17/I25: vencimiento o elegibilidad de purga → actualización/borrado debido | ≤90s | ≤120s | >180s | Para tarea de60s y lote acotado; el reloj empieza cuando la política permite/exige actuar |
| I25: recuperación de trabajo atascado | Medir por causa | Medir por causa | Según lease y cadencia reales | No prometer120s si el código sólo considera atascado un trabajo tras3min o tiene lease10min |
| I19: autosubida programada → aplicada o descartada justificadamente | ≤90s | ≤120s | >180s | Desde instante debido; tarea periódica de60s; preservar elegibilidad e idempotencia |
| I24/I25: barrido de reconciliación horario | ≤65min | ≤70min | >75min | Desde evento elegible para ese barrido; vía de respaldo, no plazo de retirada pública |

Los límites de ejecución de Celery observados son90s suave/120s duro por defecto; los trabajos de exportación declaran240s/300s por intento. **Son controles técnicos actuales, no garantías de finalización de extremo a extremo.** Reintentos, espera y recuperación pueden aumentar el total. Si se alcanza un umbral propuesto, registrar degradación y estado; no afirmar que ya existe un watchdog o una cancelación implementada.

Pausa, retirada, revocación y cualquier pérdida de autoridad deben impedir exposición en las lecturas posteriores pertinentes sin esperar30/60s a la proyección. El objetivo de refresco sólo mide convergencia de estado almacenado. En descargas o lecturas ya iniciadas deben preservarse las reglas de revocación aplicables; este documento no las redefine.

La revisión de una persona, la respuesta de un proveedor, un desafío que espera acción del usuario y los plazos jurídicos quedan fuera de estos presupuestos de cómputo. Requieren responsables, horario, prioridades y reglas propias; no se les asigna un máximo de segundos ficticio.

### Validación y tratamiento de incumplimientos

1. Integrar la propuesta en el hilo principal y vincular cada endpoint/tarea a un presupuesto, su excepción justificada y clase de tamaño. No cambiar criterios de una ejecución ya iniciada.
2. Congelar escenarios100/1000/10000 cuando sean pertinentes, fotos/corpus, red, concurrencia, recursos y estado frío/caliente. La carga20RPS corresponde a la mezcla pública vigente; no asignar automáticamente20RPS a cada una de las170rutas o tareas.
3. Informar p50/p95/p99/máximo, errores, timeouts, pendientes y población. No certificar p99 desde cinco muestras ni atribuir su coste al mismo control que lleva profiler. Obtener muestra suficiente y explicar incertidumbre.
4. Ante exceso, conservar el negativo y localizar cola/CPU/SQL/locks/render/almacenamiento/transferencia antes de corregir. Un objetivo nuevo no cambia automáticamente un veredicto contractual: reportar ambos alcances.
5. Repetir de forma equivalente y comprobar autoridad, completitud, idempotencia y comportamiento. No aumentar recursos ni relajar límites retrospectivamente para presentar mejora de código.

Todos los valores nuevos de esta sección siguen pendientes de validación. El inventario estructural y esta estimación no acreditan capacidad, cierre del roadmap ni aceptación beta.

## Fuentes inspeccionadas

Rutas y configuración: `config/urls.py`, `config/settings.py`, `apps/core/urls.py`, `apps/catalog/promotion_urls.py`, `apps/catalog/promotion_order_urls.py`, `apps/safety/urls.py`, `apps/safety/rights_object_urls.py`.

Recorridos principales: `apps/core/views.py`, `apps/listings/discovery.py`, `apps/listings/publication_state.py`, `apps/listings/moderation_views.py`, `apps/catalog/promotion_exposure.py`, `apps/mediafiles/views.py`, `apps/mediafiles/services.py`, `apps/mediafiles/similarity.py`.

Trabajo asíncrono: `apps/catalog/tasks.py`, `apps/listings/tasks.py`, `apps/mediafiles/tasks.py`, `apps/safety/tasks.py`, `apps/safety/rights_object_content.py`, `apps/safety/rights_object_delivery.py`.

Navegador y navegación: `static/geography.js`, `static/search-geography.js`, `templates/listings/draft.html`, `templates/listings/public_detail.html`, `templates/listings/favorites.html`, `templates/core/dashboard.html`, `templates/safety/_rights_portability_job.html`.

Grafo consultado: `graphify-out/graph.json` de la candidata. Recorridos contrastados, entre otros: `discovery.results → state_page/order_population/PublicationContext`, `ingest → read_upload/decode_image`, `process → detect_matches` y `generate_portability_export → rights_portability_jobs.run`. Las aristas indirectas se interpretan con cautela y no acreditan por sí solas cobertura de ejecución.
