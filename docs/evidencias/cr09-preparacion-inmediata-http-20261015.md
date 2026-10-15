# Preparación inmediata: corto limpio

Run `20261015-194053-34109fbe`, SHA `3594311`: **FAIL184.81s**. Misma carga4sync/20rps60s/10k/worker2+Beat propios/una subida/generador congelado; sin perfiladores, observadores ni trackerPG. Fuentes y limpieza verificadas independientemente: raíz/pytest/Celery/temporal/PGRedis ausentes; unidad terminalfailed/MainPID0/ControlGroupvacío acredita también descendientes Gunicorn. [Recibo completo](cr09-preparacion-inmediata-http-terminal-20261015.json).

| Métrica | Anterior160640 | Actual194053 |
|---|---:|---:|
| p95completo(s) |1.3617929541505873|0.8977655060589314|
| p50completo(s) |0.2835297118872404|0.22488752426579595|
| Pendientesal60s |4|5|
| Completadasfinales |1200|1200|
| Errores/timeouts |0|0|
| ServicioGunicornp95(s) |0.31365|0.311439|
| Peticiones>=0.8s |248|71|

| Caso p95(s),200cada | Anterior | Actual |
|---|---:|---:|
| es:listing |1.391529|0.897766|
| en:listing |1.396969|0.893532|
| es:search |1.393086|0.998651|
| en:search |1.412857|0.948491|
| es:detail |1.271050|0.766312|
| en:detail |1.328369|0.858274|

Mejora observada34.075%, una sola comparación no causal ni reproducida. Generador válido1200emisiones,0omisiones/errores/timeouts/finalpending,subida302; checks pasan salvolatencia. No repetirFAILni avanzar15min/aceptarCR09/N3. Candidata retenida provisionalmente por evidencia funcional y mejora observada. ServicioGunicorn no incluyeesperaprevia.

## Localización desde las mismas muestras

| Emisión | N | p95(s) | >=0.8s |
|---|---:|---:|---:|
|0–5s|100|1.241490|71|
|5–10s|100|0.517203|0|
|10–15s|100|0.429199|0|
|15–60s|900|0.335939|0|

Todas71lentas emitidas primeros5s; máximo posterior0.661192s. Esto localiza el transitorio restante, no prueba causalidadSQL/GC/imports/upload ni capacidad completa sostenida. No excluirarranque/añadirwarmup/redefiniraceptación. Próximo diagnóstico separado: atribuir primeraspeticiones de procesos web reales, distinguiendoCPUapp/PG/cola/GC, antes de cambiar otra política. No barrido deworkers/umbrales/cargas.

Metadatos estáticos pg_server_shared/normalstack heredados conservados en resumen original; propiedad efectiva por exactrunname/label/adaptador acotado e inspección final. No acceso aPG/Redis normales.
