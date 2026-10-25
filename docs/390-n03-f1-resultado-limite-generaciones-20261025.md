# N03F1 — límite de generaciones corregido

25 de octubre de2026. Alfa,N03abierto,3/13bloques obligatorios aceptados. Se conserva la garantía heredada deCR05: hasta cuatro intentos de generación automática por Blob. No se reescribe como un límite solamente por mensaje Celery.

## Fallo reproducido y corrección

Referencia20261025-195610-4d4d1295: runnerERROR con8FAIL/3PASS,0ERROR/SKIP depytest,57,238sJUnit. Los8casos queued/processingcaducado/failed/ready sin firma con contadores4/5 generan indebidamente5/6,abren el original ymarcan comparación completa. Tres controles positivos pasan. Evidencia conservada; no convertir estosFAIL enPASS por ser esperados.

La guardia se añade únicamente a process,bajo el bloqueo deBlob. Primero respeta un leasefresco yreadycon firma;después verifica attempts>=4 antes de incrementar,leer o generar. Failedagotado conserva error ycontador. Otros estadosagotados se liquidan como failed/generation_attempts_exhausted,para que no sigan colgados enqueued/stale/readyinválido. La recuperación puede enviarlos una vez para liquidar su estado,sin nueva generación;después failed<4 deja de seleccionarlos. Datos anteriores con contador5 se mantienen visibles,sin clamp ni reset;la corrección impide incrementarlos otra vez. No añade un mecanismo administrativo de reinicio de ciclo.

| Caso | Antes | Después |
| --- | --- | --- |
| Cuatro estadosagotados, contador4 | Quinta generación/una apertura/origen analizado | Contador4,failed,cero aperturas,nueva firma/derivado/comparación no creados |
| Cuatro estadosagotados, contador5 heredado | Sexta generación;el exceso histórico sigue creciendo | Contador5 preservado,failed,cero aperturas;no ocultar exceso previo |
| Cuarta generación desde contador3 | Permitida | Sigue permitida y completa |
| Leasevigente de cuarta generación | Processing conserva su dueño | Sigue intacto,no cancelación prematura |
| Readyválido en contador4 | Puede completar comparación | Sigue comparando,sin generar ni aumentar contador |
| Otro mensaje real tras agotar4 | No acreditado por el testigo anterior;servicio permitía superar el contador | ACKde tareaSUCCESS sinretry,pero Blobcontinúafailed4 conerrororiginal;no imagenready ni nueva generación |

## Candidata y regresión

Run20261025-200423-1535dac0:49PASS/0FAIL/ERROR/SKIP,301,561sJUnit. Un arnésreal primero,11nuevos y37anteriores (4progreso,16recuperación,11retención/limpieza,6fotos).1745huellas intactas durante ejecución. Entre referencia ycandidata sólo cambian funciónprocess,el arnésreal ampliado yregistro de trabajo;restoASTde servicios idéntico.

El arnés envía otro mensaje real mientras el original deA sigue físicamente ausente,después de cuatro ejecuciones agotadas. Una ejecuciónSUCCESS/retries0,sin eventosretry/failure deeseID,y snapshots deBlobfailed4/error/started_at exactamente iguales. Si hubiera iniciado otra generación,el original ausente habría provocado otra lectura/fallo. Luego restaura originalcanónico yconserva el resto de387:OSError/backoff,ValidationErrorsinretry,Beatnativo60s,cuatro positivos recuperados/negativos intactos,prefork2,noeager/rolSQLrestringido. 39ejecuciones de tareas observadas;el nuevoACK no se confunde con éxito de imagen.

## Tiempos y alcance de la tabla

No se realizó un nuevo contraste de aceleración. El antes hacía trabajo prohibido yel después lo evita por contrato;no atribuir un porcentaje de rendimiento equivalente. La referencia de11casos tarda57,238sQA yla candidata de49tarda301,561sQA:son baterías diferentes,no latencias de aplicación.

| Etapa de la candidata real | Antes comparable | Después observado |
| --- | --- | ---: |
| ACKdel mensaje conpresupuestoagotado | Sin testigo equivalente | 59,277 ms |
| InicioBeat→primerpublish | Referencia387en otroprotocolo, sin porcentaje | 61,352 s |
| PublishBeat→cohortereadyobservada | Sin pareja comparable deoptimización | 1,267 s |

Relojes de tarea incluyen observador/SELECTde rol;primertick no acredita distribución de intervalos niSLA. Datos completos enJSON/JUnit. No se abre una optimización marginal.

## Auditoría y siguiente condición

Codex verificó reportes/propiedades de11y49,hashes,8casos0I/O,3controles positivos,guardreal yregresiones. Roles/PIDs/credenciales/directorioprivado retirados,worker/Beatexit0,clavesajenas intactas y0nuevas fuera delnamespace. Inventario independiente sin contenedores/volúmenes/redes/temp;Telegramterminalsent en ambas pasadas. Sin datos reales,proveedores o publicación.

N03F1queda aceptado localmente. N03F2continúa pendiente:medir crecimiento histórico0/10/100 con2Blob/cohorteactual fija. Borrador nativo en worktree aislado,independiente de generación,sin pruebas/imports/lint/Git/red;Codexleyó247líneas ysuinforme,no se integra mientras la candidata está congelada ni se declara medido. Después faltará acta de conciliación final poracción,puentes de identidad ytabla consolidada. N03/N07no se cierran aquí. MOD09restante diferido al final del desarrollo,tiempos aceptables enalfa.
