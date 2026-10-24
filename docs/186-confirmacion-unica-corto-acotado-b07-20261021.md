# B07 — Confirmación única del corto acotado

Estado: confirmación única terminal auditada PASS numérico; B07 abierto, ocho de dieciocho puntos cerrados.

## Referencia y autorización técnica

El [contrato de ejecución](16-contrato-ejecucion-desarrollo.md), MOD-08, exige comparar sin perfiladores y repetir una vez sólo si cumple. El primer corto [184](184-corto-beta-cuotas-beat-20261021.md), run `20261021-191608-f5f21f49`, cumple los criterios numéricos bajo cuotas reales, según su [auditoría](evidencias/b07-bounded-short-pass-20261021-audit.json). Este documento fija esa única confirmación antes de lanzarla. No reabre el control histórico FAIL del perfil anterior ni altera su resultado.

Prerrequisitos: los artefactos originales fueron rehasheados, sus seis contenedores, volumen y red están ausentes y los avisos terminales constan enviados. El código de ejecución sigue idéntico. Las únicas diferencias en el mapa de fuentes del primer ensayo son seguimiento .ai y .graphifyignore; este registro no modifica código. El protocolo original184 fue recuperado byte a byte y validado contra su SHA preregistrado `a8bc822bd7beac90dcaf81b85b0d5979efc537107575160bb44cd828e6187f5b`. La recuperación posterior no se presenta como captura nueva anterior al ensayo.

## Condiciones congeladas

Mismo comando interno, imagen inmutable, reparto y generador: 8CPU/8GiB/swap0, almacenamiento máximo20GiB; PostgreSQL3CPU/3072MiB, Redis0,2CPU/384MiB, app3,5CPU/3968MiB, objetos1CPU/512MiB, Caddy0,2CPU/128MiB y controlador0,1CPU/128MiB. Verificación kernel antes de carga. Cuatro Gunicorn sync de un hilo y timeout60, Celery prefork2 y Beat. Nueva cohorte sintética propia de10000perfiles y2000derechos nativos; mismos servicios de autorización, ocho tablas ANALYZE y censo completo. No datos reales.

60segundos a20RPS,1200dinámicas por tercios listado/búsqueda/ficha y ES/EN alternando; una subida separada302 persistida. Mismas primeras lecturas frías, fase Beat objetivo+5s y preparación GC antes del reloj, sin congelarlo ni cambiar política. Mismos observadores declarados, sin perfiladores de solicitud. No calentamiento adicional, preparación compartida ni ejecución simultánea de otras baterías, builds o refrescos del grafo.

Criterios independientes para cada ensayo: p95 observable menor800ms, errores menores1%, generador p95≤10ms/p99≤25ms/máximo≤100ms,1200emitidas/0omitidas, contabilidad completa, pendientes de ventana≤20 y finales0, upload persistido, timeout65 y drain70. Conservar las demás guardas y límites del adaptador original. No agrupar percentiles ni compensar un fallo con el primer PASS. Fuentes, JUnit, ledgers, eventos, cuotas, recursos, salida de procesos, limpieza y recibo Telegram deben auditarse al terminal.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 confirmación única corto beta acotado' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-short --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Paso pytest limitado2400s y vida app3000s; estimación minutos/decenas, goal activo. Antes de lanzamiento guardar copia íntegra y SHA de este protocolo; congelar fuentes durante ejecución. No relanzar por pérdida de observación: comprobar el mismo proceso y sus artefactos.

## Regla de parada y alcance

Una sola confirmación. FAIL, INVALID, ERROR o timeout detienen esta secuencia; conservar evidencia y no iniciar un tercero ni900s. Un PASS permite preparar por separado un protocolo y modo beta900, sin lanzarlo automáticamente. El modo existente measure corresponde a entrega de expedientes, no sustituye beta900.

La etiqueta scope genérica heredada se conserva y declara como limitación de metadatos; el veredicto específico y los controles crudos son la evidencia pertinente. CPU total incluye preparación; cota de memoria no es pico simultáneo; los observadores tienen sobrecoste no aislado. Aplicación idéntica no acredita mejora causal. Un solo municipio no cubre diversidad territorial. Confirmación tampoco cierra B07: quedan mezclas, presupuestos y demás escenarios de la [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md). No aceptación global, N3, proveedor real ni producción.

## Confirmación terminal auditada

Run `20261021-195629-dccd5921`, entorno VPS `20261021-195629-2298d626`: BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL, salida0 y un caso PASS/0omisiones/889,696sJUnit. La [auditoría independiente](evidencias/b07-bounded-confirmation-pass-20261021-audit.json) recalcula criterios desde los ledgers y verifica fuentes congeladas, igualdad de recursos, imágenes y política respecto al primer ensayo. Cada ejecución pasa por separado; no se agrupan percentiles. El protocolo previo íntegro y su SHA `6f5a5ea3bf6ab5d72728f76f1c987a95feefac57c174cf5ee6c5cd18f835199c` permanecen en los artefactos ignorados, anteriores al lanzamiento.

1200IDs únicos/1200éxitos,0errores/omitidas/finales; cuatro pendientes al cierre de ventana. p95observable381,841ms; demoras generador p953,984ms/p997,831ms/máximo19,038ms. Mezcla400listado/400búsqueda/400ficha y600ES/600EN, una subida302persistida.10000publicaciones/2000derechos nativos,667Premium/1333Top; censo completo en un solo municipio. Primeras lecturas frías conservadas. Cuatro workers y nueve PIDruntime, raíces con salida0; tres publicaciones Beatrefresh y siete ejecuciones workerrefreshSUCCESS/noeager, sin equiparar sus cuentas. Inicio tick+5,126587s, GCsinfreeze/política intacta.

Kernel8CPU/8GiB/swap0; cota conservadora memoria1669165056bytes<6GiB y almacenamiento4865392640bytes<20GiB. Seis contenedores, volumen y red ausentes de nuevo; fuentes/ledgers/JUnit/cleanup y ambos avisos terminales Telegram confirmados.628app/config/templates siguen idénticos. La diferencia de p95 frente al primer432,620ms no prueba ganancia causal de aplicación.

La confirmación única queda agotada con PASS. No tercer corto ni900s ejecutados en este corte; se puede preparar el modo/protocolo beta900 por separado. Permanecen los escenarios y presupuestos pendientes de la matriz180, los FAIL históricos y las limitaciones scope/recursos/territorio ya declaradas. No aceptación B07, N3 o producción; ocho de dieciocho puntos cerrados.
