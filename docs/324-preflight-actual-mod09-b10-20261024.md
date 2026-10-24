# B10-361 — Comprobación previa actual de MOD-09

Ejecución 20261024-204645-750ad975: READY_NOT_CAPACITY, launcher exitoso, 1 PASS/0 FAIL/0 ERROR/0 SKIP. JUnit 75,206 segundos, caso 74,613 segundos; estos tiempos no incluyen toda la preparación del controlador. [Auditoría y huellas](evidencias/b10-current-mod09-preflight-20261024.json).

Se ejecutó el controlador oficial con --preflight-only --object-delivery --cpu-budget 8 y la imagen local inmutable sha256:f50e2f01874ebbd1147261160c6058c64bf2e8d26d50b2446c7549d2692b947b. No se cambió ninguna etiqueta latest ni se construyó o desplegó una aplicación. El controlador y la aplicación usan las fuentes del worktree y el intérprete actual montados en solo lectura; la imagen es soporte de ejecución, no acreditación de identidad con la imagen histórica.

Se verificaron PostgreSQL, Redis, RustFS y Caddy reales con cuotas kernel propias, almacenamiento cifrado y purga S3, entrega completa por proxy y rechazo de replay. Un trabajo real de Celery generó una copia pequeña de imagen de 4300958 bytes, con cuerpo/hash comprobados; Beat y worker completaron la purga. El diagnóstico observó un trabajo succeeded en un intento, no una promesa de tiempo de generación extrema.

Fuentes sin cambios, archivo sin problemas y controlador exited0/noOOM. El inventario independiente por etiqueta confirma ausencia de contenedores, redes y volúmenes propios; Telegram terminal sent. Cota conservadora de memoria propia 1359679488 bytes, dentro del umbral de este control finito. No demuestra memoria ni duración del escenario completo.

## Medición pendiente para resolver B10

La comparación de [fuentes323](323-contraste-fuentes-mod09-b10-20261024.md) justifica una medida actual porque contenido, seguridad y dependencias cambiaron respecto a MOD-09; no se repite el corte histórico para alterar su FAIL. El escenario pertinente sigue siendo dos sujetos independientes, 1500 revisiones, 16MiB JSON y 64MiB de originales por caso, con entrega real y concurrencia. Deben conservarse los presupuestos y las comprobaciones de cuerpos, autoridad, revocación, recursos y limpieza.

La selección oficial es test_owned_complete_target_delivery, mediante run_capacity_environment con --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --object-delivery --cpu-budget 8 --delivery-complete y la imagen inmutable validada. Es el mismo modo funcional del instrumento histórico, no un perfil cProfile ni un control pequeño que lo sustituya. Antes del lanzamiento se debe fijar el corte actual, registrar fuentes, entorno y diferencias de versión, y preparar ejecución persistente, Telegram y relevo para la espera.

Se reportarán por separado cobertura p95, JSON/binario por paquete, generación, preparación y cierre; no se sumarán percentiles ni se presentarán siete segundos como duración total. Una ejecución por versión permite describir diferencias observadas con límites, no atribución causal exclusiva o reproducibilidad. Los objetivos originales 2s/5s y la aceptación provisional MOD-09 permanecen.

Esta carga completa **no se ha iniciado** en B10-361. También queda pendiente justificar el extremo de similitud y emitir la disposición final de B10 dentro del contrato actual. No hay nueva aceptación B10/B16 ni autorización de apertura.
