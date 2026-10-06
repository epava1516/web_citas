# Medición del avance del contrato

## Corrección del seguimiento

Las cifras82% CR09 y56% contrato eran estimaciones sin desglose de pesos ni denominador verificable. Repetirlas tras entregas nuevas no permite medir avance: quedan como referencia histórica, no como medición actual. No sustituirlas por otra cifra subjetiva.

El contrato16 define15 hitos: BASE, CR01–10, GS01, BF, BB y C. El seguimiento17 declara BASE yCR01–08 verificados localmente:9/15,60% del número de hitos. Este cociente asigna el mismo peso a todos, no mide horas, complejidad, trabajo completado ni preparación de producción. CR09 sigue abierto, por lo que su trabajo parcial no cambia este contador. No afirmar que falta40% del esfuerzo.

## Avance verificable dentro de CR09

La aceptación de CR09 requiere la matriz residual de docs83, además de los recorridos funcionales y sus pruebas. Un requisito puede contener varias implementaciones, variantes y dependencias; un número de tests no mide cuánto trabajo falta.

Registrar para cada requisito: implementación entregada y commit, pruebas actuales y versión, evidencia, variantes pendientes, dependencias externas y condición concreta de aceptación. Distinguir estados pendiente, implementación parcial, verificado en alcance limitado y aceptado. No declarar aceptado todo un derecho por haber probado una operación.

Entregas recientes verificables:

- b50e69f: aplicador0100, destrucción física, comando operacional, restauración real PostgreSQL y aislamiento HTTP/worker/Beat;67 pruebas conjuntas y runtime verificado.
- c004262: trazabilidad de sustitutos firmados para fotos compartidas y dos eventos consecutivos;76 pruebas conjuntas, runtime actualizado y push confirmado.
- Entrega posterior de autoridad0100: validación compartida de sustituto vacío/privado y checkpoint esperado independiente;80 pruebas conjuntas correctas320,56s y Docker verificado.

Estos avances son reales aunque el hito siga abierto. Los defectos reproducidos y corregidos también son progreso hacia aceptación, pero no permiten estimar automáticamente cuántas horas o qué porcentaje quedan.

## Porcentaje de trabajo

Antes de publicar otro porcentaje de trabajo, descomponer todos los requisitos del contrato en unidades de aceptación concretas, asignar pesos con una base explícita, evitar contar dependencias o pruebas repetidas como entregas nuevas y mantener un denominador estable. Cada cambio de alcance/peso debe registrarse. Hasta que exista esa matriz, informar entregas y pendientes concretos; porcentaje de esfuerzo no disponible.

El contador de hitos y la aceptación de producción permanecen separados. Proveedores, revisión jurídica y gates de producción no se acreditan por pruebas sintéticas locales.

## Baseline ponderada v1 solicitada por el usuario

Se adopta una estimación por alcance y complejidad. Los pesos y grados de avance son juicio técnico explícito, no horas medidas ni aceptación formal. Referencias: contrato16, seguimiento17, matriz83 y recursos87. Los porcentajes antiguos82/56 no se reutilizan. Fórmula: suma(peso × avance estimado /100). Pesos100 en cada nivel; no cambiar denominador por repetir pruebas.

### CR09

| Bloque | Peso | Avance estimado |
| --- | ---: | ---: |
| Portabilidad y respuesta privada | 15% | 90% |
| Purga de contenido caducado | 5% | 100% |
| Flujos de denuncias y derechos por finalidad, verificación y autoridad | 20% | 65% |
| Conservación y destrucción por finalidad | 10% | 50% |
| Restauración de datos y medios | 15% | 85% |
| Sesiones, cachés, colas, logs y recursos externos | 10% | 45% |
| Comunicaciones y destinatarios | 8% | 50% |
| Atención urgente y escalado | 7% | 60% |
| Rendimiento de expedientes grandes | 5% | 30% |
| Aceptación integral CR09 | 5% | 0% |

El bloque de flujos incluye formularios públicos/colas de denuncias, expediente/verificación/autoridad y acceso/rectificación/supresión/limitación/oposición, para no ponderar únicamente lo que queda de recuperación. Portabilidad y purga poseen evidencia de entregas específicas; otros derechos siguen con aceptación por finalidad pendiente. Restauración incluye ensayos reales locales y recibos firmados; recursos locales incluyen trabajo de sesiones/colas aún sin entregar. Comunicaciones/escalado/rendimiento siguen parciales y aceptación integral no completada. Esta valoración inicial debe revisarse contra cambios concretos, sin presentar cada grado como un dato medido.

Resultado CR09:63,45%, comunicar **aproximadamente63% completado y37% pendiente**.

### Contrato completo

| Hito | Peso | Avance estimado |
| --- | ---: | ---: |
| BASE | 5% | 100% |
| CR01 | 4% | 100% |
| CR02 | 6% | 100% |
| CR03 | 6% | 100% |
| CR04 | 5% | 100% |
| CR05 | 8% | 100% |
| CR06 | 6% | 100% |
| CR07 | 6% | 100% |
| CR08 | 4% | 100% |
| CR09 | 15% | 63.45% |
| CR10 | 5% | 0% |
| GS01 | 3% | 0% |
| BF | 10% | 0% |
| BB | 10% | 0% |
| C | 7% | 0% |

BASE/CR01–08 aportan50 puntos del contrato; CR09 aporta9,5175. Resultado59,5175%, comunicar **aproximadamente60% completado y40% pendiente**. CR09 representa15% del peso total. GS01, BF, BB y C tienen pesos propios para no equiparar un flujo pequeño con acabado y entrega. No afirmar que esas fases están iniciadas por tener componentes reutilizables de la fase cruzada.

[Datos y cálculo](evidencias/avance-ponderado-v1.json). Esta baseline sustituye la ausencia de estimación de trabajo anterior, pero no altera el contador de hitos ni declara CR09 aceptado. Los pendientes externos de producción siguen diferenciados de pruebas sintéticas/locales.

## Revisión del avance con Git solicitada por el usuario

Revisión sobre HEAD036a1a0 y remoto master confirmado al mismo hash. Desde83c9d63 hay tres entregas:

| Commit | Cambio funcional | Efecto en cierre del contrato |
| --- | --- | --- |
| b50e69f | Aplicador tipado, destrucción física, restauración real y aislamiento HTTP/worker/Beat | Recuperación antes pendiente ahora implementada/verificada localmente; CR09 no aceptado |
| c004262 | Sustitutos firmados y recuperación de eventos consecutivos | Corrige un defecto reproducido y conserva fotos ajenas; no añade un hito cerrado |
| 036a1a0 | Checkpoint esperado independiente y validación común de preflight/aplicación | Refuerza consistencia/autoridad; sigue pendiente custodia externa y aceptación integral |

El diff83c9d63..036a1a0 contiene46 archivos,2837 inserciones/47 borrados, incluyendo aplicación, pruebas y evidencias. Son señales de actividad y entregas concretas, no una medida de esfuerzo o aceptación. El historial anterior también concentra commits en portabilidad/derechos; las tres últimas entregas siguen dentro de recuperación de CR09. No se ha avanzado a CR10 ni cerrado otro hito durante este tramo.

Conclusión: avance funcional real y comprobable, sin bloqueo técnico; concentración prolongada en un subsistema y ritmo de cierre de hitos bajo. No presentar repetir regresiones o documentar un mismo componente como requisitos distintos terminados. Próximo: concluir entrega de sesiones/colas actualmente en verificación y trabajar la matriz restante de derechos/finalidades. No ampliar recuperación con requisitos inventados; resolver defectos/requisitos concretos conservando el alcance del contrato.
