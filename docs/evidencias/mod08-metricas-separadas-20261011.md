# MOD-08 — Instrumentos separados y medición contractual sin perfiladores

## Dictamen

No se acepta el requisito de latencia. El escenario normal de dos casos
concurrentes terminó como `FAIL_DELIVERY_STAGE_LIMITS`, con todos los tipos
de operación medidos. No hubo errores de operación reportados; el test falla
por sus seis incumplimientos de p95, no por el instrumento. Producto preservado.

| p95 | Caso A | Caso B | Límite |
| --- | ---: | ---: | ---: |
| Navegación, 384 muestras por caso | 3,384803 s | 3,389665 s | 2 s |
| JSON, 20 muestras por caso | 8,747557 s | 8,961067 s | 5 s |
| Binario, 20 muestras por caso | 9,033017 s | 8,966103 s | 5 s |

La peor navegación necesita reducir 1,389665 s (aproximadamente 41,0% del
tiempo actual); JSON 3,961067 s (44,2%); binario 4,033017 s (44,6%).
Las descargas son partes de unos 8 MiB con dos autorizaciones frescas, no
una transferencia única de 64 MiB. Cada fixture contiene 1500 revisiones,
16777236 bytes de candidato y 16 originales, próximos a 64 MiB.

## Recorridos y comprobación independiente

1. Diagnóstico nativo separado `20261011-205904-6d77445d`: 1 PASS en
   1111,860 s. Diez capturas completas sin errores; cero registros del
   observador antiguo y sin cProfile del controlador ni posvalidación.
   Navegación p95 2,483100 s (382 muestras), JSON máximo 4,649687 s
   (3 muestras), binario máximo 5,422434 s (8 muestras). No aceptación.
2. Escenario normal `20261011-212056-311e7b34`: 1 FAIL, cero errores
   y skips, 1943,124 s. Se ejecutó `config.wsgi`, con todos los flags de
   perfilado falsos y `shared_preload_libraries` vacío. Cero capturas nativas,
   cero registros de tiempos WSGI, posvalidación cProfile desactivada.

Se descubrió y retiró el cProfile de posvalidación también del modo normal:
podía consumir CPU mientras el otro caso aún estaba activo. Sólo el modo
legado explícitamente diagnóstico lo conserva. Las cuatro combinaciones de
modo se comprueban con tests de exclusión. El primer lint detectó una variable
fuera de alcance en ese cambio; se corrigió antes de lanzar el escenario normal.

El test normal detiene sus asserts finales cuando detecta los límites fallidos.
Por eso se verificaron independientemente después los intervalos: todas las
parejas se solapan en los siete tipos requeridos (20/31/20/20/384/20/20).
El pico RSS del proceso pytest fue 946114560 bytes, menor que 1 GiB.
Auditoría independiente de las 1389 huellas: todas coincidían antes de escribir
esta documentación. Fuentes sin cambios durante ambos recorridos según runner.
Tras el primer recorrido sólo cambiaron dos archivos de harness/tests para
excluir posvalidación del modo normal; las huellas históricas se conservan.
Contenedores, red y volumen propios retirados y ausencia comprobada por label.
No se modificaron servicios preexistentes, presupuesto ni garantías de negocio.

## Lectura del diagnóstico

La cadena sigue acumulando trabajo: cuatro llamadas de enlaces procesaron
340 filas en 7,529706 ms al principio y 9844 filas en 203,603675 ms en el
lote tardío. Ninguno de esos dos sondeos vio `Lock`, lo que no excluye
esperas breves. Los tiempos SQL anidados se solapan y pueden incluir otros
workers; no se suman como ahorro ni se interpreta ClientRead como espera
del cliente por la base de datos.

La variación de navegación respecto al diagnóstico anterior es unos 83 ms
menos, pero el binario empeoró unos 298 ms. No hay comparación paired que
atribuya esas diferencias únicamente a las métricas. El diagnóstico de un caso
y el escenario concurrente de dos casos tampoco son comparables como antes/después.
La instrumentación antigua añadía coste, pero no explicaba el incumplimiento.

No se añade una optimización productiva sin evidencia suficiente. Siguiente
puerta: candidata que reduzca trabajo bajo concurrencia, mantenga frescura y
autoridad, supere equivalencia/PG real y sólo entonces vuelva a medirse.
No repetir esta carga sin un cambio o una pregunta nueva.

## Artefactos

- [Resumen estructurado y huellas](mod08-metricas-separadas-20261011.json).
- Reporte diagnóstico local: `artifacts/capacity-environment/20261011-205904-6d77445d/report.json`.
- Reporte normal fallido por límites local: `artifacts/capacity-environment/20261011-212056-311e7b34/report.json`.
- JUnit normal e intervalos locales: `artifacts/capacity-environment/20261011-212056-311e7b34/pytest.xml`.

Estos artefactos ignorados se conservaron en el equipo de origen; no forman
parte del checkout remoto. El resumen enlazado contiene la evidencia saneada.

El fixture de identidad es simulado; PostgreSQL, HTTP, Celery, RustFS y
Caddy son reales. No se acredita proveedor externo, producción ni N3.

Verificación posterior del harness: 102 PASS en 2,12 s; Ruff sin errores;
check_docs PASS (221 Markdown, 3049 enlaces); git diff --check sin incidencias.
Estas comprobaciones no sustituyen ni convierten en PASS el escenario de latencia.
