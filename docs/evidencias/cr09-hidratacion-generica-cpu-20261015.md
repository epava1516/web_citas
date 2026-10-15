# Hidratación genérica: experimento y hallazgo de caché

Primer intento195513-37b84a9e interrumpido antespytest porerror enpreparación delinstrumento. [Incidente preservado](cr09-hidratacion-generica-intento-interrumpido-20261015.json), limpieza independiente; no PASS. Corregidoinstrumento yvalidado sintaxis/ruff antesnuevointento.

Run correcto `20261015-195606-7ccd05d2`, base8f91553+instrumento: **1PASS122.24s**. [180observaciones](cr09-hidratacion-generica-cpu-terminal-20261015.json), fuentes/limpieza independientes. Tresbloques alternos,30requests6casosESENporconexiónnueva,proyección10k actual, sinwarmup/omisiones. Ambosbrazosthreshold0; candidatocambia sóloplan_cache_mode duranteread_publication_values bounded+prepared yrestauraauto, comprobado despuésde cadarequest. ParidadHTML/targetfirmado exacta. Incluye costeextra deatomic/savepoint/SHOW/SET/restauración, no producto modificado.

| CPU PGmedia porrequest |Actualauto|Genéricohidratación|
|---|---:|---:|
|Primeras6porconexión|66.667ms|55.556ms|
|Peticiones7–18|41.667ms|36.111ms|
|Peticiones19–30|34.167ms|32.500ms|
|Todas30|43.667ms|38.556ms|

| Bloque,CPU PGmedia |Actualauto|Genéricohidratación|
|---|---:|---:|
|0|46.333ms|36.667ms|
|1|46.667ms|38.000ms|
|2|38.000ms|41.000ms|

Bloque2empeora, rangossesolapan, cuantización100Hz/procesoPythonprecalentadodesigual: noahorro causal/reproducible ni p95. Planesfinales82actualfrente100candidato; actuales490generic/200custom,candidato620/145. Elwrapperañademásatomic/savepoint/restore; aúnno distingue beneficiogenéricodelcostecachéextra. No aplicarplan genérico globalni inferircumplimiento.

## Defecto reproducido durante revisión

Crecimiento de planes motivóuncontrolrealPGseparado, sin carga:12atomic anidadosdentrodelhelper actualpreparaban12SAVEPOINT+12RELEASEcon nombresúnicos y sólo1SELECTreutilizable. [Rojo195937-fcdecd99](cr09-preparacion-utility-reproduccion-20261015.json):1FAIL37.41s,fuentes/limpieza. No es fuga deresultadosniinvalidez semántica; síocupaciónevitable de caché100 ypreparaciónsinreutilización. Elwrapperdelexperimentoagravaese mecanismo, porloquenocompara aúnexclusivamentepolíticadeplanes.

Decisión: posponerforzadogenéricoycorregirprimeroeldefectodemostradodelcursor, preparando únicamenteSELECTtextuales, manteniendo ejecuciónsinpreparación parautility/SQLobjectsdesconocidos. Noafectabinding/params/65535fallback; noumbral/GUC/carga/cuotasnuevos. Controles+CPUintegrada pendientes antesdeotroclean. Últimop95limpio.897765506FAIL,CR09/N3abiertos.
