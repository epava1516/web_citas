# MOD08 pieza10: implementación del baseline y bloqueo verificable

Base de la inspección: `5820942`, worktree aislado
`mod08-p10-diagnostic-baseline`. Preparación offline durante el perfil vivo
`20261010-140801-58565769`. No se han ejecutado tests, imports del proyecto,
compilación, generación de datos, captura/restauración ni carga. Este documento
**no implementa una caché** y no declara terminada ni aceptada la pieza10.

## Bloqueadores observados en el código actual

1. `scripts/check_capacity_environment.py` crea `RIGHTS_OBJECT_KEYS` mediante
   `os.urandom(32)` en cada run de objetos, con id visible `capacity-v1`; el id
   permanece, pero el material cambia. También fija
   `RIGHTS_DELIVERY_GENERATION=run_id`. Una huella de configuración/keyring exacta
   rechaza el baseline de cualquier run previo. Comparar sólo `capacity-v1`
   ocultaría una rotación real. No puede prometerse ahorro inter-run bajo la
   política actual: el resultado correcto sería siempre CACHE_REJECTED.
2. `rights_validation_seal.rule_version()` cubre todas las settings mayúsculas,
   además del código apps/config. No se puede transportar un sello de otro
   módulo/rol/runtime y asumirlo válido. El baseline debe terminar antes de
   generación, contener **cero sellos/exportaciones/jobs/deliveries**, y validar
   sus aprobaciones con los validadores completos originales. Cualquier sello
   posterior debe crearse en el runtime nuevo. Esto no autoriza a reetiquetar,
   renovar o volver a firmar la evidencia original de lectura/aprobación.
3. `capacity_delivery_flow.run_case` llama a `finish` inmediatamente después de
   la aprobación real de cobertura. Falta una frontera donde detener el recorrido
   antes de generación, cerrar Gunicorn/Celery/Beat y capturar en una base sin
   conexiones externas. Copiar la DB mientras esos procesos sigan conectados no
   satisface el criterio del proyecto; tampoco se permite terminar sus backends.
4. El controlador sólo permite escribir su archivo `artifacts.tar`. `ArchiveSink`
   lo abre con O_TRUNC; admite texto, 32MiB por miembro y 256MiB de archivo total.
   El launcher no recibe ni monta un baseline de entrada. Su contabilidad incluye
   los tmpfs actuales más ese archivo de salida; no incluye un archivo de entrada
   durable. Usar el tar existente como caché mutable o un directorio externo no
   contabilizado violaría aislamiento/integridad o el criterio de presupuesto.

Estos bloqueos se deducen de las rutas concretas anteriores, no de una prueba
simulada. No se ha medido que el presupuesto exceda 20GiB/8GiB, ni que un snapshot
quepa: esas mediciones y su admisión están pendientes. No se toca el controlador
congelado del perfil vivo ni se importa un keyring ajeno para producir un hit.

## Cambio de política mínimo requerido

Codex debe fijar explícitamente una modalidad diagnóstica de **reutilización del
keyring original**. El keyring se conserva cifrado en el baseline privado y sólo
se importa en los contenedores nuevos propios de un run diagnóstico. No se publica,
no se imprime y no se toma del keyring recién aleatorizado para re-cifrar evidencia.
El bootstrap consume su versión y su huella material originales **antes** de
iniciar servidores. Una rotación solicitada, clave ausente o huella distinta
rechaza la caché y vuelve al recorrido completo con un keyring nuevo.

La clave de envoltura del baseline es distinta del keyring de objetos y proviene
de un archivo privado 0600 del operador local/fixture, montado de sólo lectura y
contabilizado. Su material no está en el archivo cifrado ni en CLI/env/JUnit. Si no
hay clave privada vigente/versionada, el baseline se rechaza. No se contrata un
servicio de claves ni se utiliza material externo al entorno sintético propio.
Esta elección permite un hit verificable; no se presupone aprobada por la simple
existencia de esta propuesta.

## Frontera y consumidores concretos

| Archivo | Cambio propuesto |
| --- | --- |
| `scripts/check_capacity_environment.py` | Flags/admisión de presupuesto, settings de diagnóstico, mount readonly de entrada, ejecución del capturador tras teardown y antes de retirar recursos propios. |
| `scripts/run_capacity_environment.py` | Validación de flags antes de output/resources, apertura segura de entrada/clave y registro del tamaño máximo adicional. Recuperación de recursos declarados de ese run. |
| `scripts/capacity_artifacts.py` | API binaria por chunks acotados; conservar cuotas de32MiB/miembro,100miembros y256MiB archivo, reservar report final. Nunca O_TRUNC sobre entrada. |
| `tests/capacity_delivery_flow.py` | Punto después de coverage_review real y antes de finish; callback diagnóstico que devuelve descriptor privado y termina sin generación. Ruta posterior reutilizable llama finish, sin fabricar reads/decisiones. |
| `tests/test_capacity_delivery_profile.py` | Captura después del recorrido completo real, o restauración+validación antes de arrancar servidores. Emitir etiqueta baseline-hit sólo diagnóstica. |
| Nuevo `tests/diagnostic_baseline.py` | Exportar/importar PG/media/S3 propios, AEAD/chunks/manifest, integridad, expiración original y validadores completos. No se introduce un helper optativo sin esos consumidores. |

Los flags serían mutuamente exclusivos
`--diagnostic-baseline-capture` y `--diagnostic-baseline-use <archivo>`; ambos
requieren `--delivery-profile --delivery-profile-full --object-delivery
--owned-controller`. Se rechazan con `--delivery-complete`, N3/aceptación,
preflight-only, selection-complete y cualquier modo que compute PASS/SLO.
El rechazo ocurre en parse_options, también en el launcher, **antes** de mkdir,
crear archivos, red, contenedores o volúmenes. El proceso test recibe sólo rutas
privadas, modo diagnóstico y un id opaco; nunca secretos o estados aprobados como
argumentos. Una ausencia de baseline/clave puede registrarse CACHE_REJECTED y
reconstruir, sin cambiar a una modalidad de aceptación.

## Formato, integridad y expiración

Formato versionado `mod08-diagnostic-approved-baseline-v1`:

- Manifest exterior mínimo: id opaco, versión, tamaños, número/orden de chunks,
  SHA256 de cada ciphertext y cuota declarada. Nada de usuarios, receipts,
  read_ids, sesiones, rutas personales ni claves. El manifest también queda
  autenticado como AAD; no basta SHA256 sin autenticación.
- Manifest interior cifrado: commit y hash de todas las fuentes apps/config,
  migraciones, serializadores, librerías fijadas y los scripts/tests del recorrido;
  versión PG/Django/codec/canónica/chain; configuración de dominio canónica;
  hashes de material y versiones de claves; esquema, constraints y funciones
  de triggers; semilla y dimensiones1500/16MiB/64MiB; IDs exactos del expediente,
  actores, proof, assessment, selection, cobertura y lecturas originales; hash de
  fuente y de cada archivo local/objeto; tiempos originales con offset UTC.
- Guardar `valid_until = min` de proof, assessment, selection, coverage, receipt y
  cualquier vigencia adicional de las evidencias guardadas. Restaurar compara
  también cada expiración DB con el manifest, y rechaza `now >= valid_until`.
  No editar clocks, expires_at, case_version, payload_digest, firmas, read_ids,
  sesiones/versiones originales ni RateWindow para lograr un hit.
- Configuración efímera de transporte (nombre de contenedor/red, login runtime,
  DB test y rutas de medios propias) se recoge separadamente y se vuelve a
  acreditar. Su normalización es una lista explícita versionada; no se excluyen
  reglas, claves, política de privacidad, proveedor ni parámetros de evidencia.
  Los sellos genéricos no participan del baseline y mantienen su semántica actual.
- PostgreSQL: pg_dump custom de la base test completa y schema/migration manifest;
  no reconstrucción por ORM de estados aprobados. El exportador cifra a chunks
  acotados; directorio0700/archivos0600 en tmpfs propio. Media y S3 se exportan con
  hashes y rutas relativas permitidas, sin symlinks/traversal. La lista de S3 se
  enumera y valida realmente: no se supone vacía por estar antes de generation.
- Snapshot fuente: entrada readonly y hash/autenticación antes y después de uso;
  nunca se actualiza para adaptarla. Rotación o cambio de código produce rechazo.

La autenticación del archivo acredita que el capturador autorizado lo creó; no
sustituye las pruebas de procedencia. El capturador sólo emite un baseline tras el
recorrido HTTP real completo: todas las páginas31 de selección,16 lecturas
binarias y1509 páginas de cobertura, incluida la decisión independiente real.
Guarda la relación a su evidencia de captura y las cuentas exactas obtenidas de
la DB. No genera IDs ni inserta filas de aprobación mediante un constructor.

## Restauración y validación fresh

1. Acreditar nombre/label/run/network de PG/media/S3 propios en el controlador y
   el DB test/worker exacto. Prohibir servicios normales, propietario en servidores
   y conexiones ajenas. Tras apagar sólo los hijos del contexto propio, exigir
   cero conexiones mediante pg_stat_activity. Ocupación implica CACHE_REJECTED;
   no pg_terminate_backend ni DROP cuando esté ocupado.
2. Restaurar en DB scratch propia con nombre declarado en resources/recovery,
   nunca directamente sobre la base activa. Restaurar media/S3 en namespaces
   privados nuevos dentro de sus cuotas; verificar AEAD y hashes en streaming.
   Volver a acreditar triggers, permisos de columna y rol LOGIN real; provisionar
   GRANTs después de restore para no perderlos al importar la DB.
3. Revalidar actores actuales, actividad, permisos, MFA/session_version,
   reviewer independiente, proof actual no expirado ni purgado, case/version,
   fuentes e imágenes originales. Usar los validadores completos
   `consume_approved_coverage` y `consume_selected`, que replayan decisiones,
   read_ids y guards actuales; nunca crear lecturas o approvals nuevos para
   sustituir los originales. No reutilizar tickets/head de otro proceso como
   prueba suficiente. Ejecutar validate_chain completo bajo el nuevo runtime.
4. Los intentos auditados de uso derivados de esos validadores se crean sólo en
   la copia restaurada y son acciones reales. Para validar antes de adoptar la
   copia, hacer esa pasada en transacción rollback, manteniendo todo el replay
   completo; la generación posterior mantiene sus auditorías normales.
5. Sólo tras validación completa adoptar la DB scratch, iniciar los servidores
   con credenciales privadas nuevas y ejecutar generation/etapas posteriores
   reales. Los cambios legítimos posteriores de proof/estado siguen el flujo
   normal; nunca prolongan `valid_until` del baseline ni autorizan restaurarlo de
   nuevo una vez caducado. Su preparación reutilizada no son lecturas nuevas.
6. En rechazo destruir **sólo** scratch/copias propias, registrar razón minimizada
   y reconstruir prepare_target+run_case completo con evidencia nueva real.
   Error de cleanup/presupuesto/integridad del entorno invalida el diagnóstico;
   no se disfraza como rechazo recuperable ni como PASS de capacidad.

## Contabilidad que falta implementar

El controlador debe comprobar antes de leer/desencriptar:

`storage_max = tmpfs_declared_existing + output_archive_max256MiB
               + input_baseline_max256MiB + private_wrapping_key_file_bound`

El input readonly también cuenta aunque no sea writable. Las copias scratch DB,
media, ciphertext y S3 quedan **dentro** de los tmpfs existentes declarados; si
requieren otro mount, su máximo se suma explícitamente. Las quotas no se suben
silenciosamente. Todo dump/plaintext/ciphertext transitorio permanece en tmpfs
propio, nunca en /home, volúmenes normales o filesystem del host no contabilizado.
La caché no añade servicios que escapen de las asignaciones8GiB/4CPU; buffers por
chunk limitados se cargan a los cgroups actuales y memoria de tmpfs ya se cuenta.

Conservar el techo por archivo32MiB exige chunks binarios con API acotada y
etiquetada; base64/texto por el writer actual sólo amplifica bytes y no acredita
cifrado. Rechazar capture si el conjunto final supera256MiB, el número de miembros
reservado o una cuota tmpfs, preservando ejecución real y evidencia del rechazo.
Para reuse contar el archivo montado completo, no sólo los bytes seleccionados.
Registrar kernel limits, filesystem lleno, source/destination bytes, tiempos
build/capture/restore/validate y peaks simultáneos; nunca inventar ahorro neto.

## N2 finita necesaria después de coordinación

Baseline creado por recorrido real de un dataset pequeño, con todos sus reads y
aprobación independientes reales, PG17/media/S3 cifrado y runtime LOGIN noowner.
Restaurar con bytes/IDs/expiraciones idénticos y fresh guard completo. Mutaciones
de usuario/permisos/sesión/MFA/proof/origen, expiración real, ciphertext/medio
corrupto, esquema/keymaterial distinto y conexión externa viva deben rechazar y
probar fallback real. Probar rechazo temprano de flags de aceptación, rollback
de revalidación, cache fuente readonly, aislamiento de workers/scratch, limpieza
exacta y contabilidad de entrada/artefactos/todos los tmpfs. El test no se salta
lecturas; el dataset pequeño sólo reduce dimensiones para la verificación N2.

Después, diagnóstico separado con tamaño objetivo para medir ahorro total y
presupuesto. No se autoriza una carga nueva por este documento. Hasta fijar la
política de keyring y completar consumidores/contabilidad/verificación, pieza10
continúa en diseño con los bloqueadores anteriores documentados.

## Preparación de implementación posterior autorizada

Codex autorizó resolver los cambios internos de keyring/contralador. Se ha escrito
una implementación conectada en el worktree aislado, sin ejecutar nada mientras
está vivo el perfil posterior. La captura detiene run_case después de la aprobación
real de cobertura y antes de finish; tras teardown de servidores hace COPY nativo
PostgreSQL en snapshot REPEATABLE READ READ ONLY y captura los medios originales.
S3 se enumera realmente y se exige vacío en esa frontera pre-generation; un objeto
inesperado rechaza la captura, no se omite de una lista por conveniencia.

El archivo AEAD usa frames4MiB autenticados por orden/nonce, manifest inicial
privado y footer SHA256 autenticado que rechaza truncamiento. El controlador
transfiere ciphertext por fragmentos8MiB al tar limitado256MiB; el lector concatena
sólo miembros indexados y acotados sin cargar el baseline entero. El keyring de
objetos original se importa del header autenticado antes de arrancar contenedores.
La clave de envoltura privada32bytes es archivo0600 readonly, nunca CLI/env/logs.
La suma de cuotas incluye baseline de entrada y clave además de la salida actual.

La restauración construye una DB scratch de esquema actual exacto, restaura COPY
con constraints deferred y desactiva exclusivamente el trigger chain INSERT bajo
migrador durante importación para preservar las filas/eventos originales; lo vuelve
a activar antes de validar. Se reponen sequences, se acredita runtime noowner y
se replayan los validadores completos de cobertura/selección más validate_chain en
rollback. Sólo después se adopta la copia y se arranca un runtime LOGIN fresh.
Errores de versión/clave/expiry/evidencia causan CACHE_REJECTED y recorrido completo;
fallos de cleanup/DDL no se ocultan como cache hit. Se conserva valid_until original.

Esta preparación **todavía no está verificada**: faltan lint, framing/flags y N2
PostgreSQL/media/S3 reales en ventana coordinada; no acredita caché funcional,
ahorro ni aceptación. Los tests de framing/flags están escritos pero no ejecutados.
El documento anterior de bloqueo describe la base original; las modificaciones
propuestas lo resuelven internamente, condicionadas a las verificaciones pendientes.


### Implementación conectada y verificación pendiente (2026-10-10)

La rama `codex/mod08-p10-diagnostic-baseline` incorpora los flags
`--diagnostic-baseline-capture` y `--diagnostic-baseline-use <artifacts.tar>`,
ambos con `--diagnostic-baseline-key <fichero privado de 32 bytes>` y únicamente
con el perfil completo diagnóstico, recursos propios y entrega S3 real.
El parser rechaza las combinaciones de aceptación antes de crear recursos.
El fichero de clave y el archivo de entrada se montan en lectura exclusiva;
ambos cuentan, junto con el archivo de salida limitado a 256 MiB y todos los
tmpfs, dentro del techo existente de 20 GiB. No se modifican 4 CPU, 8 GiB ni swap0.

El recorrido real completo detiene su consumer tras aprobar cobertura, antes
de generar; sale del contexto Gunicorn/worker/Beat y sólo entonces captura.
PG usa COPY nativo bajo snapshot repeatable-read, media conserva bytes y SHA256,
y el catálogo S3 se consulta realmente: debe estar vacío en este límite anterior
a generación. No se copian objetos de exportaciones ni se acepta un namespace
previamente poblado. El manifest cifrado contiene código, esquema, configuración,
material original del keyring, descriptor y expiración original mínima.
COPY/media se comprimen en un tar gzip antes de cifrar (expansión máxima
512 MiB, dentro de tmpfs con techo real). El payload usa AES-GCM en bloques de 4 MiB con contador autenticado y footer
SHA256 autenticado; el controller transfiere fragmentos de 8 MiB al único tar
privado, sin materializar el payload entero en sus 128 MiB.

La restauración acepta únicamente un worker propio vacío y sin conexiones
externas; no termina backends. Importa a una base scratch con rol migrador,
restaura triggers antes del commit y revalida con un rol nuevo no administrador:
ACL y funciones reales, cadena completa, origen, autoridad, proofs y todos los
reads/reviews originales mediante `consume_approved_coverage`. La validación
revierte sus intents de auditoría. No cambia ningún expires_at. DB y media se
adoptan con nombres de respaldo para poder revertir una adopción incompleta;
una autoridad actual poblada nunca se sobrescribe. Rechazo de formato, código,
configuración, integridad, expiración o autoridad vuelve al recorrido real
completo. Un hit continúa generación normal, nunca constituye PASS/N3.

Validación ejecutada hasta ahora: Ruff, compilación y cinco guards puros de
framing/flags (5 PASS, 0,45 s, Django desactivado; un aviso por opción de
configuración sin ese plugin). La prueba finita PG/media/S3 real está preparada
pero **no ejecutada**: requiere ventana coordinada por Codex raíz. Tampoco se ha
probado ni afirmado ahorro en el dataset objetivo. La primera captura útil sólo
puede realizarse después de integrar las correcciones de origen/fingerprint y
cerrar los gates PG; un cambio de código invalida la captura anterior.
