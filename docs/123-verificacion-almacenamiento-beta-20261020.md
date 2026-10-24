# Verificación conjunta del almacenamiento tras reponer dependencia fijada

Fecha:2026-10-20. Estado:199PASS auditados, sin aceptación beta.

La regresión155011 produjo52errores de preparación por Docker RustFS125 en diez archivos. La inspección posterior confirmó ausente la imagen fijada. Ya se repuso exactamente rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c y se verificaron seis unitarias del preflight, negativo real temprano y una integración S3 positiva; esa prueba no acredita todavía los52casos afectados.

## Selección y límites

Ejecutar completos estos diez archivos mediante gate focused,2workers, snapshots y broker aislado:

- tests/test_rights_validation_seal.py
- tests/test_rights_enforced_validation_seal.py
- tests/test_diagnostic_baseline_pg.py
- tests/test_rights_object_verification_parallel.py
- tests/test_rights_object_store.py
- tests/test_rights_object_read_clients.py
- tests/test_rights_orphan_objects_retention.py
- tests/test_rights_object_verify_only.py
- tests/test_object_repository_stream_read.py
- tests/test_object_repository_stream_verify.py

La colección histórica contiene174casos en esos archivos, incluidos52errores originales. Es previsión de selección, no ejecución ni PASS. Hay pruebas unitarias con dobles y pruebas de RustFS real: no presentar las primeras como verificación física. El fixture S3 real conserva --pull=never, límites propios, credenciales sintéticas, puertos privados dinámicos y retirada del contenedor; no se cambia servidor por simulador.

PostgreSQL/Redis propios y RustFS real cuando el caso lo requiere; conservar comprobación de corrupción, borrado, claves vigentes, cierre de cuerpos/clientes y autorización. El diagnóstico de restauración es un control finito de instrumento, no aceptación de capacidad o continuidad global. No se modifica producto ni pruebas de almacenamiento para este lanzamiento.

Antes de congelar, grafo dirigido y semántica de este registro. Registrar huellas de fuentes; auditar terminal, todos los52nodeids originalmente bloqueados, selección completa y ausencia de SKIP, recursos/PID/temporal y recibos Telegram. Una dependencia disponible no constituye por sí sola un PASS funcional. Si aparece un fallo nuevo, conservarlo y corregir su causa.

## Continuación

No hay dos bloques de integración simultáneos: el gate de rutas públicas185925 ya terminó y fue auditado antes de lanzar éste. Durante la ejecución sólo análisis readonly; no editar fuentes usadas. Las revisiones nativas posteriores de121/122 no escriben ni ejecutan pruebas, y sus propuestas se comprobarán por Codex antes de aplicar.

Después cerrar correctivas restantes demostradas y probar el común pertinente sobre candidata única. Comparar2vs4workers sólo con selección/fuentes idénticas y ejecución secuencial; no extrapolar tiempos con otra carga propia ni cambiar topología/recursos de los ensayos de producto. Regresión amplia y capacidad continúan pendientes. Corto TCP20RPS FAIL y900s bloqueado; B00residual y B07–B17 siguen abiertos. Sin publicación, contratación, pagos ni datos reales.

## Alcance añadido antes del lanzamiento

Las dos revisiones readonly posteriores detectaron garantías de prueba debilitadas, no defectos de producto demostrados. Se incorporan los refuerzos mínimos de121/122 al mismo bloque secuencial antes de lanzar: publication_match_dependency_edges completo15casos y publication_prepared_binding completo9casos. Se añade explícitamente beta_prepared_binding_mutation_diagnostic.py con un caso del detector de degradación dirty. Selección final prevista:199casos en13archivos,174de almacenamiento+24reforzados+1diagnóstico manual. La cifra es previsión, no PASS. No se solapan bloques de integración ni se alteran aplicaciones o recursos del benchmark.


## Terminal auditado

191359-733f2147:199PASS/0FAIL/0ERROR/0SKIP en291,67s. Auditoría beta-storage-terminal-audit-20261020.json verifica13archivos completos:174almacenamiento+24reforzados+1diagnóstico manual,622fuentes de producto idénticas a183847, congelación/comparación fresca, recursos/temporales/procesos retirados y recibo1792523961944608531-2375638 sent. Auditoría notificada con recibo1792523978724814147-2417932 sent.

Los52nodeids originalmente bloqueados por RustFS125 están presentes y pasan. Imagen fijada comprobada por ID local, sin contenedores object-tests remanentes. Esto no convierte las unitarias con dobles en S3 físico. Los quince casos de migración y nueve de prepared_binding reforzados pasan, con drenaje final y seis informes fase/idioma de preparación física; baseline/revocado usan cursores preparados y se materializan los descartados. El diagnóstico manual demuestra detección de degradación conjunta flag/cursor sólo tras revocación, conservando calentamiento. No se modifica producto ni se acepta el mutante como funcional.

Los terminales48de121/122 conservan sus cortes; sus dos archivos modificados se revalidan aquí íntegros. Pendiente común pertinente de40archivos y comparación secuencial2vs4workers, después regresión amplia cuando proceda. Negativo155011 conservado; no beta global ni capacidad.
