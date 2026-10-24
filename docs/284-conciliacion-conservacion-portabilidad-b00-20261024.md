# B00-325 — Conservación, portabilidad y diseños de capacidad

Fecha: 2026-10-24. Conciliación documental y contraste estático seleccionado.

B00-325: 258 de 295 fuentes únicas conciliadas; quedan 37 de arquitectura. Se incorporan documentación y contratos 5–6: conservación, restricciones, portabilidad, recuperación y diseños de capacidad. Aclarada la precedencia de CR09 y de la estimación v10, preservando originales. Sin cambios de aplicación o nueva aceptación funcional. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y procedencia

Seis lectores nativos de sólo lectura cubrieron 651.656 caracteres en seis partes, mediante 57 emisiones literales contiguas de hasta 12.000 caracteres. Cada contexto asignado tiene menos de 120.000 caracteres y hubo como máximo tres lectores simultáneos. No se declararon truncamientos ni reparaciones. Los informes persistidos son extractos seleccionados y marcados, no transcripciones completas. Cero nuevas invocaciones ClaudeV1; consumo previo conservado, sin estimación de tokens nativos.

| Captura | Fuente | Caracteres | Particiones contiguas |
| --- | --- | ---: | --- |
| Documentación5/8 | `source:ym5wrm6l60s5izkhzh4v` | 345446 | [0,115148), [115148,230297), [230297,345446) |
| Documentación6/8 | `source:oramqyj377mpsym4wfnd` | 306210 | [0,102070), [102070,204140), [204140,306210) |

SHA completos: `361181c17d01e9aae3885ae05c1d91cc31ad1f78a0e39db3d5c42fbe4e5b3157` y `d9fb00545bfb1fc1e13ec7378bb09da06a554e8634f674cedef73571077afba9`. Snapshot11/10/base7e04016, con transformación de formato: no se acredita identidad con bytes canónicos actuales. Los documentos, pruebas, commits y servicios referidos no reciben crédito por aparecer enlazados. Ningún handle, cola, comando o pausa histórica se reactiva.

El principal inspeccionó fronteras y doce citas con contexto. El verificador hizo catorce cotejos sobre esos doce intervalos, unió las partes sin huecos y revalidó integridad de las 295 capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de256a258 disposiciones y de39a37 pendientes, mediante reemplazo atómico que conserva permisos y exige la base256 fijada o su resultado idéntico. Artefactos: `artifacts/beta-promotion-fix-20261020/b00-325-*`.

## Contenido conciliado y límites

La captura5 abarca docs57–85: seguimiento de conservación, restricciones/oposición y levantamiento comunicado, calendarios, excepciones acotadas, inventarios seleccionados, publicación por finalidad, copias paginadas, revisión independiente, conjuntos mixtos de portabilidad, binarios, cobertura, cierre y recuperación. La caducidad operativa no levanta una medida. Una excepción puntual consumida por supresión no habilita favoritos ordinarios. Una selección de metadatos no autoriza los bytes de una imagen.

Transporte fragmentado y revisión paginada no prueban memoria acotada de toda la generación. La coherencia declarativa de covered/complete no acredita verdad jurídica o revisión independiente. La aprobación operativa de información no aprueba jurídicamente la política ni resuelve el expediente. Consulta, revisión, ejecución, respuesta, borrado y cierre mantienen sus autoridades y versiones propias. Un acuse simulado y una respuesta HTTP registrada no prueban recepción humana o identidad real.

La recuperación exige conciliación fuera del backup restaurado, referencia de autoridad vigente, controles de ámbito y destrucción física separados. Validar una referencia suministrada no acredita su procedencia externa. Los ensayos PostgreSQL/medios locales no prueban custodia externa, cadencia productiva o RPO/RTO universal. Fallos, correcciones y resúmenes posteriores conviven en las capturas; los pendientes antiguos no se convierten automáticamente en defectos actuales.

La captura6 abarca docs86–97, índice, ADR, DAFO histórico, CI local y contratos01–09. Conserva estimación ponderada v10, recursos de recuperación, comunicaciones/Redis, propuestas de terceros, estado de publicación, sello enumerativo sustituido, MOD08, objetos privados/proxy y la propuesta CC05. Un diagnóstico de un caso no acredita p95 ni dos casos simultáneos. Los FAIL/INVALID, variantes SQL rechazadas y controles limpios conservan sus diferencias; no se suman deltas marginales ni suites separadas.

El diseño enumerativo de doc94 fue sustituido por reproducción de consultas de MOD08; tampoco se adopta el prototipo de read-repair o la propuesta de similitud desde su texto histórico. La experiencia de objetos AEAD/S3/proxy conserva sus pruebas y límites específicos; no decide por sí sola el almacenamiento de preferencias B15. Los contratos profesionales capturados ceden ante la adaptación romántica vigente. No se seleccionan servicios, dependencias o proveedores por estas referencias.

## Contraste y correcciones actuales

Once archivos actuales y veinticinco literales se contrastaron estáticamente: diez documentos y cuatro funciones de `apps/safety/purpose_release.py` (permission, locked, current y execute). Las funciones seleccionadas distinguen autorización independiente, bloqueo de ámbito/medida/sujeto, lectura y comprobación vigentes, propuesta concreta, recepción y prueba posterior. Esta lectura estática no sustituye una prueba de concurrencia o vigencia bajo cada intercalación posible y no acredita todo el subsistema de derechos.

Se añadieron dos notas fechadas, conservando íntegros sus originales:

- [Portabilidad82](82-portabilidad-cobertura-entrega-cierre.md): la mención de CR09 abierto pertenece al corte antiguo; prevalece [acta05](actas/05-cr09-aceptacion-tecnica-local-20261018.md) para su aceptación técnica local y [acta10](actas/10-entrega-tecnica-local-alpha-20261020.md) para el alfa posterior, sin extenderlas a beta o producción.
- [Medición86](86-medicion-avance-contrato.md): v10 mantiene fecha, denominador y grados; no representa el producto adaptado. Los conteos de fuentes o puntos no se convierten en porcentaje de esfuerzo y no se recalculan pesos para inflar avance.

El verificador reconstruye las dos versiones previas y coteja sus hashes. Ambas páginas siguen excluidas del manifest y semántica del grafo activo. Las notas remiten al seguimiento y roadmap sin importar toda su historia a la selección semántica. No hay nuevo defecto de aplicación demostrado por este contraste ni cambios de código, migraciones, pruebas funcionales o cargas en este corte.

## Grafo y continuación

Grafo378 revalidado antes de analizar; integración mediante semántica dirigida379. Sin extracción AST nueva, semántica exhaustiva o HTML global. Las correcciones320–322 y B07 conservan sus auditorías, negativos, fallos y aceptación originales; este trabajo documental no repite ni amplía sus mediciones.

Quedan37capturas de arquitectura,23.916.857caracteres: documentación7–8, pruebas, interfaz, herramientas, referencias y grandes grafos. Continuar lectura acotada y contraste contra fuentes actuales. B00 abierto, nueve de18puntos cerrados y B15 opcional. Se conservan límites de capturas legales y preparación de producción. Sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación283](283-conciliacion-derechos-grafo-b00-20261024.md).
