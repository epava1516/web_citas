# Alcance pendiente de fuentes históricas CR09

La regla vigente de docs/16 §13 exige para el censo local origen/corte/huella/
formato/período, lectura reproducible, asociación autorizada del fixture,
diferencias y divulgación revisada. Las fuentes reales ajenas pertenecen a
preparación de producción; no se exige inventariarlas para un escenario que
no las usa. Esto no permite excluir una fuente local necesaria desconocida.

La evidencia final conservada contiene 23 capturas locales sintéticas con
asociación aún no verificada. La evidencia intermedia cubre 22; no contradice
el inventario final de 23. Se mantiene esa distinción temporal.

El mecanismo sí soporta eventos firmados por sujeto en un fixture nuevo:
`tests/test_scoped_log_history_origins.py` verifica dos capturas conservadas,
diferente corte por captura, huellas originales, proyección sin identificador/
firma, separación de otro sujeto y rechazo de alteración de ámbito/contenido,
duplicados, futuro y límites. Su PASS no autentica retroactivamente capturas
anteriores sin ese protocolo.

Además, `apps/safety/rights_access_delivery.py:348` fija siempre para una
captura histórica los pendientes definidos por retained_log_origins más
historical_log_capture_coverage. La construcción del paquete alrededor de
la línea 1084 propaga ese pendiente y conserva partial=True. Se trata de
un límite observable, no de un error que pueda resolverse eliminando una
marca. La prueba exige conservarlo.

Siguiente entrega preparada: contrastar todos los requisitos del escenario
local finito con los flujos de revisión existentes y diseñar evidencia
reproducible de asociación/divulgación. Un fixture firmado nuevo puede probar
el mecanismo y debe identificarse como evidencia nueva; no sustituye la
atribución de las 23 capturas históricas ni reescribe sus resultados. Cualquier
cierre requiere evaluación motivada por fuente y revisión independiente del
contenido exacto, preservando desconocidos. Durante la regresión activa no se
modifica el código compartido ni se inicia otra carga.
