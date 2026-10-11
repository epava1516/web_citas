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


Prototipo aislado SQL pipeline8/S3 dos objetos: N2 `20261010-200324-ff7a5086` terminó457PASS/3FAIL/0skips626,052s en39archivos, fuentes estables y PG/Redis propios retirados. [Evidencia negativa](../../docs/evidencias/mod08-protocolo-paralelo-negativa-20261010.json). No integrado. Dos nuevos casos exigían rechazo ante mutaciones que deben contrastarse con validación completa; un caso previo LOGIN enforced declinó sello válido y requiere diagnóstico sin rebajar su assert. Próxima dirigida instrumentará diferencias/expiry/errores sin exponer SQL/params/credenciales. Rendimiento todavía sin nueva medición, objetivos originales intactos.

Diagnóstico dirigido `20261010-201850-4cea6891`:21PASS/1FAIL,22casos,222,296s,fuentes estables y retirada PG/Redis. Los21casos de producción pasan; falla exclusivamente wrapper temporal por falta de marca django_db antes de fixture, sin eventos. Corregida marca/import del diagnóstico, producción intacta. Repetición `20261010-202327-4947025d` PID1581029/startticks338441669 activa; fuentes congeladas. [Evidencia dirigida](../../docs/evidencias/mod08-protocolo-dirigida-diagnostico-20261010.json). No sustituye conjunta460 ni nueva medida de request.

Dirigida correctiva `20261010-202327-4947025d`:22PASS/0FAIL/0skips243,559s,fuentes sin cambios,retirada PG/Redis. Instrumentación:124resultados pipeline==serial==grabados;caller/config coinciden,TTL>86387s. Diagnóstico no equivalente a rendimiento/aceptación. [Evidencia saneada](../../docs/evidencias/mod08-protocolo-dirigida-correctiva-20261010.json). Test temporal preservado en artifacts ignored y retirado de tests. Ruff4archivos/diffcheckPASS. Relanzada conjunta39archivos/460casos3workers PID1612282/startticks338472196;fuentes congeladas. Hipótesis estática ante fallo anterior:orden SQL sinORDER/planes,callergraph/config/TTL;ninguna probada,ningún guard rebajado.


## Pipeline SQL y verificación física paralela — integración local

Commit `e19c3fc`, integrado localmente en rama de integración y master. SQL fresco en pipeline de8 statements independientes, misma conexión/snapshot por statement, drenaje antes de rollback y fallback serial compatible. Verificación física completa de dos objetos simultáneos como máximo, transporte privado por worker dentro de una invocación, crypto/config frescos, errores observados en orden y cierre obligatorio; no se omiten tombstones/SHA/AEAD/EOF/contexto.

N2 conjunta `20261010-202832-ee994233`: **460PASS/0FAIL/0skips/632,491s**,39archivos,3workers,hashes exactos revisados,fuentes sin cambios y retirada PG/Redis/RustFS verificada. [Evidencia y JUnit saneado](../../docs/evidencias/mod08-protocolo-paralelo-integrado-20261010.json). Negativa previa preservada:dos nuevas mutaciones corregidas tras comprobar rechazo completo; warm fallback previo no reproducido y causa todavía no probada,assert original intacto. Dirigida instrumentada22PASS:124resultados pipeline==serial==grabados,caller/config coincidentes,TTL suficiente; instrumentación temporal retirada antes de conjunta.

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

[Evidencia saneada de ambas mediciones](../../docs/evidencias/mod08-medicion-puros-protocolo-20261010.json).


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

[Desglose saneado](../../docs/evidencias/mod08-desglose-http-puros-protocolo-20261010.json).


## SHA de contenido idéntico por operación — integración local

Commit `ad1189b`: retiene como máximo16entradas/64MiB durante un batch atómico, asociado a conexión, bloque atomic, hilo y PID actuales. IDs sólo localizan bytes anteriores: reutiliza SHA exclusivamente tras igualdad completa de los bytes frescos exactos; cambios incluso del mismo tamaño se hashean de nuevo y nunca reemplazan el original. Tipos no soportados/límites/atomic terminado/contexto diferente usan SHA nativo. Limpieza finally obligatoria. SQL, locks, lectura física, autorización y auditoría de cada hijo permanecen frescos.

N2 dirigida `20261010-212613-ac0fdf4d`:51PASS/0FAIL/0skips318,443s; conjunta42archivos `20261010-213243-3a0e6675`:496PASS/0FAIL/0skips696,096s. Fuentes sin cambios, cuatro SHA exactos revisados y PostgreSQL/Redis/RustFS propios ausentes verificados. Lanzamiento inicial ARGPARSE conservado: omitía native-source por instrucción de root, sin servicios/pruebas; no negativo funcional.

| Prueba finita16fotos x4 hijos | Antes | Actual | Reducción | Objetivo de equivalencia |
| --- | ---: | ---: | ---: | --- |
| Lecturas físicas completas | 64 | 64 | 0% | Mantener64 |
| Cálculos SHA nativos | 64 | 16 | 75% | Misma salida exacta |

La prueba real PG con16WebPde4MiB acredita aritmética de retención64MiB, overflow nativo y limpieza; no appRSS<=1GiB ni peakglobal<=6GiB. Negativas de corrupción tardía, auditoría eliminada y sesión/MFA/permisos/prueba/fuente/expiry conservan rollback. No hay nueva latencia medida ni avance de aceptación/porcentajes contractuales. Baseline anterior inválido para estas fuentes; requieren captura nueva y medición con todas poblaciones y cuotas originales. N3 y dos casos simultáneos siguen pendientes.

[Evidencia y JUnit saneado](../../docs/evidencias/mod08-sha-contenido-integrado-20261010.json).


### Instrumentación de GET diagnóstico, integrada localmente

Commit `1e6aae3`: transmite exclusivamente un marcador de perfil validado al GET privado de la petición extra perfilada, sin reenviar headers del POST. Las muestras ordinarias, dos validaciones, EOF, cookies, ámbito y no-store conservan el flujo original. N2 `20261010-214551-ea378e04`:41PASS/0FAIL/0ERROR/0skips269,731s, tres archivos, PostgreSQL/Redis reales y guardas legacy Caddy/worker; fuentes sin cambios y retirada propia verificada. Los14casos del marcador usan opener local: todavía no prueban propagación real del marcador por Caddy. El próximo capture/use debe producir fichero de perfil proxy real; no se declara ganancia de latencia.

Preparada captura nueva tras SHA, conservando1509páginas/383lotes/123comparables, JSON16MiB/originales64MiB, 4CPU/8GiB/20GiB/swap0 y todos los límites originales. Fuentes congeladas desde lanzamiento hasta terminal de captura y posterior reutilización; sin cargas competidoras. Doscasos/N3/CR09 íntegros siguen pendientes.

[Evidencia de instrumentación](../../docs/evidencias/mod08-perfil-forwardauth-integrado-20261010.json).


## Medición posterior a SHA y perfil real de forwardauth — 2026-10-10

HEAD medido `cfb0df3`: captura `20261010-215201-1472feb2`, BASELINE_CAPTURED_DIAGNOSTIC_ONLY, 1PASS/0FAIL/0ERROR/0skips1552,171s; reutilización `20261010-222157-124a7967`, PROFILE_DIAGNOSTIC_NOT_CAPACITY, 1PASS/0FAIL/0ERROR/0skips245,752s. HIT_DIAGNOSTIC_REUSED_PREPARATION, fuentes e inputs privados sin cambios, archivos dentro del techo y retirada propia verificada independientemente. PostgreSQL/Redis/RustFS/Caddy reales; datos sintéticos e identidad simulada. Ambos procesos terminales; termina la congelación.

| TCP p95, misma población | Anterior (s) | Nuevo (s) | Mejora | Objetivo (s) | Reducción pendiente | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recorrido, lotes sin perfil | 4.375794 | 3.880241 | 11.32% | 2 | 48.46% | 383 |
| Lotes completos comparables de cuatro páginas | 3.862194 | 3.264592 | 15.47% | 2 | 38.74% | 123 |
| Descarga JSON, dos HTTP hasta EOF | 6.735796 | 6.749283 | -0.20% | 5 | 25.92% | 3 |
| Descarga binaria, dos HTTP hasta EOF | 6.428605 | 6.545222 | -1.81% | 5 | 23.61% | 8 |

Comparación con captura204101/use211629. Recorrido1509páginas,383lotes sin perfil (incluye parciales);123sólo lotes de cuatro páginas, excluyendo el perfilado. Nueva reducción del listado; las descargas empeoran ligeramente y siguen fuera de5s. Sin atribución causal aislada ni aceptación de dos casos. JSON tres paquetes<=8MiB y ocho binarios<8MiB, dos autorizaciones frescas y EOF.

| Operación, una muestra (no p95) | Anterior (s) | Nuevo (s) | Mejora | Objetivo (s) | Reducción pendiente | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| generation | 32.589223 | 32.913815 | -1.00% | 120 | 0.00% | 1 |
| final_preparation | 11.465790 | 10.709931 | 6.59% | 30 | 0.00% | 1 |
| final_inspection | 2.815197 | 3.105194 | -10.30% | 30 | 0.00% | 1 |
| final_approval | 3.090912 | 3.760574 | -21.67% | 5 | 0.00% | 1 |
| closure | 11.075993 | 11.678849 | -5.44% | 30 | 0.00% | 1 |

Marcador comprobado ahora en Caddy real: archivos `capacity-profile-json_download_proxy-101.txt` y `capacity-profile-binary_download_proxy-100.txt`, además de sus POST. Son muestras adicionales perfiladas, excluidas de p95. El GET mantiene cierre/revisión/binding/sello SQL y verificación física frescos; los tiempos acumulados de hilos y funciones se solapan y no se suman. Ninguna autorización cacheada entre requests. N3, dos casos y criterios originales de memoria/latencia siguen pendientes; porcentajes contractuales sin incremento. Candidato nativo canónico permanece borrador no construido/no probado/no integrado.

[Evidencia saneada de captura y descargas](../../docs/evidencias/mod08-medicion-sha-forwardauth-20261010.json).


### Continuación nativa posterior a nuevas métricas

Sin aceptación final: listado/descargas siguen sobre objetivos y falta N3/dos casos. Root implementa loader/build/identidad en worktree `web_modelos_mod08_native_canonical`, basecfb0df3, separado del entorno integración: builderCython3.0.12 y runtimeuvlock aislados. Primera carga os.memfd_create falló porque CPython standalone no expone esa API ni seals; no es fallo del producto integrado. Libcmemfd+UAPILinux verificados, carga real sealed funcional. Corpus63PASS; loader/contrato113PASS; después negativas FIFO/fork y bound/rule_identity, loader36PASS. Pruebas locales sin DB no acreditan N2 ni rendimiento. Revisión readonly confirmó diferencia de presupuesto de recursión C vs Python; agente canonical_tests corrige exclusivamente pyx/fast_canonical/test diferencial, no integración hasta prueba exacta. Root posee loader, builder, artefactos, identidad de regla/baseline/freeze y testloader. No fuente ni biblioteca de integración cambiada.

Nuevo worktree `web_modelos_mod08_verify_only`, rama `codex/mod08-verify-only-candidate`, base0ae4bf9. Escritor storage_crypto posee allí exclusivamente object_storage/codec.py, repository.py, rights_object_content.py y nuevo test_rights_object_verify_only.py. Tarea JSON ignorada con contrato/alcance/dependencias y diseño: evitar solo materialización plaintext duplicada durante verify→Discard, conservando GET/tombstones/SHA/AEAD/context/EOF/legacy/orden/close/2workers/quotas. Propuesta async no es evidencia ni ganancia. Agente no ejecuta pruebas/builds/instalaciones ni commits; root revisa y verifica N2 real/conjunta y métricas antes de integrar. Agentes nativos, ninguna nueva invocación Claude V1 ni publicación; consumo anterior conservado.


### Verificación combinada nativa/objetos — en curso

La N2 nativa `20261010-224551-2b3c5259` pasó637pruebas sin fallos/errores/omisiones, pero precede una corrección necesaria del loader: una carga fallida seguida de reintento podía reutilizar el pathname memfd y conservar el mapping anterior. Reproducción confirmada por root; se impide reintentar una inicialización fallida y se retiene un único descriptor sellado cuando dlopen fue intentado. Corpus host corregido127PASS, sin afirmar aceptación conjunta ni rendimiento. Commit provisional `aeafdd1`, no integrado en rama oficial.

N2 verify-only `20261010-230150-28dd5d65`:127PASS/0FAIL/0ERROR/0skips376,927s JUnit (379,854s paso pytest), ocho archivos con PostgreSQL17/Redis/RustFS reales. Todos los gates pasan, cinco hashes y HEAD intactos; retirada propia comprobada independientemente. Root revisó y creó commit provisional `3d110d0`. Se mantiene ciphertext staging y toda autenticación fresca; solo verify evita tempfile/readback de plaintext descartado. Elimina también el posible ENOSPC de ese tempfile innecesario; read conserva su comportamiento previo. No hay medida nueva de requests ni atribución de ganancia.

Root reunió ambos commits en worktree aislado native_canonical: HEAD `ea72a522fcb619352a4028cf1306f3b32152e738`. N2 conjunta48archivos/3workers lanzada23:09:19UTC, PID2591226/startticks339436932; plan ignorado `artifacts/root-review/native-verify-final-joint-plan.json`. Incluye corrección de reintento, corpus diferencial y verify-only. Fuentes y tres artefactos compilados congelados hasta terminal. No integración oficial hasta resultado exacto y revisión independiente; luego captura/use nueva manteniendo poblaciones, cuotas y objetivos originales. Memoria, N3, dos casos y aceptación completa siguen pendientes.


### MOD-08: canónica nativa y verify-only integrados localmente

Commits `a55ce87` y `034aa1e`; conjunta corregida `20261010-230920-aa4007af`:666PASS/0FAIL/0ERROR/0skips737,418s JUnit,48archivos/3workers, PostgreSQL17/Redis/RustFS reales. Todos los gates pasan, fuentes/artefactos intactos y retirada propia verificada independientemente. Integra validación canónica Cython con fallback exacto y loader memfd sellado; ABI/fuente/build/binario real forman identidad de reglas/baseline y congelación. Builder aislado Cython3.0.12, runtime sin compilación ni Cython. Pruebas conservan recursión/errores y rechazan reintento tras inicialización fallida para impedir reutilizar un mapping anterior por pathname FD.

Verify-only mantiene ciphertext staging, GET/SHA/tombstones/AEAD/contexto/SHA plaintext/EOF/autorización frescos; elimina solo tempfile/readback del plaintext que se descartaba. Read y legacy permanecen. También desaparece el ENOSPC de ese tempfile innecesario; no se presenta como equivalencia de fallos de recursos eliminados. N2 dirigida127PASS antes de conjunta; la conjunta previa637PASS precede corrección y no acredita la fuente final.

Aceptación funcional local, sin nueva ganancia de requests medida. Se prepara captura/use nueva con todas poblaciones/cuotas/objetivos originales; no reutilizar baseline previo tras fuente/binario cambiados. N3, dos casos simultáneos, memoria y todos los objetivos de latencia siguen pendientes; porcentajes contractuales sin incremento. [Evidencia saneada](../../docs/evidencias/mod08-native-verify-integrado-20261010.json).


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

Perfiles GET reales propagados por Caddy: json_download_proxy-97 y binary_download_proxy-98. Muestras perfiladas adicionales excluidas de p95. Esperas de workers, joins y validación SQL se solapan: no sumar ni atribuir coste del join como trabajo propio. La próxima hipótesis requiere desglose finito de verificación física por worker y reproducción SQL para distinguir lectura/AEAD/planificación/materialización antes de cambiar garantías. Sin cachear autoridad ni omitir verificaciones frescas. N3, dos casos, memoria y objetivos completos siguen pendientes; porcentajes contractuales sin aumento. [Evidencia saneada](../../docs/evidencias/mod08-medicion-native-verify-20261011.json).


### Siguiente diagnóstico acotado — worker físico

No hay ensayo funcional/performance vivo tras capture232333/use235349 terminales y retirada verificada. Objetivos originales incumplidos; no repetir idéntica medición ni declarar éxito. Root separa esperas del caller de trabajo físico por hilo. Nuevo worktree `web_modelos_mod08_worker_profile`, rama `codex/mod08-worker-profile`, baseefef41d, sin cambios previos. Escritor nativo canonical_tests posee exclusivamente tests/capacity_worker_profile.py y tests/test_capacity_worker_profile.py; contrato JSON ignorado artifacts/native-tasks/mod08-worker-profile.json. Solo helper diagnóstico y pruebas propuestas, sin edición de app, SQL, almacenamiento, auth, dependencias, pruebas/builds/instalaciones ni commits por agente. Root posee wiring WSGI, recogida, verificación, integración y aceptación.

Hipótesis: cProfile caller incluye joins/esperas y no CPU de workers. Contador acotado de dos workers futuros rights-object-verify, whitelist fija de fases y tiempos wall/threadCPU agregados, sin argumentos/refs/SQL/locals. Hooks previos/concurrencia deben declinar/restaurar; errores diagnósticos no alteran error dominio/teardown. Generadores y timings inclusivos se identifican, no sumar fases como wall. Primero equivalencia/negativas del helper; después diagnóstico real representativo. No atribuir planning PostgreSQL al tiempo cursor/wait: necesita prueba SQL separada. Instrumentación no acelera requests ni acepta N3/dos casos. No cambios en política de baseline por ahorrar tiempo; si fuentes instrumentadas cambian, capture previo queda inválido bajo contrato existente. Agente nativo autorizado por relevo usuario; ninguna invocación Claude V1 nueva ni consumo previo eliminado.


Worker diagnóstico: borrador fuente revisado por root; informe delegado wire rechazado por campos/STATUS/tipos inválidos, no tomado como éxito. Root corrigió estilo y restauración tras instalación parcial de hook, conectó scope al WSGI exclusivamente en requests extra marcados y añadió tests propios WSGI/objetos reales. Sin cambios de app. Corpus host final24PASS/0FAIL/0skips0,60s; no prueba PostgreSQL ni rendimiento. Test real nuevo observa28objetos y cada fase fresca, más contexto/ciphertext corruptos frente a ejecución nativa. Sin volcar refs ni datos.

N2 dirigida10archivos/1worker lanzada `20261011-000945-13945388`, PID2950973/startticks339799506, worktree worker_profile baseefef41d. Cinco fuentes locales y binario nativo exacto b1fc70995e9a congelados hasta terminal. Plan ignorado artifacts/root-review/worker-profile-directed-plan.json; gates y PG/Redis/RustFS reales pendientes. La rama oficial solo recibe este estado documental, no instrumentation hasta resultado/revisión. Hay un solo runner funcional propio. Objetivos2s/5s, doscasos/N3/criterios memoria permanecen pendientes.


### Worker diagnóstico aceptado funcionalmente — 2026-10-11

N2 `20261011-000945-13945388` terminal PASS:133PASS/0FAIL/0ERROR/0skips406,598s JUnit,10archivos/1worker; todos gates pasan. Root comprobó HEAD, cinco hashes revisados y retirada independiente PG/Redis/RustFS. Observación real28objetos:28segmentos object_verify/repository_verify/descriptor/codec_verify/header/authenticate_frames y56 tombstone/ciphertext_segments, con dos workers. Contexto incorrecto y ciphertext corrupto conservan errores y restauración. Commit candidato029cec4 integrado localmente. Instrumentación exclusiva de requests extra marcados, sin cambio de producción ni nueva ganancia de latencia. Nueva captura privada obligatoria por cambios en tests; se mantienen cuotas y poblaciones originales, p95 excluye muestras perfiladas. [Evidencia](../../docs/evidencias/mod08-worker-profile-20261011.json).

Investigación estática literal SQL de async_generation recibida con las10 claves normativas del contrato (root corrige su anterior referencia errónea a11). ClientCursor deshabilita preparación y prepare_threshold=None la impide también en Cursor. PREPARE literal cero parámetros preservaría representación pero su equivalencia ante sesión/DDL/constantes/errores no está demostrada; coste de planificación desconocido. Propuesta ignorada en selection_local, sin implementación, pruebas SQL ni aceptación. No cambiar política del driver ni introducir caché de planes sin evidencia.


Captura worker `20261011-001802-335fb1b9` falló antes de medir requests: Gunicorn no encontraba capacity_worker_profile porque root omitió copiar el helper junto al WSGI a /tmp. N2 anterior no cubría ese despliegue temporal;133PASS acredita su corpus, no el arranque de este launcher. Fuente intacta, ensayo terminal, retirada independiente de contenedores/red/volumen confirmada. Root corrige copia en tests/capacity_gunicorn.py; Ruff pasa. Se conserva evidencia negativa y se repite captura nueva sin reutilizar archivo fallido. Sin métricas nuevas ni cambio de objetivos.


### Captura worker y descarga negativa — 2026-10-11

Captura corregida `20261011-002254-0eb08988`, HEAD75c0eb7:1PASS/0FAIL/0ERROR/0skips1529,957s JUnit. Fuentes intactas y retirada independiente confirmada. Comparación con captura20261010-232333-7e99d547, misma población1509páginas/384grupos, uno perfilado excluido.

| TCP p95 | Anterior s | Actual s | Mejora | Objetivo s | Reducción pendiente | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recorrido completo | 3.778927 | 3.830352 | -1.36% | 2 | 47.79% | 383 |
| Lotes completos de cuatro páginas | 3.303774 | 3.269685 | 1.03% | 2 | 38.83% | 123 |

Sin nueva optimización de producción ni mejora consistente; diagnóstico de un caso, no N3/doscasos. [Evidencia saneada](../../docs/evidencias/mod08-worker-capture-20261011.json).

Uso `20261011-005219-bb4a38b6` terminal ERROR:1FAIL/0ERROR/0skips231,176s JUnit, HTTP404 en descarga JSON extra perfilada. No acepta sus latencias como medición completa. Fuentes intactas, recursos propios retirados independientemente. Perfil instrumentado33,527s y workers observados~31,63s; exceso de instrumentación como posible causa de superar TTL30, causalidad todavía no probada. Root encontró PurePath y ocho reconstrucciones de suffix en cada llamada del worker, también fuera de whitelist. Candidato aislado filtra nombre primero y precomputa suffix;24hostPASS0,37s y RuffPASS. N2 real10archivos activa `20261011-010036-8118d391`, PID3260838/startticks340104580, fuente congelada. No aumentar TTL ni relajar guards/cuotas/baseline. Porcentajes contractuales y objetivos originales permanecen pendientes.


Perfilador corregido: N2 `20261011-010036-8118d391`133PASS/0FAIL/0ERROR/0skips372,141s JUnit, todos gates0, HEAD/hash revisados intactos y retirada independiente PG/Redis/RustFS confirmada. Candidatof39f8ad filtra funciones antes de PurePath y precomputa suffix fijos, sin cambiar whitelist/timings/guards/TTL. Integración local por root; sin ganancia de requests demostrada. Próxima captura privada nueva por cambio de fuente; no reutilizar baseline anterior ni ampliar TTL30.

## Captura corregida 2026-10-11, run20261011-010742-bffcf011

HEADf3da868; fuente intacta,1PASS0FAIL0ERROR0skip,JUnit1535,829s. Ausencia de contenedores/red/volumen propios verificada independientemente. Un caso sintético completo, diagnóstico; no N3/dos casos.

| Métrica TCP p95 | n | Anterior(s) | Nueva(s) | Mejora | Objetivo(s) | Reducción pendiente |
|---|---:|---:|---:|---:|---:|---:|
| whole | 383 | 3.830352 | 3.855044 | -0.645% | 2 | 48.120% |
| matched123 | 123 | 3.269685 | 3.353515 | -2.564% | 2 | 40.361% |

Sin mejora demostrada; cambios de observación, sin optimización productiva nueva. Descargas iniciadas misma fuente/baseline,PID3486601/startticks340333422. Memoria upper bound propia1944403968B y almacenamiento ceiling5939134496B; no extrapolar a dos casos. Evidencia sanitizada ignorada conservada para versionar al terminar congelación. Ultrareview gratuita1of3 realmente lanzada en clon independiente; restantes2 reservadas.

## Descargas corregidas, run20261011-013845-8f422a1a

HEADf3da868; fuente/baseline intactos;1PASS0FAIL0ERROR0skip,245,461sJUnit. Limpieza propia verificada independientemente. Un caso completo diagnóstico, no aceptación dos casos/N3.

| Fase | n | Anterior(s) | Actual(s) | Mejora | Objetivo(s) |
|---|---:|---:|---:|---:|---:|
| generation | 1 | 32.078407 | 33.482033 | -4.376% | 120 |
| final_preparation | 1 | 10.446689 | 10.957687 | -4.891% | 30 |
| final_inspection | 1 | 3.369607 | 3.042530 | 9.707% | 30 |
| final_approval | 1 | 3.268270 | 3.316173 | -1.466% | 5 |
| closure | 1 | 11.279068 | 10.733944 | 4.833% | 30 |
| json_download | 3 | 6.048998 | 6.467847 | -6.924% | 5 |
| binary_download | 8 | 6.529290 | 6.915486 | -5.915% | 5 |

n1 no p95; n3/n8 p95 nearest-rank es máximo muestral, inferencia limitada. JSON/binario requieren reducir1,467847/1,915486s respectivamente. Cuatro perfiles extra completos con540eventos,27objetos/2hilos, sin404. Observación inclusiva solapada, excluida p95; aún no calibrada para atribuir coste productivo. No sumar fases ni extrapolar dos casos. Evidencia docs/evidencias/mod08-medicion-worker-corrected-20261011.json.

## Observador de fases listado asignado 2026-10-11

Root crea worktree /home/felidae/proyectos/web_modelos_mod08_phase_spans branchcodex/mod08-phase-spans BASE854bc8f. Native canonical_tests propiedad exclusiva nuevos tests/capacity_phase_spans.py y tests/test_capacity_phase_spans.py; sin modificar producción/WSGI ni contenedores. Wrappers de límites fijos y contadores SQL, sin hooks por evento ni valores privados; root revisa equivalencia/restauración/overhead antes de aplicar. Host tests no aceptación real. No nueva invocación Claude; ultrareview1of3 única sigue activa, estado5found1verified4refuted observado, informe final pendiente.

Root revisa/commit candidatos03530e3 sessions y5a1ebbf listing-spans, cherry-picks48c8983/4f08069 sólo integración, pendientes aceptación. HOSTsessions7PASS0.28s; observer+WSGI25PASS0.33s/RuffPASS. Root añade2pruebas PostgreSQL equivalencia/auditoría/rollback exacto. Joint14files1worker fixture-snapshots/librdb pinned,PID3587657/startticks340431386; fuente integración congelada hasta terminal. No nueva medición capacidad todavía. Propiedad storage_crypto4files aislados; observer canonical_tests2newfiles/rootWsgi+gunicorn+realtests. Ultrareview única activa sin relanzamientos.

N2 conjunto terminal20261011-015504-8ec5be01:184PASS0FAIL0ERROR0skip409,427sJUnit,9steps0,1148sourcehashes/rootHEAD4f08069 verificados. PGRedis propios y labelobjecttests ausentes. Session/observer aceptados funcionalmente, sin resultado rendimiento ni aceptación final. Evidencia docs/evidencias/mod08-phase-session-functional-20261011.json. Ultrareview1of3 sigue en deduping,5verified; no relanzar. Preparar captura nueva sólo tras informe/correcciones que puedan invalidar fuente; evitar carrera de congelación.

## Ultrareview terminal 2026-10-11 02:04 UTC

Informe original recuperado del evento terminal rayg2okuq: tres hallazgos, todos nit (duplicación de validadores, constantes de compilación duplicadas y recorrido repetido de pila). Ningún hallazgo final bloqueante ni reducción de latencia demostrada. La referencia a KernelIntegrityError en el segundo comentario no constituye un hallazgo final independiente; comprobar localmente antes de inferir un fallo. Mantener el cuerpo Python en su frame para conservar semántica en límites de recursión; no aplicar unificación sugerida sin pruebas diferenciales. Las pruebas diferenciales nativas existentes deben revisarse antes de añadir duplicados. Observador de fases y Session tienen aceptación funcional real184PASS; siguiente paso medir con nueva captura privada y fuente congelada, conservando objetivos completos2s/5s y dos casos/N3. Una revisión gratuita consumida; otras dos reservadas. Remote Control activado por petición expresa del usuario en la misma sesión. Informe original: docs/evidencias/mod08-ultrareview-20261011.json.

## Medición terminal Session/observador y candidatos ultrareview — 2026-10-11

# Captura diagnóstica terminal: 20261011-020846-91bc994a

Un caso sintético completo; no constituye aceptación de dos casos/N3. Código anterior a los candidatos streaming/ultrareview. Fuentes sin cambios y limpieza comprobada independientemente.

| Métrica | Anterior (s) | Actual (s) | Reducción | Objetivo (s) |
| --- | ---: | ---: | ---: | ---: |
| whole p95 | 3.855044 | 3.806976 | 1.247% | 2 |
| matched123 p95 | 3.353515 | 3.204901 | 4.432% | 2 |

Fases del request diagnóstico adicional: inclusivas y solapadas; no se suman ni se incluyen en el p95. Sin medición anterior comparable.

| Fase | Anterior | Actual wall (s) | CPU del hilo (s) | Llamadas |
| --- | --- | ---: | ---: | ---: |
| authorize | No disponible | 0.275080 | 0.130508 | 23 |
| baseline | No disponible | 0.063026 | 0.057634 | 4 |
| batch | No disponible | 2.893509 | 1.812021 | 1 |
| compile | No disponible | 0.072345 | 0.071675 | 1 |
| page | No disponible | 1.903644 | 1.311720 | 4 |
| record | No disponible | 1.122174 | 0.789875 | 4 |
| source | No disponible | 0.640023 | 0.317613 | 1 |
| unseal | No disponible | 0.085661 | 0.079463 | 237 |
| validate_selection | No disponible | 0.274770 | 0.213382 | 4 |

| Etapa | Muestras | Anterior (s) | Actual (s) | Variación | Objetivo (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| generation | 1 | 33.482033 | 45.715597 | +36.538% | 120 |
| final_preparation | 1 | 10.957687 | 15.013529 | +37.014% | 30 |
| final_inspection | 1 | 3.042530 | 3.540519 | +16.368% | 30 |
| final_approval | 1 | 3.316173 | 4.193057 | +26.443% | 5 |
| closure | 1 | 10.733944 | 15.265296 | +42.215% | 30 |
| json_download | 3 | 6.467847 | 7.040080 | +8.847% | 5 |
| binary_download | 8 | 6.915486 | 8.191270 | +18.448% | 5 |

Captura 20261011-020846-91bc994a y use 20261011-023840-83be1976: 1 PASS cada uno, cero fallos/errores/skips; fuente 1e53347 e inputs use sin cambios. Limpieza propia comprobada independientemente mediante docker ps -a. No aceptación dos casos/N3. Las descargas empeoran y no se atribuye causa sin evidencia. n1 no p95; n3/n8 nearest-rank inferencia limitada. Evidencia docs/evidencias/mod08-medicion-listing-phases-20261011.json.

Usuario autoriza implementar hallazgos sensatos de ultrareview. Root revisa tres respuestas: constantes compartidas, pruebas diferenciales conservando frames Python y recorrido de pila acotado con criterio original. Borradores 43a5b76/3301779; joint d4899de suma streaming 3cae1a2 y fases detalladas e867064. Propiedad nativa explicitada en planes ignorados. Sin integración aún. Build inicial con .venv falla por Cython ausente; compilación aislada uv --with Cython==3.0.12 termina0, loader native-sealed, Ruff11archivos0. Real20files 20261011-024759-73a25061, PID3911469, todavía activo. No mejora atribuible a estos candidatos antes de nuevas mediciones.

Aclaración solicitada en sesión Claude existente sin nueva ultrareview ni edición/pruebas: referencia KernelIntegrityError no tiene evidencia independiente. Root comprueba propagación fail-closed y callers; docs/evidencias/mod08-ultrareview-aclaracion-20261011.md. Una ultrareview utilizada y dos reservadas. Usuario pregunta por mypyc/Cython: kernel Cython ya existente; evaluar ampliación sobre costes CPU concretos tras fases detalladas, no sustituir esperas I/O ni prometer ganancia.

Joint20files primer gate terminal20261011-024759-73a25061:363PASS1FAIL0ERROR0SKIP418,759sJUnit, fuentes sin cambios, limpieza PGRedis/objetos comprobada independientemente. Fallo diagnóstico: esperaba ciphertext_segments del generador eliminado por streaming. Root16fcc9a cambia solo3archivos test: nuevas fases qualified _HashedBodyReader._fetch/finish y prueba anti-colisión, conteos reales28finish/56tombstone/fetch>=56. RuffPASS. Batería completa repetida20files PID3964620/startticks en plan ignorado, aún activa. Sin integración ni aceptación. Evidencia docs/evidencias/mod08-stream-phase-joint-first-gate-20261011.json.

Joint corregido20261011-025620-6fa04899:365PASS0FAIL0ERROR0SKIP405,490sJUnit. Root confirma1151sourcehashes y14archivos revisados,20selecciones reales y todos9steps0; native-sealed/Cython3.0.12, limpieza PGRedis/objetos independiente. Integrados56c0fdb/c4a7f29/4c6b5a9/738feb5/ef94e50. Fuentes runtime integración iguales a candidato16fcc9a; artefacto compilado verificado trasladado conservando antiguo en ignorados, identidad validada. Aceptación funcional, aún sin ganancia ni N3/dos casos. Evidencia docs/evidencias/mod08-stream-phase-joint-corrected-20261011.json.

MOD-08 2026-10-11: ciclo streaming/fases terminal: captura 20261011-030418-57a8298d y use 20261011-033358-7f0a2acc. Verificados 1151 hashes por ejecución y retirada propia independiente. Listado383lotes p95 3,806976→3,885480s (empeora2,06%); subconjunto123 3,204901→3,376274s (empeora5,35%). JSONn3 7,040080→6,908405s (mejora1,87%); binarion8 8,191270→7,705974s (mejora5,92%). Objetivos2s/5s y dos casos/N3 pendientes. Cuadro y evidencia: docs/evidencias/mod08-medicion-stream-phase-20261011.md/.json. SHA aislado9ensayos alternados: hashlib vs cryptography sin ventaja útil; conservar hashlib. Revisión CPU no identifica bucle Python con margen suficiente para ampliar Cython. Nuevo diagnóstico factory/constructor/transporte delegado a storage_crypto en worktree codex/mod08-factory-profile, propiedad exclusiva tests/capacity_worker_profile.py y tests/test_capacity_worker_profile.py; no cambios productivos ni autoridad cacheada.

MOD08 factory diagnostic integrado: agente54eba6d + root30acd1f, gate real20261011-034708-b420ed67:77PASS0fallos/errores/skips12,251s. Root1148hashes y retirada propia verificados;28repositorios frescos,28lecturas de transporte y2constructores por operación2workers. Instrumentación solo, sin mejora de latencia acreditada. Evidencia docs/evidencias/mod08-factory-profile-gate-20261011.json.

MOD08 diagnóstico factory terminal: captura20261011-034833-051ebabc/use20261011-041853-bfd4c4a8 ambos1PASS0fallos/errores/skips.1151hashes cadauno y retirada propia comprobados. Listado383p953,865976s;JSONn3p957,313810s;binario n8p957,418959s. Cuadros y todas métricas docs/evidencias/mod08-medicion-factory-20261011.md/.json. Setup perfilado dominado por constructor primero1/workerno por hits. Análisis de constructor másligero pendiente, sin prometerganancia. Objetivoscompletos2casos/N3/2s/5s pendientes.

Experimento constructor cliente9ensayos alternados sinHTTP/profiler: boto3mediana wall0,101383s/CPU0,099833s;botocore0,094788s/CPU0,094089s. Ahorro6,6ms/cliente; no se aplica sustitución por margen insuficiente y hooks/métodos/user-agent distintos. Loader/modelos mutables no se comparten. Evidencia docs/evidencias/mod08-client-constructor-benchmark-20261011.md/.json. No mejora request atribuible.

MOD08 tiempos emparejados integrados: agente e78e32b, runtime 0d7c175. Gate real20261011-043924-04545920:59PASS0fallos/errores/skips6,013s;1150hashes y retirada propia comprobados. Primer gate56PASS3errores de arranque por imagen RustFS ausente; recuperado digest fijado y repetido PASS, evidencia negativa conservada. IDs alineados con TODOS los lotes TCP, incluidos parciales; extra perfilado excluido. Relojes WSGI wall/CPU incluyen consumo y close, sin cProfile/SQLhook; límites2048registros/256KiB. No optimización ni mejora acreditada. Evidencia docs/evidencias/mod08-paired-request-timing-gate-20261011.json. Nueva captura/use pendiente; aceptación completa doscasos/N3/2s/5s intacta.

MOD08 diagnóstico paired terminal:captura20261011-044039-31315f79/use20261011-051029-5ac023d6 ambos1PASS0fallos/errores/skips;1153hashes cadauno y retirada propia verificados. Listado383p953,802134s vs3,865976s (-1,65%);JSONn3p956,906630s vs7,313810s (-5,57%);binario n8p957,485222s vs7,418959s (+0,89%). Misma petición p95 ID327WSGI3,800317s/threadCPU2,066251s;CPUincluye nativo, espera/desplanificación no clasificada. Sin optimización productiva ni ganancia atribuida. Cuadro completo docs/evidencias/mod08-medicion-paired-20261011.md/.json. Siguiente diagnóstico fases emparejadas para elección concreta; no aceptación2casos/N3/2s/5s.

MOD08 fases emparejadas integradas:agente0edeb33/runtime4be6408. Gate real20261011-052545-6cf932cf:244PASS0fallos/errores/skips12,973s;1153hashes y retirada propia comprobados; kernelCythonreal cargado.19fases conwall/CPU inclusivo y exclusivo del mismorequestID. Registrosnuméricos8MiB/2048/4pages; flagsregistro/fase incompleta separados. Sin importsdominioanticipados: primeras fasesfaltantes explícitas, poblaciónTCP383intacta. ExclusiveincluyeSQL/trabajonoobservado; no atribuirPython/nativo sin evidencia. Sin optimización productiva ni mejora medida; siguiente nueva captura/use. Evidencia docs/evidencias/mod08-paired-phase-timing-gate-20261011.json. Criterios completos2casos/N3/2s/5s intactos.

MOD08 diagnóstico de fases terminal: captura20261011-052705-a77a598a/use20261011-055827-ff2d3cd6; 1PASS cada uno, cero fallos/errores/skips,1153hashes por ejecución y limpieza independiente. Listado383p95 3,934962s frente a3,802134s (+3,49%);JSONn3p95 7,812455s frente a6,906630s (+13,12%);binario n8p95 7,710310s frente a7,485222s (+3,01%). Sin ganancia atribuida ni aceptación completa. Cuadro y19fases del mismo requestp95 en docs/evidencias/mod08-medicion-phase-paired-20261011.md/.json. SQL447/wall1,763513s/threadCPUtotal1,932104s solapados. Candidata runtimeSQL en revisión, no implementada; preservar evidencia de sellos además de boolean.
