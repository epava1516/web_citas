# MOD-08 — coordinación de frentes en paralelo

## Estado vigente — perfil real posterior a integración SQL

Integración master58c67b8. N2 conjunta16archivos140PASS0skips303,744s. Captura174156 BASELINE_CAPTURED_DIAGNOSTIC_ONLY:1509páginas completas, fuenteigual, retirada verificada. Reuso182155 PROFILE_DIAGNOSTIC_NOT_CAPACITY: HIT_DIAGNOSTIC_REUSED_PREPARATION en controlador nuevo,1PASS0skips483,866s, fuentesiguales/retirada verificada y ausencia independiente de contenedores propios. Generación real1intento33,160s; cierre11,525s. Descargas diagnósticas JSON3muestras p95 23,539s y binario8muestras p95 24,374s: no cumplen5s y no constituyen poblaciones de aceptación. Memoria superior conservadora2.465.251.328bytes, sin aceptación N3/capacidad/CR09.

Comparación parcial equivalente primeros123lotes de4páginas no perfilados: p95 5,087→4,251s (16,418%); SQL755→515 (31,788%). No se cumple2s para lote completo. Evidencia temporal preservada en artifacts/mod08-sql-bulk-live-profile-20261010; archivo de baseline cifrado privado no se publica.

Siguiente correctiva aislada: storage_crypto posee exclusivamente apps/safety/evidence_chain.py y nuevo tests/test_rights_enforced_validation_seal.py en /home/felidae/proyectos/web_modelos_mod08_enforced_seal, base58c67b8. Objetivo: productor SQL textual seguro de7familias para permitir sello enforced; conservar rechazo Composed arbitrario, política/caller/expiración y lectura física fresca. Root verifica/integra; no tests pesados paralelos. async_generation realiza revisión de sololectura del coste S3; no propiedad escritora nueva. Consumo e historial Claude conservados.


## N2 conjunta final162PASS — integración local

Run165711 sobreb55c114:15archivos/162PASS/0skips286,84s, fuenteigual y retiro PG/Redis probado porinspect. Aviso de teardown de una base de test con1sesión; contenedor completo propio ausente al finalizar. Incorporado e871f89 documental sin cambio apps/config/scripts/tests. Conservar borrador originalClaude async-generation con nombrepreserved antes de fast-forward master. Próxima carga: captura diagnóstica real1500/16MiB/64MiB; recursos/objetivos íntegros, sinmediciones/testscompetidores. Noaceptación capacidad/N3/CR09.

## Estado vigente16:56UTC — bloqueos correctivos resueltos

Probe real163801 READY_NOT_CAPACITY: generación1intento4,009s,4.3MB realesS3/AEAD/SHA, binding/Caddy/Beat PASS, fuentes iguales/retirada. Baseline16534522PASS91,79s:1PGpositivo/adversariales+21guards. Negativos y correctivas preservados en docs/evidencias/mod08-generacion-real-y-baseline-n2-20261010.json/tar.gz. Propiedad writers terminada; raíz prepara N2 conjunta finita antes de master y perfil grande, sin cargas simultáneas. Aún no aceptación capacidad/N3/CR09.

## Estado vigente16:37 UTC — Codex

Worker real localizado: AttributeError en recording.wrapper175 por SQL compuesto de cadena de evidencia. Correctiva4e7fc34 con fallback completo y regresiones SQL/Composed/iterator; N2 conjunta48PASS/1FAIL, único fallo baseline ObjectInUse. Agente canonical_tests corrige exclusivamente restore en worktree aislado; raíz repite probe real sin baseline, fuente congelada/sin cargas competidoras. N2 jobs/preflight anterior48PASS. Negativos/fuentes/retirada archivados en docs/evidencias/mod08-sql-composable-diagnostico-20261010.json y tar.gz. No rendimiento/N3/CR09 aceptado ni integración master todavía.

Actualizado: 2026-10-10 12:16 UTC. Coordinador: Claude principal (MOD-07). Plan: docs/95-plan-modernizacion-mod08.md. Cada frente mantiene su estado en `.ai/tasks/mod08-<frente>.md` y hace commits frecuentes en su rama; el coordinador integra en master tras N2 conjunta con el runner paralelo.

## Relevo vigente a Codex — 2026-10-10

Usuario: «Claude … se ha quedado sin tokens, continúa tú desde donde lo dejó». Codex retoma coordinación, implementación, verificación e integración local; conserva criterios y consumo histórico. Tres agentes nativos escritores en worktrees existentes, sin invocar Claude V1 ni modificar su adaptador. Base integrada `209f014`: xdist ya integrado tras 414 PASS/0 skips en `20261010-115833-c37b6bfa` (1109,918 s JUnit); el estado «en curso» de la tabla anterior es histórico.

Propiedad: Codex `../web_modelos_claude_srcver` (huella3/sello4); `async_generation` worktree `agent-ab23eda63576809b3` (job/modelo/migración0113/vistas de generación/tareas/plantilla/pruebas); `storage_crypto` `agent-a52e0d2a35a796e8f` (AEAD/repositorio S3/nuevas vistas de entrega/configuración/Compose/Caddy, migración0114 provisional); `canonical_tests` `agent-aca043e68c0f1196d` (canónica/row_reference/pruebas) y después `agent-a1ea0524fd9545f88` (fixtures rápidos). Modelos/migraciones se reconciliarán antes de N2 conjunta. Evidencia inmutable y revisión por lotes quedan para el siguiente bloque dependiente; su preparación anterior permanece conservada.

No hay pytest/capacidad propio vivo al reconciliar. Ramas sin commits nuevos salvo xdist y source-version; canónica contiene únicamente dependencias sin commit y source-version contiene sello sin commit. Fuentes previas preservadas antes de corregir. Pruebas pesadas se programan por ventana; ninguna carga de capacidad junto a compilación/pytest. Una sola integración activa, estados de cada pieza independientes de aceptación CR09/N3.

Hipótesis finitas de revisión3/4: `xmin` aislado no distingue dos UPDATE dentro de una misma transacción; reproducir y añadir identidad de tupla si se confirma. El sello inicial calcula resultados al reproducir SELECT después de la validación y pierde orden al ordenar texto: debe probar que exactamente los resultados realmente consumidos y sus dependencias temporales/externas se conservan, antes de omitir la validación completa. Criterio N1: reproducciones significativas PG17, corrección y tests afectados PASS; N2 posterior: selección de49 archivos exportación/cierre/descargas/autoridad más pruebas3/4, cero skips, fuentes congeladas y retirada real. No se acredita p95 ni N3 por este registro.

| Frente | Piezas | Responsable | Estado vigente12:45UTC |
| --- | --- | --- | --- |
| Huella y sello | 3,4 | Codex raíz/source-version | Reproducciones PG confirmaron2defectos; corregidos xmin+ctid y captura SHA256 ordenada real. Reutilización del sello PASS dirigida; N2 fuente/sello/source_reads en curso |
| Runner paralelo + baseline snapshots | 9 | Codex canonical_tests | xdist integrado414PASS; snapshots15PASS78,881s +6guardsPASS; commits3c732bd/bf91bc2/8f2d34e en rama integrada |
| Generación Celery | 5 | async_generation | Primer N2 121PASS/19FAIL; parsers puros corregidos; segundo N2 en curso |
| AEAD/S3 propio y Caddy | 6,8 | storage_crypto | Garage falló escritura condicional; RustFS pin digest real42PASS0skips. Hooks de descarga y censo se completan antes de integrar |
| orjson/BLAKE3 | 7 | canonical_tests | 21pruebas puras PASS; commit3fe49c7 integrado en rama de preparación; N2 conjunta pendiente |
| Fixture diagnóstica aprobada | 10 | canonical_tests tras11 | Diseño pendiente; no reutilizar autoridad/revisión como aceptación |
| Evidencia inmutable | 11 | canonical_tests | Cadena7familias PG8PASS; hardening de padre RightsAction y nuevos adversariales antes de aceptación |
| Lotes auditados | 12 | Codex raíz/rama integrada | Código/contrato interno escritos; N2 domain/HTTP/Chromium ESEN en curso, fuentes congeladas |
| Compilación rutas calientes | 13 | Codex raíz | Condicional al perfil integrado posterior |

Reglas: sin mediciones de capacidad mientras haya pruebas; garantías y objetivos intactos; integración solo tras N2 conjunta PASS.
Siguiente paso: cerrar N2 individuales y corregir fallos; reconciliar modelos/migraciones/config/censos, N2 conjunta y luego perfil/capacidad sin otras cargas. No sumar baterías individuales como una N3.

## Continuación efectiva 2026-10-10 tras diagnóstico terminal

Codex sigue dirección y ejecución por instrucción posterior del usuario. Master6437a74 se incorporó a la rama integrada preservando preparación BF/GS01 y correctiva de aislamiento Redis; no acepta fases. Perfil702914e falló en generación3intentos y recibió cargas Claude solapadas: performance INVALID; originales conservados. Se mantiene una sola ventana de cargas, incluidas externas al equipo nativo.

Propiedad vigente: raíz integración/evidencias/sello; async_generation p12proyección pura y pruebas en web_modelos_mod08_batch_projection; canonical_tests pieza10 en .claude/worktrees/mod08-p10-diagnostic-baseline; storage_crypto revisión independiente sólo lectura. Correctiva Claude431d34d preparada fuera de integración, N2 Claude vivo20261010-155106-950fc30a antes de nueva carga. Codex comprueba terminal/cleanup y revisa cada diff antes de adoptar. No cargas de capacidad hasta N2 correctivas y coordinación confirmada. Pieza13 condicionada al perfil, sin implementación nativa todavía.

Ventana Codex: N2 correctiva12archivos,3workers,fuentes congeladas desde lanzamiento hasta terminal; agentes sólo edición en worktrees aislados, sin PG/tests/carga competidora. Usuario confirmó detención de Claude; ningún ejecutor propio/Claude vivo al comenzar. Después terminal, comprobar negativos y N2; no medir simultáneamente.

N2c1b5973terminal114PASS/1FAIL documental,248,25s,0skips/cleanup/fuenteiguales; ruta jobcorrigida1PASSsinapps/esquema. Freezelevantado. Root conserva negativos115node suiteERROR, no suma115PASS simultáneos. Propiedad storage_crypto ahora probe finito en web_modelos_mod08_async_probe(tests/capacity_async_preflight.py,hooktest_capacity_object_preflight.py ysoloqueued_generationtimeout). P10agentrun_caseboundaryenownworktree; reconcileporCodexantesintegrar. NingunaPGcarga concurrente.

## Estado vigente17:39UTC — SQL fresco y N2 conjunta

Writers nativos aislados: async_generation owns rights_portability_image_read.py/test_bulk, commits4099887/bd9409c→6614983/9d8b8b3; storage_crypto owns rights_exports.py/rights_portability_images.py/test_contents_bulk y2hooks autorizados,63e3a43/80de2fe→7e7f251/2bd47fa; root20d0eba importa Ruff. canonical_tests ejecuta72PASS y76PASS1FAIL yfinal140PASS303,75s fuente2bd47fa igual/retirada real. Root conserva negativos/5perfiles y fuente30b69cf: SQL755/lote4,p95 parcial5,0865s125muestras; SIGINT únicamente pytestpropio, no baseline válido ni capacidad. Historia/consumo Claude intactos; sin invocaciones V1. PróximoFFmaster y diagnóstico requests con código congelado, sin cargas competidoras. CC-05 documentación solicitada futura en docs/97, sinselección tecnológica.


## Correctivas de entrega verificadas y siguiente catálogo

b23cde3 trustedSQL y4354109 proxy scope: N2 conjunta184050100PASS0skips248,122s, fuentesiguales/PGRedisausentes verificados. N2 aislada18351651PASS223,290s. Root conserva evidencia diagnóstica174156/182155 y N2 en docs/evidencias/mod08-perfil-entrega-y-sellos-20261010 (baseline privado excluido). Perfil nuevo pending; master58c67b8 hasta cierre de registro.

Writer storage_crypto posee únicamente _runtime_is_trusted en apps/safety/evidence_chain.py y nuevo tests/test_rights_runtime_catalog_bulk.py en /home/felidae/proyectos/web_modelos_mod08_runtime_catalog base4354109. Agrupación26→9 fresca por llamada; N2 propia lanzada18:46PID978323 ticks337857281, sin otras cargas pesadas. Root integra/acepta tras equivalencia, fuentes y retirada reales; consumoClaudeintacto.


Catálogo eef4368 aceptado técnicamente tras18460370PASS0skips219,061s, fuentesiguales/PGRedisausentes verificados. Writerpropiedad concluida, consumos/historiaClaude intactos. Próxima carga única: captura diagnóstico original1500/16MiB/64MiB desde integración final, same4CPU8GiB20GiBswap0; no builds/tests/cambios durante perfil. Meta final permanece2casossimultáneos/objetivos completos, no baselinecomoaceptación.


## Medición real posterior al catálogo y sellos — 2026-10-10

HEAD medido `228c540`: captura `20261010-185127-467de09c`, 1PASS/0skips/1917,386s; resultado tipado BASELINE_CAPTURED_DIAGNOSTIC_ONLY, salida1 intencionada tras aprobación real, no aceptación. Reutilización `20261010-192733-599e5146`, 1PASS/0skips/280,152s, PROFILE_DIAGNOSTIC_NOT_CAPACITY y HIT entre controladores reales. Fuentes e inputs sin cambios y retirada verificada en ambos. [Métricas y perfiles saneados](../../docs/evidencias/mod08-medicion-catalogo-entrega-20261010.json); clave y estado cifrado privado excluidos.

Cobertura: 1.509 páginas reales, 383 lotes sin perfil, p95 **4,889s**. Comparación de los primeros123 lotes de4: 5,087→4,278s (**15,90%** frente al diagnóstico previo parcial), sin mejora adicional demostrada frente a 4,251s posterior a SQL. Perfil SQL447 frente a515; reducir consultas no acredita por sí solo reducir latencia. Descargas TCP JSON3 muestras p95 **9,107s**, binarias8 p95 **9,541s**, aproximadamente61% menos que el diagnóstico anterior de23,539/24,374s, todavía fuera de5s. Son cambios integrados más correctivas posteriores, sin atribución causal aislada a Claude.

Generación34,303s/1intento; preparación final11,536s, inspección4,431s, aprobación4,728s y cierre11,632s. Mediciones de un caso y muestras reducidas no sustituyen capacidad completa de2casos. Restan aproximadamente59% en lotes para2s,45% JSON y48% binario para5s. No se modifica aceptación ni avance contractual. Continúa candidato aislado de cálculos puros y transporte S3 por operación; no aceptado ni medido todavía.


Candidato aislado de cálculos puros/transporte: N2 `20261010-193904-c6edaa51` terminó **428PASS/4FAIL/0skips**, 607,294s, fuentes sin cambios y PostgreSQL/Redis propios retirados. [Evidencia negativa conservada](../../docs/evidencias/mod08-regresion-puros-negativa-20261010.json). Corregidos solo wrappers/expectativas de tres archivos de pruebas; no cambia producción ni el rechazo de mutaciones/rollback. Repetición conjunta `20261010-195055-30642e82` en ejecución con fuentes congeladas, sin aceptación ni commit del candidato. Se prepara aparte borrador de verificación física S3 de máximo2objetos paralelos; no integrado, probado ni medido todavía.


Preferencia del usuario, 2026-10-10: cada nueva métrica de rendimiento debe presentarse con cuadro comparativo (anterior/nuevo/mejora porcentual/objetivo/reducción pendiente), población y número de muestras, identificador de ejecución y alcance diagnóstico o aceptación completa de2casos. No atribuir causalidad aislada a Claude sin comparación que lo pruebe ni comparar poblaciones distintas como mejora equivalente.


## Cálculos puros y transporte por operación — integración local

Commit `d5c1db7`, integrado localmente en rama de integración y master: evitar canonización/digests repetidos por validación, firmas puras acotadas por operación atómica con SECRET_KEY fresco, validación única de decisión excluida equivalente, retorno audit-only sin copias descartadas, consultas latest id-only, transporte S3 acotado por operación con crypto/config frescos. N2 conjunta `20261010-195055-30642e82`: **432PASS/0FAIL/0skips/599,336s**, 37archivos, fuentes sin cambios, hash exacto de20archivos revisados y retirada independiente verificada de PostgreSQL/Redis/RustFS propios. [Evidencia y JUnit saneado](../../docs/evidencias/mod08-calculos-puros-transporte-20261010.json). Negativa previa preservada; correctiva posterior solo tres pruebas, no producción.

La validación pasa de428PASS/4FAIL a432PASS/0FAIL; no es una mejora de latencia del request. Rendimiento de este commit todavía no medido y baseline antiguo inválido para estas fuentes. Se revisan aparte pipeline SQL acotado y verificación S3 de dos objetos paralelos antes de una nueva medición. Cada nueva métrica temporal incluirá cuadro comparativo, número de muestras, población y alcance. Criterios originales y porcentajes contractuales intactos; N3 y capacidad completa2casos pendientes.
