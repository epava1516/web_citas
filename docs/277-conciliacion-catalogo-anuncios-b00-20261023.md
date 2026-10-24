# B00-318 — Catálogo y anuncios históricos frente al contrato romántico

Fecha: 2026-10-23. Conciliación de capturas y contraste estático seleccionado; no auditoría funcional global nueva.

B00-318: 243 de 295 fuentes únicas conciliadas; quedan 52 de arquitectura. Se incorporan catálogo y anuncios históricos, con 34 contrastes estáticos en 15 archivos actuales. Las diferencias profesionales del snapshot se contextualizan con la adaptación romántica existente; sin defecto vigente demostrado en esos contrastes. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y evidencia

Tres lectores nativos readonly cubrieron257.239caracteres mediante25salidas literales contiguas, de hasta12.000caracteres cada una, sin truncamientos declarados. Catálogo se leyó entero [0,72568); anuncios se dividió previamente en [0,92335) y [92335,184671). La frontera cae dentro de models.py y se continúa sin atribuir contenido ajeno a una parte. Se observan los cierres textuales de tasks.py y views.py en las respectivas colas.

| Fuente | Caracteres | SHA-256 del texto capturado |
| --- | ---: | --- |
| `source:9899ioy956pgxpp8sm8m`, catálogo | 72568 | `a1e786467e445218b789b694e31b98256667af1c4874cb60d29ef227a62a1e85` |
| `source:w5bg9ev59xmwpixsu95i`, anuncios | 184671 | `b00edc443131e99d40d58e37bc0d1e2b04b7af40b038261804fffc47058e32e2` |

El principal inspeccionó fronteras, inicios, colas y seis citas con contexto. El verificador realizó ocho cotejos en esos seis intervalos distintos, uniones y hashes declarados; volvió a verificar las295capturas del inventario. Se conservan tres informes íntegros, sin reparaciones o fuentes contadas por partes.

Plan, protocolo, informes, propuestas, contextos, contraste y auditoría están en `artifacts/beta-promotion-fix-20261020/b00-318-*`. El [ledger vigente](evidencias/b00-current-source-review-ledger-20261023.json) pasa de241a243disposiciones y de54a52pendientes. `verify_b00_318.py` deriva del316 con diff guardado y revisado; integra sólo sobre la base241 fijada por hash o resultado idéntico, mediante reemplazo atómico con permisos preservados. JSON estricto rechaza claves duplicadas y constantes no estándar.

## Snapshot y precedencia

Ambas capturas declaran snapshot11/10/2026 y base7e04016, anteriores a la adaptación romántica del20/10. Describen reglas, modelos, migraciones, vistas y tareas representadas en ese corte. La separación de tokens y el formato alterado impiden asumir identidad de bytes con los originales; se conserva el [contraste de representación anterior](276-conciliacion-mapa-configuracion-b00-20261023.md). No se ejecutan comandos o instrucciones contenidos en las fuentes.

Las referencias a modelaje, acompañamiento, masajes, servicios, recepción/desplazamiento y tarifas son antecedentes del producto profesional. No sustituyen al [contrato14](14-contrato-funcional-v1.md), ni prueban que esas dimensiones sigan ofrecidas públicamente. Las clases o archivos importados y meramente referidos tampoco quedan leídos por aparecer en el snapshot. Modelos, constraints, queries y tareas representadas no acreditan instalación de esquema, ejecución, concurrencia o rendimiento.

## Contrastes seleccionados con archivos actuales

El principal revisó15archivos actuales y fijó sus hashes y34comprobaciones literales reproducibles en `b00-318-current-contrast.json`. El verificador comprueba presencia o ausencia esperada de esos fragmentos y sus hashes. Esa selección acota las conclusiones: no es una prueba completa de rutas, permisos, dependencias, carreras o rendimiento.

| Materia | Evidencia actual y disposición |
| --- | --- |
| Catálogo romántico | [seed_catalog](../apps/catalog/management/commands/seed_catalog.py) crea `romantic-dating`. La [migración0023](../apps/listings/migrations/0023_romantic_profile_contract.py) codifica la desactivación de las tres categorías profesionales conocidas y sus servicios, conservando registros y contratos heredados. No se ha vuelto a ejecutar la migración en este corte. |
| Campos del perfil | [profile_contract](../apps/listings/profile_contract.py) exige contrato romántico/categoría compatible y rechaza contenido profesional residual. [DetailsForm](../apps/listings/forms.py) omite las dimensiones profesionales de sus campos actuales y rechaza entradas correspondientes; [views](../apps/listings/views.py) aplica también ese rechazo y trata revisiones heredadas de forma explícita. |
| Búsqueda | [SearchForm](../apps/listings/discovery.py) rechaza los filtros profesionales antiguos. La presencia de ramas internas genéricas de candidatos no demuestra que el formulario público las admita ni justifica restaurarlas. |
| Tarifas históricas | La vista de borrador actual no utiliza RateFormSet ni guarda un formset de tarifas. RateForm conserva usos en [rectificación privada](../apps/safety/rectification_rates.py) y [validación](../apps/listings/public_validation.py); su existencia no equivale a tarifas de servicios activas en el panel romántico. No se eliminan datos o componentes sólo por su nombre. |
| Envío y elegibilidad | [submissions](../apps/listings/submissions.py) llama a la política de contrato compartida. [publication_state](../apps/listings/publication_state.py) incluye profile_contract en sus fuentes de versión y conserva el snapshot de lectura y fallback descritos. La inspección no sustituye pruebas completas de triggers, dependencias o equivalencia. |
| Renovación | [lifecycle](../apps/listings/lifecycle.py) conserva confirmación, ventana de siete días y nueva vigencia de treinta días con fecha real de renovación. El orden y los estados se mantienen distintos de compra o autosubida. No se ha ejecutado una renovación nueva para esta lectura. |
| Promociones | [promotion_models](../apps/catalog/promotion_models.py) mantiene sellable=False. [promotion_orders](../apps/catalog/promotion_orders.py) exige modo sintético y excluye producción; [promotion_exposure](../apps/catalog/promotion_exposure.py) incorpora modo/recuperación, autoridad y visibilidad pública. Un estado sintético paid no acredita cobro real ni aceptación por pasarela. |
| Geografía | [import_geography](../apps/catalog/management/commands/import_geography.py) representa validación de procedencia, veto sintético en producción, transacción y recálculo de elegibilidad. La lectura no importa datos ni verifica licencia, cobertura nacional o despliegue de un dataset real. |

En los contrastes seleccionados no se ha demostrado un defecto vigente que requiera corregir la aplicación. Las diferencias históricas quedan conciliadas con la [adaptación B02–B03](105-adaptacion-perfil-beta-b02b03-20261020.md) y las aceptaciones locales existentes; no se extienden sus resultados a una candidata global nueva. Se conserva trabajo del usuario y no se modifican archivos de producto.

## Pendientes y continuidad

Quedan52capturas de arquitectura,28.439.759caracteres: núcleo, medios, seguridad, documentación, pruebas, interfaz, herramientas, referencias y grandes grafos. El conteo de fuentes no expresa porcentaje de trabajo por volumen. Inventarios, AST, hashes o proyecciones preparadas no sustituyen lectura semántica del contenido y contexto.

Permanecen los límites de originales y capturas anteriores: IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA. B00 sigue abierto; los cuadernos conciliados no acreditan textos originales completos o vigentes.

B07 conserva su cierre local por acta16; B15 continúa opcional. Tres lectores nativos, cero rondas de reparación, cero nuevas invocaciones ClaudeV1 y consumo histórico preservado, sin estimar tokens nativos. Sin nuevas pruebas funcionales o de carga: las comprobaciones de este corte son documentales y estáticas. Grafo365 revalidado al inicio y semántica dirigida366 al integrar; sin nueva extracción AST, semántica exhaustiva o HTML global. Corte anterior: [conciliación276](276-conciliacion-mapa-configuracion-b00-20261023.md).
