# B00-339 — Nodos históricos y disposiciones del corpus capturado

Fecha:2026-10-24. Alcance: dos capturas de nodos, corrección léxica dirigida y preparación de la conciliación final de B00.

B00-339: 295 de295fuentes capturadas con disposición verificada; sin lecturas pendientes en ese inventario. Revisados9.171nodos históricos y corregidas28clases Meta que compartían siete nodos del grafo actual. Sin cambios de aplicación ni nueva aceptación funcional. B00 sigue abierto para conciliación final de requisitos; nueve de18puntos beta cerrados y B15 opcional.

## Cobertura y método

Las dos capturas del11/10/2026/base7e04016 contienen9.171registros y3.738.548caracteres originales. Tres lectores nativos realizaron24asignaciones independientes por parte, sin trasladar crédito de lectura entre ellas. Leídas e interpretadas24vistas contextuales reversibles completas:1.631.354caracteres en145intervalos de hasta12.000caracteres. Se interpretaron3.437grupos por archivo/tipo/presencia de origen/tipo de nodo, incluidos2.439unitarios, con sus membresías completas; los grupos de un archivo pueden ser no contiguos.

| Captura | ID | Registros | Partes | Primer control inválido |
| --- | --- | ---: | ---: | ---: |
| Nodos1/2 | `source:gbdn3ox1asszgxe8nytq` | 5000 | 13 | 224101 |
| Nodos2/2 | `source:a3xmiqi2izexc6m6pgni` | 4171 | 11 | 14897 |

SHA256 de los textos: `6eb5b716022fa051a36e223d16621c83d875da3f7847a887522265379f89b68b` y`5dcae68ccbaf2302f8bfc475fb433f208ed1dd16d8b000e2ccef5e96529dbcf9`. Se conservan originales, prefijos, sobres, separadores, posiciones y todos los atributos/tipos/ausencias/órdenes. El principal contrastó las295capturas por identidad, longitud y huellas; reconstruyó cada registro de las dos fuentes y todas las vistas; cotejó48contextos literales y agrupaciones exactas, y unió cada fuente sin huecos ni solapamientos.

No se afirma lectura literal completa del formato original ni de los cuerpos enlazados. Preparación, decodificación y hashes no recibieron crédito semántico por sí solos: se comprobaron los informes de interpretación, conservados como extractos seleccionados y no transcripciones íntegras. original_literal_capture_fully_read=false se mantiene. En una parte una salida auxiliar de grupos excedió12.000caracteres; no se usa como prueba autónoma y la vista principal sí se leyó completa/acotada. Las primeras dos partes de nodos2 usaron formatos de agrupación distintos, reconstruidos expresamente por el principal. Una partición preliminar de92vistas fue reemplazada por el manifiesto final de24; no se infiere cobertura contando archivos antiguos.

Ambos originales siguen siendo JSON estricto inválido. El decoder permite controles sólo tras verificar ese defecto, rechaza claves duplicadas y constantes no JSON, y conserva440campos con controles en200registros. No se reconstruyen nombres dunder ni se convierten rutas dañadas en archivos válidos. La causa y los bytes del productor original no quedan demostrados. Cero nuevas invocaciones ClaudeV1; ocho históricas y consumo conservados; no se estiman tokens nativos.

## Interpretación de los nodos

Los nodos de clases, funciones, métodos, helpers anidados, pruebas y migraciones son anclas históricas. _callable y_callable_class son metadatos booleanos de extracción, no objetos importados o ejecuciones verificadas. Ausente no equivale a false o null. Un nombre test_real, PostgreSQL, actual_s3 o kernel no acredita un resultado. Los nombres genéricos Meta,source,review,task,connect oinspect necesitan identidad y ámbito; compartir comunidad no prueba una dependencia ni permiso.

Las migraciones identifican archivos, no esquema aplicado. Las etiquetas de pruebas distinguen simuladores, mocks, infraestructura propia, navegadores, workers y controles de capacidad, sin suministrar resultados aquí. Los nombres minificados JS conservan case en label y su normalización en norm_label; no permiten inferir cuerpos o completar símbolos ausentes. Los registros code con archivo/localización vacíos son referencias sin resolver; un vacío presente no es una clave ausente.

Las páginas y encabezados conservan decisiones, propuestas, pausas, estados parciales y aceptaciones de sus cortes históricos; no sustituyen el contrato romántico vigente. Una etiqueta truncada no acredita su continuación. Las explicaciones de validación por petición no niegan la arquitectura de estado de publicación almacenado de otros módulos. Preparación, lectura auditada, revisión independiente, aprobación, consumo, entrega y cierre se mantienen como etapas distintas: ni contabilidad, digest o sello conceden autoridad.

Los172conceptos finales externos —uno al final de la parte10 y171en parte11 de nodos2— incluyen148con origen semantic y24sin origen declarado. external=true es clasificación del grafo; también aparece en nombres de paquetes locales. No prueba proveedor contratado, instalación, importación, versión o uso. source_location ynode_kind están ausentes en esos conceptos, no vacíos inventados.

El grafo histórico no se restaura ni se importa sobre el actual. Con los [cortes337](296-conciliacion-relaciones-ambitos-ast-b00-20261024.md) y[338](297-conciliacion-relaciones-restantes-ast-b00-20261024.md), sus ocho capturas de datos —48.401registros entre nodos y relaciones— tienen disposición estructurada. Esto no acredita todos sus cuerpos referenciados o la corrección global de las inferencias.

## Corrección actual: ámbitos de Meta

La lectura señaló nodos Meta sin padre léxico. El contraste del AST actual confirmó inicialmente22declaraciones colapsadas en cinco nodos; el censo ampliado de1.346rutas Python nombradas por el grafo, todas parseadas, encontró otros dos archivos afectados. No es un censo de todo archivo no indexado del repositorio. Se corrigieron28declaraciones en siete archivos:

| Fuente actual | Meta separadas |
| --- | ---: |
| [Modelos core](../apps/core/models.py) | 8 |
| [Modelos de anuncios](../apps/listings/models.py) | 5 |
| [Formularios de anuncios](../apps/listings/forms.py) | 3 |
| [Modelos de medios](../apps/mediafiles/models.py) | 4 |
| [Formularios promocionales](../apps/catalog/promotion_forms.py) | 2 |
| [Modelos promocionales](../apps/catalog/promotion_models.py) | 3 |
| [Modelos de pedidos](../apps/catalog/promotion_order_models.py) | 3 |

Cada nodo nuevo identifica Padre.Meta, ubicación y fin exactos. Se verificó cada arista original de padre/archivo:35contains antiguas se sustituyen por56, sin salidas del alias que requieran otra resolución. Siete nodos se sustituyen por28; incremento neto21nodos y21relaciones. Todos los demás nodos y relaciones permanecen idénticos antes del refresco documental. Se conservaron48Meta del [corte337](296-conciliacion-relaciones-ambitos-ast-b00-20261024.md), cuatro decoradores y siete bases cualificadas del corte338; el sello comprueba las fuentes, atributos y nuevas contenciones para detectar regresión.

Es una reparación del grafo, no de aplicación ni prueba de comportamiento Django. No se importaron módulos, aplicaron migraciones o ejecutaron pruebas funcionales. No se modificó graphifyy globalmente: una extracción futura puede reintroducir la colisión y exige revalidación. Las comunidades se conservaron; no hubo nueva detección global. Un primer censo exploratorio no trató source_file=null y falló antes de producir cambios; se corrigió el filtro, se registró el límite y el censo definitivo completó sus1.346rutas.

## Disposición del corpus y límites

El [registro por fuente](evidencias/b00-current-source-review-ledger-20261023.json) pasa de293a295disposiciones verificadas y de dos a cero lecturas pendientes del inventario capturado. Base293SHA `bb82c74de6c1936cabf566657ce303a537c882c1fa7dc84d647a574604ede366`; resultado295SHA `4bcf6d33e29b899e7ac07d28f03e87d6fc884aa2e354320bdf25dc794abc0cd9`. Las293entradas anteriores y sus alcances se preservaron; se añadió revisión estructurada a las dos pendientes. captured_source_dispositions_complete=true; whole_corpus_reviewed=false conserva la distinción frente a cuerpos originales ausentes, nuevas entradas remotas no verificadas y requisitos finales no conciliados. B00_accepted=false.

El inventario295es el corte capturado y contrastado; no se afirma un nuevo censo remoto actual. Las limitaciones de capturas legales, originales judiciales no disponibles, proveedores y G01–G08 permanecen explícitas. Un hallazgo externo o una propuesta no se adopta por estar en el corpus. B15 conserva preferencias opcionales elegidas, cookies propias para visitante y evaluación de almacenamiento privado cifrado para cuentas, sin elegir backend, claves/retención ni autorizar seguimiento conductual por esta revisión.

## Conciliación final pendiente

La [salida del roadmap](103-roadmap-beta-clasificados-20261020.md#etapa-0-consolidar-el-alcance) exige cruzar hallazgos con contrato, DAFO y fuentes actuales, y completar una matriz de decisión, estado actual, objetivo, archivos, migración y aceptación. La matriz AD01–AD11 de[104](104-consolidacion-contrato-beta-b00b01-20261020.md#matriz-de-adaptación-y-evidencia-de-implementación) conserva observaciones iniciales del20deoctubre; hay que conciliarlas con [B02–B03](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md) y[B04–B06](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md) y actas posteriores, sin presentar observaciones históricas como defectos vigentes. Para cada decisión abierta, distinguir bloqueo de implementación y exclusión de beta.

La hipótesis de autoridad posterior al bloqueo en [revisión de cobertura](../apps/safety/rights_access_coverage_review.py), ya señalada en338, sigue sin reproducción: existen reautorizaciones antes de devolver y al final. Los nombres históricos de pruebas no demuestran el intercalado actual ni una fuga; contrastar invariantes y reproducción PostgreSQL propia antes de afirmar defecto. No se ejecutó una nueva batería funcional por estas lecturas.

Artefactos de este corte: `artifacts/beta-promotion-fix-20261020/b00-339-*`, scripts de preparación/contraste y extractos por parte; verificadores fijados a su base y no ejecutables a ciegas contra un ledger posterior. Integración semántica393 de este documento y estado vigente, AST restante retenido. La conciliación de capturas no cierra B00 ni acepta beta, capacidad, seguridad global o producción. Continúan B08–B11 yB14–B17; B15 opcional. Sin publicación, proveedores, gasto o datos reales.
