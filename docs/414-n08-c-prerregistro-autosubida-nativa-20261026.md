# N08C — prerregistro de autosubida con worker y Beat nativos

Estado: preparación, sin ejecución ni aceptación. Complementa [N08B](413-n08-b-prerregistro-comercial-20261026.md). N08 abierto, 7/13 bloques obligatorios aceptados. Base `0d7a3a3bac080cd38785672a009c39e00fb7e64c`; se preservan las evidencias comerciales originales y los resultados N08A/A2.

## Pregunta y alcance finito

Completar `task:T_apps.catalog.tasks.bump_promotions` y `beat:24:apps.catalog.tasks.bump_promotions` con observación de despacho, cola y ejecución real. La configuración fuente activa `synthetic-promotion-bumps` sólo con `PROMOTION_TEST_MODE`, fuera de producción y recuperación, a **60 segundos**. La prueba histórica con un intervalo diagnóstico de un segundo no acredita esta cadencia. Los originales de ventanas, cupos, carreras y avance del lote de 100 se conservan con su alcance; no se repiten sin causa ni se convierten en pruebas de worker.

Un caso nuevo explícito, serial, PostgreSQL y Redis desechables del runner oficial. Preparación con fixture nativa y dos pedidos creados por los servicios locales de simulación, evento sintético de éxito y dos derechos de autosubida; no pagos reales. Versiones con intervalo diario y cupo uno; desplazar los inicios de los derechos al pasado manteniendo su duración para permitir la ventana nativa sin parchear el reloj. El segundo derecho permanece inicialmente futuro para separarlo del primer despacho.

## Fases previstas

1. Encolar una tarea real antes de iniciar worker prefork de dos hijos, con rol restringido del arnés existente. Observar publicación, espera con arranque incluido, ejecución no eager y primera subida del derecho elegible. El segundo derecho futuro no puede recibir una ejecución de subida. Comprobar inmutabilidad de las fechas editoriales, revisión aprobada, versión del ciclo y cantidad de revisiones.
2. Con worker listo, despachar un reintento real inmediato y comprobar la unicidad de ventana/cupo. Si se cruza una frontera UTC durante la prueba, aplicar el oráculo de ventanas y cupo por día a las marcas reales, sin afirmar que una nueva ventana válida es una repetición del mismo intervalo.
3. Suspender explícitamente el primer derecho fuera de los relojes de tarea; activar el intervalo del segundo, revocar su consentimiento mediante la operación nativa disponible antes de Beat y verificar que nunca recibió una subida. Iniciar un único Beat privado, conservando la entrada nativa de 60 segundos. Observar dos despachos y ejecuciones de Beat, su separación real y la actualización de `last_checked_at` del derecho revocado sin nueva `PromotionBumpExecution`. La suspensión del primer derecho evita atribuir a idempotencia una exclusión que corresponde a la suspensión; la ausencia del segundo sí prueba revalidación de elegibilidad.

Se permiten las tareas nativas de refresco que produzcan las operaciones de preparación/revocación; se identifican y drenan dentro del mismo namespace, sin sumar sus métricas a las de autosubida. No alterar el calendario global, servicios, guards, broker compartido ni funciones de aplicación. El runtime privado hereda la configuración local, habilita el modo sintético y selecciona sólo la entrada nativa de autosubida; no cambia sus 60 segundos.

## Medición, limpieza y aceptación

Reutilizar el observador de tareas existente y la prueba de rol SQL en cada ejecución real. Registrar ID, publicador, PID, pared/CPU del hilo, resultado, marcas de publicación/inicio/fin y espera de cola. El primer despacho incluye arranque; los despachos posteriores se presentan aparte. Dos ticks son una referencia finita, sin p95, SLA, capacidad de producción ni mejora antes/después. No inferir uso efectivo de ambos hijos a partir de la mera existencia de dos procesos: registrar los PIDs realmente ejecutores.

Esperas internas con límites: arranque/drenaje de hasta 45 segundos y fase Beat hasta 180 segundos, con comprobación de procesos vivos. Tiempo esperado de minutos, no de horas. Si aparece un fallo, conservar evidencias y distinguir instrumento/aplicación. No repetir pruebas válidas por documentación o skills.

Comprobar separación del namespace y conservación de claves Redis ajenas, identidad PID/tiempo de inicio y desaparición de todos los procesos propios, eliminación del rol temporal, credenciales y módulo privado, más limpieza terminal del runner. No publicar logs, secretos ni datos de sujetos. Toda ejecución de pruebas usa notificación terminal Telegram y recibo confirmado.

Antes de congelar o medir: revisión acotada con `django-celery-expert`, `django-expert` y `django-reviewer`, AST del instrumento nuevo, semántica de este documento y seguimiento, auditoría del grafo y selección exacta. La aceptación de N08 requiere conciliar sus 17 identificadores; este prerregistro no lo cierra ni modifica el contrato. No migraciones, proveedores ni apertura de beta.
