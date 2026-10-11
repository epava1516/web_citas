# MOD-08: relevo y pausa solicitada por el usuario (2026-10-11)

Estado: PAUSADO por petición expresa del usuario: documentar lo realizado, commit, push y parar para cambiar el enfoque. No aceptación técnica completa. No pruebas, mediciones ni agentes escritores deben continuar automáticamente después de este relevo.

## Estado conservado

La rama de integración incorpora los cambios de Claude y Codex documentados en [plan MOD-08](../95-plan-modernizacion-mod08.md), [seguimiento](../17-seguimiento-desarrollo.md), [contrato](../16-contrato-ejecucion-desarrollo.md) y [.ai coordinación](../../.ai/tasks/mod08-coordinacion.md). PostgreSQL real, almacenamiento RustFS real y cuotas obligatorias permanecen; no publicación ni proveedores contratados ni datos reales.

Cambios conservados: generación asíncrona y límites, almacenamiento binario/AEAD y entrega, sellos por reproducción de consultas, pruebas paralelas/fixtures, lectura por lotes auditados, memo pura y acotada de contenido tras lectura física e igualdad completa, streaming/canonicalización nativa Cython y correcciones revisadas, diagnóstico TCP/WSGI/fases, pipeline de siete consultas fuente, HMAC adaptativo con igualdad completa y promoción de buckets. Los documentos previos contienen la evidencia particular; esta pausa no convierte propuestas ni pruebas pequeñas en aceptación global.

Cython ya está aplicado al núcleo canónico: binario sellado SHA256 996bc13d6f93773610470fa444beaabaaf15be80de777ede5a9fa5a307636d3c. No se añadió mypyc ni una compilación general adicional. Ampliar compilación necesita perfil que demuestre margen suficiente; CPU del hilo incluye código nativo.

## Último ciclo medido del código conservado

Captura 20261011-064425-ed839a88 / uso 20261011-071449-f8adec38, fuentes e7846d7. Ambos terminales con una prueba aprobada, cero fallos/errores/omisiones. 1156 hashes y limpieza de recursos propios verificados independientemente por ejecución. [Evidencia completa y fases](mod08-medicion-index-pipeline-20261011.md), [JSON](mod08-medicion-index-pipeline-20261011.json), [memoria](mod08-index-pipeline-memory-20261011.md).

| Operación | Antes (s) | Después (s) | Reducción | Muestras | Objetivo (s) |
|---|---:|---:|---:|---:|---:|
| Navegación, lote TCP completo p95 | 3.934962 | 3.753392 | 4.61% | 383 | 2 |
| Descarga JSON | 7.812455 | 6.930455 | 11.29% | 3 | 5 |
| Descarga binaria | 7.710310 | 7.317947 | 5.09% | 8 | 5 |
| Generación | 43.903684 | 42.731399 | 2.67% | 1 | 120 |
| Preparación final | 15.234616 | 15.433019 | -1.30% | 1 | 30 |
| Inspección final | 4.196300 | 3.160195 | 24.69% | 1 | 30 |
| Aprobación final | 3.952883 | 4.049159 | -2.44% | 1 | 5 |
| Cierre | 15.531436 | 16.237231 | -4.54% | 1 | 30 |

Un caso sintético completo; no dos casos/N3. JSONn3/binario n8 usan nearest-rank p95 igual al máximo, insuficientes para aceptación. Métricas n1 no son p95. Dos ejecuciones no aíslan causalidad ni cada optimización. El wrapper SQL no incluye espera de pipeline.sync: no interpretar su descenso aparente como reducción equivalente del tiempo SQL. Los relojes TCP/WSGI completos sí incluyen la espera.

Falta reducir aproximadamente 1.753s en navegación,1.930s JSON y2.318s binario respecto de ese ciclo. Son diferencias aritméticas respecto del objetivo, no predicción de ahorro obtenible. Tras revertir cuatro lectores se restauraron exactamente los cinco archivos anteriores; no se repitió una medición posterior del runtime restaurado.

## Verificaciones y experimentos recientes

- Pipeline siete consultas: 79PASS PG real, concurrencia/locks/snapshots, fallbacks, errores y rollback. Mantiene controles de head/trust/eventos. Micro siete filas703bytes mediana7.204861→5.977018ms; no extrapolar a request. [Evidencia](mod08-chain-source-pipeline-gate-20261011.md).
- HMAC adaptativo:31PASS PG real,44 escenarios micro. Igualdad completa de valor/secret fresco, tipos/scopes/caps128entradas/32MiB; promoción a dict tras colisión evita regresiones severas del bucket lineal. Microfresh1MiB~40–42% CPU por ocho llamadas, no request. [Evidencia](mod08-fingerprint-index-adaptive-20261011.md). Se conservan primeros negativos [probe](mod08-fingerprint-index-probe-20261011.md) y [saturación](mod08-fingerprint-index-collisions-20261011.md).
- Integración pipeline/HMAC:38PASS PG real con runtime enforced, cuatro auditorías físicas, corrupción tardía/rollback y sellos replay/tamper.1156hashes y limpieza independientes. [Gate](mod08-index-pipeline-combined-gate-20261011.md).
- Helper SQL runtime:8PASS experimento PG17, pero diseño rechazado por sustitución entre atestación y ejecución que produce trusted falsificado. No integrado. [Evidencia negativa](mod08-runtime-sql-probe-20261011.md).
- Cuatro lectores físicos:99PASS PG/RustFS funcionales, lecturas/EOF/contexto/tombstones/crypto fresco, orden/drenaje/cierre conservados. Medición empeoró descargas y se revirtió498afa6 mediante94e0219. Rama aislada codex/mod08-object-four-readers conserva candidata21424e1. [Evidencia](mod08-medicion-four-readers-20261011.md).

| Métrica | Dos lectores (s) | Cuatro lectores (s) | Variación |
|---|---:|---:|---:|
| Navegación p95 | 3.753392 | 3.726545 | -0.72% |
| JSONn3 | 6.930455 | 7.741606 | +11.70% |
| Binarion8 | 7.317947 | 8.645426 | +18.14% |

El pequeño cambio de navegación no es atribuible a lectores de exportación. Muestras de descarga pequeñas; insuficiente para aceptar mayor concurrencia. Memoria cota global uso2.714→2.808GiB, sin swap/OOM; no RSS aplicación ni pico simultáneo.

## Diagnóstico CPU y captura interrumpida

Conservado af25346: lee cpu.stat en el mismo exec final de memoria, después de los requests cronometrados; no cambia cuotas ni código productivo.43 pruebas locales de contrato pasan. Preflight20261011-080958-6460fb0b real READY_NOT_CAPACITY/1PASS,1156hashes y limpieza independientes; cinco servicios con contadores válidos, cero errores. [Evidencia](mod08-cpu-counter-preflight-20261011.md). Counters acumulados desde arranque no son p95 ni tiempo por request, y el throttling de preflight no demuestra causalidad en las descargas.

La nueva captura con carga 20261011-081514-6f6a29ab fue INTERRUMPIDA por petición del usuario, launcher1802250 terminado con SIGINT. Verificados independientemente seis contenedores, red y volumen ausentes. No resultado terminal de capacidad ni nueva latencia válida; nunca reutilizar sus artefactos como baseline válido. Registro local artifacts/capacity-environment/20261011-081514-6f6a29ab/user-stop.json y plan artifacts/mod08-cpu-counters-performance-plan.json marcado STOPPED_BY_USER. No iniciar su etapa use.

## Revisión de memo de hashes de filas

Revisión nativa read-only canonical_tests: propuesta tableoid/PK/xmin/ctid + versiónpg_proc del wrapper insuficiente para demostrar equivalencia; dependencias transitivas, identidad real de función ejecutada, tipos/esquema y configuración necesitan cobertura. Se mantiene hash completo actual. Contraejemplo sugerido de sustitución de jsonb_set requiere privilegio administrativo sobre pg_catalog; NO EJECUTADO. No se demostró que cambiar GUCs altere el hash de los siete esquemas actuales. No presentar hipótesis como fallo probado ni implementar cache bajo esas garantías incompletas. Estado local artifacts/mod08-row-memo-feasibility-plan.json. No benchmark ni mejora atribuida.

## Aceptación original pendiente y reanudación

Preservar [objetivos originales](objetivos-capacidad-local-20261009.json): dos casos completos simultáneos de1500revisiones/JSON16MiB/originales64MiB ±1%,4CPU/8GiB/20GiB/swap0,pico agregado≤6GiB incluyendo cache y RSSapp≤1GiB; selección/cobertura≤60s; lotes de hasta cuatro páginas≤50filas p95≤2s sin dividir por cuatro; guardar/aprobar p95≤5s; enqueue→generación durable≤120s incluyendo cola/reintentos; respuesta/cierre≤30s; paquetes≤8MiB y dos autorizacionesHTTP frescas+EOF p95≤5s con≥20muestras por variante y caso. Primera apertura aparte. N3/ciclo completo/CR09/integral pendientes. Ninguna prueba dirigida ni simulador sustituye aceptación.

No hay trabajos de medición activos tras esta pausa. Agentes nativos escritores terminados; ramas/worktrees preservados. No nuevas invocaciones Claude/ultrareview: una ultrareview consumida y dos reservadas. Historial de consumo anterior se conserva en [.ai/tasks/desarrollo.md](../../.ai/tasks/desarrollo.md). [FAISS/CC-05](../97-propuesta-indice-similitud-fotos-cc05.md) está documentado como futura investigación de duplicados, no optimización del listado ni resultado medido.

Los artefactos voluminosos/logs, binario Cython compilado, baselines cifrados y claves locales permanecen fuera de Git; no subir secretos ni archivos de datos. Los untracked preexistentes .ai/tasks/mod08-async-generation-claude-preserved-20261010.md, .ai/tasks/mod08-storage-crypto.md, .ai/tasks/mod08-test-speed.md y .claude/ se preservan sin añadirse. Para reproducir, revisar los comandos en evidencia local y reconstruir/verificar los binarios sellados; este relevo no promete que un checkout remoto incluya artefactos ignorados.

Retomar solo con nueva instrucción del usuario y nuevo enfoque. Leer contrato/seguimiento/este relevo, auditar Git y fuentes reales, mantener evidencia negativa y criterios originales. No repetir captura interrumpida automáticamente ni marcar el objetivo logrado.
