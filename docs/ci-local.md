# Verificación propia sin CI de pago

Decisión del usuario2026-10-09: gestionar CI con recursos propios porque no hay presupuesto para servicio alojado. Ejecutar [el runner local](../scripts/run_local_ci.py) desde la raíz del repositorio. La verificación local pasa a ser el entorno autorizado; facturación y runners de GitHub no son un prerrequisito. No implica contratar, publicar ni aceptar fases pendientes.

## Uso

```bash
# Calidad, documentación, Django y ausencia de migraciones sin generar.
uv run python scripts/run_local_ci.py --profile checks

# Prueba breve: broker, publicación e invalidación, Redis físico nativo.
uv run python scripts/run_local_ci.py --profile smoke --native-source /ruta/al/checkout/librdb

# Regresión funcional; registrar previamente la selección en seguimiento17.
uv run python scripts/run_local_ci.py --profile regression --native-source /ruta/al/checkout/librdb

# CR09: identidad, censo, cobertura, recursos y respuesta de acceso sintéticos.
uv run python scripts/run_local_ci.py --profile rights --native-source /ruta/al/checkout/librdb

# Reproducción/regresión acotada: archivos o nodos explícitos bajo tests/.
uv run python scripts/run_local_ci.py --profile focused --native-source /ruta/al/checkout/librdb --test tests/test_account_mail_projection_templates.py

# Suite completa, incluidos ensayos largos; registrar autorización y recursos antes.
uv run python scripts/run_local_ci.py --profile full --native-source /ruta/al/checkout/librdb --timeout 21600
```

El checkout librdb debe estar en el commit `bc5f295c98b40c2c33099d9d72ab30ce9e595dc7`, con hiredis `869f3d0ef1513dd0258ad7190c9914df16dcc4a4` y sin cambios en fuentes versionadas. El runner copia el checkout a su temporal antes de compilar; no altera el original. Detalles de herramientas y procedencia: [orígenes91](91-origenes-redis-rdb-aof.md).

Prerrequisitos instalados: Docker accesible, Git, uv, compilador C/make, redis-server local para fixtures de socket Unix, dependencias uv en caché y Chromium de Playwright para perfiles que usan navegador. Imágenes locales `postgres:17-alpine` y `redis:7.4-alpine`. El runner usa `--pull=never` y sincronización offline: falta de caché/imágenes es ERROR explícito, no descarga o instalación silenciosa. Preparar las dependencias necesarias con los comandos del [README](../README.md); no exige comprar servicios.

## Aislamiento, evidencia y resultado

Cada ejecución crea nombres Docker únicos, puertos dinámicos ligados a127.0.0.1, PostgreSQL en tmpfs, Redis propio y un directorio temporal para medios, fixtures y compilación. Utiliza únicamente credenciales sintéticas; no hereda configuración de producción, broker normal o switches de benchmarks. No detiene, vacía ni migra servicios normales. Al terminar o interrumpirse, elimina sus contenedores/volúmenes y temporales. Una terminación forzada del propio runner o caída del host puede impedir su limpieza: consultar los nombres exactos en los logs antes de retirar recursos propios.

Evidencia durable en `artifacts/local-ci/<fecha-id>/`: logs por paso, huellas de archivos fuente actuales (incluidos cambios locales), HEAD, selección/exclusiones, duraciones, resultado, limpieza y, si hubo pruebas, JUnit con propiedades y manifest de herramientas nativas. Los binarios temporales se retiran; su manifest conserva huellas y versiones. Directorio ignorado por Git: para registrar una entrega, conservar el resultado y los artefactos pertinentes en `docs/evidencias/` tras revisión de Codex. No copiar datos reales ni interpretar rutas a temporales retirados como recursos todavía disponibles.

PASS significa que todas las comprobaciones seleccionadas terminaron correctamente y las fuentes se mantuvieron iguales. El perfil `checks` no ejecuta pruebas. Cualquier fallo/timeout/interrupción produce salida distinta de cero; cambios en fuentes probadas producen INVALID. Los skips y exclusiones se enumeran y no acreditan el alcance omitido. Documentación puede actualizarse durante una ejecución sin alterar fuentes funcionales; sus enlaces deben comprobarse nuevamente al cerrar la entrega.

## Alcance y ensayos largos

`smoke` selecciona tres archivos explícitos; su PASS verifica el ejecutor y esos escenarios, sin sustituir regresión completa. `regression` ejecuta la suite restante y excluye expresamente carga HTTP `short`/`measured`, historial de1.500revisiones y matriz TCP100/1.000/10.000. Estas exclusiones constan en `result.json`; la calibración HTTP funcional de3s permanece incluida. No son una declaración de cierre de capacidad.

`focused` exige al menos un `--test` (archivo o nodo pytest) existente dentro de `tests/`; rechaza rutas externas y no admite esos argumentos en otros perfiles. Conserva la selección exacta, checks, herramientas nativas, integridad de fuentes y limpieza de los demás perfiles. Permite reproducción y regresión pertinente; no sustituye N3. `rights` selecciona18 archivos explícitos de identidad/censo/cobertura/respuesta/recursos.

`full` no excluye esos casos. Experimentos optativos que requieren variables de autorización siguen con sus skips originales, también registrados; ejecutar la suite completa no los convierte en PASS. Ensayos de capacidad mantienen los criterios y prerrequisitos del [contrato16](16-contrato-ejecucion-desarrollo.md), [seguimiento17](17-seguimiento-desarrollo.md) y [propuesta de expedientes](propuesta-cierre-pendientes-locales.md). Un host compartido limita la atribución de rendimiento.

GitHub Actions queda con disparo manual, sin ejecución automática por push/PR. No se configura un runner permanente, hooks, cron o publicación externa en esta entrega. El operador/Codex ejecuta el gate local antes de integrar cambios y archiva evidencia de la misma versión. La aceptación N3 conserva sus requisitos; revisión independiente y decisiones jurídicas/operativas continúan pendientes cuando corresponda.

## Verificación inicial del ejecutor

2026-10-09: perfil `smoke`,70 pruebas PASS/0 skips en357,03s con PostgreSQL y Redis reales propios; compilación nativa, calidad, documentación y migraciones PASS. Tras reforzar el postprocesamiento, `checks` final PASS y control de checkout inexistente devuelve ERROR/salida1 conservando informe y retirando recursos. Se verificó la ausencia de los seis contenedores de las tres ejecuciones. [Resultado y versiones](evidencias/ci-local-20261009.json), [logs/JUnit/manifests/huellas](evidencias/ci-local-20261009-artefactos.tar.gz). No se ejecutó regresión completa ni capacidad; estos runs no forman una aceptación N3.

## Restauración con el servidor propio

`test_recovery_pg_restore.py` y su variante comercial usan `LOCAL_CI_POSTGRES_CONTAINER` asignado por el runner y validan su nombre/puerto contra la conexión PostgreSQL activa. Ejecutan pg_dump/pg_restore del propio contenedor; no necesitan los clientes PG del host ni usan el Compose normal. Bases restauradas, medios, claves y checkpoints son sintéticos/desechables. [Prueba final y límites](evidencias/restauracion-ci-mod05-final-20261009.json). Para ejecutar esos tests fuera del gate hacen falta herramientas PG locales compatibles con la conexión de pruebas; falta de herramientas no se oculta como simulación o skip.
