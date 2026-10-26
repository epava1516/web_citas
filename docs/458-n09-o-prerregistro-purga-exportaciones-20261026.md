# N09O — prerregistro de purga de exportaciones

Estado: referencia finita pendiente; sin cambio de aplicación ni aceptación N09.
Base `665645e9597cb22e3e927a4a1abc433d2edd87c7`. N09 abierto,139IDs y8/13
bloques obligatorios aceptados. Alpha/noindex. N02 restante diferido por el usuario
al final del desarrollo; N10/N11/N15 pendientes yN12–N14 condicionados.

Corte previo: grafo focal verificado de2.101fuentes,20.564nodos y85.282relaciones,
SHA256 `171f4bcaa0027ae8c3ec4a3e901638bb6fceca9b67c2feb032c9e1f7e908d386`.
Incluye mantenimiento de disco, sin reconstrucción N15. Actualizar AST del
instrumento y semántica de este protocolo antes de congelar y medir.

Consumidor: `apps.safety.tasks.purge_expired_exports.run()` selecciona hasta1000
exports vencidos no purgados, ordenados por PK, bajo transacción yskip_locked.
Primero purga deliveries y objetos externos; después vacía contenido Image/Part,
payload ymarca purged_at. Conserva fuentes y evidencia mínima. Una baja física
anterior no puede revertirse por rollback SQL. Esta medición examina precisamente
la selección y coordinación del consumidor, sin repetir generación de paquetes.

Selección: siete casos previstos. Cinco volúmenes0/1/10/100/1001vencidos;
primera selección min(N,1000), remanente1sólo para1001yreplay0. Un caso con tres
vencidos y un export bloqueado por otra conexión PostgreSQL:2mientras lock,
1tras liberación yreplay0. Un caso con dos vencidos y fallo controlado antes del
segundo unlink local: primera baja física persiste, SQL íntegramente revierte,
segundo archivo permanece; restituir unlink, recuperación2yreplay0. No caída
abrupta real, avería externa ni rollback físico. Ajustar el detalle sólo antes de
medir si la revisión de la fixture detecta una precondición incorrecta; conservar
cualquier intento fallido posterior y su causa.

Datos: un seed nativo por servicios existentes; volumen con clones sintéticos
pequeños y acciones únicas. Cada export objetivo tendrá payload Fernet, contenido
Image/Part y archivo de delivery local propios. Mantener pines fresco y ya purgado.
Las filas clonadas no equivalen a nuevas verificaciones, aprobaciones o ejecuciones
HTTP. Almacenamiento de objetos deshabilitado en esta referencia; pruebas reales
previas de repositorio S3/tombstone conservan su alcance separado. No generar
paquetes grandes, contratar proveedor, activar servicios ni cambiar el producto.

Oráculos: comparar filas completas de exports, imágenes, partes ydeliveries;
sólo se permiten los vaciados ymarcadores correspondientes al conjunto seleccionado.
Preservar IDs, FK, auditoría, fotos, fuentes yotras tablas; snapshot de modelos
instalados incluidos through ysesiones. Medios yárbol local se contrastan por
bytes/mtime/modo yhashes, rechazando symlinks. Archivos restantes sin modificaciones.
En fallo parcial, todas las filas SQL coinciden con el estado anterior, aunque el
primer archivo haya desaparecido. En lock, comprobar PID distinto, finalización
con holder activo, statement_timeout10s/future15s yfinalmente cerrar conexiones
yejecutor. No modificar ninguna base o recurso ajeno al runner propio.

Medidas: wall únicamente alrededor de Task.run, conteo/tiempoSQLexecute yoperación
sin texto ni parámetros, unlink real observado con conteos/tiempo yfallo controlado
acotado. Son etapas anidadas, no sumables; SQLexecute puede excluir fetch. Una
muestra por fase, caché calentada, contenido pequeño yvolumen acoplado; sin p95,
capacidad histórica, SLA ni comparación causal. Preparación, snapshots, asserts,
limpieza ytiempoQA separados. Tabla posterior mostrará referencia observada y
«no evaluable» para mejora atribuible si no hay candidato.

Gates: escritor nativo aislado propietario sólo del instrumento yreporte ignorado;
worktree sparse sin copiar evidencias históricas. Root revisa diferencia, modelos,
propiedad, oráculos, privacidad ycleanup con django-reviewer/code-security.
Después Ruff yAST/semántica focal, fuentes congeladas, runnerfocusedserial con
PostgreSQL/Redis desechables propios yparserJUnit nativo. Auditar resultados,
fases, fuentes, recursos ausentes yreciboTelegram antes de aceptar; no declarar
worker/Beat desde Task.run. Las pruebas largas siguen el protocolo persistente
vigente; no iniciar ni repetir baterías por disponer de nuevas skills.

Conciliación: matriz de trabajo139/139en
`artifacts/recorridos-n09-o-20261026/139-conciliation-working-matrix.json`, aún sin
aceptación por ID. Dos fuentes compartidas difieren de las propuestas iniciales
(complaints/privacy_release); deben conciliarse con sus correcciones aceptadas,
no reutilizar la propuesta como evidencia actual. Después de esta referencia
quedan los puentes productores ydisposiciones finales, sin duplicar alias Beat.

Límites: no nueva autorización HTTP, retención natural, proveedor, carga de objetos,
worker/Beat ni generación/descarga actuales. Conservar los originalesPASS vigentes
yel ERRORglobal histórico. No reabrir optimizaciones marginales diferidas por el
usuario, ampliar el contrato ni modificar migraciones, servicios oCI.
