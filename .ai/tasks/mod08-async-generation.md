# MOD-08 pieza 5 — generación asíncrona

Base e8edcb1; escritor Codex aislado, rama worktree-agent-ab23eda63576809b3.

## Diseño antes de editar

Job durable PostgreSQL con clave UUID única, referencia a actor/caso/proof/selección,
versiones originales de sesión/MFA y inputs privados cifrados. HMAC de inputs para
conflictos de replay; broker sólo recibe PK del job. Encolado breve con locks
canónicos y autoridad/proof fresca antes/después de espera, sin producir export.
Worker reclama lease durable y ejecuta generate existente dentro de transacción
con lock del job; generate conserva todos sus guards/locks y consumidores sync.
Errores de autoridad/dominio terminan sin export; técnicos dejan reintento acotado.
Beat recupera queued y leases vencidos: caída worker revierte generación y no duplica.
Estados/progreso por fase (sin porcentaje estimado), ES/EN, HTMX local y GET canónico.
Nunca se confía en estado Celery ni se muestra motivo privado/error técnico en UI.

## Propiedad

Modelo nuevo en safety/models, migración 0113; rights_portability_jobs.py;
tasks.py append; rights_portability_export_views.py, urls y template export/job;
tests async y static/vendor/htmx. Settings beat coordinado con principal.

## Evidencia

Pendiente. No PASS ni aceptación.

## N2 primera — terminal negativo preservado

20261010-122659-14afabde:140 tests,121PASS/19FAIL/0skip,723.789s; source hashes
unchanged true, PG/Redis/tmp retirados. Worker/broker real y Chromium ESEN dentro
PASS; 19 fallos comparten inferencia job scope desde metadata de parsers puros.
Corrección: consumidores autorizados suministran job_ids explícitos, no DB lookup
implícito en parsers de origen. Se añaden pruebas de broker outage, límite retry,
espera PostgreSQL observable revocación y censo positivo; se adapta contrato HTTP
previo en coverage_use/mixed_fields/localization sin quitar pruebas sync dominio.
Segunda N2 pendiente; no aceptación ni capacidad por 302. Beat requiere entrada
reconcile-portability-export-jobs60s que principal integra en settings propiedad storage.

SegundaN2 terminalnegativo 20261010-124254-0b093368:109PASS/3FAIL/0skip112tests605.679s;
hashesunchanged/cleanupreal. Las19 anteriores corregidas y HTTPold/binary/browserPASS.
Tres nuevos harness F: idiomaEN noES; accountscope necesitaatomic; brokercopy0sinmessage.
Corrijo idioma y locks; asserts queue/appbroker/Redisraw para diagnosticar publicación.
Worker añade preflightno consumidor latestproof/status/expiry antescanonicalwait; full
proofscope aún can_prepare bajo locks. TerceraN2 jobs dirigida pendiente, sin capacidad.

N2 correctiva final `20261010-130443-c476a607`: 3 PASS, 0 FAIL, 0 skips, 57.21 s. PostgreSQL/Redis reales, publicación UUID y proyección privada positivas persona/cuenta; transporte/eager y shards comprobados. Fuentes congeladas; limpieza real confirmada. Causa del harness: eager heredado; fijado False explícitamente en prueba broker. Evidencia complementaria: tercera N2 23 PASS (worker real, revocación tras espera PG, retries, lease, HTTP ES/EN); segunda N2 109 PASS (orígenes históricos, HTTP previo, Chromium ES/EN/sin JS, binarios); primera N2 export races/inventarios originales PASS. Terminales negativos anteriores se preservan. Integración conjunta y N3 capacidad siguen pendientes; no aceptación integral.

## Diseño capacidad separado (antes de editar)

Sustituir únicamente finish generation síncrono por POST TCP autenticado a export, UUID
durable y GET privado de estado hasta succeeded/export commit. Tiempo incluye encolado,
cola y sondeo; límite original120s, nunca un302. Espera de recovery finita1800s permite
registrar una infracción sin dar PASS. Worker Celery prefork2 y Beat comparten cgroup app
existente de Gunicorn; ninguna reserva extra. Readiness ping real, cgroup leído del kernel,
VmHWM por proceso100ms, teardown verificado de grupos. Flags full delivery/profile full y
preflight finito únicamente; sin carga aquí. Rol runtime PostgreSQL aislado del helper de
canonical_tests aplica sólo a hijos y se limpia después de parar todos. Purga deliveries10s,
reconcile60s/orphans1h. Storage conserva ownership bind/proxy/303/GETEOF.

Patch de capacidad preparado: Ruff/compilación/documentación solamente. Helper runtime,
S3/proxy y launcher presupuesto requieren integración principal; no N3 ni PASS de capacidad.

## Correctiva perfil real 2026-10-10

Base5820942, worktree codex/mod08-async-diagnostic. Perfil real
20261010-141424-1decf816 terminal ERROR, cleanup=true; no se repite carga aquí.
Causa confirmada: sampled exigía303→GET a todos los POST cuyo opener disponía del
transporte private_delivery, incluido binary_page_save normal200. Fallaba antes de
append selection_versions, no acreditaba pérdida de imágenes/revisiones.
Corrección: require_private_delivery explícito sólo en descargas; profile y normal
comparten guards303→GET/status/no-store, sin ampliar límites ni negativas. Diagnóstico
incluye stage/status/bytes/cache/stages, conteos binding y traceback acotado6KiB;
error HTML sólo texto errorlist/alert1KiB, sin documentos completos ni inputs privados.
Verificación pequeña autorizada:8guards puros PASS0.54s con entorno integrado; Ruff PASS.
Son pruebas de orquestación con mocks declarados, no broker/HTTP/PG real ni capacidad.
Primer intento colección con venv root falló por dependencia orjson ausente; ejecutado
con venv integrado completo. Principal debe integrar y repetir perfil real solo.

## Diagnóstico SQL offline solicitado 2026-10-10

Base d5356ab, worktree codex/mod08-fingerprint-diagnostic. Diseño antes de editar:
perfil full después del target y antes del flujo; misma credencial runtime privada del
server, conexión independiente real, identidad LOGIN sin privilegios ni ownership,
snapshot REPEATABLE READ READ ONLY. Comparar aggregate fullsource antigua/new usando
mismas bindings y _parts/_union vigentes; cambiar sólo constante municipality antigua.
Dos rondas alternadas old/new y new/old, igualdad digest/count. Cuatro EXPLAIN ANALYZE
BUFFERS SETTINGS JSON completos (full old/new y municipality old/new), sin recortar
JIT/planning/execution/loops ni conteos municipality/revisions/through. Se conservan
negativas y límites; no acceptance/p95 ni compilación nativa. Endpoint sólo expone path
privado al consumidor; no se registra path, rol, contraseña ni credenciales. Fichero
0600/directorio0700 <=4KiB; secretos en memoria, planes saneados antes de evidencia.
Canonical P10 toca consumer y debe conservar llamada sólo en fallback tras preparación;
cache hit nunca repite diagnóstico previo. Edición offline solamente mientras N2 fuente
congelada; no imports/procesos/tests/build ejecutados. Verificación e integración pendientes.

Tras terminal N2 sourceSQL d5356ab21PASS/0FAIL/0skip106.88s, principal autorizó
verificación offline: Ruff/py_compile PASS;6guards puros PASS0.14s (modo/size/topology/
symlink/validconfig/flags/scrubbing). No conexión ni ejecución SQL real; no afirmar
planes/digest/runtime perfil PASS hasta ensayo del principal. Tests sin PG personal.

## P12 proyección pura dentro del batch (offline)

Base702914e; worktree codex/mod08-batch-projection. Diseño antes de editar comunicado
al principal: memoizar exclusivamente project_selected después de validar/decrypt frescos
por child. Ninguna decisión aprobada, firma, metadata imagen, lock, lectura física/SHA o
expiry/autoridad/proof se omite. ContextVar privado sólo vive dentro del batch atomic y
inspection_source, misma conexión; scope case/actor epochs/proof/expiry/source y exactos
ciphertexts/metadata/config/código. Resultados deepcopy, máximo4entradas, limpieza finally.
Sin toggle público, caché persistido o valores cliente como prueba. Cuatro record/audits
siguen generando UUID5 individuales y el rollback/final source/actor/proof se conserva.
No se cachea decrypt ni hashes de firmas ni _audited_images; reducción medida pendiente.

Implementación offline y N2 preparada: equivalencia batch→bypass puro con mismos IDs y
resultados, 4audited_images físicos reales y4SelectionRead+CoverageRead, 1project_selected;
negativas tardías epochs/proof/source/expiry/cipher/signature deben revertir todas las
lecturas/acciones. Selección N2 prevista módulo nuevo más coverage_batch/inspection/use,
selection_review, shared inspection source y guards binarios. Runner PG real del principal;
no tests/imports/compilación/carga ejecutados mientras perfil fuentes congeladas.
