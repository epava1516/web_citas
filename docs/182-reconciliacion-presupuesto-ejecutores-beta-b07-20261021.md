# B07 — Reconciliación de presupuesto y selección de imagen

Estado: selector de imagen inmutable y preflight oficial8CPU auditados; calibración HTTPbeta en presupuesto cubierta después por183; volumen beta pendiente. B07abierto y8de18cerrados.

## Requisito y decisión

Contrato16MOD08 exige8CPU/8GiB/storage≤20GiB/swap0, cuotas CPU duplicadas proporcionalmente respecto del perfil4y controles kernel antes de carga. La calibración181del CIbeta observa grupos sin cuota finita explícita; no acredita ese perfil. Los controlesHTTP177conservan sus resultados válidos y límites declarados: no se reclasifican retroactivamente ni se usan como aceptación del perfil acotado.

Se consideró un diagnóstico grande sólo de recursos; no se lanzó tras contrastar el requisito kernel. El paso inmediato cambió a preflightoficialsin capacidad de perfiles. `run_vps_capacity`/`run_capacity_environment`/`check_capacity_environment` ya implementan topología acotada de entrega privada, distinta del arnés HTTPbeta. No se unifican por nombre ni se atribuye su PASSaotro escenario.

## Defecto del lanzador y corrección

Primer intento `20261021-181917-8114ded9`:INVALID_CONTROLLER_NO_REPORT, limpieza confirmada; el controlador no arrancó porque faltaba la etiqueta localweb-modelos-app:latest. La imagen actual por digest sí existe. No se crea/mueve etiqueta, descarga, construye imagen ni cambia servicios normales.

Los tres scripts aceptan ahora `--app-image sha256:HEX64`, propagado al controlador y a la aplicación. Overrides explícitos del wrapper VPS requieren digest completo; el parser interno conserva el valor legado web-modelos-app:latest por compatibilidad. Los otros nombres mutables/hash incompletos se rechazan. Imágenes existentes conpullnever; reparto de recursos y modalidades de trabajo intactos.

Focal `20261021-182033-3ef5c68a`:45PASS/0omisiones entre handoffVPSycontratopreflight, incluye5casos nuevos:2propagacionespreflight/measurey3rechazos. No aceptación de infraestructura desde dobles: el ensayo real es separado.

## Preflight real auditado

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 preflight ocho CPU imagen inmutable' -- .venv/bin/python scripts/run_vps_capacity.py preflight --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Run `20261021-182132-7113fda3`, entornoVPS `20261021-182132-5dbaa85b`:READY_NOT_CAPACITY/exit0. Un caso nativo depreflightPASS/0omisiones/70,438sJUnit. [Auditoría](evidencias/b07-pinned-capacity-preflight-20261021-audit.json) confirma controles kernel cpu.max/memory.max/swapmax0porrol, imagen exacta,45focales previos y mismas fuentes de ambos cortes,628app/config/templatesiguales, seis contenedores/volumen/red ausentes y Telegramterminal.

| Rol propio | CuotaCPU | TechoRAMMiB |
| --- | --- | --- |
| PostgreSQL |3,0|3072|
| Redis |0,2|384|
| App y sus procesos internos |3,5|3968|
| RustFS |1,0|512|
| Caddy |0,2|128|
| Controlador |0,1|128|
| Total |8,0|8192|

Swapmax0enlosseisgrupos, raícesreadonly y probeENOSPCporrol; controlador con RLIMIT_FSIZE y almacenamiento escribible acotado. Techo propio de almacenamiento4865392640bytes<20GiB. Cota conservadora de memoria del preflight1444810752bytes<6GiB: no pico sincronizado ni evidencia de memoria bajo carga beta. La misma imagen5a075sirve controlador/app y no se reetiqueta.

Auditorauxiliarinicial falló al exigir textoNoSuchparauna red que Docker declaraNotFound; versión preservada/ERRORnotificado. Auditorcorregido exige código fallido, nombre exacto y mensaje de ausencia correspondiente, PASSnotificado, sin repetir preflight. El primer fallo por etiqueta sigue conservado, sin simular reporte de controlador.

## Siguiente incremento técnico

Adaptar el recorrido HTTPbeta a la topología acotada como modo separado, antes de cualquier corto nuevo: mismo reparto/workerstopología, config/env/DB/broker/media propios, sin lanzar un CI anidado que cree servicios ilimitados. Primero sólo calibración funcional pequeña con órdenes/eventos nativos, subida persistida, identidad/contabilidad/geografía y worker/Beat. Registrar CPU/memoria/colas y fuentes desde ese entorno; mantener recorrido de objetos/caddy y límites contractuales del perfil si forman parte del presupuesto. No reasignar sus recursos al app para facilitar latencia.

Demostrar paridad de rutas y guardas, limpieza/kernel antes de medir; los 8CPUdelpreflightno aceptan8CPUdeunlanzadordiferente. Después prefijar mezcla/filtros/páginas/estados y decidir un diagnóstico grande, separado de controleslimpios. El FAILp95delcorto anterior sigue abierto;900sbloqueado. No carga beta grande ni entrega completa de expedientes por este preflight. Sin proveedores, personas reales, despliegue o aceptación beta.

## Continuación posterior183

La calibración funcional HTTPbeta en cuotas queda implementada y auditada en[183](183-calibracion-http-beta-entorno-acotado-20261021.md), sin CI anidado ni reasignación de recursos. La integración de volumen grande y su medición por ventana siguen pendientes; este preflight por sí solo no las acredita. Su alcance y memoria observada conservan la fecha/corte originales.
