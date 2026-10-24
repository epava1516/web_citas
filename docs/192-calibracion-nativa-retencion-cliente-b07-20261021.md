# B07 — Calibración nativa tras liberar tareas cliente

Estado: calibración nativa terminal auditada PASS funcional; no capacidad. B07 abierto8/18.

## Motivo y fuentes

La [correctiva191](191-retencion-tareas-generador-b07-20261021.md) tiene11PASScliente y reproducción negativa preservada. Cambia únicamente scripts/benchmark_async_transport.py y sus pruebas respecto al terminal189;628fuentes apps/config/templates intactas. No cambia GC, políticas, autoridad, datos ni límites. La secuencia189 terminó INVALID y permanece detenida: esta nueva calibración es una validación afectada por la corrección, no una repetición900s ni una comparación causal de velocidad.

## Escenario y condiciones anteriores al resultado

Usar el modo existente beta-http-upload-calibration de188:10perfiles/2derechos nativos y15borradores propios sintéticos,15s20RPS/300dinámicas,100listado/100búsqueda/100ficha y150ES/150EN. Quince subidas adicionales a0..14s sobre15borradores distintos:302 y Photo+UploadAttemptaccepted/duplicate persistidos, no repeat. Sin datos reales ni proveedores. PostgreSQL17, Redis,4Gunicornsync1threadtimeout60, Celeryprefork2 y Beat reales con rol runtime restringido.

Misma imagen local inmutable5a075 y cuotas de188: total8CPU/8GiB/swap0/storage≤20GiB, límites kernel verificados. Mantener10/25/100msgenerador, cero omitidas/errores/finales,300éxitos y15uploads302; timeout65/drain70, lecturas frías, faseBeat+5s y GCsinfreeze/política intacta. Latencia descriptiva, no aceptación de capacidad. Paso300s; estimación2min. FAIL/INVALID/ERROR conservados y detienen secuencia; no repetición automática.

Antes de lanzar: verificar evidencia11PASS/recibo, fuentes correctiva,628producto y no capacidad activa; actualizar y sellar grafo dirigido AST/semántica, comprobar docs, archivar protocoloSHA. Congelar código/docs/.ai/grafo hasta terminal; no pruebas/builds paralelos. Recoger runID/handle persistente y no relanzar por timeout de observación.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración nativa liberación tareas' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-upload-calibration --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Al terminal reauditar ledgers/JUnit, políticaGC/roles/kernel/fuentes, fuentes192originales y limpieza fresca/recibo Telegram. Sólo BETA_HTTP_UPLOAD_CALIBRATION_NOT_CAPACITY con evidencia completa acepta este circuito pequeño. No cierra B07/B08–B11/B16 ni valida900s; un corto nuevo exigiría otro protocolo.

## Terminal y auditoría

Corrida `20261021-211615-4a33709f`, VPS `20261021-211615-34e76200`: BETA_HTTP_UPLOAD_CALIBRATION_NOT_CAPACITY, salida0,1PASS/0omisiones/104,116sJUnit. [Auditoría](evidencias/b07-task-release-native-calibration-20261021-audit.json) recalcula300éxitos/IDsúnicos/0erroresomitidosfinales, mezcla100/100/100 y150ES/150EN;15uploads302 en15borradores con Photo+accepted/duplicate. p95185,883ms descriptivo; generador p952,517/p994,718/máximo8,764ms, dentro10/25/100ms.

Cuatro workers/nuevePID, una publicaciónBeat unida a ejecución realSUCCESS y33refreshworker totales, sin confundirlos con33ticks. GCpolítica intacta/sinfreeze,628fuentesproducto intactas y fuentescliente coinciden con11casos previos. Kernel8CPU/8GiB/swap0, memoria conservadora1377386496bytes<6GiB/storage4865392640bytes<20GiB; procesos terminados, limpieza fresca y avisos Telegram prueba/auditoría confirmados. Protocolo192original archivado SHA `827609ed14aed42f57c1a55f055bed4be02169a34fdc617a2d83136e330186c2` antes de lanzamiento.

El tiempo del caso fue104,116s; arranque/colección del lanzador se añaden, no declarar104s como tiempo total. No hay comparación causal de latencia con188 ni garantía de evitar GCgeneración2 a10000perfiles/900s. El siguiente paso requiere nuevo corto con cohorte grande y protocolo previo; no iniciar900s directamente. B07 abierto8/18; negativo189 preservado.
