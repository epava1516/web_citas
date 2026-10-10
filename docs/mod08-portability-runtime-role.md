# MOD08 pieza11: adopción local del rol y de la cadena

Alcance acotado: siete familias de metadatos de portabilidad ya cubiertas por
0115. No sustituye validaciones de origen, prueba, autoridad, tiempo, imágenes ni
acciones mutables. No acredita aceptación N3 ni rendimiento constante global.

## Permisos y uso

`configure_rights_evidence_role` concede `UPDATE(id)` sólo en esas siete tablas
para permitir los `SELECT FOR UPDATE` existentes en los flujos Django. PostgreSQL
requiere permiso UPDATE en alguna columna para bloquear filas. Esto **no** concede
UPDATE de tabla: todo UPDATE, incluso `SET id=id`, sigue rechazado por el trigger
para el runtime no propietario. La confianza comprueba ACL por columna y permite
exclusivamente `id` en esas siete tablas, además de comprobar propietarios,
funciones de triggers, ejecución y permisos de tablas. Head/event no conceden
ninguna columna UPDATE ni INSERT directo. Migrador/propietario siempre requieren
validación completa: su capacidad administrativa impide confiar en sólo el head.

`RIGHTS_EVIDENCE_ENFORCED=1` incorpora la validación completa de cadena en
`validate_approved_assessment`, consumidor real del dominio. Rechaza contexto
propietario, superusuario y permisos/triggers inseguros. Está desactivado por
defecto; en ese modo no añade consultas a los servicios actuales. Mantiene todas
las comprobaciones del dominio y no introduce caché de aprobaciones ni autoridad.
La modalidad activada añade coste de lectura completa de las siete familias;
no se presenta como una optimización de latencia. Tickets existentes siguen
sirviendo únicamente para metadatos inmutables, nunca para autorización.

## Bloqueos

0116 preserva 0115 y fusiona las hojas 0112/0115. El bounded head usa `FOR UPDATE`,
no `FOR SHARE`, para evitar upgrade de bloqueo al validar y posteriormente
append dentro de una transacción. Una exclusión advisory transaccional por UUID
de caso se adquiere antes de head/action en funciones locked_head, insert y
tombstone; también serializa casos sin head todavía. Las colisiones del hash
sólo serializan casos distintos, no mezclan datos. El guard de alcance de
RightsAction no adquiere ese advisory después de haber bloqueado su fila.
No se llama pg_terminate_backend ni se cambia ningún servicio habitual.

## Configuración explícita, sin despliegue ejecutado

El override `compose.runtime-role.yaml` es opcional. Su job migrador ejecuta
`initialize_rights_runtime` con credenciales propietarias y después crea o
configura un login distinto, sin atributos administrativos ni herencia del
propietario. Sólo la contraseña explícita de `POSTGRES_RUNTIME_PASSWORD` se
usa como secreto; nunca se imprime. App/worker/beat esperan ese job y usan el
runtime, activando enforcement. Los grants normales de aplicación se conceden
antes de restringir metadatos; no se conceden grants automáticos sobre tablas
futuras, por lo que tras nuevas migraciones se debe repetir el job migrador.
La base y sus volúmenes no se borran. La operación debe prepararse con las copias
y el procedimiento de recuperación del operador antes de usarla sobre su entorno.

No se ha ejecutado ese override sobre servicios normales. La integración aquí
se comprueba en recursos PostgreSQL/Redis desechables propios del runner, usando
SET ROLE real y datos sintéticos. No es una simulación de privilegios.

## Evidencia N2 finita

Runner propio nativo, PostgreSQL real, dos workers y datos sintéticos:

- `20261010-130017-8ddba2e0`: 1 PASS, 15 fallos y 4 errores; falta de cast
  varchar64/text en RETURN QUERY y fixtures importadas eliminadas por lint fix.
- `20261010-130213-054de7ff`: error previo a pytest por F811 de fixtures
  importadas; se conservó la ejecución y se corrigió su declaración explícita.
- `20261010-130229-6528d26c`: 20 PASS, 0 skips, 61.40 s. Dieciséis pruebas de
  cadena y cuatro de runtime/domain. Incluye locks reales de las siete familias,
  UPDATE(id) rechazado, enforcement propietario rechazado, drift detectado,
  dos transacciones validar→tombstone sin caselock y consumo de aprobación real
  seguido de denegación por autoridad desactivada.
- `20261010-130419-39ea401b`: 6 PASS, 0 skips, 54.39 s. Repite las cuatro runtime
  y añade grant UPDATE de otra columna rechazado por confianza y provisionador
  con conexión LOGIN real independiente. El migrador del test ejecuta migrate
  real sobre la base propia y elimina el rol creado al finalizar.

Todas las ejecuciones preservan sources_unchanged y acreditan eliminación de sus
contenedores PostgreSQL/Redis. Los JUnit, logs y resultados íntegros permanecen en
artifacts/local-ci del worktree indicado en la
[evidencia resumida](evidencias/mod08-evidence-runtime-n2-20261010.json).
La comprobación quiet de Compose verifica sólo estructura, no un despliegue.

## Procesos de capacidad: helper de rol independiente

`tests/capacity_runtime_role.py` ofrece
`runtime_role_environment(base_settings_module='capacity_gunicorn_settings')`.
El proceso pytest conserva el migrador; el helper ejecuta el provisionador real
sobre su base desechable, verifica un LOGIN TCP independiente sin atributos
administrativos ni membresía propietaria y entrega un diccionario de entorno
para aplicar **después** de establecer el módulo de settings base del servidor.
El mismo diccionario sirve para Gunicorn, Celery y Beat. Su contexto debe envolver
sus readiness, uso y teardown: todos los hijos deben cerrarse antes de salir.

El password se guarda exclusivamente en JSON privado 0600 dentro de directorio
0700. Un módulo privado 0600 importa los settings base y cambia sólo la conexión
por la del runtime; activa `RIGHTS_EVIDENCE_ENFORCED` y desactiva DEBUG. Los
argumentos y el diccionario de entorno no contienen ese password; tampoco
heredan los passwords migrador/runtime originales. El output del provisionador
se captura y se comprueba antes de entregar el entorno. Al salir se exige que
no queden conexiones del runtime, se elimina el rol sin terminar backends y se
retiran ambos archivos. No hay fallback silencioso a propietario.

En capacidad se exige el contexto del controlador previamente verificado:
capacity_settings, CAPACITY_ENVIRONMENT_VERIFIED, test_capacity_ci, host pg,
puerto5432 y migrador ci. La comprobación del label/red y de la topología ocurre
en el controlador antes de instalar esos settings dentro de su contenedor app.
En N2 externo el helper comprueba adicionalmente el contenedor PostgreSQL real,
su label y el puerto publicado del runner local, y la base exacta por worker.
Un nombre de alias normal o un rol/contexto inesperado se rechaza antes de
provisionar. No autoriza acceso a servicios normales ni ejecuta carga.

`20261010-130920-a3189ffb`: **2 PASS, 0 skips, 39.84 s** con PostgreSQL real y
dos workers. El hijo Python/Django conecta mediante el LOGIN independiente,
acredita confianza por ACL/triggers y enforcement activo; el migrador del proceso
padre permanece intacto. Se comprueban modos privados, ausencia del secreto en
entorno/stdout/stderr y desaparición de archivos y rol, además del rechazo del
alias no propio. Sources_unchanged y cleanup PostgreSQL/Redis son positivos.
[Evidencia del helper](evidencias/mod08-capacity-runtime-helper-n2-20261010.json).
La integración del consumidor Gunicorn/worker corresponde a su frente de entrega;
esta N2 finita no ejecuta ni acredita una muestra de capacidad.
