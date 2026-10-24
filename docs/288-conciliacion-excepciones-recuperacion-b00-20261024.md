# B00-329 — Excepciones, publicación y recuperación

Fecha: 2026-10-24. Conciliación de pruebas históricas y corrección vigente de comprobación caducada.

B00-329: 266 de 295 fuentes únicas conciliadas; quedan 29 de arquitectura. Se incorporan pruebas5–6 de finalidades, promociones, publicación y recuperación. Corregido consumo de excepción con comprobación caducada durante la lectura de fuente: reproducción con un fallo y regresión PostgreSQL de16pruebas aprobadas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Defecto reproducido y corrección

En `apps/safety/purpose_exceptions.py`, consume comprobaba la prueba de identidad/ámbito antes de reconstruir el manifiesto y verificar la aprobación. Ese trabajo podía superar su vigencia. La autorización del actor se recargaba al final, pero no volvía a comprobarse la prueba antes de consumir la aprobación y permitir la supresión.

Se añadió [una regresión](../tests/test_purpose_exception_consumer_freshness.py) que construye la excepción y el expediente reales de la fixture PostgreSQL y avanza sólo el reloj del consumidor de pruebas después de leer el manifiesto. Los relojes de la propuesta y del resto del dominio conservan su valor, aislando la caducidad de la prueba. El negativo terminó con DID NOT RAISE ValidationError: la operación no rechazó la prueba caducada. Es una intercalación de reloj controlada, no un callback concurrente real o una comprobación de proveedor externo.

La corrección vuelve a exigir la misma prueba vigente inmediatamente antes de guardar consumed_action. El rechazo revierte la acción y mantiene la aprobación sin consumir, el favorito, la restricción y la versión del expediente. Se conservan el flujo válido y el replay de una ejecución completada; no se levanta la medida ni se cambian plazos para obtener un resultado positivo.

| Ejecución | Resultado verificado | Alcance |
| --- | --- | --- |
| `20261024-004232-7a934dc1` | Un FAIL esperado, cero errores/omisiones; runner ERROR | Reproducción con código sin corregir y PostgreSQL17/Redis7.4 propios |
| `20261024-004510-b17f1e9c` | 16PASS, cero fallos/errores/omisiones, tres workers | Nueva caducidad; consumo/replay/rollback; revocaciones tras bloqueos, medida nueva y ejecución de supresión |

[Auditoría de corrección](evidencias/b00-329-exception-proof-freshness-20261024.json): selección, hashes congelados iguales a cada plan, JUnit, pasos de calidad/migraciones y recibos terminales comprobados. Se verificó de forma independiente ausencia de los cuatro contenedores exactos y de los temporales de ambas ejecuciones. Sin cambios de esquema, proveedor real, carga o nueva aceptación global de runtime/beta.

La primera auditoría auxiliar falló porque buscaba No such con mayúscula y Docker devuelve no such object. Se corrigió el cotejo y se añadió inventario filtrado exitoso/vacío; la auditoría corregida pasó sin repetir las pruebas de producto. Se conserva ese ERROR y su recibo en los artefactos. Ruff ordenó los imports del nuevo test antes de congelar el negativo; no fue un fallo funcional ni se ocultó un intento de pytest.

## Lectura y procedencia

Seis lectores nativos de sólo lectura cubrieron600.897caracteres en seis partes y54emisiones literales individuales de hasta12.000caracteres, como máximo tres lectores simultáneos. Sin truncamientos o reparaciones delegadas declaradas. Los informes guardados son extractos seleccionados marcados, no transcripciones íntegras. Cero nuevas invocaciones ClaudeV1; ocho históricas y consumo anterior conservados, sin estimación nativa.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Pruebas5/11 | `source:24ryblhxpu6ouhzup2ux` | 325078 | [0,108359), [108359,216718), [216718,325078) |
| Pruebas6/11 | `source:pxguflbxnnx8cnpe5a4b` | 275819 | [0,91939), [91939,183879), [183879,275819) |

SHA completos: `1b6199824ee72f25de33dd3df651c84aa59b33d22afd8508a4d8c223abbf5fbf` y `4b73c80de0484e79dc160141209e28563308e2503f31d9532502f5ea53dd2e75`. Snapshot11/10/base7e04016, con formato transformado; no se acredita identidad con bytes ejecutables actuales. Imports, fixtures y artefactos referidos no reciben crédito de lectura por su referencia.

El principal cotejó las seis huellas de parte y doce citas declaradas, inspeccionó fronteras y contextos. El verificador realizó catorce cotejos sobre esos doce intervalos, verificó uniones completas y revalidó hashes/longitudes de las295capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de264a266disposiciones y de31a29pendientes, con base264fijada, reemplazo atómico y permisos conservados. La aceptación de disposición exige además la auditoría de corrección16PASS. Artefactos: `artifacts/beta-promotion-fix-20261020/b00-329-*`.

## Contenido y límites preservados

La captura5 cubre cautelas de privacidad y levantamiento comunicado, logging y fotos privadas, planes/revisión/ejecución por finalidad, publicación sin cuenta, respuestas parciales, promociones/pedidos/exposición, SEO/JSON-LD, contextos de validación, calendarios y estado derivado. La captura6 continúa estado/TCP/upgrades, calendarios/excepciones y levantamientos, inventarios, comunicación, recuperación/ledger/checkpoints/medios/PostgreSQL/worker y rectificación/localización.

Preparar o revisar una excepción no autoriza por sí solo la operación ni levanta restricciones. Una fecha de seguimiento vencida tampoco libera la medida. El levantamiento requiere su recorrido independiente, comunicación/recepción y prueba posterior; reabrir o liberar no republica automáticamente. Los cambios de autoridad después de bloqueos deben provocar rechazo sin efectos.

La promoción sintética no acredita compra, pasarela, fiscalidad o proveedor real. La exposición debe respetar el conjunto elegible/filtrado; una autosubida conserva el estado editorial y sus cuotas. Invocar una tarea síncronamente no acredita worker/Beat. SEO y JSON-LD derivan de contenido público aprobado y preservan la privacidad; los tests de navegador con datos sintéticos no se convierten en revisión jurídica o despliegue real.

La lectura pública depende de relaciones, permisos, reglas y recursos más allá de revision/edit_version/updated_at. Las comparaciones nativa/almacenada, fixtures positivos sintéticos y TCP secuencial tienen alcances distintos. Una cola de100proyecciones no equivale a100procedimientos revisados; el proveedor synthetic-coverage no es verificación externa. No sumar intervalos inclusivos, muestras diagnósticas o fixtures diferentes como capacidad contractual.

La recuperación verifica integridad y referencia de autoridad independiente, ámbitos y sufijos atómicos, recursos compartidos y replay. Los tests que reconstruyen un backup mediante ORM y los que describen pg_dump/pg_restore son evidencia distinta; leerlos no acredita ejecución. Un resultado publication_authorized false no habilita exposición. Los umbrales de una fixture local no prueban RPO/RTO operativo a escala real.

## Contraste actual y grafo

Se contrastaron once archivos y veinticinco literales: diez módulos de pruebas —incluida la nueva regresión— y las funciones completas proposal_contents/consume de `purpose_exceptions.py`. Esto fija el ámbito de los checks actuales; no equivale a ejecutar todas las pruebas capturadas. La reproducción y regresión nuevas son evidencia separada con sus propias versiones, resultados y límites. No se duplica aceptación anterior ni se cuenta presencia de asserts como PASS.

Grafo382 revalidado antes del análisis. AST dirigido del nuevo test antes del negativo y de purpose_exceptions tras la corrección, con sellos antes de congelar cada selección. Integración final por semántica dirigida383; sin AST global, semántica exhaustiva o HTML global. El descriptor del sello aclara que se conserva AST dirigido y que sus refrescos por corte se registran aparte, evitando afirmar que no hubo AST nuevo en este trabajo.

Quedan29fuentes de arquitectura,21.625.091caracteres: pruebas7–11, interfaz, herramientas, referencias y grandes grafos. Continuar lectura acotada y contraste vigente; conteos no son porcentaje de esfuerzo. B00 abierto, nueve de18puntos beta cerrados y B15 opcional. Se conservan límites legales y de producción; sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación287](287-conciliacion-pruebas-privacidad-b00-20261024.md).
