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
