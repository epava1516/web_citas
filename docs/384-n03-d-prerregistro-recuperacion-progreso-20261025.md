# N03D — progreso de recuperaciones y fotos históricas

25/10/2026. Alfa, N03 abierto,3/13bloques obligatorios aceptados. Corte previoN03Cfinal4d9218c27a9be1faad4aa074946374795f0397bc3f659e5a3e605ec4a50ef7b8,1986fuentes sin discrepancias, revalidado antes del análisis. Semántica focal383/341/seguimiento yAST vigente; no reconstrucción global ni nueva extracción de fuentes idénticas. Consulta graphify seguida de lectura directa; salida truncada no demuestra cobertura exhaustiva.

## Hipótesis funcionales antes de corregir

process considera listo todo statusready, aunque signature sea{} (estado legado posible por migración0003). detect_matches retorna sin completar si no hay firma. recover_media_jobs lo vuelve a seleccionar si hay Photo activa incompleta. Además el selector no excluye revisiones históricas, mientras el detector sí las excluye. Un Blob histórico o compartido entre histórico incompleto y actual ya completo podría permanecer en el lote de100 sin trabajo útil. Son hipótesis de no progreso pendientes de reproducción; no afirmar bug runtime antes de ejecutar. No es otra optimización marginal del detector.

Cuatro casos nuevos tests/test_media_recovery_progress.py, PostgreSQL real y archivos sintéticos privados. Preparación por servicios reales genera ready/firmas/comparison_complete; se induce firma{} como estado legado, o historial mediante ledger sintético persistido ya usado por test_photo_disposition_authority (no acredita aprobación humana/proveedor). Revisión nueva creada después de la ejecución distingue histórico/actual por la consulta nativa, sin parchearla. Transporte .delay capturado y servicio process directo; no worker/Beat/backoff reales.

1. Firma vacía: dos ticks deben reparar desde original inmutable, recuperar firma/ready/comparison_complete, attempts1→2, envíos[1,0]; original y bytesderivado intactos. Referencia prevista FAIL si ambos ticks no hacen progreso.
2. Sólo foto histórica incompleta: dos ticks sin envío[0,0],sin marcar falsamentecomparison_complete, borrar evidencia, regenerar ni modificar firmas/archivos/intentos. Referencia prevista FAIL por envíos repetidos.
3. Blob compartido por histórico incompleto y actual nuevo: primer tick completa sólo el actual, segundo no reenvía[1,0],histórico permanecefalse y sin regeneración. Referencia prevista FAIL por hermano histórico.
4. Firma vacía con original físicamente ausente: borrar exclusivamente archivo sintético propio, dejar fallo explícito/reintentable; tres recuperaciones alcanzan attempts4/failed/errorcode y cuarta omite:envíos[1,1,1,0],sincomparison_complete falso. Referencia prevista FAIL si permanece silenciosamente ready. Esto comprueba el selector periódico directo, no un límite global de mensajes Celery ni autoretry real.

Registrar por tick conteos/estado/intentos/errorboolean y reloj selector/process si se ejecuta. Sin SQL/textos/IDs de sujetos ni cuerpos. Trabajo útil cambia entre noop defectuoso y reparación real: tabla antes/después con ámbito y sin porcentaje causal de aceleración. QA separada. No afirmar SLO/p95/fairness/capacidad a partir de cuatro casos.

## Decisión y verificación

Primero ejecutar cuatro casos sobre aplicación intacta y conservar cada FAIL/ERROR real, sin alterar oráculos para pasar. Si confirman, corregir sólo preparación que necesita generar firma y selección ready con una Photo pendiente que el detector realmente admite (histórico excluido); no cambiar autoridad, marcar histórico completado, borrar evidencias ni limitar candidatos del detector. Mantener fences de generación383, privacidad y límites. Revisar qué ramas de preparación deben seguir comparándose antes de excluirlas: no inventar exclusiones por similitud de nombres.

Después ejecutar archivo nuevo completo+test_media_job_recovery.py+test_preparation_cleanup.py+test_photos.py:37casos previstos (4+16+11+6),0FAIL/ERROR/SKIP. Fences,fallo propio trasready,retención y flujos originales deben mantenerse. Congelar fuente/dependencias/imágenes/grafo antes de cada pasada,scopeAST explícito,PostgreSQL/Redis propios,namespaces/recursos/temp retirados e inventario independiente,Telegramterminalsent. No aceptar propuestas como evidencia. Nada de publicar/contratar/datos reales.

Actualizar semántica focal del protocolo yAST instrumento antes de congelar. Runner serialoficial: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test SELECCION`. Referencia sólo4nuevos y candidata37segúnselección. No pruebas de horas previstas. N03/N07 siguen abiertos para conciliación y reintentos/Beat reales;MOD09 diferido al final por usuario, tiempos actuales aceptables en alfa.
