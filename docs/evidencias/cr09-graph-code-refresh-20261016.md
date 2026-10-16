# Actualización parcial del grafo de código

Siete archivos Python cambiados entreaba6cb4 ybaeb062 reextraídos porAST, con resolución de llamadas usando contexto inmutable de archivos no cambiados. Segunda pasada usa `graphify.extract.extract` completo; la pasada inicial por archivo no resolvía llamadas cruzadas y se sustituyó antes de cerrar esta evidencia. Manifiesto AST sellado sólo para esos siete archivos. No semántica de docs/Dockerfile ni nuevo test de conteo todavía sin commit.

Resultado:11316nodos/44710aristas/541comunidades;0extremosdangling,131selfloops conservados. [Recibo](cr09-graph-code-refresh-20261016.json). JSON/reporte persistentes en graphify-out; sin HTML en este grafo grande. Reclustering local sin etiquetas LLM. Coste de modelo deAST0, consumo semántico histórico/nativo desconocido preservado y señalado en reporte, no totalcero inventado.

El exportador rechazó inicialmente una reducción neta de un nodo. Se inspeccionó la diferencia completa: siete IDs de módulo migraban/normalizaban, con seis IDs añadidos y deduplicación exacta de módulo ya existente. Cada source_file+label retirado tiene nodo sobreviviente equivalente, comprobado antes de permitir la exportación reducida. Copias automáticas anteriores conservadas; no reducción masiva aceptada sin revisar.

La primera actualización AST/clustering se solapó por error con el contraste de conteo012245-4af75967. Sus tiempos se marcan condicionados y se conserva el error. El contraste se confirmó una sola vez sin otra actividad propia,012540-47dda797, antes de la segunda pasada/resolución final del grafo. No nueva carga HTTP ni aceptación CR09/N3. El grafo orienta navegación, no sustituye revisión de fuente/pruebas.
