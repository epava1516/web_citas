# B07 — Diagnóstico del emisor de filtros combinados

B07-278 implementado: diagnóstico explícito de despertar y despacho con observador de loop existente;53pruebas locales PASS. Calibración diagnóstica nativa pendiente; INVALID277 preservado y B07 abierto.

## Incertidumbre concreta

[277](242-calibracion-http-filtros-combinados-b07-20261023.md) conserva p99demora32,880ms>25ms, con60respuestas correctas,44oráculos antes/después equivalentes y sin eventosGC. El contador de throttling acumulado no está alineado con d-17; no identifica su causa. No repetir una carga limpia buscando otro resultado.

Hipótesis a discriminar: demora antes de despertar el emisor frente a demora entre encolado y comienzo de la coroutine. Registrar scheduler_awoke_at, task_queued_at y emitted_at del emisor original mediante trace_scheduler=True. Componer observed_transport y ObservedLoop existentes, sin cargar el pluginpytest restringido a otro node. Observaciones de loop incluyen reloj monótono, CPU de hilo, /proc/self/task/tid/schedstat, espera de runqueue y selector/callbacks. Retención máxima256eventos por criterio existente; nunca contenido, encabezados o credenciales. No restar intervalos solapados ni llamar causal a wall residual sinCPU.

## Variante aislada y clasificación

--generator-diagnostic requiere --combined-filters --territorial beta-http-functional100. Se conservan las incompatibilidades de242: sin corto, contractual, observadorhost, backlog, estadosmixtos ni mezcla confirmada. Mismos100perfiles70/30,20derechos, atributos,44oráculos antes/después,60slots/38rutas/20RPS3s,1upload y4workers/unthread. Producto628 intacto,8CPU8GiBswap0, GC y límites65s/70s/p95demora10ms/p9925ms/máximo100ms sin cambios. Watchdog2400s/app3000s de la calibración100 vigente.

Si el transporte esINVALID, la aserción funcional permanece y se conservan el FAILJUnit/ERRORexterno junto al diagnóstico. Si el transporte satisface sus guards, el controlador clasifica BETA_HTTP_GENERATOR_DIAGNOSTIC_NOT_CAPACITY, nunca funcional limpio ni contractual. iterations/scope/scheduler_trace obligatorios para ese resultado. Tener datos del observador no permite aceptar un resultado inválido. El JSON completo se incrusta en la propiedad JUnit del test; archivo temporal exclusivo del contenedor se elimina con él. Sin flag no se cambia loop ni emisión.

## Ejecución279 y revisión

Una ejecución instrumentada: .venv/bin/python scripts/run_notified.py --name 'B07 generador279 diagnóstico combinado100' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-functional --territorial --combined-filters --generator-diagnostic --cpu-budget 8 --app-image sha256:385e6dcd16ea7b6a44b7383028093dbf0047488e960a8c08ced1a01582ca0056

Antes: Ruff,53guards/observador local, AST y semántica dirigidos, protocolo y fuentes congeladas; TelegramINICIO confirmado. Reutilizar preflight273 en ámbito no afectado; comprobar runtime/cuotas/limpieza reales. Sin otra batería simultánea. Auditoría antes de editar: fuentes prerregistro/CI/árbol, producto628, protocolo bytes/SHA, JUnit/ledger/44+44oráculos/mezcla/upload, observaciones y tiempos de emisión coherentes,6servicios/cuotas/Gunicorn/Beat y ausenciaDocker/PID/reciboTelegram terminalhost. Preservar negativos antes de cualquier corrección.

Los datos no explican retrospectivamente277 por sí solos; observador añade coste no causalmente calibrado. Localizar qué frontera concentra la demora observada y contrastar intervalos compatibles. Si no reproduce demora, registrar ausencia en ese diagnóstico, sin declarar resuelta la causa anterior ni repetir hasta reproducir. Ningún cambio deCPU/GC/workers/umbrales autorizado por esta prueba. No900automático ni repetir262/265/268/269/270/271. Siguiente decisión depende de evidencia; costePRODUCTION/checked conserva su alcance pendiente. Ocho18cerrados, sin aceptaciónB07/beta ni proveedor/datosreales/publicación. OchoClaudeV1históricos/consumo preservados, ninguna nueva invocación.


## Diagnóstico279 auditado

B07-279 diagnóstico nativo auditado:60HTTP correctos,44oráculos antes/después y p99generador4,943ms con loop observado. No reprodujo INVALID277 ni resuelve su causa; B07 abierto, ocho18.

Corrida20261023-075736-090ee1e6:1PASS135,026sJUnit, clasificada BETA_HTTP_GENERATOR_DIAGNOSTIC_NOT_CAPACITY. TransportePASS dentro del ensayo instrumentado; no trasladar su validez a una carga limpia ni cambiar277.60respuestas correctas,1upload302persistido,44oráculos antes y44después equivalentes. Generador p953,980ms/p99máximo4,943ms; HTTPp95235,182ms descriptivo. Nada de esto acepta capacidad sostenida.

Observador593iteraciones,0eventos retenidos con umbral existente20ms. Máximos inclusivos:CPU de hilo1,491ms/runqueue13,063ms/overshootselector12,249ms; no se suman ni son causa de277. Wallmáxima48,983ms puede incluir espera solicitada por el temporizador, no equivale a retraso de emisión. La mayor demora total esd-24:4,943ms, con4,274ms antes del despertar y0,665ms de despacho; el pequeño resto es encolado. No hubo intervalo retenido que atribuir a esa emisión. El diagnóstico no reproduce la cola de32,880ms anterior y no prueba su origen.

Auditoría generator279-audit.json verifica1703fuentes prerregistro/CI/árbol, protocolo originalbytes,628producto intacto, clasificación propia, JUnit/ledger/fronterasdeemisión/observador, fuentes del instrumento,4workers/Beatworkerreales/GCsin cambios/cuotas8CPU8GiBswap0,ausenciaDockerPID yTelegramhostPASS. Auditor inicial falló al comparar clave absoluta contra mapa relativo; audit_generator279-initial.py/EXIT1preservados. Se corrigió únicamente normalización de rutas dentro del árbol y se ejecutó de nuevo la auditoría conPASSsent, sin repetir carga ni cambiar fuentes congeladas.

Decisión: mantener277INVALID y su causa abierta. No hay hipótesis causal suficientemente respaldada para cambiar producto, GC,CPU oworkers. No repetir el diagnóstico hasta reproducir ni repetir carga limpia sólo para conseguirPASS. Conservar trazado explícito disponible para la próxima intervención pertinente. Avanzar el frente independiente de costePRODUCTION/checked de241, conprotocolo propio, datos sintéticos explícitos y equivalencia244 reutilizada en su ámbito. Ese frente no desbloquea por sí solo la aceptación HTTP combinada ni el cierreB07. No1000/10000/60s/900s automático para este escenario.
