# Diagnóstico de reutilización del sello CR09

El bloque 3 completo `20261014-081348-78888303` terminó con 846 PASS,
1 FAIL, 0 ERROR y 6 SKIP. El fallo sucede en la primera reutilización
antes de alterar la caducidad del comprobante. Se conserva el resultado negativo.

El diagnóstico observa la implementación real de `holds` y `_replay`,
sin sustituir sus respuestas, y registra únicamente coincidencias de entradas
(configuración/código, solicitante, caducidad) e índices de huellas diferentes.
No registra parámetros SQL ni contenido de expedientes.

El ensayo propio PostgreSQL de los seis casos del sello
`20261014-100501-1d4b476a` obtuvo 6 PASS, 0 FAIL, 0 ERROR y 0 SKIP
(158,750 s de JUnit). Fuentes congeladas y limpieza PG/Redis verificadas.
Incluye rechazo de manipulación, cambio ACL, comprobante caducado y
corrupción del objeto externo real RustFS. El resultado no demuestra
la corrección del fallo de la batería completa ni aceptación CR09/N3.

Siguiente comprobación: bloque 3 completo con este diagnóstico, secuencial,
con los mismos límites y conservación de cualquier fallo. Las consultas
sin orden explícito son una hipótesis pendiente, no una causa demostrada.
