# N10F — retorno de procesos actuales verificado

El caso de [489](489-n10-f-prerregistro-retorno-procesos-actuales-20261026.md) terminó con **1 PASS, 0 FAIL, 0 ERROR y 0 SKIP**. Run `20261026-232308-61cca37e`, runner oficial focused/serial, PostgreSQL17 y Redis7.4 propios, parser nativo. JUnit: **57,716 s de QA**, 1797 fuentes estables. No es una medida de latencia de aplicación.

## Resultado y tiempos observados

Se ejecutó producto `0dcf89f` → anterior `8589acd` → producto `0dcf89f`. Cada fase cargó realmente cuatro workers Gunicorn sync, validando ruta, hash de admin y presencia/ausencia del receptor de login. Doce instancias verificadas, seis HTTP200; master exit0 e hijos ausentes antes de la siguiente fase. La sesión sintética previamente admitida obtuvo Groupchange200 privado/no-store, URL y contenido esperados; health200 verificó PostgreSQL.

| Fase | Arranque hasta cuatro workers listos | Health HTTP | Lectura Group autorizada | Workers verificados |
|---|---:|---:|---:|---:|
| 1: current | 1.868 s | 38.073 ms | 230.990 ms | 4 |
| 2: previous | 1.861 s | 23.273 ms | 255.554 ms | 4 |
| 3: current | 1.662 s | 31.986 ms | 247.545 ms | 4 |

Una observación por etapa, sondeo de readiness50ms y TCP local. Sin referencia anterior equivalente de este retorno: no se calcula mejora, capacidad, percentiles ni SLA. El ensayo histórico de tres imágenes se conserva como evidencia histórica separada; no se presenta como ejecución de esta candidata.

Los 173 modelos/through, ocho archivos con hash/metadata y registros django_migrations permanecieron iguales después de cada fase. Sólo apps/core/admin.py difiere entre los 753 archivos runtime exportados: 4.065.493 bytes actuales y 4.064.970 anteriores. Cada archivo se comprobó con su blob Git; no copias de docs/evidencias, venv o artefactos ni construcción de imágenes.

## Alcance y aceptación

La fuente anterior carece del arreglo de login Admin con epoch1. Se acepta continuidad de lecturas y sesión ya admitida durante mantenimiento controlado, con vuelta final al código actual; no nueva admisión sobre la fuente anterior ni autorización productiva. Sin escrituras durante el retorno, cambio de imagen, despliegue, workers Celery mixtos, tráfico concurrente o cero interrupciones.

Se verificaron fuentes, identidades reales de las imágenes PostgreSQL/Redis contra la congelación previa, limpieza propia y Telegram terminal `sent`. No se preservan cookies, ajustes privados del hijo o logs. JUnit SHA256: `87c9d6aefce235f89baf079fdd2ef3b06fd8858a2f0a8828a57d2c1993c1a679`.

El gate posterior de requisitos resolvió únicamente la disposición pendiente O_RUNTIME_RETURN; otras76 filas permanecen iguales. La aceptación de N10 se documenta en [491](491-n10-aceptacion-local-operacion-20261026.md).

Evidencia compacta: [archivo F](evidencias/n10-f-retorno-actual-y-aceptacion-20261026.tar.gz), 16 miembros con manifiesto SHA256, SHA del archivo `361875007c999008b4f2c7805a6f7f5234ce9c0c00ea3d1b21b8a29385d820c1`. Incluye instrumentos, congelación, auditorías de ejecución y aceptación, matriz aceptada y recibos; excluye secretos y logs brutos.
