# B07 — Diagnóstico de límites del transporte

Estado: diagnóstico terminal auditado, FAIL válido de latencia y pendientes. Ocho de18cerrados;900s bloqueado.

171localiza residual cliente−servicio grande en las tres rutas y en seis ventanas;172calibra integridad de marcas cliente conTCP real pequeño. Falta localizar si el tiempo se concentra antes de conectar, entre envío y línea de estado o durante lectura. Una nueva ejecución está justificada por esta medición ausente, no por repetir el mismo candidato hastaPASS.

Usar mismo short de169:10000perfiles/2000derechos,20RPS60s/1200dinámicas ESEN por tercios,1subida,4Gunicornsync1hilo, PostgreSQL17/Redis propios y worker/Beat reales. Preparación finaliza estadísticas8tablas. Añadir sólo --benchmark-client-phases al comando169, con --workers1 --fixture-snapshots --isolate-test-broker --benchmark-normal-refresh --benchmark-beta-promotions --timeout2400. Sin observadores backend, wrappers, SQLtimers, muestreo, cuotas nuevas o eliminación de primeraslecturas frías.

Mismos objetivos y contabilidad: p95cliente<800ms,errores<1%,demorasgenerador10/25/100ms,ceroomitidas/finalespendientes,ventana≤20,timeout65/drain70. No convertir métricas de servicio o etapas en criterio de aceptación alternativo. SeaPASS/FAIL/INVALID, conservar resultado completo; una ejecución instrumentada no habilita900s: diagnostic_continue_contract debe serFalse. No prueba ahorro causal ni overhead del instrumento.

Auditar1200IDscliente/servicio y1201capturas:1200dinámicas+1subida; cada cuerpo completado debe tener siete marcas ordenadas y terminal dentro de latencia del ledger. Timeout conserva sólo etapas alcanzadas, sin inventar tiempos ausentes. Clasificar rutas exactamente porquery?q= y/listing/. Describir por ruta y ventana los deltas connect,drain→statusline,headers→body, junto con servicio y residual pareado. No llamar primerbyte a statusline ni espera socket exacta a una resta. Si faltan marcas, conservar diagnóstico incompleto, no forzar PASS ni relanzar automáticamente.

Congelar fuentes/docs/.ai/grafo desde lanzamiento hasta terminal/retirada/aviso y auditoría fresca. Validar las628fuentes aplicación iguales, dos herramientas modificadas explícitas del mapa726, AST del emisor intacto, negativas históricas y rama de exclusión de continuación contractual. Runner verifica calidad/documentación/migraciones antes del escenario. Preparación estimada en minutos/decenasdeminutos, no horas: goal activo. Sin proveedores, datos reales, publicación o cambio del contrato.

## Resultado terminal auditado

160253-3c5305fe: un casoFAIL/0SKIP. [Auditoría](evidencias/b07-client-phases-short-tcp-20261021-160253-3c5305fe-audit.json):1200dinámicas correctas/ceroerrores/omitidas/pendientesfinales,1subida302persistida; p95observable1359,675ms>800ms y25pendientesventana>20. Generador,drain ysubida cumplen. Son1201capturas completas/monótonas, sin ausencias. Rama instrumentada comprobada: client_phase_diagnostic_onlyTrue y diagnostic_continue_contractFalse. No900s.

| Ruta | p95conexión | p95drain→líneaestado | p95cabeceras→cuerpo |
| --- | ---: | ---: | ---: |
| Listado |0,758ms|1378,605ms|0,158ms|
| Búsqueda |0,875ms|1363,062ms|0,164ms|
| Ficha |0,784ms|1218,587ms|0,126ms|

Los percentiles pertenecen a etapas distintas y no son sumables. El tramo dominante observado está después del envío local y antes de la línea de estado; no en establecer conexión TCP o leer el cuerpo. Drain no prueba recepción remota y línea de estado no es primerbyte. Aún no se localizan exactamente admisión/socket/parseo/espera del worker.

[Conciliación con servicio](evidencias/b07-client-phases-latency-decomposition-20261021.json): p95servicioGunicorn355,314ms, ninguna de1200conservicio≥800ms;1167cliente≥800ms. Residual pareado cliente−servicio:mediana969,854ms/p951125,509ms, no cola exacta ni CPU. Las seis ventanas de emisión siguen afectadas. No restar percentiles ni atribuir la diferencia frente169al instrumento: overhead causal no medido, host/cachés/tiempo no aislados.

Fuentes congeladas,628app/config/templates iguales,724de726mapaimageniguales y dos herramientasCI modificadas declaradas; procesos anidados/servidores/worker/Beat/PostgreSQL/Redis/temporales retirados, reciboTelegramterminal y auditoría enviados. Los FAIL anteriores se conservan.

Siguiente decisión: distinguir admisión y parseo en servidor mediante límites mínimos calibrados, o seleccionar una corrección con coste demostrado. No repetir la misma carga sin un mecanismo nuevo que aporte esa evidencia, ni aumentar workers/recursos o relajar criterios por esta correlación. B07 sigue abierto.
