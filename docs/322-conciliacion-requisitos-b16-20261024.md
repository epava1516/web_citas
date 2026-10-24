# B16-360 — Conciliación de ejecuciones por requisito

Se contrastan los nodeids propuestos de AD01–AD11 con los reportes call de la ejecución funcional 20261024-094540-3a6ec8ac, no sólo con nombres de archivos. La [matriz de resultados](evidencias/b16-requirement-execution-reconciliation-20261024.json) preserva los identificadores y criterios.

| Requisito | Casos asociados aprobados |
|---|---:|
| AD01 Perfil romántico y preservación histórica | 29 |
| AD02 Datos, ubicación, contactos, fotos y revisión | 45 |
| AD03 Filtros y superficies públicas | 44 |
| AD04 Paridad y autoridad actual | 85 |
| AD05 Recorrido de edición y publicación | 46 |
| AD06 Renovación y estados | 41 |
| AD07 Promociones | 24 |
| AD08 Recomendaciones físicas opcionales | 0, no implementado |
| AD09 Autorización, gestión y comprobaciones | 42 |
| AD10 Textos runtime y aceptación versionada | 35 |
| AD11 Inventarios, supresión y restauración | 29 |

Los grupos se solapan: no sumar sus recuentos como pruebas únicas. Las fuentes de aplicación afectadas enumeradas en cada fila conservan sus huellas; el cambio documental del roadmap en AD08 no es implementación. La inspección de los testigos de migración, tipo opcional y etiqueta declarada confirma aserciones sobre historia preservada, borrador limpio, filtros nativos/contextuales y separación de sujetos; este contraste parcial no demuestra aún exhaustividad semántica de toda la matriz.

La corrección de señal de migraciones B16-356 afecta una dependencia compartida posterior a la batería funcional. Tiene sus testigos focales y la ejecución de capacidad posterior, pero no se describe como si la batería funcional completa se hubiese repetido sobre esa versión. La conciliación final debe justificar ese límite de reutilización.

Se conserva el ERROR original funcional con sus tres fallos de mensaje esperado y su correctiva de 23 pruebas; la [conciliación315](315-regresion-funcional-terminal-correctiva-b16-20261024.md) no se convierte en una sola ejecución verde. Los [129 SKIP funcionales](316-conciliacion-omisiones-b16-20261024.md), [nueve de capacidad](321-auditoria-carril-capacidad-b16-20261024.md) y once exclusiones oficiales siguen requiriendo disposición pertinente. No se abre una nueva batería por este recuento.

El [refresco dirigido del grafo](evidencias/b16-359360-targeted-graph-20261024.json) incorpora seguimiento vigente y los documentos 320–321, conserva AST y no satisface la reconstrucción completa final. Este documento y la matriz se incorporarán en el siguiente corte dirigido. B16 sigue abierto; la aceptación de producto en alfa no equivale a apertura o capacidad contractual productiva.
