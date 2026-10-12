# MOD-08 — instalación de instrumentos y repetición en VPS

Preparación local para un VPS Linux con Docker y CPython 3.12 administrado por uv.
No se ha conectado, instalado ni ejecutado nada en el VPS. Usar un checkout de
pruebas con el estado actual integrado: hay fuentes aún sin commit en el equipo
local; copiar sólo un HEAD antiguo no reproduce la prueba. No trasladar `.env`,
credenciales, datos reales, bases de datos ni artefactos privados. No ejecutar
cargas contra producción ni publicar endpoints: el runner usa red interna,
PostgreSQL/Redis/RustFS/Caddy propios, datos sintéticos y retirada automática.

## Preparación del checkout de pruebas

Necesita Docker local accesible por el usuario, Git, uv, ldd/glibc, compilador C
si debe reconstruirse el kernel, y recursos disponibles para las cuotas agregadas
4 CPU / 8 GiB. El ejecutor comprueba el almacenamiento propio limitado a 20 GiB;
reservar además espacio para imágenes, dependencias y artefactos de infraestructura.
No relajar cuotas para obtener un PASS. Preferir una ventana sin otras cargas.
En un VPS registrar también CPU steal y presión: no hay un modo de batería que
arregle contención del hipervisor. No se cambian governor, sysctls ni servicios.

Desde la raíz del checkout:

```bash
uv python install 3.12.15
uv sync --frozen --python 3.12.15
bash scripts/install_diagnostic_tools.sh
```

El runner actual necesita el intérprete uv bajo `~/.local/share/uv/python` y el
socket local `/var/run/docker.sock`. No usar un daemon remoto ni un Python de otra
ruta sin adaptar/verificar primero el runner. El instalador usa un venv separado:
`~/.local/share/web-citas-diagnostics/venv` (o `$XDG_DATA_HOME`). Para cambiarlo,
exportar `WEB_CITAS_DIAGNOSTICS_VENV` antes de instalar y ejecutar. Nunca señalar
el venv de la aplicación. No necesita sudo ni cambia `uv.lock` de la aplicación.

Se fijan py-spy 0.4.2, Memray 1.20.0, Scalene 2.3.0 y pyperf 2.10.0;
[lock de herramientas](../scripts/diagnostics/requirements.lock) con dependencias
transitivas y hashes. Se exige wheel binaria: si no existe para la arquitectura,
la instalación falla explícitamente. `installation.json` registra versiones,
arquitectura y hashes. El lock se resolvió para Python 3.12; no actualizarlo
silenciosamente al repetir la medición. Herramientas gratuitas, sin nuevos servicios.

### Kernel y contenedores

Si el checkout no contiene un artefacto canónico válido para este Python/Linux,
construirlo con el builder existente en un venv de compilación separado:

```bash
uv venv --python 3.12.15 "$HOME/.local/share/web-citas-diagnostics/canonical-build"
uv pip install --python "$HOME/.local/share/web-citas-diagnostics/canonical-build/bin/python" 'Cython==3.0.12'
"$HOME/.local/share/web-citas-diagnostics/canonical-build/bin/python" scripts/build_canonical_kernel.py
```

Requiere `cc` y headers compatibles. El builder rechaza sobrescribir un directorio
existente: no borrarlo automáticamente. Si falla su identidad, revisar origen/ABI
antes de reemplazarlo. El lanzador exige `kernel_identity().mode == native-sealed`
y registra la identidad. Recompilar puede cambiar hashes del binario frente al
portátil; se conserva la evidencia del nuevo entorno, no se inventa igualdad binaria.

Preparar imágenes antes de medir, fuera del intervalo:

```bash
docker build -t web-modelos-app:latest .
docker pull postgres:17-alpine
docker pull redis:7.4-alpine
docker pull 'rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c'
docker pull 'caddy@sha256:881bbc60f9986d5ab8e7cfd6cf7e4ef3c9c0439fef2429d035d065577882f028'
```

El runner registra las identidades efectivas de imágenes. PostgreSQL/Redis tienen
tags mutables: conservar sus IDs en la comparación; si cambian, documentarlo.
No usar imágenes de otra arquitectura ni declarar comparable un fallback.

## Orden de ejecución

```bash
uv run python scripts/run_vps_capacity.py preflight
uv run python scripts/run_vps_capacity.py probe
uv run python scripts/run_vps_capacity.py measure
```

Ejecutar secuencialmente, sin editar fuentes durante cada comando. `preflight`
verifica topología/límites, sin carga contractual. `probe` comprueba py-spy nativo,
observación de PostgreSQL y reconexiones con rol restringido. No es capacidad.
Si el probe falla por permisos, conservar el error; no habilitar automáticamente
SYS_PTRACE, modo privileged, ni cambiar Yama/seccomp del servidor.

`measure` repite el escenario completo sin perfiladores, spans, wrappers SQL,
cProfile ni estadísticas añadidas por el modo diagnóstico. Dos casos concurrentes,
384 navegaciones y 20 descargas por tipo/caso; fuente de 16 MiB, originales de
unos 64 MiB y partes de unos 8 MiB. Se conservan todas las validaciones de frescura,
auditoría, integridad, autorizaciones y cuerpos. Umbrales p95: navegación 2 s;
JSON y binario 5 s. Un PASS de etapas no es aceptación global/N3.

Sólo si el resultado pide investigación, en otra ejecución:

```bash
uv run python scripts/run_vps_capacity.py diagnose
```

Diagnóstico existente de un caso con capturas py-spy/PG acotadas, sin superponer
los perfiladores antiguos. Sus tiempos no sirven para aceptar los umbrales.
Memray/Scalene quedan instalados e inactivos; usarlos por separado únicamente con
hipótesis específica. pyperf se reserva para microbenchmarks, no reemplaza HTTP.
[py-spy oficial](https://github.com/benfred/py-spy),
[Memray oficial](https://bloomberg.github.io/memray/getting_started.html),
[pyperf oficial](https://pyperf.readthedocs.io/en/latest/run_benchmark.html).

## Resultados y recuperación

`artifacts/vps-measurements/<id>/environment.json`: modo, argv, kernel, CPU/afinidad,
memoria, presión, CPU steal acumulado en `/proc/stat`, disco y energía al inicio/final.
Son metadatos de los extremos, no perfilador continuo ni explicación causal de
cada request. No almacena variables de entorno, credenciales o argumentos de
procesos del host. Bloqueo de lanzador y detección de entornos activos evitan cargas
superpuestas. No modifica los servicios existentes.

`artifacts/capacity-environment/<id>/`: resultado, XML con métricas, huellas de
fuentes, imágenes, límites, logs acotados y comprobación de limpieza. Conservar
fallos también. El recibo VPS enlaza el ID del runner; verificar `launcher.json`,
`report.json`, cero fallos/errores/skips, fuentes sin cambios y limpieza real.
Si el proceso se interrumpe y quedan recursos propios, usar el recuperador existente
con el ID exacto, nunca un prune general:

```bash
uv run python scripts/run_capacity_environment.py --recover ID_EXACTO_DEL_RUNNER
```

Última referencia del portátil en batería/rendimiento: 1,576682 / 4,163148 /
3,997933 s, sólo etapas locales. No atribuir diferencias del VPS a una optimización:
es otro hardware y puede haber CPU compartida. Primero evaluar sus límites propios.

## Verificación de esta preparación

Instalación real del lock en venv vacío local: cuatro herramientas responden.
Probe Docker/PG real `20261011-234614-8d848d74`: 1 PASS, 15,247 s,
NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY, fuentes sin cambios y limpieza verificada.
106 pruebas de contratos y separación pasan; Ruff y sintaxis shell comprobados.
El primer test de la nueva preparación falló en colección por un import del runner;
se corrigió el path de scripts y se repitió. No fue fallo del VPS ni evidencia de
capacidad. Después del probe se corrigió el argv exclusivo del preflight y se añadió
la guarda de identidad nativa; los cuatro modos se validaron contra el parser real.
No se repitió el recorrido completo ni se declara verificación remota.

### Verificación completa posterior

El lanzador completo sí se ha probado después: 20261012-001431-53a220c0,
1 PASS en 909,989 s; peores p95 1,611558/4,181215/4,166493 s.
La primera repetición falló al cerrar procesos y se conserva. Se añadió --init
estándar de Docker al contenedor propio y espera acotada de reaping, sin omitir
supervivientes. Preflight correctivo y probe nativo final pasan; 109 pruebas
locales pasan. Energía alternó externamente; no prueba constante ni mejora causal.
[Evidencia completa y fallo conservado](evidencias/mod08-vps-preparacion-verificada-20261012.md).

## Primera ejecución real en el servidor, 2026-10-12

La preparación local anterior precede al relevo remoto. Ya ejecutado en servidor
OpenStack:preflight/probe PASS, measure FAIL válido2casos/4CPU/8GiB, diagnose
separado PASS. Aplicación sin cambios; energía variable del portátil y CPUvirtual
diferente impiden comparación causal de código. [Resultados completos, por caso y
recibos](evidencias/mod08-vps-medicion-servidor-20261012.md). Usuario autoriza después
comparar8CPU, manteniendo el resto; implementación y medición de ese perfil pendientes.

## Perfil8CPU autorizado posteriormente

`--cpu-budget 8` duplica sólo CPU de servicios y controlador; default4 permanece
para reproducir la referencia. RAM8GiB,storage≤20GiB,workers y SLO iguales.
El host debe exponer8CPU; no se amplía el VPS ni se cambia su configuración.

```bash
uv run python scripts/run_vps_capacity.py preflight --cpu-budget 8
uv run python scripts/run_vps_capacity.py probe --cpu-budget 8
uv run python scripts/run_vps_capacity.py measure --cpu-budget 8
```

Secuencia/limpieza/datos/perfiladores y criterio de repetición siguen vigentes.
Un resultado8CPU no acredita4CPU ni N3. [Plan y verificación](evidencias/mod08-vps-perfil-8cpu-20261012.md).

## Diagnóstico profesional adicional autorizado

El usuario pide usar instrumentos gratuitos para investigar costes restantes.
`probe --cpu-budget 8 --professional-profile memray` verifica importación aislada,
rol/reconexión PostgreSQL propios y una petición marcada sobre Gunicorn real.
Después, `diagnose --cpu-budget 8 --professional-profile memray` captura sólo
cobertura temprana/tardía; no py-spy, observadorPG, spans ni cProfile simultáneos.
Measure/preflight rechazan esa bandera. Mismos datos, límites y validaciones.

Memray1.20.0 en venv readonly separado, paquetes app prioritarios y procedencia
comprobada; aplicación Python3.12.15. Traza256MiB máximo, resumen2M registros
máximo; si excede, conservar fallo. Tras resumen válido retira binarios para
evitar acumulación. Registra pico y volumen positivo de asignaciones/reasignaciones
por separado; contadores CPU/pared incluyen inicio/vaciado de Tracker.
No p95 ni atribución CPU por línea. Scalene aún sin adaptador Gunicorn comprobado.

Revisión independiente:32pruebas rápidas de separación/parser/WSGI PASS0.82s,
RuffPASS. Resumen sobre traza previa coincide exactamente con `memray stats`
4940078860bytes,202736registros; no sustituye sonda de contenedor. Evidencia real
de probe/diagnose pendientes al introducir el adaptador.

### CPU profesional con Scalene2.3.0

Nuevo modo `probe --cpu-budget 8 --professional-profile scalene`, seguido sólo
tras verificarlo por `diagnose --cpu-budget 8 --professional-profile scalene`.
Incompatible con Memray, py-spy y perfiles heredados; measure/preflight lo rechazan.
ScaleneCLI inicializa el maestroGunicorn con --cpu-only --off; sólo ventanas
marcadas usan start/stop y output_profile públicos. Dos workers sync iguales;
CLI agrega sus muestras al cerrar. CPU estadística por línea Python/nativo/sistema,
agregada para ventanas marcadas, no p95 ni porcentajes de pared.

Prueba previa realGunicorn con WSGIsintético en contenedor propio1CPU/512MiB,
sin redpublicada, pasóHTTP200 yJSONCPU agregado. Primer cierre señaló lanzadorCLI
intermedio y terminó-15: se corrige señalando su único hijoGunicorn observado.
Scalene sobreescribía SIGTERM enworker y causaba143; conservar el manejador de
Gunicorn durante captura corrige ese cierre, workers terminan sinERROR.
No APIs privadas ni cambios de sysctls/host. --init yobservación de descendientes
incluyen el lanzadorintermedio para no ocultar procesos/zombis/RSS.

La salidaCPU se compacta a líneas con muestras, números de línea y porcentajes,
sin source-text/arrayscrudos/locals/payloads, máximo2000líneas yraw16MiB. Hashraw
registrado. Sonda agrega CPU sintética0.15s para asegurar muestras en /health/;
ese burn no ocurre en coberturareal y no es prueba de coste de aplicación.

127tests de separación/cierre/parser PASS3.00s, RuffPASS. Un test AST anterior
falló por depender de runtime_settings reciénintroducido; namespace aislado
actualizado y nuevos contrastes COMPLETE/FAIL verifican detener flujo inválido.
Sonda app/PG real pendiente; no inferir aceptación de la prueba WSGIsintética.


Scalene 568ff53: probe real 20261012-085809-69e4aa37 PASS (51.545s),
pero diagnose 20261012-090224-1fc377fd ERROR: el flujo JUnit pasó
(1583.477s), ambas ventanas COMPLETE, y faltó el JSON combinado.
ScaleneAnalysis.is_native importa apps.core.models al renderizar en el maestro,
cuya registry Django no estaba inicializada. AppRegistryNotReady conservado.
Fuente 1414 archivos inalterada y limpieza independiente verificadas.
Estos tiempos son duración diagnóstica, no p95 ni aceptación.
Corrección instrumental: django.setup y close_all sólo tras salir Gunicorn,
sin preload ni cambio de arranque de workers; sonda sintética marcada incluye
rights_exports.canonical para ejercitar imports de dominio durante el merge.
54 tests rápidos PASS (0.73s), Ruff PASS. Sonda PG real pendiente antes de
repetir diagnose. No nueva optimización de aplicación ni medición HTTP limpia.


Sonda c892c08 20261012-094409-a7b09d5e: launcher 0, 1 PASS/0 fallos,
51.155s; fuentes 1414 idénticas, memoria superior 1140568064 bytes y limpieza
independiente verificadas. JSON final presente y sin AppRegistryNotReady,
pero CPU positiva sólo en helper, no en dominio. No basta para validar el
merge que falló. Se sustituye el burn SHA de la sonda por canonical con lista
sintética de 8192 enteros y se exige CPU positiva en /apps/safety/.
No se modifica captura coverage ni aplicación; repetir sólo esta sonda acotada.

| Evidencia | Diagnose 568ff53 | Sonda c892c08 |
| --- | --- | --- |
| Resultado runner | ERROR | PROBE_NOT_CAPACITY |
| JSON combinado | Ausente | Presente |
| CPU de aplicación demostrada | No | No; helper únicamente |
| Nueva aceptación p95 | Ninguna | Ninguna |


Sonda reforzada 35b5c97 / 20261012-094755-68d38932 PASS: launcher 0,
1 test/0 fallos/0 errores/0 skips, 58.595s; JSON combinado incluye CPU positiva
de fast_canonical, rights_exports y otros módulos de dominio (imports fríos
incluidos en esta sonda sintética, nunca interpretados como CPU de cobertura).
Sin AppRegistryNotReady. Auditoría independiente de fuentes y limpieza PASS.
Esta evidencia valida el instrumento, no capacidad ni SLO. Siguiente acción:
diagnose separado sin otros perfiladores; medir limpio después de corregir
con evidencia. Conservado el diagnóstico fallido 090224, sin sustituirlo.

| Sonda | c892c08 | 35b5c97 |
| --- | --- | --- |
| Duración de test instrumental | 51.155s | 58.595s |
| JSON combinado | Presente | Presente |
| CPU positiva en dominio | No | Sí, incluyendo imports sintéticos |
| Fallos / errores | 0 / 0 | 0 / 0 |
| Nueva latencia HTTP aceptable demostrada | No | No |


Diagnose Scalene 8af315a / 20261012-095117-11c3b82a PASS diagnóstico,
no aceptación: JUnit 1PASS1566.464s, dos ventanas COMPLETE y JSON combinado
validado. Auditoría fuentes1414/limpieza/archivo PASS. Evidencia versionada en
docs/evidencias/mod08-vps-scalene-cobertura-20261012.md y .json.
Pendiente análisis causal/corrección y p95 HTTP limpio; global/N3 no aceptado.


## Diagnóstico SQL tardío aislado, continuación 2026-10-12

Autorizado por «investiga pues». Nuevo parámetro exclusivo:
`uv run python scripts/run_vps_capacity.py diagnose --cpu-budget 8 --sql-plan-target 304`.
Usa la misma infraestructura propia y cuotas; no py-spy/Memray/Scalene,
ni wrappers de tiempo heredados, ni background Celery. Selecciona el test
finito de planes existente con niveles 0/304; conserva tope 420s de siembra,
90s por hijo y 15s por SQL. No ampliar si no llega al nivel tardío.

Fixture 1500 revisiones/~16MiB y originales físicos/~64MiB creado por servicios.
Los 304 lotes son inspecciones escalares repetidas, con commits/auditorías
normales, no filas de evidencia fabricadas. Flujo parcial; verificador de
identidad simulado explícitamente, PostgreSQL/HTTP sí reales. Objetos/proxy
propios disponibles en topología pero este ensayo no acredita su entrega.
Dos workers Gunicorn sync, roles propios separados. EXPLAIN en login exclusivo
no propietario, checks de permisos y atestación frescos, cabeza bloqueada;
comparación exacta de hashes del corpus antes de planes. Se registra ausencia
de otras conexiones activas de ese mismo login. Las 8 consultas son las actuales
EVENT+7sources. No cambios de esquema/índices/planner ni candidata inline
productiva. Relojes separados execute/fetch del driver, SQL hash y planes con
TIMING OFF/ON y SERIALIZE TEXT. No p95 HTTP ni CPU pura de PostgreSQL.

46 tests rápidos PASS/1.36s, Ruff de los cambios PASS. Sources se congelarán
antes de ejecutar; registrar resultado/fallo, SHA, versiones y limpieza real.
No atribuir diferencias del portátil a código ni declarar N3/global.


Corrección de adaptación, posterior al primer terminal SQL:
431149c / 20261012-111350-eba253e3 ERROR:1FAIL532.004s, agotado tope
420s de siembra. Plan temprano36eventos completo, rol exclusivo0otros activos,
fuentes1415 idénticas, archivos y cleanup auditados; RAMupper1498865664bytes.
No plan tardío ni aceptación. El límite420 era de la prueba original64lotes;
se aplicó indebidamente al nuevo tamaño304(4.75veces). Fallo conservado.
La variante64 retiene420s; la explícita304 tendrá1200s finitos para preparación,
dentro del tope9000 del runner. No cambia15s por sentencia/90s por hijo,
CPU8/RAM8GiB/storage20GiB ni SLO2s/5s. No cambio de aplicación/performance.
Checkpoints de siembra se registrarán también en JUnit para conservar el último
estado en cualquier fallo. Ésta es una corrección del instrumento, no una
reescritura SQL especulativa ni una medida de mejor rendimiento.


SQL tardío terminado: db52437 /20261012-112648-cc0ad6f8, JUnit1PASS805.570s,
0fallos/errores/skips;304lotes/heads36→2468, roles restringidos exclusivos y
hashes exactos/8consultas/captura, fuentes1415/archivo/cleanup independientesPASS.
LauncherEXIT1 conservado: nueva etiqueta SQL_PLANS_DIAGNOSTIC_NOT_CAPACITY
omitida en lista final de éxitos. Fix clasificación, expresión real de exit
verificada para SQL0/ERROR1/falloSLO1, RuffPASS; sin rerun carga. Resultado
científico válido, no launcherPASS ficticio ni capacidad. Evidencia versionada
[evidencias/mod08-vps-planes-tardios-20261012.md](evidencias/mod08-vps-planes-tardios-20261012.md).
No índicefaltante observado en corpus caliente: tardío eventos33.832ms versus
controlinline19.661;SelectionRead37.818/21.781;CoverageRead36.060/23.243.
Misma estructura de planes por variante,0reads/spills traswarmup. NoHTTPnuevo,
no aplicacióneditada ni restitución inline retirada. Próximo: sólo candidata
con beneficioHTTPVPS demostrado o rediseño redundancia con garantías exactas.
No extrapolar sumasmedianasonline ni atribuir portátil al código. N3pendiente.
