# Revisión de alcance: restauración y comunicaciones CR09

Requisitos: docs/83-auditoria-pendientes-cr09.md, filas restauración (15%)
y comunicaciones (8%). Esta revisión parcial no cambia porcentajes ni acepta CR09.

## Restauración

La prueba `test_old_pg_dump_and_media_cannot_reintroduce_erased_data` en
`tests/test_recovery_pg_restore.py` utiliza pg_dump/pg_restore del contenedor
propio, copia medios y compara sus huellas. En el hijo Django comprueba
checkpoint independiente incorrecto sin efectos, reconciliación, destrucción de
medios de la identidad sintética, preservación de otro sujeto, sesión antigua
rechazada e idempotencia. Verifica invalidación y refresco MOD05 y limpia la
base restaurada. Las aserciones limitan reconciliación a 28.800 s y antigüedad
a 3.600 s. Las propiedades terminales proceden del JUnit del bloque 2.

| Medida sintética | Resultado | Objetivo local |
|---|---:|---:|
| Restauración y reconciliación | 5,129507 s | <= 28.800 s |
| Antigüedad superior acotada del backup | 7,021105 s | <= 3.600 s |

[Propiedades verificadas](cr09-restauracion-regresion-propiedades-20261014.json).
No demuestra cadencia, custodia ni capacidad productivas. La evidencia pertenece
a 9b0353f; falta reconciliar versión común N3. No confundir estos backups
funcionales con las tres pruebas opt-in del caché de fixtures del directorio.

## Comunicaciones

Los seis casos de `tests/test_rights_communications.py` pasaron en el bloque 4.
Su contenido verifica revisión independiente, alcance exacto, auditoría antes de
descifrado, rechazo de falsos recibos de entrega y permisos revocados para
supresión, limitación y oposición. Esto es evidencia funcional de esa selección,
no de todos los canales ni de entrega externa.

Docs/90 define el buzón privado PostgreSQL interno como canal local real.
`tests/test_notice_delivery.py` declara explícitamente entrega simulada externa,
producción deshabilitada, reintentos/backoff, ausencia de secretos en errores y
reclamación concurrente. Para la matriz de cierre deben vincularse también los
resultados de ese archivo y de buzón/acuse/inventario, sin llamar entrega real
a una simulación. Reconciliación completa de comunicaciones pendiente.

## Comprobación adicional del buzón interno

La inspección de `tests/test_rights_communications.py` confirma GET con payload
privado ausente, POST de lectura auditada, rechazo de destinatario ajeno,
acuse ligado a lectura exacta, replay con una sola auditoría y rechazo de
alteración de la hora de acuse. La entrega serializada rechaza autoridad retirada.
Son aserciones del buzón real local de la aplicación, distintas de los adaptadores
externos simulados. No afirman entrega a personas reales.

Los resultados adicionales vinculados son 7 casos de operaciones/recuperación
de avisos, 2 de localización ES/EN, 2 de inventario propio y 6 de entrega
simulada/reintentos. Todos tienen reports terminales sin fallo en sus bloques.
[Reports exactos](cr09-comunicaciones-buzon-regresion-20261014.json).
Estos archivos tienen alcances diferentes: localización de textos no sustituye
un recorrido HTTP, y un inventario opaco no demuestra lectura ni recepción.
Sigue pendiente la correspondencia completa por derecho y versión común.
