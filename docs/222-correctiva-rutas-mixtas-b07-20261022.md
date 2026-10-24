# B07 — rutas estables en escenario mixto

B07-250 auditado: integración PostgreSQL de 100 y 1.000 perfiles PASS; censos de rutas 56/30 y 686/300, 44 páginas y rollback lógico verificados. Fuentes1700, limpieza, Telegram, compactación y reactivación confirmados. Control HTTP corregido pendiente; 8 de 18, B07 abierto.

## Diagnóstico y cambio

El negativo249 auditado conserva56 de60 lecturas correctas y cuatro404: página30 de ciudad1, texto vacío/photography y ES/EN. Censos nativos:700 perfiles frescos,686 tras exclusiones; página máxima30→29. La aplicación responde404 correctamente a una página inexistente; el instrumento conservaba rutas del censo inicial y exigía200. No se cambia producto.

El plan contrafactual guarda route_geography desde sus referencias nativas posteriores a la mutación, antes del rollback. Exige igual cardinalidad para texto vacío y photography en esta fixture explícita. HTTP mixto prepara ese plan antes de construir rutas y antes de arrancar servidores; usa su censo para seleccionar primera/intermedia/última en carga y probes fríos. No usa respuestas HTTP ni proyección para crear esperados. Los oráculos frescos y reparados siguen recorriendo sus propias fronteras completas seleccionadas: la página30 fresca no desaparece de la cobertura, y los28 detalles excluidos siguen exigiendo404. Las rutas dinámicas esperan200 en ambas fases.

Fuentes cambiadas: tests/mixed_state_plan.py, tests/test_capacity_beta_http.py, tests/test_mixed_state_plan.py y tests/test_benchmark_territorial_routes.py. El plan mantiene fechas, rollback lógico, secuencia monotónica,14 mutaciones y límites de reparación. Prepararlo antes de servidores evita despacho de tareas durante su transacción contrafactual. PostgreSQL debe comprobar su equivalencia antes de otra cargaHTTP.

## Prerregistro de integración250

Ejecutar una sola batería oficial focused con PostgreSQL17/Redis7.4 reales propios, --workers1, --fixture-snapshots, --isolate-test-broker, native-source /tmp/web-modelos-librdb-v2.4.0 y timeout3600: tests/test_mixed_state_plan.py::test_counterfactual_mixed_plan_rolls_back_then_matches_actual_pages[100] y [1000]. Dos casos esperados. Verificar route_geography56/30 y686/300 respectivamente, cuatro censos nativos por escala, rollback/restauración,14 marcas y28 detalles404,20/24 páginas y patrocinios11/191. No acredita TCP ni worker ni capacidad. Conservar negativo si falla; no repetir para verde.

Congelar fuentes CI completas, protocolo por bytes/SHA, producto628 y grafo antes de lanzar. Sin ediciones ni pruebas concurrentes hasta auditar resultado, fuentes, limpieza real y Telegram. Relevo persistente, preaviso confirmado, pausa del mismo objetivo, compactación y reactivación automática autorizadas. Sólo después de integración auditada preparar nuevo control HTTP1000 con protocolo actualizado y criterios intactos. No900s ni10000 automático.


## Resultado auditado 250

Ejecución `20261022-151128-752f43f0`: dos casos PASS, sin fallos, errores ni omisiones; JUnit537.864s. Censos posteriores56/30 y686/300 obtenidos de referencias nativas antes del rollback. Cada escala conserva14 exclusiones,28 detalles404 y cuatro censos nativos;20/24 páginas,86/986 visibles y11/191 patrocinios. Restauración lógica verificada y secuencia monotónica, sin setval. Auditoría `artifacts/beta-promotion-fix-20261020/mixed250-audit.json`:1700 fuentes iguales entre prerregistro, lanzamiento, CI y auditoría; protocolo original por bytes/SHA, producto628 intacto y limpieza real de Docker, temporal y procesos. Telegram terminal enviado, compactación reconocida y mismo objetivo reactivado conservando consumo. No acredita carga HTTP, worker ni capacidad. Negativo249 conservado. Siguiente: prerregistrar control HTTP1000 con rutas corregidas; sin10000 ni900s automáticos.
