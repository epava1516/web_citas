# MOD08 — Consumidores y coste base de campos/punteros — 2026-10-11

Campaña autorizada por «Procede pues con lo que se propone», tras
[la sala de deliberación](mod08-salon-deliberacion-20261011.md).
Runner final `20261011-134116-08cc3941`: **10 PASS/0 fallos/errores/skips**, 112.021s JUnit.
1208 entradas del mapa de fuentes verificadas exactamente antes de documentar; PostgreSQL,
Redis, runner y Gunicorn propios ausentes comprobados independientemente. HEAD `7e04016d`.
Código productivo intacto. [Datos, muestras y negativa previa](mod08-scalar-consumers-20261011.json).

## Resultado y decisión

La pista del profiler queda acotada: hay **27163 hojas**, no 101755 diccionarios. El
recorrido que construye conjuntos de rutas cuesta unos **23.059ms** de mediana en el
corpus representativo, y resolver sus **4501 punteros seleccionados**, **6.305ms**.
Son costes del código original consumido de esas formas; **no son ahorros ni una
descomposición exacta del request**.

No se prepara ni aplica una candidata productiva en esta campaña. El coste base observado
es modesto para justificar una reescritura orientada a resolver el déficit de segundos del
escenario contractual. No se demuestra que toda optimización local sea inútil: podría
existir una mejora pequeña, pero no se ha comparado una variante. El acuerdo entre modelos
no sustituye esa evidencia. Se cierra este diagnóstico, conservando el instrumento y
dejando la API pública, autoridad, consultas frescas y auditoría intactas.

`compile_coverage` es el consumidor que enumera todas las hojas en este request, y sólo
usa sus rutas. Las cuatro páginas apenas añaden 108 hojas. La construcción de la fuente
es un perímetro mayor, pero incluye materialización, consultas y trabajo no separado;
no se atribuye su residual a ORM puro ni se reabre la precarga de relaciones ya descartada.

## Método y perímetros

Cuatro archivos nuevos sólo en tests: `capacity_scalar_diagnostic.py`,
`capacity_scalar_wsgi.py`, `test_capacity_scalar_diagnostic.py` y
`test_capacity_scalar_consumers_http.py`. Se reutilizan los helpers existentes de
servidor, roles y clones, sin modificarlos. No cProfile ni hooks SQL/fetch/pipeline/next.

Fixture sintético: 1500 revisiones, selección de 16777214 bytes, originales retenidos
de aproximadamente 64MiB no seleccionados y cobertura parcial escalar. Aprobación con
31 lecturas paginadas reales; historial mediante 64 POST reales: 548 eventos y 256
lecturas de cobertura. Rol LOGIN runtime separado, PostgreSQL17/Redis propios y dos
workers Gunicorn sync calientes mediante POST comprobados.

Cada petición medida usa un clon idéntico con nueva conexión y commit normal. Inspección
independiente después del commit comprueba cuatro lecturas y ocho eventos añadidos.
Preparación y warmups fuera de cifras. Sin Caddy/RustFS, cuotas contractuales ni carga
concurrente. Tres tiempos HTTP no forman un p95 ni aceptan 2s/5s o dos casos.

La cuarta petición usa otro clon y se dedica a contar, con sus tiempos descartados.
Se envuelven aliases de `scalar_fields` en consumidores; la definición recursiva original
no se parchea. El conteo estructural separado calcula filas, hojas, contenedores,
profundidad y rutas sin conservar valores. Censo y SHA de la fuente recibida en el
worker coinciden con el corpus materializado del padre.

## Tres peticiones control/spans/control

| Muestra | TCP completo | WSGI | CPU de hilo | PID | Colecciones GC 0/1/2 |
| --- | ---: | ---: | ---: | ---: | --- |
| Control anterior | 1645.055ms | 1643.470ms | 911.186ms | 200149 | 68/6/1 |
| Spans | 1664.316ms | 1672.298ms | 938.915ms | 200148 | 71/6/1 |
| Control posterior | 1620.490ms | 1619.004ms | 882.591ms | 200148 | 67/6/0 |

Dos workers calientes, pero distintos PIDs medidos. Las colecciones GC también difieren.
El scope y su restauración se incluyen en WSGI; preparar/escribir el reporte y capturar
estadísticas GC quedan fuera de ese reloj. El cuerpo TCP puede terminar antes del cierre
WSGI. No restar diferencias como overhead causal ni como ganancia ajustada.

La primera tanda fallida, con el mismo método HTTP, tuvo controles 801/769ms. La variación
entre tandas es grande y afecta también a CPU; no se ha identificado su causa. No atribuir
la diferencia al cambio de nombre del arnés ni a una optimización: no hubo variante.

## Consumidores completos, sólo petición instrumentada

| Función | Calls | Wall inclusivo | CPU inclusiva | Wall exclusivo | CPU exclusiva |
| --- | ---: | ---: | ---: | ---: | ---: |
| source_copy | 1 | 405.580ms | 251.397ms | 405.580ms | 251.397ms |
| compile_coverage | 1 | 42.851ms | 42.837ms | 31.289ms | 31.275ms |
| project_selected | 2 | 64.789ms | 64.789ms | 64.789ms | 64.789ms |
| coverage_page | 4 | 0.414ms | 0.407ms | 0.414ms | 0.407ms |

`required_pages`, `inspect_catalog`, `prepare_page` y `access_compile_coverage` no se
observaron. Eso no prueba coste cero de esas funciones en otros recorridos. Exclusivo
descuenta sólo hijos observados: una llamada a `project_selected` está dentro de
`compile_coverage`, la otra fuera. No sumar inclusivos ni interpretar los 31ms como
tiempo puro de `scalar_fields`; incluyen referencias, conjuntos, decisiones y otra lógica.

## Conteo independiente

| Sitio observado | Invocaciones externas | Hojas producidas |
| --- | ---: | ---: |
| compile_coverage, línea 66 | 1502 | 27163 |
| coverage_page, línea 43 | 4 | 108 |

Los 1502 objetos son 1500 revisiones, un perfil y una cuenta sujeto. Censo total de ese
corpus: 40682 nodos, 13519 contenedores, 10484 vacíos; profundidad máxima 3, suma de
profundidades de hojas 33458 y 336156 caracteres de rutas (máximo 27). No hay claves con
escapes en este fixture; se cubren en el corpus adicional. Las hojas son str/None/bool/int.
No equivale a un censo exhaustivo de los dominios permitidos por las API públicas.

## Baseline puro original A/A

Se ejecuta en el padre después de terminar Gunicorn, sin lecturas DB dentro del tiempo.
Preparación, validación de resultados y estadísticas GC fuera del cronometraje; estado GC
conservado. Dos warmups descartados por operación, luego `ABBA × 5`: 20 muestras,
10 por etiqueta. **A y B ejecutan exactamente el mismo código original.**

| Operación, corpus representativo | Resultados por muestra | Mediana wall | Mediana CPU | Rango wall | Desv. poblacional wall |
| --- | ---: | ---: | ---: | --- | ---: |
| Conjuntos de rutas por fila | 27163 | 23.059ms | 23.056ms | 21.599–27.745ms | 1.433ms |
| Conteo de hojas | 27163 | 21.001ms | 20.957ms | 20.289–31.571ms | 2.647ms |
| Punteros seleccionados | 4501 | 6.305ms | 6.280ms | 5.610–7.948ms | 0.558ms |

Medianas wall A/B: rutas 23.013/23.059ms, conteo 20.829/21.246ms y punteros
6.343/6.237ms. Cero colecciones GC durante estos intervalos. Ese A/A caracteriza esta
medición pura, no el ruido TCP ni un supuesto ahorro. Rutas incluye formar conjuntos;
conteo incluye consumir el generador; punteros incluye descartar el valor devuelto. No
se atribuye toda la proyección a `pointer_value` ni se elimina su `deepcopy`.

Corpus adicional de cuatro filas: objeto ancho de 256 hojas, rama de profundidad 64,
escapes RFC6901 y un contenedor vacío. 259 hojas, profundidad máxima 65, ruta máxima
389 caracteres. Conjuntos 0.184ms, conteo 0.167ms y tres punteros 0.023ms de mediana;
no son cifras del request. Resultados y censo idénticos antes/después, sin normalizar
mediante JSON. Tests separados cubren subclases/tuplas/bool/float no finito, raíz escalar,
clave inválida, escapes y límites de rutas, mutación entre yields, close/throw y RecursionError.

## Incidente y verificación

Primera tanda `20261011-133814-09f90cce`: 8 PASS/1 FAIL/0 errores/skips, 94.805s JUnit,
fuentes congeladas y retirada propia comprobada. Falló después de HTTP/conteo, al
preparar el corpus de punteros: el dict `body` quedó oculto por la función `body()` que
creaba el POST. Se renombró `request_body` después del terminal y se completó el corpus
ancho/profundo/escapes. No se declara aquella tanda PASS ni se suman sus tests a la final.

La tanda corregida tiene nueve casos unitarios y una integración PG/TCP real, todos PASS.
Checks de Ruff, Django, migraciones y documentación incluidos en el runner; la documentación
final se verifica aparte. El mapa completo de fuentes coincide exactamente y la ausencia
de contenedores de ambas tandas y procesos propios se comprobó por inventario independiente.
No queda un benchmark de esta campaña ejecutándose. MOD08 general sigue pausado y sus
objetivos contractuales permanecen pendientes.
