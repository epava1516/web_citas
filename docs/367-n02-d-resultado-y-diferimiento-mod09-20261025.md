# N02D — resultado completo y diferimiento de optimización MOD09

25 de octubre de 2026. Ejecución `20261025-145903-bd2edbe9`, según [366](366-n02-d-prerregistro-evaluacion-completa-mod09-20261025.md). Resultado original **FAIL_DELIVERY_STAGE_LIMITS: 1 FAIL, 0 ERROR, 0 SKIP**. No hay mejora clara del circuito completo. El usuario acepta los tiempos actuales para continuar en alfa y ordena pasar al siguiente punto, posponiendo esta optimización al final del desarrollo. Se conserva el guard adoptado y verificado en [365](365-n02-c-resultado-contraste-agrupado-guard-20261025.md).

| Etapa de aplicación | Anterior A / B | Actual A / B | Objetivo original |
| --- | ---: | ---: | ---: |
| Lectura de cobertura, p95 | 3,377 / 3,368 s | 3,403 / 3,404 s | 2 s |
| Descarga JSON por paquete, p95 | 6,600 / 6,529 s | 6,420 / 6,494 s | 5 s |
| Descarga binaria por paquete, p95 | 6,645 / 6,770 s | 6,660 / 6,608 s | 5 s |
| Generación asíncrona, una por sujeto | 40,744 / 40,667 s | 39,749 / 39,668 s | Presupuesto original conservado |

Anterior: [326](326-auditoria-medicion-actual-mod09-b10-20261024.md), misma selección original. Son ejecuciones en fechas diferentes, sin repeticiones emparejadas del circuito completo: las diferencias observadas no prueban causalidad ni una mejora general. Cada sujeto tiene 384 lecturas de cobertura y 20 descargas de cada tipo; los dos sujetos son concurrentes, no 40 tests independientes. La mejora local del guard no se extrapola al p95 del circuito.

Duración QA separada: JUnit completo 2004,770 s frente a 2015,181 s anteriores (10,411 s menos, aproximadamente 0,52%). El caso consumió 2003,935 s; controlador 14:59:03–15:34:21 UTC, con preparación/recogida propias. La duración QA no es latencia de aplicación.

## Auditoría y límites

La [auditoría reproducible](evidencias/n02-d-resultado-auditoria-20261025.json) conserva referencias SHA a report, launcher y archivo de ambas fases. Control previo READY_NOT_CAPACITY con limpieza; carga completa con fuentes congeladas intactas (1734 huellas), cuotas originales de 8 CPU más controlador separado, límite conservador de memoria propia 4326178816 bytes y almacenamiento 5939134464 bytes. Consulta independiente posterior: cero contenedores, redes y volúmenes de ambas ejecuciones. Archivos legibles, dentro de techo y sin problemas declarados de archivo. No se publican logs privados.

Ambos flujos llegan a la asignación final de success sin excepciones: antes se verifican 1500 revisiones, datasets, cuerpos completos, SHA, originales recuperados, partes ZIP ≤8 MiB, separación y respuestas originales. success sigue falso por las infracciones temporales. Las aserciones finales de concurrencia del test quedan después del FAIL; la auditoría recalcula por separado los intervalos originales y registra los solapamientos, sin convertir el caso en PASS. Identidad externa sintética: no acredita proveedor real.

Telegram terminal confirmado. La shell completó la compactación mediante nuevo elemento persistido y reactivó el mismo goal conservando createdAt y consumo. No se creó otro objetivo ni se repitió la batería.

## Disposición acordada

Se difiere **la optimización restante de rendimiento de MOD09** al final del desarrollo por instrucción expresa del usuario, no por cumplimiento de 2 s/5 s. Se conservan objetivos, FAIL, evidencia, cambio local y deuda de atribución/crecimiento/retención/concurrencia pendiente. No se lanza otra batería MOD09 para perseguir más reducción ahora. No se aplazan correcciones funcionales o de seguridad que aparezcan con evidencia.

N02 queda con trabajo local verificado y resto diferido por decisión del usuario; no se cuenta como bloque íntegramente PASS. N00/N01 siguen siendo los dos bloques aceptados sin límite. El siguiente frente ya abierto es N06, con continuidad de [359](359-n06-b-resultado-peticion-cola-real-20261025.md); su selección concreta requiere refresco previo del grafo y revisión de pendientes. Alfa, sin apertura ni proveedores nuevos.
