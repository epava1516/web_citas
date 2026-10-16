# Retorno de marcado vacío — funcional correcto, ROI inconcluso

Run114702-82b41c65, fuentea3d9bd6:1PASS90,22s. Ocho controles funcionales pasan:NULL/vacío/[NULL]/válido/duplicado+NULL/IDausente/UUIDmalformado22P02/doblemarca. Mismasfilas, deltasgeneración yerrores; doblemarca conserva timestampinicial. Funciónproductiva intacta, clonespropios retirados. Fuentes/limpieza verificadas. [Recibo con18backendsy216warm](cr09-empty-mark-20261016.json).

| Primera operación | ReferenciaA/B | Prototipo | Cambio observado | A/A |
|---|---:|---:|---:|---:|
| direct_empty | 14.300ms | 2.254ms | -84.24% | 16.39% |
| complete_mark_stale | 35.219ms | 17.711ms | -49.71% | 27.32% |

Tresbloques con dirección favorable, peroA/A16,39/27,32%supera10%. **No cumple estabilidad previa**; no adoptar, no crear migración ni repetir carga limpia. Candidato sigue sóloen tests, ahorro aparente no es porcentaje delHTTP.

Carencia de protocolo identificada: los12repetidos calientes se ejecutan inmediatamente antes de abrir la siguiente conexión; pueden dejar trabajo/consumo de cuota que contamine la primera operación siguiente. No hay contadores para confirmar esa causa. Es una hipótesis de medición, no una explicación demostrada de la dispersión ni delSLO.

Se define una única correctiva de instrumento: conservar brazos/operaciones/umbrales, añadir pausa fija150ms antes de cada primera operación, igual en todos losbrazos/fuera del reloj, yleer cpu.stat delcgroupPGpropio antes/después. Registrar tiempo total delbrazo incluyendo pausa y warm, no simularlo como política operativa ni excluir llegadas delgate. Si sigueinestable, conservar ynoensayarotraspausas; no ajustar10%/20%/2de3. ContadoresPGsonagregadosconposiblebackground, noCPUporquery. No cambio delproducto.
