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
