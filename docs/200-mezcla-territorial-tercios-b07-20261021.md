# B07 — Mezcla territorial alineada con tercios contractuales

Estado: guardas unitarias y calibración TCP local auditadas PASS. B07 abierto8/18.

La calibración [200](199-calibracion-tcp-territorial-b07-20261021.md) fue válida para el alcance declarado6/14listado+6/14búsqueda+2/14ficha; no era mezcla contractual de tercios. Su PASS se conserva sin reclasificar. Antes de carga grande se corrige sólo el ciclo territorial: mantener bloque base de seis y añadir por ciudad/página paresESEN de listado/búsqueda/ficha, repitiendo las dos fichas como slots declarados. No crear identidades extra ni eliminar rutas. Misma preparación70/30, productos, orden, generador, GC y criterios.

B07-201 alinea ciclo territorial con tercios contractuales: bloques6alternandoESEN, ficha repetida como slot explícito;18slots/14rutas únicas a10 y42slots/30únicas a1000/10000.21guardasPASS; calibración nativa del nuevo ciclo pendiente. Mantiene bloqueo short/measured y8de18.

A1200llegadas se exigen400listado/400búsqueda/400ficha y600poridioma. A18000,6000porcategoría/9000poridioma; nueve combinaciones de población y longitud verificadas con contabilidad independiente por URL, más negativas del plan y guardas previas:21PASS en total. Las guardas no ejecutan TCP, no autorizan900 ni capacidad. Cobertura grande funcional199 reutilizada únicamente en su alcance; la mezcla cambia fuentes del harness y requiere calibración propia.

## Protocolo previo de calibración

Una sola calibración oficial functional con --benchmark-territorial:10perfiles7/3/2derechos/18slots14rutas únicas,18sondas200,60dinámicas20porcategoría30poridioma y1upload302persistido. Exigir1PASS sin omisiones, ledger igual al ciclo, cero omitidas/finales,628producto intactas/mapas congelados/limpieza fresca y Telegram confirmado. El runner sigue rechazando short/measured. Si ERROR/FAIL, conservar y detener, corregir antes de nuevo corte. No cambiar umbrales ni extrapolarp95.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test 'tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[functional]' --workers 1 --fixture-snapshots --isolate-test-broker --benchmark-normal-refresh --benchmark-beta-promotions --benchmark-territorial --timeout 300
```

Congelar fuentes/protocolo tras grafo dirigido actualizado; almacenar SHA y mapa antes de lanzamiento. Sin900 ni corto grande automáticos. Pendientes de matriz180 incluyen recursos por ventana/estados/backlog/PRODUCTIONchecked.

## Resultado nativo local

B07-201 calibración TCP del ciclo equilibrado auditada1PASS/87,098sJUnit:60éxitos20listado20búsqueda20ficha/30ES30EN,18slots14rutas/18sondas200 y1upload persistido;10perfiles7/3.628producto/fuentes/limpieza/Telegram verificados. No entorno kernel ni carga grande ni cierreB07;8de18. Run20261021-235209-352ad338. [Auditoría](evidencias/b07-territory201-balanced-tcp-20261021-audit.json). Misma secuencia declarada en manifiesto y ledger; protocolo previo y mapas iguales comprobados antes de editar. El entorno kernel usa tests/test_capacity_beta_http.py, distinto del harness local; necesita adaptación explícita y calibración propia, sin trasladar esta evidencia a sus cuotas.
