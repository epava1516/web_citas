# Diagnóstico finito de crecimiento de la cadena de evidencia

2026-10-11. Autorización del usuario: «Hazlo pues», tras recomendar diagnóstico acotado del coste de `validate_chain`. No reanudación de capacidad completa ni cambio productivo. [Datos completos y verificación](mod08-chain-growth-20261011.json).

## Resultado

El coste observado de las cuatro validaciones de cadena aumenta al crecer el historial: aproximadamente 39 → 70 → 179ms de pared. El aumento se concentra en la consulta de eventos, su recuperación y la barrera del pipeline de filas fuente. La lectura de la cabeza y la atestación del entorno permanecen aproximadamente estables. Esto respalda la hipótesis de crecimiento con historial en este recorrido; no demuestra superlinealidad ni explica toda la diferencia con el p95 histórico.

| Lotes sembrados por HTTP | Eventos encontrados por las validaciones instrumentadas | TCP control, mediana de 2 muestras | Cadena, total de 4 llamadas | Consulta de eventos | Fetch de eventos | Pipeline sync | Lectura SQL de cabeza |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 44–58 | 1,337s | 38,640ms | 6,671ms | 1,901ms | 17,021ms | 2,393ms |
| 16 | 204–218 | 1,490s | 69,692ms | 16,812ms | 5,643ms | 34,623ms | 1,778ms |
| 64 | 620–634 | 1,809s | 178,845ms | 48,309ms | 19,212ms | 91,105ms | 2,167ms |

Los tiempos de desglose son medianas de dos peticiones instrumentadas por nivel. Cada petición contiene cuatro páginas secuenciales, no cuatro requests. La atestación fresca `_runtime_is_trusted` suma aproximadamente 30,388 / 29,105 / 31,822ms por petición. `_source_rows` completo suma 22,801 / 40,094 / 99,820ms e incluye `pipeline.sync`: no sumar padre e hijo. Cada petición instrumentada ejecuta 28 consultas de fuentes físicas (7 tablas × 4 validaciones) y cuatro lecturas completas de eventos. La recuperación de filas fuente observada aumenta de 188/220 a 2492/2524 filas sumadas por petición, con conteos completos en JSON.

## Recorrido, controles y población

Solo instrumentación en tests: `capacity_chain_diagnostic.py`, `capacity_chain_wsgi.py`, `test_capacity_chain_diagnostic.py`, `test_capacity_chain_wsgi.py` y `test_capacity_chain_growth.py`. Recorrido real `inspect_batch → inspect_page → record → validate_approved_assessment → require_runtime_chain → validate_chain`. Se mantienen SQL, argumentos, bloqueos, orden, descifrado, autoridad, comprobaciones y auditorías. No se instrumenta `validate_coverage_pages` como supuesto alias de `validate_assessment`.

Fixture nuevo sintético: 1500 revisiones, proyección seleccionada de aproximadamente 16MiB calibrada dentro de ±1%, originales WebP reales calibrados a 64MiB ±1% por el constructor. Evaluación y selección aprobadas por servicios, 31 lecturas paginadas reales, cobertura parcial de escalares. El campo `original_bytes` del reporte queda null por una diferencia de nombre con `originals_bytes` del manifest: no representa cero bytes. La calibración y lectura física de originales son verificadas por el constructor; no se publica un tamaño exacto adicional no recogido.

Se ejecutan 64 lotes de siembra y 12 lotes medidos por TCP local Gunicorn2 sync, PostgreSQL17 y Redis7.4 propios, LOGIN runtime no propietario y enforcement real. En cada nivel se alterna control/instrumentado/instrumentado/control. Sesión, MFA y CSRF reales del flujo de pruebas; verificador de identidad simulado explícitamente. Cada POST usa un UUID nuevo, EOF completo, HTTP200/no-store y cuatro nuevas `RightsPortabilityCoverageRead` comprobadas. No se fabrican filas ni IDs de auditoría. Todos los lotes repiten las mismas cuatro páginas escalares; no reproducen la distribución completa de navegación histórica.

Historial inicial 36 eventos y final 644: los 76 lotes añaden 608 eventos reales (304 lecturas de cobertura y sus 304 lecturas de selección). Los controles también escriben, por lo que las muestras adyacentes no tienen idéntico historial mutable: se registra el conteo exacto antes/después y la cabeza de cada llamada. El número de consultas permanece constante mientras crece el trabajo sobre filas. Presupuesto finito 420s desde fixture preparado; ejecución y retirada del servidor 127,637s aproximadamente, dentro del presupuesto.

## Interpretación y límites

Los controles sin los spans de cadena también aumentan en este escenario, pero dos muestras por nivel no acreditan p95, intervalo de confianza ni causalidad exclusiva. La captura es secuencial sobre un solo expediente; no hay prueba concurrente ni carga de fondo controlada por cuotas contractuales. No restar overhead de la captura instrumentada para inventar un control limpio. Los controles ya proporcionan tiempos HTTP propios.

`execute`, `fetch` y `pipeline.sync` son tiempos de aplicación/driver: no separan transporte, esperas y ejecución del servidor. CPU de hilo no es CPU de PostgreSQL. El residual exclusivo de cadena incluye verificación Python, transacción y overhead del observador; no es una medición pura de hashing. Los spans del pipeline incluyen trabajo del servidor y espera de su barrera, no Redis. No hay sonda de locks ni planes EXPLAIN en esta ejecución.

No comparar este total inclusivo de `chain` con la fase exclusiva histórica `validate_assessment` como si fueran idénticos. El diagnóstico anterior de 2,24s incluía sondas de copia/parseo; esta ejecución las omite y no representa una optimización productiva. Tampoco es equivalente al histórico de 383 lotes, proxy/RustFS, binarios seleccionados y cuotas originales. No extrapolar a miles de eventos ni declarar cumplido el objetivo 2s.

La siguiente investigación útil sería revisar los planes y el trabajo repetido real de las consultas de eventos y fuentes físicas sobre historial acumulado. Esta ejecución no demuestra todavía una transformación productiva segura. No justifica cachear cabeza/autoridad, omitir controles frescos ni reutilizar una validación después de escrituras propias que avanzan la cadena.

## Verificación y cierre

Runner `20261011-114954-9aaaaa72`, fuente base `7e04016d8ece6cf52388e283eb06cf0a6040fd2b` con cambios locales preservados y congelados. **8PASS/0FAIL/0ERROR/0skips, 207,724s JUnit**: una integración TCP real y siete pruebas de forwarding, restauración y cierre/error del instrumento (estas últimas no acreditan integración de base de datos). Gates Ruff, documentos, Django, migraciones y builder nativo pasan. Se verificaron independientemente las 1166 huellas antes de actualizar documentación; cero discrepancias.

PostgreSQL/Redis etiquetados de esta ejecución ausentes en inventario independiente; sin procesos Gunicorn del wrapper diagnóstico. El contexto del servidor termina los hijos antes de retirar credenciales y rol propio. No intervención en servicios normales. Diagnóstico autorizado completado, producto intacto, MOD08 general pausado y objetivos 2s/5s pendientes.
