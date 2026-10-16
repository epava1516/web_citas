# CR09: calentamiento desigual observado por worker

Run024716-c64da86d,SHA431ddd0,1FAIL187,54s. Diagnóstico separado con observer ingress SQL/GC; NO medición clean/aceptación. Python3.12.15/PG17.11/native-sealedca3c,4sync/controlador4CPU/PG1CPU/Redis0,2CPU y límites habituales. 1200scheduled/emitted/successful,0errores/timeouts/pending,invalid_reasons vacío,subida302. Generadorp951,900ms/max12,422ms válido.

| Métrica | Último clean020854 | Diagnóstico024716 |
|---|---:|---:|
| p95 total segundos |1,173553838|1,198622245|
| Servicio Gunicorn p95 s |0,305278|0,322136|

Instrumentación distinta: no inferir mejora/regresión causal entre columnas. No repetirFAIL ni900s.

El observador empieza post_worker_init antes de requests, no importa handlers. Registra hasta32 peticiones sinID porPID como p-N (clave compuestaPID+ID; no son IDs globales), sin modificar environ, sinURI/cookies. Sondas totales observadas9; ninguna alcanzó límite32. Estado arranque y primeros d-N:

| PID | Peticiones previas sinID | Primera dinámica | WSGI wall ms | CPU hilo ms | SQL inclusive ms |
|---|---:|---|---:|---:|---:|
|403945|1|d-1|505,780|277,162|197,946|
|403951|0|d-0|1164,937|626,562|477,529|
|403952|6|d-2|416,890|246,630|138,591|
|403966|2|d-3|659,258|212,105|408,048|

Conteos incluyen health/login/sondas; sinURI no se distingue qué ruta recibió cadaPID. Se observa inequívocamente un proceso sin ninguna petición previa observada. GC d-0wall91,706ms,solapado con CPU/SQL; no sumar. SQLwall no CPU PG. Es evidencia de calentamiento desigual y primer trabajo caro, no causalidad exclusiva de cola global ni prueba de que calentar todos cumpla0,8s.

Próximo: evaluar preparación estática porworker (rutas/reverse/plantillas) que ocurra en arranque real, sin lecturas privadas/caches de autorización ni exclusión artificial de peticiones del criterio. Contraste aislado antes de integración/carga. Si no reduce trabajo demostrado, no integrar. Preservar arranque y límites del contrato.

Hashes congelados idénticos;runner/hijo/temp/contenedores ausentes. Unidadterminal/MainPID0/ControlGroupvacío. FinalstopGunicorn/worker/beatTrue yRedisvacío. Datos artifacts/local-ci/20261016-024716-c64da86d/{load-summary-parsed.json,worker-events-raw,source-hashes.json,JUnit}. LeyendaslegacyPGcompartido preservadas; adaptadorcontainer-limits confirmaPGpropio acotado. Sin datosreales/producción/proveedores/Claude,consumo previo intacto. CR09/N3 ycontratoabiertos.
