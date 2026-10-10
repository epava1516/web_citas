# Plan de modernización técnica — MOD-08

Fecha: 2026-10-10. Autoridad: decisión del usuario registrada en [contrato16 §MOD-08](16-contrato-ejecucion-desarrollo.md#mod-08--modernización-técnica-del-núcleo-autorizada-2026-10-10). Redactado por Claude principal (MOD-07) para que cualquier agente —incluido Codex si retoma la dirección— pueda continuarlo sin depender de la conversación. Estado y cola vigentes: [seguimiento17](17-seguimiento-desarrollo.md).

## Principios no negociables

- Objetivos y criterios intactos: [objetivos de capacidad](evidencias/objetivos-capacidad-local-20261009.json) (2 casos simultáneos, 1.500 revisiones, 16MiB JSON, 64MiB originales, 4CPU/8GiB/20GiB, swap0, pico ≤6GiB, RSS ≤1GiB, páginas ≤50 filas p95 ≤2s, guardar/aprobar ≤5s, generar ≤120s, final/cierre ≤30s, paquetes ≤8MiB p95 TCP ≤5s), contratos funcionales, privacidad, autoridad fresca, auditoría, idempotencia, locks y transacciones.
- Una sustitución cambia **cómo** se demuestra una garantía, nunca la garantía. Cada pieza: diseño breve, pruebas de equivalencia y de completitud por fuente/mutación con PostgreSQL real, N2 propia con fuentes congeladas y retirada verificada, registro en seguimiento17.
- Sin producción ni datos reales: los digests y artefactos sintéticos pueden regenerarse si cambia una forma canónica; la evidencia histórica se conserva como tal.
- Sin proveedores externos, compras ni publicación. Servicios nuevos solo autoalojados en Docker propio.

## Diagnóstico que motiva el plan

Perfiles a escala objetivo ([caso completo](evidencias/capacidad-perfil-caso-completo-20261010.json), [entrega completa FAIL](evidencias/capacidad-entrega-completa-20261009.json)): la seguridad del núcleo de derechos se demuestra **re-derivando todo en cada petición** (dos copias del origen de ~17MB, recompilación de cobertura, revalidación de 1.509 páginas e imágenes). Coste O(tamaño del expediente) por clic: lecturas ~2,7s, etapas finales ~12,5s y descargas ~9,5s con un caso.

## Componentes, diseño y estado

| # | Pieza actual | Sustitución | Garantía y cómo se demuestra | Ganancia estimada | Estado |
| --- | --- | --- | --- | --- | --- |
| 1 | Repetición de trabajo en validaciones | Equivalencias exactas: memo de `row_reference` por fila del origen compartido, un descifrado por acción, compilación reutilizada, un descifrado por imagen | Igual; N2 414 PASS | moderada | **Integrado** (`4d5ef38`) |
| 2 | Validación completa repetida 2–3 veces por operación | Una validación por operación y transacción | Igual; cota de regresión en `test_portability_source_reads.py` | ÷2–3 en finales/descargas | **Integrado** (`68ed42c`) |
| 3 | Segunda lectura completa del origen al salir | Huella `(tabla, id, xmin, ctid)` de exactamente las filas que lee `source_copy`, tomada antes de leer y comparada al salir; si difiere, comparación completa de siempre | Identidad de versión y tupla detecta incluso varios UPDATE dentro de la misma transacción; `tests/test_rights_source_fingerprint.py` traza tablas de `source_copy`, muta las 25 familias, inserción/borrado, cambio concurrente | lecturas ~2,7s → ~0,3–0,5s | **Integrado; N2 dirigida y casos pertinentes conjuntos PASS; perfil/capacidad pendientes** |
| 4 | Re-derivación de la exportación en finales/descargas | Sello por **reproducción de consultas**: tras una validación completa se guardan sus SELECT (cifrados), el SHA256 PostgreSQL de cada resultado ordenado realmente consumido, digest de los objetos del llamador, versión de reglas y `valid_until` (primer `expires_at` leído). Verificar = reproducir y comparar SHA256; si no, validación completa. Imágenes siempre se releen y hashean | Determinismo de la validación respecto a sus entradas; `tests/test_rights_validation_seal.py` (mutaciones por familia, inserción/borrado, tiempo, cambio de código, equivalencia con la validación completa) | finales/descargas ~10s → <1–2s | **Integrado; N2 dirigida y conjunta pertinente PASS, incluida corrupción S3 sin cambio SQL y acceso; perfil pendiente** |
| 5 | Generación síncrona 50–65s en la petición | Tarea Celery con estado/progreso y misma validación; la petición devuelve inmediatamente | Mismas funciones de dominio; pruebas de estado, reintento, idempotencia y concurrencia | libera workers; UX | Integrado; N2 jobs/HTTP/móvil pertinente PASS; correctiva móvil conjunta en ejecución, capacidad pendiente |
| 6 | Fernet (AES-CBC+HMAC+base64) para blobs grandes en columnas de texto | AEAD en flujo (AES-GCM o ChaCha20-Poly1305 de `cryptography`), binarios en **almacenamiento de objetos S3 compatible autoalojado** (RustFS privado en Compose), cifrado por envoltura | Mismo secreto/autenticación; pruebas de integridad, rotación de claves, purga y restauración | -33% tamaño, 2–4× cifrado, PostgreSQL más ligero | Integrado opt-in; AEAD/S3/purga reales PASS, integración capacidad pendiente |
| 7 | `json.dumps(sort_keys=True)` + HMAC-SHA256 en caliente | `orjson` (`OPT_SORT_KEYS`) para forma canónica; BLAKE3 para huellas de contenido sin clave (HMAC donde se requiera clave) | Forma canónica nueva y estable; regenerar digests sintéticos | 5–10× serialización, 3–5× hashing | Integrado; forma canónica v2, equivalencia bytes/HMAC y casos N2 PASS; ganancia depende del tipo de datos |
| 8 | Descargas servidas por Django | Revalidación de autorización y bytes; grant efímero de un uso, URL firmada y forward_auth Caddy | Autorización y conteo de descargas en Django; bytes por el proxy | descarga sin CPU Python | Integrado opt-in; S3/Caddy y revocación/purga dirigidas PASS; preflight conjunto pendiente |
| 9 | N2 en serie (~80 min) | `pytest-xdist` con base por worker, plantillas `CREATE DATABASE … TEMPLATE` para fixtures pesados; selección explícita sin testmon | Misma selección y cero skips; runner conserva evidencia por worker | 3–6× | xdist integrado: 414 PASS/0 skips; snapshots con credenciales/fallback ocupado verificados en conjunta, sin plantilla de derechos aprobados |
| 10 | Diagnósticos que releen 1.509 páginas | Plantilla privada AEAD de estado aprobado original; fresh LOGIN y validación completa antes de adoptar; aceptación sigue con lecturas reales | Solo diagnóstico, nunca aceptación | 85 → ~10 min | [Diseño y restricciones](mod08-diagnostic-baseline-design.md); implementación22PASS N2 dirigida; captura/reutilización a escala y ganancia pendientes |
| 11 | Evidencias mutables revalidadas por relectura | **Evidencia inmutable por construcción**: tablas append-only (REVOKE UPDATE/DELETE al rol de aplicación + triggers de rechazo) y cadena de hashes/Merkle por expediente; validación completa de cadena; ticket exacto reutilizable sólo con rol confiable | Más fuerte que hoy; pruebas de rechazo de mutación, restauración y purga legal (que pasa a ser tombstone auditado) | Sin reducción global O(1) acreditada | Integrado opt-in con rol runtime separado y 7 familias; N2 cadena/ACL/domain PASS; capacidad con rol real pendiente |
| 12 | Revisión independiente página a página por HTTP | Revisión por lotes auditados: varias páginas ≤50 filas por petición, cada una registrada como lectura | Mismo contrato de lectura auditada; actualizar contratos internos antes de GS01 | ÷N peticiones | Integrado; N2 dirigida20PASS y conjunta pertinente PASS, incluidos rollback final y fin de imágenes; contrato actualizado; capacidad pendiente |
| 13 | Rutas calientes Python | `mypyc`/Cython solo si el perfil lo justifica tras 3–7 | Igual | variable | Condicional |

## Orden y criterio de cierre por pieza

1. 3 → micro-medición a escala (`--delivery-profile --source-profile`, añade `source_fingerprint`) → N2 dirigida → integración.
2. 4 → pruebas de sello → micro-medición (validación completa vs sellada a escala) → N2 de exportación/cierre/descargas/retención/supresión → integración.
3. Diagnóstico completo de un caso; si predice PASS con margen ≥30–40%, ensayo objetivo de dos casos (aceptación de capacidad). Si no, continuar con 5–8.
4. 9–10 en paralelo cuando no haya mediciones vivas (nunca durante carga).
5. 11–12 con diseño escrito, actualización de contratos y N2 antes de GS01.

## Cómo retomar (para cualquier agente)

- Leer AGENTS.md, contrato16 (MOD-07/MOD-08) y seguimiento17; reconciliar Git, worktrees (`web_modelos_claude_*`) y procesos antes de actuar.
- Ejecuciones largas siempre con `scripts/run_detached.py`; si un run quedó sin terminal, `scripts/run_local_ci.py --recover` o `scripts/run_capacity_environment.py --recover RUN_ID` (escriben artefactos de recuperación separados, nunca PASS).
- No ejecutar pruebas ni compilaciones mientras mida un ensayo de capacidad.
- La propuesta GraphQL fue descartada y eliminada por decisión del usuario (2026-10-10); no se reintroduce.

## Continuación SQL — 2026-10-10 17:39UTC

Dos optimizaciones dirigidas por perfil limpio: evidencias una consulta fresca por página y metadatos scoped3consultas por llamada, con physicalSHA/firmas/guards/locks/evidencias individuales intactos. N2 conjunta140PASS/0skips303,75s, fuentes y limpieza verificadas; [registro](evidencias/mod08-sql-bulk-y-perfil-20261010.json). Reducción estructural en el lote16imágenes×4páginas:64→4 consultas de evidencias y192→12 metadatos; no porcentaje de mejora temporal acreditado. El perfil anterior interrumpido queda negativo/incompleto. Próximo medir con misma población y límites. [Propuesta CC-05](97-propuesta-indice-similitud-fotos-cc05.md) documentada por solicitud posterior del usuario para ponderación futura, fuera de estas optimizaciones y sin dependencia adoptada.


## Perfil posterior a integración SQL y correctivas de entrega

Lecturas diagnósticas en123lotes equivalentes: p95 5,087→4,251s; SQL755→515. Restauración entre controladores reales HIT, generación33,160s/1intento y cierre11,525s. Descargas diagnósticas23,539–24,374s exceden5s; las muestras reducidas no son aceptación. Correctivas SQL de cadena enforced y scope por autorización: N2 conjunta100PASS0skips248,122s; no mejora temporal nueva demostrada todavía. [Registro y límites](evidencias/mod08-perfil-entrega-y-sellos-20261010.json). Continúa la optimización hasta cumplir objetivos originales y ejecutar capacidad completa de2casos; sin relajación de fuentes, autoridad, físicos, población ni límites.


Catálogo runtime eef4368:26→9consultas frescas, N2 70PASS0skips219,061s; [registro](evidencias/mod08-catalogo-runtime-20261010.json). Nueva medición pendiente antes de cualquier afirmación de mejora temporal.


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
