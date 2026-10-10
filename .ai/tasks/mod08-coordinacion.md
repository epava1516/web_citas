# MOD-08 — coordinación de frentes en paralelo

Actualizado: 2026-10-10 12:16 UTC. Coordinador: Claude principal (MOD-07). Plan: docs/95-plan-modernizacion-mod08.md. Cada frente mantiene su estado en `.ai/tasks/mod08-<frente>.md` y hace commits frecuentes en su rama; el coordinador integra en master tras N2 conjunta con el runner paralelo.

## Relevo vigente a Codex — 2026-10-10

Usuario: «Claude … se ha quedado sin tokens, continúa tú desde donde lo dejó». Codex retoma coordinación, implementación, verificación e integración local; conserva criterios y consumo histórico. Tres agentes nativos escritores en worktrees existentes, sin invocar Claude V1 ni modificar su adaptador. Base integrada `209f014`: xdist ya integrado tras 414 PASS/0 skips en `20261010-115833-c37b6bfa` (1109,918 s JUnit); el estado «en curso» de la tabla anterior es histórico.

Propiedad: Codex `../web_modelos_claude_srcver` (huella3/sello4); `async_generation` worktree `agent-ab23eda63576809b3` (job/modelo/migración0113/vistas de generación/tareas/plantilla/pruebas); `storage_crypto` `agent-a52e0d2a35a796e8f` (AEAD/repositorio S3/nuevas vistas de entrega/configuración/Compose/Caddy, migración0114 provisional); `canonical_tests` `agent-aca043e68c0f1196d` (canónica/row_reference/pruebas) y después `agent-a1ea0524fd9545f88` (fixtures rápidos). Modelos/migraciones se reconciliarán antes de N2 conjunta. Evidencia inmutable y revisión por lotes quedan para el siguiente bloque dependiente; su preparación anterior permanece conservada.

No hay pytest/capacidad propio vivo al reconciliar. Ramas sin commits nuevos salvo xdist y source-version; canónica contiene únicamente dependencias sin commit y source-version contiene sello sin commit. Fuentes previas preservadas antes de corregir. Pruebas pesadas se programan por ventana; ninguna carga de capacidad junto a compilación/pytest. Una sola integración activa, estados de cada pieza independientes de aceptación CR09/N3.

Hipótesis finitas de revisión3/4: `xmin` aislado no distingue dos UPDATE dentro de una misma transacción; reproducir y añadir identidad de tupla si se confirma. El sello inicial calcula resultados al reproducir SELECT después de la validación y pierde orden al ordenar texto: debe probar que exactamente los resultados realmente consumidos y sus dependencias temporales/externas se conservan, antes de omitir la validación completa. Criterio N1: reproducciones significativas PG17, corrección y tests afectados PASS; N2 posterior: selección de49 archivos exportación/cierre/descargas/autoridad más pruebas3/4, cero skips, fuentes congeladas y retirada real. No se acredita p95 ni N3 por este registro.

| Frente | Piezas | Responsable | Rama / worktree | Estado |
| --- | --- | --- | --- | --- |
| Huella de fila + sello de validación | 3, 4 | coordinador | `claude/source-version` / `../web_modelos_claude_srcver` | 3: `4ea995e`, 12 PASS completitud; 4: código y pruebas escritos sin ejecutar |
| Pruebas paralelas (xdist) | 9 (base) | coordinador | `claude/parallel-tests` / `../web_modelos_claude_xdist` | `9cb8214`; validación 414 casos con 6 workers en curso (run `20261010-115833-c37b6bfa`) |
| Generación asíncrona Celery | 5 | agente async-generation | worktree propio | en curso |
| AEAD + objetos MinIO + descargas Caddy | 6, 8 | agente storage-crypto | worktree propio | en curso |
| orjson + BLAKE3 | 7 | agente fast-canonical | worktree propio | en curso |
| Instantáneas de fixtures + auditoría de duplicados | 9, 10 | agente test-speed | worktree propio (sobre `claude/parallel-tests`) | en curso |
| Evidencia inmutable + cadena de hashes | 11 | agente immutable-evidence | worktree propio | en curso |
| Revisión por lotes auditados | 12 | pendiente | — | lanzamiento de agente denegado por el clasificador de modo automático; lo hará el coordinador tras 3/4 o con permiso del usuario |
| mypyc/Cython | 13 | — | — | condicional a perfiles |

Reglas: sin mediciones de capacidad mientras haya pruebas; garantías y objetivos intactos; integración solo tras N2 conjunta PASS.
Siguiente paso del coordinador: leer terminal de la validación paralela; si 414 PASS, integrar `claude/parallel-tests` en master; ejecutar pruebas del sello y micro-medición de la huella.
