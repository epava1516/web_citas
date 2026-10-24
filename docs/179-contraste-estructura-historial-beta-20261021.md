# Contraste acotado de estructura de historial

Estado: contraste mayor terminal auditado; candidata rechazada por ahorro insuficiente. Sin cambio de producto. B07abierto8/18.

178atribuye coste a construcción/validación de historial dentro del recorrido comercial nativo. Se contrasta una hipótesis específica: retener sólo el QuerySetnoevaluado de rectification_history_ids y devolver un clon nuevo por llamada. No es la plantilla de páginaORMrechazada anteriormente; no se reabre esa variante. Sin caché de filas, documentos, resultados o decisiones.

Instrumento explícito `tests/beta_history_structure_diagnostic.py`:10perfiles/2derechos nativos, comparar SQLyparámetros del predicado, independencia de clones y caché de resultados vacía. Dos tareas: exists de historial y publicly_visible nativo con objeto fresco por lectura. SecuenciaABBA/BAAB, tres lecturas por bloque/12porbrazo y tarea, tiempos de reloj/CPUhilo, paridad del orden y número de consultas. Una secuencia local, sin aislamiento de cachés/host; no prueba mutaciones concurrentes, reversión ni equivalencia universal.

Compuerta antes de ejecutar: reducción de al menos10%en mediana de reloj y CPU del recorrido native_visibility, junto a paridad de consultas/resultados. Si falla, descartar sin contraste grande ni integración. Si pasa, sólo elegible para un contraste mayor y pruebas de vigencia; nunca adopción automática. No existe presupuesto nuevo de capacidad. Conservarnegativos.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/beta_history_structure_diagnostic.py --workers 1 --fixture-snapshots --isolate-test-broker --timeout 300
```

No más cargas60/900s, cambios de producto ni reducción de guardas por este instrumento. Telegraminicio/terminal, huellas y limpieza auditables.

## Resultado pequeño y decisión

`20261021-174234-9eb547b1`:1PASS/0omisiones,46,491sJUnit,48lecturas. [Auditoría](evidencias/history-structure-small-contrast-20261021-audit.json) reproduce medianas/compuerta, propiedadesJUnit, huellas, limpieza/temporales/PIDs y Telegram. Historialexists8,586→6,457ms/reloj−24,80%,CPU−51,75%; visibilidad nativa111,454→73,219ms/reloj−34,31%,CPU−33,26%. Mismas26consultasporlectura de visibilidad. SQLyparámetros del predicado exactos y clonesindependientes/sinresultadosretenidos. No cambia producto.

Variación entre bloques de un mismo brazo considerable: visibilidadoriginal89–124ms y candidata60–92ms en medianas de bloques. No acredita causalidad estable ni ausencia de regresiones. Elegible sólo para contraste mayor, no integración. La plantilla se evalúa únicamente en is_rectification_history/ordinary_matches vía referenciasglobales dehistory, sin reemplazar otros alias importados: no acredita optimización de todo lector público.

## Contraste mayor prefijado

Cuatro casos secuencialesABBA: original0,candidate0,candidate1,original1. Cada caso empieza tras bootstrap fuera del reloj, sin órdenes ni derechos, prepara1000perfiles/200derechos por servicios originales y refresca publicación. Misma selección/fuentes/recursos en una corrida, cohortesUUID/tiempos nuevas según generador. Registrar reloj/CPUhilo y contadorSQLsin cProfile; cotejar1000publicados,200órdenespaid/rights/attemptssucceeded/events y400audits,67Premium/133Top, estado limpio/vigente y template sin resultados. No paralelismo ni cambio deagencias/locks/validaciones. Tiempo previsto minutos, no horas; goal activo.

Compuerta antes de ejecutar: mismas cantidades de consultas y testigos de dominio en los cuatro casos; reducción al menos10%en mediana de reloj y CPU de preparación completa tras bootstrap. Dispersión de repeticiones de cada brazo `(max-min)/median` no debe superar15%en reloj niCPU. Si incumple ahorro, paridad o estabilidad, resultado no elegible/inconcluso según corresponda; no integración ni repetición automática buscando verde. Si pasa, todavía falta paridad de revocaciones, historia rectificada y consumidores antes de adoptar. No900s ni aceptaciónB07.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/beta_history_structure_diagnostic.py::test_history_structure_native_preparation --workers 1 --fixture-snapshots --isolate-test-broker --timeout 1200
```

## Resultado mayor terminal: candidata rechazada

`20261021-174846-0b37a4f5`:4PASS/0FAIL/0ERROR/0SKIP,391,920sJUnit sumados por caso. [Auditoría mayor](evidencias/history-structure-native-preparation-20261021-audit.json) reproduceABBA, medianas/compuertas y confirma propiedadesJUnit, cuatro cohortes, fuentes congeladas, contenedores/temporales/PIDs retirados y Telegramenviado. Intento previo `20261021-174734-fdf62600` detenido por RuffI001antesdepytest, cero casos, conservado; corregido sólo el formato de imports del instrumento.

Medianas de preparación tras bootstrap: original85,202sreloj/45,656sCPU; candidata84,347s/43,738s. Reducción1,004%reloj y4,200%CPU: ambas menores al10%prefijado. Dispersiónoriginal8,284%reloj/6,032%CPU,candidata2,339%/2,649%, todas≤15%; estable según compuerta, sin aislamiento causal universal.30213executeSQLporcasoenloscuatro, mismos1000publicados/200órdenespaid/200derechos/200attemptssucceeded/200eventos/400audits y estado limpio/vigente.

DecisiónREJECTED_GATE: no elegible, no integración ni pruebas de consumidores motivadas por esta variante. No repetición automática, no carga60/900s, no aceptaciónB07. Se conserva el contraste pequeño positivo, que no se generaliza a la preparación completa. Los alias de consulta fuera de las rutas del instrumento no han sido sustituidos; esto no demuestra que toda posible optimización de historial sea inútil. Hipótesis específica ensayada cerrada sin adopción; no reabrir sin mecanismo y evidencia nuevos. Aplicación intacta y8de18cerrados.
