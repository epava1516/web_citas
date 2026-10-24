# B08-341 — Paridad promocional en transacción heredada

El corte396 del grafo se ha revalidado antes de este hito: 14.001 nodos y 60.213 relaciones, sin fuentes obsoletas. El alcance conserva AST dirigido y semántica seleccionada; no es una extracción global nueva.

## Hallazgo y alcance

La descripción inicial de B08 en el roadmap103 corresponde al problema anterior a la corrección. Actualmente discovery.results llama state_page también con promociones. promotion_paging usa un mapa de derechos compatibles en snapshot propio y orden SQL cuando hereda una transacción. El mapa sigue siendo proporcional al número de derechos compatibles; iterar en bloques no demuestra memoria constante.

La prueba existente de transacción heredada verifica un patrocinio positivo y evita reutilizar el mapa. Falta un testigo completo del oráculo congelado bajo READ COMMITTED heredado. Se añade tests/test_promotion_inherited_full_parity.py reutilizando el recorrido de referencia existente: 49 perfiles sintéticos, derechos solapados Premium/Top/Autosubida, empates, dos días, ES/EN, búsqueda y filtros; se comprueban todas las páginas, IDs, orden, etiquetas, recuento, unicidad y estado editorial. El aislamiento se comprueba antes y después. No se modifica aplicación ni el oráculo congelado.

## Prerregistro

Ejecución enfocada con PostgreSQL y Redis propios, tres workers y timeout1200s por comando. Selectores: test_promotion_paged_equivalence.py (4), test_promotion_snapshot_ordering.py (4), test_promotion_pagination_rotation.py (1) y test_promotion_inherited_full_parity.py (1): diez casos esperados. Se conservarán fuentes, JUnit, limpieza y recibo Telegram. No se repetirá carga contractual ni se atribuirá capacidad nueva a esta regresión.

B08 sigue pendiente de aceptación: además de esta ejecución hay que conciliar evidencia de coste y cobertura de fallback natural. B07 aceptado no sustituye esos requisitos. El resultado terminal se añadirá tras inspeccionarlo.

## B15: aclaración de almacenamiento

La dirección del usuario mantiene cookies propias para visitantes sin cuenta y evaluación de preferencias privadas cifradas con cuenta. PostgreSQL con campos cifrados es una recomendación técnica, no una decisión del usuario frente a almacenamiento de objetos. No se implementa B15 en este corte, no se importan automáticamente preferencias a una cuenta ni se habilita seguimiento conductual. La decisión DEC-038 conserva pendientes arquitectura, claves, plazos y evaluación jurídica por campo.

## Corrección del instrumento antes de aceptación

La ejecución20261024-050202-1eae46cc se interrumpió expresamente: nueve casos completados en el journal y el nuevo caso sin resultado terminal propio. No se acredita PASS de esa batería. Fuentes conservadas, limpieza del runner y envío Telegram confirmados; resultado ERROR preservado.

La primera versión envolvía también preparación/refresh en la transacción heredada. Se corrige el alcance del instrumento: los fixtures conservan sus límites de commit y cada una de las32peticiones HTTP del oráculo se ejecuta dentro de una transacción real READ COMMITTED, comprobada antes y después. No se simula la respuesta ni la función state_page. La causa exacta del coste de preparación dentro de la transacción no se declara defecto de aplicación.

Se prerregistra nuevamente la misma batería de diez casos, tres workers y timeout1200s, con fuentes y grafo actualizados antes del lanzamiento.

## Resultado verificado

Ejecución20261024-050815-461b26b4: diez PASS, cero fallos, errores u omisiones;286,126s sumados de casos JUnit, tres workers. El caso heredado comprueba32peticiones y doce variantes del oráculo congelado. Auditoría b08-341-regression-audit.json:1711fuentes coinciden con las congeladas, contenedores y temporal ausentes, identidad del proceso terminada y Telegram enviado. El negativo interrumpido se conserva en b08-341-interrupted-audit.json.

Reuso auditado: b08-341-contractual-identity.json verifica cuatro artefactos originales y cuatro fuentes actuales frente a contractual296; b08-341-historical-cost-reuse.json verifica14artefactos y el mismo instrumento de diagnóstico1000/10000. La primera página promocionada histórica pasó de15758,2/160637,0ms y3426/34026consultas a151,3/361,3ms y33consultas. Son medianas descriptivas de peticiones seriales con Django Client y diferentes IDs sintéticos; no una medición nueva ni atribución causal emparejada. La coincidencia de fuentes con B07 no cubre automáticamente cada rama de B08.

La revisión estática b08-341-fallback-review.json distingue casos de49pendientes reales, límites reducidos y referencias/prototipos. Próximo trabajo: testigos multipágina de la función actual con promociones para fallback natural, incluyendo el umbral real1000 y la guarda final con divergencia derivada explícitamente simulada. No hay defecto nuevo de aplicación demostrado ni cierreB08. Se mantienen diez de18puntos aceptados y B15 opcional.

Decisión posterior: la cobertura pendiente se verifica en [302](302-fallback-promocional-umbrales-reales-b08-20261024.md) y se concilia en [303](303-matriz-cierre-promocional-b08-20261024.md); B08aceptado por [acta18](actas/18-beta-b08-aceptacion-local-20261024.md). Las afirmaciones de pendiente anteriores corresponden al corte341.
