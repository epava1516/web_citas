# B07–B09 — Autoridad comercial sobre la persona enlazada

Estado: paridad PASS y contraste de coste rechazado; consulta de producto original conservada. B13 conserva pendiente el ensayo de retorno; la imagen66c6d381 compatible con HMAC queda como base de retorno para un cambio posterior real.

El perfil115651 de10000perfiles/2000derechos observa selección comercial80–127ms inclusivos; los planes muestran un recorrido adicional de core_person dentro de la comprobación de gestión. No atribuirle todo ese tiempo ni convertir lecturas del plan en CPU. Se contrasta una forma SQL distinta: persona enlazada al pedido, comprador activo/no borrado, manager_version, persona no borrada y propietario/particular/editor asignado con membresía activa mediante EXISTS. Conservar restricciones temporales, suspensión, orden sintética pagada y población filtrada; no volver al experimento de derechos globales ni cambiar iterator500.

La candidata existe sólo en tests/beta_commercial_authority_diagnostic.py. Su condición de autoridad es experimental y no se adopta como copia independiente de person_queryset. Una eventual integración deberá compartir una definición verificada de permisos con person_queryset, revisar sus consumidores y probar equivalencia antes de aceptar. No introducir una segunda autoridad permanente para conseguir rendimiento.

Primera ejecución prefijada: ocho casos PostgreSQL, un worker, broker/medios propios. Todas las páginas con derechos solapados contra referencia nativa congelada; revocación particular/propietario/editor; frontera entre snapshots; checked pendiente ES/EN; transacción READ COMMITTED heredada. Cada llamada candidata compara además los IDs completos, ordenados y sin deduplicación, con live_entitlements original en la misma transacción. Esto añade lecturas deliberadas: sus tiempos no son un ROI ni carga limpia. Todos los casos deben acreditar al menos una comparación real.

Sólo después de PASS de paridad se obtendrán planes nuevos y un contraste limpio balanceado de coste sobre fuentes únicas, con umbrales prefijados y CPU/memoria. No hay autorización de adopción por ocho PASS. Mantener cortoTCP112359 FAIL y900s bloqueado; no elevar recursos, cambiar SLO, omitir guardas o afirmar proveedor real.

Conservar negativos, freeze, limpieza propia y Telegram terminal; actualizar esta entrada con el resultado real. El objetivo íntegro B00–B17 sigue abierto, siete puntos cerrados de18.

## Paridad verificada

073316-ee4f9a5a:8PASS/0FAIL/0ERROR/0SKIP y sin advertencias;65comparaciones de IDs completos entre original y candidata. Todas las páginas de referencia, tres revocaciones, frontera de snapshots, checked ES/EN y transacción heredada pasan. [Auditoría](evidencias/b08-joined-authority-parity-20261021.json): fuentes congeladas/fresh,726fuentes runtime iguales a la candidata Docker HMAC, PostgreSQL/Redis/temporales/PIDs propios ausentes y Telegram terminal confirmado. No se acredita equivalencia exhaustiva de todas las combinaciones de gestión ni coste por esta batería.

## Contraste de coste prefijado, aún no ejecutado

Usar la misma fixture10000perfiles/2000derechos sintéticos y dos rutas listadoES/búsquedaEN de111. C sustituye exclusivamente live_entitlements en una copia del helper comercial; A/B llaman al original. Eliminar el cotejo adicional de IDs del instrumento de paridad durante los controles, manteniendo la comparación de bytes, IDs ordenados, recuento y patrocinio por respuesta. Conservar iterator500, lectura filtrada de población, orden, guardas, configuración, GC, recursos y base de datos. Ningún profiler, observador SQL o tracemalloc dentro de los controles.

Seis permutaciones ABC/ACB/BAC/BCA/CAB/CBA por ruta, backend propio nuevo por brazo, un calentamiento y tres controles:36calentamientos/108controles. Registrar wall y CPUthread por lectura y CPUbackend real por schedstat con identidad comprobada. Exigir A/A estable dentro10% en wall/CPUapp/CPUbackend; C debe mejorar al menos10% de wall en ambas rutas, no empeorar CPUapp o backend más5% y no regresar en al menos4de6bloques. Mismos umbrales111; un resultado no elegible se descarta, no se repite idéntico para cruzar el corte.

Después de controles, cuatro observaciones A/C por ruta con SQL/FETCH comercial y heapPython separados; ambas variantes deben conservar streaming y cardinalidad completa. Capturar planes actuales originales/candidatos SELECT y DECLARE en RR/read-only, redactados, sin inferir CPU ni tiempo de los planes de sólo planificación. Total148lecturasHTTPClient. Antes de ejecutar, verificar el instrumento derivado y sus huellas exactas. No lanzar TCP/900s por un PASS de integridad experimental.

Una integración posterior exige definición de autoridad compartida, matriz adicional de permisos/borrado/membresías y regresión de consumidores. Sólo un cambio real integrado permitirá un ciclo de retorno a la base66c6d381; no presentar este experimento como cierre B13.

Instrumento de coste preparado: tests/beta_joined_authority_roi_diagnostic.py deriva del arnés111, con bucle de controles y cálculo de elegibilidad exactamente iguales. La candidata compila sólo el helper comercial en un namespace privado con joined_authority; no usa el wrapper de65comparaciones de la batería de paridad. Observaciones separadas conservan streaming en ambos brazos y capturan ocho planes de planificación. SHA del módulo experimental de autoridad fijado al corte073316; umbrales y fuentes de producto intactos. Resultado pendiente.

## Resultado de coste y rechazo

074147-0ae01cbc:1PASS de integridad,0fallos/omisiones/advertencias,939,331sJUnit,148lecturas. [Auditoría independiente](evidencias/b08-joined-authority-roi-audit-20261021.json):36brazos/108controles,criterios recalculados,huellas de candidata idéntica a paridad y726fuentes runtime intactas durante el ensayo; fuentes/limpieza/PIDs/backend/Telegram confirmados antes de editar. Los ocho planes son de planificación, no tiempos de ejecución ni CPU.

| Ruta | Mediana A | Mediana B | Mediana C | C frente AB | A/A estable | Bloques no regresivos |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| ListadoES |301,387ms|276,995ms|367,279ms|+27,00%|no|2/6|
| BúsquedaEN |355,783ms|357,347ms|349,600ms|−1,95%|sí|3/6|

candidate_eligible=false. El listado no cumple estabilidad de CPUbackend y C/AB empeora CPUapp36,02%/CPUbackend14,55%; no atribuir la causa a factores externos no medidos. Búsqueda mejora menos10% y no alcanza4bloques no regresivos. No rescatar sólo la CPU favorable de búsqueda. Rechazar sin aplicar ni repetir esta misma variante para cruzar umbral.

Ambos brazos conservan cinco fetch comerciales y2000filas en cada observación; las cuatro observaciones de heap/SQL están separadas de controles y no son RSS. El PASS acredita integridad del experimento, no aceleración, TCP ni beta. Corto112359 sigueFAIL y900s bloqueado. No se extrae una segunda definición permanente de permisos para una candidata descartada. La posterior corrección B14 de configuración de correo queda en otro corte y no altera esta comparación histórica.
