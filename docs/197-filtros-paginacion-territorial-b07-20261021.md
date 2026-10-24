# B07 — Filtros combinados y paginación territorial sintética

Estado: equivalencia funcional10/100 verificada en PostgreSQL real; B07 abierto8/18.

La preparación196 se verifica ahora con poblaciones10y100, reparto70/30 proporcional. Se corrige limits del nuevo retorno para no declarar geografía compartida, conservando el objeto original intacto. No cambia código del producto ni fixture TCP por defecto.

## Protocolo previo

Runner oficial focused/1worker/snapshots/native-source, timeout300, sólo tests/test_promotional_statistics_preparation.py. Cuatro casos esperados sin omisiones: dos previos de censo/finalizador y dos poblaciones territoriales. Para cada población: seis negativas sin mutación, nativa publicly_visible para todos, refresco/estado actual, órdenes y derechos idénticos; ciudad sola y ciudad+texto photography por ambos idiomas. Recorrer todas las páginas y exigir IDs únicos/disjuntos cuya unión sea el censo exacto de cada ciudad, recuento y número de página estables, máximo24filas. A100exigir20páginas HTTP y alcanzar tercera página (incluye intermedia/última), no sustituirlo por primera página.

Guardar protocolo íntegro/SHA; congelar fuentes/docs durante ejecución. Exigir4PASS/0FAIL/0ERROR/0SKIP,628fuentesproducto intactas, fuentes/limpieza propia/PIDs/Telegram verificados antes de documentar. FAIL/ERROR se conserva y detiene secuencia. Es equivalencia funcional con cliente Django y PostgreSQL real, no TCP/20RPS/1000/10000 ni prueba de recursos/p95/representatividad nacional. Mantiene todos los pendientes de matriz180 para carga grande. Sin900automático ni aceptaciónB07/global.

## Resultado terminal auditado

Run `20261021-221648-026152c0`:4PASS/0FAIL/0ERROR/0SKIP,82,671sJUnit sumados por caso. [Auditoría](evidencias/b07-territory197-filters-pages-20261021-audit.json):10perfiles7/3 con8páginas HTTP;100perfiles70/30 con20páginas HTTP y tercera página alcanzada. Todas las publicaciones verificadas por regla nativa, cada combinación ciudad/texto/idioma conserva censo exacto y unión de IDs sin duplicados entre páginas; órdenes y derechos idénticos. Seis negativas sin mutación por población. Se verificó la corrección de limits sin reescribir el dataset original.628fuentes de producto intactas; protocolo, mapa de fuentes, limpieza de contenedores/temporal/PIDs y Telegram comprobados antes de documentar.

La [preparación196](196-preparacion-territorial-explicita-b07-20261021.md) queda ampliada en este corte, sin atribuirle retrospectivamente esos casos. La [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md) conserva1000/10000, TCP, estados/backlog, recursos y PRODUCTIONchecked pendientes. No se midió orden contra un oráculo independiente de ranking; la evidencia acredita IDs/recuento/completitud por filtro y página, no equivalencia global de ranking ni capacidad.

## Protocolo previo198 — orden por página

Tras el corte197 se amplía la prueba con un comparador independiente del ranking comercial: lee todos los derechos del censo y usa autoridad nativa eligible, pero no llama candidates/order_population/ranked ni toma el orden HTTP como referencia. Recalcula en Python Premium→Top→orgánico, SHA256 díaUTC/ID y desempateUUID; conserva orden orgánico por publicación/ID y relevancia obtenida del primitivo PostgreSQL SearchRank. Es independencia del orden comercial, no una segunda implementación del motor de búsqueda o de autoridad. Fixture sin autobump; no generalizar a autosubida o revocaciones concurrentes.

Mismo runner/comando y cuatro casos10/100, timeout300. Exigir en cada una de las8/20páginas igualdad de la secuencia completa de IDs con su segmento de referencia, además de recuento/completitud/negativas/derechos existentes. Mantener4PASS/0omisiones,628producto intactas, fuentes/protocolo/limpieza/PIDs/Telegram. Congelar durante ejecución. Un fallo se conserva y detiene secuencia. No escala1000/10000 ni TCP por esta prueba; resultado no se suma al corte197 como ocho casos de una candidata común.

## Resultado198

Corte198 auditado:4PASS/0FAIL/0ERROR/0SKIP,117,715sJUnit sumados;10/100perfiles y8/20páginas coinciden en secuencia completa con comparador comercial independiente.628producto/fuentes/protocolo/limpieza/PIDs/Telegram verificados; no autosubida, escala1000/10000 ni TCP. [Auditoría](evidencias/b07-territory198-filters-pages-20261021-audit.json). Los resultados197anteriores se preservan en su corte; no se suman como ocho casos comunes.
