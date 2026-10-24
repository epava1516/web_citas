# CC-05 — evaluación pendiente de recuperación de fotos similares

Fecha: 2026-10-10. Estado: propuesta documentada por petición del usuario para ponderar cuando se aborde este frente. No hay implementación, dependencia elegida, benchmark propio ni mejora de tiempo acreditada. Se conserva primero la entrega MOD-08 actual; esta propuesta no cambia sus objetivos ni crea una aceptación de fase.

## Problema observado y alcance

El hallazgo [CC-05 del análisis](92-analisis-claude-code-20261008.md) sigue visible en [detect_matches](../apps/mediafiles/services.py): después de obtener fotos elegibles y la firma de la foto nueva, recorre los Blob ready con fotos candidatas, deserializa cada firma y llama compare_signatures. Sólo después de un candidato perceptual abre el derivado y ejecuta confirm_match, seguido del registro ORM con comprobaciones actuales. La confirmación visual es ORB/regional; ORM es el acceso a la base de datos, no el nombre de ese algoritmo.

Hipótesis a medir: recuperar previamente un conjunto menor de candidatos podría ahorrar deserialización, comparaciones y consultas posteriores. Esto afecta al procesamiento de subidas y duplicados, no al listado público ni a las dos optimizaciones SQL de evidencia/metadatos de la entrega actual.

Los pHash son valores binarios de 64 bits. La [firma actual](../apps/mediafiles/similarity.py) incluye hash completo, rotaciones y ventanas de recorte; compare_signatures prueba hash completo (distancia máxima 12), rotaciones (10) y recortes en ambas direcciones (10), excluyendo firmas sin información suficiente. Indexar sólo Blob.phash puede perder candidatos detectados hoy. retrieval_hashes tampoco debe asumirse equivalente al comparador sin comprobar todas esas relaciones, especialmente las rotaciones.

## Alternativas que se ponderarán

| Alternativa | Qué comparar | Coste o condición pendiente |
| --- | --- | --- |
| Recorrido exacto con firmas binarias compactas | Referencia sencilla; separar coste Python/ORM de distancia de Hamming | Sigue recorriendo el conjunto; medir si basta sin un índice adicional. |
| BK-tree u otra recuperación exacta por radio Hamming | Construcción, consultas por radio y cobertura de todas las variantes de firma | Evaluar con corpus real sintético, distribución y radios actuales; no prometer complejidad ni velocidad sin medir. |
| FAISS binario | Índice exacto como referencia y alternativas indexadas como experimentos | La documentación oficial distingue IndexBinaryFlat, exhaustivo, de otros índices binarios. Elegir FAISS no implica automáticamente evitar O(N); contabilizar RAM, reconstrucción, borrados y compatibilidad nativa. [Fuente](https://github.com/facebookresearch/faiss/wiki/Binary-indexes). |
| PostgreSQL con pgvector y bits | Distancia Hamming y coste de integrar la recuperación con filtros transaccionales | Su documentación distingue búsqueda exacta e índices aproximados y ofrece Hamming para bits. El índice HNSW no garantiza conservar por sí solo todos los candidatos actuales. Extensión y migraciones pendientes de decisión. [Fuente](https://github.com/pgvector/pgvector). |
| LSH u otros índices aproximados | Recuperación, falsos negativos y coste de mantener un respaldo exacto | No aceptar un top-k fijo o búsqueda aproximada que omita coincidencias existentes sin una decisión explícita sobre ese cambio de comportamiento. |

Las fuentes externas se consultaron el 2026-10-10; describen capacidades, no resultados de este proyecto. No se propone convertir los hashes a embeddings semánticos ni introducir reconocimiento facial.

## Condiciones de evaluación y decisión

1. Perfilar detect_matches con corpus sintético versionado, tamaño creciente y presupuesto de CPU/RAM definido. Medir tiempo p50/p95 completo de procesamiento, SQL, firmas deserializadas, candidatos, confirmaciones visuales, memoria y coste de altas/bajas/reconstrucción. Separar búsqueda de la confirmación ORB y de esperas de cola. Conservar referencia exhaustiva en el mismo código, población y recursos; ningún porcentaje de mejora se presupone.
2. Comparar conjuntos contra compare_signatures para duplicados exactos, cambios de escala/compresión, giros y recortes en ambas direcciones, imágenes uniformes y negativos. Para mantener el comportamiento, la recuperación debe entregar un superconjunto de los candidatos existentes; una prueba finita sin pérdidas no basta para justificar una garantía universal de un índice aproximado. Resolver radios inclusivos, endianidad, identificadores, deduplicación por Blob y límites antes de elegir tecnología.
3. Mantener compare_signatures/confirm_match y las comprobaciones ORM actuales después de recuperar candidatos. Conservar detección exacta por SHA, exclusiones de rectificación y rights-stage, fotos retiradas y comprobaciones de pertenencia/vigencia bajo locks; un resultado del índice no autoriza lectura ni registro.
4. Verificar PostgreSQL real y carreras: subida simultánea, borrado/redacción/rectificación durante búsqueda o confirmación, crash entre commit e indexación, índice retrasado o corrupto, reconstrucción y restauración sin reintroducción. Un índice auxiliar debe poder invalidarse o reconstruirse; definir respaldo seguro cuando su integridad/frescura no se demuestre. Preservar supresión de huellas y medios, sin datos reales ni servicios contratados.
5. Ponderar beneficio medido frente a dependencia, despliegue, memoria, mantenimiento y riesgo de omisiones. Registrar entonces decisión y evidencias: adoptar, posponer o descartar. Ni esta nota ni los benchmarks externos seleccionan FAISS, pgvector, BK-tree o LSH.

## Punto de retoma

Revisar esta propuesta cuando el seguimiento priorice CC-05/procesamiento de medios, después de terminar y medir la integración actual. El [seguimiento](17-seguimiento-desarrollo.md) sigue siendo la cola de ejecución; esta nota no incorpora una nueva tecnología ni declara cerrado el hallazgo.

## Nota de vigencia — B10, 2026-10-24

El selector usa actualmente EXISTS desde la corrección medida el15/10; conserva el recorrido de todos los blobs admisibles. El contraste10002Photo/cincoBlob no es una evaluación de recuperación con muchos blobs diferentes. La [descomposición308](308-descomposicion-extremos-exportacion-similitud-b10-20261024.md) separa esa evidencia y prepara diagnósticos actuales; FAISS, pgvector, BK-tree y LSH siguen sin adoptarse. Las alternativas y condiciones anteriores conservan carácter de propuesta.
