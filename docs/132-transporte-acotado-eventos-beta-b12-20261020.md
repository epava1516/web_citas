# B12 — Transporte acotado de eventos

Estado: corrección verificada funcionalmente en selección47PASS; coste normal y operación completa pendientes. No cierra B12 ni capacidad. Continúa [eventos131](131-eventos-operativos-beta-b12-20261020.md). Antes de analizar este incremento: grafo71 sellado, SHA28b0e3c097e78c86403d4f714a109d02978d093ea2cb3612d0066e8ff57a120d, actualización dirigida sin semántica exhaustiva.

## Defecto reproducido

[Ensayo de tubería real](evidencias/b12-blocked-event-sink-reproduction-20261020.json): emisor de eventos y StreamHandler original en proceso propio, tubería llena65536bytes. No retornó durante300ms y el canal de espera kernel fue pipe_write; retornó después de vaciar. El PASS del instrumento acredita la reproducción de bloqueo, no corrección ni capacidad. No fue servidorHTTP ni PostgreSQL ni un proveedor externo. El emisor tiene SHAc2b88212433a0d37d78464859d234968b4bbf57651a2e4a636f76a74af682ed4.

Capturar excepciones de logger.info no impedía esperar al destino. El estado funcional40PASS de131 se conserva en su corte original; no demuestra que esta nueva configuración de transporte esté verificada.

## Corrección y límites

`NonBlockingOperationalHandler` recibe los mensajes ya acotados del canal operational.events. El productor sólo formatea y encola sin esperar espacio; un hilo daemon por handler/proceso es dueño de la escritura al destino. Cola≤256mensajes, cada mensaje≤1024bytes más terminador, además de un mensaje en vuelo y marcador de pérdida. Esto acota payloads pendientes, no acredita por sí solo RSS total, stack del hilo ni presupuesto del servidor.

Si se llena, descarta y cuenta. El writer emite transport_gap al poder escribir de nuevo. Sus contadores son acumulados del proceso, sin identidad de visitante, y no se suman como un contador global. Cualquier marcador invalida una interpretación de ventana completa; ausencia de marcador no acredita que no se perdiera la cola al terminar el proceso. Se mantienen pérdidas posibles de cola/inflight en shutdown y errores de escritura. No es un ledger durable.

El handler duplica el descriptor, no cambia sus flags y sólo cierra su duplicado. La escritura os.write ocurre fuera del lock del handler y del módulo logging. close no hace flush ni join de un destino bloqueado. No se aplica a todos los logs históricos de Celery, Gunicorn o terceros: estos pueden tener otros bloqueos y políticas.

Primera revisión readonly detectó tres fallos de la propuesta antes de probar: cierre/publicación de descriptor no serializado con fork; cierre hijo con Event heredado; cleanup incompleto entre dup y construcción de Queue/Thread. Se corrigieron antes de ejecutar: protocolo atfork único con registro débil de handlers, serialización frente al ciclo del descriptor, reset hijo y cleanup de toda la inicialización posterior a dup.

El orden es lock del módulo logging y adquisición sin espera de locks de handlers; si uno no está disponible se liberan todos antes de reintentar, evitando esperar al handler mientras se bloquea logging.shutdown. El hijo recibe estado nuevo sin cola ni thread ni Event del padre. La coordinación usa logging._lock privado: se contrastó el CPython3.12.15 instalado y la [fuente oficial3.13](https://github.com/python/cpython/blob/v3.13.0/Lib/logging/__init__.py); no se declara ejecución3.13. Este acoplamiento exige conservar pruebas de fork/retirada al actualizar Python.

## Protocolo previo a pruebas

Siete casos ejecutados en test_operational_event_handler.py, con scripts/probe_operational_sink.py congelado como fuente:

- Tubería real llena:1000eventos retornan en<1s sin vaciarla, cola≤256 y pérdidas contadas≥743. Después se vacía, aparece transport_gap y termina el writer.
- Fork controlado con writer bloqueado: hijo no hereda cola ni contadores del padre, emite sin esperar al destino y termina. No acredita todas las pérdidas de workers prefork.
- Cierre y salida de proceso con tubería llena, sin vaciarla: retorno de close<1s, sin join del destino. El primer caso de pipe incluye fork y recuperación; esta es otra ejecución.
- Retirada de descriptor con reutilización real por/dev/null y fork concurrente: fork espera la transición y el hijo no cierra el descriptor ajeno. Se cierra el handler en el hijo antes de emitir.
- Fallo de constructor Queue y de constructor Thread después de dup: cada duplicado retirado, descriptor original intacto.
- Mensaje excesivo y handler cerrado no arrancan writer; pipe roto queda en contador, sin texto de excepción.

Los siete casos incluyen tres escenarios de pipe/fork, dos fallos de inicialización y dos controles de límite/error. El límite1s es criterio del ensayo de transporte de1000eventos y cierre, no presupuesto HTTP, ni comparación ROI, ni cambio del p95<800ms contractual. No ajustar después del resultado. Datos y errores son sintéticos; tubería y fork son del kernel real.

Ejecutar además los40casos de131 con la nueva configuración; no reutilizarlos como si fueran fuentes idénticas. Congelar fuentes después de actualizar AST/configuración y semántica de este protocolo. Verificar terminal, limpieza de procesos/colas/contenedores y Telegram. No otras cargas propias durante el ensayo.

Persisten B12: coste normal/RSS del transporte y recolector, destino/rotación propios, salud y ventanas de recogida, umbrales/runbook, entrega fallida/retraso y recuperación del outbox con worker real. B07 sigueFAIL y900s bloqueado. No proveedores, datos reales, servicios normales ni despliegue.

## Resultado terminal

232949-2d2b26df:47PASS/0FAIL/0ERROR/0SKIP,76,338sJUnit. [Auditoría terminal](evidencias/b12-transport-terminal-audit-20261020.json):7casos de transporte+5eventos+6snapshot+2recuperaciónworker/Beat+27privacidadlogging. Fuentes comparadas de nuevo, procesos terminales, PostgreSQL/Redis y temporal eliminados, TelegramPASS confirmado. Producto previo sólo cambia config/settings.py y añade operational_event_handler.py; emisor, reglas, tareas y modelos permanecen idénticos al corte131.

Los tres escenarios de tubería/fork cumplen los criterios prerregistrados, incluido retorno de1000eventos y cierre<1s sin drenar el destino, recuperación con transport_gap, reinicio del hijo y supervivencia del descriptor reutilizado. El instrumento drena continuamente tras liberar al productor; no supone que todo el lote restante quepa en la tubería. Las dos revisiones fueron estáticas y no sustituyen estos casos ejecutados.

Corregida y verificada la espera síncrona del canal de eventos en los escenarios indicados. No medida de coste normal/RSS ni de SLOHTTP, ni robustez de todos los logs de terceros, ni pérdida prefork en tareas de negocio. Persisten ventanas/salud del receptor, rotaciónruntime, umbrales/runbook y recuperación del outbox; B12 sigue abierto y B07no cambia.
