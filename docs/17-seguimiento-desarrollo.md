# Seguimiento de ejecución del contrato

**Estado posterior vigente, 2026-10-12 /MOD-09:** el usuario acepta provisionalmente
el rendimiento actual MOD08 como suficiente ymejorable, yordena continuar el
resto del contrato. [Decisión contractual](16-contrato-ejecucion-desarrollo.md#mod-09--aceptación-provisional-de-rendimiento-mod-08-2026-10-12),
[medida y límites](evidencias/mod08-lectura-fresca-medicion-20261012.md).
Código c92fe64: preflight/probe pasan; measure conserva FAIL de6p95, sin perfiles,
fuentes/cuerpos/concurrencia/recursos ylimpieza verificados. No aceptación global/N3.
El diagnóstico posterior se interrumpió por la nueva prioridad yse conserva
ERROR/1FAIL, limpio, sin editar fuentes. Todos los runners cerrados.
Próxima acción única: consolidar escenarios ymatriz deCR09 sobre la versión común,
identificar selecciones necesarias de N3 yejecutarlas en CI propio sin reabrir por
rutina componentes aceptados. Después CR10→GS01→BF/BB→C. La perfección deestos
tiempos queda como deuda no bloqueante. El historial inferior conserva sus cortes.


**MOD-08 catálogo runtime verificado (18:50 UTC):** eef4368 agrupa comprobaciones frescas26→9consultas por llamada, sin cachear confianza ni cambiar orden de fases, triggers, permisos o validación de cadena. N2 aislada18460370PASS0skips219,061s, PG17/Redis7.4/S3 reales, fuentes iguales y retirada independiente verificada; incluye LOGIN real,9/18consultas, cambios ACL/owners/triggers entre llamadas y dentro de la fase relevante, más cadena/sello enforced. [Evidencia](evidencias/mod08-catalogo-runtime-20261010.json), [originales](evidencias/mod08-catalogo-runtime-20261010.tar.gz). Continúa nueva captura y perfil con código congelado; no mejora temporal, capacidad/N3 ni CR09 aceptados.

**MOD-08 perfil real posterior a SQL y correctivas de entrega (18:46 UTC):** master58c67b8 integra las optimizaciones SQL. Captura174156 completa las1509páginas; reuso182155 devuelve HIT_DIAGNOSTIC_REUSED_PREPARATION en controlador nuevo y PROFILE_DIAGNOSTIC_NOT_CAPACITY/1PASS. Generación real1intento33,160s, cierre11,525s; descargas JSON3muestras p95 23,539s y binarias8muestras p95 24,374s, superiores al objetivo5s. Comparación parcial de123lotes equivalentes sin perfilador: p95 5,087→4,251s (16,418%); SQL755→515 (31,788%). Ambas ejecuciones conservan fuentes y retiran recursos propios; no aceptación capacidad/N3/CR09 ni p95 de población completa.

Correctivas locales b23cde3/4354109: SQL textual seguro exclusivamente para las7familias de evidencia permite crear/reproducir un sello enforced; Composed arbitrario sigue declinándolo. La autorización del proxy usa el scope existente para validar una vez por operación, nunca entre peticiones; conserva autoridad/grants/expiración/lecturas físicas. N2 aislada51PASS223,290s y conjunta100PASS248,122s, cero skips, PG/Redis/S3 reales, fuentes iguales y retirada verificada independientemente. [Evidencia](evidencias/mod08-perfil-entrega-y-sellos-20261010.json), [originales sin baseline privado](evidencias/mod08-perfil-entrega-y-sellos-20261010.tar.gz). Pendiente N2 de agrupación de catálogo runtime26→9 y nueva medición con código final congelado; mejora temporal de estas correctivas todavía no acreditada.


**MOD-08 optimizaciones SQL verificadas e integración local (17:39 UTC):** `20261010-173322-af68c7fc`, HEAD2bd47fa,16archivos/140PASS/0fallos/0skips303,75s, PostgreSQL17/Redis7.4 reales,3workers/snapshots; fuentes iguales y retirada verificadas. Evidencias de imágenes frescas por página: DISTINCT ON para pares exactos, newest corrupt sin fallback, firma por imagen. Metadatos:3consultas scoped por llamada, Blob→Photo ordenados y mapping postwait; lectura física/SHA por imagen, auditoría posterior y rollback intactos. Perfil limpio anterior `20261010-170451-74183205` interrumpido intencionalmente para corregir:125muestras de lote, p95 parcial5,0865s; SQL755 en traza de4páginas, nunca capacidad ni mejora medida. N2 inicial72PASS y76PASS/1FAIL preservadas; fallo del hook corregido conservando frontera auditada y assert1lectura. [Evidencia y límites](evidencias/mod08-sql-bulk-y-perfil-20261010.json), [originales](evidencias/mod08-sql-bulk-y-perfil-20261010.tar.gz). Siguiente: integrar localmente y medir requests del código congelado con población/límites originales; no capacidad/N3/CR09 aceptado.

**Propuesta futura CC-05 registrada por petición del usuario:** [índice de similitud de fotos](97-propuesta-indice-similitud-fotos-cc05.md), pendiente de ponderación al abordar procesamiento de medios. Compara recuperación exacta, BK-tree, FAISS binario, pgvector y LSH; exige preservar rotaciones/recortes, confirmación visual, guards y supresión. No dependencia elegida, implementación ni mejora acreditada; separado de esta integración.

**MOD-08 N2 conjunta final correctiva:** `20261010-165711-aa25419f`, HEADb55c114,15archivos/162PASS/0skips286,84s; PostgreSQL17/Redis7.4 reales,3workers/snapshots, fuentes iguales. Aviso de teardown de base por1conexión todavía abierta; el runner verificó por inspect la ausencia final de todo su PG/Redis, sin tocar servicios normales. Se incorpora además el último registro documental de pausa Claude e871f89 sin cambiar apps/config/scripts/tests verificados. [Resultado y límites](evidencias/mod08-conjunta-final-n2-20261010.json), [originales](evidencias/mod08-conjunta-final-n2-20261010.tar.gz). Autoriza integración técnica local de las correctivas; no demuestra capacidad/N3 ni acepta CR09. Siguiente: captura real de expediente1500/16MiB/64MiB, sólo diagnóstico, con4CPU/8GiB/20GiB y objetivo120s intacto, sin otras cargas.

**MOD-08 generación pequeña real y baseline corregidos (16:56 UTC):** `20261010-163801-22ff8d45` READY_NOT_CAPACITY/1PASS72,269s; job succeeded en1intento, encolado→disponible4,009s; imagen4.300.958bytes AEAD/SHA/S3, binding, Caddy303→GETEOF/replay404 y Beat/workerpurge verificados. Fuenteigual/retirada verificada/cota memoria1.226.350.592bytes, sin objetivos modificados. La corrección SQL compuesto resuelve el fallo observado; no acredita el expediente1500. Baseline `20261010-165345-8716bad4`22PASS/0skips91,79s (1test PG/media/RustFS con positivo/adversariales y21guards puros); preserva originales/LOGINreal/TTL, rechaza deriva y limpia scratch, falla cerrado si limpieza no se verifica. Negativos anteriores archivados: eventos FK pendientes, multiplicidad de settings, inyección recursiva de copia e import inicial. [Evidencia](evidencias/mod08-generacion-real-y-baseline-n2-20261010.json), [originales](evidencias/mod08-generacion-real-y-baseline-n2-20261010.tar.gz). Próximo: N2 conjunta finita, integración local y captura/perfil grande limpio. No capacidad/N3/CR09 aceptado.

**MOD-08 causa real localizada y correctiva SQL (16:37 UTC):** preflight `20261010-162302-b2816afa` ERROR/1FAIL, con dos registros `rights_validation_seal.wrapper:175`/AttributeError y último estado running/intento3 sin exportación. El wrapper asumía SQL textual; la cadena de evidencia usa SQL compuesto del driver. `4e7fc34` conserva consulta/parámetros intactos y descarta el sello para esa consulta, manteniendo validación completa. N2 anterior48PASS; correctiva conjunta48PASS/1FAIL/0skips349,199s, único fallo en restauración diagnóstica PostgreSQL: ObjectInUse por eventos pendientes antes de reactivar trigger. Todas las fuentes iguales y retiradas verificadas. [Evidencia](evidencias/mod08-sql-composable-diagnostico-20261010.json), [originales](evidencias/mod08-sql-composable-diagnostico-20261010.tar.gz). Próximo: repetir generación pequeña real sin baseline; reparar/verificar baseline por separado. Sin capacidad/N3 ni aceptación de fase.

**MOD-08 prueba pequeña terminal negativa:** `20261010-160608-d368dcc8`, HEAD02a6117,ERROR por watchdog180s sinJUnit; fuenteigual/retirada verificada. Observación parcial del log vivo revela2intentos conAttributeError, sin mensaje privado; no identifica instrucción ni demuestra timeout del worker. El watchdog no contemplaba preparación/startup además de180sdeobservación; correctiva360s sólo diagnóstica, objetivo120s intacto. Se añade al registro de fallos sólo módulo/función/línea final, sin traceback/mensaje/locals. [Negativo y límites](evidencias/mod08-async-probe-negativo-20261010.json), [originales](evidencias/mod08-async-probe-negativo-20261010.tar.gz). Próximo: N2 guards/observabilidad/baseline y reproducción pequeña clasificada; no readiness/PASS ni capacidad.

**MOD-08 preflight correctivo de generación pequeña reservado:** HEAD7c73c7e más este registro; un caso sintético independiente, WebP lossless real≥4MiB, evaluación/selección/cobertura aprobadas mediante servicios y todas sus lecturas independientes. Mismos Gunicorn2/Celeryprefork2/Beat/LOGINnoadministrador/S3/Caddy reales y4CPU/8GiB/20GiB/swap0; observación finita180s, sin fixture1500/p95 ni aceptación120s. Encolado TCP→estado durable, objetos AEAD/SHA y vínculo con bytes actuales; además conserva todos los guards de readiness anteriores. Ninguna carga competidora. Criterio READY_NOT_CAPACITY sólo si pasa el gate único y fuente/retirada/cuotas reales; cualquier error conserva clase minimizada y rollback para atribuir antes de repetir40min. Agentes sólo edits offline en sus worktrees hasta terminal.

**MOD-08 N2 correctiva terminal:** `20261010-155905-1390e488`, HEADc1b5973,114PASS/1FAIL/0skips248,25s; PG17/Redis7.4/Chromium reales propios, fuentes iguales/retirada verificada. Todos los casos funcionales jobs/sello/huella/lotes/bytesSHA/rollback/Redis pasan; único fallo: ruta nueva de estado ausente del inventario documental. Contrato corregido a POST302→job durable y GET200privado; inventario1PASS0,19s sin cambiar aplicación/esquema/pruebas. [Evidencia y límites](evidencias/mod08-correctiva-conjunta-n2-20261010.json), [originales](evidencias/mod08-correctiva-conjunta-n2-20261010.tar.gz). No115PASS simultáneos, N3 ni capacidad. Siguiente: completar/verificar baseline diagnóstico y prueba pequeña real de generación Celery+LOGINrestringido+S3 antes de repetir expediente grande. Causa del fallo original sigue pendiente de reproducción clasificada.

**MOD-08 N2 correctiva conjunta reservada, 2026-10-10:** rama integrada con master6437a74 preservado y correctivas431d34d/fe76650/db98167/cdd5ca5 revisadas por Codex; fuente6119d7c más este registro. Selección finita12archivos: jobs/jobs_mobile, validation_seal/source_fingerprint, coverage_batch/batch_projection/coverage_inspection/coverage_batch_validation, redis_history_scope/scoped_redis_history_origins, capacity_coverage_batches y route_inventory. PG17/Redis7.4 propios,3workers,snapshots,timeout2400s; ninguna carga competidora. Criterio: selección PASS sin skips necesarios, fuente congelada, JUnit y retirada verificada. Cubre errores minimizados/límites sin confundirlos con causa del perfil anterior; proyección pura conserva4evidencias/bytesSHA/guards y rollback tardío. No capacidad ni N3. Ejecutor Claude anterior detenido por usuario:20261010-155106-950fc30a ERROR signal15, sinXMLterminal, limpieza y fuentes iguales; no PASS ni reutilización de puntos verdes parciales.

**MOD-08 perfil completo terminal negativo:** `20261010-145630-dc465781`, HEAD702914e,1FAIL2414,23s. La generación termina `failed` con3intentos en253,61s; excepción original no registrada, límite Celery90s es hipótesis pendiente de confirmar. Fuente igual y recursos propios retirados, memoria global NOT_PROVEN. Claude notificó dos cargas solapadas14:56–15:00: este ensayo y los dos perfiles anteriores con solapes no acreditan rendimiento, mejora ni p95. Igualdad exacta de huella vieja/nueva sí observada en un mismo snapshot PG restringido; trazas completas conservadas. [Negativo y límites](evidencias/mod08-perfil-generacion-negativo-20261010.json), [originales](evidencias/mod08-perfil-generacion-negativo-20261010.tar.gz). Codex mantiene dirección: revisar clase de error y tiempos de worker, comprobar correctivas PG, integrar lotes puros y baseline diagnóstico antes de otro ensayo sin carga competidora. No aceptación MOD-08/CR09/N3.

**MOD-08 consulta de huella municipal N2 PASS:** `20261010-144427-945382a1`, HEADd5356ab,21PASS/0FAIL/0skips106,88s. Semijoin por IDs UNION conserva conjunto exacto id/xmin:ctid y huella/count completos frente al SQL anterior. Duplicados, directo/desplazamiento, NULL, ajenos/compartidos, sin listing/cuenta y mutaciones/derivas tardías cubiertos; rollback intacto. Fuentes congeladas y PG/Redis propios retirados. [Evidencia](evidencias/mod08-source-fingerprint-n2-20261010.json), [originales](evidencias/mod08-source-fingerprint-n2-20261010.tar.gz). Comparación de tiempos y EXPLAIN real pendiente: nuevo helper sólo diagnóstico completo verificado, rol LOGIN restringido/no propietario, mismo snapshot REPEATABLE READ READ ONLY,4 muestras alternadas y4 planes completos, identidad/secretos minimizados.18 guards puros de flags/config/proxy pasan aparte; no sustituyen SQL ni p95.

**MOD-08 diagnóstico parcial detenido por operador:** `20261010-142951-d78cecdf`, HEAD55a3da9. Supera el fallo del instrumento; observación de dos trazas WSGI sitúa7,87/8,28s en dos huellas de fuente por request, frente a copia0,76/0,67s. Se identifica consulta de municipios correlacionada candidata a reescritura equivalente. SIGINT sólo al pytest propio para corregir y volver a medir; JUnit0tests, no PASS ni p95. Las trazas completas efímeras no quedaron conservadas: los valores transcritos son observación, no perfil original retenido. Memoria/limpieza originales sí conservadas; fuentes iguales y recursos propios ausentes. [Registro y límites](evidencias/mod08-perfil-parcial-20261010.json), [originales disponibles](evidencias/mod08-perfil-parcial-20261010.tar.gz). Nueva captura de interrupción la registra como test fallido y conserva métricas JUnit. Próximo N2 PG de equivalencia/invalidación antes de perfil completo.

**MOD-08 primer perfil completo ERROR del instrumento:** `20261010-141424-1decf816`, HEAD5820942,1FAIL/0skips264,27s. El primer guardado TCP200 tarda9,63s; `sampled()` exige incorrectamente POST303→GET200 también para guardados porque todo cliente dispone de transporte proxy. Se detiene antes de revisar/generar/descargar; no se declara rendimiento ni aceptación. Fuentes intactas, limpieza propia verificada, swap0/OOM0. Correctiva: exigir proxy sólo en descargas y conservar todos sus controles. [Registro](evidencias/mod08-perfil-negativo-20261010.json), [originales](evidencias/mod08-perfil-negativo-20261010.tar.gz).

**MOD-08 preflight real READY_NOT_CAPACITY:** `20261010-140801-58565769`,1PASS/0FAIL/0skips61,88s de gate. PostgreSQL/S3 privado/Caddy/LOGIN restringido/Gunicorn/Celery prefork2/Beat reales. AEAD/read/purge, POST303→GETEOF+SHA256, replay404 y purga automática Beat→broker→worker comprobados; montajes appRW/CaddyRO y volumen512MiB contado una vez. Cota conservadora RAM1.169.072.128bytes, todos los roles swap0/OOM0; techo de almacenamiento4.865.392.640bytes, cuotas totales4CPU/8GiB, procesos appRSS<1GiB. Fuente igual y contenedores/volumen/red retirados. [Evidencia](evidencias/mod08-preflight-real-20261010.json), [originales y negativos](evidencias/mod08-preflight-real-20261010.tar.gz). Dos intentos previos INVALID por alias de imagen inexistente y capability de Caddy; resueltos con digest probado y copia binaria idéntica sin atributo en tmpfs limitado, sin conceder privilegios. No p95, población objetivo ni aceptación de capacidad. Próximo perfil diagnóstico de un caso1500/16MiB/64MiB, misma topología/budget, sin pruebas concurrentes; incluye espera de cola hasta exportación durable.

**MOD-08 integración funcional con correctivas dirigidas:** batería604 casos `20261010-133425-2d10e5dc`:590PASS/14FAIL/0skips,1025,82s; snapshot/credenciales/rol/domain ya pasan. Doce fallos buscaban campos del formulario en la nueva pantalla de job completado; dos contaban mal las copias/huellas del replay alternativo. Correctiva `20261010-135235-80c463e7`:35PASS/2FAIL/0skips273,38s; todos los móviles ES/EN con/sin JS, exportación, descargas y revocación completos pasan. Los dos restantes prueban cuatro huellas porque hay dos contextos, no dos; último run `20261010-135818-213b34e3`:6PASS/0FAIL/0skips71,64s. Código/esquema de apps/config idénticos entre los tres, comprobados por huellas; cambios sólo de pruebas/documentación. [Evidencia y límites](evidencias/mod08-integracion-n2-correctivas-20261010.json), [originales](evidencias/mod08-integracion-n2-correctivas-20261010.tar.gz). PG/Redis propios retirados y fuentes intactas. Ningún caso fallido pendiente de esta selección; no se presenta como604PASS simultáneos ni N3. Próximo preflight finito real S3/Caddy/Celery/Beat/LOGIN restringido,4CPU/8GiB/20GiB/swap0, sin población objetivo ni p95; después perfil/capacidad. No carga mientras pruebas activas.

**MOD-08 integración conjunta — negativo conservado:** `20261010-131345-824b6f67`, 563 PASS/39 FAIL/1 diagnóstico omitido, 1011,76 s; PostgreSQL17/Redis7.4 propios, fuente `5ca954b` intacta y retirada verificada. [Diagnóstico](evidencias/mod08-integracion-n2-negativa-20261010.json), [originales](evidencias/mod08-integracion-n2-negativa-20261010.tar.gz). Fallos agrupados en snapshot de credenciales/conexiones/permisos, pruebas de huella final y selectores móviles; correctivas preservan garantías. Primera colección falló por IDs aleatorios de cifrado entre workers y se corrigió con IDs explícitos, sin cambiar los bytes aleatorios. No aceptación conjunta/N3/capacidad. Próxima selección: mismos archivos funcionales, excluyendo explícitamente `test_capacity_source_profile.py`, diagnóstico exclusivo del controlador de capacidad. No ejecutar carga mientras las pruebas estén activas.

**MOD-08 pieza12 N2 PASS:** run `20261010-124631-32e33970`,20PASS0skips157,921s, PostgreSQL17/Redis7.4 y Chromium ES/EN reales; fuentes intactas/retirada verificadas. [Evidencia](evidencias/mod08-coverage-batch-n2-20261010.json). Primer negativo14PASS6FAIL conservado: fixture sólo tenía una revisión y selector contaba campos en vez de páginas; correctiva usa3revisiones y secciones de página. Límite1–4/idempotencia/conflicto/revisor independiente/rollback posterior y privacidad GET/CSRF/móvil verificados. Pendiente integración conjunta y capacidad.

**MOD-08 pieza12 — reserva N2:** lote de cobertura1–4 páginas con lecturas independientes, acción raíz idempotente, rollback atómico y presentación ES/EN móvil. Se ejecutan nuevo archivo batch y regresiones domain/HTTP/mobile actuales, PostgreSQL17/Redis7.4 propios,2workers y snapshots sólo baseline; fuentes congeladas hasta terminal. No acredita capacidad ni aprobación de revisión.
**MOD-08 piezas3/4 N2 dirigida PASS:** run `20261010-124250-bb8366fc`,24PASS/0FAIL/0ERROR/0SKIP241,787s; fuentes congeladas y PG/Redis retirados. [Evidencia](evidencias/mod08-source-seal-n2-20261010.json). Captura resultados SHA256 realmente consumidos, orden preservado, xmin+ctid cubre cambios misma transacción; digest del caller tomado antes de cargar relaciones internas. Generación/fresh delivery pueden sellarse por vistas distintas; valid_until y regla/config siguen invalidando. Pendiente N2 conjunta y objetos externos S3 en guard heldseal; no medición de capacidad.

Actualizado: 2026-10-09. Fuente contractual: [contrato16](16-contrato-ejecucion-desarrollo.md). Este documento mantiene el estado y la única cola de ejecución; evidencias y condiciones de cierre se enlazan desde él.

## Estado vigente para reanudar

**N1 correctiva3/4 reservada:** `claude/source-version` `5131d03`; archivos completos `test_rights_source_fingerprint.py` y `test_rights_validation_seal.py` (completitud/mutaciones25familias, misma transacción, fresh caller, orden, captura real, parámetros, expiración/configuración y resultado equivalente a validación completa). PG17/Redis7.4/nativos propios,2workers,timeout1800s,detached/fuentes congeladas. Reproducciones anteriores: dos defectos confirmados y un error JSONB incidental; repetición de snapshot tras soporteJSONB confirmó aceptación incorrecta. Corrección usa xmin+ctid, recarga caller ante drift y SHA256 de filas anotadas en el SELECT realmente consumido, con orden preservado/cursor equivalente; expiry y configuración viva, fallback ante inputs no soportados. Salida: todosPASS,0skips,huellas/cleanup; luego N2 conjunta sin afirmar capacidad.

**N1 reproducción3/4 reservada por Codex:** rama `claude/source-version`, `dcfd0c7`, tres nodos nuevos: dos UPDATE dentro de una transacción (identidad de fila), orden consumido por SELECT y cambio entre lectura validada/reproducción posterior. PG17/Redis7.4 propios, runner detached focused/1worker/nativos, timeout1800s. Fuentes congeladas hasta terminal, mantener fallos como reproducción; no aceptación. Salida: confirmar o refutar hipótesis, JUnit/huellas/limpieza; después corregir únicamente garantías demostradas y ejecutar los archivos afectados.

**Relevo vigente a Codex, 2026-10-10**, por petición posterior del usuario de continuar desde los frentes paralelos que dejó Claude sin tokens. Codex retoma dirección/ejecución local e integración, con agentes nativos escritores aislados y propiedad registrada en `.ai/tasks/mod08-coordinacion.md`; no invoca el adaptador Claude V1 ni reinicia consumo. Las menciones de pausa exclusiva y dirección Claude inferiores son antecedentes. Criterios/objetivos y prohibiciones externos intactos. Base `209f014`, pruebas paralelas ya integradas: 414 PASS/0 errores/fallos/skips, 1109,918s JUnit sobre `9cb8214`; no capacidad ni N3. Continuación: verificar/corregir huella3 y sello4 con reproducciones PG y fuentes congeladas; completar piezas5–10 en worktrees aislados, N2 por cambio y conjunta antes de integrar; después inmutabilidad/lotes y ensayo de capacidad sin carga competidora. Registro de hipótesis, propiedad y condiciones de salida en coordinación; seguimiento de ejecuciones se añadirá aquí antes de lanzar.

**Contrato v1.7, relevo directo MOD-07 vigente por aclaración posterior del usuario.** Claude es agente principal de la entrega local restante, autorizado a leer/editar, ejecutar/verificar, corregir e integrar con commits locales y aceptación técnica documentada hasta CR09→CR10→GS01→BF/BB→C. No detenerse al entregar una propuesta ni esperar aplicación de Codex. Goal Codex sigue pausado. [Reglas MOD-07](16-contrato-ejecucion-desarrollo.md#mod-07--relevo-directo-a-claude-autorización-vigente), [nuevo prompt](prompt-relevo-claude-20261009.md). Las prohibiciones tool-free y condición de parada del prompt anterior quedan como historia, no instrucciones para Claude principal.

Primera acción: leer documentos y revisar propuesta externa P1–P8 antes de decidir cambios; no asumir verificación kernel, storage o PASS desde inspección. Aplicar únicamente correcciones justificadas, N1/N2 propio real, y continuar con p95/etapas pendientes/censo y N3 según contrato, sin aprobación por hito. El JSON externo y revisión manual no añaden PASS ni aceptación de fase. Consumo: ocho invocaciones históricas conservadas; revisión externa con lectura reportada, fuera de scripts/claude-task, registrada separadamente en el plan.

### Controlador de capacidad validado (Claude principal, MOD-07)

Revisión crítica de P1–P8 y del prototipo: el lanzador no podía ejecutarse (tmpfs `noexec` para los wrappers); se corrige y se sustituye la escritura en directorio por un único archivo de artefactos limitado por RLIMIT_FSIZE del kernel, porque el XFS del host está montado `noquota`. PG/Redis sin root ni capacidades, logs de servidor en su tmpfs y recogidos, sondas reales EROFS/ENOSPC/EFBIG por rol, tmpfs contado una vez por dispositivo, ausencia por `inspect` exacto y etiqueta de run, timeouts con salida parcial y cota de memoria >6GiB como NOT_PROVEN. N2 propio: dos negativos conservados, `20261009-224151-e7d44c80` **READY_NOT_CAPACITY** (cuotas4CPU/8GiB/swap0 leídas del kernel, techo de almacenamiento2,94GiB, memoria dentro de cota sin swap/OOM, limpieza e inventario Docker iguales) y control negativo fuera del lanzador. Fallo GC 2/3 diagnosticado por hipótesis finita y reproducción determinista: `gc.collect(2)` síncrono en el bucle del generador; corregida la prueba, 14PASS. Ruff del árbol PASS. [Evidencia](evidencias/capacidad-controlador-n2-20261009.json). No acredita carga, p95 ni N3. Siguiente: reensayo del recorrido binario objetivo bajo este controlador.

**Ensayo reservado — entrega completa objetivo bajo controlador validado.** Fuentes: commit que contiene este registro (driver `tests/capacity_delivery_flow.py` y consumidor `tests/test_capacity_delivery_complete.py`, antes experimentales, ahora revisados: las violaciones de umbral válidas se registran y la ejecución continúa para medir todas las etapas; resultado FAIL si existe alguna). Comando `uv run python scripts/run_capacity_environment.py --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --delivery-complete`; recursos PG1,5CPU/3GiB, app2,25/4,5GiB, Redis0,2/384MiB, controlador0,05/128MiB, swap0; tmpfs PG2GiB/app1GiB; timeouts pytest9000s, lanzador11500s. Casos: dos expedientes simultáneos de1500revisiones/16MiB/64MiB; ≥20muestras nuevas por etapa/caso, nearest-rank; umbrales del JSON de objetivos sin cambios. Salida: DELIVERY_STAGES_PASS o FAIL/INVALID/NOT_PROVEN con evidencia, fuentes iguales y retirada verificada.

**Terminal `20261009-224749-d7b20ad4`: FAIL válido de etapas** (`81b48e4`, fuentes iguales, retirada por inspect/etiqueta verificada; launcher reconstruido porque su proceso host terminó con la sesión). Cumplen guardado binario p953,59/3,69s, preparaciones, decisión de selección, generación66,3/64,7s, JSON16.782.538bytes (+0,03%), RSS proceso≤824MiB, cota global de memoria3,13GiB sin swap/OOM y techo de almacenamiento4,0GiB. FAIL: lectura de selección p952,09/2,05s, inspección binaria2,76/2,79s, guardado de cobertura10,9/10,8s, lectura de cobertura3,87s (1.509páginas/caso), respuesta final/inspección/aprobación/cierre40–59s y descargas p95~31s. [Resultado](evidencias/capacidad-entrega-completa-20261009.json). Siguiente: perfil diagnóstico por etapa (rama `claude/cr09-capacity-perf`), hipótesis finita y correcciones conservando garantías.

**N2 de equivalencia reservado — origen compartido (rama `claude/cr09-capacity-perf`, commit `47a3b82`).** Hipótesis por perfil a escala: el guardado de página de cobertura ejecutaba `source_copy` 12 veces (8,4 de 14,9s perfilados); lecturas/inspecciones repetían copia y digest del origen de 17,3MB. Cambio: un único `inspection_source` por operación de página de cobertura, inspección de selección e inspección binaria, digest reutilizado y salida del contexto con comparación fresca en la transacción y autoridad revalidada después (precedente aceptado del guardado binario); HMAC invariantes fuera del bucle de1.509 páginas. Selección `focused` de32 archivos (cobertura, selección, binarios, exportación/cierre, carreras, HTTP/móvil/localización, origen compartido y conteo de lecturas), PG17/Redis7.4 propios y nativos, timeout7200s, fuentes congeladas. Salida: todos PASS, cero skips, fuentes iguales y retirada; después perfil diagnóstico y nuevo ensayo objetivo.

**Negativos conservados (2026-10-10).** N2 `20261010-013007-b2f3d6c5` **INVALID**: edité y comprometí `tests/test_portability_source_reads.py` del worktree mientras el run estaba vivo (violación de congelación de fuentes); se detuvo con SIGTERM y reveló un defecto del runner: sin manejador, salía con143 sin `result.json` ni retirada. Contenedores y temporal propios retirados por nombre/identificador exacto. Corregido `run_local_ci.py`: SIGTERM/SIGHUP siguen la ruta de limpieza y la ausencia se prueba con `docker container inspect` no encontrado, no con filtro vacío; control negativo `20261010-013316-0635f024` ERROR «signal 15», retirada verificada y sin residuos. N2 repetida con fuentes congeladas en `4c31c7d`.

**N2 `20261010-013223-1958814e` terminal (fuentes `4c31c7d`, iguales):284PASS/3FAIL/0skips en2.854s**, retirada verificada. Los3fallos (`mixed_fields`×2, `review[True]`) se reproducen idénticos en master sin estos cambios: preexistentes, no cubiertos por la N2 de63. Causa: la vista inspecciona siempre paginado y las pruebas reutilizaban la clave de una inspección de servicio sin página (conflicto de idempotencia409 correcto); pruebas corregidas con clave propia y réplica (`e2369b8`). Conteo de validaciones por operación a escala-independiente: cada etapa final y descarga repetía la validación completa de la exportación2–3 veces; corregido a una por operación y transacción (`2c3305e`), con cota de regresión. Siguiente N2 reservada (31archivos de exportación/cierre/respuesta/descargas acceso y portabilidad/retención/supresión/localización y las pruebas corregidas), PG17/Redis7.4/nativos, timeout7200s, fuentes congeladas en `2c3305e`.

**Continuidad de ejecutores (2026-10-10).** La N2 `20261010-023038-aade9d13` (`2c3305e`) quedó **incompleta** al cerrarse la sesión (~108 casos, sin `result.json`/XML): evidencia archivada, recursos propios retirados tras archivar. Sus dos F (`test_account_only_exports` portabilidad) se reproducen idénticos en la base `16a41f7`: preexistentes desde `1b03ddb`, prueba alineada (`3b708e9`, 4PASS). Corregida la continuidad: `run_detached.py` (sesión propia), `runner.json` durable + `--recover` (INTERRUPTED separado, hijo huérfano terminado, solo recursos declarados) y `--recover` del lanzador de capacidad (`launcher-recovered.json` distinto del original). Controles reales A–D PASS, más SIGTERM. Documentación válida en checkout limpio sin el archivo GraphQL sin versionar (conservado, nombrado sin enlace) ni `graphify-out`. [Evidencia](evidencias/continuidad-ejecutores-20261010.json). Siguiente: integrar la rama de rendimiento en master y N2 por lotes con ejecutor desacoplado.

**N2 correctiva unificada reservada.** Rama `claude/cr09-capacity-perf` rebasada sobre `b578d34`, fuentes congeladas en `40a30a8` (origen compartido, validación única por operación, pruebas alineadas). Selección `focused` de49archivos/414casos (unión de los dos lotes: selección, binarios, cobertura, exportación, cierre, respuesta, descargas acceso/portabilidad, retención/supresión, localización, conteo de validaciones), PG17/Redis7.4/nativos propios, timeout7200s por paso, lanzada con `run_detached.py`. Salida: todos PASS, cero skips, fuentes iguales, retirada verificada; después integración en master.

**N2 correctiva cerrada e integrada (master `57af4ff`).** Unificada `20261010-051659-670b042f`:413PASS/1FAIL/0skips (5.014s); el fallo era una aserción previa a la inspección paginada. Tras dos correcciones solo de prueba (decisión ligada a la última lectura, restauración de la lectura original, recuento de tres lecturas), repetición del único archivo afectado `20261010-064630-4b450291` 2PASS. Fallos preexistentes reproducidos en `16a41f7`. [Evidencia](evidencias/n2-origen-compartido-validacion-unica-20261010.json). Siguiente: diagnóstico del coste por validación de exportación (imágenes/transporte/cobertura) con perfil acotado antes de otro ensayo completo.

**Corrección de registro.** El commit `3a08e7c` incluyó por error (`git add docs`) la propuesta GraphQL sin versionar y de procedencia no confirmada. Retirada del índice en el commit siguiente con `git rm --cached`; el archivo local se conserva byte a byte y sigue fuera del contrato. Historia no reescrita.

**N2 reservada — equivalencias exactas en validación (`3c1ef66`).** Por el perfil completo de un caso (`20261010-064907-320e9495`): memo de `row_reference` por fila del origen compartido activo, un descifrado por acción en el bucle de páginas (orden de comprobaciones original), reutilización de compilación con argumentos idénticos y un descifrado por instantánea de imagen. Misma selección unificada de49archivos/414casos, PG17/Redis7.4/nativos, timeout7200s, `run_detached.py`, fuentes congeladas. Salida: todos PASS, cero skips, fuentes iguales y retirada.

**N2 de equivalencias exactas PASS e integrada.** `20261010-091912-0d3425cf`:414PASS/0FAIL/0skips (4.913,6s), fuentes iguales, retirada verificada; integrada en master (`4d5ef38`). [Evidencia](evidencias/n2-equivalencias-validacion-20261010.json). Siguiente: diagnóstico completo de un caso desacoplado para medir el efecto antes de decidir el sello de entrega.

**MOD-08 adoptado (2026-10-10).** Modernización técnica autorizada por el usuario: [contrato16 §MOD-08](16-contrato-ejecucion-desarrollo.md#mod-08--modernización-técnica-del-núcleo-autorizada-2026-10-10). Cola: (1) mejora 3 huella de versión de fila — implementada en `claude/source-version` (`4ea995e`), 12 PASS de completitud; (2) mejora 4 sello por reproducción de consultas — escrito, pruebas pendientes; (3) generación en Celery; (4) AEAD en flujo y objetos S3 propios; (5) orjson/BLAKE3; (6) pytest-xdist y plantillas de base; (7) evidencia inmutable con cadena de hashes y revisión por lotes, con actualización de contratos. Los objetivos de capacidad no cambian.

**GS01/BF preparación y CI paralelo (2026-10-10, Claude; dirección MOD-08 en Codex).** Inventario de rutas completo: 164 patrones documentados en contratos, exigido por `tests/test_route_inventory.py` (estático) y [contratos12](contratos/12-rutas-complementarias.md). [Borrador de acta GS01](96-acta-gs01-borrador.md): puerta **no superada** (CR09 integral, CR10 y cambios coordinados MOD-08 pendientes). Defecto del runner paralelo corregido (`03a5a75`): los workers xdist usaban Redis `/N` y la validación del origen Redis retenido exige `/0`; ahora comparten `/0` con prefijo propio. Validado `20261010-145515-72dd0e3c` 35 PASS; reproducción previa en master `20261010-145017-19ad1f35` 4 FAIL. BF preparación en `claude/bf-design-system` (sistema de tokens, resultados en cuadrícula, ficha con galería y panel de contacto, formularios de cuenta y panel agrupado; mismos datos, rutas y selectores). Batería navegador/móvil completa 105 PASS (`20261010-153943-a5d5b882`, sin ensayo vivo) e integrada en master `470a5c6` como preparación; no acepta BF ni GS01. Ningún solapamiento con ensayos se cuenta como medición válida ([registro](../.ai/tasks/mod08-revision-claude.md)).

**GraphQL descartado (2026-10-10).** Por decisión del usuario («nunca saldremos de navegador web») se elimina la propuesta local sin versionar `docs/propuesta-graphql-manual.md` (SHA-256 previo `b1d3cddb1263b6c0f07430198dce9a66c51c14fc872b475ac71de8a646f6173a`); nunca hubo código GraphQL. Las menciones históricas del relevo quedan como antecedente.

### Corte anterior de pausa y propuesta acotada

**Pausa y relevo solicitados el 2026-10-09.** El goal está **pausado** tras recoger los terminales y comprobar ausencia de contenedores/redes/temporales propios; no se inicia otro bloque del contrato ni se invoca a Claude. Este corte sustituye las instrucciones de ejecución inmediata que aparecen en los antecedentes inferiores. [Informe y continuación exacta](relevo-claude-20261009.md), [inventario completo y evidencia](evidencias/relevo-local-20261009.json), [prompt conforme al modelo vigente](prompt-relevo-claude-20261009.md).

Último N2 confirmado: `20261009-201631-db21c6aa`, **63 PASS/0 FAIL/0 ERROR/0 SKIP, 467,214s JUnit**; fuentes iguales, PostgreSQL/Redis/nativos reales propios, retirada contrastada y archivo de 1.020 fuentes verificado. No acredita p95, presupuesto global, N3 ni CR09 integral. El último p95 válido de revisión binaria sigue **2,372175/2,395124s > 2s**; no se repitió después de la correctiva funcional. Generación/cobertura/cierre/descargas del flujo grande y controlador/almacenamiento global siguen pendientes.

Continuación exacta, únicamente cuando se reanude el desarrollo autorizado: revisar el prototipo sin commit de controlador y el inventario del relevo, resolver su falta de ejecución nativa/contabilidad y el diagnóstico Ruff; validar controles efectivos completos sin tocar servicios normales antes de cualquier carga. A continuación comprobar el p95 binario sobre fuentes de la correctiva o diagnosticar por hipótesis finita, sin alterar objetivos. Las etapas posteriores del driver siguen NOT_PROVEN. El helper de artefactos tiene solo **8 PASS N1 puro, 0,147s JUnit**, no aceptación del controlador. La comprobación de limpieza del relevo dio **13 PASS/1 FAIL** en un observador GC temporal no modificado (dos peticiones emitidas frente a tres); resultado negativo conservado y causa no atribuida sin diagnóstico. No repetir ensayos ni avanzar mientras siga vigente esta pausa.

Gobernanza sin modificación: AI_ENGINEERING1.0.1 leído completo. V1 delegado sin herramientas, escritura, ejecución ni Git; **Claude propone, Codex aplica/verifica/integra/acepta**. El límite numérico de invocaciones está eliminado, no sus restricciones operativas. Un goal Claude que aplique directamente requiere autorización expresa para cambiar dirección/atribuciones y adoptar un procedimiento de escritor compatible; el texto de autorización propuesto está en el informe y no ha sido adoptado. Ocho invocaciones históricas preservadas; cero nuevas en este relevo.

Antecedente anterior a la pausa: goal autónomo activado el2026-10-09 por petición del usuario para seguir el contrato hasta completar la entrega técnica local: CR09 → CR10 → GS01 → BF/BB → C. Codex continúa elecciones ordinarias, correcciones y verificaciones sin confirmaciones por hito; se mantienen CI propio, PG real, datos sintéticos, evidencia y limpieza. El usuario eligió expresamente «Delegar los objetivos técnicos»: Codex debe fijarlos conforme a recursos locales disponibles y registrar población, límites, variantes y condición de salida antes de ensayar capacidad. No falta una aprobación rutinaria del usuario para esa definición; las cifras de la propuesta no se convierten en resultados ni en una promesa productiva. Continuar censo/identidad/cobertura y escenarios independientes. Su activación no aceptó fases ni autoriza publicación, contratación o gasto; requisitos reales de producción separados.

**Formulación contractual consolidada; CR09 técnico y fases posteriores abiertos.** Contrato vigente v1.6/MOD-06: entrega técnica local y preparación real de producción tienen criterios separados. La [matriz83](83-auditoria-pendientes-cr09.md) reclasifica las entradas del [acta residual](evidencias/residuales-locales-post-aceptacion0110.json); los bloqueos por proveedor, revisión jurídica, custodia o identidad de personas reales pertenecen a producción y no impiden probar sus mecanismos con fixtures sintéticos. El bloqueo global de la auditoría anterior queda como antecedente, sin alterar sus resultados ni marcar completados los requisitos locales restantes.

Saneamiento y CI propio entregados; Codex conserva arquitectura, integración y aceptación. La consolidación no ejecuta nuevas baterías/cargas, no acepta CR09/GS01/fases ni reabre lectura u otros componentes aceptados. Los objetivos de expedientes grandes han sido fijados por delegación; el ensayo y su aceptación siguen pendientes. Las pausas, reanudaciones y estados automáticos anteriores se consultan como historia; esta formulación documental no modifica por sí sola un goal automático.

Mantenimiento autorizado el 2026-10-09: retirar instrumental descartado sin consumidores actuales. Fuentes afectadas: `scripts/benchmark_call_profile.py`, `scripts/benchmark_local_monitor.py` y sus dos archivos de pruebas exclusivos; código de aplicación y esquema fuera del cambio. Verificación N1: referencias/imports, colección de pytest, pruebas de observadores que sí siguen en uso, Ruff, enlaces y diff. Sin PostgreSQL de integración ni cargas: se eliminan herramientas autónomas, no comportamiento persistente. Resultado: cuatro archivos y337líneas retirados; cero referencias en código activo,14 pruebas pertinentes PASS y2.073 casos recogidos. En aquel corte Ruff conservaba280incidencias idénticas a HEAD; el saneamiento posterior las trató. [Registro y límites](evidencias/limpieza-instrumental-descartado-20261009.json). Mantenimiento concluido; no aceptó desarrollo integral.

## Saneamiento técnico autorizado — completado

Petición del usuario2026-10-09: resolver deuda detectada. Ruff global PASS:233 incidencias corregidas y47 diagnósticos de variables inyectadas documentados en dos fragmentos históricos conservados byte a byte. Rutas:89 trasladadas a `safety/urls.py`; las156 mantienen orden, argumentos y callbacks. Se corrigió una omisión demostrada: el adaptador de colas no reconocía refresco/barrido MOD05 sin argumentos y bloqueaba respuestas de acceso. Los argumentos o envelopes inesperados siguen rechazados. Preparación nativa reproducible y requisitos CI incorporados.

Verificación terminal: batería inicial120 casos,112 PASS/8 FAIL; cuatro fallos por binarios nativos ausentes y cuatro por la omisión. Correctiva posterior97 PASS, incluidas las ocho variantes fallidas, interfaz ES/EN, Redis físico/orígenes y guards. Worker/Beat reales PASS en la batería inicial. Unitarios16 y26 en runs separados; colección completa2085 casos sin errores. No se suman versiones/entornos como N3 ni se afirma ejecución completa de2085. Primera pasada interrumpida por variable Redis incorrecta, sin acreditar aislamiento ni sumar sus casos. [Fuentes, artefactos, huellas, preparación y límites](evidencias/saneamiento-tecnico-20261009.json).

PostgreSQL/Redis desechables, medios, checkout nativo y binarios propios retirados tras preservar evidencia. Modelos/reglas y servicios normales sin despliegue deliberado; CI externo no ejecutado. Capacidad de expedientes y demás insumos de matriz83 siguen pendientes. Pesos/porcentajes y aceptaciones de fases intactos.

## Entrega aceptada y runtime

| Alcance | Estado y fuente |
| --- | --- |
| BASE y CR01–08 | Verificados localmente; 9 de 15 hitos. [Actas](README.md#verificar-una-entrega) y [componentes reutilizables](88-matriz-cierre-derechos.md). |
| CR09-REND-LECTURA | Aceptado expresamente por el usuario el 2026-10-09 en `1a10ecf86a808daf9ae4dd2f72fbe414d5fc3c91`, con datos y proveedor sintéticos; integrado en master por fast-forward en `7691642`. |
| Servicios normales | Código desplegado `73d28f6`, migración Docker de derechos `0110`; núcleo de purga `72ff79a`. La integración de lectura aceptada no se desplegó en esos servicios. La versión de esquema de `listings` se distingue de `safety 0110`. |
| CR09 integral y fases posteriores | Abiertos; las preparaciones CR10/UI/ESEN/accesibilidad/SEO se reutilizan, sin aceptación de CR10, GS01, BF/BB o C. |
| Producción | Pendiente de gates y evidencia externa; sin publicación, contratación o datos reales. Cobros reales fuera de v1. |

## Evidencia y límites de la lectura aceptada

La revisión de Codex reutilizó artefactos originales y comprobó huellas y recálculos, sin nuevas cargas. [Informe de gates](evidencias/mod05-gates-normal-informe0110.md), [comparación 4/6](evidencias/mod05-capacidad-4-vs-6-refresco-informe0110.md) y originales [60 s](evidencias/mod05-gate-normal-short-artefactos0110.tar.gz), [900 s intento 2](evidencias/mod05-contractual-normal-intento2-artefactos0110.tar.gz) y [4/6](evidencias/mod05-capacidad-4-vs-6-refresco-artefactos0110.tar.gz).

| Escenario | Resultado conservado |
| --- | --- |
| Gate normal, 60 s | PASS: 1.200 éxitos, cero errores, p95 621,608 ms; pendientes de ventana 5 y finales 0, upload 1/1, drain 0,133 s. |
| Contractual normal, 900 s, intento 2 | PASS: 18.000 éxitos, cero errores, p95 392,360 ms; pendientes de ventana 7 y finales 0, uploads 15/15, drain 5,087 s. |
| Contractual normal, intento 1 | INVALID por demora del generador; no se sustituye por el resultado posterior. |
| Comparación 4/6 | Beneficio de seis FAIL en ambos pares; cuatro workers siguen como referencia, seis no adoptados. |

La [cobertura positiva](evidencias/mod05-cobertura-positiva0110.json) de [la prueba](../tests/test_publication_positive_coverage.py) conserva equivalencia byte a byte con la vía nativa y ruta `state`, ES/EN: normal 25 sin filtro/contact/agency y 10 con `checked` age; PRODUCTION 10 en todos los filtros. No acredita verificación externa real. La prueba positiva conserva código y resumen, sin JUnit original, y no fue repetida por Codex.

Los gates no archivan logs originales de Gunicorn ni eventos WSGI individuales. Host compartido, fixture y topología `normal_worker_beat` delimitan el PASS. No se acredita capacidad con grandes poblaciones positivas PRODUCTION/`checked`. Página 3 y promociones sintéticas conservan las limitaciones del informe; promociones usan fallback nativo medido. No se separan causalmente el efecto de la topología y el de la corrección de la marca sin señal, ni se atribuye la corrección GC del generador al backend. Todos los FAIL/INVALID/PASS anteriores conservan sus escenarios.

## Próximo trabajo y criterio de salida

Correctiva final de revisión binaria terminal `20261009-201631-db21c6aa`, handle82922 cerrado:63PASS/0FAIL/0SKIP; retirada de auditoría durante lectura real rechazada con rollback de Selection/action/evidencias, conjunto comprobado después de bytes/hash, una consulta real para dos photos y guards/paginación/ESEN/esperas PG PASS. Fuente igual, recursos propios retirados. [XML, duración exacta y fuentes](evidencias/revision-binaria-candidatos-n2-correctiva-20261009.json). Optimización funcional verificada; p95 de revisión todavía pendiente en flujo objetivo.

Preparación del controlador contenida antes del próximo flujo: nuevo launcher `scripts/run_capacity_environment.py` ejecutará el controlador existente dentro de Docker propio, herramientas Git/Docker y dependencias nativas readonly, UID local/grupo del socket, cap-drop/no-new-privileges, network none, CPU0,05/RAM128MiB/swap0/tmp64MiB. Mantener PG1,5/app2,25, reservar Redis0,20CPU/384MiB: suma4CPU/8GiB con controlador, verificar todos los cgroups reales y usar límite128MiB del controlador como cota conservadora al sumar picos disjuntos con caché. No cambiar aplicación, tamaños, umbrales ni fuentes de los63casos.

Storage previsto: rootfs readonly y log-driver none en cuatro roles; PGdata2GiB, app/tmp1GiB, PG/Redis/tmp/runtime/data pequeños explícitamente acotados y shm limitado. Único bind RW del controlador será su directorio de artefactos propio; RLIMIT_FSIZE32MiB real para él/CLI y máximo100archivos del runner, cota conservadora3200MiB. Inventariar tamaños de fuentes/stdlib/herramientas/imágenes readonly, tmpfs, artefactos y metadata; sumar cota y exigir≤20GiB, además de medir tamaños reales. No sustituir cota kernel+programa por disco libre. Primero prueba unitaria pertinente de escritura acotada/rechazo y preflight nativo del launcher sin cargas (Git real, PG/migraciones/Redis/temp/control/retirada); solo tras PASS lanzar flujo completo bajo todos controles con fuentes congeladas9000s. Si compatibilidad o control falla, preservar diagnóstico y corregir; no afirmar capacidad ni N3 desde readiness.

Sonda de controlador systemd terminal: [kernel y scope retirado](evidencias/capacidad-controlador-systemd-sonda-20261009.json). MemoryMax128MiB/swap0 reales, pero cpu.max ausente: user.slice solo delega memory/pids. Propiedad CPUQuota no acredita cuota; scopes inactivos tras terminar, ningún servicio normal modificado. Este camino no resuelve presupuesto completo. Preparar alternativa de controlador Docker propio después de terminal funcional, con herramientas nativas/montajes readonly, CPU/memoria/swap y storage comprobables; no ampliar límites ni declarar PASS desde propiedad de configuración.

Preparación independiente de presupuesto, sin editar fuentes congeladas de82922 ni cargar aplicación: systemd de usuario disponible. Sonda propia finita de scope transitorio `web-modelos-capacity-controller-probe-20261009-*`, CPUQuota5%/MemoryMax128MiB/MemorySwapMax0; Python real leerá /proc/self/cgroup y cpu.max/memory.max/memory.swap.max, además del cgroup del padre, para comprobar posibilidad de contener controlador/CLI propios. Conservar resultado y verificar scope terminado. No acredita carga/almacenamiento ni adopta reparto todavía. Propuesta compatible a evaluar después: PG1,5/app2,25/Redis0,20/controlador0,05CPU=4; RAM3072/4608/384/128MiB=8GiB, sin swap. Mantener presupuestos/objetivos globales y muestras; rootfs/logs/temp/storage requieren controles propios antes de aceptación.

Reproducción de frescura terminal `20261009-201431-21848dc2`, handle88920 cerrado:1FAIL esperado («DID NOT RAISE ValidationError») con retirada real de RightsImageAccess durante lectura nativa. Fuente igual, PG/Redis/temporales retirados. [Fuente exacta y fallo](evidencias/revision-binaria-auditoria-frescura-reproduccion-20261009.json). Corregir ahora orden de consulta después de bytes/hash, guardar solo UUID/digest; variantes negativas de evidencia leerán ambos contenidos antes de comprobar conjunto final, sin devolver bytes/autorizar resultado si falta evidencia.

N2 correctivo exacto reservado: mismos nueve archivos de la batería62 más nuevo caso de retirada tardía (63casos esperados, comprobar JUnit; no deducir PASS por colección), `run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --timeout 7200`. Archivos completos de guardado compartido, images, image_selection, image_storage, coverage_images, binary_races, selection_pagination, inspection_shared_source y inspection_source_unit. Exigir rollback de fila/acción/evidencias, dos bytes reales y una consulta en agrupado, equivalencia/idempotencia/guards/ESEN/PG waits intactos; Ruff/diff antes, fuentes congeladas, cero skips y retirada. Reensayo completo cambiado solo tras PASS, mismo4CPU/8GiB/1500/16MiB/64MiB y límites por etapa.

Reproducción `20261009-201312-00e0fc06` interrumpida por continuación antes de native-build/pytest; handle99577 ausente y procesos propios confirmados terminados. Sin JUnit ni crédito de prueba. Fuente igual; dos contenedores y único temporal propio identificado por configuración/corte retirados. [Interrupción y retirada](evidencias/revision-binaria-auditoria-reproduccion-interrumpida-20261009.json). Repetir el mismo nodo y condiciones para obtener reproducción real, sin alterar fuentes por esta interrupción.

N2 candidatos terminal `20261009-200400-7081b9a0`, handle98984 cerrado:62PASS/0FAIL/0SKIP461,323s JUnit; cinco variantes de consulta agrupada real1SELECT/caso, dos lecturas reales en válido y rechazo de evidencia/actor/versión/digest; paginación/ESEN/esperas PG y guards anteriores PASS. Fuente igual, recursos propios retirados. [Fuentes/XML/consultas](evidencias/revision-binaria-candidatos-n2-inicial-20261009.json). Continúa pendiente el requisito concreto de auditoría retirada durante lectura; no lanzar capacidad por este PASS parcial.

Reproducción acotada siguiente: añadir un caso a `test_portability_binary_save_shared_source.py` que retira RightsImageAccess al terminar image_content real durante un guardado nativo y exige rechazo/rollback (sin fila Selection/action nueva y evidencias restauradas por transacción). Ejecutar únicamente ese nodo bajo CI propio PG/Redis/nativos7200s antes de mover consulta. Tras negativo terminal, desplazar consulta agrupada después de todas las lecturas/hash, reteniendo solo UUID/digest; revalidar archivo completo y consumidores pertinentes, fuentes congeladas/retirada. No recortar bytes ni eliminar consulta/hash; mismo presupuesto/objetivos de capacidad.

Revisión del orden de frescura mientras N2 sigue vivo (sin editar fuentes congeladas): la consulta agrupada se ha situado antes de image_content, mientras la comprobación anterior ocurría después de cada lectura. Tras terminal y archivo de fuentes, añadir reproducción PG de retirada de RightsImageAccess durante la lectura real de bytes; exigir rechazo/rollback y consulta agrupada posterior a todas las lecturas/hash, sin conservar cuerpos. Si la reproducción falla, mover únicamente ese orden y revalidar variantes de evidencia y guards afectados. El PASS de la batería viva por sí solo no resolverá este requisito nuevo de equivalencia de frescura; no lanzar capacidad hasta verificarlo. Fuente actual permanece intacta durante98984.

N1 candidatos terminal: baseline1FAIL0,47s frente a500referencias; después13PASS0,29s, una sola referencia de índice original317, output/fuente preservados y hash de fila ajena rechazado. [Antes/después y fuentes](evidencias/revision-binaria-candidatos-n1-20261009.json). Validación agrupada implementada sin cambiar lectura/hash/locks de bytes. Se añaden cinco casos PG con dos photos reales de fixture: válido→dos lecturas/una consulta de auditoría; evidencia ausente, actor/versión/digest ajenos→rechazo. No criterio de capacidad por N1.

N2 exacto reservado para revisión binaria: `run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --timeout 7200`; archivos completos `test_portability_binary_save_shared_source.py`, `test_rights_portability_images.py`, `test_rights_portability_image_selection.py`, `test_rights_portability_image_storage.py`, `test_rights_portability_coverage_images.py`, `test_rights_portability_binary_races.py`, `test_portability_selection_pagination.py`, `test_portability_inspection_shared_source.py`, `test_rights_inspection_source_unit.py`. Incluye origen exacto, idempotencia/fresh-source, rechazo de actor/prueba/tokens/bytes/evidencia, paginación íntegra y ESEN/esperas PG existentes. PostgreSQL/Redis/nativos propios;7200s, congelar fuentes hasta terminal, cero skips y retirada antes de reensayar. No N3 ni p95 desde esta selección.

Perfil nativo terminal `20261009-195633-990d7a16`, handle84162 cerrado:1PASS154,945s JUnit, fuente igual y recursos retirados. Página real50filas/31páginas/1517entradas; perfil2,909s instrumentados,131SELECT. Dos source_copy,3002row_reference entre proyección/validación binaria,16image_content. [Perfil completo y fuentes](evidencias/revision-binaria-perfil-nativo-20261009.json). Tiempos acumulados se solapan; no p95 ni atribución causal bajo cuotas.

Correctiva acotada prefijada: `rights_portability_images.checked_images` calculará referencias únicamente para filas candidatas que contienen los photos declarados, conservando índice original/hash íntegro/validación exacta de path y ready; `audited_images` consultará evidencias existentes en un conjunto único por caso/actor/version, conservando image_content bloqueado+bytes/hash reales para cada foto y rechazos de digest/auditoría. Sin caché persistente ni modificación de selección/proyección/HTTP/fresh source/autoridad. N1: test puro nuevo en archivo de imágenes con500filas, selección exacta, contador candidato y rechazo de referencia/foto ajena; reproducción antes de cambiar app y archivo completo después. N2 siguiente: archivos nuevos de guardado, imágenes, storage, cobertura, carreras binarias, paginación y contextos; selección exacta antes de lanzar, PG/Redis/nativos propios7200s, fuentes congeladas y cero skips/retirada. Reensayo solo tras PASS, con límites intactos.

Flujo cambiado terminal `20261009-194511-abc85ce0`, handle94583 cerrado:1FAIL479,042s JUnit, negativo válido de revisión con16binarios incluidos. Guardado20versiones/caso PASS p954,064946/3,801835s≤5; revisión31páginas/caso FAIL p952,372175/2,395124s>2. Pares solapados en ambas etapas; siguientes inspección binaria/cobertura/generación/cierre/descarga NOT_PROVEN. DriverRSS517.992.448B; fuentes iguales, Gunicorn cerrado, tres contenedores y red ausentes. [Mediciones y fuentes exactas](evidencias/capacidad-entrega-binaria-revision-inicial-20261009.json). No sumar este PASS parcial a aceptación de capacidad/N3.

Diagnóstico siguiente prefijado antes de cambiar fuentes: nueva prueba `test_portability_binary_page_profile.py`, un expediente sintético completo1500/16MiB/64MiB con16imágenes incluidas usando constructor nativo existente. Perfilar un `selection_review.record(page=1)` real con cProfile y agregados de consultas SQL (execute_wrapper observador); conservar perfil completo y recuentos, sin sustituir fuente/bytes/SQL/autoridad. Solo atribución del camino en un caso, entorno PG/Redis/nativos propio focused7200s; no p95 ni causalidad bajo cuotas. Comprobar contenido ≤50filas/cifrado/auditoría y retirada, Ruff/diff antes de lanzar; fuentes congeladas hasta terminal. Elegir correctiva acotada únicamente tras localizar coste y luego guards/equivalencia antes de reensayo. No eliminar comprobaciones binarias para bajar tiempos.

Correctiva de fuentes de guardado terminal `20261009-193834-4d083022`, handle87323 cerrado:35PASS/0FAIL/0SKIP319,320s JUnit; siete casos nuevos completos PASS, contador real dos snapshots por guardado/replay, fallback nativo equivalente, cinco cambios tardíos con rollback y contexto falso/caducado rechazado. Guards existentes de imágenes/cobertura y esperas PG PASS; Ruff/check/migraciones/nativos/documentación PASS. Fuentes iguales y dos contenedores/temporales propios retirados. [Fuentes exactas, contador y XML](evidencias/guardado-binario-fuentes-correctiva-n2-20261009.json). No capacidad/N3 por esta batería funcional.

Reensayo completo reservado tras cambio verificado: `.venv/bin/python scripts/check_capacity_environment.py --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --delivery-complete`. Mismos tamaños, variantes y límites prefijados: dos casos1500/16MiB/64MiB,16imágenes incluidas,20guardados/versiones nuevas por variante, todas las páginas de cobertura y descargas completas. Topología4CPU/8GiB/swap0, PG1,5/app2,25/Redis0,25CPU, RAM3/4,5/0,5GiB;9000s pytest/10000s app/8400s futures. Inventario previo: MemAvailable10.787.484KiB y104.618.835.968B disco disponible, ningún contenedor CI propio anterior vivo. Congelar todas las fuentes no documentales; conservar FAIL/NOT_PROVEN, picos/huellas y retirada. Controlador sin cuota kernel y almacenamiento global pendientes, por lo que incluso PASS de etapas no acepta capacidad integral/N3.

N2 de guardado binario reservado: `run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --timeout 7200`, con archivos completos `test_portability_binary_save_shared_source.py`, `test_rights_portability_image_selection.py`, `test_rights_portability_image_storage.py`, `test_rights_portability_coverage_images.py`, `test_rights_portability_binary_races.py`, `test_portability_inspection_shared_source.py` y `test_rights_inspection_source_unit.py`. Siete casos nuevos: dos lecturas reales por guardado/replay, equivalencia con fallback nativo, cinco cambios tardíos con rollback y rechazo de contexto falso/caducado. Autoridad final fijada a epochs del token firmado. Ruff de fuentes tocadas y diff PASS. PostgreSQL/Redis/nativos propios; congelar fuentes hasta terminal, conservar fallos, exigir cero skips y retirada. Esta batería funcional no acredita p95 ni N3; repetir flujo objetivo cambiado solamente tras PASS.

Reproducción de contador terminal `20261009-192546-29fc91aa`, handle92475 cerrado:1FAIL42,32s CLI, siete source_copy completos por guardado frente a2 exigidos; selectores/evidencia/binario preservados antes de aserción. Fuente igual y recursos retirados. [Fuentes/XML/contador](evidencias/guardado-binario-fuentes-reproduccion-20261009.json). Ajuste prefijado: `_inspection_source` privado optativo en consume_approved/save_selection/catalog, default siguelecturas nativas; save envuelve en contexto existente de dos snapshots, autoridad/proof después de salida. No cambia modelos/HTTP/canonical/bytes/fuentes/locks/objetivos ni añade caché persistente. N2: nuevo test completo (contador/replay/equivalencia/cambios tardíos), image_selection/coverage_images/image_storage/binary_races y shared_source existentes; PG/Redis/nativos propios7200s, fuentes congeladas/retirada. Registrar selección exacta y20muestras TCP posteriores solo tras PASS.

Hipótesis finita de guardado binario tras FAIL5,811/5,670s: `image_selection.save` repite fuente completa en consume/catalog/store, mientras el contexto existente admite una fuente en transacción y comparación fresca final. Confirmar contador real PG en nuevo `tests/test_portability_binary_save_shared_source.py` sobre fixture native pequeño, exigir equivalencia de selectores/digests/idempotencia y dos lecturas completas por guardado; reproducción solo ese nodo antes de cambiar aplicación. N1 runner focused PG/Redis/nativos propios7200s, fuente congelada/retirada. Luego proponer opcionalctx privado en consume/store/catalog y envolvente pública de save, sin persistencia, con actor/proof revisados tras comparación fresca; casos de cambios tardíos/rollback/contexto inválido y carreras existentes antes de repetir capacidad. El contador demuestra trabajo repetido, no CPU causal ni p95 del escenario pequeño.

Flujo objetivo `20261009-190618-143874bf` terminal FAIL, handle52839 cerrado,1FAIL503,108s. Ambos casos1500/16MiB/64MiB y16binarios incluidos;20guardados HTTP200/no-store/versiones nuevas por caso, pares solapados, contenido conservado. p955,811144/5,669920s>5. Preparaciones nativas por operación≤60s; posteriores selección/cobertura/generación/cierre/descarga NOT_PROVEN por gate temprano. Fuente igual, Gunicornexit0, contenedores/red retirados. Memoria cgroup y controlador reales en informe, sin quota del controlador/storage global. [Fallo válido y límites](evidencias/capacidad-entrega-binaria-guardado-inicial-20261009.json), [Fuentes/XML/logs](evidencias/capacidad-entrega-binaria-guardado-inicial-20261009-artefactos.tar.gz). Próximo: confirmar coste de reconstrucciones repetidas en guardado binario mediante test PG de contador/equivalencia; compartir solo dentro de transacción y conservar comparación fresca final/autoridad/proof/bytes. No repetir idéntico para buscar PASS ni elevar5s.

Driver completo implementado y por ejecutar: `test_capacity_delivery_complete.py` usa helpers `capacity_delivery_flow.py` y `capacity_delivery_http.py`; árbol actualRuff/diff/docs PASS, tres consumidores recogidos. [Instrumento de IP real N12PASS](evidencias/capacidad-transporte-ip-real-n1-20261009.json), sin acreditar aplicación. Comando prefijado `check_capacity_environment.py --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --delivery-complete`; mismo4CPU/8GiB, reparto RAM PG3GiB/app4,5GiB/Redis0,5GiB para snapshots+paquetes/WAL, tmpfsPG2GiB/app1GiB. CPU PG1,5/app2,25/Redis0,25, swap0 verificados antes de pytest;9000/10000/8400s. Memoria cgroup se intenta registrar también en FAIL y controlador/CLI RSS por separado; controlador sin cuota kernel, storage global aún no probado. Resultado del runner, aunque todas etapas pasen, queda DELIVERYSTAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3; completar presupuestos y aceptación común aparte. No reducir tamaños/umbrales, truncar datos o declarar variantes mayores8MiB conformes.

Driver completo prefijado: dos casos1500/16MiB/64MiB con16binarios incluidos;20guardados HTTP nuevos de selección binaria y20de página de cobertura por caso (opción guardar del criterio guardar-o-aprobar, versiones distintas, sin replay),31páginas de selección y todas las páginas originales de cobertura,20inspecciones binarias incluyendo16distintas, negativas de aprobación incompleta. Decisiones finales nativas/HTTP independientes y tiempos individuales declarados, sin atribuirles p95 de guardados. Generación≤120s; preparación/inspección/aprobación final/cierre≤30s/op.20descargas JSON y20binarias/caso sobre sockets/IPs reales, consumir cuerpo entero y recuperar todos los campos/16hashes, packages≤8MiB y p95≤5s separados por caso/variante. Gunicorn2sync/PG1,5/app2,25/Redis0,25=4CPU, RAM8GiB/swap0;9000s pytest/10000s app/8400s futures, sin cargas competidoras. Si un gate previo falla, terminar FAIL y conservar posteriores NOT_PROVEN, sin truncar un PASS. Registrar cgroups/controlador/storage/huellas/limpieza y no aceptar N3/capacidad global por este runner parcial. Nueva rama de fixture obligatoria; fuentes congeladas tras lanzar.

Transporte del flujo objetivo prefijado: helper de pruebas con sesiones/CSRF reales, consumo completo/timing de cuerpos y SourceHTTPHandler que liga socket a loopback real. Descargas20JSON+20binarias por cada caso usan127.0.0.2/.3/.4/.5 (caso×variante), ventanas30/15min intactas; no forwarded headers, clocks o borrados de RateWindow. N1 significativo: servidor HTTP local efímero confirma dirección TCP del peer y cuerpo consumido para dos direcciones; no acredita Django/rights/capacidad. Helper se usará en driver completo; actor/receipt/sesiones permanecen contexto privado, fuera del manifest. Ruff/diff/pruebas transporte y colección antes de carga.

Constructor binario objetivo preparado: `prepare_target(include_binary=True, details=...)` conserva interfaz escalar por defecto y contexto privado sin receipt en manifest; incorpora16prepare/save nativos, límites60s por operación, digests del inventario y1500filas/campos intactos. Ruff global/diff/docs PASS y dos consumidores actuales recogidos. Rama binaria aún NO ejecutada/verificada funcionalmente; no aceptar por colección. Próximo paso: implementar driver completo de ambos expedientes y reservar recursos/casos/timeouts antes de cargar; conservar todos los guardados/inspecciones/decisiones reales y límites originales. No hay proceso de tests vivo al corte tras cerrar62711 y67548.

Preparación de flujo objetivo prefijada: extender constructor privado de pruebas `prepare_target` con inclusión binaria optativa de sus16imágenes mediante `image_selection.prepare/save` nativos y evidencias sintéticas elegible/provided/contract, cada operación≤60s medida aparte. Conservar interfaz por defecto y metadatos1501 del escenario escalar, añadir retorno de contexto privado opcional sin volcar receipt/actores en manifest. Mantener tres campos de1500revisiones/JSON16MiB y todos los originales64MiB; localizar imágenes por inventario actual, no posiciones inferidas. Este cambio prepara el ensayo completo, no se ejecutará carga parcial para declarar capacidad. N1 previo: Ruff/diff/colección de los consumidores existentes; funcionalidad nueva debe verificarse en el próximo flujo propio completo, con cuotas/criterios y selección registrados antes de carga. Guardados HTTP nuevos≥20/caso para medir el criterio guardar-o-aprobar por tipo de página, sin replay y con versionado real; inspección de todas las páginas originales, decisión final independiente, binarios, cierre y20descargas completas/caso. Ningún borrado de rate-limit, reloj congelado o lectura fabricada.

N2 de agrupación terminal `20261009-184147-7ce88b8c`, handle62711 cerrado:18PASS/0FAIL/0SKIP266,886s JUnit; checks/migraciones/nativos/Ruff/docs PASS. Generación de ocho WebP >64MiB total, imágenes individuales>8MiB completas/aisladas; guardas de generación/paquete/imagen tras esperas PG, ESENmóvil, cierre nativo y TCP íntegro con WebP9.437.486B. La parte de imagen mayor conserva límite64MiB y no aprueba capacidad≤8MiB. Fuente igual, PG/Redis/temporales propios retirados. [Evidencia/fuentes/límites](evidencias/capacidad-paquetes-objetivo-n2-20261009.json), [Artefactos](evidencias/capacidad-paquetes-objetivo-n2-20261009-artefactos.tar.gz). Agrupación e integración compatibles verificadas; no dos casos1500/16MiB/64MiB, p95, presupuesto propio/N3 ni capacidad integral.

Agrupación8MiB N1 terminal: reproducción2FAIL0,45s y correctiva8PASS0,72s; ZIP real/CRC/nombres/recuperación completa, bordes4+4MiB y aislamiento de9MiB. Límite duro64MiB/imagen10MiB conservados. [Fuentes/XML/límites](evidencias/capacidad-paquetes-objetivo-n1-20261009.json). N2 prefijado: `tests/test_rights_part_delivery.py`, `tests/test_rights_portability_binary_races.py` y `tests/test_portability_large_closed_transport.py`, enteros; cobertura generación>64MiB de binarios9MiB íntegros, POST privado/CSRF/replay/purga, ESENmóvil, esperas PG/revocación y cierre/descargaTCP funcional/grande. Runner propio focused PG17/Redis7.4/nativos,7200s por comando, fuentes congeladas y retirada.18casos esperados según parametrización; colección autoritativa se guarda. No benchmark de objetivos nuevos ni capacidad integral/N3; XML/huellas/logs/limpieza terminal obligatorios.

Ajuste de paquetes prefijado tras terminal: mantener límite duro64MiB y admisión de imagen10MiB para conservar el binario9.437.486B ya probado en matriz88; introducir agrupación objetivo8MiB contando cabeceras ZIP reales. Una imagen que exceda el objetivo se aísla en su propio paquete dentro del límite duro existente, sin recorte/recompresión ni pérdida. En el escenario de capacidad definido, cada imagen≈4MiB cabe y todos los paquetes deberán≤8MiB; la excepción de imagen mayor no aprueba ese gate y no modifica su criterio. N1 finito antes/después: nuevo caso de dos imágenes4MiB que demuestra límite real8MiB por overhead; caso mixto con9MiB verifica aislamiento y recuperación íntegra; archivo `tests/test_rights_copy_parts.py` completo y Ruff/diff. Sin PG porque es ZIP puro; después N2 de generación/descarga binaria y guards en PG/Redis propios, selección concreta a registrar antes de lanzar. Fuentes exactas/errores/retirada; no capacidad/N3 por unitarios.

Bloque siguiente preparado, dependiente del terminal de selección: entrega completa de ambos expedientes (16binarios/caso, cobertura de todas las páginas exigidas, generación, revisión final, cierre y descarga TCP completa). Inspección actual confirma `rights_copy_parts.PART_LIMIT=64MiB` frente al objetivo8MiB; revisar también admisión de imagen individual y límites efectivos al ajustar paquetes, sin recortar contenido ni declarar cuerpos incompletos válidos. Primero fijar cambio compatible y controles de ZIP real/equivalencia/guards; después ejecución con recursos propios y fuentes congeladas. La cobertura exige todas las páginas originales enumeradas por `required_pages`, no bastan las31páginas de selección; no sustituirla por flags o IDs fabricados. Comprobar por separado muestras mínimas por caso/variante, memoria disjunta con caché, almacenamiento, hashes y retirada. No cargar ni editar fuentes mientras siga vivo67963; no cambiar umbrales o tamaños para aceptar resultados.

Ensayo20versiones terminal `20261009-181502-57a345f5`, handle67963 cerrado,1PASS/0FAIL/0SKIP1284,576s. Por caso620consultas nuevas y20aprobaciones/selecciones distintas;31páginas/version, incompleto409 sin decisión en cada versión. p95páginas1,800605/1,801080s≤2; p95aprobación1,869632/1,885314s≤5. Máximo de página2,134895s conservado; no es un límite por petición. Preparaciones de versiones≤5,237s/op; iniciales13,955/13,608s. Auditoría adicional confirma620pares de lectura y20pares de aprobación solapados. DriverRSS521.850.880B, master35.053.568/workers209.145.856/208.900.096B, todos<1GiB. Picos cgroup disjuntos PG388.423.680/Redis8.822.784/app1.044.135.936B, controlador excluido; no memoria/almacenamiento global completo. Fuente igual, grupoGunicornexit0, tres contenedores y red ausentes. [Datos/fuentes/límites](evidencias/capacidad-seleccion-completa-versiones-20261009.json), [Artefactos](evidencias/capacidad-seleccion-completa-versiones-20261009-artefactos.tar.gz). PASS de consulta/aprobación escalar con tamaños objetivo; no binarios/cobertura/cierre/descarga/N3 ni capacidad integral. No relanzar este ensayo sin cambio/riesgo o requisito común pertinente.

Selección completa inicial `20261009-180338-4b3ca4cf` terminal INVALID de muestreo de aprobaciones:31páginas reales/caso p951,807638/1,795329s≤2; incompleto409 sin decisión y primera aprobación1,612185/1,567782s válidos. Segunda clave nueva409 correcto: Review.selection esOneToOne y servicio exige selección no revisada; test suponía20decisiones por misma selección. Aplicación no defectuosa por este resultado. [Datos/invariante/retirada](evidencias/capacidad-seleccion-completa-inicial-20261009.json), [Artefactos](evidencias/capacidad-seleccion-completa-inicial-20261009-artefactos.tar.gz). Sin20muestras positivas no aceptar gate≤5s, ni N3/capacidad íntegra.

Corrección de fixture ejecutada en el ensayo terminal anterior:20versiones reales de selección por cada uno de los mismos dos casos, cada versión mantiene1500revisiones/JSON16MiB y requiere31lecturas HTTP nuevas, luego una aprobación nueva. Nunca duplicar decisión de versión, copiar firmas ni sustituir lecturas por flags/replay. Medir620consultas/caso y20aprobaciones/caso separadas con p95≤2/≤5s, ventanas pareadas e independencia; preparación de nueva versión nativa medida aparte≤60s/op. Misma cuota4CPU/8GiB y Gunicorn2sync; originales64MiB residentes, aún sin binarios/cobertura/cierre. Trabajo humano sintético de620páginas exige presupuesto finito5400s pytest/app6000s; no cambiar límites por operación ni umbrales. Registrar fuentes/fallos/RSS/retirada; confirmar prerequisitos de muestra antes de carga para evitar falsas acreditaciones.

Plan inicial histórico, sustituido por el ensayo de20versiones anterior tras demostrar OneToOne: dos expedientes/revisores propios, mismos1500/16MiB/64MiB y reparto4CPU/8GiB PG1,5/app2,25/redis0,25, Gunicorn2sync. Nuevo modo --selection-complete:31páginas distintas por caso, rondas sincronizadas, ≤50filas; p95 de31respuestas completas≤2s por caso. Intento de aprobación tras página1 debe409 sin decisión, fuera de muestras positivas. Después20aprobaciones HTTP con claves nuevas por caso (misma selección/lecturas completas, no replay), p95≤5s, referencias exactas31páginas y20decisiones distintas por caso, RSS≤1GiB por proceso. Selección exclusiva mismo test concurrente,600s, fuentes congeladas/retirada. No selección de imágenes ni cobertura/generación/cierre/descarga/N3; originales64MiB residentes pero no entregados. Conservar FAIL/INVALID y no sumar versiones.

Reserva de benchmarks N1 terminal: Ruff globalPASS, dos nodos recogidos sin errores; pytest general2SKIP por guard de entorno sin montar fixture/cargar población. [Registro y límites](evidencias/capacidad-reserva-benchmarks-20261009.json). Flag definido exclusivamente por capacidad propia tras cuotas verificadas; no crédito de gates desde N3 genérico. Aplicación intacta. Estado vigente: consulta concurrente página1 PASS en reparto propio anterior; siguiente ensayo completar páginas/decisiones HTTP bajo mismo reparto y medir etapas restantes, con condición de salida prefijada antes de editar/ejecutar.

Separación de ejecución de benchmarks prefijada antes de N3: los dos módulos de latencia de selección exigen entorno de capacidad propio con límites kernel verificados. Evitar que pytest general lance cargas con SLO fuera de esa topología y convierta un skip de reserva en evidencia. Guard de colección `CAPACITY_ENVIRONMENT_VERIFIED`, fijado por runner de capacidad después de verificar cuotas; runner CI general no lo fija. N1: colección de ambos módulos, markskip y RHS explícitos, Ruff/documentos; sin nueva carga por cambio de marca. Gates de capacidad siguen obligatorios en runner dedicado y sobre mismo código integrado; N3 no acredita lo omitido. Fuente de aplicación intacta; PASS precedente es para su versión, sin ampliarlo a aprobación/binarios/cierre/capacidad íntegra.

Reparto PG1,5/app2,25/Redis0,25 de los mismos4CPU/8GiB verificado kernel: `20261009-175045-cbd4e105` PASS consulta concurrente página1,20respuestas completas/caso, p951,840419/1,726815s≤2s, sin contaminación ni errores y rondas solapadas. Máximo2,124082s del primer caso conservado; es p95, no techo por solicitud. Gunicorn2sync reales/master-grupoexit0; RSS driver342.401.024/master34.848.768/workers207.601.664/207.499.264B. Picos cgroup individuales PG296.701.952/Redis8.790.016/app847.745.024B, no total sincrónico ni almacenamiento global. Preparación14,041/14,660s y construcción15,227/14,750s separadas. Fuentes iguales/recursos retirados. [Datos/controles/límites](evidencias/capacidad-seleccion-reparto-pg-20261009.json), [Artefactos](evidencias/capacidad-seleccion-reparto-pg-20261009-artefactos.tar.gz). Adoptar reparto para siguientes ensayos propios de expedientes; no modifica servicios normales ni demuestra causalidad contra runs separados. Próximo: completar31páginas por caso y decisiones HTTP con muestreo de aprobaciones; después selección/cobertura binaria completa, generación/cierre/descarga≤8MiB y medición de presupuesto global. CR09 integral/N3/fases abiertos.

Siguiente experimento finito prefijado: misma aplicación/fixtures/umbrales/memoria y presupuesto total4CPU/8GiB, redis0,25CPU, PG1,5CPU/app2,25CPU en lugar de1/2,75. Es hipótesis de reparto, no diagnóstico causal de falta CPU; verificar límites efectivos kernel. Comando `check_capacity_environment.py --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy`,600s,20rondas pareadas/caso sin wrapper perfilado, RSS por proceso real y retirada. No agrupar casos/versiones, no aumentar recursos, no aceptar cierres/binarios/N3 ni capacidad íntegra. Adoptar reparto solo con resultado pertinente; si FAIL analizar sin repetir idéntico para buscar suerte.

Diagnóstico WSGI terminal `20261009-174257-a068d6f8`: FAIL p95 ordinario1,882800/2,119387s, veinte rondas por caso sin perfil; dos solicitudes adicionales perfiladas en dos workers con snapshots frescos~1,49s acumulados y seis fetchmany~0,675/0,757s. No atribución causal a CPU de PostgreSQL desde cProfile. [Perfiles/medidas](evidencias/capacidad-seleccion-perfil-wsgi-20261009.json), [Artefactos](evidencias/capacidad-seleccion-perfil-wsgi-20261009-artefactos.tar.gz). Fuente igual/recursos retirados/grupoexit0; handle72441 cerrado. No N3/capacidad integral.

UUID nativo N2 `20261009-173403-5830708d`4PASS75,19s. Gunicorn concurrente `20261009-173627-2aa5699c` FAIL: p952,022424/1,911865s,20respuestas completas/caso, sin errores/contaminación, solapadas. DriverRSS343.019.520/master34.996.224/workers207.679.488/207.839.232B, todos<1GiB; no presupuesto global probado. Fuentes iguales/grupoexit0/conts-red retirados. [Datos y límites](evidencias/capacidad-seleccion-uuid-nativo-20261009.json), [Artefactos](evidencias/capacidad-seleccion-uuid-nativo-20261009-artefactos.tar.gz). No beneficio causal de latencia demostrado; no repetir igual para buscar PASS. Próxima selección finita: mismo ensayo Gunicorn600s,20rondas sin instrumentar por caso más una consulta adicional perfilada por worker con wrapper WSGI propio, sin cambiar código de aplicación/criterios; conservar perfil separado/muestras/fallos/RSS y retirada. Objetivo diagnóstico de coste por función en procesos reales; no atribuir tiempos instrumentados a p95 ni CPU causal.

Gunicorn2sync `20261009-172759-22f20b7b` terminal FAIL:20muestras TCP pareadas por caso, p951,915102/2,024067s; segundo excede2s. RSS driver334.544.896B/master35.049.472B/workers207.527.936/207.417.344B, muestras realesVmHWM100ms, grupo terminadoexit0. Aplicación/guards/tamaños/cuotas originales, intervalos solapados; fuentes iguales y contenedores/red retirados. [Muestras/servidor/límites](evidencias/capacidad-seleccion-gunicorn-inicial-20261009.json), [Artefactos](evidencias/capacidad-seleccion-gunicorn-inicial-20261009-artefactos.tar.gz). No aceptación por margen pequeño ni nueva carga idéntica para buscar suerte.

Siguiente ajuste prefijado: parámetro de IDs de batch mantiene objetosUUID nativos de ORM, eliminando conversión a str/cast de arraytext; SQLparametrizado/orden/límite/locks/contenido inalterados. N2 finito: equivalencia nodo histórico[30], deriva de cuenta/imagen, equivalencia fuente compartida perfil[False] y cambio tardío[source]; PG/Redis/nativos propios7200s, fuentes congeladas/retirada. Historias1280 y demás17 ya demuestran límites/agrupación del helper anterior, sin ampliar validación de tipo al cambiar tamaño. Después repetir Gunicorn2sync600s/20rondas/caso/RSS con mismos objetivos. No N3/capacidad integral/cierre/binarios.

Concurrente válido `20261009-171918-3c04f157` terminal FAIL: dos casos/revisores reales distintos,20respuestas200/no-store completas por caso, intervalos pareados solapados, sin contaminación peer; p953,254659s/3,302852s>2s, RSS489.103.360B<1GiB. Preparaciones13,426/15,242s, construcción13,497/13,758s excluidas. Django live_server de un proceso con hilos; no causalidad de GIL demostrada. Fuentes iguales/recursos retirados. [Muestras/intervalos/versión](evidencias/capacidad-seleccion-concurrente-inicial-20261009.json), [Artefactos](evidencias/capacidad-seleccion-concurrente-inicial-20261009-artefactos.tar.gz). Siguiente experimento finito: misma selección/tamaños/barrera/20muestras por caso, Gunicorn real2procesos sync dentro de la misma cuota app2,75CPU/6GiB y presupuesto total4CPU/8GiB,600s; PG de prueba/Redis propios, mismo código y guards, sesiones reales; registrar RSS por proceso y picos cgroup, preparar/media/simulador explícitos en settings hijo. Fuente/umbral/tamaño intactos. No Caddy, cierre/binarios/N3/capacidad integral ni conversión del FAIL anterior en PASS.

Concurrente `20261009-171546-118034f5` INVALID de fixture: revisor nuevo sin email_verified_at ni aceptaciones corrientes; gate de cuenta redirige302/login antes de TCP. [Registro/retirada](evidencias/capacidad-concurrente-fixture-cuenta-20261009.json), [Artefactos](evidencias/capacidad-concurrente-fixture-cuenta-20261009-artefactos.tar.gz). Fixture correctivo conserva versiones de sesión/MFA e incorpora correo sintéticamente verificado y aceptaciones de documentos actuales del revisor sembrado para cada actor independiente; no se declara registro/correo/proveedor/MFA real probado por creación directa. Middleware/guards intactos, mismos criterios/selección/recursos prefijados; Ruff previo obligatorio y fuentes congeladas hasta terminal.

Concurrente `20261009-171230-6acfa69e` INVALID de fixture: sesión de nuevo revisor redirige302/login en lectura auditada antes de serie TCP, sin muestras. [Registro/retirada](evidencias/capacidad-concurrente-fixture-sesion-20261009.json), [Artefactos](evidencias/capacidad-concurrente-fixture-sesion-20261009-artefactos.tar.gz). Corrección de fixture: refrescar revisor después de force_login y fijar account_version/mfa_version actuales en sesión sintética real DB; guards de aplicación intactos. Repetir selección concurrente prefijada tras Ruff PASS, mismas condiciones/umbrales.

Concurrente intento `20261009-171027-01dc19cf` INVALID: IndentationError del helper extraído, error de colección antes de casos/muestras; Ruff lo detectó pero secuencia shell lanzó runner. Fuentes iguales durante run; recursos retirados. [Fuente fallida/limpieza](evidencias/capacidad-concurrente-fixture-sintaxis-20261009.json), [Artefactos](evidencias/capacidad-concurrente-fixture-sintaxis-20261009-artefactos.tar.gz). Corrección exclusiva de indentación, repetir selección concurrente prefijada solo tras Ruff PASS; no capacidad acreditada por este intento.

Ensayo concurrente prefijado: dos casos propios independientes, cada uno1500revisiones/JSON16MiB/originales64MiB, dos revisores autorizados distintos con lectura auditada real. Fixture localizará solicitud por submission_key de POST, no get global. Selección exclusiva nuevo `tests/test_capacity_selection_concurrent_tcp.py` vía `check_capacity_environment.py --selection-tcp --selection-concurrent`,4CPU/8GiB efectivos/600s,20rondas HTTP sincronizadas por barrera/20respuestas completas por caso, registrar intervalos solapados, p95 individual≤2s y RSS≤1GiB. Preparaciones secuenciales excluidas del p95; no prueba de login/proveedor real. No sustituir fallo por promedio combinado. Salida: muestras/metadatos/aislamiento/fuentes/recursos y PASS o FAIL documentado; no cierre, imágenes entregadas, N3 ni capacidad integral.

Relaciones por array UUID N2 terminal17PASS549,24s y TCP `20261009-170346-b03c6b84` PASS en alcance de un caso/página1 repetida:20respuestas200/no-store completas, nearest-rank p951,950027s≤2s, muestra máxima2,073637s conservada, RSS408.125.440B≤1GiB. Preparación13,700s y construcción13,698s separadas. Dos snapshots frescos mantenidos; fuentes iguales y tres contenedores/red retirados. Picos cgroup PG245.915.648/Redis18.468.864/app488.456.192B individuales, no total simultáneo ni presupuesto global completo. [Versiones/muestras/límites](evidencias/capacidad-snapshot-relaciones-20261009.json), [Fuentes/XML](evidencias/capacidad-snapshot-relaciones-20261009-artefactos.tar.gz). Siguiente acción: fixture multi-caso y medición TCP de dos expedientes independientes concurrentes,20muestras por caso sin mezclar, mismos tamaños/recursos/umbrales. Guardado, selección binaria completa, generación/cierre/descarga y N3 permanecen abiertos.

Relaciones N2 terminal `20261009-165335-d4f74278`:17PASS549,24s, sin skips; equivalencia histórica30/1280 contra ORM anterior, datos propios/aislamiento/cambios de fuente y cambios tardíos PASS. Fuentes iguales; PG/Redis propios retirados. Nueva fuente `rights_copy_revision_batches.py` conserva modelos, orden, lote1000 y locks de cursor. Handle64831 cerrado; no relanzar. Siguiente ensayo ya prefijado: `check_capacity_environment.py --selection-tcp`,20muestras del mismo caso1500/16MiB/64MiB, p95≤2s/RSS≤1GiB,600s, recursos propios; preservar resultado y retirada. No concurrencia/capacidad integral/N3.

Ajuste prefijado de relaciones: lectura por lote de IDs UUID exactos mediante un parámetro PostgreSQL `unnest(uuid[])`, sin listas ORM IN expandidas. Cinco consultas de relaciones, agrupación por revisión, mismos modelos/orden/bloqueos y límite1000. N2: archivo `tests/test_rights_copy_scope.py` completo y `tests/test_portability_inspection_shared_source.py`; equivalencia contra prefetched ORM anterior conservado como referencia de test, perfiles ajenos y cambios tardíos. PG/Redis/nativos propios7200s/comando, congelar fuentes hasta terminal; todos seleccionados PASS sin skips y retirada obligatoria. Solo después repetir TCP objetivo600s/20muestras/RSS, umbrales originales.

Batch1000 terminal: N2 `20261009-163919-c0a3c575`2PASS452,86s, historias30/1280; snapshot31/1281revisiones con15/20consultas respectivamente, equivalentes a batch50 cargando vector. TCP `20261009-164733-32f5fec9`20respuestas200 completas, p952,142210s todavía FAIL contra2s; RSS pico Linux486.993.920B durante construcción/preparación/20consultas <1GiB, no suma cgroup/presupuesto global. Preparación15,263s y construcción13,406s separadas. Perfil adicional conserva dos snapshots:20prefetch acumulan0,947s; no comparación causal de velocidad en host compartido. Fuentes iguales y todos recursos propios retirados. [Fuentes/medidas/límites](evidencias/capacidad-snapshot-batch-20261009.json), [Artefactos](evidencias/capacidad-snapshot-batch-20261009-artefactos.tar.gz). Estado vigente: optimizar materialización de relaciones del snapshot manteniendo contenido, orden, bloqueos, aislamiento y frescura; definir cambio concreto y selección N2 antes de tocar fuentes. No repetir carga idéntica para buscar PASS por variabilidad. CR09/N3/capacidad completa abiertos.

Vector generado diferido: N2 `20261009-162622-980d310c`48PASS495,37s; equivalencia, carreras y cambios tardíos PASS, fuentes iguales/recursos retirados. TCP correctivo `20261009-163525-4532f549`20respuestas200 completas, p952,250879s, todavía FAIL frente a2s; preparación16,186s, construcción13,639s, mismo tamaño. Diagnóstico adicional:60prefetch acumulados0,934s, dos snapshots frescos conservados. [Versiones/evidencia/límites](evidencias/capacidad-snapshot-vector-20261009.json), [Artefactos](evidencias/capacidad-snapshot-vector-20261009-artefactos.tar.gz). No N3 ni capacidad integral.

Siguiente ajuste finito prefijado: batch ORM1000 revisiones, manteniendo vector diferido, orden/locks/contenido y frescura. N2: solo nodo `tests/test_rights_copy_scope.py::test_profile_copy_queries_are_batched_without_losing_historical_revisions` con30/1280, cruce de batch1000 y referencia de batch50 que carga vector. Las48 anteriores cubren revocaciones sin modificación de esas reglas; no repetir40 sin riesgo nuevo. PG/Redis/nativos propios7200s/comando. Luego TCP mismo único caso/20muestras600s y añadir pico RSS real del proceso Linux separado de cgroup; umbral1GiB, sin convertirlo en presupuesto global. Criterio: equivalencia completa sin datos perdidos, todas variantes seleccionadas PASS; medir p95 sin cambiar2s; preservar FAIL, fuentes y retirada.

Corrección prefijada de coste de snapshot: diferir exclusivamente `Revision.search_document`, vector de búsqueda generado que `source_copy` no lee ni entrega. Mantener batch250, orden, select_for_update, prefetch y dos snapshots frescos. N2 finito: nodo `tests/test_rights_copy_scope.py::test_profile_copy_queries_are_batched_without_losing_historical_revisions` (30/280, equivalencia íntegra contra consulta que sí carga el vector), `tests/test_rights_portability_export_races.py` y `tests/test_portability_inspection_shared_source.py`; runner PG/Redis/nativos propios,7200s/comando, fuentes congeladas/retirada obligatoria. Salida: todos seleccionados PASS sin skips, copia idéntica y SELECT sin vector generado. Después repetir ensayo TCP exclusivo de1.500 revisiones/20muestras,600s, mismos objetivos/recursos. No cambiar umbrales ni acreditar N3/capacidad íntegra.

Diagnóstico TCP terminal `20261009-162106-0fd61c67`: veinte muestras p952,926983s, FAIL. Una consulta adicional perfilada separada identifica dos `source_copy` frescos:2,541s acumulados dentro de3,521s del servicio instrumentado, con coste ORM/prefetch; no atribución causal CPU ni latencia sin instrumentar. Ambas comprobaciones de frescura se conservan. Sin cambio de aplicación. Ruff del test falló por orden de imports antes del run; corregido después de conservar la fuente. Recursos retirados/fuentes iguales. [Diagnóstico](evidencias/capacidad-seleccion-tcp-diagnostico-20261009.json), [Artefactos](evidencias/capacidad-seleccion-tcp-diagnostico-20261009-artefactos.tar.gz). Siguiente trabajo: optimizar materialización del snapshot manteniendo contenido, bloqueos y frescura; registrar selección concreta y verificar equivalencia/races antes de repetir capacidad. CR09/N3 continúan abiertos.

Consulta TCP objetivo inicial terminal FAIL: `20261009-161655-8ffedc42`,20respuestas200/no-store completas, p95 nearest-rank2,895688s >2s; apertura GET0,165781s, preparación20,301s separada, construcción13,803s.1.500revisiones/JSON16.777.041B/imágenes originales67.095.050B. Un caso, página1 repetida; no concurrencia/cierre/selección binaria ni aceptación integral. Fuentes iguales; tres contenedores y red propios ausentes. [Muestras y límites](evidencias/capacidad-seleccion-tcp-inicial-20261009.json), [XML/fuentes](evidencias/capacidad-seleccion-tcp-inicial-20261009-artefactos.tar.gz). Siguiente selección finita: diagnóstico cProfile de una consulta adicional sobre el mismo escenario, hasta600s, misma topología, conservar veinte muestras aparte; identificar tiempo acumulado sin omitir validaciones ni cambiar el umbral.

Ensayo finito registrado antes de ejecución: consulta TCP de selección sobre un caso sintético de1.500 revisiones, JSON candidato16MiB e imágenes originales64MiB. Selección exclusiva `tests/test_capacity_selection_tcp.py`, PG/Redis/app propios con4CPU/8GiB, máximo600s para pytest y retirada obligatoria. Construcción y preparación separadas de20consultas completas de página1, máximo50filas, p95 nearest-rank ≤2s. Conservar muestras y FAIL; no acreditar concurrencia, guardado, cobertura, generación, descarga, presupuesto global ni N3. Primera apertura separada. Criterio de salida: registro terminal, fuentes iguales y recursos ausentes; si excede límite, analizar antes de repetir.

Revisión paginada de selección entregada en alcance local N2: máximo50 filas combinadas, lecturas por página firmadas y conjunto completo exacto para decisión web; no sustituible por consulta binaria/interna completa, replay y épocas vigentes. Migración0111 propia; ciphertext ilegible409 sin efecto. Batería inicial72PASS/1FAIL (fixture sesión), correctiva7PASS/2FAIL (selectores de test), navegador final `20261009-160706-0ac20ba7`2PASS ESEN móvil50→2filas, incompleto409 localizado, completo aprobado y sin desbordamiento; aplicación final igual a correctiva salvo selectors del test. No suma como N3. [Todas las versiones/fallos/límites](evidencias/seleccion-paginacion-correctiva-20261009.json), [XML/fuentes/migración](evidencias/seleccion-paginacion-correctiva-20261009-artefactos.tar.gz). Recursos retirados y fuentes iguales. Siguiente acción: enlazar fixture grande con casos reales y medir preparación/consulta/guardado por TCP HTTP, conservando etapas y límite de descarga; no repetir esta batería sin riesgo nuevo. Censo/N3/CR09 integral y fases siguen abiertos.

Correctiva de paginación `20261009-160242-89eac183`:7PASS/2FAIL en178,37s; sesiones nuevas, integridad/replay y ciphertext409 sin efecto PASS. Los dos fallos Chromium ocurren antes de interactuar: selector exacto sin suffix de etiqueta no coincide con `Página:`/`Page:` de Django. Fuentes iguales y recursos retirados. Ajuste exclusivo de test: etiquetas ancladas con suffix opcional `:`, conservando comparación de idioma y acciones reales. Repetir solo nodo `test_browser_requires_both_selection_pages` (ES/EN); no repetir7 ni72, sin cambio adicional de aplicación. Misma topología y condiciones de salida.

Ciphertext paginado reproducción `20261009-155928-6d2b27d4`:1FAIL en43,50s,500 por InvalidToken en preparación antes del guard de assessment; fuentes iguales y recursos retirados. Corrección compatible: convertir fallo de descifrado a ValidationError409 antes de crear acción; mensajes nuevos de páginas/assessment localizados ES. Correctiva N2 prefijada: solo archivo `test_portability_selection_pagination.py` (9casos, incluye dos Chromium móvil ESEN, primera página50/segunda2, intento de aprobar incompleto409, lectura completa y decisión, replay/metadatos/épocas/ilegible sin efecto). Sesión browser real DB sintética compartida desde fixture autorizado; no nueva prueba de login/MFA ni capacidad. PG/Redis/nativos/medios propios,7200s/comando; nueva lógica del servicio normal conserva72casos anteriores y no se repiten sin riesgo nuevo. Criterio: todos9PASS sin skips, fuentes iguales, XML/limpieza, bytes/sesiones/fuentes protegidos.

Terminal de paginación `20261009-154539-699bdc88`:72PASS/1FAIL en693,66s; único fallo sesión nueva de fixture,302 en lectura porque force_login conservó account_version antiguo; fuentes iguales y recursos retirados. Se descarta interpretación de fallo de aplicación para ese caso. Corrección exclusiva: logout/force_login y marcador account_version ligado a epoch actual de la sesión sintética. Reproducción adicional prefijada antes de ejecutar: `test_page_rejects_illegible_assessment_without_server_error` altera solo ciphertext de assessment propio después de preparar selección y exige409 sin efecto, frente a posible InvalidToken no convertido en preparación de página. Focused solo ese nodo, propios PG/Redis/nativos y7200s/comando; luego corrección/revisión de casos afectados y navegador paginado ESEN. No repetir72 sin riesgo nuevo ni acreditar N3.

Bloque de revisión paginada concluido en alcance N2 local seleccionado; la nota de proceso vivo anterior queda conservada en el registro de evidencia correctiva. Siguiente integración: capacidad HTTP con los dos fixtures grandes, según la selección finita que se registre antes de ejecutarla.

Reproducción paginación `20261009-153846-7ad60bd6`:2FAIL en50,91s,52filas devueltas y aprobación200 después de consultar una sola página; fuentes iguales y recursos retirados. Corrección de interacción compatible con alcance: máximo50 filas combinadas de datasets/imágenes por página, metadatos firmados por lectura y referencias exactas por decisión; migración0111 agrega JSON de página y lecturas a modelos existentes. Inspección nativa completa mantiene firmas sin metadatos; UI usa siempre página explícita. N2 final prefijado: nuevo archivo paginación (límites/completitud/replay/manipulación/revocación/ESEN/browser), `test_rights_portability_selection.py`, `test_rights_portability_selection_mobile.py`, `test_rights_portability_export_races.py`, `test_portability_inspection_shared_source.py`. PG/Redis/nativos/medios propios,7200s/comando, sin capacidad; registrar XML/huellas/limpieza. Una decisión paginada no acepta lecturas de otra sesión/versión/selección/revisor ni altera identidad/fuente; servicio interno completo no equivale a capacidad grande.

Requisito de revisión paginada registrado antes de construir: selección `rights_portability_selection_views.review` renderiza todo `projected.datasets` sin límite; objetivo local fija≤50filas por página. Reproducción finita nueva `test_portability_selection_pagination.py`,52filas seleccionadas (perfil+51revisiones), dos variantes: respuesta no supera50; aprobación tras primera página incompleta debe409. Preparación/identidad elegibilidad sintéticas con fixtures existentes, PG/Redis propios `focused`,7200s/comando, sin carga de capacidad. Si confirma fallo, implementar páginas de50 y evidencia autenticada de cada página, aprobación solo conjunto completo actual del mismo revisor/sesión/MFA/fuente/selección; preservar inspección nativa completa y firmas históricas como interfaz interna, GET sin contenidos, replay y roles/ESEN/browser. No limitar solo HTML ni aprobar datos no revisados; cambio cruzado de interacción/persistencia documentado y verificado antes de aceptación.

Fixture objetivo validado en versión final `20261009-153157-5b204d74`:1PASS/0fallos/errores/skips; dos sujetos propios con1500 revisiones cada uno,16777041B candidato JSON y≈67095KB originales por sujeto (dentro de±1% de16MiB/64MiB),32 WebP únicos válidos. Proyección nativa exacta, campos/textos distintos≤6000caracteres, párrafos completos y asociación separada; originales guardados verifican SHA. Fuentes iguales,3 contenedores/red retirados y Ruff/enlaces PASS. [Datos/tamaños/límites](evidencias/capacidad-fixture-objetivo-20261009.json), [dos runs/fuentes/XML](evidencias/capacidad-fixture-objetivo-20261009-artefactos.tar.gz). Próxima acción: reutilizar helper en casos reales y medir HTTP de preparación/revisión/guardado, generación/cierre/TCP concurrentes. Separar construcción del fixture de operaciones de producto y registrar política de muestreo compatible con30 descargas/IP/15min. El candidato no equivale a entrega completa revisada; almacenamiento/RSS/concurrencia y cierre integral siguen pendientes.

Fixture grande inicial `20261009-152826-4f2ac66e`:1PASS/0fallos/errores/skips en67,544s, dos sujetos×1500 revisiones,16777041B JSON cada uno y67095050/67095042B originales, fuentes iguales y recursos retirados. N1 inicial mostró F811 por fixture importado y parámetro con mismo nombre, sin fallo de ejecución. Ajuste de wiring del test a `usefixtures` para conservar exactamente fixture/semántica sin supresión estática; Ruff y repetición del único caso para verificar la versión final. Sin cambios funcionales de aplicación.

Fixture objetivo, selección registrada antes de construir: `tests/test_capacity_target_fixture.py` y helper reutilizable `tests/capacity_target_fixture.py`; nuevo modo `--fixture-target` del controlador limitado (exclusivo con control/diagnose). Crear dos sujetos/listings sintéticos propios con exactamente1500 revisiones cada uno, títulos/descripciones ES/EN distintos≤6000caracteres por descripción, párrafos completos de temas del anuncio y valores válidos. Calibrar número/distribución de párrafos del fixture antes de persistir, nunca truncar texto/documento ni duplicar filas para aparentar tamaño. JSON candidato de campos requeridos mediante proyección real16MiB±1% por sujeto;16 originales WebP procedurales distintos por sujeto de≈4MiB, sin bytes/metadata de relleno, suma64MiB±1%, validación real `read_upload`, archivos/hashes iguales y vínculos de sujeto exactos. Son texturas gráficas sintéticas aceptadas por validador, no fotografías de personas/verificación de contenido. Comprobar proyección de cada sujeto excluye el otro. Plazo180s/comando, mismos límites4CPU/8GiB ytmpfs; fuentes/limpieza. Criterio: fixture válido y métricas durables, no flujo aprobado/identidad/capacidad/worker/HTTP ni aceptación por tamaño solo.

Reducción SQL de conflicto concluida en alcance seleccionado: test correctivo `20261009-151722-0d4f6cbb`1PASS, más45 escenarios pertinentes previos PASS en intento con fallo de constructor preservado; no N3 común. Comparación válida instrumentada `20261009-150557-1777e6d4`→`20261009-151817-2b5bcad5`:9716→8952SQL (−764;7,86%), conflicto1528→764 mediante una consulta fresca por agencia, misma población/guardas. Tiempo de preparación23,863→24,352s: ninguna mejora de latencia demostrada; p95 ZIP1,101→1,156s sobre20 muestras de control, sin acreditación grande. Fuentes iguales y limpieza completa en todos los intentos. [Diagnóstico/corrección/límites](evidencias/capacidad-sql-conflicto-agencias-20261009.json), [fuentes/artefactos](evidencias/capacidad-sql-conflicto-agencias-20261009-artefactos.tar.gz). Siguiente trabajo: implementar fixture grande completo e instrumentación por operación/HTTP, distinguiendo preparación del trabajo acumulado de todas las lecturas obligatorias; no extrapolar preparación completa del fixture humano como una sola operación ni omitir lecturas. Censo propio/N3/fases siguen abiertos.

Regresión de conflicto `20261009-150949-eff2f194`:45PASS/1FAIL en410,73s; único fallo en constructor del test nuevo por email vacío duplicado, antes de invocar función. Los45 casos existentes pasaron, incluida autoridad/fuentes/esperas; fuentes iguales y contenedores propios retirados. Corrección exclusiva de fixture: tres correos sintéticos distintos `example.invalid`; repetir solo `test_rights_agency_conflict.py` y después el control instrumentado comparable ya registrado. No repetir45 sin cambio funcional/riesgo nuevo.

Diagnóstico corregido `20261009-150557-1777e6d4` control PASS con9716SQL atribuidos;9647 en aplicación (99,29%),69 exteriores. `agency_conflict`1528 consultas, `source_copy`924, `locked_case`707; preparación instrumentada23,863s sin atribuir cursor a CPU PG. Hipótesis/cambio mínimo prefijados: dos exists frescos de propietario/membresía se pueden unir con EXISTS correlacionado manteniendo agencia exacta y membresías históricas/inactivas como conflicto. Sin caché ni cambio de autoridad/modelos/rutas. N2 seleccionado antes de ejecutar: nuevo test de agencia/proprietario/membresía activa-inactiva/otras agencias y cambios frescos; `test_portability_inspection_shared_source.py`, `test_rights_portability_coverage_inspection.py`, `test_rights_portability_coverage_races.py`; luego control30 instrumentado comparable para demostrar reducción SQL, sin convertir tiempo instrumentado en gate. Recursos runner propios y7200s/comando para regresión; control180s. Criterio: todas las negativas/revocaciones/fuentes/esperas seleccionadas PASS, consulta fresca única por agencia no vacía, menor conteo comparable, huellas y limpieza.

Diagnóstico `20261009-150245-1c7a83ca`: control1PASS, pero diagnóstico INVALID por métricas ausentes. Causa comprobada: `DJANGO_SETTINGS_MODULE=config.settings` del contenedor prevalecía sobre ini pytest; archivo settings escrito pero no activado. El control anterior usó medios temporales proporcionados por fixture, no el MEDIA_ROOT adicional de settings inactivo; base test_capacity_ci siguió propia por nombre automático. No acreditar ese override ni atribución. Corrección: env Django explícito al ejecutar pytest y guard obligatorio de propiedad no vacía si se solicita diagnóstico. Misma selección/límites, fuentes iguales y3 contenedores/red retirados.

Diagnóstico finito registrado antes de programar2026-10-09: repetir exclusivamente control30 con `--diagnose`; hipótesis: inspecciones obligatorias por fila concentran SQL repetido entre comprobaciones de fuente/autoridad. Instrumento Django `execute_wrapper`: contar operaciones según función llamadora de aplicación y duración cursor.execute/executemany, sin SQL/parametros/valores personales y sin llamar tiempo SQL a CPU PG o tiempo total. Conservar mismas30 revisiones, aprobaciones,20 descargas, PG/Redis propios y límites/plazo180s; no otra carga propia. Criterio de salida: PASS de control, clasificación de≥90% SQL de preparación, grupo dominante identificado y evidencia terminal/limpieza; tiempos instrumentados no comparables como gate de rendimiento y ninguna corrección funcional hasta observar la distribución.

Control pequeño validado `20261009-145738-cd1b2e8e`:1PASS/0fallos/errores/skips en88,608s.30 revisiones, JSON10159B, WebP12418B, ZIP12598B;20 descargas TCP completas/hashes exactos, p95 paquete1,055s. Preparación/cobertura nativa23,280s y9716SQL; generación1,918s, cierre0,789s. RSS de etapa hasta284626944B; picos cgroup disjuntos PG194355200B/Redis16617472B/app244662272B, no pico agregado observado. Guards CSRF/enlace incorrecto/revocación/replay reales. Fuentes iguales y recursos retirados. [Registro de control y fallo previo](evidencias/capacidad-control-expediente-20261009.json), [logs/XML/fuentes](evidencias/capacidad-control-expediente-20261009-artefactos.tar.gz). Siguiente entrega de capacidad: fixture objetivo realista completo, revisión/guardado por HTTP e instrumentación concurrente/almacenamiento antes del ensayo1500×2; usar el coste de preparación observado para una hipótesis finita y evitar repetir89min históricos sin diagnóstico. Control validado no acredita el objetivo ni N3.

Control pequeño primer intento `20261009-145429-558facbb`:1FAIL en92,32s por HTTP429 tras superar30 descargas/IP/15min; guard legítimo, sin cambio funcional. Recogida JUnit por `docker cp` no vio tmpfs: ERROR instrumental, sin XML conservado, log original sí. Fuentes iguales y3 contenedores/red retirados. Ajuste antes de repetir:20 muestras completas únicamente del paquete ZIP (objetivo contratado), manifiesto/imagen medidos individualmente; total de descargas del control<30, sin limpiar ventanas ni modificar reloj/rate limit. Leer XML con `docker exec cat` dentro del mount. Misma población/límites/plazo, no interpretar fallo como capacidad del objetivo grande.

Selección control registrada antes de implementación/ejecución: un expediente sintético con30 revisiones históricas distintas por título y descripción legible de dominio, JSON≤1MiB y fotografía WebP válida≤8MiB, reutilizando aprobaciones independientes, cobertura, borrador y cierre reales del transporte nativo existente. Controlador propio `--control` ejecuta solo `tests/test_capacity_case_control.py`, plazo180s por comando/fixture, PG/Redis y límites de disponibilidad sin cambios; medios/settings/pytest en tmpfs. Medir etapas internas y20 descargas TCP completas por tipo con CSRF y hash/bytes exactos; registrar RSS del proceso y memoria cgroups disjuntos. Guards de enlace incorrecto/revocación/replay conservados. PASS significa instrumentación y control pequeño, no población grande ni p95 de revisión/guardado HTTP aún sin implementar. Salida: cero fallos/skips, fixture/tamaños verificados, métricas existentes, huellas iguales y recursos propios retirados.

Controlador de disponibilidad implementado y verificado: `20261009-145103-1c17bc58` READY_NOT_CAPACITY. Tres controles efectivos exactos de CPU/RAM/swap0; migraciones y Django check, conexión PG17/Redis7.4 y archivo temporal reales dentro de red propia interna, sin puertos públicos ni descarga. Fuentes iguales y tres contenedores/red retirados. [Registro de ambos intentos](evidencias/capacidad-entorno-propio-20261009.json), [artefactos y controlador](evidencias/capacidad-entorno-propio-20261009-artefactos.tar.gz). Siguiente trabajo: fixture de control pequeño y medición real por etapa/TCP/memoria; no repetir disponibilidad salvo cambios del controlador/topología. Almacenamiento total, navegador y expedientes grandes siguen sin verificar.

Disponibilidad de capacidad, primer intento `20261009-145033-3895554f`: ERROR antes de arrancar PG, configuración del driver local incompatible (`max-file=1` con compresión predeterminada). Fuentes iguales y contenedor/red retirados. Corrección finita: desactivar compresión del log limitado y repetir la misma selección; no altera límites ni criterios.

Selección finita de preparación registrada antes de ejecutar: controlador `scripts/check_capacity_environment.py`, modo de disponibilidad, red Docker interna propia sin puertos publicados, imagen app ya local con proyecto/UV readonly y Python actual; PG17 (1CPU/1536MiB), Redis7.4 (0,25CPU/512MiB), proceso Django (2,75CPU/6144MiB): suma de límites4CPU/8GiB. Verificar `cpu.max`, `memory.max` y swap desactivado dentro de los tres contenedores, conexión PG/Redis reales, migraciones completas y `check`, lectura/escritura de medios temporales propios, fuentes iguales y limpieza contrastada. Plazo180s por comando; sin navegador ni expedientes, sin atribuir capacidad/latencias o almacenamiento total20GiB a esta preparación. No ejecutar ensayo grande desde este modo. No tocar servicios normales ni descargar imágenes.

Conservación por finalidad verificada en alcance N2 local actual: `20261009-142404-35ed23b7`,43 PASS/0 errores/fallos/skips en357,78s; fuentes iguales y recursos propios retirados. Plan/seguimiento independiente y revocación durante espera PG real, fechas que no amplían autoridad, calendario/HTTP/móvil ES/EN, purga de copias/borradores vencidos y protección de evidencia emitida/fuentes/auditoría, reintentos/skip-locked y límites. [Resultado y parámetros](evidencias/conservacion-finalidad-ci-propio-20261009.json), [artefactos](evidencias/conservacion-finalidad-ci-propio-20261009-artefactos.tar.gz). Tareas invocadas realmente en pytest; no atribuir a este run worker/Beat real ni política jurídica productiva. N3 común pendiente; no repetir esta selección sin riesgo nuevo.

Preparación de capacidad: [sonda systemd](evidencias/capacidad-control-recursos-sonda-20261009.json) no verificó archivos de controles efectivos; no se acredita esa vía. [Sonda Docker](evidencias/capacidad-control-docker-sonda-20261009.json) leyó del kernel0,25CPU/64MiB exactos y retiró su contenedor. [Primer intento Python](evidencias/capacidad-python-contenedor-sonda-20261009.json) falló por alias del intérprete fuera del montaje; [corrección readonly](evidencias/capacidad-python-contenedor-sonda-v2-20261009.json) ejecutó Python3.12.13/Django5.2.17/cryptography/Pillow actuales en imagen local sin setup/DB/red y retiró el contenedor. No es carga, reserva de4CPU/8GiB, disponibilidad de Chromium ni capacidad acreditada. Próxima acción: construir controlador propio de capacidad con límites Docker verificables y fixture pequeño valido antes de medir el objetivo grande; preservar criterios ya fijados, censo/cobertura y guardas, sin cargar mientras otra batería propia esté viva. Censo propio y N3 siguen pendientes.

Selección conservación por finalidad registrada antes de ejecutar2026-10-09: `focused`,10 archivos explícitos: `test_erasure_plans.py`, `test_erasure_plan_authority.py`, `test_retention_reviews.py`, `test_retention_review_races.py`, `test_retention_calendar.py`, `test_retention_mobile.py`, `test_retention_localization.py`, `test_rights_final_draft_retention.py`, `test_rights_export_retention.py`, `test_erasure_execution_revocation_races.py`. Criterio concreto pendiente de matriz83: verificar configuraciones sintéticas por finalidad/artefacto, excepciones/reservas, autoridad independiente y revocación, vencimiento, retención debida/destrucción autorizada, reintentos e idempotencia en el CI propio y versión actual; no sumar componentes históricos como N3. Parámetros de los fixtures: decisiones `retain/review/erase/redact`, revisión inicial+30d y seguimiento+7d cuando corresponda; rechazar fecha fuera del límite admitido; vencimiento de copia/borrador forzado a pasado para ejecutar la tarea real y preservar auditoría/fuentes; respuesta emitida protegida como excepción, expiración no la autoriza a purgar. Fechas son parámetros de ensayo, no plazos legales; calendario1100 registros es metadato de paginación, no capacidad de expediente. PG17/Redis7.4 propios, datos/medios sintéticos, herramientas fijadas, HTTP/navegador ES/EN y esperas PostgreSQL observadas en los casos pertinentes. Fuentes congeladas/huellas del runner, timeout7200s por comando, JUnit/limpieza; salida todos los casos pertinentes PASS/0 skips, ningún efecto fuera del fixture y pruebas de permisos/privacidad vigentes. Restauración anterior se reutiliza como alcance propio; esta selección no acepta conservación productiva, fase o N3.

Restauración PG/medios y coherencia MOD05 completadas en alcance N2 local: final `20261009-141811-b62d6f5c`,2 PASS/0 skips en60,57s, fuentes iguales y recursos propios retirados. Dump real del contenedor CI y bases restauradas únicas, inventario completo de medios/huellas, autoridad independiente sintética y rechazo del checkpoint incorrecto, supresión/replay/sesión vieja, otro sujeto/comercial preservados, triggers restaurados activos y `refresh_publication_state --all` real antes de exposición. [Resultado, métricas y límites](evidencias/restauracion-ci-mod05-final-20261009.json), [cuatro pasadas originales](evidencias/restauracion-ci-mod05-final-20261009-artefactos.tar.gz). Los intermedios no sustituyen la pasada final ni se suman como N3. Próxima acción finita: completar censo propio/conservación pendiente y comenzar diagnóstico de capacidad con fixture validado y límites ya prefijados; no repetir esta restauración sin cambio/riesgo pertinente. Fases y N3 común siguen abiertos.

Selección de restauración registrada antes de programar/probar2026-10-09: `focused`, `tests/test_recovery_pg_restore.py` y `tests/test_promotion_recovery.py`, fuentes `recovery_*`, ledger/store, medios, MOD05 y fixture de supresión. Motivo concreto: la prueba antigua llama al Compose normal y no sirve en el CI propio; el contrato exige además comprobar coherencia MOD05 tras restaurar sin triggers. Adaptar herramientas PG al contenedor desechable identificado por el runner (validar nombre/puerto contra conexión activa), sin tocar Compose normal; probar dump PG real+medios, checkpoint independiente/rechazo de autoridad incorrecta, aplicación de supresión y conservación de otro sujeto/comercial, replay/sesión vieja, invalidación completa de estado restaurado y triggers activos tras restaurar. Registrar edad máxima del corte ensayado≤3600s (RPO de diseño en este fixture) y tiempo total de restaurar medios/PG/reconciliar≤28800s (RTO), sin inferir cadencia o capacidad productiva. PG17/Redis7.4 propios, claves/datos/medios sintéticos y base restaurada única retirada; fuentes congeladas, JUnit y limpieza. Operaciones dump/restore/child≤120s cada una, runner≤7200s por comando. Salida: ambos recorridos PASS sin skips, hashes iguales y ninguna base/contenedor/medio propio restante. N2 acotado, no N3 ni restauración de producción. Inicial terminal:2 FAIL en56,54s por relación inversa `Person.listing` mal referenciada en la comprobación nueva; [registro y originales](evidencias/restauracion-ci-mod05-inicial-20261009.json), fuentes iguales/recursos retirados. Corregir a `person.listing.pk`; repetir ambos casos y completar evidencia de huellas SHA256 del dump y de todos los medios antes/después de copiar/restaurar, con manifiesto restante exacto tras destrucción autorizada. Correctiva `20261009-141144-ddad4cb3`:2 PASS en62,39s y fuentes/limpieza correctas. Antes de archivar el cierre, completar el registro durable con el manifiesto completo de medios, corte absoluto del backup y retirada de la base restaurada; el temporal ya eliminado no permite recuperar ese inventario desde la segunda pasada. Repetición final pertinente de los mismos2 casos para conservar esos datos en JUnit; mismos recursos/límites, sin añadir carga o dar por medido inventario ausente. Inventario final `20261009-141623-601014ec`:2 PASS en61,50s, fuente/limpieza correctas. La revisión del procedimiento85 exige además ejecutar `refresh_publication_state --all` antes de salir de recuperación; marcar con la función interna sola no verifica ese comando. Incorporar su ejecución real y comprobar marcas vacías, versión actual y estado no elegible del anuncio suprimido; repetir la misma selección con fuentes congeladas y guardar todos los intermedios con sus límites. Cualquier incumplimiento bloquea este alcance.

Bloque correctivo correo/autoridad y simulacro de urgencia completado N2: `20261009-135130-83dd9d2e`,73 PASS/0 errores/fallos/skips en437,14s, fuentes iguales y PG/Redis/temporales retirados. Los dos fallos iniciales de correo y las16 reproducciones tienen ahora sus variantes correctas dentro de esta selección, sin sumar versiones como N3. Cronología ES/EN de recepción a decisión0,910029/0,902186s contra plazo sintético300s; no SLA humano. [Resultado y límites](evidencias/cr09-correo-autoridad-urgencias-correctiva-20261009.json), [artefactos](evidencias/cr09-correo-autoridad-urgencias-correctiva-20261009-artefactos.tar.gz), [protocolo local de urgencias](37-alertas-denuncias-urgentes.md#simulacro-técnico-local-de-suplencia-2026-10-09). Las selecciones/preparaciones siguientes son antecedentes de este bloque, no órdenes de repetirlo. Próxima fila activa: censo propio/cobertura de recursos y conservación/restauración pendientes de matriz83; reutilizar este cierre y confirmar después N3 común. Capacidad y fases posteriores siguen pendientes.

Reproducción terminal `20261009-134750-95b74428`:16 FAIL/0 errores/skips en99,70s, fuentes iguales y recursos retirados. Confirmados4 formatos del productor real de correo (ES/EN×verify/reset) no proyectados y12 revocaciones no rechazadas en decisiones de denuncia (permiso/sesión/MFA/actividad; tras controles de locks, replay y tras outbox). Intercalado determinista, sin alegar espera de bloqueo separada observada. [Registro](evidencias/cr09-correo-autoridad-reproduccion-20261009.json), [originales](evidencias/cr09-correo-autoridad-reproduccion-20261009-artefactos.tar.gz). Corrección: tres pares asunto/cuerpo conocidos (dos actuales y formato retenido anterior), manteniendo propiedad de token y redacción estrictas; actor fresco con actividad/permiso/sesión/MFA después de locks y al retorno. Sin migración ni nuevo canal.

Selección correctiva N2 prefijada antes de ejecutar: `focused`, archivos `test_account_mail_projection_templates.py`, `test_urgent_report_drill.py`, `test_rights_access_recipient_payload.py`, `test_report_decisions.py`, `test_report_inspection.py`, `test_report_notices.py`, `test_urgent_report_alerts.py` y los dos nodos fallidos `test_integrated_access_includes_console_mail_without_authentication_link` de `test_rights_access_coverage_store.py`. Código actual corregido y huellas de cambios locales congelados por runner; PG17/Redis7.4 reales propios, medios/compilación temporales y navegador ES/EN en los casos pertinentes;7200s máximos por comando, sin cargas de capacidad. Criterio de salida: todos los casos seleccionados PASS, ningún skip necesario, fuentes iguales, JUnit y limpieza contrastados; una pasada reducida no es N3 ni cierra fase.

Preparación independiente registrada2026-10-09: REQ-CR09-URGENT-DRILL-01, simulacro técnico de urgencia en cola interna real con responsable primario y suplente sintéticos, ES/EN. Fuentes finitas: `urgent_alerts.py`, `decisions.py`, vistas/inspección/avisos de denuncias y pruebas `test_urgent_report_alerts.py`/`test_report_decisions.py`/`test_report_notices.py`. Criterio: prioridad0→reconocimiento sin resolución→asignación→revocación del primario→rechazo de reasignación sin permiso→reasignación autorizada al suplente→rechazo de resolución sin lectura→consulta auditada→decisión motivada terminal/replay único y retirada del seguimiento. Cronología real local y plazo sintético de300s desde recepción a decisión, sin modificar relojes ni inferir SLA humano. Avisos internos cifrados/minimizados, ninguna entrega externa. La lectura del recorrido `decisions.act` muestra autorización sobre el objeto inicial sin reconsulta explícita de sesión/MFA/actividad después de locks; preparar reproducción determinista de revocación (permiso/sesión/MFA/actividad, replay y antes del retorno tras outbox), sin declarar fallo ejecutado o carrera observada antes de probar. Preparar el caso fuera de las fuentes congeladas mientras corre `rights`; aplicar y probar únicamente después de su resultado terminal. Recursos propios y condición de salida N2 pertinente deberán quedar registrados antes de ejecutarlo; preparación no equivale a PASS. Tras terminal de `rights`, se incorpora el caso y el perfil `focused` con selección explícita de archivos/nodos para reproducir el guard de revocación (12 variantes) y el correo ES/EN del productor real (4 variantes), antes de cambiar aplicación. PG17/Redis7.4 propios, herramientas fijadas y datos sintéticos; límites de ejecución del runner7200s por comando, integridad/limpieza y JUnit obligatorios. Salida esperada de reproducción: fallos identificados que confirmen o refuten la hipótesis; nunca aceptarlos como PASS. Luego corregir y verificar casos afectados y regresión pertinente de denuncias/correo sobre fuentes congeladas.

Selección finita CR09 registrada antes de ejecutar,2026-10-09: perfil `rights` del CI propio,18 archivos explícitos (identidad, inventario, declaraciones/referencias, decisiones por campo, cobertura independiente, respuesta/cierre, logs históricos, Redis retenido/físico y envelopes de broker). Incluye recorridos completos existentes de cierre/descarga, variantes cuenta/perfil, HTTP/concurrencia y navegador ES/EN. Fuentes: módulos `rights_access_*`, verificación y adaptadores de recursos; huellas actuales congeladas por el ejecutor. Recursos: PostgreSQL17 y Redis7.4 desechables propios, medios y compilación nativa temporales, sin recursos normales; host compartido de8CPU/23.204MiB,11.075MiB disponibles y98GB de disco en el inventario previo, sin aislamiento de rendimiento. Condición de salida: checks y todos los casos seleccionados PASS, skips identificados, integridad de fuentes y limpieza comprobadas; cualquier fallo exige corrección y nueva evidencia. Esta batería funcional N2 no acredita exhaustividad de censo productivo, capacidad numérica, N3 ni aceptación integral de fase. Terminal `20261009-131556-43982c5a`:194 PASS/2 FAIL/0 skips,1.712,48s; ambas variantes cuenta/perfil de correo de consola conservado fallan por candidato sin proyectar. Fuentes iguales y PG/Redis/temporales retirados. [Resultado inicial y diagnóstico](evidencias/cr09-censo-bateria-inicial-20261009.json), [artefactos originales](evidencias/cr09-censo-bateria-inicial-20261009-artefactos.tar.gz). No se acredita PASS conjunto/N3. El productor actual usa plantillas ES/EN separadas y el adaptador exige la antigua plantilla bilingüe; reproducir con productor real y corregir proyección estricta, sin limpiar pendientes genéricamente.

CI propio autorizado2026-10-09 y entregado: el usuario indica que no hay presupuesto para CI alojado y solicita gestionarlo nosotros. `scripts/run_local_ci.py` sustituye la dependencia operativa de GitHub con recursos desechables y evidencia local; GitHub queda solo manual. Perfil `smoke`:70 PASS/0 skips en357,03s, broker/publicación/Redis físico con PostgreSQL17 y Redis7.4 propios. Comprobaciones finales PASS; control negativo con checkout nativo inexistente devuelve ERROR/salida1 y limpia sus recursos. Las tres ejecuciones conservan huellas iguales y seis contenedores retirados. [Resultado y límites](evidencias/ci-local-20261009.json), [artefactos](evidencias/ci-local-20261009-artefactos.tar.gz) y [procedimiento](ci-local.md). Dos ajustes posteriores del postprocesamiento del ejecutor se verificaron con checks/control negativo, sin repetir ni sumar la batería funcional como N3. Sin cargas de capacidad, publicación, ejecución alojada o gasto. Facturación GitHub deja de ser prerrequisito; N3 y demás insumos continúan según su alcance.

Consolidación autorizada2026-10-09: [contrato16 v1.6](16-contrato-ejecucion-desarrollo.md) integra reglas vigentes y CI propio, con [historial exacto](17-historial/2026-10-09-16-contrato-ejecucion-desarrollo-antes-consolidacion-contrato.md). Alineados contratos14/15, matriz83 y esta cola. [Registro de conservación y verificación](evidencias/consolidacion-contrato-20261009.json). Sin aceptación ni cambio de porcentajes.

Los [objetivos locales de capacidad](propuesta-cierre-pendientes-locales.md) están fijados bajo delegación del usuario: dos expedientes simultáneos de1.500 revisiones,16MiB JSON y64MiB imágenes por expediente;4CPU/8GiB/20GiB para el entorno, memoria medida máxima6GiB y1GiB RSS por proceso de aplicación. Preparar≤60s, revisión50filas p95≤2s, guardar/aprobar p95≤5s, generar≤120s, cierre≤30s y descarga de paquetes≤8MiB p95≤5s. Muestras, tamaños, variantes, aislamiento y cálculo están definidos en el documento y en el [registro estructurado de criterios](evidencias/objetivos-capacidad-local-20261009.json), creado antes del ensayo y sin resultados de capacidad. Falta instrumentar/validar fixture y ejecutar; no se acredita capacidad desde esta definición. No se ejecutó carga al consolidar el contrato. El bloqueo de facturación GitHub es histórico: CI local lo sustituye y no exige pago.

1. Próxima entrega técnica: Codex debe concretar los escenarios locales aún sin evidencia de matriz83, empezando por censo/identidad/cobertura sobre fuentes sintéticas propias y reutilizando los alcances cerrados de matriz88. Registrar aquí una selección finita y su criterio antes de programar/probar; no iniciar otra auditoría global por rutina.
2. Codex define fixtures/parámetros ordinarios y, por delegación expresa, objetivos técnicos locales de capacidad; registrar criterios finitos antes del ensayo. Decisiones productivas reales permanecen en la columna de producción y no bloquean escenarios técnicos independientes.
3. Aplicar N1/N2 según riesgo y ejecutar N3 común al cerrar los requisitos técnicos locales, sobre una misma versión integrada, con CI propio y carga/recuperación exigidas. No trasladarlo al usuario ni sumar versiones; revisión jurídica o seguridad externa de producción no son requisito de ese N3 local.
4. Tras aceptación técnica integral CR09, continuar CR10 → GS01 → BF/BB → C. La preparación independiente puede avanzar por dependencia funcional; no acepta fases anticipadamente. Preparación productiva permanece separada y sin autorización de publicar/contratar.

## Avance ponderado vigente

Revisión v10: **CR09 72,50%** y **contrato 65,375%** (65,38% mostrado). [Método y tablas](86-medicion-avance-contrato.md), [cálculo original](evidencias/avance-ponderado-v10.json). Estimaciones de ingeniería por alcance; no horas, número de pruebas ni aceptación de fases. Esta organización y el cierre local de lectura no cambian pesos, denominador ni porcentajes.

## Reglas de continuación

Una cola, entregas completas y PostgreSQL en integración. Datos y medios sintéticos, recursos propios y limpieza. Reutilizar evidencia válida y mantener sus fuentes, versiones y límites; congelar fuentes durante ejecuciones vivas. Una hipótesis finita y una condición de salida antes de diagnosticar; sin pruebas o cargas por rutina. No publicar, contratar proveedores, usar datos reales ni modificar servicios ajenos.

Claude propone; Codex aplica y verifica. No hay máximo numérico desde MOD-03. Antes de delegar leer completo el contrato externo AI_ENGINEERING 1.0.1 y usar su `scripts/claude-task`, sin copiar ni alterar el adaptador. Consumo e invocaciones conservados en `.ai/tasks/desarrollo.md`; no sustituirlos por resúmenes de grafo.

## Historial y organización documental

[Copia íntegra anterior](17-historial/2026-10-09-17-seguimiento-desarrollo-antes-organizacion.md): conserva exactamente las 751 líneas previas, incluidas decisiones, verificaciones, fallos y antiguos próximos pasos. [Historial anterior](17-historial-desarrollo.md), [inventario de copias y huellas](historial-documentacion.json) y [registro de esta organización](evidencias/organizacion-documental-20261009.json). Las copias son consulta de evidencia, no una segunda cola; sus enlaces relativos conservan la base registrada en el inventario. [Comprobación de documentación](README.md#mantener-la-documentación).

## MOD-08 pieza 5 — ventana N2 aislada Codex, 2026-10-10

Usuario autoriza continuidad de los frentes paralelos tras agotarse tokens de Claude.
Escritor aislado `worktree-agent-ab23eda63576809b3`, base e8edcb1. Diseño y propiedad
registrados en `.ai/tasks/mod08-async-generation.md`. Generación Celery usa job durable,
misma función de dominio, motivo cifrado, UUID solamente en broker, autoridad original
fresca, locks e idempotencia; estado ES/EN con HTMX local y GET canónico. Familia nueva
incluida en inventario derechos por persona/cuenta y proyección broker/AOF tipada.

Principal autoriza ventana N2 PostgreSQL/Redis reales aislados, sin ensayo de capacidad;
reserva máxima dos workers (runner base sólo permite serie, usa uno). Runner detached,
fuentes congeladas, selección jobs + Chromium ES/EN + export races + broker schema +
inventarios y orígenes Redis. Estado **en curso**, sin PASS ni aceptación. Se preservan
consumidores síncronos internos y consumidores HTTP se actualizan al contrato de job.

Pieza5 primera N2 terminal negativo `20261010-122659-14afabde`:121PASS/19FAIL/0skip,
140 casos723.789s; fuentes sin cambios y retirada realPG/Redis/tmp. Los19 fallos comparten
inferencia de ámbito de jobs desde metadata pura de orígenes. Corregido paso explícito de
job_ids desde consumidor autorizado; añadidos casos positivos censo/brokerhistórico,
brokeroutage,3retry y esperaPG observable. Contrato HTTP y pruebas antiguas actualizados
sin quitar guards/sync/replay/descargas. Segunda N2 serie autorizada, fuentes congeladas
al arrancar, sin capacidad; [contrato pieza5](mod08-generacion-asincrona.md).

Pieza5 segunda N2 `20261010-124254-0b093368`:109PASS/3FAIL/0skip112casos605.679s;
fuentes sin cambios y retirada comprobada. Orígenes puros corregidos, HTTPprevios,
ChromiumESEN/sinJS, brokerworkerreal, revocación trasesperaPG y retries PASS. Tres fallos
en tests positivos nuevos: idioma activoEN frente expectativaES, censo cuenta sinatomic,
y publicación broker sin mensaje en cola leída. Se fijan idioma/locksdelharness y se
verifica cola/config/publicaciónreal antes de proyección. Preflight no consumidor de
prueba vigente añadido antes de esperar locks; autorización completa sigue bajo locks.
Tercera N2 dirigida módulojobs; no repetir las109sin cambio funcional que las afecte.

Pieza5 tercera N2 `20261010-125708-9a5d3971`:23PASS/2FAIL/0skip25casos224.186s; fuentes congeladas y limpieza PG/Redis confirmadas. Lease/atomic/preflight y worker real pasan. Positivos broker carecen de mensaje observable; se comprueban transporte/eager/cuatro shards y se corrige monkeypatch sobre objeto Task concreto, evitando restauración ambigua del proxy Celery. Cuarta N2 dirigida sólo outage y dos positivos, serial autorizada, sin capacidad.

Cuarta N2 `20261010-130258-e01b9a03`:1PASS/2FAIL/0skip59.05s. Transporte coincide; fallo diagnóstico confirma task_always_eager=True heredado del harness, sin publicación Redis. Positivos fijan CELERY_TASK_ALWAYS_EAGER=False igual que prueba worker real. Quinta N2 dirigida mismos tres casos; no cambio de dominio ni debilitamiento de proyección.

N2 correctiva final `20261010-130443-c476a607`: 3 PASS, 0 FAIL, 0 skips, 57.21 s. PostgreSQL/Redis reales, publicación UUID y proyección privada positivas persona/cuenta; transporte/eager y shards comprobados. Fuentes congeladas; limpieza real confirmada. Causa del harness: eager heredado; fijado False explícitamente en prueba broker. Evidencia complementaria: tercera N2 23 PASS (worker real, revocación tras espera PG, retries, lease, HTTP ES/EN); segunda N2 109 PASS (orígenes históricos, HTTP previo, Chromium ES/EN/sin JS, binarios); primera N2 export races/inventarios originales PASS. Terminales negativos anteriores se preservan. Integración conjunta y N3 capacidad siguen pendientes; no aceptación integral.


## Medición real posterior al catálogo y sellos — 2026-10-10

HEAD medido `228c540`: captura `20261010-185127-467de09c`, 1PASS/0skips/1917,386s; resultado tipado BASELINE_CAPTURED_DIAGNOSTIC_ONLY, salida1 intencionada tras aprobación real, no aceptación. Reutilización `20261010-192733-599e5146`, 1PASS/0skips/280,152s, PROFILE_DIAGNOSTIC_NOT_CAPACITY y HIT entre controladores reales. Fuentes e inputs sin cambios y retirada verificada en ambos. [Métricas y perfiles saneados](evidencias/mod08-medicion-catalogo-entrega-20261010.json); clave y estado cifrado privado excluidos.

Cobertura: 1.509 páginas reales, 383 lotes sin perfil, p95 **4,889s**. Comparación de los primeros123 lotes de4: 5,087→4,278s (**15,90%** frente al diagnóstico previo parcial), sin mejora adicional demostrada frente a 4,251s posterior a SQL. Perfil SQL447 frente a515; reducir consultas no acredita por sí solo reducir latencia. Descargas TCP JSON3 muestras p95 **9,107s**, binarias8 p95 **9,541s**, aproximadamente61% menos que el diagnóstico anterior de23,539/24,374s, todavía fuera de5s. Son cambios integrados más correctivas posteriores, sin atribución causal aislada a Claude.

Generación34,303s/1intento; preparación final11,536s, inspección4,431s, aprobación4,728s y cierre11,632s. Mediciones de un caso y muestras reducidas no sustituyen capacidad completa de2casos. Restan aproximadamente59% en lotes para2s,45% JSON y48% binario para5s. No se modifica aceptación ni avance contractual. Continúa candidato aislado de cálculos puros y transporte S3 por operación; no aceptado ni medido todavía.


Candidato aislado de cálculos puros/transporte: N2 `20261010-193904-c6edaa51` terminó **428PASS/4FAIL/0skips**, 607,294s, fuentes sin cambios y PostgreSQL/Redis propios retirados. [Evidencia negativa conservada](evidencias/mod08-regresion-puros-negativa-20261010.json). Corregidos solo wrappers/expectativas de tres archivos de pruebas; no cambia producción ni el rechazo de mutaciones/rollback. Repetición conjunta `20261010-195055-30642e82` en ejecución con fuentes congeladas, sin aceptación ni commit del candidato. Se prepara aparte borrador de verificación física S3 de máximo2objetos paralelos; no integrado, probado ni medido todavía.


## Cálculos puros y transporte por operación — integración local

Commit `d5c1db7`, integrado localmente en rama de integración y master: evitar canonización/digests repetidos por validación, firmas puras acotadas por operación atómica con SECRET_KEY fresco, validación única de decisión excluida equivalente, retorno audit-only sin copias descartadas, consultas latest id-only, transporte S3 acotado por operación con crypto/config frescos. N2 conjunta `20261010-195055-30642e82`: **432PASS/0FAIL/0skips/599,336s**, 37archivos, fuentes sin cambios, hash exacto de20archivos revisados y retirada independiente verificada de PostgreSQL/Redis/RustFS propios. [Evidencia y JUnit saneado](evidencias/mod08-calculos-puros-transporte-20261010.json). Negativa previa preservada; correctiva posterior solo tres pruebas, no producción.

La validación pasa de428PASS/4FAIL a432PASS/0FAIL; no es una mejora de latencia del request. Rendimiento de este commit todavía no medido y baseline antiguo inválido para estas fuentes. Se revisan aparte pipeline SQL acotado y verificación S3 de dos objetos paralelos antes de una nueva medición. Cada nueva métrica temporal incluirá cuadro comparativo, número de muestras, población y alcance. Criterios originales y porcentajes contractuales intactos; N3 y capacidad completa2casos pendientes.


Prototipo aislado SQL pipeline8/S3 dos objetos: N2 `20261010-200324-ff7a5086` terminó457PASS/3FAIL/0skips626,052s en39archivos, fuentes estables y PG/Redis propios retirados. [Evidencia negativa](evidencias/mod08-protocolo-paralelo-negativa-20261010.json). No integrado. Dos nuevos casos exigían rechazo ante mutaciones que deben contrastarse con validación completa; un caso previo LOGIN enforced declinó sello válido y requiere diagnóstico sin rebajar su assert. Próxima dirigida instrumentará diferencias/expiry/errores sin exponer SQL/params/credenciales. Rendimiento todavía sin nueva medición, objetivos originales intactos.


## Pipeline SQL y verificación física paralela — integración local

Commit `e19c3fc`, integrado localmente en rama de integración y master. SQL fresco en pipeline de8 statements independientes, misma conexión/snapshot por statement, drenaje antes de rollback y fallback serial compatible. Verificación física completa de dos objetos simultáneos como máximo, transporte privado por worker dentro de una invocación, crypto/config frescos, errores observados en orden y cierre obligatorio; no se omiten tombstones/SHA/AEAD/EOF/contexto.

N2 conjunta `20261010-202832-ee994233`: **460PASS/0FAIL/0skips/632,491s**,39archivos,3workers,hashes exactos revisados,fuentes sin cambios y retirada PG/Redis/RustFS verificada. [Evidencia y JUnit saneado](evidencias/mod08-protocolo-paralelo-integrado-20261010.json). Negativa previa preservada:dos nuevas mutaciones corregidas tras comprobar rechazo completo; warm fallback previo no reproducido y causa todavía no probada,assert original intacto. Dirigida instrumentada22PASS:124resultados pipeline==serial==grabados,caller/config coincidentes,TTL suficiente; instrumentación temporal retirada antes de conjunta.

| Regresión conjunta (misma población460) | Anterior | Actual | Objetivo |
| --- | ---: | ---: | ---: |
| Pruebas aprobadas | 457 | 460 | 460 |
| Fallos | 3 | 0 | 0 |
| Casos omitidos | 0 | 0 | 0 |

Es una correctiva/verificación funcional, no mejora medida del request. Próxima captura nueva1509páginas y reutilización diagnóstica con comparativa383/123batches y JSON3/binario8; baseline antiguo inválido para estas fuentes. Objetivos originales2casos y límites intactos; N3/capacidad completa/CR09 pendientes, porcentajes contractuales sin avance.


## Medición posterior a cálculos puros y protocolo — 2026-10-10

HEAD medido `b978377`: captura `20261010-204101-c0279589`, 1PASS/0FAIL/0skips, 1749,892s y resultado BASELINE_CAPTURED_DIAGNOSTIC_ONLY; reutilización `20261010-211629-2481e9a8`, 1PASS/0FAIL/0skips, 240,652s y PROFILE_DIAGNOSTIC_NOT_CAPACITY. HIT entre controladores reales, fuentes e inputs sin cambios, retirada completa verificada. PostgreSQL, Redis, RustFS Docker y Caddy reales; identidad simulada, datos sintéticos. Clave y captura cifrada privadas excluidas.

| TCP p95, misma población | Antes (s) | Actual (s) | Mejora | Objetivo (s) | Reducción adicional pendiente |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recorrido, 383 lotes sin perfil | 4,889199 | 4,375794 | 10,50% | 2 | 54,29% |
| Primeros123 lotes completos de4 páginas | 4,277687 | 3,862194 | 9,71% | 2 | 48,22% |
| Descarga JSON, 3 muestras | 9,106714 | 6,735796 | 26,03% | 5 | 25,77% |
| Descarga binaria, 8 muestras | 9,541089 | 6,428605 | 32,62% | 5 | 22,22% |

Recorrido de1509páginas; los383lotes incluyen grupos parciales, mientras123compara exclusivamente lotes de4 y excluye el único perfilado. Descargas incluyen respuesta303 y segundo GET con autorización fresca; JSON máximo8MiB y binarios inferiores8MiB. Comparación con capturas185127/192733 sobre HEAD228c540: mejora conjunta de los cambios posteriores, sin atribución causal aislada a Claude ni a una pieza.

| Operación, una muestra | Antes (s) | Actual (s) | Mejora | Objetivo (s) |
| --- | ---: | ---: | ---: | ---: |
| Generación encolada hasta durable | 34,303443 | 32,589223 | 5,00% | 120 |
| Preparación final | 11,536023 | 11,465790 | 0,61% | 30 |
| Inspección final | 4,430837 | 2,815197 | 36,46% | 30 |
| Aprobación final | 4,728369 | 3,090912 | 34,63% | 5 |
| Cierre | 11,631584 | 11,075993 | 4,78% | 30 |

Una muestra por operación no acredita p95 ni dos casos simultáneos. Los límites globales y poblaciones originales siguen intactos; no acepta N3/capacidad completa/CR09 ni incrementa porcentajes contractuales. Próxima candidata aislada: memo SHA de contenido idéntico por operación tras lectura física fresca, acotado16entradas/64MiB, todavía no probado ni integrado; su impacto y RSS deben medirse.

[Evidencia saneada de ambas mediciones](evidencias/mod08-medicion-puros-protocolo-20261010.json).


### Desglose de las mismas muestras TCP, sin una nueva ejecución

Runs anterior192733-599e5146 y actual211629-2481e9a8. Extracción de los campos originales download_http_stages; sin payloads, rutas privadas ni hashes de cuerpos.

| p95 por fase | Antes (s) | Actual (s) | Mejora | Muestras |
| --- | ---: | ---: | ---: | ---: |
| JSON POST autorización | 4,365753 | 3,246551 | 25,64% | 3 |
| JSON GET con forwardauth hasta EOF | 4,831444 | 3,709235 | 23,23% | 3 |
| Binario POST autorización | 4,840278 | 3,344003 | 30,91% | 8 |
| Binario GET con forwardauth hasta EOF | 4,846598 | 3,163433 | 34,73% | 8 |

No hay objetivo contractual independiente por fase ni porcentaje pendiente por fase. Los p95 marginales NO se suman: objetivo de la descarga completa dosHTTP<=5s, pendientes JSON25,77% y binario22,22%. Ambas fases conservan trabajo obligatorio; no aceptar una sustitución por HEAD, headers o cache entre requests. Captura de un caso sigue diagnóstica.

Candidato de metadata current-images declinado antes de implementación: image_contents valida toda la lista y espera todos los locks antes de primer read; adelanta errores de foto posterior y cambia ventana física del original. Borrador de contraste en worktree aislado sin integrar ni probar. SHA acotado por operación sigue N2 dirigida real, integración pendiente.

[Desglose saneado](evidencias/mod08-desglose-http-puros-protocolo-20261010.json).


## SHA de contenido idéntico por operación — integración local

Commit `ad1189b`: retiene como máximo16entradas/64MiB durante un batch atómico, asociado a conexión, bloque atomic, hilo y PID actuales. IDs sólo localizan bytes anteriores: reutiliza SHA exclusivamente tras igualdad completa de los bytes frescos exactos; cambios incluso del mismo tamaño se hashean de nuevo y nunca reemplazan el original. Tipos no soportados/límites/atomic terminado/contexto diferente usan SHA nativo. Limpieza finally obligatoria. SQL, locks, lectura física, autorización y auditoría de cada hijo permanecen frescos.

N2 dirigida `20261010-212613-ac0fdf4d`:51PASS/0FAIL/0skips318,443s; conjunta42archivos `20261010-213243-3a0e6675`:496PASS/0FAIL/0skips696,096s. Fuentes sin cambios, cuatro SHA exactos revisados y PostgreSQL/Redis/RustFS propios ausentes verificados. Lanzamiento inicial ARGPARSE conservado: omitía native-source por instrucción de root, sin servicios/pruebas; no negativo funcional.

| Prueba finita16fotos x4 hijos | Antes | Actual | Reducción | Objetivo de equivalencia |
| --- | ---: | ---: | ---: | --- |
| Lecturas físicas completas | 64 | 64 | 0% | Mantener64 |
| Cálculos SHA nativos | 64 | 16 | 75% | Misma salida exacta |

La prueba real PG con16WebPde4MiB acredita aritmética de retención64MiB, overflow nativo y limpieza; no appRSS<=1GiB ni peakglobal<=6GiB. Negativas de corrupción tardía, auditoría eliminada y sesión/MFA/permisos/prueba/fuente/expiry conservan rollback. No hay nueva latencia medida ni avance de aceptación/porcentajes contractuales. Baseline anterior inválido para estas fuentes; requieren captura nueva y medición con todas poblaciones y cuotas originales. N3 y dos casos simultáneos siguen pendientes.

[Evidencia y JUnit saneado](evidencias/mod08-sha-contenido-integrado-20261010.json).


### Instrumentación de GET diagnóstico, integrada localmente

Commit `1e6aae3`: transmite exclusivamente un marcador de perfil validado al GET privado de la petición extra perfilada, sin reenviar headers del POST. Las muestras ordinarias, dos validaciones, EOF, cookies, ámbito y no-store conservan el flujo original. N2 `20261010-214551-ea378e04`:41PASS/0FAIL/0ERROR/0skips269,731s, tres archivos, PostgreSQL/Redis reales y guardas legacy Caddy/worker; fuentes sin cambios y retirada propia verificada. Los14casos del marcador usan opener local: todavía no prueban propagación real del marcador por Caddy. El próximo capture/use debe producir fichero de perfil proxy real; no se declara ganancia de latencia.

Preparada captura nueva tras SHA, conservando1509páginas/383lotes/123comparables, JSON16MiB/originales64MiB, 4CPU/8GiB/20GiB/swap0 y todos los límites originales. Fuentes congeladas desde lanzamiento hasta terminal de captura y posterior reutilización; sin cargas competidoras. Doscasos/N3/CR09 íntegros siguen pendientes.

[Evidencia de instrumentación](evidencias/mod08-perfil-forwardauth-integrado-20261010.json).


### MOD-08: medición SHA y forwardauth real (2026-10-10)

Listado p95:383lotes4,375794→3,880241s (11,32%);123lotes completos comparables3,862194→3,264592s (15,47%). Objetivo2s, pendientes48,46%/38,74%. Descargas completas JSON6,735796→6,749283s y binaria6,428605→6,545222s: no mejoran, objetivo5s pendiente25,92%/23,61%. Un caso sintético, no aceptación de dos casos/N3. Capture215201/use222157 terminales sin errores, fuentes/inputs estables y retirada propia comprobada. Propagación real del marcador de perfil por Caddy verificada; dos autorizaciones frescas conservadas. Cuadros completos y muestras en [coordinación](../.ai/tasks/mod08-coordinacion.md); [evidencia saneada](evidencias/mod08-medicion-sha-forwardauth-20261010.json).


### MOD-08: canónica nativa y verify-only integrados localmente

Commits `a55ce87` y `034aa1e`; conjunta corregida `20261010-230920-aa4007af`:666PASS/0FAIL/0ERROR/0skips737,418s JUnit,48archivos/3workers, PostgreSQL17/Redis/RustFS reales. Todos los gates pasan, fuentes/artefactos intactos y retirada propia verificada independientemente. Integra validación canónica Cython con fallback exacto y loader memfd sellado; ABI/fuente/build/binario real forman identidad de reglas/baseline y congelación. Builder aislado Cython3.0.12, runtime sin compilación ni Cython. Pruebas conservan recursión/errores y rechazan reintento tras inicialización fallida para impedir reutilizar un mapping anterior por pathname FD.

Verify-only mantiene ciphertext staging, GET/SHA/tombstones/AEAD/contexto/SHA plaintext/EOF/autorización frescos; elimina solo tempfile/readback del plaintext que se descartaba. Read y legacy permanecen. También desaparece el ENOSPC de ese tempfile innecesario; no se presenta como equivalencia de fallos de recursos eliminados. N2 dirigida127PASS antes de conjunta; la conjunta previa637PASS precede corrección y no acredita la fuente final.

Aceptación funcional local, sin nueva ganancia de requests medida. Se prepara captura/use nueva con todas poblaciones/cuotas/objetivos originales; no reutilizar baseline previo tras fuente/binario cambiados. N3, dos casos simultáneos, memoria y todos los objetivos de latencia siguen pendientes; porcentajes contractuales sin incremento. [Evidencia saneada](evidencias/mod08-native-verify-integrado-20261010.json).


### Medición canónica nativa + verify-only — 2026-10-11

HEAD medido `b74274e`; captura `20261010-232333-7e99d547`1PASS/0FAIL/0ERROR/0skips1527,206s JUnit y uso `20261010-235349-4508b0cf`1PASS/0FAIL/0ERROR/0skips236,062s. HIT_DIAGNOSTIC_REUSED_PREPARATION, inputs/fuentes sin cambios y retirada propia comprobada independientemente. Termina congelación tras ambos terminales. PostgreSQL/Redis/RustFS/Caddy reales, identidad simulada; no proveedor verificado.

| TCP p95, misma población | Anterior (s) | Actual (s) | Mejora | Objetivo (s) | Reducción pendiente | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recorrido,383lotes sin perfil | 3.880241 | 3.778927 | 2.61% | 2 | 47.07% | 383 |
| 123lotes completos de cuatro páginas | 3.264592 | 3.303774 | -1.20% | 2 | 39.46% | 123 |
| JSON dos HTTP hasta EOF | 6.749283 | 6.048998 | 10.38% | 5 | 17.34% | 3 |
| Binarios dos HTTP hasta EOF | 6.545222 | 6.529290 | 0.24% | 5 | 23.42% | 8 |

Comparación con capture215201/use222157;1509páginas y384grupos, uno perfilado excluido. Efecto pequeño/desigual del listado, JSON mejora, binario prácticamente sin cambio. Todos siguen fuera de objetivos2s/5s. No atribuir causalidad a un candidato aislado ni declarar aceptación original de dos casos por un diagnóstico de un caso. Tres JSON<=8MiB y ocho binarios<8MiB, dos autorizaciones frescas y EOF.

| Operación, una muestra (no p95) | Anterior (s) | Actual (s) | Mejora | Objetivo (s) | Reducción pendiente | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| generation | 32.913815 | 32.078407 | 2.54% | 120 | 0.00% | 1 |
| final_preparation | 10.709931 | 10.446689 | 2.46% | 30 | 0.00% | 1 |
| final_inspection | 3.105194 | 3.369607 | -8.52% | 30 | 0.00% | 1 |
| final_approval | 3.760574 | 3.268270 | 13.09% | 5 | 0.00% | 1 |
| closure | 11.678849 | 11.279068 | 3.42% | 30 | 0.00% | 1 |

Perfiles GET reales propagados por Caddy: json_download_proxy-97 y binary_download_proxy-98. Muestras perfiladas adicionales excluidas de p95. Esperas de workers, joins y validación SQL se solapan: no sumar ni atribuir coste del join como trabajo propio. La próxima hipótesis requiere desglose finito de verificación física por worker y reproducción SQL para distinguir lectura/AEAD/planificación/materialización antes de cambiar garantías. Sin cachear autoridad ni omitir verificaciones frescas. N3, dos casos, memoria y objetivos completos siguen pendientes; porcentajes contractuales sin aumento. [Evidencia saneada](evidencias/mod08-medicion-native-verify-20261011.json).

MOD-08 2026-10-11: diagnóstico Session/observador terminal, un caso completo. p95 lote TCP383muestras3,806976s (anterior3,855044s), objetivo2s pendiente. Descargas JSONn3p957,040080s/binariasn8p958,191270s, peores que anterior6,467847/6,915486s; objetivo5s pendiente. Cuadro íntegro/evidencia en .ai/tasks/mod08-coordinacion.md y docs/evidencias/mod08-medicion-listing-phases-20261011.json. Candidatos streaming/fases/ultrareview jointd4899de compilados native-sealed/Ruff, gate real20files activo sin aceptación. Criterios completos dos casos/N3 y CR09/integral siguen pendientes.

MOD08 streaming/fases/ultrareview: gate corregido20files365PASS0fallos/errores/skips con PG/RustFS, fuentes y retirada comprobadas. Conjunto integrado localmente ef94e50, runtime igual a16fcc9a probado. Kernel compilado native-sealed actualizado. Medición nueva pendiente; objetivos completos2s/5s/dos casos/N3 siguen sin aceptación. Evidencia docs/evidencias/mod08-stream-phase-joint-corrected-20261011.json.

MOD-08 2026-10-11: ciclo streaming/fases terminal: captura 20261011-030418-57a8298d y use 20261011-033358-7f0a2acc. Verificados 1151 hashes por ejecución y retirada propia independiente. Listado383lotes p95 3,806976→3,885480s (empeora2,06%); subconjunto123 3,204901→3,376274s (empeora5,35%). JSONn3 7,040080→6,908405s (mejora1,87%); binarion8 8,191270→7,705974s (mejora5,92%). Objetivos2s/5s y dos casos/N3 pendientes. Cuadro y evidencia: docs/evidencias/mod08-medicion-stream-phase-20261011.md/.json. SHA aislado9ensayos alternados: hashlib vs cryptography sin ventaja útil; conservar hashlib. Revisión CPU no identifica bucle Python con margen suficiente para ampliar Cython. Nuevo diagnóstico factory/constructor/transporte delegado a storage_crypto en worktree codex/mod08-factory-profile, propiedad exclusiva tests/capacity_worker_profile.py y tests/test_capacity_worker_profile.py; no cambios productivos ni autoridad cacheada.

MOD08 factory diagnostic integrado: agente54eba6d + root30acd1f, gate real20261011-034708-b420ed67:77PASS0fallos/errores/skips12,251s. Root1148hashes y retirada propia verificados;28repositorios frescos,28lecturas de transporte y2constructores por operación2workers. Instrumentación solo, sin mejora de latencia acreditada. Evidencia docs/evidencias/mod08-factory-profile-gate-20261011.json.

MOD08 diagnóstico factory terminal: captura20261011-034833-051ebabc/use20261011-041853-bfd4c4a8 ambos1PASS0fallos/errores/skips.1151hashes cadauno y retirada propia comprobados. Listado383p953,865976s;JSONn3p957,313810s;binario n8p957,418959s. Cuadros y todas métricas docs/evidencias/mod08-medicion-factory-20261011.md/.json. Setup perfilado dominado por constructor primero1/workerno por hits. Análisis de constructor másligero pendiente, sin prometerganancia. Objetivoscompletos2casos/N3/2s/5s pendientes.

Experimento constructor cliente9ensayos alternados sinHTTP/profiler: boto3mediana wall0,101383s/CPU0,099833s;botocore0,094788s/CPU0,094089s. Ahorro6,6ms/cliente; no se aplica sustitución por margen insuficiente y hooks/métodos/user-agent distintos. Loader/modelos mutables no se comparten. Evidencia docs/evidencias/mod08-client-constructor-benchmark-20261011.md/.json. No mejora request atribuible.

MOD08 tiempos emparejados integrados: agente e78e32b, runtime 0d7c175. Gate real20261011-043924-04545920:59PASS0fallos/errores/skips6,013s;1150hashes y retirada propia comprobados. Primer gate56PASS3errores de arranque por imagen RustFS ausente; recuperado digest fijado y repetido PASS, evidencia negativa conservada. IDs alineados con TODOS los lotes TCP, incluidos parciales; extra perfilado excluido. Relojes WSGI wall/CPU incluyen consumo y close, sin cProfile/SQLhook; límites2048registros/256KiB. No optimización ni mejora acreditada. Evidencia docs/evidencias/mod08-paired-request-timing-gate-20261011.json. Nueva captura/use pendiente; aceptación completa doscasos/N3/2s/5s intacta.

MOD08 diagnóstico paired terminal:captura20261011-044039-31315f79/use20261011-051029-5ac023d6 ambos1PASS0fallos/errores/skips;1153hashes cadauno y retirada propia verificados. Listado383p953,802134s vs3,865976s (-1,65%);JSONn3p956,906630s vs7,313810s (-5,57%);binario n8p957,485222s vs7,418959s (+0,89%). Misma petición p95 ID327WSGI3,800317s/threadCPU2,066251s;CPUincluye nativo, espera/desplanificación no clasificada. Sin optimización productiva ni ganancia atribuida. Cuadro completo docs/evidencias/mod08-medicion-paired-20261011.md/.json. Siguiente diagnóstico fases emparejadas para elección concreta; no aceptación2casos/N3/2s/5s.

MOD08 fases emparejadas integradas:agente0edeb33/runtime4be6408. Gate real20261011-052545-6cf932cf:244PASS0fallos/errores/skips12,973s;1153hashes y retirada propia comprobados; kernelCythonreal cargado.19fases conwall/CPU inclusivo y exclusivo del mismorequestID. Registrosnuméricos8MiB/2048/4pages; flagsregistro/fase incompleta separados. Sin importsdominioanticipados: primeras fasesfaltantes explícitas, poblaciónTCP383intacta. ExclusiveincluyeSQL/trabajonoobservado; no atribuirPython/nativo sin evidencia. Sin optimización productiva ni mejora medida; siguiente nueva captura/use. Evidencia docs/evidencias/mod08-paired-phase-timing-gate-20261011.json. Criterios completos2casos/N3/2s/5s intactos.

MOD08 diagnóstico de fases terminal: captura20261011-052705-a77a598a/use20261011-055827-ff2d3cd6; 1PASS cada uno, cero fallos/errores/skips,1153hashes por ejecución y limpieza independiente. Listado383p95 3,934962s frente a3,802134s (+3,49%);JSONn3p95 7,812455s frente a6,906630s (+13,12%);binario n8p95 7,710310s frente a7,485222s (+3,01%). Sin ganancia atribuida ni aceptación completa. Cuadro y19fases del mismo requestp95 en docs/evidencias/mod08-medicion-phase-paired-20261011.md/.json. SQL447/wall1,763513s/threadCPUtotal1,932104s solapados. Candidata runtimeSQL en revisión, no implementada; preservar evidencia de sellos además de boolean.

MOD08 runtimeSQL experimento PG17 terminal20261011-061145-885358c3:8PASS50,183s/0errores;1155hashes ycleanupindependientes. Diseño helperRECHAZADO para producción: sustitución entre atestación/ejecución devuelve trusted falsificado. Medianas micro plain13,482495→8,173336ms/recorded17,066960→10,206525ms,n20porvariante, sincuotas y sinmejorarequest atribuida. Cuadro/evidencia docs/evidencias/mod08-runtime-sql-probe-20261011.md/.json. No integración runtime. Candidata índiceHMAC independiente en gatePGreal20261011-061409-419d935d/session57239.

MOD08 índiceHMAC primera dirigida PGreal20261011-061409-419d935d:26PASS91,589s;1155hashes ycleanupindependientes. Microfresh-hit1MiB str/bytesCPU -41,95%/-42,45% por8llamadas,n9parejas, no requestgain. Regresión4097bytes same-object+14,18%: candidata NO integrada; elevarumbral y añadir colisión tardía. Cuadro24escenarios docs/evidencias/mod08-fingerprint-index-probe-20261011.md/.json. Criterios originales pendientes.

MOD08 índiceHMACcolisiones gate20261011-061832-7c89443c:28PASS106,914s;1155hashes ycleanupindependientes.44escenarios cuadro docs/evidencias/mod08-fingerprint-index-collisions-20261011.md/.json. Microfresh-hit1MiB CPU~42%menor pero saturated-bucket+190%str65537/+154%bytes1MiB: NOintegrar82d088c. Promociónadaptiva a dict exacta preparada, gatependiente. Pipeline7sourcequeries ramaaislada gatePG3872/20261011-062201-7a9f150d actual. Objetivoscompletos pendientes.

MOD08 pipeline7sourcequeries gate real20261011-062201-7a9f150d:79PASS473,610s/0fallos/errores/skips,6archivos;1154hashes ycleanupindependiente. Micro7filas/703bytes,mediana7,204861→5,977018ms(-17.04%),n20/warmup2; no requestgain ni memoriafullsize. Cuadro docs/evidencias/mod08-chain-source-pipeline-gate-20261011.md/.json. Head/trust/eventos intactos, fallbacks y concurrencia/SQLerror/rollbackprobados. Integración localpendiente y objetivos completos2casos/N3 pendientes. HMACadaptativo gate58087/20261011-063047-4f8475cd en curso.

MOD08 pipeline7sourcequeries integrado localmente: candidatoea5eed6→runtime8d2aa7b trasgatePG79PASS/1154hashes/cleanupindependientes. Sin gananciaTCPp95 atribuida niaceptaciónfullsize; siguiente combinarHMACadaptativo si gatefavorable ymedir fuentescongeladas. N3/doscasos/2s/5s pendientes.

MOD08 HMACadaptativo gate20261011-063047-4f8475cd:31PASS106,207s/0fallos/errores/skips;1155hashes ycleanupindependiente.44escenarios/cuadro docs/evidencias/mod08-fingerprint-index-adaptive-20261011.md/.json. Fresh-hit1MiBCPU -40,46%str/-42,13%bytes por8calls/n9pairs, no requestgain. Saturación+0–4%vsreferencia traspromoción dict, negativos+190%/+154%anteriores conservados. Integración/gateconjuntopendientes; caps128/32MiB/secretfresco/scopes intactos. Aceptacióncompleta pendiente.

MOD08 pipeline/HMAC integrados e5e531c: gate conjunto PG real 20261011-063647-2425f04d 38PASS0fallos/errores/skips; 1156 hashes y retirada propios independientes. Evidencia docs/evidencias/mod08-index-pipeline-combined-gate-20261011.md/.json. Sin mejora request atribuida; nueva captura/use pendiente y aceptación completa intacta.

MOD08 pipeline/HMAC medición terminal captura20261011-064425-ed839a88/use20261011-071449-f8adec38:1PASS cadauno/0fallos/errores/skips;1156hashes cadauno ycleanupindependientes. TCP383p95 3,934962→3,753392s(-4,61%);JSONn3 7,812455→6,930455s(-11,29%);binario n8 7,710310→7,317947s(-5,09%). Cuadro completo docs/evidencias/mod08-medicion-index-pipeline-20261011.md/.json. Objetivos2s/5s/doscasos/N3 pendientes; SQLwrapperexcluye pipeline.sync.

MOD08 four-readers candidato21424e1:gatePG/RustFS20261011-072544-e4d007eb 99PASS0errores/fallos/skips,1156hashes ycleanupindependientes. Candidata integrada localmente para medición, rendimiento pendiente. Evidencia docs/evidencias/mod08-four-readers-gate-20261011.md/.json. Objetivos2s/5s/doscasos/N3 intactos.

MOD08 cuatrolectores RECHAZADOS rendimiento:captura20261011-073025-e9a3cb1c/use20261011-075925-06fbddf7 terminales1PASS cadauno/1156hashes+cleanup. TCP383p953,753392→3,726545s(-0,72%,noefectoatribuible);JSONn3 6,930455→7,741606s(+11,70%);binario n8 7,317947→8,645426s(+18,14%). Restaurar doslectores; negativa conservada docs/evidencias/mod08-medicion-four-readers-20261011.md/.json. Criterios originales pendientes.

MOD08 diagnósticoCPU af25346 preflightreal20261011-080958-6460fb0b READY_NOT_CAPACITY/1PASS/1156hashes ycleanupindependientes, cinco servicios con contadores válidos/0errores.43testscontractPASS. Cuotasintactas, CPUstatrecogidodespuésrequestsenexecmemoriaexistente. No pruebasaturaciónrequests: arranque/preflightsolo. Evidencia docs/evidencias/mod08-cpu-counter-preflight-20261011.md/.json; carga siguiente y aceptación completa pendientes.

MOD08 PAUSADO por petición explícita2026-10-11: documentar/commit/push/parar para otro enfoque. CapturaCPU20261011-081514-6f6a29ab interrumpida, launcher ausente y seiscontenedores/red/volumen propios ausentes verificados; sin resultado válido/no use. Relevo consolidado docs/evidencias/mod08-relevo-pausa-20261011.md. Doslectores restaurados; pipeline/HMAC/Cython conservados; objetivos originales2s/5s/doscasos/N3 pendientes. No agentes ni mediciones nuevos hasta reanudación expresa.


MOD08 2026-10-11: usuario autoriza exclusivamente diagnóstico local de descifrado/decode/parse JSON repetido en inspect_batch («Hazlo pues»). No reanudación automática de capacidad completa. Bloque activo: instrumentación temporal solo en tests/capacity_unseal_diagnostic.py y tests/test_capacity_unseal_diagnostic.py; objetivo contadores/bytes/CPU/wall sin saltar lecturas, crypto, autoridad ni auditoría. Dirigida PostgreSQL17/Redis7.4 propios, rol runtime separado, fixture sintético pequeño y sondas aisladas 4KiB/1MiB/16MiB; equivalencia/idempotencia, rollback y token inválido. Primera invocación20261011-110823-104b3a1e detenida antes de pytest por enlace absoluto histórico; corregido a relativo en acta04. Segunda20261011-110845-ba7c22e0 activa, un worker, selección nueva + test_capacity_phase_real_listing; fuentes congeladas y huellas en artifacts/local-ci/.../source-hashes.json. Condición de salida: terminal, resultados numéricos saneados y limpieza independiente; ninguna aceptación p95/capacidad. Artefacto Cython histórico ausente: límites de comparación explícitos.

Diagnóstico unseal primera dirigida20261011-110845-ba7c22e0 terminal8PASS/0fallos/errores/skips95,621s; fixture3páginas49unseal, repeat_parseCPU1,030501ms/copy_probe1,543643ms. No extrapolación a1500revisiones ni mejoraHTTP. Se amplía solo por riesgo concreto del instrumento: restauración de aliases importados durante scope y prueba de límites/reentrancia; dirigida20261011-111132-92674fec activa sobre test_capacity_unseal_diagnostic, un worker, fuentes congeladas. Evidencia esperada: métricas/7tests y limpieza. No cambios productivos.

Diagnóstico unseal autorizado TERMINADO20261011-111132-92674fec:7PASS/0fallos/errores/skips73,365s;1155huellas verificadas y doscontenedores propios ausentes comprobados independientemente. Lote runtime enforced3páginas49unseal: parseo repetidoCPU1,091ms, copia1,686ms, igualdad/búsqueda0,456ms; no margen demostrado para memoJSON en fixture pequeño. Sondas4KiB/1MiB/16MiB no son request/capacidad;16MiBcadena plana y sinCythonhistórico. No mejoras productivas ni p95nuevo ni aceptación2s. Evidencia [diagnóstico](evidencias/mod08-unseal-diagnostico-20261011.md)/[JSON](evidencias/mod08-unseal-diagnostico-20261011.json). Instrumento conserva crypto/lecturas/auditoría, limpieza/rollback probados. Finaliza este diagnóstico acotado; restoMOD08 permanece pausado y objetivos originales pendientes.

MOD082026-10-11: usuario autoriza adaptar/ejecutar diagnóstico grande si procede. No baseline/clave encontrados en búsqueda acotada artifacts/tmp/cache; no fallback a preparación contractual. Bloque activo: tests/capacity_unseal_wsgi.py y tests/test_capacity_unseal_large_batch.py, loteTCPúnico4páginas con Gunicorn2/LOGINruntime, fixturecalibrado1500revisiones/selección16MiB/originales64MiB, aprobación por servicios y31lecturaspaginadas reales. Diferencias: cobertura parcial, binarios retenidos no seleccionados, sinCaddy/RustFS/cuotascontractuales; nunca comparaciónp95 histórica. Cython recompilado explícitamente con3.0.12, binario4a178c247bccc9eae6883d298bd1546d613d0608538c48b959d84cc51bd94c8e validado antes de medir; no equivalente alSHAhistórico. Runnerdirigido20261011-112800-6d076bff/timeout900s/unworker, fuentes congeladas yhuellas durables. Condiciónsalida: terminal, reporte saneado de mismoHTTP conunseal+fases,4auditorías, limpiezaverificada; no exports/generación/capacidad completa.

Diagnóstico grande primera dirigida20261011-112800-6d076bff terminal1PASS/0errores/fallos/skips118,513s. LoteTCPúnico4páginas193unseal, selecciónproyectada16777586bytes pero descriptorscifrados223141bytes: parseoCPU42,211ms/repetido40,105ms, deepcopyprobe220,666ms, lookup2,577ms. TCPinstrumentado2,584294s no p95 ni comparaciónhistórica. No margen para memoJSON en este lote. Sourceexclusive451,524mswall/268,277msCPU; validate_assessment175,597/64,663ms. Diferencia relevante: loteinicial sin cientos de auditorías previas, no reproducir fasep95histórica. Se corrigió cierreGETdelwrapper;4testsEOF/errorHOSTPASS0,20s, no integración simulada. Gate final20261011-113250-ddd24db2 activo sobre lotegrande+4testsdelwrapper; fuentes congeladas. Evidencia prevista5tests, hashesyretiradaindependiente.

Gategrande20261011-113250-ddd24db2 terminal4PASS/1FAIL117,378s: POST/auditoríascorrectos, colector batchcalls0 por coldworker distinto delGET previo. Negativo de instrumentación conservado, no resultadofásico válido. Corregido inventarioURLnormal de Django antes de planificar aliases en worker marcado (sin lecturas/validaciones de dominio; import incluido enWSGI/TCP). Métricas se registran antes de assertfases para conservar futuros negativos. Dirigidafinal20261011-113602-59a09648 activa5tests, mismas fuentescongeladas/cuotas no aceptación.

Diagnósticolotegrande adaptado TERMINADO20261011-113602-59a09648:5PASS/0fallos/errores/skips116,956s,1161huellas exactas yPG/Redis/Gunicorn propios ausentes comprobados independientemente. TCPúnico4páginas2,241219s instrumentado, NO p95/cuotasni comparaciónhistórica.193unseal: parseorepetido31,466msCPU vs copia195,651ms; descriptorselección223141bytes frente aproyección16MiB, no unseal16MiB repetido. No implementar memoJSON. Validaciónchain132mswall aquí tiene31reads previos, nohistorialcentenariodelp95original; fuente426mswall/253msCPU. [Evidencia](evidencias/mod08-unseal-lote-grande-20261011.md)/[JSON](evidencias/mod08-unseal-lote-grande-20261011.json). Negativo4PASS/1FAILcoldworker conservado ycorregido. Diagnósticos autorizados terminados, sin modificaciónproductiva ni aceptación2s; MOD08 general siguepausado.

MOD08 2026-10-11: usuario autoriza diagnóstico finito de crecimiento de cadena («Hazlo pues»), sin reanudar capacidad completa. Bloque activo solo tests/capacity_chain_diagnostic.py, capacity_chain_wsgi.py y test_capacity_chain_{diagnostic,wsgi,growth}.py. Fuente base7e04016 con cambios locales preservados y huellas del runner; producto intacto. Hipótesis: el historial puede aumentar coste de validate_chain dentro de inspect_batch→record→validate_approved_assessment→require_runtime_chain, no causalidad/superlinealidad demostradas. Fixture nuevo1500revisiones/16MiB/64MiB,31lecturas reales y cobertura parcial como diagnóstico anterior; historial por POST real Gunicorn2/runtimeLOGIN, niveles0/16/64lotes sembrados y4muestras alternadas control/instrumentada por nivel, conteos reales antes/después porque cada muestra escribe auditorías. Presupuesto420s desde fixture preparado; no historial inventado/baselinefallback/descargas/proxy/cuotascontractuales. Desglose test-only chain/head/events execute+fetch/source_rows/pipeline.sync/runtime_trust; residual incluye verificación Python/transacción/overhead, no atribución kernel ni CPUservidor. Dirigida PG17/Redis7.4 propios/unworker, tests de restauración y EOF/error más integraciónTCP. Condición de salida: terminal, resultados y límites documentados, huellas y retirada independiente; no cambio productivo ni aceptación2s/5s. Fuentes congeladas mientras viva.

Diagnóstico crecimientochain TERMINADO20261011-114954-9aaaaa72:8PASS/0fallos/errores/skips207,724sJUnit,1166huellas exactas antes de actualizar docs yPG/Redis/Gunicorn propios ausentes comprobados independientemente.64lotes sembrados+12medidos porTCP crean608eventos reales, cabeza36→644. En niveles44–58/204–218/620–634eventos, cadena4calls porHTTP mediana38,640/69,692/178,845ms; events_execute6,671/16,812/48,309ms ypipeline.sync17,021/34,623/91,105ms crecen; cabezaSQL2,393/1,778/2,167ms yruntime_trust30,388/29,105/31,822ms estables aproximadamente. ControlesTCP n2por nivel medianas1,337/1,490/1,809s: no p95 ni comparaciónhistórica. Hipótesis crecimiento respaldada enescenario, no superlinealidad/causa completa/transformaciónproductiva demostradas. [Evidencia](evidencias/mod08-chain-growth-20261011.md)/[JSON](evidencias/mod08-chain-growth-20261011.json). Fuenteproductiva intacta; no memoautoridad, descargas ni aceptación2s/5s. Diagnóstico acotado autorizado completo; MOD08 general siguepausado.

MOD08 2026-10-11: usuario autoriza diagnóstico finito de planes («Procede pues») tras segunda opinión crítica de NotebookLM. No reanudación completa ni adopción UNIONALL/EXCEPT/sellos. Bloque activo exclusivamente tests/capacity_chain_explain.py y tests/test_capacity_chain_explain.py; fuente7e04016 con cambios locales previos preservados y huellas del runner. Fixture nuevo aprobado por servicios1500revisiones/16MiB/64MiB,31lecturas selección y cobertura parcial; niveles0/64lotes reales sembrados porTCPGunicorn2, no baseline disponible. Niño diagnóstico con LOGIN restringido independiente, fresh trust y validación íntegra/cabeza bloqueada antes de sondas. Ocho SELECT actuales (evento con digest +7sources), controles whole_row/jsonb_payload/inline_hash sin modificar producción. Huellas inline comparadas exactamente con originales sobre todas filas presentes; no prueba de equivalencia general de nuevo algoritmo. Por consulta: warmup1por variante,4rondas rotadas TIMINGOFF, nativo TIMINGON y nativo SERIALIZETEXT; planes/filas/buffers/estadísticas/índices registrados, sin ANALYZEmanual/índices/forzarplanner. Proyección/ancho pueden cambiar plan: informar shape, no atribuir delta puro aSHA. Presupuesto420s desde preparación/90schild/15sstatement;PG17/Redis7.4 propios, unworker. Condición salida: terminal, planes/interpretación/evidencia saneada, huellas y limpieza independiente; producto intacto, no p95/aceptación2s/5s. Fuentes congeladas durante prueba.

Diagnóstico planesSQL TERMINADO20261011-121055-8cc59a3c:1PASS/0fallos/errores/skips233,992sJUnit (integraciónPG/TCP real),1168huellas exactas antes de docs yPG/Redis/Gunicorn/hijoEXPLAIN propios ausentes comprobados independientemente. Fixtureactual16777325bytesproyectados/67095050bytesoriginales;64lotes reales cabeza36→548, variantes exactas/directas coinciden en584enlaces+584filas físicas observadas. Planes/control porfamilia mismaestructura en cada nivel; alto autoanalyze2 cambia planes respecto bajo. Eventos original8,242ms→directo4,954ms;SelectionRead7,494→5,232ms;CoverageRead11,215→7,262ms (medianas4SQL EXPLAIN TIMINGOFF, noHTTP). Controles sinhash0,469/0,543/0,846ms respectivamente; sugiere coste de expresión/normalización/wrapper, no atribución CPU pura ni índicefaltante. Dosfamiliasvacías/tombstones/concurrencia fuera corpus; candidataexpresiones SQL requiereequivalenciaymediciónHTTP antesadopción. [Evidencia](evidencias/mod08-chain-explain-20261011.md)/[JSON](evidencias/mod08-chain-explain-20261011.json). No UNIONALL/caché/omisiónchecks/cambio productivo ni aceptación2s/5s; diagnósticoacotado concluido yMOD08general siguepausado.

MOD08 experimento inline autorizado y TERMINADO2026-10-11: plan discutido críticamente con NotebookLM y aplicado sólo a hashes lectores EVENT+7sources; productores/DDL/bloqueos/frescura/pipeline íntegros. Runner20261011-123640-097bae75:78PASS0fallos/errores/skips248,26s,1171huellas exactas y recursos propios retirados comprobados independientemente. Equivalencia siete familias+tombstone/zonas/JSON/DST/search_path y regresiones PG reales; HTTP2syncworkers/runtimeLOGIN,20muestrasporvariante/ABBA-BAAB/cadauna clon idéntico548eventos,commit normal4lecturas+8eventos. Original mediana797,984ms/p95819,964ms;inline789,795ms/829,377ms: beneficio pequeño/ruidoso y cola peor. RECHAZADA productivamente, evidence_chain.py restaurado exactamenteHEAD; patch/test-only/evidencia negativa conservados. Gate posterior del helper tras retiro20261011-124558-a4d43659:28PASS0fallos/errores/skips20,36s/1172huellas exactas/PGRedis ausentes; no nuevo benchmarkHTTP ni aceptación conjunta por sumar tandas. Notebook coincide tras recibir método/resultados/opinión propia. [Plan, incidentes y dictamen](evidencias/mod08-inline-http-20261011.md)/[JSON](evidencias/mod08-inline-http-20261011.json). Objetivos2s/5s/topología completa siguen pendientes;MOD08general pausado.

MOD08 deliberación siguientevía2026-10-11 autorizada, sin carga/producto: dos intercambios con NotebookLM tras negativo inline, con resultados previos/código/opinión propia y correcciones de perímetros, GIL, formatos canónicos y umbrales inventados. Priorizar diagnóstico de construcciónfuente: source_copy/iteración efectiva batches/materializaciónORM/construccióndicts/fingerprints/canonicalentrada-salida/render. Propuesta unbloquecontrol-perfilado-control conhistoriaidéntica/PGpropio/2workers/warmPOST y CPUprofiler auxiliar sinlocals; NOejecutado ni p95. CandidataCONDICIONAL sólo valores primitivos categorías/servicios/travelareas si coste instanciación significativo; consumidoresadaptados,filas/orden/momentoslecturas/frescura intactos, sin tocarRevisionlocks/PhotoBlob/autoridad. Sin porcentajes/ahorros asumidos ni límitearquitectónico declarado. [Deliberación, fuentes y condiciones](evidencias/mod08-notebook-siguiente-via-20261011.md). MOD08generalpausado,objetivos2s/5spendientes.

MOD08 diagnóstico construcciónfuente autorizado «Procede» y TERMINADO20261011-130102-8286f2c3:5PASS0fallos/errores/skips98,47sJUnit/1176huellas exactas/retiradaPGRedisGunicorn propia independiente. TresPOSTcontrol-perfilado-control,clonesidénticos548eventos/256reads tras64lotes reales,2workerswarm/mismoPIDmedido,4auditorías+8eventosporcommit. TCP812,239/1882,635/796,736ms;perfilCPU1563,754 vscontroles428,554/425,883ms:gran intrusión,no descuentooverhead nip95. Fuente1call425,327wall/362,969CPU ybatches_next1501calls378,769/319,893msperfilados;residualnoORMpuro. RelacionesCategory/Service/Municipality pequeñas,residualCPU~5,4ms conjunto trasSQLobservado: candidata valoresprimitivosNOjustificadaenfixture,cerrarporahora,sinproducto. Pista scalar_fields101755entradas/reanudaciones(inclrecursión) ypointer_value9002: NOrecorridoscompletos ni147msahorrables;medición sinprofiler/equivalencia requerida antescandidataiterativa. Incidencia primerRunner125955-bb11e9ddinterrumpido0tests47,93s porcolisiónnombretest;existente restauradoexactoHEAD,nuevo test_capacity_source_construction_profile.py. [Evidencia/limitaciones](evidencias/mod08-source-construction-profile-20261011.md)/[JSON](evidencias/mod08-source-construction-profile-20261011.json). Resultados/opinión remitidosnotebook;sin nuevaoptimizaciónniaceptación2s/5s;MOD08generalpausado.


MOD08 2026-10-11: usuario autoriza montar sala local de deliberación y debatir desde diagnóstico construcción fuente. Excepción expresa «Sí, excepción solo para deliberar» al adaptador/contrato externo ausentes: Claude CLI revisor sin herramientas ni edición, consumo registrado en .ai/tasks/desarrollo.md. Sala .ai/rooms/mod08-20261011, script scripts/deliberation_room.py, cuatro solicitudes externas máximo y cierre por Codex. No modificación productiva ni reanudación capacidad general. Bloque activo: contraste Claude/NotebookLM con código y resultados previos, controles unitarios del orquestador, decisión finita documentada; propuestas no son PASS.

Sala MOD08 TERMINADA: dos opiniones Claude y una NotebookLM recibidas; cuarto turnoNotebook rechazadoqueryinvalid, preservado sinretry. Cierre porCodex trascontraste crítico, sinconsenso final supuesto. Nueve controles unitariosPASS, Ruff correcto y fuentesmanifest11intactas; no producto/benchmarks nuevos. Decisióncondicional: consumidorescompletos+conteoestructural+costebasepuro antescandidatarutasprivadas; cortes70%/101755dicts/overheadrestado rechazados. Campaña posteriorNOejecutada. [Sala y uso](salon-deliberacion-local.md), [acta y límites](evidencias/mod08-salon-deliberacion-20261011.md). MOD08generalpausado/objetivos2s5spendientes.


MOD08 2026-10-11 usuario «Procede pues con lo que se propone»: autoriza campaña diagnóstica de consumidores y baseline puro acordada en sala. Fuentes HEAD7e04016 más cuatro archivos nuevos test-only capacity_scalar_diagnostic.py/capacity_scalar_wsgi.py/test_capacity_scalar_diagnostic.py/test_capacity_scalar_consumers_http.py. Fixture1500revisiones/selección16MiB/originales64MiB/cobertura parcial;31lecturas aprobadas reales+64POSThistoria548eventos. PG17/Redispropios/runtimeLOGIN/Gunicorn2sync/clonesidénticos,warmambosworkers. TresPOSTcontrol-spans-control;cuartoPOSTcount separado sin usar sustiempos. Ocho targets de consumidor, sincProfile/SQLhook/per-next;conteos de aliasroot sin parchar definiciónrecursiva pública. Baselineoriginal A/A ABBAx5=20muestras/operación,tresoperaciones,2warmups descartados,GCfuera timer;corpus materializado originalsinJSONnormalización. Nuevecasosunitarios de instrumentación/errores/gen/profundidad másHTTPreal;historiay4reads+8eventos verificadas porcommit. Cierre: terminal,huellas/retirada propia,tabla/costos/perímetros ydecisióncondicional;sin candidata/producto/p95contractual/89min. Fuentes congeladas durante runner, timeout900s/unworker.

Primera campaña consumidores20261011-133814-09f90cce TERMINAL ERROR:8PASS1FAIL0errores/skips94,805sJUnit,fuentes congeladas/retirada PGRedisGunicorn propia comprobada. Fallo test-only al prepararpunteros despuésHTTP porvariablebodyocultadaporfunciónPOST; no resultadofinaldebaseline puro. Renombrada request_body trasterminal; tambiénsecompleta corpus ancho256/profundo64/escapes conA/Aoriginal,fuera integraciónHTTP. Selección corregida9unitarios+1HTTP=10casos (pre-registro9unitarios erainexacto,eran8). Nuevo runner mismoslímites/fixtures/controles, condiciónsalidaigual, timeout900/unworker. Negativa previa conservada,sin cambiosproductivos.

Consumidores/scalar campaña TERMINADA20261011-134116-08cc3941:10PASS0fallos/errores/skips112,021sJUnit,1208entradasfuentes exactas antesdocumentar,retiradaPGRedisGunicorn propia independiente. TresTCPcontrol/spans/control1645,055/1664,316/1620,490ms,dosPIDsmedidos/GCdiferente;sinprofiler/SQL/per-nexthooks,no restaroverhead nip95. ConteoHTTPseparado:compile1502raíces27163hojas,page4raíces108hojas;sourcecopy1,project2,compile1,pages4,otrosconsumidoresnoobservados. SpansCPU:source251,397ms/compileexcl31,275ms/projectsum64,789ms/page0,407ms;no asignaciónCPUORM/recorridopuro. BaselineoriginalA/A20muestrasporoperación:conjuntosrutas23,059ms/conteo21,001ms/4501punteros6,305ms,preparaciónfuera;corpusancho256/profundo64/escapesynegativas/gen/RecursionError cubiertos. No ahorro ni comparaciónvariante ni extrapolacióncontractual. Decisión:costeobservadomodesto,no candidataproductivaenestacampaña,cerrar diagnóstico,fuenteconstrucciónmayor sinatribuircausa. Negativa8PASS1FAILbodyfunciónpreservada;corregidotrasterminal,ambosrecursospropiosausentes. [Informe y límites](evidencias/mod08-scalar-consumers-20261011.md)/[muestras](evidencias/mod08-scalar-consumers-20261011.json). ResultadosañadidoscomoCodexalregistrocomún,sin llamadas externas nuevas. MOD08generalpausado/2s5sdoscasosN3pendientes.


MOD08 2026-10-11: nueva deliberación solicitada, sala mod08-siguiente-20261011 cerrada con opiniónClaude yNotebook válidas y negativaNotebook extensa conservada. DecisiónCodex: sólo siguiente bloque20controlesA/A, unworkersync, hashes/fixture/clones/commit/frescura preservados; compuertaheurística10% dispersión/derivaTCPyCPU predeclarada. No nueva campaña ni producto ejecutados, no causa del factor2 demostrada; fases futuras condicionadas y sin cacheautoridad. [Plan y objeciones](evidencias/mod08-siguiente-plan-20261011.md). MOD08general continúa pausado y aceptación pendiente.


## Contrato del próximo goal de investigación de rendimiento — 2026-10-11

El usuario solicita condiciones de continuación y salida para evitar un callejón sin salida.
Este contrato define el próximo goal; no activa todavía el runner ni reanuda MOD08 completo.
Objetivo propuesto: determinar y verificar una vía viable de optimización del request,
conservar sólo mejoras demostradas y entregar un dictamen final con evidencia. Puede
concluir con una mejora validada o con un diagnóstico justificado de las vías agotadas;
ese segundo resultado no significa cumplir los objetivos de rendimiento ni aceptar MOD08.

### Entrada y primer bloque

Aplicar el [plan de estabilidad acordado](evidencias/mod08-siguiente-plan-20261011.md):
20 controles A/A y dos warmups descartados, un worker sync, clones equivalentes,
PostgreSQL real, código y fixture congelados, autoridad fresca y auditorías comprobadas.
Los umbrales de dispersión y deriva del 10% son compuertas diagnósticas predeclaradas,
no aceptación contractual. El escenario de un worker no sustituye el escenario completo.

### Decisión al terminar cada ciclo

| Resultado | Acción |
| --- | --- |
| Medición inválida, fixture desigual o instrumento defectuoso | Conservar negativa, corregir únicamente el defecto identificado y permitir una repetición correctiva. Un segundo fallo del mismo bloque cierra esa vía como inconcluyente. No repetir buscando una cifra favorable. |
| Controles válidos pero inestables | No comparar candidatas pequeñas. Sólo abrir un bloque correctivo si se identifica una hipótesis comprobable con acción concreta y reversible; si falta o la corrección no estabiliza, cerrar esa vía. Correlación no es causalidad. |
| Hipótesis refutada o candidata sin beneficio distinguible del ruido | Revertir sólo los cambios propios de la candidata, conservar resultados y volver a deliberar únicamente si surge una hipótesis distinta y comprobable. |
| Beneficio reproducible, pero seguridad, frescura o integridad fallan | Rechazar y retirar la candidata. Deliberar sobre una solución diferente que conserve las garantías; nunca rebajar el contrato para conservar la mejora. |
| Mejora reproducible y verificaciones pertinentes correctas, objetivo aún pendiente | Conservar como mejora parcial con su alcance, actualizar el presupuesto de latencia observado y deliberar sobre el cuello restante. No declarar aceptación total. |
| Objetivos contractuales y verificaciones completas satisfechos | Cerrar con éxito técnico y evidencia revisada, dentro de la topología y criterios vigentes. |

Cada deliberación recibirá código exacto, resultados positivos y negativos, conjeturas,
objeciones de Codex y vías ya descartadas. Claude y NotebookLM son revisores: su acuerdo
no constituye evidencia. Si un revisor falla, no se relanza automáticamente ni se bloquea
una decisión sustentada por pruebas; se explicita la ausencia de esa opinión.

### Presupuesto y condición de no progreso

Primera ventana: hasta tres ciclos de investigación después del bloque de estabilidad.
Un ciclo exige una hipótesis, un experimento acotado y una decisión; no se cuentan respuestas
de modelos como ciclos. Máximo cuatro solicitudes externas por ciclo. Antes de ejecutar,
registrar muestras, timeout, recursos propios y criterio de descarte; no expandirlos a
posteriori para obtener un resultado favorable. Una corrección del arnés consume el
presupuesto de repetición del bloque y no permite reiniciar la ventana.

Progreso significa beneficio reproducible o evidencia nueva que elimina una incertidumbre
nombrada y cambia la siguiente decisión. Reformular la misma propuesta o repetir perfiles
sin una pregunta nueva no es progreso. Dos ciclos consecutivos sin progreso, tres ciclos
agotados sin una vía viable, o ausencia de una nueva hipótesis falsable cierran la ventana
con un informe de hallazgos y pendientes; no se abre otra automáticamente. Una continuación
requiere un cambio concreto de alcance, entorno, mecanismo o información, decidido por el
usuario, no simplemente más deliberación.

### Interrupción y cierre seguro

Una pérdida de aislamiento, uso accidental de datos reales, deriva de fuentes durante
una medición o riesgo de dañar trabajo ajeno obliga a detener la campaña afectada,
conservar evidencia y retirar únicamente recursos propios. Nunca publicar, contratar,
modificar infraestructura compartida ni ampliar permisos para desbloquear este goal.
Si la única vía requiere cambiar garantías, proveedores o criterios contractuales,
terminar la investigación con ese requisito explícito y dejar la decisión al usuario.

Un impedimento externo sin acción local útil se documenta sin relanzamientos. El estado
`blocked` del goal sólo se establece después de la misma condición en tres turnos
consecutivos, conforme al control de goals; no equivale a aceptar el trabajo. `paused`
requiere petición explícita del usuario. `complete` sólo corresponde al objetivo realmente
alcanzado: un dictamen de investigación acotada puede estar completo con rendimiento aún
pendiente, pero un goal de aceptación de rendimiento no puede marcarse completo por agotar
la ventana. El contrato del goal activo deberá distinguir esos dos objetivos.

Al terminar: no runners ni procesos propios abandonados, candidata fallida retirada,
cambios del usuario preservados, evidencias y consumo conservados, estado de cada prueba
y limitaciones claros. No prometer que una mejora de un microbenchmark resolverá el p95.


Goal investigación MOD08 ACTIVADO por adjunto del usuario 2026-10-11: ejecutar contrato acotado anterior, preservando límites y sin reanudar aceptación general. Primer bloque estabilidad original20POST+2warmups, unGunicornsync, PG17/Redisprivados/runtimeLOGIN/fixture1500revisiones16MiBhistoria548EVENT256reads, clonidénticopormuestra,4reads8eventscommitverificadoantes/después. Nuevos tests capacity_stability.py/capacity_stability_wsgi.py/test_capacity_stability.py/test_capacity_stability_http.py; helperclone_server sólo añade workersopcionaldefault2preservado. Kernelcanónico native-sealed comprobadoenworkerfuera reloj; crypto.unseal sigueFernet+json,noinventarbackendnativounseal. No cProfile/SQL/per-nexthooks ni spansinternos/GCforzado. RSS/loadavg/PGstatslectura fuera reloj; TCPincluye telemetríapreviaworker, WSGIexcluye esa lectura y reporte posterior, límites publicados. Compuerta10%spreadP90-P10y10%derivaprimeras5/últimas5paraTCPyCPUthreadconcuantileslineales,reportarnoassertpassdelacompuerta. Timeoutrunner900s, unpytestworker, fuentescongeladas, sinotra carga propia. Evidenciaesperada3unitarios+1PGHTTPreal, samples/gatebackend/GC/PID,huellas/retiradaindependiente y deliberaciónposterior. Una repeticióncorrectiva permitida si defecto específico; no repetirporinestabilidad.


Estabilidad goal TERMINAL20261011-141107-bc244cec:4PASS (3unitarios+1PGTCP real),1231fuentesexactas,retirada propia PGRedisGunicorn verificada.20controlmedidos+2warmups unworker/kernelcanóniconative-sealed/historia548eventos256reads idéntica ycommit4reads8eventsverificados. MedianaTCP1556.081msCPU877.342ms;spreadTCP8.064%CPU11.824%,deriva1.381%/1.684%. CompuertaNOsuperadaCPU; no cambiar10%ni repetirbuscandoPASS. GCgen2variable,costeno medido/correlaciónnocaudal. Deliberaciónsiguiente sólo decidir nueva hipótesiscomprobable o cierrejustificado;producto intacto. [Datos](evidencias/mod08-stability-20261011.json).


Goal investigación acotada MOD08 — DICTAMEN FINAL2026-10-11: bloque20controles válido4PASS pero compuertaCPUFAIL11.824%>10%. DeliberaciónrealClaude/Notebook, negativaqueryextensaconservada yreducciónmanual válida; Claude rectifica tras código sincopiasintermediasdemostradas. Salida porausenciade nueva hipótesisoptimizaciónaccionable; no consumir3ciclosporobligación, ningúncicloproductivoposterior. GCgen2correlaciona77mspero duración/causahistórica desconocidas; nofreeze/desactivarGC/cambiarumbralesni perfilesporcuriosidad. Producto intacto,1231huellas verificadaspre-documentación,recursos propiosausentes. [Dictamen y auditoría](evidencias/mod08-goal-investigacion-20261011.md). Resultadoinvestigacióncompleta,no aceptaciónMOD08ni rendimiento2s5s. Reapertura requiere evidencia/mecanismonuevo, no automática.


## Reapertura por beneficio parcial — instrucción posterior 2026-10-11

El usuario indica: «Pues si no encontrais ninguna suficiente rebajais el requisito para
intentar encontrar una solucion». Se rebaja el beneficio mínimo esperado para seleccionar
una candidata: no necesita resolver por sí sola la brecha de segundos. Son admisibles
mejoras pequeñas, incluso de milisegundos, y mejoras parciales acumulables verificadas.
Esta interpretación se refiere al tamaño del beneficio, no modifica los objetivos
contractuales 2s/5s ni seguridad, frescura, integridad, privacidad, auditoría o completitud.
El goal anterior permanece cerrado con su evidencia; esta autorización justifica una
nueva vía parcial y no reclasifica la compuerta histórica negativa.

Reglas de selección y aceptación posteriores:

1. Una candidata requiere mecanismo concreto, código localizado y comparación acotada;
   ya no se descarta sólo porque su coste sea modesto frente a la brecha total.
2. Si el efecto pequeño no se distingue del ruido del request, medir primero la etapa
   pura con corpus representativo, equivalencia y muestras originales/variante
   intercaladas. Registrar también comportamiento adversarial y coste de memoria.
   Un beneficio en esa etapa no acredita una mejora de TCP ni del p95 contractual.
3. La compuerta histórica CPU 11.824% sigue siendo negativa. No elevar el 10%, eliminar
   muestras, restar GC ni hacer pasar una comparación inconcluyente. Su fallo no prueba
   que cualquier comparación de una etapa independiente sea imposible.
4. Adoptar una mejora de etapa sólo si es reproducible, conserva semántica y garantías,
   y supera las verificaciones del recorrido afectado. Declarar por separado beneficio
   de etapa, resultado HTTP y alcance pendiente; no sumar microbenchmarks como ahorro
   total garantizado. Si empeora el request o recursos relevantes, rechazarla.
5. Conservar presupuestos finitos, evidencia negativa y retirada de recursos propios.
   Si no hay beneficio medible, cambiar de mecanismo o cerrar esa vía. No reducir
   exigencias de evidencia para convertir un resultado dudoso en mejora.

Primera candidata que vuelve a ser elegible: recorrido privado que produce sólo rutas
para compile_coverage, que actualmente consume diccionarios scalar_fields sólo para
extraer leaf['path']. El coste original de conjuntos de rutas (~23ms en el corpus previo)
no es ahorro esperado; hace falta medir original/variante. La API pública scalar_fields,
los valores/punteros, la autoridad y las lecturas frescas deben conservarse. Elegibilidad
no equivale a implementación, equivalencia ni aceptación. La lectura concreta del
consumidor y el diseño se harán antes del experimento; no ampliar la API por conveniencia.


Mejora parcial goal ciclo1PRE-REGISTRO2026-10-11: Claude yNotebook opinionesválidas recibidas con código/metodología/nuevoumbrealmodesto. Candidatarecursivaprivada_scalar_paths módulo rights_portability_paths.py y única comprehensióncompilecoverage (no set(gen), conservarframe/RecursionError);scalar_fields público/pointervalues/freshautoridad/auditoría intactos. Nuevas12pruebasdiferencialespermanentesincluyen250árbolesrandomdeterministas,customitems/claves/vacíos/subclasses/erroresparciales/generator/mutaciones/ciclos y barridoprofundidad90nivelesenbordeCPython3.12.15. ASTbaselinecompletoigualHEAD ycachefncompiladaantesclocks(warmupdescartado) noautoridadmemo;aliasesoriginal/actualsimétricosyrestauraciónlateenerror comprobadas. Instrumentoconteoprevioreconocenuevoconsumidor,aliaspúblicoconservado.24controleslocalesPASSantesgate (noPGclaim).
BateríaN2afectadaPGreal/Redispropios/unpytestworker,runner900s/native-sourcepropio. Fixture1500revision16MiB/historia548eventos256reads,1Gunicornsync,2warmups(1porvariante)+40HTTPABBAx10(20porvariante),clonidéntico/normalcommit4reads8events/ownerbeforeafter/GCsin tocar/kernelcanóniconative-sealed. HTTPsinprofiler/SQL/spansinternos,setupscopesfueraWSGIperoTCPloincluye;scan/restauraciónigualambosmodos. Despuésservidorterminado comparaciónpureoriginal20/candidata20ABBAx10+2warmupsporvariantefueraDB,corpusmaterializadoreal+edgeancho256/deep64/escapes;ordenresultadosidénticos comprobadosfuerareloj. Memoria5porvariante tracemallocSEPARADA:picovivonoallocstotalesni dictstemporalesacumulados.
Aceptaciónetapapredeclara:almenos15/20parejaspositivasenwallYCPUy4bloquescronológicosmedianaspositivasenambos;picomedianavariant<=original*1.05+1024bytesheurísticarecursos,no significaciónformalnip95. No beneficioabsoluto mínimo. Request40muestras no prueba noninferiority ni mejora de pocosms:reportar mediana/p95muestral/parejas/bloques/GC, rechazar si>=15/20parejaspierdeTCPy4bloquesmedianospeores,o degradaciónmedianaYp95>5%(señaltriagepredeclarada,noumbrealcontractual). SiHTTPinconcluyentesóloaceptacióndeetapa, límitesexplícitos/objetivos2s5spendientes. Ningunafirma/autoridadomitida ni invocaciónClaudeeditora. RamaspreviousFAILsconservadas. Fuentescongeladas mientrasrunner, no cargaspropiasparalelas. Condiciónsalida:terminal/huellasyretiradaindependiente,resultadosy2opinionesfinalescierre;rechazoretirarsólopatchpropio,no repetirporbuscarPASS.


Mejora parcial ciclo1 TERMINADO20261011-145141-3ea7872c:126PASS0fallos/errores/skips885.979sJUnit<900s,1275fuentesexactasantesdocs/retiradaPGRedisGunicornindependiente. Pure1502rows27163hojasoriginalmed20.391ms→paths17.589ms;20/20parejaswallCPUy4bloquespositivos;medianapareada2.943/2.938ms;edge259hojas tambiénPASS. Pico5706vs5698Bsin beneficio memoria significativo;tracemallocseparadonoallocsacumuladas. HTTP20pormodo med1626.673→1621.596/p95muestral1693.458→1687.279mspero12/20winsúltimobloquenegativo:beneficioHTTPINCONCLUYENTE,noequivalencianoninferiorityformal/2s5s. Precriteriosregressiontriagenoactivados, compuertaCPUanteriorFAILpreservada. DosopinionesClaude/dosNotebookvalidas(consumoregistrado) noPASS. CodexADOPTAmejoraETAPA~3msbajoinstrucciónposteriormejora pequeña;APIpública/digests/autoridad/frescura/auditoríaintactos,oraclepermanenteCPython3.12.15yN2afectado. [Evidencia/alcance](evidencias/mod08-small-paths-20261011.md). Goalcontinuaciónentregaparcialverificada,noMOD08completo;no nuevas pruebas por rutina ni fuentesNotebookañadidas.

### Continuación autorizada: diagnóstico de esperas — 2026-10-11

Usuario: «Procede con lo que hay que hacer en orden y adaptate a las necesidades».
Prerregistro: aislar llamadas psycopg execute/fetchone/fetchmany/fetchall, apertura real
de conexión y Pipeline.sync/__exit__ por fase source/validate_assessment y cadena.
Sin profiler, SQL nuevo, cache de autoridad ni cambios productivos. Un worker propio,
mismo fixture sintético 1500 revisiones/16MiB y 548 eventos, clones equivalentes,
dos warmups y cuatro controles alternados con cuatro observaciones. Timeout runner420s,
petición120s; una corrección de arnés como máximo, sin repetir para perseguir mejora.
Pruebas: tres controles de forwarding/restauración y una integración PostgreSQL/TCP
con commit verificado independientemente (ocho eventos/cuatro lecturas por petición).
Fuentes congeladas por runner; kernel native-sealed y PostgreSQL/Redis propios.
Decisión: localizar un coste repetido observado en las cuatro muestras antes de proponer
una candidata. Execute/fetch/sync son tiempos cliente inclusivos; no equivalen a red
o CPU del servidor. No sumar spans solapados. Si ninguna incertidumbre se resuelve,
registrar resultado negativo y detener esta vía; revisión Claude/Notebook posterior
sin ejecución competidora durante la medición. Objetivos y garantías intactos.

Diagnóstico inicial terminal runner20261011-152912-82f64983: 4PASS193.74s.
La inspección del MRO real detectó ServerSideCursor/ServerCursor con overrides execute
y fetch no cubiertos; source incompleto y no usado para concluir. Captura preservada
en evidencias/mod08-wait-initial-20261011.json. Única corrección autorizada del arnés:
incluir implementaciones propias ServerCursor sin duplicar métodos heredados, prueba
de restauración y aserción de al menos1500 filas observadas en source.fetchmany.
Mismas ocho muestras/timeout420s; sin modificaciones productivas ni ampliar presupuesto.

Diagnóstico corregido runner20261011-153333-078ab072:4PASS196.69s,1290hashes
independientes exactos antes de escribir documentos, limpieza verificada. Fuente
wall286–325ms/fetch155–185ms; cuatro validate_assessment193–206ms/pipeline69–74ms.
Claude recibido; Notebook largo inválido preservado, reformulación manual breve
recibida. No candidata productiva sustentada. Defer geográfico propuesto no aborda
1500revisiones conFKgeográficasNULL; sin cambiar fixture para favorecerlo.

Segundo ciclo prerregistrado: separar métodos ServerCursor de Cursor y medir
Revision.from_db (constructor/hidratación) para decidir si proyección de filas
eliminaría CPU observada o si hay que investigar espera de fetch. Misma4+4/doswarmups,
timeout420s/POST120s/recursospropios. Sin nuevo SQL ni cambios productivos ni profiler.
Criterios instrumentales:server_fetchmany3llamadas con[1000,500,0],Revision.from_db1500
por request; identidad kernel worker native-sealed/manifest igual en8muestras.
No usar70%/125ms ni supuesto techo16MiB del notebook como contrato o regla de descarte;
no declarar plataforma agotada por predominio de fetch. Beneficio sólo tras candidata
y comparación propia; dos ciclos sin nueva incertidumbre resuelta cerrarían esta vía.

Segundo ciclo terminal runner20261011-154421-99415089:4PASS193.91s,1307hashes
exactos. Serverfetch revisiones139–149ms;22fetch cliente relaciones/resto<1ms;
1500Revision.from_db25–29ms. Kernel native-sealed/manifest igual8requests real.
No optimizar fetch relaciones como cuello; hidración ahora es coste observado pequeño.
Claude revisión final recibida: ensayo defer7camposunusedRevision razonable condicionado
a no save/clone/clean/serializarinstancias. Inventario:source_copy sólo construye dicts,
batches asigna copy_* y usa pk;contact_data phone/whatsapp;image_inventorycopy_photos;
Revision no overrides y no init receivers. Instancias no salen delsource.

Tercer ciclo prerregistrado (último de esta ventana):sin modificarproducto, comparar
constructorDjango real original/defer7 sobre1500filas sintéticas predecodificadasPG.
Obtener init_list/values delquerysetreal original y delquerysetdefer candidato fuera
reloj;verificarattrsconsumidos/camposdiferidos. Columnas omitidas:source_revision,step,
edit_version,telegram,contact_exposure_accepted,publisher_acceptance,updated_at.
Conservarlisting_id,manager_version y todasgeoFK. A/A20paresABBAx10 yA/B20paresABBAx10,
2warmups por etiqueta, sin spans/profiler/SQL/GCforzado dentro reloj. GateA/B>=15/20
wallCPU y4bloquespositivos; A/A debe5<wins<15 ambos relojes, regla triage no pvalue.
Timeout120s,1pytestworker,PGRedisprivados,nativa propia. Si falla gateconstructor,
rechazar esta candidata sin runHTTP y cerrarventana; no afirmar que fetch no mejoraría
ni descartar otrasrutas globalmente. SiPASS, exigir equivalenciaSource/N2/HTTPpropio
antes integrar. Mediciónconstructor consume1objeto a la vez, no memoria batchservicio.

Microconstructor terminal20261011-155320-446ba755:1PASS39.964s,1312hashes exactos.
GatebeneficioPASS17/20wallCPU,4bloquespositivos;A/A12/20ambos neutrosegún triage.
Medianas original19.537ms/candidata17.470ms:2.067ms(~10.58%) etapa sólo.
Corrección inventario: síexiste receiverglobal post_init rights_validation_seal._loaded;
lee __dict__/fields_cache para EXPIRY_FIELDS(expires_at,receipt_expires_at,valid_until),
ninguno omitido enRevision. No negar existencia delreceiver; ambosmodos lo conservan.

Aplicación provisional fuente rights_exports.py única expansión defer7campos;
no retener hasta equivalencia/N2/HTTP. PrerregistroN1:ASTbaseline==HEAD función completa,
restauraciónaliasesfallo,Sourcecopyfixturecompleto original/candidata canonicaligual,
mismanconsultas/params,SQLsólocambian columnasSELECTprincipal/OFself igual,updated_at
de todasrevisiones intacto. Timeout120s,PGRedisprivados,nativo,selec3tests equivalencia.
PrerregistroHTTP/N2 trasN1:40POST ABBAx10(20variante) +1warmup cada,1Gunicornsync/
clones548eventos/256reads/commit+8/+4;kernelmanifestigual;sinprofiler/spans/SQLwrapper
dentroHTTP. Mismo triageregresión que mejora rutas:rechazar>=15/20parejasTCPpeores
y4bloquesnegativos, o mediana y p95 ambos>5%peores. No prueba noinferioridad formal.
Criterio conservarbeneficioparcial:microPASS/equivalencia/N2PASS,sin triageHTTPregresión;
HTTPbeneficio sólo si>=15/20parejasfavorablesTCPyCPU+4bloquespositivos. No sumar
2ms a p95histórico ni cumplir2s5s por topología reducida. N2timeout900s,1pytestworker.

N1equivalencia terminal20261011-155855-a0872543:3PASS35.21s,fuentes exactas
independientemente comprobadas antes registro, recursos retirados. Fuente canonical
idéntica/SQLnparamsiguales/único cambio columnasSELECTprincipal, OFself igual, no
updated_at modificado. ASTbaselinecompleto==HEAD/restauraciónaliasfalloPASS.
N2 selecciónconcreta anteslanzar:equivalencia3;exports(HTTP/móvil/descarga/concurrencia),
source_fingerprint(completitud/mutación/carreras),inspection_source_unit,validation_seal,
validation_seal_pipeline,enforced_validation_seal(loginPGreal/S3propio),coverage_batch,
coverage_races,coverage_review_http/mobile yrevisionHTTP20pares. Timeout900s fijado,
fuentes congeladas,noprocesos de modelosniotrobench competidor. Sinrunconstructor
repetido ni aceptación global/p95contractual por esta batería.

N2terminal20261011-160045-77fc3354:ERROR por timeout900s, noJUnit terminal,
no aceptar puntosdeprogreso comoPASS. DosE visibles; colección readonly124nodes
identifica candidates test_held_seal_rechecks_external_object_bytes y
test_enforced_held_seal_still_rejects_real_external_object_corruption, ambosfixture
S3real. RecursosPGRedis ausentesverificados, inventarioobjecttests vacío. No
aumentartimeout retrospectivo ni reabrirmuestrasHTTP incompletas como válidas.
Diagnóstico afectado separado:dosnodesS3 yHTTPcompleto20pares enPGpropio,timeout420s;
recuperar detalle errores y decidircorrección antesretenercandidato. Otraspruebas
terminadasdentrotimeout sinJUnit no se cuentanformalmente.

Diagnóstico afectado terminal20261011-161740-abbc2d44:1PASS(HTTP40muestras),
2ERROR(S3fixtureDocker--pullnever exit125),258.61sJUnit,1316hashes exactos antes
documentar. Imagenrustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c
ausenteenDocker confirmada coninventario. No modificar guardas/fixture para
evitar S3real;preparar imagen fijada y repetir2nodes. HTTPterminado baseline
1691.390→1678.776msmediana,p952079.933→1815.411ms;11/20parejasTCPyCPU, bloques
TCP58.706/109.234/14.039/-6.876ms; beneficioHTTPinconcluyente, no triageregresión.
JSONcompleto revision-http preservado. No usar p95 aislado favorable para aceptación.
Elintentoglobal900s sinJUnit sigueERROR, no reconvertido enPASS.
Para completarN2sobre mismaversión se dividirá selección por recursos: fuente/HTTP
yhuellas, sellos/pipeline+enforcedS3, cobertura/batch/carreras/móvil. Mismos tests
requeridos sin descartarnodes fallidos;splitporcostefixture evita quecasoHTTP
compitalímite900 con124tests. No repetirbenchmark ya terminal; sólo suites sinJUnit
yS3tras preparar dependencia. No subirtiempo/recursos delensayoHTTP ni nuevasmuestras.

DependenciaRustFS preparada correctamente mediantepull deldigestexacto ya fijado;
sin cambiarfixture/guardas ni comprarproveedor. HTTPya terminal1PASS no se repite.
Adaptación operacional de repeticiónN2:usar pytest-xdist3workers/loadfile soportados
por runner/MOD08 para suitesdecorrectitud restantes, PGdb/media/Redisnamespacepropios
porworker. No sonworkersGunicorn ni aceptación decapacidad;HTTPanterior mantiene1.
Se conserva timeout900s y todos los123nodes deN2sinHTTP(incluye2S3fallidos),
misma fuenteproductiva congelada. No excluir ni reconvertir intento900s previo.
Memoriahostavailable7.7GiB antes arranque, sin benchmark/modelCLI concurrentes.
Seleccionar12filesanteriores salvobenchmarkHTTP ya completado. Cierre sólo tras
JUnit terminalsinfallos/errores/skips y revisión de mismo códigoactual/limpieza.


### Cierre del ciclo de esperas/proyección — 2026-10-11

Runner `20261011-162456-8718be57`: 123 PASS, cero fallos/errores/skips (PostgreSQL y RustFS reales; tres workers de corrección aislados). Auditoría independiente de 1316 huellas sin diferencias antes de documentar. Se conserva la proyección diferida de siete campos no consumidos de Revision: construcción 19,537191→17,470186 ms (2,067006 ms; 10,58 %), A/A neutral y 17/20 victorias A/B. HTTP de veinte pares: mediana 1691,390432→1678,775960 ms pero sólo 11/20 victorias; resultado inconcluso, sin activar descarte por regresión. El intento serial agotado y los dos errores previos por imagen RustFS ausente se preservan como ERROR, no PASS; dependencia fijada preparada y ambos casos repetidos satisfactoriamente. No se modifica el objetivo ni se declara aceptación MOD-08. Sala acotada cerrada; siguiente investigación necesita una nueva hipótesis sobre fetch/adaptación principal, sin caché de autoridad. Evidencia: [diagnóstico y decisión](evidencias/mod08-wait-revision-20261011.md).


### Nuevo diagnóstico autorizado: fases completas y adaptación del fetch — 2026-10-11

Usuario: «Procede con todo lo que haya que hacer». Hipótesis pendiente: separar adaptación de filas del fetch principal y localizar el mayor coste del recorrido actual antes de otra candidata. Instrumento sólo tests: inventario fijo de 19 fases, driver previo y proxy reversible de Transformer en ServerCursor._fetch_gen (mismos argumentos, retorno y generator throw/close); captura sólo contadores. No altera fuente productiva, llamadas frescas, bloqueos, GC, cifrado o protocolo. Dos tests de forwarding/restauración y una integración TCP PostgreSQL: 1500 revisiones/16 MiB, historial real 548 eventos/256 lecturas, cuatro controles alternados con cuatro instrumentadas, dos calentamientos, 1 Gunicorn sync, clones privados y commits +8/+4 comprobados independientemente. Sin profiler ni aceptación contractual. Timeout420s, fuentes congeladas. Éxito exige instrumentar 3 adaptaciones, 1500 hidrataciones y 4 páginas y limpiar recursos; fallo permite corregir el instrumento tras terminal, no aceptar medidas incompletas. Después deliberación acotada sobre datos reales; no aplicar una candidata sin equivalencia y beneficio demostrado.

Primer intento 20261011-164311-29fd15f5 terminó ERROR en Ruff por orden de imports del instrumento, antes de pytest; no pruebas acreditadas. Imports corregidos tras terminal. Repetición con idéntico prerregistro, fixture y timeout.

Diagnóstico completo terminal 20261011-164325-0f8daba0: 3 PASS en 103,65s; 1323 huellas independientes exactas. Nueva adaptación directa del fetch: 9,874–14,753ms wall; fetch completo 74,660–91,396ms. Controles TCP 791–869ms, sustancialmente distintos de tandas previas sin cambio productivo: no atribuir esa bajada a optimización. Usuario dirige siguiente trabajo a cambio de enfoque y brainstorming con investigación web de cada participante. Se habilita modo explícito web-only de Claude en sala nueva por su instrucción posterior, sin herramientas locales, escritura ni delegación V1; pruebas de controles pertinentes antes de invocar. Notebook investigación web sin autoimportar. No benchmark compitiendo con investigación; prueba anterior ya terminal.


Prerregistro del filtro arquitectónico posterior al brainstorming: dos pruebas nuevas de PostgreSQL real, sólo tablas/funciones temporales propias, sin producto. (1) función IMMUTABLE suplantada al escribir columna GENERATED, restaurada después: mismo prosrc/head/digest almacenado pero hash físico fresco distinto. Refuta confianza ingenua en digest derivado/counter; no modifica tablas reales de evidencia. (2) mil tuplas observadas antes/después de VACUUM FREEZE/REINDEX; ALTER ADD COLUMN fast-default conserva metadata pero cambia JSON de fila genérica (no afirmar source_copy estática consume columna añadida). No prueba wraparound de 32 bits ni seguridad del manifiesto. Añadir dos pruebas existentes de runtime: owner drift y alteración permitida de fuentes detectados por verificación física, PostgreSQL/Redis propios, timeout180s, 1 worker, código congelado; ejecutar tras última llamada externa terminal para evitar diferencias en artefactos de fuentes. Gate es filtro de riesgos, no rendimiento/aceptación MOD08.

Filtro inicial 20261011-170211-4c4e4320: 3 PASS/1 FAIL en14,99s, no PASS global. Fallo del arnés al tratar to_jsonb como dict: backend Django entrega JSON textual al cursor crudo y la conversión JSONField ocurre más tarde. No fallo productivo. Parseo explícito json.loads corregido tras terminal; repetir misma selección4/timeout180s. Contraprueba generated_digest y ownerdrift ya ejercidas pero no sumar versiones como gate.


Ensayo de viabilidad de datos posterior al filtro4PASS: prototipo sólo tests, NO candidato productivo ni API de autoridad. 1500 revisiones escalares/16MiB calibrados sin fotos/relaciones; chunks cifrados<=50 en tabla temporal PG y manifiesto firmado(scope/schema/shape/source_digest/fullphysicalstamp/xid64/db/expiry). Antes/después de uso, huella física de TODO el conjunto; descifrado nuevo cada llamada. Comparación de veinte pares ABBA entre inspection_source completo y lectura del chunk (SQL/crypto/guardas de datos dentro del tiempo), dos warmups por variante. Preparación fuera, coste registrado; equivalencia primera/intermedia/última, objetos independientes y rechazo updatefuente/root equivocado/chunk intercambiado/ausente. Gate sólo cribado >=15/20 deltas favorables wall/CPU; no HTTP/SLO. Limitaciones declaradas: no autoridad/proof/latest/chain, catálogoRLS/funciones/enums/restore incompleto, no wrapreal, no purga/fallback durable; no adoptarlo por PASS. Timeout180s/PGRedisprivados/1worker, fuentes congeladas. Si complica semántica o no gana, cerrar esta ruta como negativa; si gana sólo habilita diseño completo y N2 antes de conectar un endpoint.

Prototipo inicial terminal20261011-170851-d0a9ec69: 1 PASS28,78s, mapa independiente exacto; datos preservados como iniciales. Ajuste tras revisión: ligar manifiesto al fingerprint HMAC productivo existente, no SHA256 alternativo de la fuente; así futura integración no exige cambiar source_digest. Ampliar filtro de riesgos con ciphertext inválido, expiración, anchorXID demasiado antiguo(simulado aritméticamente, no wrapreal), contador falso y ALTER fast-default de schema; todo rollback privado. Repetir mismo ensayo20pares180s para versión corregida, sin agregar versiones como gate. Sigue prototipo de datos sin autoridad/endpoints/purga durable y sin aceptación.


### Cierre de investigación web y cribado arquitectónico — 2026-10-11

Claude investigó vía pública únicamente y Notebook deepresearch encontró51fuentes, no importadas; notebook conserva100IDs. Sala cuatro turnos cerrada con errores/correcciones preservados. Filtro de riesgos final4PASS (170322-92aed466) refuta hashes GENERATED/head ingenuos y contrasta FREEZE/REINDEX/fast-default; no rendimiento. Prototipo paginado de DATOS final1PASS34,77s (171059-35a451e6), 1350huellasexactas: misma página50/1500/16MiB, wall199,011898→21,376303ms (177,635595ms;89,26%), CPU118,703060→4,711684ms;20/20pares favorables. Preparación1,752980swall; nueve ataques rechazados en alcance definido. NO APIautoridad, endpoint, fotos/RustFS/Caddy, persistencia/purga/funcionesRLSgrantscompletas o SLO. Fuenteproductiva sin cambios desde mejora previa; no conectar por estos PASS. Se concreta camino de implementación con gatesN1/N2/HTTP y abandonos antes de adopción: [decisión](evidencias/mod08-brainstorm-web-20261011.md). Todos recursos propios retirados/auditados, errores iniciales preservados. No goal nuevo ni aceptación de MOD08.


### Integración paginada autorizada: puerta de contenido físico — 2026-10-11

Usuario: «procede con lo que haga falta para implementarlo probarlo y aceptarlo si realmente funciona». Antes de migración/endpoint: gate de coste del manifiesto con hash físico fresco de todas las filas de las familias de source_copy, además de las comprobaciones del prototipo. Es una condición necesaria de igualdad de contenidos, no catálogo/permisos/bloqueos/retención completos. Hash de Revision excluye sólo los ocho campos ya diferidos; demás familias incluyen todas las columnas. Hashes se calculan en PostgreSQL sin transferir cuerpos. Se conserva baseline inspection_source real, preparación separada, misma página50/1500revisiones16MiB, dos calentamientos,20paresABBA, sin profiler/GC ni servicios ajenos. Lectura de páginas incorpora contenido físico antes y después; equivale a una estrategia fuerte distinta del atajo xmin/ctid. Gate descriptivo >=15/20 victorias wall y CPU y cuatro bloques positivos, mediana mejor; de fallar, descartar esta forma antes de crear persistencia. De pasar, continuar API paginada explícita y garantías pendientes: no aceptación automática. Un test PostgreSQL nativo, timeout180s/1worker, fuentes congeladas. Reportar cualquier ERROR separadamente y preservar intentos.

Puerta física terminal20261011-185510-406302c8:1PASS66.361s, fuentes sin cambios según runner, recursos propios retirados. Medianas fuente404.3473115ms/página352.5235205ms; delta51.823791ms12.82%,19/20wall20/20CPU, cuatro bloqueswall51.918/61.198/35.698/39.812ms positivos. Preparación1785.431438ms. Entorno tiene tiempos distintos de la tanda previa: comparación sólo paired actual, no suma/resta a p95histórico. Test detecta update físico. No endpoint ni aceptación.

Segunda puerta antes de integrar: consumidor ordinario actual requiere fuente completa. Implementar carga masiva cifrada de los30chunks en una consulta, descifrar manifiesto una sola vez y header cifrado separado, verificar contenido físico fresco antes/después y conservar inspection_source original con sus HMAC/deriva/mutación completos. No repetir30guards por chunk. Se mide límite inferior de coste: todavía faltan locks/catálogo/expiraciones/permisos, que añadirían trabajo; no entregar esta vía incompleta. Mismafixture/ABBA20pares/warmups/180s/1worker/kernel. Equivalencia páginas0/14/29 y mutabilidad independiente, fuente completa antes de retornar mismo50filas. Si no hay mejora consistente o regresa mediana>=5%, rechazar integración directa que mantiene contrato de dict completo; no convertir este resultado en imposibilidad universal de un rediseño. SiPASS, continuar contrato explícito paginado y N1/N2/HTTP, no aceptar.

Puerta de consumo terminal20261011-185923-110820be:1PASS73.889s,0fallos/errores/skips. Auditoría independiente1357huellas exactas antes de documentación, procesos y PG/Redis propios ausentes. Funcionalmente las páginas comparadas y objetos independientes coinciden; rendimiento RECHAZADO: fuente411.6953005ms frente manifiesto materializado649.770997ms (+238.0756965ms,+57.827%);0/20victoriaswall, CPU235.5106105→238.620325ms. Esto conserva los HMAC completos/guardas de mutación de inspection_source; faltan todavía locks/catálogo/expiraciones del proveedor alternativo, por lo que su coste es un límite inferior, no integración segura. No conectar ni aceptar. El primer ensayo de50filas no prueba este contrato. Se descarta la integración directa de manifiesto+dict completo; no demuestra imposibilidad del rediseño explícito con inventario de referencias/campos y validación sin materializar valores. Esa estrategia sería candidata diferente y necesitaría sus propios N1/N2/HTTP, no aceptar por acuerdo. Producto previo preservado, cero cambios nuevos apps, migraciones o endpoint. Evidencia mod08-page-manifest-integration-gates-20261011.md.


### Deliberación posterior de consumidores — 2026-10-11

Usuario «Adelante» para sala Claude/Notebook tras rechazo integración completa. Cuatro solicitudes: Claude inicial/opinióncorrectiva2éxitos, Notebook1ERRORargumentos inválidos preservado y1éxito tras reducir contexto manualmente. Claude propone ensayo audit-only sin ensamblaroutput, Notebook proponefullchain sin candidata/medidas; no consenso ni PASS. Codex corrige dobledeepcopy,ABpseudoABBA,GCcambiado,source_fingerprintmetadatanocuerpos y ahorrotextos16MiBincorrecto. Próximaúnicahipótesis privadaN1+AA/AB sobrefuenteactualfrío/caliente antes de tocar producto; cerrar si falta beneficio, no inventar siguientechain. Inventario100IDsunchanged, fuentescontextuales exactas yCLIterminales. Deliberación solamente, no nuevoejecutorbench/test ni aceptación. Decisión/gates: [deliberación consumidores](evidencias/mod08-deliberacion-consumidores-20261011.md).

### Herramientas gratuitas de diagnóstico — 2026-10-11

Usuario autoriza instalar y usar herramientas gratuitas para cerrar el bloqueo.
Se prioriza ahora evidencia del caso completo frente a la microhipótesis de
contenedores audit-only, que sigue sin aplicar. Instalación aislada de py-spy,
Scalene y Memray; 80 pruebas de controles/WGSI aprobadas, smoke nativo host y
contenedor real sin ampliar privilegios. Próxima acción: captura nativa más
PostgreSQL en el recorrido completo sintético, incluidos un lote tardío y las
descargas reales. No se ha cambiado producto ni aceptado 2s/5s. Plan y límites:
[perfiladores locales](evidencias/mod08-perfiladores-locales-20261011.md).


### Cierre del diagnóstico nativo gratuito — 2026-10-11

Recorrido completo terminado y recursos retirados: navegación p95 2,565728 s,
JSON máximo 4,807344 s y binario máximo 5,124024 s. Son resultados diagnósticos
de una población con instrumentación previa, sin aceptación ni mejora causal
demostrada. No se añadió optimización productiva. Se corrigió el seguimiento
de PID y la superposición de perfiladores; probe real PostgreSQL restringido
1 PASS y comprobaciones locales 82 PASS. Véanse resultados, fallos conservados
y límites en [la evidencia](evidencias/mod08-perfiladores-locales-20261011.md).
Los objetivos 2 s/5 s y las lecturas frescas permanecen vigentes.


Separación posterior de instrumentos: el modo nativo deja los controles HTTP
sin hooks locales y las capturas marcadas sin spans, cProfile ni perfil de
workers. También se desactiva cProfile del controlador y su posvalidación.
Memray/Scalene no se incorporan al recorrido. Pendiente nueva medición; no
se atribuyen ahorros a estos cambios del harness.


### Medición posterior sin perfiladores — 2026-10-11

Diagnóstico separado terminal 20261011-205904-6d77445d: 1 PASS, diez
capturas completas sin errores, navegación p95 2,483100 s; no aceptación.
Escenario normal terminal 20261011-212056-311e7b34: FAIL_DELIVERY_STAGE_LIMITS,
dos casos concurrentes sin perfiladores, 384 navegaciones y 20 descargas por
tipo/caso. Peores p95: 3,389665/8,961067/9,033017 s frente a 2/5/5 s.
Todos los intervalos exigidos se solapan, comprobado independientemente;
1389 huellas exactas antes de documentación y recursos propios ausentes.
Se retiró también cProfile de posvalidación del modo normal. No cambios
productivos ni aceptación; la instrumentación no explicaba todo el exceso.
[Evidencia y límites](evidencias/mod08-metricas-separadas-20261011.md).


### MOD-08 — control profesional y energía, 2026-10-12

Dos HTTP completos pasan etapas locales, sin perfiladores: candidata S3
1,730212/4,379374/4,657655 s y control original 1,626706/3,864846/3,840579 s.
No aceptación global/N3. Candidata retirada pese a dos puertas 139 PASS y
microbeneficio emparejado: no mejora HTTP demostrada. Usuario confirma alternancia
energética sin correspondencia por ejecución; gran salto causalmente no atribuible.
Herramientas profesionales aisladas, recursos propios retirados, consumo conservado.
[Evidencia](evidencias/mod08-s3-profesional-20261012.md).


### Medición en batería con rendimiento fijo — 2026-10-12

Usuario autoriza performance en batería y desactivar cambios automáticos de energía.
Ejecución 20261011-232221-3fc0bca2: 1 PASS en 903,803 s, cero errores/fallos/skips.
Peores p95 1,576682/4,163148/3,997933 s: pasan etapas locales 2/5/5 s, no global/N3.
Batería 49→28 %, desconectado al inicio/final; performance mantenido. Sin cambios
productivos ni perfiladores. 1.405 huellas independientes exactas antes de docs,
recursos propios ausentes. No atribución causal ni estabilidad entre ejecuciones.
[Evidencia](evidencias/mod08-bateria-rendimiento-20261012.md).


### Preparación de medición VPS — 2026-10-12

Instalador aislado de py-spy/Memray/Scalene/pyperf, lock transitivo con hashes y
lanzador de preflight/probe/measure/diagnose. Metadatos de entorno inicio/final,
guarda kernel native-sealed, separación de instrumentos y bloqueo de cargas.
Instalación local vacía e idempotente verificada; probe PG/Docker real
20261011-234614-8d848d74: 1 PASS 15,247 s, fuentes sin cambios, limpieza.
106 pruebas locales PASS, Ruff/shell/documentos PASS. Se conserva error inicial
de colección corregido. No conexión, instalación ni ejecución remota; no producto,
proveedores, datos reales, cambios de despliegue o sysctls. Consumo previo intacto.
[Procedimiento VPS](mod08-vps-medicion.md).

### Verificación local completa del procedimiento VPS — 2026-10-12

Usuario solicita probar aquí antes del servidor y después subir todos los cambios
para pull remoto. Primera carga ERROR por proceso observado presente en cierre;
no PASS pese a p95 bajo límites. Init Docker estándar y espera de reaping acotada,
sin omitir vivos/zombis. Preflight correctivo PASS; carga 20261012-001431-53a220c0:
1 PASS 909,989 s, p95 1,611558/4,181215/4,166493 s; sólo etapas, no global/N3.
Probe final PG/py-spy 20261012-003153-2f383fa9: 1 PASS 18,653 s y limpieza.
109 pruebas locales PASS. 1.411 huellas exactas antes de docs. Usuario confirma
sólo cable alternante, perfiles cambiaron pese a ajustes; causa no demostrada,
energía no constante. No despliegue remoto ni nuevos cambios productivos.
[Evidencia](evidencias/mod08-vps-preparacion-verificada-20261012.md).

### MOD-08 — inicio del relevo VPS, 2026-10-12

Reanudación expresa: servidor OpenStack, worktree aislado
`codex/mod08-vps-server-20261012`, base c46d0e101e8f260493a53bd4617b54dd4f0171f5;
checkout original con untracked preservado. Corrección sólo documental 72e6468
para referencias a artefactos locales ignorados ausentes en el VPS. uv actualizado
0.11.19→0.13.0 para instalar Python 3.12.15; sync frozen y herramientas con hashes
instaladas en venv separado. Kernel reconstruido Cython3.0.12/GCC11.5, native-sealed
SHA256 ca3c388585ed10a6f5ca3f5e82aeea385c5c496368e3800b45758df6fa2a0726.
Ruff PASS, docs PASS, 109 tests rápidos PASS/5.27s. Preparación de imágenes antes
de cargas; sin reiniciar servicios existentes. Secuencia autorizada y exclusiva:
preflight→probe→measure; una repetición sólo si PASS. Ante fallo, conservarlo y
diagnose separado según procedimiento, sin ensayos especulativos. Congelar fuentes
hasta salida de cada comando. Recibos en artifacts/vps-measurements y
artifacts/capacity-environment; exigir huellas, cero fallos/errores/skips, cuerpos
completos, concurrencia y limpieza independiente. Límites 4CPU/8GiB/storage20GiB,
p95 por caso navegación2s/JSON5s/binario5s. Entrega no acredita global/N3; energía
variable del portátil impide atribuir diferencias al código. Resultados pendientes.

### MOD-08 — relevo real VPS4CPU cerrado y ampliación autorizada8CPU

SHA2a6b81c incluye c46d0e1; sin cambio de aplicación respecto del relevo. Python3.12.15
/uv0.13.0/frozen/kernel native-sealed reales,109 rápidos PASS. Preflight77.460s y
probe42.375s PASS, limpieza/1411huellas independientes. Measure20261012-005632-9fb82130:
FAIL válido por límites,1fallo/0errores/skips/2317.495s; dos casos,384coberturas y20
descargas/tipo/caso. p95A/B cobertura3.829796/3.835592,JSON10.732150/10.565686,
binario10.334944/10.442426s. Integridad/concurrencia/huellas/retiro independientes;
cota memoria3.853565GiB,sin swap/OOM. Diagnose separado20261012-013900-179969c8:
1PASS1658.382s,10capturas(3parciales),SHA nativo en workers/esperas futures y PG; no
CPU causal exacto ni corrección probada. Sin reensayo especulativo. PSIausente,
stealmedio0.0338313%; portátil energético variable impide atribuir diferencias a
código. No global/N3. Evidencia [servidor4CPU](evidencias/mod08-vps-medicion-servidor-20261012.md).
Usuario autoriza posteriormente8CPU máximas; próxima acción perfil explícito de8CPU
con RAM/dataset/workers/garantías/SLO conservados,preflight antes de medir y una
repetición sólo si PASS. Conservar FAIL4CPU;8CPU no acredita contrato4CPU.

MOD-08 VPS8CPU: perfil explícito `--cpu-budget 8` preparado en ejecutor propio;
aplicación/kernel/images iguales al ciclo4CPU. Cuotas PG3CPU/app3.5/objetos1/
Redis0.2/proxy0.2/controlador0.1,total8; memoria8GiB,workers/storage/dataset/SLO
intactos. Default4 conservado;8 rechaza topología ajena y baselines diagnósticas.
Ruff PASS,120 rápidos PASS/2.91s. Congelar tras commit; secuencia propia exclusiva
preflight8→probe8→measure8, una repetición sólo si PASS. Verificar todas las cuotas
kernel, huellas, cero errores/skips, cuerpos/intervalos y limpieza independiente.
No global/N3 ni PASS4CPU por extrapolación. [Plan8CPU](evidencias/mod08-vps-perfil-8cpu-20261012.md).

## MOD-08 VPS8CPU y diagnóstico profesional,2026-10-12

Ciclo8CPU concluido: preflight/probe PASS, measure FAIL con seis incumplimientos,
diagnose separado PASS, fuentes y limpieza auditadas. Peores p95
3.547708/7.115129/7.099972s; mejora7.51/33.70/32.01% respecto4CPU con mismaapp.
[Tabla por caso y recibos](evidencias/mod08-vps-perfil-8cpu-20261012.md).
Usuario pide investigar con herramientas gratuitas adicionales y corregir.
Scalene/Memray acotados por separado detectan copias evitables del codec;
[corrección y evidencia limitada](evidencias/mod08-vps-professional-codec-20261012.md).
Memray sobre coberturaHTTP real en preparación aislada; sin nueva aceptación
HTTP/global/N3. Pendiente integración real y medida sin instrumentos trascorrección.

Memray HTTP real: probe finalPASS49.641s, diagnóstico posteriorERROR por2M
registrosenresumenonline; traza tempranacompleta recuperada yreplayofflinepropio
produce1.906GBasignaciones/176.9MBpico, rutaimágenes939.5MB ycanonical318.7MB.
[Receipts, límites ycorreccionesdeinterpretación](evidencias/mod08-vps-memray-cobertura-temprana-20261012.md).
No nueva métricap95 ni reducciónHTTP atribuida alcodec; objetivo sigueactivo.


## Diagnóstico SQL tardío aislado, continuación 2026-10-12

Autorizado por «investiga pues». Nuevo parámetro exclusivo:
`uv run python scripts/run_vps_capacity.py diagnose --cpu-budget 8 --sql-plan-target 304`.
Usa la misma infraestructura propia y cuotas; no py-spy/Memray/Scalene,
ni wrappers de tiempo heredados, ni background Celery. Selecciona el test
finito de planes existente con niveles 0/304; conserva tope 420s de siembra,
90s por hijo y 15s por SQL. No ampliar si no llega al nivel tardío.

Fixture 1500 revisiones/~16MiB y originales físicos/~64MiB creado por servicios.
Los 304 lotes son inspecciones escalares repetidas, con commits/auditorías
normales, no filas de evidencia fabricadas. Flujo parcial; verificador de
identidad simulado explícitamente, PostgreSQL/HTTP sí reales. Objetos/proxy
propios disponibles en topología pero este ensayo no acredita su entrega.
Dos workers Gunicorn sync, roles propios separados. EXPLAIN en login exclusivo
no propietario, checks de permisos y atestación frescos, cabeza bloqueada;
comparación exacta de hashes del corpus antes de planes. Se registra ausencia
de otras conexiones activas de ese mismo login. Las 8 consultas son las actuales
EVENT+7sources. No cambios de esquema/índices/planner ni candidata inline
productiva. Relojes separados execute/fetch del driver, SQL hash y planes con
TIMING OFF/ON y SERIALIZE TEXT. No p95 HTTP ni CPU pura de PostgreSQL.

46 tests rápidos PASS/1.36s, Ruff de los cambios PASS. Sources se congelarán
antes de ejecutar; registrar resultado/fallo, SHA, versiones y limpieza real.
No atribuir diferencias del portátil a código ni declarar N3/global.


Corrección de adaptación, posterior al primer terminal SQL:
431149c / 20261012-111350-eba253e3 ERROR:1FAIL532.004s, agotado tope
420s de siembra. Plan temprano36eventos completo, rol exclusivo0otros activos,
fuentes1415 idénticas, archivos y cleanup auditados; RAMupper1498865664bytes.
No plan tardío ni aceptación. El límite420 era de la prueba original64lotes;
se aplicó indebidamente al nuevo tamaño304(4.75veces). Fallo conservado.
La variante64 retiene420s; la explícita304 tendrá1200s finitos para preparación,
dentro del tope9000 del runner. No cambia15s por sentencia/90s por hijo,
CPU8/RAM8GiB/storage20GiB ni SLO2s/5s. No cambio de aplicación/performance.
Checkpoints de siembra se registrarán también en JUnit para conservar el último
estado en cualquier fallo. Ésta es una corrección del instrumento, no una
reescritura SQL especulativa ni una medida de mejor rendimiento.


SQL tardío terminado: db52437 /20261012-112648-cc0ad6f8, JUnit1PASS805.570s,
0fallos/errores/skips;304lotes/heads36→2468, roles restringidos exclusivos y
hashes exactos/8consultas/captura, fuentes1415/archivo/cleanup independientesPASS.
LauncherEXIT1 conservado: nueva etiqueta SQL_PLANS_DIAGNOSTIC_NOT_CAPACITY
omitida en lista final de éxitos. Fix clasificación, expresión real de exit
verificada para SQL0/ERROR1/falloSLO1, RuffPASS; sin rerun carga. Resultado
científico válido, no launcherPASS ficticio ni capacidad. Evidencia versionada
[evidencias/mod08-vps-planes-tardios-20261012.md](evidencias/mod08-vps-planes-tardios-20261012.md).
No índicefaltante observado en corpus caliente: tardío eventos33.832ms versus
controlinline19.661;SelectionRead37.818/21.781;CoverageRead36.060/23.243.
Misma estructura de planes por variante,0reads/spills traswarmup. NoHTTPnuevo,
no aplicacióneditada ni restitución inline retirada. Próximo: sólo candidata
con beneficioHTTPVPS demostrado o rediseño redundancia con garantías exactas.
No extrapolar sumasmedianasonline ni atribuir portátil al código. N3pendiente.


## Lectores SQL por conjunto autorizados, 2026-10-12

Candidata preparada: migración0118/8helpers invoker/STABLE, productores v1 intactos,
fresh hashes/8snapshots/bloqueos/guards conservados. 73PASS y29PASS; cinco fallos
de topología de tests preservados y repetidos en adaptador CI oficial:6PASS,
fuentes iguales/cleanup real. Sin nueva métricaHTTP ni aceptación todavía.
[Evidencia, límites y fallos](evidencias/mod08-vps-lectores-conjunto-20261012.md).
Próximo: preflight8→probe8→measure8 sin editar fuentes; sólo repetir si cumple.


## Resultado lectores por conjunto / auditoría ROI, 2026-10-12

SHA388c991: preflight/probe PASS; measure125702-b2d8dd6f FAIL por6límites,
p95A/Bnav3.251440/3.275722s,JSON6.486092/6.379550s,bin7.064550/7.070781s.
Reducciónobservada conjunto codec+SQL≈7.7%nav/8.8–9.6%JSON,bin≈igual;
JUnit2050.766→1960.506s. No atribuciónaislada ni aceptaciónglobal/N3.
No repetirFAIL; diagnoseSQL304133355-c56f5505 PASS771.444s,comparaciónexacta
set_hash actual versus scalarcontrol, con sobrecostepequeñocorpus. Fuentes1418,
archivo y cleanup independientesPASS,todosrunners terminales.
[Resultados/recibos](evidencias/mod08-vps-medida-lectores-20261012.md),
[SQL](evidencias/mod08-vps-planes-lectores-20261012.md).

Usuarioautoriza analizar ROI/sobreingeniería:3lecturas nativas independientes,
rootverifica en código/negativas y RGPD/CEPD. Obligaciones legales ≠ mecanismo
prescrito. Conservar garantías probadas; trabajoevitable confirmado rewrapsink
noHTTP; amplitudbytechecks, replayhistoria y gatecada página requieren justificar
beneficio/contrato, no eliminaciónautomática. [Auditoría](evidencias/mod08-auditoria-roi-20261012.md).
Siguienteacción técnica: inventario de fronteras de validación y propuesta simple
con garantía explícita, antes de otra optimización/medición. No caché deautoridad,
noheadsolo ni datos reales/proveedores/publicación.


Simplificación posterior a las mediciones (2026-10-12): rewrap autentica con
verify sobre la copia cifrada y elimina los dos temporales en claro descartados.
Conserva autenticación completa, formato y frames; 97 pruebas unitarias PASS
(10 excluidas: integración RustFS y caminos ajenos), incluidas siete regresiones
para rotación sin salida ante fallo y almacenamiento temporal sólo cifrado.
Ruff y documentación verificados. Este cambio de mantenimiento no tiene p95
HTTP medido: las cifras publicadas siguen correspondiendo al SHA 388c991.
Las demás candidatas de ROI permanecen propuestas; no se han retirado garantías.


MOD08 lectura final streaming: integrada candidata de eliminación de staging
cifrado, con 184 pruebas codec/transport y 25 de integración LOGIN/PG/RustFS/Caddy
PASS. Conserva lectura fresca, guards y publicación posterior a integridad completa.
[Diseño y evidencia funcional](evidencias/mod08-lectura-fresca-integrada-20261012.md).
Pendiente ciclo HTTP limpio en SHA congelado; no inferir ahorro p95 ni N3.
