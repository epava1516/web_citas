# N01C — Contraste auditado de preparación operativa de estados

25deoctubrede2026. [Prerregistro348](348-n01-c-prerregistro-estados-20261025.md), corte0d2ade5, run20261025-090357-d51eb3f9:1PASS,0FAIL/ERROR/SKIP y120peticiones verificadas. [Auditoría independiente](evidencias/n01-c-diagnostico-auditoria-20261025.json) y [archivo original](evidencias/n01-c-diagnostico-evidencia-20261025.json). N00aceptado1/13;N01/N04siguen abiertos,alfa.

## Antes y después de preparación, no de un cambio de código

La misma cohorte100publicados y el mismo helper B se midieron en dos fases. Entre ellas se ejecutó el comando nativo refresh_publication_state --all, que también realiza VACUUM/ANALYZE. Orden y calentamiento no están aleatorizados. La comparación representa condiciones operativas distintas; no efecto puro del estado ni mejora causal de código. No se calcula porcentaje de optimización.

| Idioma | Escenario | Mediana5antes(ms) | Mediana5tras preparar(ms) | SQLantes→tras preparar | Ruta antes→después |
| --- | --- | ---: | ---: | --- | --- |
| es | listing | 254.833 | 147.753 | 29→32 | fallback→state |
| es | page2 | 217.162 | 148.407 | 29→32 | fallback→state |
| es | profile | 252.834 | 146.273 | 29→32 | fallback→state |
| es | empty | 77.249 | 63.649 | 17→16 | state→state |
| es | detail | 49.367 | 41.660 | 22→22 | None→None |
| en | listing | 271.240 | 147.674 | 29→32 | fallback→state |
| en | page2 | 237.750 | 163.922 | 29→32 | fallback→state |
| en | profile | 274.776 | 164.618 | 29→32 | fallback→state |
| en | empty | 76.984 | 73.552 | 17→16 | state→state |
| en | detail | 53.497 | 51.813 | 22→22 | None→None |

Mantenimiento nativo:0.271738s,fuera de las peticiones medidas. Pendientes PublicationDirty:98→0;estados actuales para102Listings totales, incluidos100publicados y2no publicados de la fixture. Población,IDs,orden y campos de negocio se conservaron. El total102no significa que se crearan dos perfiles durante el mantenimiento.

Los listados/página2/perfil pasaron de fallback/state_unknown_over_limit a state. Los48requests de búsqueda/listado posteriores usaron estado; las12fichas de cada fase conservaron su guard propio sin marcador. La preparación evita atribuir al camino mantenido los costes que N01B observó con98marcas pendientes. No demuestra un defecto de aplicación ni operación real de worker/Beat.

En los listados el número deSQL subió29→32 mientras la mediana observada bajó. SQLcount por sí solo no explica el coste; no se acepta una corrección que quite consultas necesarias de autoridad. El resultado orienta próximas fichas y atribución por etapa, sin forzar un índice, caché o refactor.

## Verificación y pendientes

Paso pytest:68.937s,con fixture y120peticiones, no latencia de una solicitud. JUnit1caso/journal3fases, dos fases de10segmentos×6muestras, rutas,hashes/orden/conteos y oráculos originales B aprobados. Los1507SHAprevios, helper B,instrumento C,documentos y grafo congelados permanecieron intactos hasta auditoría. Estados actuales y cero pendientes tras la preparación y fase final; campos de negocio iguales. Contenedores y temporal ausentes,Telegramterminalsent.

No se modificó producto. No p95/TCP/capacidad, grandescohortes,filtros exhaustivos,promociones,trabajo asíncrono real o comparación entre versiones candidatas. La tabla anterior es un contraste de preparación operativa; no cierra N01/N04 ni reemplaza las tablas/evidencias del cierre de cada bloque.

## Investigación paralela de los otros ocho grupos

Se recibieron19representantes propuestos S02–S09:10del frenteA y9delB. [Propuestas y procedencia](evidencias/n01-propuestas-restantes-20261025.json), [verificación literal y selectores](evidencias/n01-propuestas-restantes-verificacion-20261025.json). Los93registros de cita y29selectores se contrastaron con SHA, rangos/literales y AST. Cuatro rangos del frenteA excedían EOF:gate originalERRORconservado,autora corrigió sólo esas cuatro entradas y el gate correctivo pasó. No fueron fallos de producto ni se ejecutaron esas pruebas por la investigación.

Estas propuestas no están aceptadas como fichas finales ni acreditan tiempos, presupuestos o cobertura de todas las acciones. Próxima acción: incorporar el resultado al grafo y revisarlas por escenario, roles, dato/recursos, puntos de medida, oráculos y presupuestos antes de ejecutar o comparar candidatos. Mantener los restantes segmentos de S01 pendientes explícitos y el alcance completo I01–I28.
