# MOD08 — Diagnóstico finito de descifrado y parseo JSON

Autorización del usuario 2026-10-11: «Hazlo pues», referida al diagnóstico mínimo; no reanudación de aceptación completa de capacidad. Código productivo sin cambios. [Métricas completas y límites](mod08-unseal-diagnostico-20261011.json).

## Instrumento y garantías verificadas

Instrumentación exclusivamente en tests/capacity_unseal_diagnostic.py y pruebas en tests/test_capacity_unseal_diagnostic.py. Conserva cada cipher(), Fernet.decrypt, decode y json.loads. Cada llamador recibe un objeto recién parseado; no reutiliza autoridad, plaintext como respuesta, ni resultados criptográficos. Descompone wall/CPU de hilo en descifrado (incluye cipher y codificación del token), decode y parseo. Reconoce repeticiones mediante igualdad completa de bytes independientes, retenidos temporalmente hasta128entradas/32MiB. Exporta solo números/grupos ordinales, nunca plaintext, hashes, ciphertexts ni claves. Mide búsqueda/igualdad y deepcopy como trabajo adicional del observador. El coste de búsqueda incluye recorrer todos los grupos, no solo un hit. Los cronómetros tienen overhead; CPU/wall de las etapas no son medidas intrínsecas de syscalls.

Las siete pruebas finales cubren lote real con runtime enforced, resultados/idempotencia y auditorías equivalentes, rollback completo de fallo posterior, restauración de aliases originales y tardíos, límite/reentrancia, resultado mutable siempre nuevo y rechazo de token inválido, y tres tamaños sintéticos. No cambios de locks/aislamiento ni omisión de lectura física. La primera corrida conjunta incluyó dos pruebas existentes de fases, pero no se suman sus8PASS a los7PASS de la versión final.

## Resultado

Final20261011-111132-92674fec:7PASS/0fallos/errores/skips73,365s JUnit. PostgreSQL17 y Redis7.4 reales propios, Python3.12.15/Django5.2.17/cryptography50.0.2, un worker. Rol runtime no propietario con enforcement activo en lote/rollback. 1155huellas comprobadas independientemente, ninguna diferencia; contenedores propios ausentes comprobados con inventario Docker independiente. Los medios/identidad son fixtures sintéticos: no proveedor ni datos reales. No RustFS en esta dirigida; no transporte externo ni aceptación de almacenamiento/descarga.

| Escenario | Llamadas unseal | Descifrado CPU ms | Parseo CPU ms | Parseo repetido CPU ms | Búsqueda/igualdad CPU ms | Copias de prueba CPU ms |
|---|---:|---:|---:|---:|---:|---:|
| Lote real pequeño (3 páginas) | 49 | 7.334 | 1.271 | 1.091 | 0.456 | 1.686 |
| 4096 bytes sintéticos | 4 | 0.445 | 0.072 | 0.041 | 0.024 | 0.031 |
| 1048576 bytes sintéticos | 4 | 41.834 | 8.745 | 6.522 | 0.588 | 0.055 |
| 16777216 bytes sintéticos | 4 | 717.227 | 185.972 | 121.104 | 9.921 | 0.082 |

Lote sintético pequeño:49llamadas, seis grupos de contenido,4832bytes únicos. Solo1,091ms de CPU de parseo repetido frente a1,686ms de copias y0,456ms de búsqueda/igualdad. No hay margen demostrado para añadir memo JSON a este escenario. El parseo repetido es una cota de CPU eliminable ideal en las llamadas observadas, no ahorro HTTP: habría que restar lookup/copia y preservar semántica de mutación.

La sonda16MiB tiene una cadena grande, no el JSON anidado del expediente1500revisiones. Sus121,104ms de parseo repetido no prueban ventaja en el request; deepcopy comparte la cadena inmutable y por eso cuesta poco. No extrapolar copias a dicts/listas grandes. La retención numérica mide solo bytes de plaintext único, no RSS, árboles parseados, buffers del descifrado ni pico agregado.

## Límites y decisión

No p95 HTTP/TCP/WSGI ni población contractual ni20muestras. Una medición por escenario en la versión final; evidencia inicial conservada aparte. Control directo crea auditorías y observado es replay: no comparación A/B causal ni overhead estimado por resta. El binario Cython histórico no está presente en este checkout; no comparar tiempos globales con baseline3,753392s. El código observado permite imports nuevos: se restauran también sus aliases al salir; contextos de otros hilos delegan a original y concurrencia del instrumento es rechazada.

Decisión: no implementar cache ni afirmar solución de2s. Para decidir sobre JSON en el bloqueo original haría falta observar esta descomposición en el mismo expediente grande/ciclo, con fixture y runtime equivalentes. Este diagnóstico pequeño NO descarta que la distribución grande sea distinta. Si allí el coste repetido sigue siendo pequeño, priorizar descomposición de ejecución/fetch/pipeline.sync y trabajo no observado en validate_assessment/source, sin atribuir wall−CPU automáticamente a red.

Se corrigió el enlace absoluto histórico en docs/actas/04-cr09-auditoria-pendiente.md hacia ../46-historial-colas-generales.md: bloqueaba el runner antes de pytest. Negativo inicial20261011-110823-104b3a1e conservado; siguiente20261011-110845-ba7c22e0 pasó8tests y motivó mejora acotada de limpieza/límites del instrumento. Sin commits/push ni publicación, sin agentes ni nueva captura completa. Diagnóstico autorizado terminado; aceptación MOD08 original permanece pendiente.
