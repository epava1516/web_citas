# N02C — contraste agrupado del tiempo del guard

25 de octubre de 2026. Base4d160ad; [resultado363](363-n02-b-resultado-guard-imagenes-sello-20261025.md) conserva tiempo inconcluso:mediana menor,pero2/5parejas posteriores peores y rangos solapados. No se repite la misma medición esperando una pareja favorable: se fija antes de ejecutar una unidad de observación agrupada para reducir el peso del ruido de llamadas pequeñas. Aplicación y todos los instrumentos/oráculos anteriores permanecen byteidénticos. N00/N01aceptados2/13,N02/N06abiertos,alfa. Grafo previo1958fuentes/18378nodos/80792relaciones/SHAverificado antes de este hito; refresco focal del presente protocolo y AST nuevo antes de congelar/ejecutar.

## Diseño fijo antes de medir

Instrumento nuevo tests/test_held_seal_guard_grouped_reference.py,un caso explícito/serial. Reutiliza sin cambios la receta nativa _generated_two, el baseline literal575bytes/SHA94f391fe875267666ef2316ae5470965f9cc888481241adbb8232e72deb6761c y los observadores de locks de N02B. Dos imágenes sintéticas distintas/10554bytes en orden inversoPK,autoridad y selección/aprobación/cobertura/generación nativas; simulador externo de identidad explícito de la fixture,no proveedor real. DEBUGFalse se establece sólo antes de generar sellos,sin reasignaciones posteriores.

Seis parejas de grupos,alternando cuál variante va primero. Cada grupo contiene diez llamadas independientes al helper check,con transacción y holds/replay reales nuevos por llamada. Cada guard debe alcanzarse exactamente una vez después de sello válido; no fallback. Son120invocaciones de guard:60baseline/60candidato,240lecturas completas y480testigos de filaNOWAITdesde otro backend. Preparación/sellos/replay/sondeos de locks quedan fuera del reloj de guard; no se fuerza caché fría. No ejecutar diez guards artificiales dentro de una sola llamada/transacción.

Registrar individualmente todas las120muestras:pared,CPUdelhilo,SQLtiempo/conteo,2lecturas/hash/bytes/orden,4locks previos y digest agregado. No SQL/parámetros/UUID/datos privados. Por grupo calcular media aritmética del tiempo de sus10guards y también total; conservar cada outlier. Primera pareja de grupos separada; cinco parejas posteriores para mediana/rango de medias. No mezclar medias de grupos con las muestras individuales de363ni inferir p95/p99 de grupos.

## Criterio de decisión previo

Corrección/coste se mantienen:por invocación7SELECTbaseline/4candidato,2lecturas y todos los bytes/hash/orden iguales,cero nuevos efectos de auditoría/descarga. Las12medias de grupo no sustituyen esos120oráculos. Si falla alguno,se conservaFAILy se atribuye antes de decidir.

Contraste temporal limitado: para concluir mejora local de esta etapa agrupada, la media por llamada del candidato debe ser menor en **cada una de las cinco parejas posteriores** y la mediana de esas medias debe ser menor. Registrar también CPUySQLtiempo,primera pareja y rangos/peores llamadas de todas las muestras. No es una prueba de significación ni una garantía estadística/producción; no se inventa un porcentaje objetivo. Si alguna pareja posterior no mejora,resultado temporal sigue inconcluso; no aumentar grupos,eliminar outliers,ampliar bucle o repetir sin una hipótesis nueva. El resultado363no se reescribe.

La modificación de agrupación afecta sólo al muestreo y no cambia etapa,dataset,trabajo útil ni presupuesto354. No se compara causalmente la duraciónQA entre ejecuciones. Un resultado favorable sólo permite decidir adopción de este guard pequeño; no da por aceptados N02,MOD09,entregaHTTP,crecimiento o concurrencia de sujetos. Evaluar luego el flujo completo y otros costes;objetivos2s/5s/FAIL/excepción original intactos.

## Ejecución y evidencia

Un caso nuevo seleccionado directamente,0SKIP; no repetir los14oráculos válidos ni el negativo ya aceptado de N02B porque no cambia aplicación/fixtures anteriores. Justificar reutilización con SHA de fuentes/dependencias/instrumentos y evidencia original363. Runner focused --workers1,PostgreSQL17/Redis7.4propios,librdbv2.4.0,timeout900s,recursos sin cuotas dedicadas. Observar tiempos instrumentados,no carga/proxy/worker externo ni imágenes de tamaño MOD09.

Antes: grafo focal verificado,congelación completa de fuentes/grafo/selección/imágenes/entorno y commit. Después: JUnit/journal,120muestras/12grupos exactos y pares,digests/bytes/lecturas/SQL/locks,baseline exacto,oráculos previos intactos,recursos propios retirados y avisos terminalesTelegramsent. Publicar tabla anterior/candidato de tiempos con muestra/variabilidad/diferencia válida y estado;no convertir inconclusión enPASS. Mantener todo el contrato obligatorio abierto donde falte evidencia;sin proveedores/publicación/datos reales.
