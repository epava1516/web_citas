# MOD-08 pieza 11 — cadena acotada de metadatos de portabilidad

Diseño reservado antes de implementación. Alcance: únicamente Read, Review,
SelectionRead, SelectionReview, ImageRead, CoverageRead y CoverageReview. Estas
siete tablas no contienen ciphertext ni campos purgables. No se congela RightsAction,
que actualiza payload_digest, ni assessment/selection/coverage/export/payloads.

Cada INSERT añade mediante trigger una entrada hash por expediente y actualiza
una cabeza bloqueada FOR UPDATE. El evento guarda tabla, PK, huella SHA-256 de la
fila, secuencia, hash anterior y hash de enlace; no copia texto, ciphertext ni actor.
Fechas se codifican con formato UTC explícito. Backfill de filas existentes ordena
tabla+PK, usa created_at original y no reescribe eventos previos. La transacción
comparte row/event/head: rollback no deja huérfanos. Tombstone es evento append-only
con código acotado y referencia opaca; no elimina ni reemplaza la purga original.

El rol runtime separado recibe SELECT/INSERT en las siete fuentes y SELECT en
head/event; se revoca UPDATE/DELETE/TRUNCATE. Triggers rechazan mutación para todos
salvo propietario/migrador exacto. Funciones SECURITY DEFINER tienen search_path
fijo, interfaces acotadas y funciones internas sin EXECUTE PUBLIC. Head/event
rechazan mutación directa runtime y sus inserts sólo los realiza el definer.

El owner/migrador conserva mantenimiento/restore y pytest flush. Esta excepción no
es enforcement de runtime: el usuario normal de los servicios actuales coincide
con owner y **no acredita inmutabilidad**. El comando configure_rights_evidence_role
rechaza superuser, owner y miembros del owner; se exige separación de roles antes
de habilitar confianza incremental en un entorno. No se alteran servicios normales.

validate_chain verifica filas y enlaces completos; tickets conservan head/count y
sólo permiten comprobación rápida si el rol es runtime separado y las garantías de
catálogo/privilegios/triggers están comprobadas. Con owner/superuser siempre relee
filas: modificar evidencia aunque head no cambie debe detectarse. Ningún ticket
reemplaza fuentes, pruebas, autoridad, tiempo, imágenes ni RightsAction mutable.
Los validadores de dominio actuales permanecen íntegros en esta primera entrega.

Selección PostgreSQL prevista: archivo test_rights_evidence_chain completo, dos
workers con roles runtime reales NOOWNER/NOSUPERUSER, fuentes congeladas, PG17/Redis7.4
propios, timeout7200 y JUnit/limpieza. Controles: siete triggers completos,
UPDATE/DELETE/TRUNCATE runtime denegados, eventos/cabeza protegidos, inserciones
concurrentes serializadas, rollback, backfill/restauración y tombstone minimizado;
owner drift detectado por validación completa. No PASS ni aceptación antes de
terminal. Capacidad/N3 y optimización de validadores posteriores siguen pendientes.

Reserva de ejecución: N2 focused `tests/test_rights_evidence_chain.py` completo,
8 casos recogidos, dos workers loadfile (aislamiento de bases del runner propio),
nativos /tmp/web-modelos-librdb-v2.4.0, timeout7200. Datos puramente sintéticos
creados directamente para probar infraestructura: no acreditan verificación de
identidad ni aprobación funcional de portabilidad. Antes del lanzamiento Ruff,
documentación y colección PASS; después árbol congelado hasta terminal.

Negativo N2 conservado `20261010-123938-adfbb627`: 4 PASS/4 FAIL/0 skips,
48,276s JUnit, fuentes intactas y recursos retirados. Causa confirmada: SELECT
FOR SHARE de head exige privilegio UPDATE en PostgreSQL, que correctamente no
posee runtime. Se añade función SECURITY DEFINER acotada a UUID de expediente para
leer/bloquear la cabeza sin conceder UPDATE. Tombstones con misma clave/código son
idempotentes y códigos distintos en la misma clave se rechazan. Repetición afectada:
mismo archivo completo, ocho casos, mismos recursos y timeout, fuentes congeladas.

Correctiva N2 `20261010-124149-b01cdd3e`: 8 PASS/0 fallos/errores/skips,
47,770s JUnit, fuentes intactas y ambos contenedores retirados. Queda control
específico adicional de alteración administrativa del enlace (payload_digest,
source_pk y created_at) y count booleano: tres casos nuevos, mismos recursos,
fuentes congeladas hasta terminal. No se repiten los ocho casos ya válidos,
porque sólo se añade el control específico sin modificar implementación.

Control adicional de enlaces `20261010-124340-ca7ee810`: 3 PASS/0 skips,
45,408s JUnit y retirada/fuentes correctas. Revisión raíz detecta dependencia
mutable de scope en RightsAction: se añade guard de request_id/actor_id/operation/
expected_version/key sólo cuando la acción está referenciada por estas siete
familias, permitiendo payload/encrypted_reason y demás campos legítimos. INSERT
bloquea la acción FOR UPDATE antes de derivar request para serializar carreras de
scope. Confianza de ticket comprueba este trigger y rol propietario de la acción.
Nuevo N2 completo de dieciséis casos (cinco nuevos campos de scope); misma selección
PG/worker2/timeout, congelación y limpieza. No sustitución de guards de dominio.

N2 scope `20261010-124553-2372fdce`: 11 PASS/5 FAIL/0 skips, 60,611s JUnit,
fuentes/retirada correctas. Los cinco casos nuevos fallaron preparando el segundo
usuario: email vacío duplicado contra la restricción real. Se da email sintético
único al actor nuevo; implementación intacta. Repetición de las cinco variantes
nuevas únicamente, mismos recursos y fuentes congeladas; los once controles
anteriores ya verificaron la implementación con guard de scope activo.

Correctiva específica scope `20261010-124739-db4a59c4`: 5 PASS/0 fallos/errores/
skips, fuentes/retirada correctas. Los once controles previos verifican la misma
implementación final; sólo cambió el email del fixture de estos cinco casos.
[Evidencia y negativos conservados](evidencias/mod08-evidence-chain-n2-20261010.json).
No se suman ejecuciones como N3 ni se declara pieza11 global completada: faltan
adopción en validadores, dominio completo, runtime separado integrado y capacidad.
La infraestructura acotada queda reportada para revisión/integración del principal.
