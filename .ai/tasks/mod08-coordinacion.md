# MOD-08 — coordinación de frentes en paralelo

Actualizado: 2026-10-10 12:16 UTC. Coordinador: Claude principal (MOD-07). Plan: docs/95-plan-modernizacion-mod08.md. Cada frente mantiene su estado en `.ai/tasks/mod08-<frente>.md` y hace commits frecuentes en su rama; el coordinador integra en master tras N2 conjunta con el runner paralelo.

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
