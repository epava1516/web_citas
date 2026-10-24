# B07 — Integración del plan mixto escalable

B07-246 auditado: 2 PASS en PostgreSQL real, 100/1000 perfiles, rollback contrafactual y 44 páginas verificadas; fuentes y limpieza confirmadas. Compactación aceptada y mismo objetivo reactivado por la shell. Sin capacidad acreditada; 8 de 18, B07 abierto.

## Cambio y criterio

El control 245 acredita equivalencia funcional mixta a 100/1000, pero no ejecuta el plan contrafactual que prepara las referencias antes de la ventana de Beat. Ese plan y los adaptadores HTTP fijaban 100 perfiles, 20 derechos, 86 visibles y 11 patrocinios. Se parametrizan para 100/1000, conservando siete causas duplicadas orgánico/promocionado, 14 exclusiones, dos derechos inactivos sin ocultar perfiles y protección de los dos detalles usados por carga.

No se habilita 10000. Se conservan la separación funcional frente a capacidad, PostgreSQL propio, simuladores explícitos, no producción, no recuperación, no reparación por GET, recursos de 8 CPU/8 GiB y límites de 45 s de reparación y del generador. Las 43 pruebas de handoff pasaron en 8,82 s; Ruff pasó en los siete archivos afectados. Son guardas, no integración ejecutada.

## Prerregistro del control 246

Ejecutar únicamente test_counterfactual_mixed_plan_rolls_back_then_matches_actual_pages[100] y [1000] en tests/test_mixed_state_plan.py. Primero regresión 100, luego 1000. PostgreSQL17/Redis7.4 reales, native-build, runner focused serial, snapshots y broker aislado; timeout3600. No TCP ni carga HTTP concurrente: cliente Django local.

Exigir rollback de campos nativos y derechos, ausencia de marcas tras rollback, secuencia monotónica sin setval, generaciones reales posteriores, cuatro censos completos nativos y 14 marcas tras aplicar. Población 100/1000, distribución 70/30, derechos 20/200, visibles 86/986 y patrocinios activos 11/191. En 100 recorrer todas las páginas posteriores (20); en 1000 seleccionar primera/intermedia/última (24), ES/EN y texto vacío/photography, con IDs, orden, recuento y etiquetas exactos. Comprobar 28 detalles404, visibilidad de perfiles con derechos inactivos y marcas/generaciones intactas por GET.

Congelar fuentes completas y este protocolo por bytes/SHA después del grafo266. Auditar JUnit, propiedades, fuentes, producto628, limpieza real y Telegram antes de editar. Si falla, conservar negativo antes de corregir. Resultado PASS sólo habilita preparar el HTTP mixto1000; no acredita worker, capacidad ni beta. No lanzar10000 ni900s automáticamente.

Persistir prueba, watcher, callback y compactor. Confirmar Telegram de inicio y prepausa, guardar relevo y verificar PID/start_ticks antes de pausar. La shell solicita compactación durante espera y reactiva el mismo goal al terminar con su consumo conservado; ningún sondeo del modelo pausado.


## Resultado auditado del control 246

Ejecución `20261022-141230-c15fcc1e`: dos casos PASS, sin fallos, errores ni omitidos; 561,583 s sumados de casos. Para 100/1000 perfiles: 20/200 derechos, 86/986 visibles, 11/191 patrocinios activos, cuatro censos nativos completos y 20/24 páginas comprobadas. Cada caso acredita rollback lógico, secuencia monotónica sin reinicio, 14 generaciones posteriores y 28 detalles excluidos con 404; los GET conservan las marcas. La selección de páginas de 1000 no equivale a recorrerlas todas.

Auditoría `mixed246-audit.json`: las 1699 fuentes congeladas coinciden con lanzamiento, CI y estado posterior; protocolo original preservado por bytes y SHA, 628 fuentes de producto intactas, PostgreSQL17/Redis7.4, native-build y pasos correctos. Limpieza contrastada con Docker, temporal y procesos; recibos Telegram confirmados, compactación aceptada y reactivación del mismo objetivo conservando consumo. No se ejecutó carga TCP ni worker en esta integración y no acredita capacidad.

El siguiente trabajo es preparar y prerregistrar HTTP mixto a 1000 con imagen e instrumento verificados. No habilita 10000 ni una prueba contractual de 900 s automáticamente. B07 sigue abierto y el balance permanece en 8 de 18.
