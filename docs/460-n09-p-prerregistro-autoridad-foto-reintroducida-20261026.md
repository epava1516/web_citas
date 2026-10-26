# N09P — prerregistro de autoridad en imagen reintroducida

Estado: diagnóstico finito pendiente, sin cambio de aplicación. N09 abierto y8/13
bloques obligatorios aceptados. Base5735b72; [última referencia459](459-n09-o-referencia-purga-exportaciones-verificada-20261026.md).

Corte: grafo2104fuentes/20615nodos/85412relaciones, SHA256
468902ac759dec9c047982476b15354f5c5cd82e1e211d016edc8f7a0fb1bcef;
manifiesto completo contrastado sin diferencias antes del análisis. Actualizar AST
del nuevo instrumento ysemántica de este protocolo antes de congelar ymedir.

Hipótesis: photo_reintroduction_views.allowed consulta permiso/MFA del User de la
petición antes de locked(). Photo_reintroduction_review.locked comprueba ese actor
antes de esperar alcance/candidate/Revision/Blob; refresca prueba yrecursos, pero
no el operador antes de retornar. Image comprueba read propio ysource, abre el
derivado ydevuelve FileResponse. Una retirada del permiso durante la espera de
Blob podría dejar vigente la caché del actor yentregar bytes privados. Las
protecciones E–H de otras operaciones no se aplican a este helper; las carreras
existentes de medios/prueba son garantías distintas. Es hipótesis de fuente,
no vulnerabilidad runtime confirmada todavía.

Selección: dos casos HTTP Django Client sobre el mismo tipo de seed nativo de
setup_review: control legítimo yretirada de review_photo_reintroduction durante
una espera realPG. Misma instancia de usuario/permiso cacheado en la petición,
sesión MFA/accountversion válidas. Holder retiene el Blob de mayorPK del par,
workerPIDdistinto observado bloqueado mediante pg_blocking_pids; sólo entonces
retirar el permiso yliberar el holder. Sin mocks de permisos ni sustitución de
locks. SQL, recursos yservicios fuera del runner propio no se tocan.

Oráculos: controlHTTP200con los bytes exactos del derivado; revocadoHTTP403ycero
bytes privados. Consumir ycerrar cada respuesta en el hilo que la obtiene.
Snapshots de todos los modelos instalados/through/sesiones antes ydespués de la
operación; el snapshot previo incluye la retirada autorizada del permiso dentro
de la transacción holder para no confundirla con efecto del consumidor. Medios
por árbol/digest/mtime/modo, sin diferencias. Espera confirmada, permissioncache
calentada, worker statement_timeout10s, future15s, cancelación sólo de su conexión
en timeout yfinalmente conexión/thread/holder cerrados. Emitir sólo hashes,
conteos, estados ybanderas; sin cuerpos, identidades oSQL.

Criterio: ambos casos deben preservar oráculos; el original se espera inseguro
en el revocado si la hipótesis es correcta. Conservar PASS/FAIL/ERROR originales;
un ERROR de fixture no demuestra el defecto. Si se confirma, corregir la guarda
compartida yla frontera de petición sin relajar negativos. Después repetir sólo
los casos no válidos oafectados yseleccionar regresiones pertinentes de revisión,
inspección/decisión/proof/medios, con variantes frescas de sesión/MFA según el
cambio. Prerregistrar esa candidata ysu alcance antes de ejecutarla.

Medidas: tiempos del cuerpoQA con preparación, espera inducida ysnapshots;
no latencia normal de app ni mejora causal. Tabla posterior separará lectura
ilegítima antes/después de tiemposQA yconservará la ausencia de benchmark.

Gates: root escribe/revisa instrumento acotado con Django/seguridad; revisión
nativa independiente si el slot está disponible. Ruff yAST/semántica focal,
congelación mediante secuencia estricta, runnerfocusedserial/parsernativo y
PostgreSQL/Redispropios. Toda prueba ysu auditoría notifican terminal porTelegram
con recibo. No reproducir la desviación de lanzamientoN09O: no arrancar si falla
un prerrequisito documental. Sin migraciones, servicios normales, proveedor oCI.

Conciliación: propuesta nativa52IDs de derechos disponible,49con referencias
limitadas y3que comparten este hueco; todavía requiere aceptación independiente
porroot. Otros87IDs conservan su trabajo de conciliación. No139pruebas ni nuevas
funcionalidades. Un intento de segundo escritor bloqueado por límite de threads
no paraliza el trabajo; root prepara el diagnóstico sin duplicar escritores.

Límites: escenario finito de imagen/privateUser revocado, no barrido exhaustivo,
worker,proveedor,entrega de originales opublicación real. Alpha/noindex. N02restante
al final,N10/N11/N15pendientes,N12–N14condicionados. Mantener limpieza final deartifacts
como última acción obligatoriaN15, aún no ejecutada; preservar cambios laterales.
