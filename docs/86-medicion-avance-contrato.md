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
