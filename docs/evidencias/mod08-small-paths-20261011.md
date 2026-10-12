# MOD08 — Mejora parcial del recorrido de rutas — 2026-10-11

**Se conserva una mejora local de unos 3ms en el recorrido de rutas. No se demuestra
una mejora del request HTTP completo ni cumplimiento de los objetivos 2s/5s.**

El usuario autorizó aceptar beneficios más pequeños para continuar la investigación.
Esta instrucción reduce el impacto mínimo buscado, conservando seguridad, frescura,
completitud, privacidad, auditoría y los objetivos contractuales.
[Registro](../17-seguimiento-desarrollo.md#reapertura-por-beneficio-parcial--instrucción-posterior-2026-10-11),
[muestras completas](mod08-small-paths-20261011.json) y
[deliberación íntegra](../../.ai/rooms/mod08-small-paths-20261011/transcript.md).

## Cambio y equivalencia

`compile_coverage` sólo usa la ruta de cada hoja del catálogo escalar. Ahora consume
`_scalar_paths`, un recorrido privado recursivo que devuelve directamente esas rutas,
en lugar de construir diccionarios con valores que después descarta. La comprensión
mantiene su frame y el orden de recorrido. `scalar_fields`, `pointer_value`, sus valores
copiados, consultas, bloqueos, firmas y validaciones de autoridad permanecen intactos.
No se introduce una caché ni un modo de rendimiento productivo.

El algoritmo privado duplica deliberadamente el recorrido público, manteniendo
recursión, iteradores, subclasses, errores y escapes RFC6901. El riesgo de deriva se
controla mediante un oráculo diferencial permanente, descubierto por pytest: 12 casos,
250 árboles generados con semilla fija, rutas vacías, escapes, custom items/replace,
errores parciales, mutaciones durante consumo, send/close/throw, ciclos y barrido de
90 niveles alrededor del borde de recursión. La prueba usa las comprensiones reales.
Esto está verificado en CPython3.12.15; no heredar el resultado de frontera a otro runtime.

El alias previo scalar_fields se conserva para diagnóstico. El contador test-only se
adapta para observar también el nuevo consumidor y evitar un conteo falsamente cero.

## Verificación

Runner `20261011-145141-3ea7872c`: **126 PASS, 0 fallos/errores/skips**, 885.979s JUnit,
dentro del timeout de 900s. No se amplió el presupuesto ni se repitió el benchmark.
1275 entradas del mapa completo de fuentes coincidieron exactamente antes de documentar.
Los 24 controles locales previos no se suman a esa cifra.

N2 afectado: cobertura coherente, persistencia/cifrado/purga, páginas, inspección,
lotes e idempotencia/rollback, carreras con esperas PostgreSQL observadas y revocación,
uso de aprobación, HTTP de edición/revisión y Chromium móvil. Checks Ruff, Django,
migraciones y documentación también correctos. No es N3 conjunto ni aceptación MOD08.

PostgreSQL17 y Redis propios; login runtime restringido separado del owner. El backend
de verificación de identidad del fixture es un simulador, sin afirmar verificación real
de proveedor. PostgreSQL, el servidor HTTP y los commits sí son reales. Un solo worker
Gunicorn sync, kernel canónico native-sealed con identidad comprobada, datos sintéticos,
1500 revisiones y selección de 16777407 bytes. El historial inicial se sembró con 64
POST reales: 548 eventos y 256 lecturas. Cada muestra empieza en un clon equivalente;
la comprobación owner independiente confirma 556 eventos y 260 lecturas tras el commit.

## Comparación de etapa pura

Después de detener Gunicorn, con el corpus materializado de 1502 filas y 27163 hojas:
20 muestras por variante, ABBA×10, dos warmups por variante y validaciones fuera del reloj.
No DB, profiler ni manipulación de GC dentro del cronometraje. Se consumen conjuntos de
rutas; no se mide sólo crear el generador. Orden y conjuntos de salida coinciden.

| Etapa pura | Original | Rutas privadas |
| --- | ---: | ---: |
| Mediana wall | 20.391ms | 17.589ms |
| Mediana CPU | 20.387ms | 17.572ms |
| Pico mediano tracemalloc, medición separada | 5706B | 5698B |

Mediana de diferencias pareadas: **2.943ms wall / 2.938ms CPU**. Las 20 parejas favorecen
a la candidata en ambos relojes, al igual que los cuatro bloques cronológicos. Se cumple
la regla predeclarada de al menos 15/20 parejas favorables y cuatro bloques positivos.
La diferencia de medianas wall es aproximadamente 13.74%; no extrapolar ese porcentaje
al request. No existe un mínimo absoluto de ahorro bajo la nueva instrucción.

Corpus adicional de 259 hojas ancho/profundo64/escapes/vacíos: medianas wall
0.173→0.145ms, también 20/20 parejas y cuatro bloques positivos. No representa el request.

Tracemalloc se ejecuta por separado, cinco veces por variante. Sus picos vivos no cuentan
asignaciones acumuladas de diccionarios temporales. Los 8B de diferencia no acreditan un
beneficio de memoria significativo. Evitar un diccionario por hoja se observa en el código,
no es una medición de bytes o bloques acumulados ahorrados. El pico cumple el límite de
triage predeclarado: candidato ≤ original×1.05+1024B.

## Comparación HTTP: inconcluyente

40 peticiones medidas, veinte por variante ABBA×10, y **un warmup por variante**.
Ese protocolo es distinto de los dos warmups por variante del experimento puro y estaba
fijado antes. Clones, historial, commits y comprobaciones son equivalentes. El baseline
reconstruye exclusivamente el statement original; un control AST compara la función
entera con HEAD. Se prepara y cachea sólo código test-only antes de los relojes; no hay
caché de autoridad. Instalación/retirada de aliases es simétrica, incluidos imports tardíos.

| HTTP | Original | Rutas privadas |
| --- | ---: | ---: |
| Mediana TCP | 1626.673ms | 1621.596ms |
| p95 muestral TCP | 1693.458ms | 1687.279ms |
| Mediana CPU WSGI | 898.419ms | 889.801ms |

Sólo 12/20 parejas TCP y 11/20 CPU favorecen a la candidata. Los bloques TCP de diferencias
pareadas son +50.013, +2.258, +11.103 y −48.554ms. La variación impide atribuir causalmente
los aproximadamente 5ms de diferencia de medianas a la mejora. No prueba de no inferioridad
formal ni de p95 contractual. No se cumple ninguna señal de regresión de triage fijada
antes: 15/20 parejas TCP desfavorables con cuatro bloques negativos, o mediana y p95
ambos más de 5% peores. La ausencia de esa señal no acredita equivalencia universal.

La compuerta histórica CPU11.824%>10% sigue FAIL y no se reinterpreta. No se retiran
muestras ni se resta GC. Las colecciones gen2 suman once en cada variante, sin probar
causalidad. No Caddy/RustFS, cuotas contractuales ni carga concurrente. Un worker no
sustituye la topología contractual. Estadísticas owner previas pueden calentar páginas;
los clones no garantizan identidad de buffers. TCP incluye preparación del scope;
WSGI incluye cierre de respuesta/conexión. La captura GC posterior al scope puede incluir
su limpieza: no atribuir el conteo entero sólo a la fase cronometrada.

## Deliberación y cierre

Dos opiniones Claude y dos NotebookLM, todas recibidas, antes y después del experimento.
Claude actúa sin herramientas/edición bajo la excepción expresa. Consumo declarado
registrado, sin convertir coste de lista en factura. NotebookLM sólo consulta sus fuentes;
no se añade ninguna, y el CLI no identifica el modelo. Ningún consenso constituye PASS.

Codex corrige dos detalles de las opiniones: 126 es la batería completa, no 126 pruebas
diferenciales; los protocolos de warmup distintos no son una incoherencia. No dividir
costes de experimentos independientes para inferir el presupuesto exacto del request ni
atribuir el ruido a red o GC sin medirlo. No repetir ensayos para perseguir un resultado.

Se adopta esta mejora **como parcial de etapa**, sustentada por equivalencia y N2 afectado.
El goal de continuación con beneficios pequeños entrega una candidata aplicada y verificada;
no necesita consumir tres ciclos por obligación ni supone que el problema integral esté
resuelto. Recursos propios retirados y cambios previos del usuario conservados. Sin commits,
push, publicación, proveedores contratados ni datos reales. Objetivos2s/5s, capacidad y N3
siguen pendientes en su alcance correspondiente.

[Auditoría de cierre](../../.ai/rooms/mod08-small-paths-20261011/completion-audit.json):
requisitos, fuentes probadas actuales, oráculos públicos intactos, muestras, revisores y
retirada de procesos/recursos comprobados antes de cerrar el goal.
