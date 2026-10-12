# Reproducción dirigida del ciclo de bloqueos de publicación

Estado: preparada, sin ejecución; no confirma todavía la causa del fallo de privacidad.

`tests/test_publication_refresh_lock_order.py` prepara un anuncio sintético sin
estado materializado, marca su generación dirty y utiliza dos conexiones propias.
La primera ejecuta el refresco real y pausa después del INSERT de estado.
La segunda bloquea Listing y solicita el marcado dirty real. El observador espera
un bloqueo efectivo entre esos dos PID mediante `pg_blocking_pids`; sólo entonces
libera el refresco para llegar al commit y sus restricciones referenciales.

El test propaga errores de ambos participantes, cierra sus conexiones y exige que
el cambio del escritor quede pendiente de recalcular. Los eventos tienen límites
finitos; no se usan esperas temporales como evidencia de intercalado. La prueba
no altera claves foráneas, no termina backends y no modifica restricciones de
privacidad. Su objetivo inicial es confirmar o refutar el ciclo propuesto.

Es una reproducción estructural: incluso si reproduce un deadlock, habrá que
relacionar las esperas con el fallo original de aprobación/restricción. Un resultado
positivo aislado tampoco descarta otros intercalados. Cualquier corrección debe
conservar exclusión entre refrescos, generación dirty, lectura pública nativa y
validación completa de autoridad. El intercalado del test tendrá que adaptarse
al orden correcto demostrado, sin convertirlo en una prueba que exige mantener
el bloqueo defectuoso.

Ejecutar mediante selección focused del runner oficial en PostgreSQL propio, sin
otra carga de pruebas. Conservar el resultado negativo y las observaciones antes
de editar la aplicación. CR09 y N3 siguen abiertos.
