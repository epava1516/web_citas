# B07 — Escala de equivalencia territorial1000/10000

Estado: secuencia terminada y auditada; B07 abierto8/18.

Extiende el [comparador197/198](197-filtros-paginacion-territorial-b07-20261021.md) a1000/10000. Refactor compartido conserva recorrido exhaustivo10/100 y calcula referencia una vez por ciudad/texto, reutilizada entre idiomas. Escala grande exige censo nativo completo, orden comercial de referencia e IDs/recuento/secuencia de páginas inicial/intermedia/última por ciudad, texto y ESEN. No afirma recorrer todas las páginas grandes. Repartos700/300 y7000/3000; a1000máxima página30, a10000máxima292.24páginas HTTP por escala,24filas máximo. Sin autosubida ni proveedores.

## Secuencia preregistrada

Tres runners oficiales focused/1worker/snapshots/native-source, PostgreSQL/Redis propios. Primero archivo tests/test_promotional_statistics_preparation.py:4PASS,10/100exhaustivo. Sólo si pasa ejecutar tests/test_capacity_territorial_equivalence.py::test_large_territorial_equivalence[1000]:1PASS. Sólo si pasa ejecutar el mismo caso[10000]:1PASS. No ejecutar fase posterior tras FAIL/ERROR/omisiones/fuentes cambiadas o aviso fallido; conservar terminal. El nuevo archivo se registra en LONG_CASES para excluirlo de regresiones ordinarias; la selección focused explícita lo incluye. No pérdida silenciosa de cobertura.

Timeout por fase:300/1800/5400s. Estimación total15–60min, sin promesa de ahorro. Un solo proceso persistente coordina secuencia y guarda fase/resultado/runs. Todos los runners notifican terminal tras limpieza; aviso de secuencia terminal separado. Congelar código/docs/.ai/grafo; no otras baterías/builds durante espera. Verificar628fuentesproducto, mapas de fuentes por cada runner, JUnit y propiedades, limpieza fresca de contenedores/temporal/PIDs y recibosTelegram antes de documentar. Cada fase exige su propioPASS; no sumar percentiles ni presentar tres runners como un caso común.

Avisar porTelegram antes de pausar y verificar recibo/lanzamiento. Pausar mismo goal; disparador autorizado espera terminal de secuencia sin modelo y reactiva mismo objetivo preservando consumo. Solicitar compactación al pausarse. Si no se confirma relevo, no afirmar preparado. No relanzar por observación perdida.

Resultado sólo equivalencia funcional con clienteDjango/PostgreSQL real; no TCP/20RPS/p95/8CPU8GiBkernel ni distribución nacional representativa, no PRODUCTIONchecked ni aceptaciónB07/global. Estados/backlog/recursos y mezclaTCP de matriz180 siguen pendientes. Sin900automático.

## Resultado auditado

B07-199 secuencia territorial auditada: tres runners con4+1+1PASS; escalas1000/10000 repartidas700/300 y7000/3000,24páginas seleccionadas por escala hasta30/292. Censo nativo y orden comercial de referencia verificados;628fuentesproducto intactas, limpieza y Telegram confirmados. Compactación solicitada y reactivación automática del mismo goal comprobadas. Equivalencia funcional, sin capacidadTCP ni cierreB07;8de18.

[Evidencia por runner](evidencias/b07-territory199-scale-20261021-audit.json): común20261021-223012-fb19db56,4PASS/100,563sJUnit;1000en20261021-223225-ff043b95,1PASS/387,046s;10000en20261021-223924-38a4e2f2,1PASS/3519,818s. Cobertura10/100 exhaustiva;1000/10000 inicial/intermedia/última, sin afirmar todas las páginas HTTP grandes. Fuentes de los tres runners iguales al mapa previo y protocolo originalSHA19155848b4779bef425193b4bab0170cb6e0ff0faf75e0a75f52f004c24a624d conservado. La auditoría se ejecutó antes de modificar documentación.
