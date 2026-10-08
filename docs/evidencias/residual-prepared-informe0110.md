# Intervención residual única — preparación del SELECT escalar

**Rechazada, no adoptada. CR09-REND-LECTURA aplazado por instrucción posterior del usuario hasta reanudación expresa.** Goal automático pausado; no cierre ni disminución de requisitos. Backend y recursos sin cambios; no cargas30/60/900.

[Perfil actual](residual-perfil0110.json), [diagnóstico de bindings](residual-bindings-diagnostico0110.json), [manifiesto previo](residual-prepared-tcp-manifiesto0110.json), [TCP/equivalencia/SHA/retirada](residual-prepared-tcp0110.json), [revisión aritmética independiente](residual-prepared-decision0110.json). Prototipo opt-in en tests, nunca activado en aplicación/runtime.

Operación: lectura escalar completa de10.000 candidatos, en listado y búsqueda (pesos contractuales1/3 cada uno). Fuente vigente sobreb285aba, captura/índice/presentación agrupada intactos. Perfil2pares plain/cProfile por fixture: controles623,025ms repetido/586,891ms diverso; observados723,065/922,180ms. Proyección actual10000positivos/0unknown, guard24 y motivo audited_current_values. No10.000Details/Contacts nativos en esta ruta. Eventos de construcción/compilación/lectura/hidratación/render anidados/lazy; no sumarlos ni atribuir total−SQL a validación. El texto genérico heredado del perfil menciona cuatro pares: la población real del ledger es dos, aquí corregida sin reinterpretar tiempos.

Hipótesis: reutilizar planificación real del SELECT actual mediante preparación en la sesión, sin reutilizar resultados ni elegibilidad. El diagnóstico baseline separado registró PlanningTime36,443–69,658ms según ruta/fixture. Sus ocho pares de lectura comparaban ClientCursor/ServerCursor **sin preparación real**: Django deja prepare_threshold=None incluso con prepare=True. Es evidencia válida de bindings, no de planes reutilizados. No inferir ahorro de execute o de su diferencia.

Cambio mínimo experimental: psycopg Cursor servidor, prepare=True y prepare_threshold=0 solamente durante la lectura, restaurado en finally; freshSQL/parámetros y snapshot original, mapeo de errores Django conservado. Ninguna plantilla SQL ni cambio de workers, recursos, conexiones persistentes60s, esquema o planificación en controles. Cache de planes del driver limitada100; no cache de resultados/autoridad. Se necesitaría revisar dependencias y guard al adoptar, pero esta candidata no se adopta.

Equivalencia comprobada: vectores completos ordenados de IDs/revisiones/bool iguales, revocación confirmada fuera de primera página, caducidad y restauración leídas de nuevo; excepción devuelve DjangoProgrammingError y restaura política. SQL/predicados no cambiaron: reutilizada equivalencia nativa previa en su alcance. Cuerpos/recuento10000/flags/ruta y motivo exactos porTCP. Dos fingerprints del iterador experimental se seleccionan solo en el servidor sintético, fuera de cálculo de peticiones; no relajar digest de producción ni presentar esto como nueva garantía general de huella.

Planes separados reales de sesión propia: ocho lecturas preparadas por familia,5custom/3generic antes deEXPLAIN forzado. Se registraron planes force_custom/force_generic e índices utilizados; esta etapa precedeANALYZE. Los controlesTCP posteriores usanANALYZE y modoauto normal, servidores nuevos. **No atribuir su regresión exclusivamente a esos planes o índices**; decisiones custom/generic de los workers en control not_measured. Ambos planes separados usan índices de joins; índices parciales unknown no aparecen en esa etapa. No afirmar que el flag de estrategia indexada acredita uso físico de índice. No se fuerza modo en controles ni se reabre la hipótesis con otra variante.

Primer preflightTCP terminó antes de muestras; import del soporte omitido y finally de media vacía enmascaró el assert de startup. Fuentes/retiro revisados, sin veredicto de efecto ni carga. Corregidos solo PYTHONPATH, conservación del log y manejo de población vacía; final completó ambosfixtures. El log privado del primer worker no se conservó al retirar el directorio: no se reconstruye literalmente su excepción. Los reintentos fueron correcciones del instrumento, no repeticiones de un efecto negativo.

Criterios prefijados vigentes: ambosfixtures, mediana del ahorro emparejado medio de4rutas≥max50ms/8%,≥6de8pares positivos, ninguna familia con regresión>max25ms/5%.4workerssync, máximo1requestpendiente,8AB/BA×4ESEN,64controles/fixture, sin profiler. Warmup50/26requests, ocho combinacionesPID/modo observadas. WSGI mínimo porID/entry/close, overhead causal not_measured; mismo instrumento ambos modos. Sesiones reales cambiaron en algunosworkers conCONN_MAX_AGE60: PID registrados, sin ocultar nueva preparación.

| Fixture | Ahorro HTTP emparejado mediano | Pares favorables | Decisión |
| --- | ---: | ---: | --- |
| Repetido |−82,704ms|1/8|Rechazar|
| Diverso |−20,553ms|4/8|Rechazar|

| Fixture/familia | Media WSGI A,ms | Media WSGI B,ms | A−B,ms |
| --- | ---: | ---: | ---: |
| Repetido/listado |597,589|645,841|−48,251|
| Repetido/búsqueda |621,955|752,355|−130,400|
| Diverso/listado |674,669|650,930|+23,739|
| Diverso/búsqueda |661,010|770,553|−109,543|

N=16por modo/familia (8ES+8EN). Aportes medidos: ΔD_lecturas=(Δlistado+Δbúsqueda)/3=−59,550ms repetido/−28,601ms diverso; ΔW20_lecturas=−1,191010/−0,572026worker-s/s. Signo negativo es empeoramiento. **ΔD total de mezcla not_measured**, fichas no muestreadas; uploads aparte/no medidos, sin atribuirles ahorro. No sustituir elD406,435ms de población saturada200/familia por estas medias seriales ni extrapolar capacidad desdeΔW. Wocupación noCPU.

Filas devueltas10000 medidas en fetchs escalares, no filas escaneadas globales/afectadas. CPU PostgreSQL, waits acumulados y desglose SQL/reglas/render en controles not_measured. Temporizador constructor+compilación del diagnóstico incluye lectura documental: no aisla construcciónPython/compilación. Sus planes EXPLAIN son separados y redactados.

Decisión revisada: **no conservar la preparación de este SELECT**; ninguna variante de planner ni otra intervención automática. Backend permanece con su iterador original. Dos casos finales PostgreSQL correctos no convierten el efecto enPASS ni acreditan capacidad. Revisión independiente verificó hashes, bases/media propios ausentes; masters esperados terminados y ocho PID finales ausentes. HistóricosFAIL corto/INVALIDcontractual, porcentajes y contrato10000/20RPS900s/mezcla/uploads/p95<800ms/errores<1% y todos los umbrales intactos.60/900bloqueados. Continuación ahora exclusivamente en pendientes independientes de contrato16§13, colaúnicadocs17.
