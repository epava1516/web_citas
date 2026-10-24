# B12 — Informes locales de ventanas de eventos

Estado: verificado en selección20PASS; cobertura operativa completa pendiente.

Grafo previo77:055a94fe4f56781dbbf5676fbe4a0d8e8ed3e38478880af4367f13950ab248fd. Continúa [medición134](134-coste-transporte-eventos-beta-b12-20261020.md) y [eventos131](131-eventos-operativos-beta-b12-20261020.md). No modifica autoridad ni rutas públicas.

El comando administrativo operational_events_report lee un archivo JSONL regular local con --input, --start y --end (epoch enteros, ventana semiabierta de1a3600segundos). Límite8MiB total,2048bytes por línea y100000líneas. Archivo ausente, no regular o límites excedidos producen error fijo y ninguna salida JSON parcial. Sin endpoint, demonio, cron ni envío externo.

apps/core/operational_window.py valida esquema1, claves exactas y vocabulario fijo. Rechaza duplicadosJSON, constantes no finitas, UTF8 inválido y valores ajenos al contrato. Agrega lecturas observadas, fallback, clases5xx, motivos, resultados del cuerpo de tareas y contadores de entrega conocidos; conserva muestras de contadores desconocidos sin convertirlas en cero. Si no hay lecturas o existe ruta other, la fracciónfallback es null.

coverage=unverified y health=unknown siempre. El archivo puede estar incompleto, repetido o cortado por rotación; no acredita todo el tráfico ni disponibilidad del worker. Los marcadores transport_gap se cuentan, sin sumar sus contadores acumulados entre procesos no identificados. No registrar identidades, preferencias, contactos, líneas originales ni nombres de archivos de entrada en el JSON o mensajes de error.

Prerregistro: nueve casos nuevos, incluidos límites temporales, fallback y éxito de cuerpo con entrega retry, marcadores repetidos, entradas privadas/malformadas, ventana inválida, consumo de dos eventos del handler real y errores del comando sin salida parcial. Ejecutar junto a cinco pruebas de emisor y seis del snapshot en PostgreSQL/Redis aislados con workers1;20casos previstos. Revisar fuentes congeladas, XML, limpieza y Telegram antes de declarar resultado.

El informe es una herramienta administrativa de observación parcial. No sustituye receptor continuo con salud/ventanas conciliadas, verificaciónruntime de rotación, coste/cadencia del snapshot, umbrales justificados ni ejecución de runbook. B12 sigue abierto y B07 permanece pendiente de capacidad.

## Resultado terminal

235519-c96ad4c1:20PASS/0FAIL/0ERROR/0SKIP,60,607sJUnit. Nueve casos de ventanas, cinco de eventos y seis de snapshot. [Auditoría terminal](evidencias/b12-windows-terminal-audit-20261020.json): fuentes congeladas contrastadas de nuevo, procesos terminales, contenedores y temporal ausentes, TelegramPASS confirmado.

Producto previo intacto respecto234058; sólo se añaden el agregador y su comando administrativo. Verificado consumo de dos eventos del handler real, rechazo de entradas privadas/malformadas y límites efectivos de bytes/líneas, FIFO sin bloqueo, errores fijos sin salida JSON parcial y cobertura/health explícitamente desconocidas. El worker real de la selección y el recorridoHTTP state/fallback también pasan. No medición nueva de capacidad ni aceptación global.

Uso administrativo: `python manage.py operational_events_report --input /ruta/local/eventos.jsonl --start 100 --end 200`. Los números son un ejemplo de límites epoch, no una ventana actual. El archivo debe contener líneas JSON sin prefijo añadido por el visor de logs. Inspeccionar counts.malformed_or_unrecognized y los marcadores observados; una fracciónfallback null no significa frecuencia cero. No deduplicar ni sumar pérdidas acumuladas sin identidad de origen.

La ausencia de eventos o marcadores no acredita receptor sano. El informe mantiene health=unknown y coverage=unverified incluso con entrada válida. Pendientes: receptor y salud, ventanas conciliadas, rotaciónruntime, coste/cadencia de snapshot y umbrales/runbook. B12 sigue abierto.
