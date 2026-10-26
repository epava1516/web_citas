# N10B — prerregistro de referencias operativas actuales

Estado: preparado, sin ejecución ni aceptación. Base `ae33175`, N10A aceptado localmente en [477](477-n10-a-groupadmin-autoridad-verificada-20261026.md); N10 abierto, 9/13 bloques obligatorios aceptados. Alpha/noindex.

## Preguntas y selección anterior a la medición

El testigo histórico de arranque Gunicorn verifica cuatro workers reales, pero no registra spawn→ready y fue omitido por su guarda explícita en la batería global posterior. El contraste GC mide inicialización WSGI/Client, no arranque Gunicorn. Las fuentes y plantillas actuales requieren una referencia actual, sin reconstruir imágenes ni repetir carga.

El collector tiene 18 observaciones válidas con 0/10/100 pendientes; se reutilizan. Su coste no incluye necesariamente el comando ni su JSON positivo. Los cuatro perfiles reales de restauración y la conciliación de 46 comandos permanecen válidos con sus límites; este lote no los repite.

Instrumento nuevo: `tests/test_owned_operational_reference.py`, dos casos explícitos y seriales. Revisión de fuente y hashes en `artifacts/recorridos-n10-20261026/n10b/instrument-review.json`; no equivale a ejecución. No cambia la aplicación.

| Caso | Medida | Oráculos y límites |
| --- | --- | --- |
| `test_current_four_worker_startup` | Una observación de spawn hasta cuatro logs ready y seis peticiones TCP secuenciales a health, primera separada de cinco posteriores | Cuatro workers sync reales, configuración raíz vigente y preparación estática ES/EN; health 200 y cuerpo exacto, PostgreSQL propio. Sondeo de readiness cada 50 ms incluido. Sin afinidad por worker ni conteo SQL del proceso hijo. |
| `test_positive_snapshot_cli_reference` | Seis invocaciones en proceso mediante call_command, primera separada de cinco calientes; tiempo total dispatch/collector/JSON, SQL y bytes de salida | JSON válido de una línea, esquema 1, alcance durable explícito, publicación vacía y resultados estables salvo sampled_at; autocommit restituido. No mide arranque de Python ni escala de backlog. |

Datos: tablas de trabajo sin pendientes ni actores creados para este lote; las filas inicializadas por migraciones quedan protegidas por el oráculo. Antes/después se compara el estado completo de todos los modelos, incluidas tablas intermedias, y hash/metadatos de archivos de MEDIA_ROOT propio. No se excluyen modelos enteros. La muestra de arranque usa las credenciales del migrador del runner desechable, sin acreditar separación de rol runtime.

## Protocolo y criterios

Runner oficial focused, un worker de pytest, PostgreSQL17 y Redis7.4 propios, parser nativo ya disponible, timeout de lote 600 s. No crear imagen, tocar servicios existentes ni conectar PostgreSQL MCP. Confirmar propiedad real de contenedor, puerto, usuario y base antes del ensayo. Lanzar Gunicorn sólo en loopback con puerto efímero; HTTP sin proxy y timeout 5 s. Cota de readiness 45 s, cierre TERM 15 s y fallback KILL 5 s; todos los hijos observados deben desaparecer y el master salir 0.

Antes de ejecutar: refresco focal del grafo para el instrumento y este prerregistro; congelar fuentes completas, configuración/dependencias/instrumento/documentos y IDs de imágenes cacheadas. Registrar plataforma/recursos efectivos del runner y observar IDs de sus contenedores vinculados al PID/start_ticks exactos. El corte previo consultado tiene 2131 fuentes y SHA `171b73cb1425c7dbb9a529c98e1de5c6d8dfb2f856e767ac061d2449a9f9fd82`; semántica selectiva, no reconstrucción final N15. La consulta de vocabulario startup/worker/snapshot/health/gunicorn se conserva en source-graph-cut.json.

Exigir dos PASS, cero fallos/errores/omisiones, todas las muestras finitas y positivas, efectos nulos, fuentes estables, limpieza de recursos propios y recibo Telegram terminal. Auditar propiedades del JUnit original y resultado del runner; una propuesta o revisión no sustituye ejecución. Separar tiempo QA de tiempo de máquina. No hay presupuesto universal nuevo, p95/p99, porcentaje de mejora o candidato de rendimiento: se registra referencia actual y tabla antes/después con ausencia de medida comparable explícita.

N10 no se cierra con estos dos casos: quedan las 77 disposiciones y obligaciones compartidas verificadas. N11 y N15 siguen pendientes; N02 residual diferido al final del desarrollo, N12–N14 condicionados. No cambia alcance ni alpha/noindex.
