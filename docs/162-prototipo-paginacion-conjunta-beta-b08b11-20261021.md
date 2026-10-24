# B08–B11 — Prototipo aislado de paginación comercial por agregación

Estado: variante materializada con23PASS comunes y agrupación única verificada; unión repetida y plan original de permisos impiden pasar todavía a ROI. Ocho de18puntos cerrados; TCP contractual sigue FAIL.

## Mecanismo nuevo y límites

La implementación actual materializa derechos compatibles en Python y devuelve posiciones como JSON a PostgreSQL. Este prototipo agrupa derechos en una CTE materializada y selecciona sólo los24identificadores/prioridades de página. Conserva exactamente live_entitlements/person_queryset y su restricción por población: no amplía a derechos globales ni sustituye permisos por otra regla. No repite la autoridad enlazada156, JSON129 ni la consulta correlacionada por candidato. Sin caché persistente, cambios de producto, migraciones o proveedor.

Interfaz interna experimental: ordered/count/values_list/slice, exclusivamente los dos campos que consume state_page. count usa la población original. La selección SQL parametrizada conserva prioridad premium/top/orgánico, SHA256 del díaUTC y UUID textual, bump máximo sólo sin búsqueda, relevancia/publicación/UUID. Los empates de patrocinio quedan resueltos por digest+UUID antes de bump. Sin ventanas ni límites sobre derechos/candidatos antes de ordenar.

Sólo se enlaza temporalmente en tests/beta_set_pager_diagnostic.py mediante el hook de snapshot propio. Formas con DISTINCT, slice u orden desconocido vuelven al original. Transacción heredada conserva la implementación SQL original por sentencia, sin usar este hook. El producto no cambia. No atribuir autorización a un caller arbitrario de este helper experimental.

## Primer gate prefijado

Ocho casos PostgreSQL reales: páginas completas frente a referencia nativa congelada con derechos superpuestos, doce combinaciones de día/idioma/filtros; revocaciones de particular/propietario/editor; snapshot concurrente y petición siguiente; checked y refresh pendiente ES/EN; transacción heredada READ COMMITTED que prohíbe reutilizar el hook. Cada caso aplicable debe demostrar uso real del prototipo; el heredado debe demostrar ausencia. No basta un fallback verde.

Antes de ejecutar: Ruff, actualización dirigida del grafo y freeze. Runner funcional con4workers, datos sintéticos/recursos separados, sin otra integración simultánea; fuentes/cleanup/PIDs/Telegram auditados al terminar. Cualquier fallo se conserva y corrige en su alcance. No ejecutar medición de rendimiento paralela.

Este gate sólo demuestra paridad cubierta. Si pasa, ampliar casos de formas desconocidas/cero derechos/fechas límite y revisar SQL/planes antes de un contraste ROI predeclarado con cohorte20%promociones. Para adopción sigue siendo necesario beneficio en ambas rutas y estabilidad de controles, mismas fuentes/datos y presupuestos. No lanzar aún la carga contractual900s ni aceptar B07/B08/B11 por este prototipo.

## Primer resultado auditado

Runner20261021-133131-df70cdfc:8PASS/0FAIL/0SKIP,140,98spytest, sin warnings. [Auditoría](evidencias/b08-set-pager-20261021-133131-df70cdfc-audit.json):726fuentes runtime intactas, todas las fuentes congeladas iguales al terminal, contenedores/temporales/procesos propios retirados y Telegramterminal confirmado; auditoría terminal también enviada.

El caso de páginas verifica doce combinaciones completas de día/idioma/filtros y usa SetPager32veces sin fallback. Las tres revocaciones, snapshot concurrente y checkedESEN lo usan dos veces por caso; READ COMMITTED no entra en el hook. Los ocho casos están en un único archivo con loadfile:4trabajadores arrancados no significan cuatro casos simultáneos ni una medición de paralelismo.

Precisión sobre el test concurrente reutilizado: su propiedad histórica dice «after map read». En este prototipo no hay mapa; SHOW transaction_isolation ya establece el snapshot PostgreSQL antes de revocar desde la otra conexión, y la consulta diferida se ejecuta en ese mismo snapshot. La evidencia válida es primera respuesta patrocinada y siguiente respuesta sin patrocinio, con repeatable read observado en ambas; no afirmar una lectura anticipada de derechos que aquí no existe.

No hay modificación de producto ni mejora de velocidad acreditada, tampoco aceptación B07/B08/B11. Próximo gate: cero derechos, vencimiento y suspensión, formas desconocidas/fallback, y revisión del plan sobre población grande antes de contrastar coste. Conservar presupuestos y criterio en ambas rutas; ocho de18cerrados.

## Gate de bordes prefijado

Quince casos adicionales en beta_set_pager_edges.py: seis estados de derechos (ausente/futuro/inicioexacto/finexacto/suspendido/activo) por listadoES y búsquedaEN, más DISTINCT/orden desconocido/slice. Los doce casos HTTP comparan bytes/IDs/count contra implementación actual y patrocinio contra ranked nativo, y exigen uso real del prototipo. Los casos de forma no admitida conservan la conducta original: DISTINCT y orden desconocido mantienen orden exacto; slice conserva TypeError, no se añade soporte que el producto no tenía. Un worker, PostgreSQL real, freeze/limpieza/Telegram. Sin cambiar los ocho casos ya pasados ni declarar quincePASS antes del terminal.

## Resultado de bordes y siguiente diagnóstico prefijado

133917-9885702a:15PASS/0FAIL/0SKIP,143,31spytest sin warnings. [Auditoría](evidencias/b08-set-pager-edges-20261021-133917-9885702a-audit.json):doce combinaciones HTTP usan prototipo y coinciden con nativo/original; tres formas no admitidas conservan comportamiento.726runtimeintactos, ocho casos previos y sus fuentes de app/config/tests/scripts idénticos; fuentes congeladas, recursos/procesos retirados y Telegram terminal/auditoría confirmados.23casos únicos entre dos corridas, no una corrida23PASS. Sin adopción ni mejora medida.

Siguiente test beta_set_pager_plans.py:1000perfiles/200derechos emitidos por servicios sintéticos reales, unworker. Dos rutas (listado y búsqueda) dentro de snapshot propio RRreadonly; comparar exactamente los24pares UUID/prioridad, count1000 y guarda nativa. Capturar sólo tres SELECT por comparación: derechos originales, página original y páginaCTE. EXPLAIN ANALYZE BUFFERS TIMING OFF posterior verifica200/24/24filas raíz y conserva plan redactado. SQL/params/UUID no se envían a Telegram. Este diagnóstico pequeño precede al eventual ROI10000/2000 para evitar repetir montajes costosos sin revisar el mecanismo. No es medición limpia de latencia ni capacidad, y los nodos internos del plan no se suman como sujetos distintos.

## Primer plan: paridad correcta, mecanismo de agrupación insuficiente

134531-dd83848c:1PASS de integridad/0FAIL/0SKIP,126,58spytest sin warnings. [Auditoría](evidencias/b08-set-pager-plans-20261021-134531-dd83848c-audit.json):1000perfiles/200derechos,200filas raíz de derechos originales y24en ambas páginas, IDs/prioridades/count/guarda nativa iguales.726runtimeintactos, freeze/cleanup/PIDs/Telegram terminal y auditoría confirmados. Los identificadores directory_es/search_en del artefacto denominan los modos de población; es llamada directa a state_page, no una prueba HTTP ni una nueva comprobación de localización de HTML.

El plan de búsqueda contiene Aggregate con Actual Loops1000 y Actual Rows180 por ejecución, bajo Nested Loop de1000filas. CTE live se lee una vez (200filas), pero agruparla no queda materializado: se repite el trabajo de agrupación. En listado Aggregate200filas/1loop, aunque el join anidado también merece revisión. No sumar las filas de nodos anidados como personas distintas.

Tiempos observados EXPLAIN ANALYZE, sólo atribución: listado derechos2,125ms/páginaoriginal1,285ms/candidata16,109ms; búsqueda3,633ms/1,537ms/32,638ms. No son mediciones limpias HTTP, ni CPUbackend, ni un porcentaje de regresión causal. Sí contradicen la expectativa de una agrupación única en búsqueda. La variante inicial queda retenida como evidencia y no pasa todavía a ROI10000/2000.

Siguiente variante acotada, aún no implementada: rights AS MATERIALIZED además de live, sin cambiar selección de derechos/población/permisos/orden ni umbrales. Preservar código previo por hash. Volver a verificar los23casos funcionales tras cambiar SQL y repetir el plan1000/200 una vez para comprobar agrupación única y revisar el join. Sólo después decidir si justifica contraste ROI, manteniendo reducción10%ambasrutas, estabilidadA/A y no empeorar CPU según protocolo. No adoptar ni modificar producto por planes favorables. Ocho de18cerrados.

## Variante de agrupación materializada preparada

Cambio test-only de una cláusula: rights AS MATERIALIZED. Código inicial preservado en artifacts/beta-set-pager-20261021/initial-live-only.py, con SHA registrado; se conserva además el instrumento de plan anterior. No se cambian permisos, pertenencia, orden ni producto. Gate previo: ejecutar los23casos funcionales originales completos en dos archivos,4workers/loadfile; después el plan1000/200 en1worker, sin otra integración. Instrumento de plan añade requisito literal CTE rights con200filas y1loop; si falta o no se cumple, conservar negativo y no lanzar ROI. Aun cumpliéndose, revisar join/planes antes de decidir coste. No se mezclan tiempos funcionales con latencia y no se atribuye mejora a la corrección por mera lectura.

## Agrupación única confirmada; unión y autoridad aún costosas

135242-e5c69200:23PASS/0FAIL/0SKIP comunes en147,66spytest sin warnings. [Auditoría funcional](evidencias/b08-set-pager-materialized-20261021-135242-e5c69200-audit.json):delta del prototipo exactamente rights AS MATERIALIZED, doce combinaciones nativas/páginas, revocaciones, snapshot, doce bordes HTTP y tres formas preservadas.726runtimeintactos, fuentes/limpieza/PIDs/Telegram verificados.

135610-5bcb7ad5:1PASS de integridad del plan,130,91spytest sin warnings. [Auditoría de planes](evidencias/b08-set-pager-plans-20261021-135610-5bcb7ad5-audit.json):1000perfiles/200derechos, ambas páginas24pares idénticos. CTE rights produce200filas/1loop en ambas rutas; se cumple la corrección acotada. Ambas ejecuciones tienen exactamente las mismas huellas de fuente, runtime726intacto y limpieza/Telegram confirmados. No se presenta como una ejecución24PASS ni aceptación de rendimiento.

El plan conserva CTE Scan rights con200filas y1000loops en las dos rutas: materializar evita reagrupar, pero no evita la unión anidada repetida. Además, en búsqueda, el SELECT de derechos original ya parte de PublicationState estimado1fila frente1000reales. Su rama de permisos se reejecuta por cada fila exterior: Hash Join200filas/1000loops; acceso core_person por persona202000loops y subrama de permisos200000loops. Son ejecuciones de nodos, no sujetos distintos ni nuevas concesiones de autoridad. El prototipo conserva esa misma regla original dentro de live.

EXPLAIN ANALYZE observado, sin comparación causal entre corridas: listado originalderechos4,591ms/originalpágina1,543ms/candidata22,313ms; búsqueda1287,523ms/1,262ms/1400,706ms. La degradación del plan original también aparece aquí; no atribuirla al cambio de cláusula del prototipo. No se ha medido CPUbackend ni HTTP limpio. Sin cambios de parámetros de PostgreSQL, recursos, umbrales, reglas de permisos o producto.

Decisión: no iniciar todavía ROI10000/2000. La siguiente investigación debe separar la pertenencia exacta a la población de la evaluación de permisos sin permitir la reejecución de toda la rama por cada candidato. Conservar filtros completos, mismo snapshot propio y person_queryset original; no volver a derechos globales127 ni a permisos duplicados156. Necesita protocolo nuevo y evidencia de plan/paridad antes de implementación o adopción. La mera agrupación materializada queda como prototipo funcional, no optimización entregada. Ocho de18cerrados.

## Límite posterior de la atribución de permisos

El [contraste163](163-barrera-pertenencia-promocional-beta-b08-20261021.md) añade EXPLAINANALYZE DECLARE y no reproduce la repetición extraordinaria en una nueva muestra1000/200: originalSELECT y cursor muestran200loops en los nodos de agencia en ambas rutas. Por tanto, los loops200000 de162 describen aquel SELECT ordinario observado, no demuestran el cursor de la petición real ni una causa contractual. Diferencia de estado/plan entre corridas no aislada. La barreraOFFSET0 se descarta por compuertafalse; SetPager sigue sin adoptar.
