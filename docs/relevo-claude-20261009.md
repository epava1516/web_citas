# Relevo técnico local — 2026-10-09

**Actualización MOD-07 vigente:** por aclaración posterior del usuario, Claude continúa directamente como agente principal con lectura/escritura/herramientas/pruebas/commits e integración/aceptación local. No limitar su goal a propuestas. Codex sigue pausado; reglas vigentes en AGENTS y docs16§15. Las secciones de incompatibilidad/autorización no adoptada inferiores describen el corte previo. No se modifica el adaptador V1 ni el contrato externo; se registra excepción local de autoridad para el agente principal. [Prompt actualizado](prompt-relevo-claude-20261009.md).

Goal **pausado** por orden del usuario. No se avanzó a otro bloque ni se invocó a Claude. El inventario de Docker/redes/systemd y procesos confirma ausencia de verificaciones propias vivas y de recursos de sus runs; servicios normales intactos. No se ha publicado, hecho push, contratado, usado datos reales ni reescrito historia.

## Git y conservación

Base del trabajo: `2e4f6b64e15b68f70a5298ec401fb9b94a658642` en `master`, igual al `origin/master` local antes de los commits del relevo; no se consultó la red. El HEAD final es el commit que contiene este informe: obtenerlo con `git rev-parse HEAD`. Los commits preparados y su orden quedan en [inventario del relevo](evidencias/relevo-local-20261009.json); el hash del propio informe se comunica al entregar, para evitar autorreferencia.

Commits de trabajo terminado, exclusivamente locales:

| Commit | Trabajo |
| --- | --- |
| `d8cad736` | Instrumental sin consumidores, rutas/lint y conservación de originales/evidencia negativa de limpieza. |
| `32d54e7e` | CI local y herramientas nativas; Actions solo manual, corrección de envelopes conocidos. |
| `53a1c677` | Paginación/0111, autoridad/correo, restauración y correctivas binarias verificadas en sus selecciones. |
| `49a771c3` | Fixtures realistas y arneses escalar/TCP/perfil; no capacidad integral. |
| `HEAD` | Organización/contrato/estado pausado, matrices, evidencias y relevo. |

Antecedentes relevantes: `7691642` aceptación local CR09-REND-LECTURA; `1a10ecf` cobertura positiva PRODUCTION/checked; `88fdbb0` reconciliación residual; `2e4f6b6` bloqueos independientes. No equivalen a CR09 integral ni a despliegue de los cambios actuales.

Inventario inicial completo:220 entradas;209 propias terminadas/verificadas en su alcance,4 retiradas de instrumental,6 propias incompletas y1 documento fuera de contrato de procedencia no confirmada. Las fuentes de aplicación actuales coinciden con el último N2 de63PASS. El único archivo del manifest funcional modificado después fue `scripts/check_capacity_environment.py`; durante el relevo se actualizó además el plan `.ai/tasks/desarrollo.md`, conservando su consumo. Evidencia por archivo/huella y política de commit en el JSON, no inferida desde número de pruebas.

Ramas locales: once commits no antecesores de master, tres en `codex/cr09-inspection-hotfix` y ocho en `codex/cr10-catalog-prep`; `git cherry` marca todos con `-`, equivalentes ya integrados. Las demás ramas locales no tienen commits exclusivos. Se conservan las once ubicaciones de worktree (diez externas limpias) y todas las ramas; no se elimina trabajo por no ser antecesor. Los antiguos prototipos de lectura presentes solo en referencias remotas almacenadas no autorizan una integración nueva.

Quedan **sin commit**, preservados byte a byte:

| Archivo | Motivo |
| --- | --- |
| `scripts/check_capacity_environment.py` | Instrumento en curso; controlador global añadido después de63PASS, no ejecutado, Ruff F401 y presupuesto/almacenamiento sin concluir. No se vuelve silenciosamente a su versión anterior. |
| `scripts/run_capacity_environment.py` | Lanzador experimental; ninguna ejecución nativa ni comprobación integral de aislamiento/presupuesto. |
| `scripts/capacity_artifacts.py` | Helper del prototipo:8PASS N1 puro, no integración con controlador. Se mantiene junto a su capacidad incompleta. |
| `tests/test_capacity_artifacts.py` | Ocho casos puros del helper; no aceptación del controlador. |
| `tests/capacity_delivery_flow.py` | Driver del flujo grande: guardado/revisión ejecutados, etapas posteriores no alcanzadas ni verificadas. |
| `tests/test_capacity_delivery_complete.py` | Consumidor del driver incompleto; no ejecución completa satisfactoria. |
| `docs/propuesta-graphql-manual.md` | Propuesta independiente de lanzamiento manual, fuera del contrato; procedencia no confirmada en este corte. No implementar ni incorporar al backlog. |

Las seis fuentes incompletas y el XML N1 se conservan también en [archivo del prototipo](evidencias/relevo-prototipo-capacidad-20261009-artefactos.tar.gz). No son herramientas descartadas: tienen consumidores/proyecto de continuación. Los archivos de evidencia negativa son necesarios y se conservan. Los logs brutos del adaptador Claude siguen ignorados; no se versionan. Se preserva `/tmp/web-modelos-librdb-v2.4.0`, checkout nativo reutilizable, no temporal de un run.

## Terminales y límites

Último N2: `20261009-201631-db21c6aa`, **63PASS/0FAIL/0ERROR/0SKIP,467,214s JUnit** (467,33s CLI). PostgreSQL17/Redis7.4 propios, herramientas nativas y Chromium; checks, migraciones dry-run, Ruff y documentación PASS en ese corte. `sources_unchanged=true` y retirada confirmada. Archivo SHA-256 `4ea02d33620e48e7cdd2bf2d5eb196805406b86ff04d6e0eb6e54a8c31d1f03f`:1.020 fuentes contrastadas con el manifest. [Informe original](evidencias/revision-binaria-candidatos-n2-correctiva-20261009.json). Corrige referencias de candidatos y auditoría final tras leer bytes, con rechazo/rollback ante borrado tardío. No acredita p95, capacidad global ni N3.

Helper de artefactos:8PASS/0SKIP,0,147s JUnit; puro filesystem. Lanzador no probado. Comprobación de limpieza: **13PASS/1FAIL,11,09s CLI**; `test_gc_timestamps_share_standard_generator_monotonic_origin` emitió2peticiones frente a3esperadas. Las fuentes de prueba/observadores coinciden con el HEAD original, no se modificaron al retirar los cuatro archivos; causa sin diagnosticar, no atribuirlo a GC/carga del host como hecho. [XML y fuentes negativos](evidencias/relevo-limpieza-20261009-artefactos.tar.gz).

Limpieza autorizada: confirmada ausencia de consumidores actuales con búsqueda en apps/config/scripts/tests/CI. Se consolidan las retiradas de `benchmark_call_profile.py`, `benchmark_local_monitor.py` y sus dos tests exclusivos,337líneas. El grafo existente conserva nodos históricos; no se usa para afirmar ausencia vigente. Antes hubo14PASS de instrumental conservado; el nuevo13PASS/1FAIL se registra sin sustituir el antecedente ni declararlo verde. No hay nuevos recursos Docker que retirar en este relevo: los runners ya retiraron contenedores PG/Redis/app, red, Gunicorn y temporales; el inventario confirma ausencia. No se borra otro elemento de utilidad/procedencia dudosa.

Fallos/requisitos abiertos: último p95 binario válido **2,372175/2,395124s >2s**; no medido tras63PASS. Guardado binario20muestras/caso dio4,064946/3,801835s≤5s en su variante. Cobertura completa, inspecciones, generación, respuesta final, cierre y descargas del escenario grande siguen NOT_PROVEN. Cuotas completas del controlador, almacenamiento20GiB y pico global6GiB no acreditados. Ruff del árbol completo tiene F401 por MAX_FILES sin usar en el prototipo sin commit. Fallo temporal GC arriba conservado. CR09 conjunto/N3 y las filas restantes de matriz83, CR10, GS01, BF/BB y C siguen abiertos. Restauración2PASS, conservación43PASS, correo/autoridad/urgencias73PASS, escenario escalar de capacidad y componentes de matriz88 se reutilizan únicamente en sus alcances, sin sumarlos como aceptación común. No se recalculan los porcentajes de docs86/v10.

Comprobaciones finales del relevo: documentación162Markdown/23copias históricas protegidas PASS; diff del worktree PASS. Diff completo del índice detecta una línea vacía al final de la copia histórica exacta de contrato16 anterior a consolidación; se conserva su SHA original, y todos los demás archivos staged pasan diff-check.  colección del árbol actual2.145casos en2,05s, solo imports/colección, no ejecución. Ruff **global del snapshot a commit PASS sin exclusiones**; Ruff **del árbol actual FAIL** por el único F401 del prototipo sin commit. Snapshot privado retirado. [Logs](evidencias/relevo-comprobaciones-20261009-artefactos.tar.gz), [alcances y comandos](evidencias/relevo-local-20261009.json).54huellas de archivos declaradas en metadata9Oct contrastadas; originales y negativos preservados.

## Continuación exacta

Primero reconciliar inventario, commits y seis fuentes incompletas; revisar el diseño del controlador global y su contabilidad/almacenamiento, sin ejecutar cargas con instrumentos no validados. Resolver el diagnóstico Ruff y el fallo temporal del instrumental conservado mediante hipótesis finita/prueba pertinente. Después de controles efectivos completos y recursos propios reservados, comprobar el recorrido binario corregido con los criterios inmutables; conservar FAIL/INVALID/NOT_PROVEN y completar etapas no probadas. Consolidar censo/identidad/cobertura y demás filas pendientes de matriz83 y N3 en la versión integrada. Orden **CR09 → CR10 → GS01 → BF/BB → C**. No reabrir lectura aceptada ni reiniciar bloques cerrados sin riesgo concreto. Esta es la continuación preparada, no una orden de reanudar el goal pausado.

## Gobernanza vigente

AI_ENGINEERING1.0.1 leído **completo**. Regla explícita: «V1 delegates no direct edits or Git operations»; adaptador V1 sin herramientas, solo propuestas, FILES_CHANGED/TESTS_RUN vacíos. «Only Codex controls commits, merges/cherry-picks and integration» y solo Codex acepta. AGENTS y docs16§15: **Claude propone; Codex aplica y verifica**. La autorización de invocaciones ilimitadas elimina el contador máximo, no el aislamiento ni atribuciones. Ocho históricas conservadas, nuevas cero.

Por ello, un goal de Claude que ejecute/aplique toda la entrega de forma autónoma **es incompatible con el modelo vigente**. El [prompt preparado](prompt-relevo-claude-20261009.md) sirve para continuación como delegado de propuestas, bajo coordinación Codex; no se presenta como relevo operativo completo. La primera tarea acotada es revisión del prototipo de controlador; Codex suministra snapshots dentro del contrato de tarea y aplica/verifica las propuestas. No invocar ahora. No pegar el prompt en un entorno con permisos de escritura como autorización implícita para usarlos.

## Autorización necesaria para un relevo directo

Texto concreto propuesto, **no adoptado**: «Para la entrega técnica local restante de web_modelos, designo a Claude como agente principal y le autorizo a leer/editar el repositorio, ejecutar verificaciones locales reales, aplicar correcciones, gestionar commits e integración local y aceptar técnicamente con las evidencias del contrato; Codex deja de ser el aplicador/verificador exclusivo. Mantener objetivos y criterios, protección del trabajo existente, datos sintéticos, PostgreSQL real, CI propio sin gasto y prohibición de push/publicación/proveedores/datos reales. Registrar la nueva autoridad en AGENTS.md y docs16§15. La ejecución principal directa usará un procedimiento de escritor con herramientas nativas, propiedad/base de trabajo explícitas y registro de pruebas; el adaptador V1 oficial sin herramientas se conserva para delegaciones acotadas y no se copia ni altera.»

Además habría que revisar/versionar esa excepción de gobernanza frente a AI_ENGINEERING1.0.1, cuyos controles Git/aceptación/ejecutor actual no habilitan escritor directo. No modificar automáticamente el contrato externo o el adaptador para eludirlo. No hay autorización de esta modificación en la petición actual.

Intervención del usuario: autorizar ese cambio de dirección/atribuciones si desea relevo directo, o reanudar expresamente la continuación Codex si mantiene el modelo; cualquier cambio material del alcance/objetivos/coste, uso de identidad/datos reales, proveedor/credenciales/acción externa o intervención en recursos ajenos. Los objetivos técnicos ya delegados, correcciones compatibles y fixtures ordinarios no requieren aprobación por hito. Falta de cuota efectiva exige alternativa técnica válida propia, no cambiar límites para lograr PASS; solo escalar si ninguna alternativa cabe sin afectar recursos ajenos/gasto.
