# Reproducción dirigida del ciclo de bloqueos de publicación

Estado: reproducción estructural negativa completada; correctiva en verificación.

El runner propio `20261012-235050-1dcb0e6f`, fuente `6944a4e`, reproduce
DeadlockDetected entre el escritor que mantiene Listing y solicita dirty y el
refresco que mantiene dirty y confirma referencias al terminar. Fuentes iguales
y contenedores propios retirados. [Negativo conservado](evidencias/cr09-refresco-deadlock-negativo-20261012.json).
El ciclo es consistente con el fallo histórico de privacidad; no se observó
independientemente el intercalado exacto de aquella ejecución.

La candidata `13453c2` conserva el bloqueo dirty y toma KEY SHARE NOWAIT de
Listing y la revisión referenciada antes de almacenar estado. Únicamente SQLSTATE
55P03 deja el lote pendiente y devuelve cero; otros errores se propagan. Un
savepoint permite deshacer los bloqueos parciales al fallar. La semántica de
conflicto de KEY SHARE con FOR UPDATE y liberación por rollback se contrasta con
la [documentación PostgreSQL 17](https://www.postgresql.org/docs/17/explicit-locking.html).
Continúa sin validar hasta completar las pruebas reales.

Primera verificación `20261012-235318-e2bf861b` registra dos errores del test:
PublicationDirty tiene listing_id directo, no relación listing. Fallan antes
de ejercitar NOWAIT. Ajuste preparado fuera de las fuentes congeladas; conservar
este negativo y repetir después la selección corregida, sin confundirlo con un
fallo de la corrección de aplicación ni con evidencia positiva.

La versión inicial de `tests/test_publication_refresh_lock_order.py` preparaba un anuncio sintético sin
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
