# Cola verificable CR09 y continuación del contrato

Estado: abierto. No se modifica el objetivo CR09→CR10→GS01→BF/BB→C,
los pesos, límites ni la aceptación provisional MOD-09.

| Pendiente | Evidencia de salida | Acción siguiente |
|---|---|---|
| Regresión común integrada | Cuatro particiones conciliadas sobre fuentes integradas, terminal y limpieza independiente | Actualización 2026-10-15: misma versión `8fb4cf1`. Bloque 1: 849 PASS/9 SKIP; bloque 2: 728 PASS sin omisiones; ambos terminales y limpieza independiente. Bloque 3 conserva 826 PASS/23 errores de preparación/6 SKIP; recuperación afectada 61 PASS, todos los 23 errores cubiertos, 849 PASS únicos tras descontar 38 duplicados, con limpieza independiente. Bloque 4 `20261015-081053-9720829d` terminal: 870 PASS/1 FAIL/3 SKIP. Fallo conservado; diagnóstico original ES/EN 2 PASS y espera explícita de navegación 2 PASS, con limpieza independiente. Sólo cambia el archivo de test, confirmado por huellas. Falta conciliación contractual/N3, sin aceptación |
| Caché de fixtures | Tres controles opt-in PostgreSQL ejecutados sin SKIP, preservación/aislamiento/limpieza | Recibo histórico `cr09-broker-snapshots-terminal-20261014.json`: selección broker/snapshot 30 PASS, cero SKIP, fuentes intactas y limpieza independiente. El test permanece igual, pero `tests/directory_snapshot.py` cambió desde ese recibo; selección incluida en plan v3. Conciliar su terminal integrado antes de pedir otra ejecución |
| Recursos históricos | Censo finito por escenario; asociación/divulgación autorizadas y pendientes necesarios resueltos | Cuatro recorridos aislados perfil/cuenta ES/EN PASS en candidato `287ea23`, integrado como `34edf14`/`95afc89`. Metadatos autenticados de los23originales recuperados y decisiones por fuente de cada escenario ligadas/verificadas contra registro previo, sembrado, montajes e inputs sin importaciones/snapshots (`cr09-historicos-escenarios-revisiones-20261015.json`). Resuelve trazabilidad de pertinencia en esos cuatro escenarios; negativa conjunta/archivos privados anteriores y asociación general fuera de ellos siguen pendientes. No clasificación por diferenteID ni N3 |
| Cobertura contractual | Cada fila de docs83 ligada a aserciones y reports pertinentes, incluyendo negativos y límites | Completar matriz parcial; restauración, urgencias y comunicaciones ya inspeccionadas |
| Conservación/worker | Correspondencia de tareas, scheduler y finalidades con evidencia actual/histórica aplicable | Selector integrado Beat→worker PASS, `20261015-024215-b7fd60c2`, fuentes intactas y limpieza independiente; recibo `cr09-worker-beat-integrado-terminal-20261015.json`. Alcance específico, sin aceptación de capacidad |
| N3 común | Versión integrada común, conjunto, carga/recuperación pertinentes, resultado terminal sin omisiones necesarias | Reconciliar selección/exclusiones, sin sumar versiones distintas como gate |

Después de CR09: los siete criterios de contrato11 para CR10 incluyen catálogo
incompleto no vendible, pedidos propios particular/agencia, evento sintético
válido una sola concesión, patrocinio/filtros/rotación, suspensión de exposición,
correspondencia de datos con derechos/restauración y Docker/gate común.
Adaptador real de pago fuera de v1. No aceptar CR10 por contar tests comerciales.

GS01 mantiene GS-S01 matriz común, GS-S02 asíncrono/lote/ESEN y GS-S03 fuentes/
comunicaciones/CR10. BF requiere recorridos visuales/responsive/accesibilidad y
recursos/metadatos; BB mantiene autoridad/tareas/retención/recuperación y deuda
justificada. C exige integración final y preparación de producción separada.
No se ejecutan cargas simultáneas ni se desplaza deuda pesada provisionalmente
aceptada para convertirla en nuevo bloqueo de GS01.

Actualización documental 2026-10-15: esta tabla sustituye los estados activos antiguos de esas filas, conserva los recibos históricos y no acepta CR09/N3. Véanse [plan v3](cr09-regresion-version-comun-plan-v3-20261015.json), [censo y límites](cr09-censo-completo-alcance-validacion-20261015.json) y [conciliación de omisiones](cr09-omisiones-conciliacion-alcance-20261015.json).
