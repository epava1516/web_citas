# MOD08 — Consulta explícita de optimización

2026-10-11. Notebook bb1f4634-45b7-4f41-b807-4b8502614b9d; conversación 99c86acd-9184-4561-8d47-e5c44f4636ab. Modelo interno no expuesto; fuentes conservadas (100).

[Consulta inicial](mod08-notebook-optimizacion-explicita-consulta-20261011.txt) / [respuesta](mod08-notebook-optimizacion-explicita-respuesta-20261011.json).
[Consulta correctiva](mod08-notebook-optimizacion-correctiva-consulta-20261011.txt) / [respuesta](mod08-notebook-optimizacion-correctiva-respuesta-20261011.json).

La respuesta inicial propone caches que omiten lecturas User, baseline_body y decrypt, incompatibles con las restricciones. La correctiva las retira. No se implementa ninguna.

Hipótesis de diagnóstico: contar parseos JSON repetidos tras descifrado autenticado fresco, medir decode/loads con wall y CPU de hilo, volumen, coste de igualdad real entre bytes independientes/copia y memoria. No saltar decrypt ni checks ni lecturas físicas. No hay margen medido ni garantía de equivalencia de resultados mutables compartidos.

El instrumento propuesto por el notebook es insuficiente: b == b mide identidad, no comparación de valores independientes; solo mide wall; el hash truncado no demuestra igualdad y no debe registrarse como huella de datos privados. record_unseal_metric no es implementación existente. No se aplica ese pseudocódigo. En coverage_page item.update modifica objetos construidos en la función; ello por sí solo no demuestra mutación de los dicts parseados, aunque hay referencias anidadas y deben auditarse consumidores. checked_assessment ya realiza deepcopy: no ignorar ese coste.

No pruebas nuevas ni cambios productivos ni capacidad ejecutada. MOD08 sigue pausado. Propuestas no constituyen evidencia de rendimiento ni aceptación.
