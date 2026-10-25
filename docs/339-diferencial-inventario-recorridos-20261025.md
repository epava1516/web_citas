# Diferencial del inventario de recorridos — 25 de octubre de 2026

Base preservada: [111](111-inventario-rendimiento-recorridos-beta-20261020.md), SHA256 `380b026c51b5e9647052838bb77a0712e9efff4ccdd857b5df3d4b545d921a95`. Resultado separado: [inventario338](338-inventario-acciones-recorridos-alpha-20261025.md) y [censo completo](evidencias/inventario-acciones-final-20261025.json). Se parte del grafo reconstruido y auditado, no se arrastran sus estados como pruebas de ejecución.

## Comparación trazable

El original111 citaba el ensayo20261020-111928-b91538fc. Se recupera su manifiesto de fuentes como testigo fechado; no se finge que111 guardó un listado de todas sus acciones o la hora exacta de su inspección manual. Doce archivos de rutas/tareas son idénticos porSHA: los conjuntos de170 rutas nombradas y27 tareas conservan identidad frente a ese testigo, no sólo cantidades iguales.

No se añadieron, retiraron o modificaron declaraciones en esos doce archivos. Esto no significa que formularios, servicios, autoridad, plantillas, datos o rendimiento permanezcan iguales. Las huellas actuales y previas de fuentes relacionadas se conservan en JSON. Cambios de archivo no prueban por sí solos cambio funcional de cada función que contiene.

Los11 comandos anteriores pasan a15: se añaden `operational_snapshot`, `operational_assessment`, `operational_events_report` y `encryption_key_inventory`; `apply_recovery_ledger` cambia y diez se conservan por bytes. No se retira ninguno de ese conjunto. Los cuatro nuevos son acciones de operación dentro de I28, no familias ficticias I29–I32.

Admin, métodos, controles y disparadores no estaban enumerados individualmente en111. Su expansión actual se clasifica como **cobertura añadida al inventario**, no como funcionalidad necesariamente añadida al producto. La misma distinción se aplica a las106 plantillas y los tres scripts propios.

| Unidad | Base | Actual | Diferencia acreditada |
| --- | ---: | ---: | --- |
| Familias I01–I28 | 28 | 28 | Identidades conservadas; evidencia y desglose ampliados |
| Declaraciones URL propias con nombre | 170 | 170 | 0 añadidas/retiradas/modificadas en archivos declarantes comparados |
| shared_task | 27 | 27 | 0 añadidas/retiradas/modificadas en archivos declarantes comparados |
| Comandos propios | 11 en testigo fechado | 15 | 4 añadidos,1 modificado,10 conservados,0 retirados |
| Admin | Pendiente de expansión | 16 patrones canónicos | Desglose nuevo, no incremento demostrado de funcionalidad |
| Patrones por idiomas y comunes | No censados | 366 totales | 334 aplicación+32Admin; no URLs concretas ni funcionalidades |
| Beat | No confundido con27 tareas | 25 declaraciones,24/25/0 por modo | Cadencias y modos añadidos al inventario |
| Controles de formulario | No desglosados | 154 valores asociados a rutas | Valores y condiciones, no154 acciones independientes |
| Señales y callbacks | Pendientes | 3 tipos de señal y14 lugares async/commit | Unidades distintas; no sumar como trabajos ejecutados |

## Disposición de las 28 familias

| ID | Familia | Diferencia frente a111 | Fuentes relacionadas cambiadas/nuevas |
| --- | --- | --- | --- |
| I01 | Listado orgánico | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I02 | Listado promocionado | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I03 | Búsquedas y filtros | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I04 | Paginación | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I05 | Ficha pública | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I06 | Entrega de imágenes | Familia conservada; métodos/dependencias/evidencia conciliados | 4 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I07 | Favoritos | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I08 | SEO y documentos públicos | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I09 | Cuenta y sesión | Familia conservada; métodos/dependencias/evidencia conciliados | 3 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I10 | Seguridad y verificación | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I11 | Panel del anunciante | Familia conservada; métodos/dependencias/evidencia conciliados | 0 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I12 | Edición del perfil | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I13 | Subida de fotografías | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I14 | Procesamiento fotográfico | Familia conservada; métodos/dependencias/evidencia conciliados | 0 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I15 | Gestión de fotografías | Familia conservada; métodos/dependencias/evidencia conciliados | 1 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I16 | Revisión y publicación | Familia conservada; métodos/dependencias/evidencia conciliados | 3 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I17 | Ciclo de vida | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I18 | Agencias y representación | Familia conservada; métodos/dependencias/evidencia conciliados | 0 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I19 | Gestión comercial sintética | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I20 | Denuncias y reclamaciones | Familia conservada; métodos/dependencias/evidencia conciliados | 6 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I21 | Derechos y rectificación | Familia conservada; métodos/dependencias/evidencia conciliados | 22 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I22 | Exportación y portabilidad | Familia conservada; métodos/dependencias/evidencia conciliados; FAILtemporal MOD09 y selecciónTCP dispuestos por separado | 8 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I23 | Avisos y comunicaciones | Familia conservada; métodos/dependencias/evidencia conciliados | 6 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I24 | Publicación en segundo plano | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I25 | Limpieza y recuperación | Familia conservada; métodos/dependencias/evidencia conciliados | 13 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I26 | Navegador y entrega web | Familia conservada; métodos/dependencias/evidencia conciliados | 2 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I27 | Infraestructura transversal | Familia conservada; métodos/dependencias/evidencia conciliados | 12 archivos; detalle SHA en JSON, no equivalencia transitiva |
| I28 | Operación administrativa | Familia conservada; métodos/dependencias/evidencia conciliados;4 comandos nuevos y expansiónAdmin | 24 archivos; detalle SHA en JSON, no equivalencia transitiva |

## Cambios relevantes y deuda

El contrato adapta el perfil romántico y preserva historia privada, autoridad fresca, revisión y ciclo de vida. La evidencia actual añade la regresión funcional/capacidad conciliada de B16, variantes explícitas y carga contractual vigente. No se convierte la antigua columna «por conciliar» en un PASS universal: el inventario actual conserva límites por escenario, versión y método.

B07/B08/B09 mantienen optimizaciones aceptadas con sus comparaciones; B10 queda resuelto como evaluación/disposición, con deuda MOD09 y detector exacto. B14/B15/B17 se trasladan según336, sin aceptación de proveedores, personalización o apertura. El inventario y su primera cola de medición/optimización son la primera prioridad del siguiente contrato; QA específico sigue aplazado a la primera versión estable/productiva.

El documento111 y sus propuestas de presupuestos no se modifican. No se eleva un objetivo propuesto a contrato ni se repite una prueba válida para actualizar este registro. Una revisión futura que cambie código, escenarios o exposición deberá actualizar las huellas, la evidencia y este diferencial.

## Entrega y aceptación documental

Se requiere comprobar identidad I01–I28, conjuntos de rutas/tareas, vínculo de cada fila a fuente/familia/evidencia, huellas, referencias de plantillas y límites de Admin/modos. La integración semántica de338/339 y del seguimiento/roadmap se realizará sobre el grafo nuevo, declarando el alcance focal y sin presentarlo como una segunda reconstrucción desde cero. El acta final sólo se emitirá después de esa comprobación. El proyecto sigue en alfa.

