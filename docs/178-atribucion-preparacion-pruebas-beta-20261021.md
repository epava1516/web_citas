# Atribución del coste de preparación de pruebas

Estado: diagnóstico terminal auditado; un casoPASS, sin optimización aplicada. B07abierto y8de18cerrados.

Tras el FAILlimpio[177](177-control-limpio-tras-diagnostico-sync-beta-b07-20261021.md), no se repite capacidad. La preparación grande ha consumido unos825s en[164](164-atribucion-actual-peticion-promocional-beta-b07b09-20261021.md), sin atribución detallada. Se mide un conjunto menor de1000perfiles/200derechos para localizar costes; no extrapolar tiempos lineales ni declarar aceleración.

Instrumento explícito `tests/beta_preparation_cost_diagnostic.py`, fuera de colección ordinaria: cProfile de preparación nativa y refresco final; spans de populate/create_order/synthetic_event/receive_event/refresh_all con reloj y CPU del hilo; contador/tiempo executeSQLsin guardar consultas, parámetros, filas ni sujetos. Las llamadas originales mantienen argumentos/resultados/excepciones, sin nuevas transacciones ni cambio de política. cProfile registra tiempo transcurrido, no CPU; acumulados inclusivos se solapan y SQLexecute no incluye fetch. Sobrecoste del observador no medido.

ComprobarPostgreSQLpropio, brokeraislado, noPRODUCTION/RECOVERY, autocommit,200órdenes sintéticaspaid/200derechos,1000publicaciones y estado limpio/vigente. Fallos y omisiones se conservan. No datos reales, proveedores, servicios omitidos, fixtures reducidas en capacidad ni cambio de aplicación.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/beta_preparation_cost_diagnostic.py --workers 1 --fixture-snapshots --isolate-test-broker --timeout 900
```

El resultado orientará una propuesta equivalente y su comparación posterior; este diagnóstico no acredita optimización, concurrencia, HTTP ni aceptaciónB07. No otra batería simultánea. AvisosTelegramdeinicioyterminalobligatorios.

## Resultado y límites

Corrida `20261021-172914-78f1a9e5`:1PASS/0FAIL/0ERROR/0SKIP,166,253sJUnit. [Auditoría](evidencias/test-preparation-cost-20261021-audit.json) concilia propiedadesJUnit/artefacto, huellas, contenedores/temporal/PIDretirados y Telegramenviado. Negativo inicial `20261021-172843-e923faed` detenido por importaciónsinusoantesdepytest, conservado y corregido; cero casos en ese intento.

Preparación instrumentada129,121s: populate4,352s; create_order200llamadas56,658s/14600executeSQL; receive_event200llamadas56,428s/15200executeSQL; firma sintética0,040s; refresh_all3,412s. Creación/recepción de derechos suman113,087s,87,58%del tiempo instrumentado.31107executeSQLen total; no sumar tiempoSQLa spans que ya lo incluyen. El resto incluye bootstrap, selección y guardado del comprador; no está atribuido por completo. `other_preparation` sólo cuentaSQLfuera de spans, sus relojes0no representan coste0.

cProfilelocaliza800llamadasauthorize/96,722sinclusivos y804publicly_visible/86,175sinclusivos; esas cifras se solapan, no se suman. Psycopgwait41,218sexclusivosnoequivaleCPUdel servidor ni demuestraSQLconcretolento. Modelo de1000/200no acredita escalado10000/2000 ni aceleración real.

La lectura de `apps/core/verification.py::locked_manager_person` confirma bloqueoAgencyselect_for_update dentro de cada transacción de create_order/receive_event. La cohorte comparte agencia; añadir hilos a esta preparación encontraría esa serialización. No se ha medido contención ni paralelismo: no se adopta esa propuesta ni se cambia la distribución del conjunto para evitar el bloqueo. Las validaciones de autoridad/publicación al inicio/final son comprobaciones vigentes; no se omiten ni se cachean entre operaciones para acelerar tests.

Conclusión operativa: la prioridad está en el coste repetido del recorrido comercial nativo, no en bulk_create de perfiles. Próxima investigación acotada: distinguir consultas y construcción de las validaciones antes de diseñar un cambio equivalente. No nueva carga60s/900s, cambios de producto o aceptaciónB07 por este diagnóstico.

## Atribución por ubicación de consulta

Segundo diagnóstico explícito `test_native_authorization_query_attribution`, corrida `20261021-173700-f33a515d`:1PASS/0omisiones con10perfiles/2derechos nativos. [Auditoría de consultas](evidencias/test-preparation-authorization-queries-20261021-audit.json) verifica146executepara2create_order y152para2receive_event:73/76poroperación, iguales al cociente de la cohorte1000/200. No extrapola latencia ni rendimiento. Las pilas sólo retienen ubicaciones de código y hash del textoSQL, nuncaSQL/parámetros/filas; sobrecoste de captura no medido. Llamadas/propiedadesJUnit/huellas/cleanup/PIDs/Telegram conciliados.

Las ocho validaciones públicas del recorrido pequeño consultan, entre otros, preparaciónprivada/historial/reintroducción, restricciones, teléfono/agencia, documento/aceptación/grant, edad, ubicación, formulario, contrato de perfil, fotos y conflictos. DetailsForm.is_valid genera32executeen ocho llamadas; actor12 y la mayoría de guardas8cada una. Estos recuentos incluyen lecturas de relaciones diferidas y comprobaciones distintas; repetición no equivale a redundancia eliminable. No se han medido tiempos porconsulta sin observador ni planes concretos en este diagnóstico.

Se conserva autorización fresca antes/después de mutaciones, bloqueoAgency/Person/Listing y semántica nativa del formulario que debe observar cambios de catálogo durante su inicialización. No se adopta un contexto o resultado compartido entre operaciones. La preparación es cara por el recorrido comercial completo, y su paralelización dentro de la misma agencia no se justifica por esta evidencia. Producto intacto; B07continúaabierto8/18. Una propuesta futura deberá identificar una operación sustituible equivalente y demostrar ahorro frente a esta referencia, sin reactivar automáticamente variantes ya rechazadas.
