# MOD-08 — medición real del servidor con 4 CPU, 2026-10-12

Resultado: **FAIL_DELIVERY_STAGE_LIMITS**. Procedimiento de instalación y relevo
real ejecutado; los umbrales de entrega no se cumplen en este VPS. Sin aceptación
global de capacidad, MOD-08 o N3. [Resumen saneado y hashes](mod08-vps-medicion-servidor-20261012.json).

## Fuentes y preparación

Fetch y pull --ff-only en worktree aislado `codex/mod08-vps-server-20261012` desde
origin/master. Incluye c46d0e101e8f260493a53bd4617b54dd4f0171f5; checkout original
preservado con sus cuatro untracked previos. SHA ejecutado en las cuatro etapas:
**2a6b81c27068af28f09a85f3522b1cd9e0ead552**. Sus dos cambios respecto de c46d0e1
son sólo documentación: referencias explícitas a artefactos ignorados del portátil
y registro del plan. Sin cambios en lógica de aplicación ni nuevas optimizaciones.

uv0.11.19 no ofrecía Python3.12.15; actualización gratuita a uv0.13.0 resuelve
instalación. Python3.12.15 y `uv sync --frozen --python 3.12.15` reales. Instrumentos
con lock/hashes en venv separado: py-spy0.4.2, Memray1.20.0, Scalene2.3.0,
pyperf2.10.0; intérprete de ese venv3.12.13, admitido por instalador3.12. Memray y
Scalene permanecieron inactivos. Ruff PASS,109 tests rápidos PASS/5.27s. check_docs
inicial falló por tres enlaces a artefactos locales ignorados ausentes; corregidos
como referencias locales en72e6468 y check_docs PASS/226Markdown/3057enlaces.
No locks cambiados ni versiones sustituidas para hacer pasar instalación.

Kernel reconstruido en venv aislado Python3.12.15/Cython3.0.12/GCC11.5.0/O3;
identidad **native-sealed**, binarioSHA256
`ca3c388585ed10a6f5ca3f5e82aeea385c5c496368e3800b45758df6fa2a0726`.
Builder/manifest/locks e IDs efectivos de cinco imágenes figuran en JSON. No
fallback ni igualdad binaria inventada con portátil. Imagen propia preparada antes
sin reiniciar servicios normales. Imagen probada retenida como
`web-modelos-mod08-vps:c46d0e1-20261012`; tag `web-modelos-app:latest` anterior
restaurado al cerrar todas las etapas. Para repetir con el runner actual, volver
a asociar explícitamente la imagen probada a su tag esperado antes del ensayo.

## Entorno y límites

OpenStack Nova, Linux5.14.0-570.58.1.el9_6.x86_64/glibc2.34, Docker29.8.1,
8vCPU visibles. Modelo anunciado por invitado: Intel Core Processor(Haswell,noTSX),
no identificación probada del procesador físico. CPU guest anuncia AES/AVX2,
no SHA-NI/AVX512. El usuario aporta para el portátil i5-1235U, máximo anunciado
4.4GHz/mínimo0.4GHz: no frecuencias medidas durante su prueba ni flags comprobados.
El portátil cambiaba perfiles al alternar cargador. No atribuir diferencias entre
máquinas al código ni demostrar causa única de hardware mediante esa comparación.

Cuotas verificadas: PostgreSQL1.5CPU/3072MiB, Redis0.1/384MiB, aplicación1.75/3968MiB,
objetos0.5/512MiB, proxy0.1/128MiB y controlador0.05/128MiB: **4CPU/8GiB totales**.
Swap propio0, storage propio kernel-capped5939134464bytes, inferior a20GiB.
Sin servicios existentes reiniciados, providers, despliegue o datos reales.

## Resultados terminales secuenciales

| Etapa | ID capacidad | Resultado | JUnit | Duración test (s) |
|---|---|---|---|---:|
| preflight | 20261012-004721-70fdb78c | READY_NOT_CAPACITY | 1PASS/0fallos/errores/skips | 77.460 |
| probe | 20261012-005205-34d7626e | NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY | 1PASS/0fallos/errores/skips | 42.375 |
| measure | 20261012-005632-9fb82130 | FAIL_DELIVERY_STAGE_LIMITS | 1fallo/0errores/skips | 2317.495 |
| diagnose | 20261012-013900-179969c8 | PROFILE_DIAGNOSTIC_NOT_CAPACITY | 1PASS/0fallos/errores/skips | 1658.382 |

Recibos VPS correlacionados en JSON. Cada etapa conserva report/launcher/XML,
1.411 huellas comparadas independientemente y retiro independiente de seis
contenedores/red/volumen propios. Fuentes iguales y sin cambios; sin problemas de
archivo. No procesos de prueba vivos al cerrar. Duraciones de test no son duración
completa de lanzamiento ni latencia HTTP. No repetición de measure: condición de
PASS incumplida; no corrección demostrada ni reensayos especulativos.

## p95 contractual de measure, por caso

Dos casos sintéticos concurrentes,1500revisiones,JSON16777236bytes y originales
67095050/67095042bytes, dentro de±1% de16MiB/64MiB.384lecturas de cobertura y20
 descargas por variante **por caso**. Cuerpos íntegros,ZIP/digests/datasets y EOF
verificados dentro de workers; cero errores de carga. Cada descarga tiene POST303
 y GET200 frescos. Sin perfiles, spans, cProfile o registros WSGI añadidos.

| Operación | Caso A (s) | Caso B (s) | Muestras/caso | Límite (s) |
|---|---:|---:|---:|---:|
| Guardar imágenes | 1.997628 | 1.945690 | 20 | 5 |
| Leer selección | 1.656140 | 1.653232 | 31 | 2 |
| Inspección binaria | 1.638473 | 1.644180 | 20 | 2 |
| Guardar cobertura | 3.010549 | 2.970579 | 20 | 5 |
| Leer cobertura, lote entero | 3.829796 | 3.835592 | 384 | 2 |
| Descarga JSON | 10.732150 | 10.565686 | 20 | 5 |
| Descarga binaria | 10.334944 | 10.442426 | 20 | 5 |

Percentiles recalculados nearest-rank. Intervalos pareados de las siete etapas se
solapan. Auditoría independiente necesaria: la aserción de success que registra el
FAIL precede a las aserciones exteriores de concurrencia/RSS. Las verificaciones
del cuerpo sí terminaron dentro de workers. RSS observado del proceso de prueba
926208000bytes<1GiB; cota conservadora global propia4137734144bytes=3.853565GiB,
incluye cache/tmpfs, no pico síncrono. Sin swap/OOM. Esto no convierte el fallo de
rendimiento en PASS ni acredita toda la aplicación/N3.

## Diagnóstico separado y sus límites

CPU steal medio entre snapshots de measure0.0338313%; no excluye picos breves.
PSI CPU/memoria no existe en este host: presión no medida, nunca asumir cero.
Loadavg inicial5.88/4.36/3.61 y final3.64/4.22/4.60. Contadores cgroup acumulados
registran throttling(app5006/23636períodos;PG3103/21884), no coste por request ni
causa cuantificada. Observador PG sólo en base desechable, rol de negocio intacto.

Diez capturas py-spy nativo/PG: siete completas y tres parciales(cobertura inicial,
final y save), nueve errores de muestreo en total; ningún error de instrumentación
invalidante ni ausencia de muestras. Sin cProfile/spans/perfiladores anteriores.
Las capturas incluyen idle y cierre del instrumento; muestras de pared inclusivas,
no porcentajes de CPU ni timings de aceptación. Thread observador excluido.

| Captura descarga | Hilo principal esperando futures (%) | Espera psycopg (%) |
|---|---:|---:|
| JSON autorización inicial | 49.6 | 19.2 |
| JSON autorización proxy | 57.3 | 25.8 |
| Binario autorización inicial | 52.4 | 30.4 |
| Binario autorización proxy | 61.2 | 26.2 |

Espera psycopg en cobertura inicial23.8% y final36.4%, con muestreo parcial. PG está
frecuentemente idle-in-transaction/ClientRead: espera al cliente, no atribuirlo a
trabajo de servidor. Deltas PG incluyen otros workers del rol durante la captura;
no sumar tiempos anidados ni interpretarlos como CPU o filas fuente reales.

Símbolos Python desconocidos resueltos offline mediante addr2line del ejecutable
3.12.15 instalado, SHA en JSON; sin otro ensayo ni nuevo profiler. SHA256_Update y
otras hojas SHA256 representan33.2–44.7% de muestras de cada worker físico en las
cuatro capturas de descarga. La ausencia de SHA-NI visible refuerza una hipótesis
sobre aceleración nativa, no demuestra causalidad o ahorro obtenible. Direcciones
libc/otras bibliotecas quedan sin resolver; no inventar equivalencia con símbolos
del host. No se identifica con precisión el cuello CPU completo del p95 sin
instrumentación bajo dos casos. No evidencia suficiente para ampliar mypyc/Cython,
cachear autoridad, omitir bytes frescos o volver a cuatro lectores(rechazados antes).

## Continuación autorizada posteriormente

Tras conocer este FAIL, el usuario autoriza pasar de4CPU al máximo8CPU del VPS.
Se conserva este ciclo íntegro como evidencia de4CPU. La siguiente comparación
mantendrá aplicación, dataset, workers, memoria8GiB, storage20GiB, garantías y
umbrales; perfil de cuotas8CPU explícito y verificable, no resultado todavía.
Una mejora grande indicaría efecto de la cuota de CPU asignada dentro de este VPS,
no causa única de todas las diferencias con portátil. Repetir una vez sólo si
la nueva medición cumple. Nunca trasladar un PASS de8CPU al contrato original4CPU
ni declarar aceptación global/N3. No nuevos modelos/cuentas; consumo previo intacto.

Artefactos completos permanecen locales en `artifacts/capacity-environment/ID/`
y `artifacts/vps-measurements/ID/environment.json`. No se versionan claves,
venvs, cuerpos, bases, binarios grandes o logs privados. Los hashes del resumen
permiten verificar recibos locales; un checkout remoto no contiene esos archivos.
