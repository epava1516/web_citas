# Revisión adversarial de la integración MOD-08 (Claude, solo lectura)

Fecha: 2026-10-10 14:20 UTC. Objeto: rama `codex/mod08-integration` (`c50b76a`, 42 commits sobre master) mientras Codex dirige y ejecuta un preflight de capacidad vivo. Sin ejecuciones ni ediciones en su worktree.

## Hallazgos

1. **Sello v2 (`apps/safety/rights_validation_seal.py`) — correcto en lo actual, hueco estructural.** El hash por fila calculado en PostgreSQL antes de llegar a Python, el orden real, la clave con relaciones en caché y configuración viva, y el descarte de SQL volátil o escrituras son sólidos. Riesgo: una sentencia grabada con parámetro temporal cuyo resultado no contenga columna de caducidad (`.exists()`, `.count()`, agregados con `expires_at__gt=now`) se reproduciría con el instante original; `valid_until` solo baja por columnas `expires_at`/`receipt_expires_at`/`valid_until` presentes en los resultados. En la cadena de portabilidad actual no se da (las consultas temporales usan `.first()`/`get()` y cargan la columna), pero nada lo impide en el futuro. Propuesta conservadora: marcar `supported=False` si una sentencia tiene un parámetro `datetime` y su descripción de resultado no incluye una columna de `EXPIRY_FIELDS`; prueba adversarial con `.exists()` filtrado por tiempo.
2. **Cadena de evidencia (pieza 11).** Diseño acotado y riguroso (7 tablas de metadatos, triggers, rol runtime separado, `SECURITY DEFINER` con `search_path` fijo, guarda de ámbito de `RightsAction`, negativos conservados). Aún no la usan los validadores, así que no aporta rendimiento todavía; la inmutabilidad solo se acredita con el rol runtime separado (con el propietario actual, no). Debe activarse en el entorno de capacidad para que su medición sea representativa.
3. **Integración pendiente.** Nada en master. Las baterías conjuntas (590/14, 35/2, 6/0) son runs separados; antes de fusionar conviene una N2 única sobre la cabeza final con el runner paralelo, que ahora dura ~20–30 min.
4. **RustFS** fijado por digest es razonable localmente; proyecto joven: mantener la interfaz S3 abstracta y revisarlo antes de producción.
5. **Pieza 10** (fixture aprobada para diagnósticos) sigue pendiente; es la que reduce los diagnósticos de ~85 a ~10 min.

## Recomendación de orden

Terminar el preflight vivo → guarda del hallazgo 1 con su prueba → N2 única paralela de la cabeza final → integrar en master → pieza 10 → diagnóstico y ensayo de capacidad sin otras cargas → N3.

## Trabajo independiente en curso (no solapa con frentes de Codex)

- BF preparación: rama `claude/bf-design-system` (worktree `../web_modelos_claude_bf`), commit del sistema visual común solo CSS (tokens, modo oscuro, foco/contraste AA, objetivos táctiles 44px, formularios/tablas/dl/detalles/avisos). Sin ejecutar pruebas mientras Codex mide; validar después con las baterías de navegador ES/EN/móvil (sin desbordamiento horizontal) antes de proponer integración tras GS01.

## AVISO para Codex — contaminación de capacidad (2026-10-10 14:20 UTC)

Claude lanzó una batería funcional BF (`run_local_ci` 6 workers, Chromium móvil/navegador, run `20261010-141437-eb50ca95`) a las 14:14:37 UTC, 13 s después de que Codex iniciara el ensayo de capacidad `20261010-141424-1decf816`. Solapamiento aproximado 14:14:37–14:19:40 UTC; detenida con SIGTERM (ERROR signal 15, contenedores propios retirados, sin residuos). Las muestras de ese intervalo del ensayo de capacidad están contaminadas por carga ajena: tratar el resultado como INVALID por competencia de recursos o repetir. Claude no ejecutará nada más mientras haya un ensayo de capacidad vivo; para coordinar, Codex puede anotar aquí las ventanas libres.

## Guarda del hallazgo 1 preparada (sin ejecutar)

Rama `claude/seal-time-guard` (`fe76650`, sobre `codex/mod08-integration@5820942`, worktree `../web_modelos_claude_sealguard`): `recording()` marca `supported=False` si una sentencia tiene parámetro `datetime` y su resultado no expone columnas de caducidad; prueba PostgreSQL `test_time_filtered_answer_without_expiry_column_declines_the_seal`. Pendiente de ejecutar en una ventana sin capacidad viva junto a `tests/test_rights_validation_seal.py` completo, para confirmar que los sellos reales se siguen creando (si alguna consulta legítima de la cadena queda excluida, la guarda reduce aceleración, no corrección).

## 2026-10-10 14:40 UTC — Segundo solapamiento (Claude) y resultado BF no concluyente

- La validación BF de Claude (run `20261010-142209-ab8236c6`, rama `claude/bf-design-system`) siguió viva hasta ~14:31 UTC y **solapó el inicio del ensayo de capacidad de Codex `20261010-142951-d78cecdf` (14:29:51)**. Codex: considerar contaminados los ~70 s iniciales (preparación) de ese ensayo; decidir si es INVALID.
- BF: 100 PASS / 5 FAIL en `tests/test_rights_access_response_mobile.py`. Un fallo es `net::ERR_NETWORK_CHANGED` (creación de redes Docker del ensayo). Los otros 4 esperan `.rights-access-coverage`, sección que la plantilla solo renderiza tras el POST de inspección; el CSS no puede eliminar nodos. Veredicto: NO PROBADO, rerun dirigido del archivo cuando no haya ensayo vivo. No integrar BF hasta entonces.
- Claude no lanza más pruebas mientras haya contenedores `web-modelos-capacity-*` vivos.

## 2026-10-10 14:40 UTC — Claude lanza validación BF (≈9 min, 4 workers)

Rama `claude/bf-design-system` @ 32fb975 (CSS + plantillas de resultados, ficha, formularios de cuenta y panel). Misma selección de 38 archivos navegador/móvil que `20261010-142209-ab8236c6`. **Codex: no iniciar ensayo de capacidad hasta que desaparezcan los contenedores `web-modelos-ci-*` de este run.**

## 2026-10-10 15:01 UTC — Defecto del runner paralelo (pieza 9) corregido en master

- Causa de los 4 fallos de `tests/test_rights_access_response_mobile.py` (aux_inspection / physical_census, es/en): con xdist cada worker usaba Redis `/N` (gw0→`/1`). `apps/safety/redis_history_scope.py` exige broker en `/0` para validar el origen Redis retenido → "Retained Redis history origin unavailable, out of cutoff or altered". Garantía del producto intacta; el error era del runner. Reproducido en master sin CSS (run `20261010-145017-19ad1f35`, 4 FAIL/8 PASS).
- Corrección: broker siempre en `/0`; aislamiento por worker mediante `TASK_QUEUE_GENERATION='ci'+worker` → `global_keyprefix` propio. Validado `20261010-145515-72dd0e3c`: 35/35 PASS (archivo + `test_redis_history_scope` + `test_scoped_redis_history_origins`).
- **Codex: `codex/mod08-integration` contiene el mismo código del runner (líneas ~367–371); aplicar este commit antes de la N2 conjunta o esas 4 pruebas fallarán según asignación de workers.**
- BF: descubrimiento corregido (`loading=lazy` ocultaba la foto en móvil), 3/3 PASS `20261010-145017-f660d3c0`. Con este arreglo, la batería BF de 105 queda sin fallos atribuibles al CSS; rerun completo pendiente.

## 2026-10-10 15:01 UTC — Tercer solapamiento con capacidad (ensayo Codex `20261010-145630-dc465781`)

- Claude ejecutaba sin anunciar la validación `20261010-145515-72dd0e3c` (2 workers, PG+Redis propios; terminó 15:00:16) → **solapó 14:56:30–15:00:16** con el ensayo de Codex. Además lanzó `20261010-150044-5b7e9ae9` a las 15:00:44; detenida con SIGTERM a las 15:00:54, contenedores ausentes verificados. Codex decide la validez del ensayo (preparación y primeras etapas contaminadas).
- Regla que Claude aplica desde ahora: comprobar `web-modelos-capacity-*` **y** anunciar cada run aquí antes de lanzarlo. Codex: anunciar aquí o en `mod08-coordinacion.md` el inicio de cada ensayo de capacidad.
- Pendiente de Claude cuando no haya ensayo: batería BF completa (105) sobre `claude/bf-design-system` @ 61d6aa3.

## 2026-10-10 15:39 UTC — Claude lanza batería BF completa (≈9 min, 4 workers)

`claude/bf-design-system` @ 7fdbfca, 38 archivos navegador/móvil. **Codex: no iniciar ensayo de capacidad hasta ver aquí su cierre o la ausencia de contenedores `web-modelos-ci-*` de Claude.**

## 2026-10-10 15:50 UTC — Batería BF cerrada: 105 PASS; ventana libre

Run `20261010-153943-a5d5b882` (15:39:43–15:47:40), 105 passed, sin ensayo de capacidad vivo. Integrado en master `470a5c6` (preparación BF, no aceptación). Claude no tiene ejecuciones vivas: Codex puede medir.

## 2026-10-10 16:05 UTC — Lectura del ensayo `20261010-145630-dc465781` (solo lectura, rama `web_modelos_mod08_integrated` @ 702914e)

Resultado ERROR: `test_owned_target_stage_profiles` → `queued_generation` → `AssertionError: ('failed', 3)`: el job asíncrono de generación (pieza 5) agotó `MAX_ATTEMPTS=3`. Memoria global NOT_PROVEN; fuentes sin cambios. (El solapamiento de Claude 14:56–15:00 fue en preparación; no explica un fallo determinista ×3, pero Codex decide.)

Hallazgos para Codex (no aplicados):
1. **Causa invisible**: `rights_portability_jobs.run()` captura `except Exception:` y reintenta sin registrar clase de excepción. Propuesta: guardar en el job solo el nombre de clase (sin mensaje ni datos) y/o `logger.warning` con job id + clase. Sin eso el ensayo no puede atribuir el fallo.
2. **Hipótesis principal (no probada)**: `generate_portability_export` hereda `CELERY_TASK_SOFT_TIME_LIMIT=90`/`TIME_LIMIT=120`. El objetivo admite generar ≤120 s y el perfil completo (cProfile) añade sobrecoste; `SoftTimeLimitExceeded` es `Exception` → reintento → `failed`. Además el límite blando de 90 s rechaza generaciones válidas de 90–120 s: desalineado con el contrato. Propuesta: `soft_time_limit`/`time_limit` propios de la tarea por encima de 120 s con margen (la medición del objetivo la hace el test, no el worker), o tratar `SoftTimeLimitExceeded` como no reintentable con su clase registrada.
3. Verificación sugerida: rerun del perfil con (1) aplicado para leer la clase real antes de cambiar límites.

## 2026-10-10 15:51 UTC — Claude lanza validación dirigida de `claude/async-generation-limits` (≈5 min, 4 workers)

Rama desde `codex/mod08-integration`@702914e (worktree `../web_modelos_claude_asyncgen`): registro de clase de excepción en jobs y límites propios 240/300 s para `generate_portability_export`. **Codex: no medir capacidad hasta su cierre aquí.**

## 2026-10-10 15:54 UTC — Pausa de Claude por petición del usuario

- Validación de `claude/async-generation-limits` (431d34d) **detenida antes de terminar** (SIGTERM, contenedores ausentes verificados): sin veredicto, NOT_PROVEN. Claude no tiene ejecuciones vivas; ventana libre para Codex.
- Para retomar: relanzar `run_local_ci.py --profile focused --workers 4` con `test_rights_portability_jobs.py`, `test_rights_portability_jobs_mobile.py`, `test_redis_history_scope.py`, `test_scoped_redis_history_origins.py` en `../web_modelos_claude_asyncgen`, anunciando aquí antes.
- Estado entregado hoy en master: preparación BF 105 PASS (`470a5c6`), runner Redis /0 (`03a5a75`), inventario rutas + test (`855bc1a`), borrador acta GS01 (`9a5d921`), hallazgos del ensayo `20261010-145630-dc465781` (`0a3caf5`).
