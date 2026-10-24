# Acuerdos de alcance y prioridades — 24 de octubre de 2026

Decisiones expresas del usuario posteriores al [roadmap](103-roadmap-beta-clasificados-20261020.md). El proyecto permanece en alfa; este documento no acepta puntos pendientes ni autoriza apertura, proveedores o publicación.

## Contrato actual: B10 y MOD-09

El usuario confirma: «B10 si se debería de resolver en este contrato». B10 no se traslada automáticamente al siguiente contrato. Deben conciliarse exportación, similitud y su disposición final con las evidencias actuales.

Se mantiene íntegra la aceptación provisional de [MOD-09](16-contrato-ejecucion-desarrollo.md#mod-09--aceptación-provisional-de-rendimiento-mod-08-2026-10-12): los objetivos originales de 2/5 segundos y el FAIL histórico se conservan, y las latencias aceptadas provisionalmente no bloquean por sí solas la continuación. Resolver B10 no significa convertir ese FAIL en PASS ni revocar la excepción acordada.

Los cambios posteriores podrían haber mejorado el circuito, pero no existe todavía una medición comparable que lo demuestre. Para resolver B10:

1. Comparar las fuentes y dependencias actuales del recorrido MOD-09 con el corte medido; identificar cambios que puedan afectar consultas, imágenes, autoridad, generación y entrega.
2. Definir qué escenario vigente responde a esa incertidumbre y medirlo con PostgreSQL y las garantías originales aplicables, conservando versión, recursos y límites. Evitar repetir cargas por rutina o extrapolar mediciones de una etapa a toda la solicitud.
3. Contrastar resultados y límites con la referencia histórica; atribuir una mejora sólo si la comparación lo permite. Si queda coste relevante, corregirlo o documentar expresamente su disposición conforme a MOD-09.
4. Justificar el extremo aplicable de similitud y cerrar su disposición sin adoptar FAISS u otro índice por defecto. Conciliar evidencias y deuda residual en el cierre de B10.

Base disponible: [diagnóstico de extremos](308-descomposicion-extremos-exportacion-similitud-b10-20261024.md), [atribución de exportación](309-atribucion-circuito-exportacion-b10-20261024.md) y [composición SQL](310-composicion-sql-cobertura-b10-20261024.md). Estos diagnósticos no acreditan una mejora global actual de MOD-09.

## Próximo contrato: orientación provisional

El usuario plantea como probable trasladar B14, B15 y B17 a deuda para un contrato posterior. Es una orientación pendiente de formalizar en la conciliación final, no una aceptación técnica ni un cierre de esos puntos.

La revisión y optimización de recorridos del inventario actualizado ocuparía la primera posición del próximo roadmap. B14 conserva selección/autorización e integración real de proveedores pendientes; B15 sigue opcional; B17 queda ligado a una futura decisión de apertura.

La reconstrucción completa del grafo y la actualización diferencial del inventario de recorridos siguen siendo entregas obligatorias finales del contrato actual, en el orden de la [adenda contractual](16-contrato-ejecucion-desarrollo.md#acción-final-obligatoria--actualización-diferencial-del-inventario-de-recorridos). No se trasladan al siguiente contrato.

## Optimización de pruebas y QA

Se aplaza un inventario y contrato específico de medición, corrección y optimización de QA hasta alcanzar la primera versión estable/productiva, para concentrar el esfuerzo actual en el desarrollo principal. Se conserva el análisis ya realizado como antecedente; no autoriza iniciar ahora ese frente ni una nueva batería.

Durante el desarrollo siguen correspondiendo las correcciones de pruebas que fallen, bloqueen el avance o produzcan resultados poco fiables, y las verificaciones necesarias de los cambios. Optimizar QA no equivale a mejorar la latencia de la aplicación ni permite reducir cobertura silenciosamente.

## Corte de documentación

Acuerdo registrado durante B16-358, ejecución 20261024-154224-43b1e770. Sólo se añade este documento, fuera del manifiesto de fuentes ejecutables congeladas; no se modifican el protocolo, el grafo ni la selección de la prueba activa. Su enlace desde seguimiento/índice y su incorporación semántica al grafo quedan pendientes del resultado terminal y de la auditoría del corte congelado. No se declara actualización del grafo ni aceptación B16.
