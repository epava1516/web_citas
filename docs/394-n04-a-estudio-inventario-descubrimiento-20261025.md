# N04A — inventario y estudio de descubrimiento

Alfa, 25 de octubre de2026. N00/N01/N03/N06 aceptados:4/13. N04 empieza después del acta393. No hay cambio de aplicación, candidato de optimización ni prueba nueva en este paso.

Antes del estudio se revalidaron las2001 fuentes del corte de grafo N03 final, SHA482b51b745e7a88050dd418ec1766a4aa68c8969366eb1ea6020bce7459eeb50; consulta graphify seguida de fuentes primarias. Es un corte focal AST/semántico, no reconstrucción global ni prueba de comportamiento.

## Acciones y evidencia disponible

El censo338 y la matriz N00 asignan dos acciones a N04, no cinco endpoints:

| Acción | Familias | Fuente y autoridad | Estado de evidencia |
| --- | --- | --- | --- |
| route:R_home | I01 listado orgánico, I02 promocionado, I03 filtros, I04 paginación | core.views.home→listings.discovery.results, validación de formulario y autoridad de publicación, estados/fallback, orden y presentación | N01A/B/C mide segmentos orgánicos ES/EN; B16 y pruebas de promociones conservan oráculos finitos de IDs/orden/conteos/cupos/rotación/exclusiones |
| route:R_listing_detail | I05 ficha pública | moderation_views.public_detail, snapshot read-only fuera de transacción heredada y guard nativo en ésta, descripción/fotos aprobadas | N01B/C mide ficha ES/EN; testigos funcionales de idioma, contactos elegidos, privacidad y retirada |

Codex comparó las12 fuentes directas y dependencias estáticas declaradas: idénticas a N00/B16 y a la congelación N01C. Esto permite estudiar la reutilización; no certifica un cierre transitivo exhaustivo ni adjudica rendimiento a todo el bloque. N03 cambió procesamiento/similitud y N06 el panel: no trasladar sus tiempos a estos GET.

## Qué se conserva y qué falta medir

N01A345: dos peticiones ES orgánicas, poblaciones10/100; no comparar sus tamaños como antes/después. N01B347:100perfiles, dos idiomas y cinco segmentos por idioma, primera más cinco posteriores; listado/página2/perfil usaron fallback por estados desconocidos. N01C349: mismo corpus antes y después de mantenimiento nativo refresh_publication_state --all;120peticiones con paridad de IDs/orden/conteos. El mantenimiento incluye VACUUM/ANALYZE y calentamiento; no es candidato de código.

El testigo B16/334 conserva su carga contractual original, promociones sintéticas, filtros y verificaciones finitas de páginas/exclusiones. Sus18 000respuestas no son18 000oráculos completos de contenido ni percentiles individuales por variante. No se repite esa carga por documentación. Las promociones no implican compra, proveedor o cobro real.

La brecha de N04 es atribuir el coste de segmentos seleccionados que N01 no midió: promoción, mayor profundidad y selectividad combinada, con estados mantenidos; separar consulta, hidratación y render mediante observadores que deleguen ejecución real. Los perfiles históricos de materialización y checkpoints fuerzan state_page→None: sirven para su rama fallback, no sustituyen una medida actual del camino mantenido.

El siguiente lote debe prerregistrar cohortes, primera y posteriores, idiomas, orden, páginas y filtros, versión/dataset/recursos, marcadores state/fallback, oráculos exactos y muestras antes de ejecutar. Mantener ranking/cupos/rotación y negativos; comparar con autoridad nativa y no con la salida que se pretende validar. Medir SQL numérico, materialización, validación/presentación/render, pared/CPU y recursos pertinentes sin sumar tiempos anidados ni inventar CPU de PostgreSQL a partir de execute.

No se selecciona todavía un índice, caché o refactor. Si la referencia no justifica cambio, disponer «sin cambio necesario» con evidencia suficiente; si un candidato no aporta mejora clara, conservar el resultado, diferir esa optimización al final y avanzar. No se rebajan guards ni se aceptan huecos obligatorios por tiempos aceptables.

## Tabla de situación antes y después de N04A

| Medida o decisión | Antes | Después del estudio | Diferencia / límite |
| --- | --- | --- | --- |
| Disposición de superficie N04 | Cinco familias del roadmap | Dos acciones HTTP y12 fuentes declaradas comparadas | Mayor trazabilidad, no dos PASS nuevos |
| Listado ES preparado, mediana5 N01C |147,753ms ya medidos |Mismo testigo histórico, no nueva medida |Sin candidato; mejora atribuible no evaluable |
| Ficha ES preparada, mediana5 N01C |41,660ms ya medidos |Mismo testigo histórico, no nueva medida |Sin candidato; no inferir SLA por endpoint |
| Promoción/profundidad/filtros y etapas |Testigos funcionales y carga agregada con límites |Brecha de atribución delimitada para próximo prerregistro |No hay un después temporal inventado |

N04 permanece abierto. La aceptación posterior requiere disposición por ambas acciones, mediciones suficientes para los escenarios escogidos y tabla de tiempos comparable o ausencia de base declarada. N05 conserva navegador/entrega; N07 publicación/lifecycle; N11 candidata integrada. Proyecto en alfa, sin proveedores ni apertura.
