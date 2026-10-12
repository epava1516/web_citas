# MOD08 — Lote grande único: diagnóstico adaptado y ejecutado

Autorización2026-10-11: adaptar y ejecutar si procede. [Métricas completas finales](mod08-unseal-lote-grande-20261011.json), [primera medición](mod08-unseal-lote-grande-inicial-20261011.json). No optimización productiva aplicada.

## Adaptación y escenario

No se halló baseline/clave en búsqueda acotada artifacts/tmp/cache. No se usó test_owned_target_stage_profiles ni resume/finish ni fallback a preparación completa. Nuevo arnés tests/test_capacity_unseal_large_batch.py crea con populate las1500revisiones calibradas,16MiB seleccionados(16777586bytes) y64MiB±1% de originalesWebP reales(67095030bytes), sobre PostgreSQL17/Redis7.4 propios. Preparación mediante servicios nativos: prueba de alcance simulada identificada, evaluación aprobada, selección completa de tres campos por revisión,31lecturas paginadas reales y aprobación independiente; cobertura parcial vigente. No IDs/approvals inventados. Los binarios están retenidos pero no seleccionados ni revisados como entregas: esta es una diferencia explícita respecto del fixture completo.

Una petición POST real TCP→Gunicorn2sync→WSGI→Django→inspect_batch de4páginas, sesión y CSRF reales, LOGINruntime restringido/no propietario con enforcement, respuesta hastaEOF y cuatro CoverageRead persistidos. AperturaGET fuera de la muestra. No generación, cierre, descargas, Caddy ni RustFS; sin cuotascontractuales, no aceptación de capacidad. Cython3.0.12 reconstruido explícitamente con fuente actual y validado; binario4a178c247bccc9eae6883d298bd1546d613d0608538c48b959d84cc51bd94c8e, distinto del histórico. Python3.12.15/Django5.2.17/cryptography50.0.2.

Tests/capacity_unseal_wsgi.py combina el instrumento unseal y19fases en EL MISMO HTTP; sin cProfile. Conserva llamadas físicas/crypto/autoridad/auditoría, salida/close/error. El lookup/copyprobe del instrumento añade coste, incluido enunseal yWSGI. Resolver inventarioURLnormal de Django antes de instalar aliases garantiza observación también en worker frío, sin ejecutar lecturas/validaciones de dominio; import queda incluido en totalWSGI/TCP. Falta explícita content_digest en inventario inicial (sin llamadas observadas); no atribuir fase ausente como medición de cero coste.

## Resultado final y decisión JSON

20261011-113602-59a09648:5PASS/0fallos/errores/skips116,956sJUnit (una integraciónTCP, cuatro pruebas unitariasEOF/error). 1161huellas verificadas independientemente, ninguna diferencia; doscontenedores y procesosGunicorn deldiagnóstico ausentes comprobados independientemente. El contexto runtime exige ausencia de conexiones de hijos antes de retirar rol/credenciales.

193unseal,6grupos,226836bytes de plaintext único retenido. El descriptor de selección es223141bytes, leído/descifrado16veces; NO se descifra el JSON de16MiB en cada unseal. Los16MiB son la proyección de datos fuente.

| Etapa | CPU ms | Wall ms |
|---|---:|---:|
| Descifrado fresco total (incluye cipher y encode del token) | 48.052 | 48.043 |
| Decode total | 0.826 | 0.814 |
| Parseo JSON total | 33.402 | 33.358 |
| Parseo repetido (subconjunto del total) | 31.466 | 31.423 |
| Lookup/igualdad de bytes (overhead diagnóstico) | 1.835 | 1.822 |
| Deepcopy de prueba (overhead diagnóstico) | 195.651 | 197.028 |

No implementar memoJSON con copia: la copia observada es más costosa que el parseo evitado. Tampoco justificar diccionarios compartidos sin equivalencia de mutabilidad. La cota ideal de parseo repetido es~31msCPU en este lote, sin descontar lookup/copia; no ahorroHTTP garantizado. Primera versión midió~40msCPUparseo repetido y~221msCPUcopias; no comparar como mejora porque no hubo cambio productivo ni ensayo controlado.

TCPinstrumentado2,241219s;WSGI2,241113s/CPUhilo1,473748s. NO p95 ni ensayo limpio ni comparación con3,753392s histórico. No restar overhead para inventar un tiempo limpio o aceptar2s. Las etapas del instrumento ya están incluidas en unseal: no sumarlas a las fases otra vez.

## Fases exclusivas del mismo HTTP

| Fase | Llamadas | Wall exclusivo ms | CPU hilo exclusivo ms | SQL atribuido |
|---|---:|---:|---:|---:|
| source | 1 | 426.172 | 252.662 | 20 |
| authorize | 23 | 279.365 | 158.577 | 93 |
| record | 4 | 241.068 | 128.294 | 80 |
| page | 4 | 231.845 | 126.801 | 84 |
| validate_assessment | 4 | 132.315 | 48.350 | 88 |
| canonical_bytes | 1705 | 142.523 | 142.411 | 0 |
| batch_projection | 4 | 57.549 | 56.751 | 0 |
| compile | 1 | 64.929 | 64.233 | 0 |
| fingerprint | 363 | 47.642 | 47.307 | 0 |

Unsealexclusivo288,120mswall/286,589msCPU incluye195,651msCPUdecopyprobe; no interpretarlo como crypto puro. SQL423sentencias, relojwrapper excluye fetch/adaptación completa y pipeline.sync; susduraciones están dentro de fases y se solapan. Wall−CPU incluye esperas/desplanificación/trabajo externo, no identifica red. No se ha instrumentado aún fetch o pipeline.sync como etapas propias.

## Límites, negativo y siguiente frente

Este es un lote inicial tras31lecturas de selección; NO acumula cientos de CoverageRead/SelectionRead de navegación anteriores como el requestp95 histórico. Por eso validate_assessment aquí~132mswall exclusivo no reproduce los~1064ms anteriores: la cadena es distinta. Para explicar el bloqueo original hay que observar crecimiento y desglose de validación física de cadena en un historial comparable, sin fabricar auditorías ni reutilizar autoridad; source_copy/materialización también tiene coste medible (~426mswall/253msCPU) por desglosar. No deducir un ahorro seguro ni consolidarSQL a partir de estas cifras.

Negativo20261011-113250-ddd24db2:4PASS/1FAIL, POST/auditorías correctos pero batchcalls0 por inventario de worker frío; sin resultadofásico aceptado. Corregido antes de gatefinal. Inicial20261011-112800-6d076bff1PASS conserva primera medición; no sumar tests de versiones distintas como gate. Cuatro unitariasHOST0,20s verificaron close/error, no integración real.

Diagnóstico acotado terminado. Sin caché/producto/commits/push/publicación/proveedores/datos reales, ni capacidad completa. MOD08 original sigue pendiente y pausado fuera de esta autorización.
