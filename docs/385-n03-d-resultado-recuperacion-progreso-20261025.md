# N03D — recuperación con progreso y conservación de históricos

25/10/2026. Alfa, N03 abierto,3/13bloques obligatorios aceptados. Corrección funcional de384 aceptada localmente con37PASS; no es una nueva optimización marginal del detector.

## Referencia y resultado funcional

Referencia20261025-184432-abf4326e:runnerERROR/4FAIL de pytest,0ERROR/SKIP,45,739sJUnit. Los cuatro casos reproducen no progreso: diez envíos en los episodios observados, estado ready/intento1 repetido. Firma{} no se regenera; la foto histórica excluida por detector sigue provocando envíos; su hermano vigente ya completo no evita otro envío; un original ausente tampoco llega a fallo explícito. Evidencia FAIL preservada.

Candidata20261025-184941-1ac056e3:37PASS/0FAIL/ERROR/SKIP,202,223sJUnit. Mismo instrumento/datos sintéticos/entorno serial y1742huellas intactas en cada ejecución; sólo cambian2archivos de aplicación entre pasadas. Cuatro casos nuevos,16de recuperación383,11de limpieza/retención y6flujos originales de fotos. Ledger histórico sintético persistido y consulta SQL nativa, sin afirmar aprobación humana o proveedor. Transporte capturado/direct process no equivale a worker/Beat.

| Escenario | Antes | Después |
| --- | --- | --- |
| Ready sin firma | Dos ticks siguen sin firma/comparación, envíos[1,1], intento1 | Regenera desde original, firma/ready/comparación completas; envíos[1,0], intento2; original y bytesderivado intactos |
| Sólo histórico incompleto | Envíos[1,1] sin trabajo elegible | Envíos[0,0], comparación histórica permanecefalse; evidencia/archivos/firma/intento1 intactos |
| Histórico y revisión vigente comparten Blob | Actual termina, histórico provoca segundo envío[1,1] | Completa sólo actual y termina recuperación[1,0], histórico permanecefalse, sin regenerar |
| Firma vacía y original ausente | Cuatro ticks ready sin avanzar ni error explícito | failed/errorcode/intentos2→3→4; envíos[1,1,1,0], sin marcar comparación completa |

## Cambio y alcance

process considera reutilizable ready sólo con firma no vacía, antes de decidir si adquiere lease. Reparación entra en la generación normal, conservando fences de383 y fallo propio después de guardar derivado. Root verificó AST: único cambio del proceso es esa condición, resto de servicios idéntico.

recover_media_jobs exige en su rama ready que exista una Photo activa/incompleta fuera de rectification_history_ids, igual que el ámbito de fotos origen del detector. Conserva ramas queued/stale/failed,distinct,lote100 y despacho porID. No aplica las exclusiones de candidatos ajenos a las fotos origen: rights-stage/preparaciones privadas deben poder completar su análisis propio. Consulta nativa, sin marcar histórico como completo ni borrar evidencia. Resto de tareas idéntico por AST. Revisión nativa sólolectura n06e_coverage_review:11fuentes/11citas conSHA/L/texto verificados porroot; propuesta no se usó como PASS de runtime.

## Tiempos antes y después

Milisegundos, primer tick de cada escenario. Selector real con delay capturado; process directo real si hubo envío. Una muestra por transición, sin mediana/p95. El antes hace trabajo incorrecto/incompleto y el después repara o evita trabajo: no son presupuestos de aceleración equivalentes. No mezclar tiempos QA con aplicación ni extrapolar al usuario o carga productiva.

| Escenario | Selector antes, ms | Selector después, ms | Process antes, ms | Process después, ms |
| --- | ---: | ---: | ---: | ---: |
| Firma vacía | 5.659 | 20.812 | 73.163 | 309.975 |
| Sólo histórico | 4.799 | 12.372 | 21.584 | — |
| Histórico + actual | 3.635 | 9.598 | 98.869 | 55.227 |
| Firma vacía + original ausente | 4.158 | 22.871 | 50.591 | 38.589 |

El selector es más costoso en estas observaciones por comprobar elegibilidad histórica; SQL sigue siendo1consulta por llamada en las cinco cohortes0/1/10/100/101 del instrumento383, seis observaciones cada uno, con≤100envíos y continuación verificadas. La corrección elimina no progreso y no afirma mejora temporal universal. El coste adicional queda visible y no se abre otra hipótesis marginal ahora: tiempos actuales aceptables en alfa por decisión del usuario; contrastar escalas/optimización al final del desarrollo si se justifica. Regenerar una firma realiza más trabajo útil que el retorno defectuoso anterior. No borrar derivados antiguos como parte de este arreglo; conservación/huérfanos mantienen sus controles separados.

## Auditoría y continuación

Huella de fuentes/selección verificadas,PostgreSQL/Redis propios,namespaces aislados,contenedores/volúmenes/redes/temp retirados e inventario independiente vacío,Telegramterminalsent en ambas pasadas. Lint inicial del instrumento falló por import no usado, corregido antes de congelar; recibos preservados. Grafo previo:semántica focal384 yAST instrumento; candidata actualizada porAST de2archivos, sin llamarlo semántica completa. Sin datos reales, publicación o proveedores.

N03D queda aceptado localmente; N03/N07 no están cerrados. Pendiente conciliar reintentos/backoff/recuperación con broker/worker/Beat reales y suficiencia de las acciones de cada bloque. El límite del caso de original ausente prueba selección periódica directa failed<4, no un máximo global a través de mensajes Celery. Firma{} legado es el alcance: no garantiza reparar JSON arbitrariamente corrupto. No prometer fairness o capacidad universal. MOD09restante continúa diferido al final del desarrollo.
