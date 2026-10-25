# N06B — referencia auditada de petición y cola real

25 de octubre de 2026. [Prerregistro358](358-n06-b-prerregistro-peticion-cola-real-20261025.md), candidata instrumentalbd3bee6, run20261025-112239-ba9f016f. **2PASS,0FAIL/ERROR/SKIP**,3inicios302con cuerpos originales de revisión/rechazo intactos. [Auditoría](evidencias/n06-b-cola-auditoria-20261025.json), [eventos estructurados y reproducción](evidencias/n06-b-cola-evidencia-20261025.tar.gz), [congelación](evidencias/n06-b-prerregistro-congelacion-20261025.json). N00/N01aceptados2/13;N06abierto,alfa. Ningún código de aplicación ha cambiado.

## Tiempos anteriores y nueva referencia

Una observación por inicio/estado. La columna de disponibilidad es la cota observada **después de terminar el reloj de la petición**, incluyendo drenaje de tareas y verificaciones del arnés.

| Escenario | Petición anterior N06A eager (ms) | Petición actual N06B encolada (ms) | Disponibilidad observada tras petición (ms) | SQL en conexión de petición N06B | Mejora atribuible a código (ms / %) |
| --- | ---: | ---: | ---: | ---: | --- |
| Inicio desde versión publicada | 456.182 | 109.875 | 460.337 | 27 | No evaluable |
| Inicio en caso de rechazo | 496.601 | 114.054 | 514.251 | 27 | No evaluable |
| Corrección tras rechazo | 556.703 | 131.019 | 471.346 | 27 | No evaluable |

**No es un antes/después de optimización de código.** La aplicación es la misma; cambia el escenario eager por despacho real a worker, con preparación nativa explícita y concurrencia prefork2. No se calcula un porcentaje de mejora atribuible. Los27SQLde petición son una medida real nueva, no el resultado de restar los89/97anteriores. No contabilizan SQL de otros procesos; no se demuestra reducción del trabajo total del servidor.

## Publicación y ejecución en el worker

Cada tarea de estos tres inicios tiene publicación y ejecución correlacionadas por ID técnico, con PID prefork propio, SUCCESS y eagerFalse. Los tiempos publicación→inicio incluyen transporte desde la señal de publicación, no sólo espera pura en Redis.

| Escenario/ordinal | Tarea | Publicación→inicio (ms) | Ejecución worker (ms) |
| --- | --- | ---: | ---: |
| approved/1 | refresh_publication_state | 3.863 | 208.415 |
| approved/1 | process_blob | 3.689 | 226.956 |
| rejected_correction/1 | refresh_publication_state | 6.988 | 231.098 |
| rejected_correction/1 | process_blob | 4.885 | 247.054 |
| rejected_correction/2 | refresh_publication_state | 5.905 | 227.015 |
| rejected_correction/2 | process_blob | 7.606 | 228.254 |

Las dos tareas pueden solaparse entre sí y con el final de la petición. La disponibilidad observada espera también trabajos derivados y sondeos antes de comprobar las fotos; no es el instante exacto de preparación de la foto. No sumar las duraciones del worker como si fueran seriales ni equiparar su máximo a la cota del arnés. El observador de refresh añade consultas diagnósticas propias.

Pasaron los oráculos originales de instantánea publicada, reutilización de bytes, fotos privadas, rechazo e historial/tarifa privada intactos. En cada inicio quedó una foto activa completa/blob ready. La preparación eager original sólo crea la fixture; después, losPOSTmedidos y su trabajo real son no eager. Antes de cadaPOSTse drena y solicita refresh nativo fuera del reloj. No se arrancó Beat ni se alteró su cadencia.

## Entorno, límites y limpieza

PostgreSQL17yRedis7.4propios, namespaceRedis por caso y workerprefork2con rol restringido verificado porTCP, sin privilegios superiores ni propiedad de evidencia. El padre es DjangoClient con rol migrador del arnés: no prueba autorizaciónSQLuniversal del servidor web. Archivos locales privados y almacenamiento de objetos desactivado; sin proveedores/TCP/Gunicorn/carga ni cuotas dedicadas.

Ambos workers terminaron con código0, PIDs/start-ticks ausentes; roles y archivos de credenciales retirados, claves anteriores conservadas y cero claves nuevas fuera del namespace. Contenedores propios y temporal ausentes; fuentes congeladas intactas hasta auditoría. Avisos terminales del runner y auditoría Telegram entregados.

El paso pytest tardó63.887s, incluyendo fixture, roles, arranque/parada y pruebas; no es latencia de aplicación. Con una muestra por estado no hay p95/p99 ni garantía de producción. Las diferencias conN06Ason de modalidad y condiciones, sin candidato de aplicación. Una comparación de optimización deberá conservar modalidad/instrumentos/datos/recursos y medir tiempos anterior/posterior y diferencias válidas.

## Disposición

La señal116/124ya no se interpreta como coste exclusivo del inicio del panel. En este escenario encolado la petición usa27SQLy109,875–131,019ms instrumentados. Esto fija referencia actual; no obliga a modificar código sin coste o defecto demostrado. Permanecen cuenta/representación, variantes y crecimiento de N06, y el procesado fotográfico/refresco conserva sus propios bloquesN03/N07.

Siguiente: integrar semántica del resultado y seguimiento; completar las variantes pendientes deN06 y elegir correcciones por coste probado. Investigación independienteN02sobre las etapasMOD09FAILen curso, sin nuevos ensayos ni cambios de aplicación hasta contrastar su evidencia y prerregistrar el candidato. N02conserva2s/5s y excepción provisional sin ampliarla.
