# Reanálisis del estado: arquitectura, evidencia y método

Corte79bb7d9, comprobación de worktree limpia y ninguna unidad propia cr09/mod08 activa. Análisis de fuentes y artefactos existentes, sin carga nueva, producción, datos reales ni modificación de dependencias.

## Despiece del recorrido

1. Cliente emite a ritmo abierto → TCP/listener Gunicorn → uno de cuatro workers sync. El tiempo emisión→WSGI incluye scheduling/transporte/admisión; no es una medición exclusiva de cola kernel.
2. Django valida filtros y selecciona población. PublicationState evita recalcular toda la población; dirty/versiones desconocidas usan comprobación nativa con límites y fallback.
3. Página seleccionada de24filas: PublicationContext carga autoridad, relaciones y catálogo, valida elegibilidad nativa dentro del snapshot propio RR. No equivale a leer sólo una tabla ni a un único SQL.
4. Presentación consulta fotos/checks frescos después del guard y renderiza. Reutilizar indiscriminadamente lo leído por el guard puede cambiar su semántica de frescura.
5. Escrituras de subida/procesado marcan dependencias transaccionalmente; workerCelery yBeat refrescan.0022 conserva MARK0020 ytriggers originales;0021rechazada no es optimización vigente.

La complejidad útil es proteger pertenencia exacta, revocación, concurrencia y frescura. No hay evidencia de que toda esa complejidad sea legalmente obligatoria ni de que eliminarla conserve contrato. La invalidación de borradores es conservadora y mejorable, pero el intento de evitarla causó stale-negative sin fence ydeadlock con fence: ambosFAIL preservados. No reintroducirlo sin resolver protocolo completo.

## Qué está probado y qué no

Último clean:025813/c0b6645,p951,013029795sFAIL frente<0,8s,1200completas0errores. No representa una nueva medición deHEADactual. Imagenv5con0022,PGreal/health/118paridades prueba entrega en su alcance, no capacidad. Controles de comunicaciones10perfil/20cuenta/6editor son selecciones distintas, no N3 sumado.

Captura031208 instrumentada: espera media emisión→WSGI829,518ms primeros5s y217,730ms15–60s, servicioWSGI229,978/191,256ms. Ocupación de4workers asociada aespera; fasesSQL/CPU/GC solapan. Últimorefreshpositivo2,084s no excluye backlog acumulado. No algoritmo único demostrado, ni prueba de causalidad hardware/ORM/legalidad.

## Hallazgo metodológico

Los contrastesgeo ydirect_fields llaman connection.close() porbrazo y luego miden2requests. Runtime config/settings.py usa CONN_MAX_AGE60/healthchecksTrue, y el arnésHTTP importa esa configuración. La preparaciónSQL se conserva porconexiónfísica, no entreconexiones. Mezclar primerasegundarequest no equivale a servicio caliente estable ni alHTTPconcurrente. Cierre explícito fue simétrico y resultadosfunctional siguenválidos; rechazo significa **sin evidencia suficiente para adoptar**, no demostrar que la idea siempre empeora.

Relectura offline, referencia original de cada ensayo, sin nuevas mediciones:

| Ensayo | Primera request porbrazo, media | Segunda request, media |
|---|---:|---:|
|directbinding055219|431,28ms|316,67ms|
|geocat053127|457,42ms|289,76ms|

No atribuir toda diferencia a conexión/preparación: intervienen calentamiento, orden, GC yhost. Dosrepeticiones/tresbloques no cuantifican por sísolos ruido niintervalos deconfianza. Las fuentes/recibos se preservan; no revertir rechazos ni seleccionar sólo muestras favorables. Resultadooffline/hashentradas en artifacts/cr09-state-reanalysis-20261016/result.json.

[Django5.2](https://docs.djangoproject.com/en/5.2/ref/databases/#persistent-connections) explica persistencia porconexión, máximo devida yrestauración de parámetros. [pyperf](https://pyperf.readthedocs.io/en/stable/run_benchmark.html) recomienda comprobar estabilidad y metadatos; [sistema](https://pyperf.readthedocs.io/en/stable/system.html) distingue afinidad/frecuencia/ruido. No ejecutar system tune global ni cambiar cuotas/energía. Perfil energético del portátil variaba con cargador: no atribuir diferencias de portátil al código.

## Siguiente control antes de otra optimización

Prerregistrar control A/A sin cambios de app: mismo callable en ambos labels, conexión fría y persistente separadas, identificador backendSQL y recuento de prepared statements comprobados fuera del reloj, mismos datos/cutoffs/bytes/no-store. Medir porbloque y porrepetición, no mezclar frío/caliente; mismas cuotas y una sola actividad propia. Elegir número finito de repeticiones y criterio de estabilidad antes del ensayo. RegistrarGC/metadatos sin perfilador ni alterar política, preservar errores, sourcefreeze ycleanup. Si referencia varía tanto como el ahorro buscado, declarar inconcluso y atribuir ruido antes de más variantes. No hay autorización técnica inferida para relajar SLO, añadir caché de autorización, cambiar dependencias o repetirFAILclean.

Después, según evidencia: reducir demanda material porrequest o resolver admisión con progreso seguro, conservando filtros/revocación/guardia. No barrido workers/threads: contrastes4/6/8 yrechazogthread mantienen alcance. Matriz83y88/contrato16 conservan el resto deCR09→CR10→GS01→BF/BB→C. No porcentaje nuevo ni aceptación global.
