# B07 — Calibración de quince subidas

Estado:24focalesPASS y calibración real de quince subidas auditados; ningún900s lanzado. B07 abierto8de18.

## Propósito y aislamiento

El [modo contractual187](187-modo-beta-http-contractual-b07-20261021.md) exige quince borradores distintos para quince subidas; repetir sobre uno mediría la ruta repeat y no el trabajo previsto. Los dos cortos184/186cumplen por separado, sin extrapolar esos resultados al largo.

Nuevo modo beta-http-upload-calibration del lanzador: traduce a beta-http-functional más modificador exclusivo beta-http-upload-calibration. El modificador exige funcional y rechaza corto/contractual/preflight/perfiladores u otra carga. Conserva frontera verificada DB/broker/quota y cuatro Gunicornsync/workerprefork2/Beat. Resultado BETA_HTTP_UPLOAD_CALIBRATION_NOT_CAPACITY, nunca PASScontractual.

Cohorte propia10perfiles/2derechos nativos, censo y ocho tablas ANALYZE. Duración15s/20RPS/300dinámicas, seis rutas listado/búsqueda/ficha ESEN y quince uploads adicionales en t=0,1,…,14s. Quince borradores creados por ORM nativo, una foto persistida y un intento accepted/duplicate en cada uno; repeat no acredita esa persistencia. Payload sintético original782134, mismo multipart por borrador y controles normales de autoridad, limitación e ingestión. No bypass ni modificación de producto. Sin datos reales.

## Criterios previos

Exactamente300dinámicas emitidas y exitosas, cero omitidas/errores/pendientes finales y contabilidad reconciliada; generador válido con10/25/100ms de demora y timeout65/drain70 originales. Quince uploads emitidos y exitosos302, sin omisión/error/pendiente, quince rutas de borrador distintas y persistencia nativa por cada una. Lecturas frías, patrocinio, faseBeat+5s, GCsinfreeze/política intacta y tarea refresh real verificables. Latencia es descriptiva de calibración, no SLOgrande.

Misma imagen inmutable5a075 y cuotas agregadas8CPU/8GiB/swap0/storage≤20GiB; sin reasignación. Límite paso pytest300s para preparar cohorte pequeña, arrancar roles, esperarBeat,15s y desmontar; no criterio de latencia de producto. Guardar JUnit/ledgers/fuentes/kernel/recursos, salida de procesos, limpieza fresca y avisoTelegram. FAIL/INVALID/ERROR conservados e impiden largo hasta resolver causa; no relanzar por pérdida de observación.

Primero focal de exclusividad/handoff y checks estáticos, después calibración real sólo si cumplen. Refrescar AST/semántica antes del hito. No otras baterías/builds/grafo/cambios de fuentes durante ejecución. Comando prefijado:

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración quince subidas real' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-upload-calibration --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

El contractual conserva900s/18000dinámicas y quince subidas cada60s en quince borradores distintos. Esta calibración no cambia su espaciado ni sustituye la carga. Tras terminal auditado puede prepararse su protocolo definitivo; no lanzamiento900automático, aceptaciónB07/N3/producción ni proveedor real. Las mezclas territoriales/filtros/páginas/backlog y recursos pendientes conservan matriz180.

## Focal y calibración terminal auditados

Focal `20261021-202423-fb5123f2`:24PASS/0FAIL/0ERROR/0SKIP,0,483sJUnit para handoff y exclusividad. Prerrequisitos verifican fuentes, limpieza y aviso terminal enviado. Protocolo previo188 archivado íntegro antes del lanzamiento con SHA `3e95c46d34d018fee9726b9457311c60e8a857bb56e92a87e78a50eb29f8a4fb`; no se ajustaron criterios al resultado.

Calibración `20261021-202556-86e772e1`, entornoVPS `20261021-202555-96e2d23c`: BETA_HTTP_UPLOAD_CALIBRATION_NOT_CAPACITY, salida0,1PASS/0omisiones/104,788sJUnit. [Auditoría independiente](evidencias/b07-fifteen-upload-calibration-20261021-audit.json) recalcula300IDsúnicos/300éxitos/0errores/omitidas/finales;100listado/100búsqueda/100ficha,150ES/150EN. Quince subidas exitosas302/0erroresomitidasfinales, quince rutas de borrador distintas y planificación0..14s, una Photo y un intento accepted/duplicate por cada borrador; repeat no usado como prueba de persistencia. p95observable177,713ms descriptivo; demorasgenerador p952,721ms/p996,047ms/máximo10,168ms cumplen10/25/100ms.

Diez perfiles y dos derechos nativos, censo completo, lecturas frías y patrocinio verificados. Cuatro workers/nuevePIDruntime/raícesexit0, una publicaciónBeatrefresh unida a ejecución realSUCCESSnoeager;33ejecucionesrefreshtotales, no33ticksBeat. GCsinfreeze/política intacta, topología8CPU/8GiB/swap0 kernel, memoria conservadora1378381824bytes<6GiB y storage4865392640bytes<20GiB. Fuentes focal y runtime idénticas,628app/config/templates intactos, seis contenedores/volumen/red ausentes de nuevo y Telegram terminal de prueba y auditoría enviados.

Esta evidencia valida el circuito de quince ingestiones a escala pequeña y temporización abreviada. No acredita quince minutos ni10000perfiles; el largo conserva900s/18000dinámicas/subidas0,60,…,840s y requiere protocolo definitivo separado antes de lanzamiento. B07abierto8de18; pendientes de matriz180 y limitaciones de recursos, instrumentación y territorio conservados.
