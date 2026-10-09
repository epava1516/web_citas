# MOD05: residual actual, desconocidos acotados (retirado) y dependencia de concurrencia

**Equivalencia PASS; mecanismo SQL demostrado; efecto HTTP prefijado no cumplido → cambio retirado.** No es un gate de carga ni cierre de CR09. Trabajo manual de Claude Code (Claude Opus 5.5) por instrucción directa del usuario, goal automático del proyecto pausado, cola única en [seguimiento17](../17-seguimiento-desarrollo.md).

## 1. Reconstrucción del camino y diagnóstico finito

Fuente `c82a746` (producto `2dd4ca5`). Ruta pública de listado/búsqueda: `discovery.results` → `publication_state.state_page` (instantánea REPEATABLE READ) → lectura de sucios → `all_state_current()` si no hay sucios, o enumeración de desconocidos si los hay → pertenencia no correlacionada al estado elegible → recuento y página → hidratación y guard nativo de 24 filas (`PublicationContext`) → `PagePresentation` (2 lecturas agrupadas) → render. Ficha: handler nativo.

Graphify (reconstruido hoy) se contrastó con el código: los nodos y relaciones de MOD05 coinciden con las fuentes; la topología de la rama de desconocidos se tomó del código, no del grafo.

**Única incertidumbre medida:** dónde va el tiempo no-SQL de las rutas actuales. [Diagnóstico](mod05-perfil-python-diagnostico0110.json) con cProfile, Client in-process y PostgreSQL sintético propio. 10.000 anuncios, repetido/diverso, 6 rutas contractuales: 2 warmup, 5 controles sin profiler y 3 requests perfilados agregados. [Test](mod05-perfil-python-test0110.py.txt) y [runner](mod05-perfil-python-runner0110.py.txt) archivados. Base y medios propios retirados y verificados.

| Ruta (10.000) | `psycopg` `Connection.wait` por request perfilado |
|---|---:|
| Listado ES/EN | 128–234 ms (≈60 esperas) |
| Búsqueda ES/EN | 178–246 ms |
| Ficha ES/EN | 50–83 ms |

- `Connection.wait` es tiempo bloqueado esperando al servidor: ejecución, red y recepción. No es CPU de PostgreSQL ni planificación.
- El resto del tiempo Python se reparte en miles de llamadas pequeñas (isinstance/getattr/copy/compilación SQL/plantillas ≈4–7 ms por grupo). **No existe un tramo Python concreto ≥20 ms**, así que no se justifica código nativo.
- Picos aislados de 55–67 ms por request aparecen en funciones arbitrarias con pocas llamadas. Se interpretan como pausas del GC del proceso de test (heap con la población creada en el mismo proceso). No se atribuyen a esas funciones ni se trasladan a gunicorn.
- cProfile infla el Python: solo se usa la clasificación relativa.
- Host compartido con servicios ajenos: los controles de hoy son más lentos que la matriz previa. No se comparan poblaciones.

## 2. Discriminación con evidencia existente

| Candidato | Evidencia | Valoración |
|---|---|---|
| COUNT separado de la población (camino limpio) | Matriz: 14,5–16,1 ms en listado, 20,5–27,9 ms en búsqueda | No llega a 20 ms en listado. Solo no es material |
| `all_state_current()` (camino limpio) | 7,3–16,9 ms | Necesario para exactitud; ahorro no material |
| Validación/render de 24 filas | 24 `full_clean` ×2 ≈18 ms inclusive; render ≈40 ms | Guard obligatorio; sin tramo dominante |
| **Enumeración de desconocidos (camino sucio)** | 346/400 requests bajo carga con `native_unknown=1`. Planes archivados: 10.000 index probes correlacionados al estado, 38–105 ms de ejecución | Mecanismo distinto de la ordenación ya retirada → **intervención seleccionada** |

## 3. Intervención prefijada

[Manifiesto anterior a la implementación](mod05-sucios-acotados-manifiesto0110.json).

- **Hipótesis:** con sucios presentes, la enumeración evalúa «sin estado fiable» para cada candidato aunque un invariante global demuestre que ningún anuncio carece de estado vigente.
- **Cambio mínimo ([diff](mod05-sucios-acotados-candidato0110.diff)):** si hay sucios y `all_state_current()` es verdadero en la misma instantánea, desconocidos = candidatos ∩ sucios, con el mismo orden y límite. En otro caso, enumeración original. El camino limpio no cambia.
- **Equivalencia:** `PublicationState.listing_id` es PK/FK con CASCADE. El invariante vacía el segundo término para cualquier subconjunto, así que salen el mismo conjunto, la misma decisión de fallback (>48) y la misma evaluación nativa.
- **Criterio:** reducción de la media HTTP ≥20 ms y ≥5 % en **las 8 celdas** de listado y búsqueda (ambos fixtures, ambos pares equilibrados); ficha sin regresión mayor que max(10 ms, 5 %); mecanismo observado en el plan.

## 4. Equivalencia y regresión

PostgreSQL sintético propio, verificado con el código candidato:

- [Test](mod05-sucios-acotados-equivalencia-test0110.py.txt): 5 límites nuevos PASS.
  - Sucio elegible y sucio revocado (invariante verdadero).
  - Sucio con estado ausente y sucio con versión antigua (invariante falso con sucios).
  - Sucio no candidato.
  - Cada uno en ES/EN, páginas 1/2, `checked` age y contact+agency, y filtro de servicios. Contenido HTML byte a byte, recuento y ruta frente al nativo.
  - La consulta correlacionada al estado aparece solo cuando el invariante es falso.
- Regresión MOD05: 39 PASS (pertenencia 4, `test_publication_state.py` 28 incluida la equivalencia PRODUCTION con sucios y estados ausentes, condicional, inventario y upgrade).
- Una primera ejecución falló en la aserción de mecanismo por un marcador demasiado amplio, que coincidía también con la anotación correlacionada de `safety_restriction`. La equivalencia de contenido ya había pasado. Se corrigió el marcador, no el producto, y se repitió.
- PRODUCTION con el fixture multipágina no publica ningún anuncio sintético (verificador simulado): resultado trivial. La cubre la prueba existente.

## 5. Contraste TCP

Arnés existente con el modo opt-in añadido ([diff ejecutado](mod05-sucios-acotados-arnes0110.diff)) y la [referencia congelada](mod05-sucios-reference0110.py) igual al `_state_page` de HEAD (sha256 `77d8fb58…4540`).

- Diseño: antes→después→después→antes, 10 controles por ruta y bloque, 6 rutas, 480 controles TCP secuenciales, 10.000 repetido y diverso, cuatro workers sync propios.
- Un sucio fuera de la primera página: `native_unknown=1` comprobado en cada request de listado/búsqueda.
- Sin profiler en los controles.
- [Análisis](mod05-sucios-acotados-analisis0110.json) y [script](mod05-sucios-acotados-analisis-script0110.py) reconcilian los 480 eventos WSGI con los logs originales de los workers; los 8 PIDs ya no existen.

| Fixture | Familia | Par 0→1 (ms, %) | Par 3→2 (ms, %) | Cumple |
|---|---|---:|---:|---|
| Repetido | Listado | 5,3 / 1,3 % | 11,8 / 3,1 % | No |
| Repetido | Búsqueda | 18,9 / 4,4 % | 7,9 / 2,0 % | No |
| Diverso | Listado | 4,8 / 1,2 % | 9,8 / 2,4 % | No |
| Diverso | Búsqueda | **48,1 / 10,6 %** | **47,8 / 10,1 %** | Sí |
| Ambos | Ficha (control) | sin regresión | sin regresión | Sí |

Medias WSGI antes→después (n=40), por familia:

| Fixture | Listado | Búsqueda | Ficha | D |
|---|---|---|---|---|
| Repetido | 399,5→390,8 | 409,8→396,4 | 125,9→121,0 | 311,7→302,7 (ΔD 9,0 ms) |
| Diverso | 395,4→388,2 | 463,9→415,5 | 121,1→116,8 | 326,8→306,8 (ΔD 20,0 ms) |

El ΔD es descriptivo: incluye la fluctuación de ficha, cuyo código no cambia. Upload y ΔU: not_measured.

**Mecanismo, en EXPLAIN separado de búsqueda EN:**

| Fixture | Enumeración antes | Enumeración después | Comprobación global añadida |
|---|---|---|---|
| Repetido | 60,3 ms, Index Scan sobre el estado ×10.000 | 0,155 ms, sin estado | 17,4 ms |
| Diverso | 77,9 ms, Index Scan sobre el estado ×10.000 | 0,130 ms, sin estado | 8,6 ms |

En repetido, el plan de hoy difiere del hash archivado de la intervención anterior. El plan no es aceptación HTTP. El listado no se sondeó con EXPLAIN y su ganancia HTTP fue pequeña, así que la enumeración no parece explicar su coste (no comprobado con plan).

## 6. Decisión y limpieza

**Retirado.** `apps/listings/publication_state.py`, `tests/test_publication_state_tcp.py` y `scripts/publication_order_benchmark.py` están restaurados con huella idéntica a `c82a746` ([huellas](mod05-sucios-acotados-huellas0110.json)). Candidato, test, arnés, referencia, JUnit, logs y planes están archivados ([tar](mod05-sucios-acotados-artefactos0110.tar.gz)). No se repetirán variantes de esta intervención.

Verificado independientemente: sin bases `promotion_gate_cr09diag_*`, PIDs ausentes, `pytest-temp` eliminado y sin procesos propios. Runtime normal y servicios ajenos intactos. Sin cargas 30/60/900 s ni cambios de workers, PostgreSQL o caché.

## 7. Conclusión: la evidencia favorece evaluar concurrencia

- **El trabajo exacto eliminable identificado no es material para la capacidad.**
  - En el camino limpio queda como máximo COUNT + comprobación global ≈22–45 ms por request de listado/búsqueda, es decir ΔD ≲ 13–22 ms.
  - En el camino sucio, la intervención medida dio ΔD 9–20 ms y solo fue material en búsqueda diversa.
  - Con la matriz limpia vigente, D = 206,7–221,8 ms → 20D = 4,13–4,44 worker-s/s antes de uploads. Incluso restando 13–22 ms, 20D ≈ 3,7–4,2: ocupación ≈ 0,92–1,04 con cuatro workers sync, sin margen para p95 bajo carga.
- **El servicio está dominado por espera bloqueante, no por CPU Python concentrada.**
  - `Connection.wait` supone 128–246 ms por request perfilado de listado/búsqueda.
  - Bajo carga, la CPU del thread fue ≈52 % del WSGI en listado y búsqueda ([diagnóstico de recursos](mod05-recursos-informe0110.md)).
  - Un worker sync no puede usar esa espera, y el host mostró CPU usada por debajo de su total (sin garantía, con servicios ajenos).
- **Seguir optimizando** exigiría encadenar microintervenciones de <20 ms cada una, lo que el contrato excluye.
- **Dependencia concreta que impide avanzar:** autorización expresa renovada para ejecutar la [propuesta 4/6/6/4 ya preparada](mod05-capacidad-4-vs-6-propuesta0110.json) sobre el código actual. Su estado es `PROPOSED_NOT_EXECUTED_REQUIRES_RENEWED_AUTHORIZATION`, su runner rechaza ejecutar sin `AUTHORIZED`, y queda **no ejecutada**. Seis workers sigue siendo candidata, no adoptada.
- **Observación para decisión del usuario, no aplicada:** el arnés contractual no ejecuta el refresco MOD05 (worker/Beat) que forma parte de la arquitectura desplegada. Por eso, tras el primer upload, casi todo el listado y la búsqueda sigue el camino sucio. Cambiar esa definición del escenario no es una decisión técnica local.

CR09 y GS01 abiertos; porcentajes, contrato, umbrales y veredictos FAIL/INVALID/PASS históricos intactos con sus ámbitos. Ningún resultado local habilita los 900 s.
