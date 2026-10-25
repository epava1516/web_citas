# N07B — primer fallo y corrección del instrumento

25 de octubre de2026. Alfa, N07 abierto6/13. Continúa el protocolo403, sin cambio de aplicación ni aceptación anticipada.

Run20261025-224510-1359e09b:1FAIL/0ERROR/SKIP,47,249sJUnit, fuentes intactas y Telegram terminal sent. Falló antes de arrancar el worker, al consultar PublicationDirty.objects.filter(listing=individual). PublicationDirty define listing_id como UUIDField, no una relación listing. Se conserva fuente/JUnit/prueba JSON originales; ninguna fase runtime se completó, no hubo procesos worker/Beat propios y no se acredita defecto de aplicación.

Corrección: cinco consultas del instrumento usan listing_id=valor.pk. Además, el finally exterior registra la retirada de rol/credencial incluso si una fase falla antes de las aserciones de éxito. Se mantienen las mismas guardas, población100,18GET ES/EN, prefork2, cadencias30/60sin acelerar, sweep manual, selección de un caso y todos los oráculos. No se sustituye dispatch, autorización, SQL de producto o reloj. Se contrasta el campo real en models.py; no se modifica el modelo.

El original confirma ausencia de PG/Redis/volúmenes/redes/temporal propios y retirada del runtime privado; no se convierte en prueba de retirada observada por rol/credencial individual: esos campos eran None. El helper existente aplica su limpieza de contexto; el nuevo registro añade observación explícita para futuras ejecuciones. No reescribir ese límite del original.

La auditoría comprobó1750huellas del manifiesto del runner; los documentos400/401/403 de la congelación se verificaron aparte porque no estaban en ese manifiesto. Un primer auditor supuso que sólo403quedaba fuera y terminó ERROR; corregido el alcance, pasó sin omitir fuentes de ejecución. Los errores originales y sus recibos se conservan.

Próximo contraste: mismo comando403con instrumento corregido, después de AST/semántica focal y nueva congelación. Las muestras de pared/CPU/cola/edad siguen pendientes.47,249s es QA fallida, no latencia ni mejora temporal. N07B no cierra39unidades; propietarios compartidos y diferimientos vigentes conservados.
