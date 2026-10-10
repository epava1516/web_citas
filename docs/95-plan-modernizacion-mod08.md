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
| 3 | Segunda lectura completa del origen al salir | Huella `(tabla, id, xmin, ctid)` de exactamente las filas que lee `source_copy`, tomada antes de leer y comparada al salir; si difiere, comparación completa de siempre | Identidad de versión y tupla detecta incluso varios UPDATE dentro de la misma transacción; `tests/test_rights_source_fingerprint.py` traza tablas de `source_copy`, muta las 25 familias, inserción/borrado, cambio concurrente | lecturas ~2,7s → ~0,3–0,5s | **N2 dirigida24PASS241,787s; pendiente integración conjunta/perfil** |
| 4 | Re-derivación de la exportación en finales/descargas | Sello por **reproducción de consultas**: tras una validación completa se guardan sus SELECT (cifrados), el SHA256 PostgreSQL de cada resultado ordenado realmente consumido, digest de los objetos del llamador, versión de reglas y `valid_until` (primer `expires_at` leído). Verificar = reproducir y comparar SHA256; si no, validación completa. Imágenes siempre se releen y hashean | Determinismo de la validación respecto a sus entradas; `tests/test_rights_validation_seal.py` (mutaciones por familia, inserción/borrado, tiempo, cambio de código, equivalencia con la validación completa) | finales/descargas ~10s → <1–2s | **N2 dirigida24PASS; queries/caller/expiry/config/adversariales cubiertos; integración/perfil pendientes** |
| 5 | Generación síncrona 50–65s en la petición | Tarea Celery con estado/progreso y misma validación; la petición devuelve inmediatamente | Mismas funciones de dominio; pruebas de estado, reintento, idempotencia y concurrencia | libera workers; UX | Pendiente |
| 6 | Fernet (AES-CBC+HMAC+base64) para blobs grandes en columnas de texto | AEAD en flujo (AES-GCM o ChaCha20-Poly1305 de `cryptography`), binarios en **almacenamiento de objetos S3 compatible autoalojado** (p. ej. MinIO en Compose), cifrado por envoltura | Mismo secreto/autenticación; pruebas de integridad, rotación de claves, purga y restauración | -33% tamaño, 2–4× cifrado, PostgreSQL más ligero | Pendiente |
| 7 | `json.dumps(sort_keys=True)` + HMAC-SHA256 en caliente | `orjson` (`OPT_SORT_KEYS`) para forma canónica; BLAKE3 para huellas de contenido sin clave (HMAC donde se requiera clave) | Forma canónica nueva y estable; regenerar digests sintéticos | 5–10× serialización, 3–5× hashing | Pendiente |
| 8 | Descargas servidas por Django | Verificación al escribir + objeto inmutable servido por Caddy (`X-Accel-Redirect`/URL firmada corta) | Autorización y conteo de descargas en Django; bytes por el proxy | descarga sin CPU Python | Pendiente (tras 6) |
| 9 | N2 en serie (~80 min) | `pytest-xdist` con base por worker, plantillas `CREATE DATABASE … TEMPLATE` para fixtures pesados, `pytest-testmon` para selección por impacto | Misma selección y cero skips; runner conserva evidencia por worker | 3–6× | Pendiente |
| 10 | Diagnósticos que releen 1.509 páginas | Plantilla de base con estado aprobado validado para diagnósticos; aceptación sigue con lecturas reales | Solo diagnóstico, nunca aceptación | 85 → ~10 min | Pendiente |
| 11 | Evidencias mutables revalidadas por relectura | **Evidencia inmutable por construcción**: tablas append-only (REVOKE UPDATE/DELETE al rol de aplicación + triggers de rechazo) y cadena de hashes/Merkle por expediente; validar = comprobar la cabeza | Más fuerte que hoy; pruebas de rechazo de mutación, restauración y purga legal (que pasa a ser tombstone auditado) | O(1)/O(log n) por operación | Pendiente (diseño propio antes de implementar) |
| 12 | Revisión independiente página a página por HTTP | Revisión por lotes auditados: varias páginas ≤50 filas por petición, cada una registrada como lectura | Mismo contrato de lectura auditada; actualizar contratos internos antes de GS01 | ÷N peticiones | N2 dirigida20PASS157,921s; contrato interno actualizado; integración/capacidad pendientes |
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
