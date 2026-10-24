# B07 — Confirmación única del corto con cliente corregido

Estado: confirmación única terminada y auditada PASS acotado. B07 abierto; ocho de18 puntos cerrados.

## Requisito e incertidumbre

El [contrato16 MOD-08](16-contrato-ejecucion-desarrollo.md#mod-08--perfil-cpu-del-vps-autorizado-2026-10-12) exige comparar sin perfiladores y repetir una vez sólo si cumple. [193](193-corto-grande-retencion-cliente-b07-20261021.md) pasó tras corregir la retención de tareas terminadas del generador en191 y calibrar192. Su [auditoría](evidencias/b07-corrected-client-short-20261021-audit.json) verifica1200éxitos, p95515,045ms y máximo generador16,209ms. La incertidumbre es la repetibilidad de ese escenario con el instrumento corregido; no la velocidad causal del producto ni la diversidad territorial. Es la única confirmación de este corte, no una tercera repetición idéntica de184/186, cuyo cliente era distinto. Se conserva el INVALID900de189.

## Condiciones y límites congelados

Misma imagen inmutable5a075, mismo código de cliente/pruebas y628fuentes de producto. Nueva cohorte sintética nativa10000publicaciones/2000derechos(667Premium/1333Top), misma distribución de agencia, municipio y foto; autorización comercial real local, ocho tablas ANALYZE, rol PostgreSQL restringido. No datos reales ni proveedor externo.

Cuotas kernel idénticas a193: PG3CPU3072MiB, Redis0,2CPU384MiB, app3,5CPU3968MiB, objetos1CPU512MiB, Caddy0,2CPU128MiB y controlador0,1CPU128MiB; agregado8CPU8GiB/swap0, almacenamiento≤20GiB. Cota conservadora de memoria≤6GiB/PID≤1GiB. Cuatro Gunicorn sync/un hilo/timeout60, Celery prefork2 y Beat reales; mismas lecturas frías y fase objetivo tick+5s. GC sin congelar y política intacta; observadores existentes sin profiler de solicitudes ni calentamiento nuevo. CPU final incluye preparación.

60s20RPS/1200dinámicas:400listado/400búsqueda/400ficha,600ES/600EN. Un upload separado302persistido. p95 observable de todas las dinámicas terminadas incluidos errores/timeouts<800ms; errores<1% sobre1200; cero omitidas; demora generador p95≤10ms/p99≤25ms/máximo≤100ms; timeout65/drain70/elapsed≤130s; pendientes ventana≤20 y finales0, contabilidad reconciliada. Cada ensayo debe pasar solo; no agrupar percentiles ni compensar un fallo con193.

## Ejecución y parada

Antes de lanzar: rehashear evidencia193 y fuentes contra su mapa; verificar imagen, limpieza fresca, recibos y grafo; guardar este protocolo íntegro y SHA. Congelar fuentes/docs/.ai/grafo durante ejecución. No otras baterías/builds. Comando previsto:

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 confirmación única cliente corregido194' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-short --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Pytest2400s/app3000s, estimación15–20min con preparación. Lanzamiento persistente stdinDEVNULL/logdurable y handles propios. Aviso previo Telegram confirmado; pausar el mismo goal, guardar relevo y compactar. Vigilante sin llamadas al modelo verifica terminal/limpieza/recibo y reactiva este mismo goal preservando consumo. No relanzar por una observación perdida.

Una sola confirmación: FAIL/INVALID/ERROR/timeout detienen secuencia; conservar todo y diagnosticar, sin tercer corto ni900automático. PASS sólo permite preparar por separado el siguiente protocolo pertinente. Auditar JUnit/ledgers/fuentes/protocolo/roles/GC/Beat/kernel/recursos/limpieza fresca/Telegram antes de editar documentos. Resultado esperado de alcance acotado `BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL`, nunca aceptación B07 por sí solo. La [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md) mantiene territorio/filtros/páginas/estados/colas/recursos por ventana y PRODUCTIONchecked pendientes. Sin N3 global, proveedor real ni producción.

## Resultado auditado

Ejecución `20261021-214608-a48261b2`: `BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL`, salida0; un caso PASS/0FAIL/0ERROR/0SKIP,892,861sJUnit incluida preparación. La [auditoría independiente del ledger](evidencias/b07-corrected-client-confirmation-20261021-audit.json) recalculó1200éxitos/0errores/0omitidas/0pendientes finales; seis pendientes al cierre de ventana. p95 observable461,745ms; demora generador p953,456/p996,426/máximo15,335ms. Mezcla400porruta/600poridioma y upload302persistido verificados.

Censo10000publicaciones/2000derechos, cuatro workers/nueve procesos, tres publicaciones Beat y siete ejecuciones reales exitosas; comienzo tick+5,146s. GC intacto/sin congelar, cuotas8CPU8GiB/swap0, cota memoria1620942848bytes y almacenamiento4865392640bytes. Las628fuentes apps/config/templates y el mapa completo del ensayo permanecieron intactos; protocolo previo SHA256 `38f5ac24c9c202295b66860eaed2536313707ed3faa39d487b279c672952886e` contrastado antes de editar. Limpieza fresca y recibo terminal Telegram comprobados.

El vigilante registró `TERMINAL_NOTICE_CONFIRMED`; el disparador `RESUMED_AFTER_TERMINAL`, mismo thread/goal y consumo preservado. La solicitud de compactación quedó `REQUEST_ACKNOWLEDGED`. No hubo sondeos del modelo durante la espera pausada.

193 y194 pasan individualmente, sin agrupar percentiles. La única confirmación de este corte está consumida: no tercer corto ni900automático. Se conserva INVALID189. Un solo municipio sigue sin demostrar diversidad territorial, filtros profundos, estados, colas y recursos por ventana de matriz180. No se acredita mejora causal del producto ni aceptación B07/beta/producción.
