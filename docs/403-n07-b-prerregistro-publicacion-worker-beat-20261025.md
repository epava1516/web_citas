# N07B — prerregistro de publicación con worker y Beat nativos

25 de octubre de2026. Alfa, base4ebc067. N07A/402 acepta una corrección local de reordenación; **N07 sigue abierto,6/13bloques obligatorios**. Contratos340/354 y roadmap341 vigentes. No hay candidato de optimización: se mide el trabajo diferido que no acredita una llamada directa, sin repetir el procesamiento fotográfico aceptado N03/393.

## Corte, alcance y preparación

Antes de estudiar el lote se verificó el corte final N07A:2013fuentes sin diferencias,19157nodos/82488relaciones/918comunidades; SHA2666164a7a6c21e4a15d93f4d576e43c3f91cfe616078721b6075a05c94fe7f5. Refresco focal AST/semántica nativa sobre base preservada, no reconstrucción exhaustiva.39IDs de N07 conservados; este lote representa señales/refresh/sweep/expiry y su frontera pública, no todos los recorridos de revisión/apelación, purga o retención compartida.

Un escritor nativo preparó356líneas en worktree aislado, base4bd9a59 y propiedad exclusiva del instrumento/reporte. Codex leyó todo el código y helpers y comprobó la diferencia hasta4ebc067: sólo la corrección reorder aceptada. Al integrar añadió27líneas para comprobar READ_REPAIRdesactivado y todas las páginas públicas ES/EN, sin modificar producto ni los oráculos existentes. La revisión y el reporte son propuestas, no PASS.

Instrumento tests/test_publication_worker_cadence_reference.py, un caso explícito serial. PostgreSQL/Redis locales propios con labels/puertos/generación comprobados; librdb nativa sellada; almacenamiento local sintético. Fixture directory y populate(100) generan100publicados, imágenes compartidas y otros estados originales; esa preparación eager y refresh_all directo ocurren antes de medir. Se declara el entorno exacto, SHA de fuentes/fixtures/dependencias/instrumento y manifiesto nativo. Datos y colas externas excluidos.

## Fases y oráculos previstos

| Fase | Acción real y medida | Oráculo / límite |
| --- | --- | --- |
| A: worker ausente | POST lifecycle pause del titular, señal real tras commit y marca pendiente; iniciar después prefork2restringido | Antes del worker: ficha/foto/favorito denegados y favorito guardado sin enlace; las cinco páginas ES/EN contienen99perfiles únicos y excluyen al pausado. Marca aún pendiente. Medir publicación→inicio/ejecución/observación de vaciado, incluyendo retraso deliberado y arranque |
| B: worker vivo, Beat aún ausente | QuerySet.update pausa otro perfil; rawSQL pausa otro y caduca uno más, sin señales de modelo. Iniciar Beat real después | Antes de Beat: tres marcas conservadas, cero nuevos publishes del harness, denegaciones y cuatro páginas ES/EN con96perfiles únicos. Beat copia sólo las entradas nativas refresh30s/expiry60s, sin acelerarlas. Una sola acción expire, actor sistema y versión/revisión correctas |
| C: sweep manual | Corromper una elegibilidad almacenada, enviar sweep nativo y después refresh | Un divergente marcado y reparado; igualdad de todas STATE_COLUMNS frente a expected_states nativo para todos los Listings. El envío manual no acredita la cadencia horaria3600s |

Los18GETde páginas (10faseA/8faseB) y las verificaciones de autoridad son oráculos, no muestras de carga ni latencias HTTP. READ_REPAIRdebe estar desactivado de forma nativa; no se cambia el valor para favorecer el resultado. Se comprueba que esas lecturas no vacíen las marcas antes de iniciar los procesos pertinentes. La ficha/foto/favoritos se representan en EN; el listado cubre ES/EN. Se conservan los testigos funcionales de otras variantes, sin convertir este muestreo en compatibilidad universal.

Worker real prefork2 con rol PostgreSQL restringido del helper existente, credencial privada y retirada al terminar. El observador existente benchmark_celery_observer registra publish/ejecución, pared/CPU del hilo y edad de marcas; una señal adicional local verifica current_user/PID por ejecución. Capturar todos los mensajes relevantes y exigir SUCCESS, no eager, sin snapshot_error y cobertura completa de comprobantes. El trabajo útil y los oráculos nativos no se sustituyen. Reportar el overhead del observador; no equiparar CPU del hilo a CPU del servidor PostgreSQL ni sumar tiempos de fases distintas.

Una faseA incluye espera/arranque deliberados; B parte de worker drenado y mide ticks nativos30/60más cola/ejecución. Una observación/tick no ofrece p95/p99 o SLA. La cadencia no garantiza extremo a extremo ni capacidad. No se atribuye a este lote el transporte de imágenes, procesamiento real de originales o integración externa.

## Ejecución, errores y limpieza

Comando previsto: `.venv/bin/python scripts/run_local_ci.py --profile focused --workers 1 --timeout 900 --native-source /tmp/web-modelos-librdb-v2.4.0 --isolate-test-broker --test tests/test_publication_worker_cadence_reference.py`. Antes de medir: integrar AST/semántica focal, revisar literal/procedencia, congelar fuentes y selección, comprobar opciones del runner y entorno propio. Sin switches de carga ni mocks de dispatch/autoridad/reloj.

Esperas acotadas: arranque45s, drenaje45s y faseBeat150s; se aborta si muere un proceso o aparece un error del observador. Duración prevista de minutos, no horas. Si el entorno impidiera esa previsión, aplicar la persistencia/avisos/pausa/reactivación vigentes sin reiniciar ni duplicar baterías.

Conservar cada FAIL/ERROR/timeout y su causa confirmada o desconocida. Un fallo del instrumento no se atribuye automáticamente a la app. No recortar poblaciones, cadencias u oráculos para obtener PASS. Runner notifica Telegram al terminar tras limpiar; comprobar recibo. Detener procesos propios antes de retirar rol/credenciales, probar identidades PID ausentes y preservar bytes de claves ajenas del broker. Guardar prueba JSON segura y JUnit; excluir logs/credenciales/datos de sujetos del archivo versionado.

## Tabla de comparación y salida

| Medida | Antes aplicable | Referencia nueva prevista | Atribución |
| --- | --- | --- | --- |
| Mantenimiento directo de estados |N01C/349:0,271738s,102Listings,98marcas→0y comando con VACUUM/ANALYZE | Worker refresh con observador y colas | Etapas/condiciones distintas: sin porcentaje causal |
| Tiempo lifecycle HTTP |N01D/351 y oráculos heredados, ramas concretas | No nueva distribución HTTP | No usar tiempo QA como latencia |
| Cola/Beat y antigüedad de publicación | Sin esta referencia nativa30/60en cohorte100 | Pared/CPU y publicación→inicio/edad/vaciado observados por fase | Pendiente; no SLO ni mejora antes/después de código |
| Cadencias |refresh30s/expiry60s/sweep3600s | Las dos primeras sin modificar; sweep manual | Sin optimización de producto ni prueba de una hora |

La salida debe demostrar efectos y retirada inmediata durante retraso, mediciones atribuibles y limpieza; o preservar un fallo que requiera corrección. El resultado no cierra automáticamente39IDs ni N07. N03/N04/N05/N06 y N09/N10 conservan sus límites/propietarios; MOD09 restante al final y optimizaciones marginales aplazadas por el usuario. No beta, proveedor ni datos reales.
