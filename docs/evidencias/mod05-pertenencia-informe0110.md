# MOD05: pertenencia al estado elegible — cambio conservado

**Equivalencia pertinente PASS; efecto prefijado PASS.** Se conserva la sustitución del EXISTS correlacionado de la población final por una subconsulta de pertenencia no correlacionada. No es un PASS del gate de carga ni cierre de CR09.

## Coste observado y cambio

Los [planes originales](mod05-orden-desconocidos-ab-revisada0110.json) de búsqueda diversa mostraban 9.999 accesos indexados a PublicationState en la selección final. El fixture repetido ya usaba pertenencia hash: no se supuso ahorro en él. Esta hipótesis afecta al acceso repetido al estado en la población final y es distinta de la ordenación intermedia retirada.

[Manifiesto anterior al cambio](mod05-pertenencia-manifiesto0110.json): se seleccionan en SQL los identificadores del estado elegible bajo la versión vigente y los flags checked actuales; se mantiene la exclusión de sucios y la unión con IDs evaluados nativamente. PublicationState.listing_id es una clave primaria única y no nula: pertenencia y EXISTS tienen la misma semántica booleana en este caso. Permanecen la enumeración de desconocidos, límites/fallback, filtros, DISTINCT pertinente, ranking, orden promocional, recuento exacto, páginas y guard nativo dentro de la misma instantánea REPEATABLE READ.

No se guardan resultados nuevos ni se cambia invalidación, autoridad, revocación, privacidad o caducidad. La subconsulta se construye con parámetros actuales en cada petición; no es un prepared statement ni reutiliza un plan preparado. El esquema y dependencias siguen siendo los de MOD05; cambiar esta fuente también cambia rules_version, por lo que sigue siendo necesario el refresco oficial antes de servir tráfico con estados fiables. No se ha desplegado en el runtime normal.

## Equivalencia y controles

[9 casos PostgreSQL correctos](mod05-pertenencia-funcional-revisada0110.json), 219,56 s de pytest / 221,68 s del runner. Incluyen normal/PRODUCTION, filtros multivaluados, checked, estado ausente o de versión antigua, sucio todavía elegible o revocado, segunda página/desempates y las dependencias condicionales decision/proof. Se comparan HTTP, recuento y páginas con validación nativa. Evidencias anteriores de triggers, refresco concurrente, barrido, presentación y navegador se reutilizan en su alcance sin sumar versiones como N3 común.

[Dos casos TCP correctos](mod05-pertenencia-ab-revisada0110.json), 307,31 s pytest / 309,41 s runner: 480 controles secuenciales por TCP, fixtures repetido/diverso de 10.000 anuncios, cuatro workers síncronos propios. En cada fixture: antes→después→después→antes, diez controles por seis rutas ES/EN en cada bloque. Cada familia/variante tiene 40 observaciones y cada familia/bloque, 20. Dentro de cada familia, las dos rutas ES/EN pesan 1/2. Un candidato dirty fuera de la primera página conserva el aprobado y permanece realmente desconocido.

Se reutiliza el adaptador sintético opt-in de referencia congelada: «antes» ejecuta únicamente la función _state_page original; «después», el candidato. El resto del código, esquema, datos, proceso, preparación y observadores es común. Metadatos comprueban la variante realmente servida, `state/trusted_state` y native_unknown=1 en listado/búsqueda. HTML completo equivalente; en fichas solo se canonicaliza el token tras comprobar firma y Listing/revision exactos. Los 480 eventos originales de workers coinciden con JUnit, tienen IDs únicos y PIDs correspondientes a sus ficheros.

Sin profiler SQL/reglas intrusivo en controles. El observador común incluye iteración y cierre del response WSGI; su overhead causal es not_measured. Emisión y entrada se verifican con el reloj monotónico común. El cierre WSGI puede ser posterior a la recepción del cliente: 20/240 casos repetidos, máximo 1,013 ms; 15/240 diversos, máximo 6,412 ms. No se fuerza anidamiento de intervalos distintos.

## Efecto HTTP y WSGI

Criterios registrados antes de implementar: búsqueda diversa mejora ≥20 ms y ≥5 % de media HTTP en ambos pares; las demás celdas no empeoran más de max(10 ms, 5 % de su baseline). La asimetría está justificada por el plan previo ya hash en repetido. Ninguna cifra es un SLO nuevo.

| Búsqueda diversa | Antes HTTP (ms) | Después HTTP (ms) | Reducción |
|---|---:|---:|---:|
| Par 0→1, n20 por celda | 484,268 | 427,738 | 56,530 ms / 11,673 % |
| Par 3→2, n20 por celda | 487,448 | 440,355 | 47,093 ms / 9,661 % |

Ambos pares cumplen; las diez celdas de control cumplen sus límites de regresión. Es una mejora material reproducida dentro del diseño finito prefijado, no una atribución exclusiva de todas las fluctuaciones a código.

Medias WSGI por familia, n40 antes y n40 después:

| Fixture | Listado antes→después (ms) | Búsqueda antes→después (ms) | Ficha antes→después (ms) |
|---|---:|---:|---:|
| Repetido | 336,753→339,710 | 391,066→358,728 | 108,217→93,956 |
| Diverso | 350,703→345,360 | 484,556→432,845 | 108,886→117,818 |

ΔD descriptivo = Σ(antes−después)/3: 14,547 ms repetido y 16,040 ms diverso. 20ΔD = 0,290943 y 0,320807 worker-s/s. Incluye fluctuaciones de ficha, cuya implementación no cambia; no se atribuyen como mejora del backend. El componente observado de búsqueda diversa ponderado por 1/3 es 17,237 ms de worker/request y 0,344735 worker-s/s a 20 RPS. Es cálculo sobre controles secuenciales; **no se resta del D=239,186 ms de la cohorte histórica bajo carga ni predice cumplimiento**. Upload y ΔU: not_measured en este contraste y contabilizados aparte en el diagnóstico original. W sigue siendo ocupación, no CPU.

## Mecanismo SQL separado

Se capturan las mismas tres operaciones unknown/count/page, no simplemente los nuevos tres eventos más lentos. EXPLAIN (ANALYZE, BUFFERS) se ejecuta sobre lecturas propias en transacción de solo lectura, separado de HTTP. JIT observado conservado; sin alterar configuración de PostgreSQL, concurrencia o planes preparados. Parámetros no persistidos y literales de texto redactados. Las sondas Client y EXPLAIN calientan cachés antes de los controles; no se vacían cachés.

| Diverso | Operación | Planning antes→después (ms) | Execution antes→después (ms) | Shared hits antes→después |
|---|---|---:|---:|---:|
| Estado sucio | Enumeración desconocidos, sin cambiar | 1,150→1,094 | 89,354→105,094 | 61.785→61.785 |
| Población final | Recuento | 0,842→0,511 | 21,254→20,565 | 2.224→2.224 |
| Población final | Página | 0,746→0,506 | 83,322→28,590 | 61.776→2.224 |

En la página diversa, el nodo de estado pasa de Index Scan (Actual Rows=1, Actual Loops=9.999, shared hits=29.997) a Seq Scan (Actual Rows=10.000, Actual Loops=1, shared hits=173). Todos estos planes observan shared reads=0. El fixture repetido conserva un único scan de estado en ambas variantes; página 41,270→39,217 ms de ejecución en la sonda. Estos valores de una ejecución EXPLAIN no sustituyen los controles HTTP ni son CPU o ahorro esperado.

La enumeración dirty continúa con 10.000 accesos indexados en el plan diverso: el cambio no elimina todo el coste residual. No se reabre por rutina la variante de quitar order_by ya rechazada. Otra intervención requerirá un mecanismo distinto y evidencia pertinente.

`cursor.execute` mezcla servidor/esperas/recepción y no mide planificación ni CPU PostgreSQL ni todas las conversiones/fetch lazy de Python. Los campos Planning/Execution provienen directamente del plan separado. Actual Rows/Loops son observaciones del nodo, no filas globales escaneadas/afectadas ni objetos ORM. CPU por operación, construcción/compilación Python desglosada, validación directa por regla, render desglosado, rows_scanned globales y overhead causal: not_measured en estos controles. Los perfiles anteriores mantienen sus fuentes, alcance y solapamientos; no se deduce validación como total−SQL.

## Decisión, limpieza y aceptación

Conservar el cambio mínimo. [Recálculo](mod05-pertenencia-analisis0110.json), [script](mod05-pertenencia-analisis-script0110.py), [archivo original con fuentes probadas](mod05-pertenencia-artefactos0110.json). Fuentes congeladas y hashes intactos hasta revisión terminal. Bases y medios propios ausentes mediante verificación independiente; ocho PIDs de workers observados ausentes, Gunicorn retirado antes de archivar logs. No cambios permanentes de recursos/servicios ajenos, workers, PostgreSQL, generador o caché.

La aceptación local de esta intervención permite avanzar a la integración/matriz vigente, reutilizando lo pertinente; no autoriza ejecutar otra carga. No se encadenan variantes. CR09 sigue abierto y no hay N3 común ni capacidad aceptada. Goal activo. Cuatro workers referencia, seis candidata no adoptada. Mantener gate VPS60 VALID/FAIL, diagnóstico30 VALID/FAIL, PASS de portátil y veredictos históricos con sus propios ámbitos; porcentajes intactos. Los 900 s siguen bloqueados. Solo un PASS completo del gate de 60 s tras los pasos exigidos puede habilitar el contractual, con autorización de alcance correspondiente.
