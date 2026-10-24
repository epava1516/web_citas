# B07 — Finalización de estadísticas del escenario promocional

Estado: finalización sintética integrada y calibrada; sin aceptación de capacidad ni cambio de producto. Producto sin cambios, ocho de18cerrados.

167detecta tres estimaciones iniciales incompletas sin alterar filas. Se añade finalize_promotional_statistics al helper sintético y se invoca sólo en el escenario beta_promotions de test_contract_http_load, después de refresh_publication_state y antes de levantar servicios/medir HTTP. Camino orgánico y actuales políticas de requests sin cambio. El manifiesto guardará método/tablas/tiempo de preparación, no fingirá que el benchmark anterior lo incluía.

La función exige noPRODUCTION/noRECOVERY/PROMOTION_TEST_MODE, autocommit, DBPostgreSQLtest/usuarioCI/hostloopback, runIDycontenedor exactos/label/puerto/estado real, cohorte sintética completa y publicación limpia/actual. Rechaza antes de ANALYZE una preparación incompleta, transacción heredada, producción, contenedor ajeno o cardinalidad declarada incorrecta. Sólo ejecuta ANALYZE de ocho tablas predefinidas. No amplía permisos del runtime ni modifica filas, restricciones, índices, GUC, recursos, workers, carga o SLO.

Primer gate: test_promotional_statistics_preparation.py con10perfiles/2derechos por servicios reales sintéticos. Cinco negativos deben rechazar sin ejecutar ANALYZE, positivo debe emitir exactamente las ocho tablas y conservar once checksums de dominio. PostgreSQL real, fuentes congeladas/limpieza/PIDs/Telegram. No simulador de DB ni de ownershipDocker.

Después de PASS auditado, calibración existente functional TCP10perfiles/20RPS3s/1upload, cuatro Gunicorn sync, worker/Beat propios y modo promocional. Revisar metadata nueva y retiro de servicios, sin denominarla capacidad. Sólo tras ese terminal se preparará un nuevo corto10000/2000 con la diferencia de preparación explícita. Antiguo112359FAIL sigue válido; no se borran ni atribuyen mejoras al código de aplicación.900s sigue bloqueado.

## Gates terminales auditados

151858-6e0282f2:1PASS/0FAIL/0SKIP en PostgreSQL propio; [auditoría focal](evidencias/b07-statistics-finalizer-20261021-151858-6e0282f2-audit.json). Cinco negativos previos aANALYZE, ocho tablas exactas y once checksums de dominio preservados. La función exige además get_autocommit verdadero; IDs oficiales de ejecución aislada o benchmark admitidos con Docker real. El test sólo se omite fuera del runner desechable requerido; aquí se ejecutó, sinSKIP.

152059-4462fced:1PASS/0FAIL/0SKIP,87,22spytest sin warnings; [auditoría TCP funcional](evidencias/b07-statistics-tcp-calibration-20261021-152059-4462fced-audit.json). Diezperfiles/dosderechos,20RPS3s/60dinámicas200 y1subida302conPhoto/borrador/UploadAttempt persistidos; p95observable239,600ms. Patrocinio presente en primerasrespuestas frías. Manifest post_preparation_statistics contiene las ocho tablas y10,034ms de ANALYZE. Cuatro Gunicorn sync/unhilo y worker/Beat reales propios; procesos/servicios/Redis/temporales retirados, recibosTelegram terminales y auditorías confirmados.

Las dos ejecuciones comparten exactamente las fuentes congeladas;726runtime de la candidata de aplicación permanecen idénticos. Auditoría también comprueba que prepare_promotional_load/reset_preparation_broker anteriores son prefijo byteexacto, y que el único añadido al arnés HTTP es invocar la finalización en beta_promotions tras refresh. No se cambian timeout por petición, generador, mezcla, cupos o SLO. Los borradores de upload posteriores conservan su preparación y refresh nativos existentes; no se ejecuta ANALYZE en los workers ni durante arrivals.

La finalización queda aceptada como preparación sintética explícita del arnés, no como mejora medida del runtime. La muestraTCP10no acredita10000/2000 ni900s. Nuevo corto169 conservará112359FAIL válido y registrará sus diferencias; no calcular porcentaje de mejora causal frente a otro corte/host. Ocho de18cerrados.
