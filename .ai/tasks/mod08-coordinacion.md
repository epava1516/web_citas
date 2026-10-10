# MOD-08 — coordinación de frentes en paralelo

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
