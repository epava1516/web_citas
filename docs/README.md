# Documentación del proyecto

Entrada de consulta y mantenimiento. Idioma: español. Organización: 2026-10-09. Las rutas existentes se conservan; las copias históricas y evidencias tienen fecha, fuente y límites propios.

## Consultar por tarea

| Necesito… | Empezar aquí | Consultar después |
| --- | --- | --- |
| Ejecutar el proyecto localmente | [Inicio, Docker, datos y verificación](../README.md) | [Base técnica](adr/001-base-tecnica.md), [datos sintéticos](contratos/07-datos-sinteticos.md). |
| Retomar el desarrollo o conocer el estado | [Seguimiento vigente](17-seguimiento-desarrollo.md) | [Pendientes e insumos](83-auditoria-pendientes-cr09.md), [alcances reutilizables](88-matriz-cierre-derechos.md). |
| Entender módulos y publicación | [Arquitectura implementada](02-arquitectura.md) | [ADR](adr/001-base-tecnica.md), [MOD-05](16-contrato-ejecucion-desarrollo.md#17-estado-de-publicación-almacenado--mod-05). |
| Saber qué debe hacer el producto | [Contrato funcional](14-contrato-funcional-v1.md) | [Apartado legal](15-apartado-legal-publico.md), [contratos de interacción](#contratos-de-interacción). |
| Desbloquear un pendiente | [Matriz única de pendientes](83-auditoria-pendientes-cr09.md) | Entrada faltante, rol responsable, evidencia y condición de cierre; registrar la acción en seguimiento. |
| Verificar una entrega | [Actas y evidencias](#verificar-una-entrega) | [Contrato de ejecución](16-contrato-ejecucion-desarrollo.md), [criterios de carga](criterios-revision-benchmark-carga.md). |
| Recuperar datos/medios y recursos | [Instrucciones de recuperación](85-operacion-registro-recuperacion.md) | [Recursos](87-recursos-locales-recuperacion.md), [diseño](84-restauracion-sin-reintroduccion.md), [incidentes](12-operacion-seguridad.md). |
| Interpretar el porcentaje de avance | [Método y tablas v10](86-medicion-avance-contrato.md) | [Cálculo original](evidencias/avance-ponderado-v10.json); no equivale a aceptación de fases. |
| Investigar decisiones o resultados anteriores | [Historial](#historial-y-análisis) | [Inventario de copias/huellas](historial-documentacion.json); las fuentes actuales prevalecen. |

## Autoridad de cada documento

Las instrucciones expresas del usuario prevalecen. Conservar la distinción entre una regla requerida, su implementación y su evidencia; una fecha posterior en un informe no sustituye una decisión contractual.

| Pregunta | Fuente mantenida | Qué no establece |
| --- | --- | --- |
| Comportamiento y alcance | [Contrato14](14-contrato-funcional-v1.md) y [legal15](15-apartado-legal-publico.md). | No acredita que el producto entero esté implementado. |
| Orden, gates y cambios autorizados | [Contrato16 v1.6](16-contrato-ejecucion-desarrollo.md), texto consolidado; cambios anteriores como historial. | No acredita PASS ni permite publicar/contratar. |
| Estado, runtime y próxima acción | [Seguimiento17](17-seguimiento-desarrollo.md), única cola. | No sustituye los originales de una prueba. |
| Insumos faltantes y condición de cierre | [Matriz83](83-auditoria-pendientes-cr09.md), basada en el acta residual enlazada. | No crea otra cola ni nuevos requisitos. |
| Alcance cerrado y reutilizable | [Matriz88](88-matriz-cierre-derechos.md), actas e informes enlazados. | No acepta un derecho/fase integral por cerrar un componente. |
| Arquitectura e interfaces | [Arquitectura02](02-arquitectura.md), [ADR](adr/001-base-tecnica.md), contratos de interacción. | No acredita proveedor o rendimiento productivo. |
| Método y estimación de avance | [Método86](86-medicion-avance-contrato.md), JSON v10 original. | No mide horas ni aceptación jurídica/productiva. |
| Resultado observado | Artefacto original con versión, huella, escenario y límites. | No se extrapola a otras versiones ni se suma como batería común. |

## Verificar una entrega

- [Acta BASE/CR-06 local](actas/01-base-cr06-local.md).
- [Acta CR-07 local](actas/02-cr07-local.md).
- [Acta CR-08 local](actas/03-cr08-local.md).
- [Auditoría inicial CR-09](actas/04-cr09-auditoria-pendiente.md), [matriz actual](83-auditoria-pendientes-cr09.md) y [componentes](88-matriz-cierre-derechos.md).
- [Evidencias de desarrollo y revisión documental](18-evidencias-desarrollo.md).
- [Gates MOD-05 y sus límites](evidencias/mod05-gates-normal-informe0110.md), con originales y aceptación en seguimiento17.
- [Revisión documental previa](evidencias/revision-documentacion-20261009.json) y [organización actual](evidencias/organizacion-documental-20261009.json); no son pruebas funcionales.

## Contratos de interacción

- [Interfaces comunes v1](contratos/00-base.md).
- [CR-01 — Cuentas y documentos, interfaz v1](contratos/01-cuentas-legal.md).
- [CR-02 — Agencias, asignación y MFA, interfaz v1](contratos/02-agencias-mfa.md).
- [CR-03 — Verificación y representación, interfaz v1](contratos/03-verificacion-representacion.md).
- [CR-04 — Borradores, catálogos y geografía, interfaz v1](contratos/04-borradores-catalogo-geografia.md).
- [CR-05 — Fotografías y coincidencias, interfaz v1](contratos/05-fotografias-coincidencias.md).
- [CR-06 — Moderación y publicación, interfaz v1 en curso](contratos/06-moderacion-publicacion.md).
- [Datos sintéticos de demostración — fixture v1](contratos/07-datos-sinteticos.md).
- [CR-07 — Descubrimiento, contrato de interacción](contratos/08-descubrimiento.md).
- [CR-08 — Favoritos y ciclo de vida, diseño pendiente de implementación](contratos/09-ciclo-vida.md).
- [Publicación por finalidad: calendario y levantamiento](contratos/09-publicacion-finalidad.md).
- [CR-09 — Denuncias, derechos y reclamación sin cuenta](contratos/10-denuncias-derechos.md).
- [CR-10 — Contrato de preparación comercial](contratos/11-promociones-preparacion.md).

## Índice

Las referencias de detalle se agrupan por su función. Un diseño inicial conserva su fecha y las decisiones que lo sustituyen; para reanudar se utiliza siempre seguimiento17.

Propuesta independiente pendiente de lanzamiento manual: [evaluación acotada de GraphQL](propuesta-graphql-manual.md). No forma parte de la cola del goal ni modifica la aceptación contractual.

<details>
<summary>Producto, diseño inicial, seguridad y legal</summary>

- [Producto y alcance](01-producto.md).
- [Seguridad, privacidad y moderación](03-seguridad-privacidad.md).
- [SEO y competitividad](04-seo.md).
- [Decisiones y preguntas pendientes](05-decisiones.md).
- [Marco legal y plan de cumplimiento](06-marco-legal.md).
- [Referencias de producto y competencia](07-referencias-competencia.md).
- [Publicaciones: categorías, campos, etiquetas y tarifas](08-fichas-categorias.md).
- [Taxonomía, ubicación y búsqueda](09-taxonomia-ubicacion-busqueda.md).
- [Unicidad y prevención de anuncios duplicados](10-unicidad-antiduplicados.md).
- [Plan de seguridad, implementación y validación](11-plan-seguridad-validacion.md).
- [Operación de seguridad e incidentes](12-operacion-seguridad.md).
- [Decisiones para cerrar el contrato de desarrollo](13-cierre-contrato-desarrollo.md).
- [Contrato funcional de desarrollo — versión 1](14-contrato-funcional-v1.md).
- [Apartado legal público y condiciones de publicación](15-apartado-legal-publico.md).

</details>

<details>
<summary>Implementación de derechos y privacidad</summary>

- [Resolución independiente de reclamaciones — CR-09](21-resolucion-reclamaciones.md).
- [Procesamiento de avisos privados — CR-09](22-procesamiento-avisos.md).
- [Copia privada de datos e imágenes — CR-09](23-copia-derechos-datos-imagenes.md).
- [Respuestas y cierre de derechos — CR-09](24-respuestas-cierre-derechos.md).
- [Medidas de privacidad sobre publicación](25-medidas-privacidad-publicacion.md).
- [Inventario previo a supresión y conservación](26-inventario-supresion-retencion.md).
- [Decisiones por finalidad de supresión y conservación](27-planes-supresion-conservacion.md).
- [Ejecución parcial de supresión por ámbitos](28-ejecucion-supresion-ambitos.md).
- [Supresión de contenido editorial y alias](29-supresion-contenido-publicacion.md).
- [Supresión de imágenes, huellas y almacenamiento](30-supresion-imagenes-almacenamiento.md).
- [Recuperación operativa de borrado de archivos](31-recuperacion-borrado-archivos.md).
- [Redacción de referencias a imágenes compartidas](32-redaccion-imagenes-compartidas.md).
- [Supresión de desafíos, invitaciones y asociación de teléfono](33-supresion-contactos-invitaciones.md).
- [Supresión de identidad y acceso de cuenta](34-supresion-cuenta.md).
- [Supresión de autorización de representación](35-supresion-representacion.md).
- [Indicadores de atención de derechos](36-atencion-derechos.md).
- [Alertas internas persistentes de denuncias urgentes](37-alertas-denuncias-urgentes.md).
- [Registro explícito de recepción de respuestas de derechos](38-recepcion-respuestas-derechos.md).
- [Levantamiento revisado de cautelas de publicación](39-levantamiento-cautelas-privacidad.md).
- [Auditoría de dependencias pendientes de derechos](40-auditoria-dependencias-derechos.md).
- [Aclaración de referencias de reclamaciones](41-aclaraciones-reclamaciones.md).
- [Copias privadas por partes — integración verificada localmente](42-copias-por-partes.md).
- [Rectificación de datos — ejecución y comunicaciones locales](43-rectificacion-datos.md).
- [Conservación y limpieza de cargas preparadas](44-conservacion-cargas-preparadas.md).
- [Acceso histórico tras rectificación](45-acceso-historico-rectificacion.md).
- [Historial rectificado en colas generales](46-historial-colas-generales.md).
- [Recarga de imágenes tras rectificación](47-reintroduccion-imagenes.md).
- [Revisión privada de recargas: contrato de implementación](48-revision-privada-recargas.md).
- [Rectificación de cuenta — contrato de implementación](49-rectificacion-cuenta.md).
- [Vinculación de derechos a un perfil sin anuncio](50-vinculacion-perfil-sin-anuncio.md).
- [Derechos de una cuenta sin perfil](51-derechos-cuentas-sin-perfil.md).
- [Purga de entrega de confirmación — worker y Beat](52-purga-entrega-confirmacion-worker.md).
- [Inventario de derechos de cuenta por finalidad](53-inventario-derechos-cuenta.md).
- [Copia privada de cuenta sin perfil](54-copia-cuenta-sin-perfil.md).
- [Inventario y decisiones de supresión de cuenta propia](55-inventario-supresion-cuenta.md).
- [Dependencias y causalidad del inventario propio de cuenta](56-dependencias-inventario-cuenta.md).
- [Calendario y revisión de conservación por finalidad](57-revision-conservacion-finalidad.md).
- [Limitación y oposición por finalidad](58-limitacion-oposicion-finalidades.md).
- [Ejecución durable de restricciones por finalidad](59-ejecucion-restricciones-finalidad.md).
- [Levantamiento comunicado de restricciones por finalidad](60-levantamiento-restricciones-finalidad.md).
- [Calendario operativo de restricciones por finalidad](61-calendario-restricciones-finalidad.md).
- [Excepciones acotadas a restricciones de tratamiento](62-excepciones-acotadas-tratamiento.md).
- [Inventario seleccionado de evidencias por finalidad](63-inventario-evidencias-finalidad.md).
- [Variantes y autoridad de excepciones durante la espera](64-variantes-autoridad-excepciones.md).
- [Nueva medida durante una supresión pendiente](65-nueva-medida-durante-espera.md).
- [Ejecución y levantamiento por finalidad: publicación](66-publicacion-finalidad-diseno.md).
- [Copias de datos por paquetes: diseño de entrega](67-copias-datos-volumen.md).
- [Consulta paginada de fuentes de copia privada](68-consulta-paginada-copias.md).
- [Revisión persistente de páginas de copia privada](69-revision-persistente-copias.md).
- [Compilación de decisiones por páginas](70-compilacion-paginas-copia.md).
- [Contactos registrados de la propia cuenta en copias privadas](71-copia-contactos-propios.md).
- [Relaciones de la propia cuenta con agencias](72-copia-relaciones-cuenta.md).
- [Información adicional de acceso y distinción de portabilidad](73-informacion-acceso-portabilidad.md).
- [Revisión independiente de información de acceso](74-revision-independiente-informacion.md).
- [Información revisada en exportación privada](75-informacion-revisada-en-exportacion.md).
- [Evaluación de portabilidad por conjuntos](76-evaluacion-portabilidad-conjuntos.md).
- [Selección granular aprobada de portabilidad](77-portabilidad-seleccion-aprobada.md).
- [Portabilidad de conjuntos con origen mixto](78-portabilidad-origen-mixto.md).
- [Entrega privada de portabilidad aprobada](79-entrega-portabilidad-aprobada.md).
- [Portabilidad de contenido de imágenes](80-portabilidad-contenido-imagenes.md).
- [Cobertura declarada de portabilidad — base técnica parcial](81-cobertura-declarada-portabilidad.md).
- [Portabilidad: vincular cobertura, entrega y respuesta final](82-portabilidad-cobertura-entrega-cierre.md).

</details>

<details>
<summary>Ejecución, operación y matrices</summary>

- [Arquitectura y operación](02-arquitectura.md).
- [Contrato de ejecución del desarrollo — versión 1.6 consolidada](16-contrato-ejecucion-desarrollo.md).
- [Historial del seguimiento de desarrollo](17-historial-desarrollo.md).
- [Seguimiento de ejecución del contrato](17-seguimiento-desarrollo.md).
- [Auditoría de pendientes para aceptación CR-09](83-auditoria-pendientes-cr09.md).
- [Restauración sin reintroducir datos retirados o suprimidos](84-restauracion-sin-reintroduccion.md).
- [Operación del registro de recuperación](85-operacion-registro-recuperacion.md).
- [Medición del avance del contrato](86-medicion-avance-contrato.md).
- [Recursos locales y aislamiento tras restauración](87-recursos-locales-recuperacion.md).
- [Matriz de ejecución y cierre por derecho — CR09](88-matriz-cierre-derechos.md).
- [Corrección de ejecución: cerrar recorridos completos](89-plan-cierre-integrado-cr09.md).
- [Comunicaciones de derechos ejecutados](90-comunicaciones-derechos-ejecutados.md).
- [Preparación de orígenes Redis RDB/AOF](91-origenes-redis-rdb-aof.md).

</details>

## Historial y análisis

<details>
<summary>Historial y análisis</summary>

- [Evidencias de desarrollo](18-evidencias-desarrollo.md).
- [Graphify: instalación, uso y límites](19-graphify-analisis-local.md).
- [Autoría y publicación del historial](20-autoría-historial.md).
- [Análisis estático del repositorio — Claude Code](92-analisis-claude-code-20261008.md).
- [Propuesta técnica: estado de publicación almacenado con invalidación por triggers](93-propuesta-estado-publicacion-claude-code.md).
- [Análisis del bloqueo y DAFO — coste y capacidad de servicio](analisis-bloque-rendimiento-dafo0110.md).
- [Criterios de revisión del benchmark de carga](criterios-revision-benchmark-carga.md).
- [Propuesta para cerrar pendientes locales: capacidad, insumos operativos y CI](propuesta-cierre-pendientes-locales.md).
- [Verificación propia sin CI de pago](ci-local.md).
- [Checkpoint de atribución del listado](diagnostico-coste-listado0110.md).
- [Diagnóstico de proyección y contraste Claude — 0110](diagnostico-proyeccion-claude0110.md).
- [Dependencias de la lectura pública y decisión de optimización](diseno-lectura-publica-dependencias0110.md).
- [Revisión extensa con Claude del rendimiento público](revision-claude-rendimiento-extensa0110.md).

</details>

El [inventario de copias](historial-documentacion.json) registra ruta, SHA-256 y base original de enlaces. Las copias de `17-historial/` conservan sus bytes; las referencias a código retirado tienen una consulta Git registrada. No editar copias para actualizar el estado. Graphify facilita navegación, pero su grafo conserva cortes históricos y se contrasta con fuentes actuales: [uso y límites](19-graphify-analisis-local.md).

## Mantener la documentación

1. Actualizar el documento responsable del dato, según la tabla de autoridad; enlazarlo desde los demás. Mantener seguimiento breve y matriz de pendientes consolidada.
2. Registrar requisito/cambio, versión, evidencia y límites. Distinguir propuesto, confirmado, pendiente, descartado y cerrado localmente; no afirmar cumplimiento desde una especificación.
3. Si se retira una cronología de un documento activo, conservar una copia exacta con nombre/fecha nuevos y registrar su huella/base de enlaces en `historial-documentacion.json`. No sobrescribir originales ni recalcular huellas para ocultar cambios.
4. No registrar secretos, identidades reales, claves o datos privados. Las correcciones documentales no cambian aceptación, porcentajes ni autorización de acciones externas.
5. Ejecutar desde la raíz:

```sh
python3 scripts/check_docs.py
uv run ruff check scripts/check_docs.py
```

El comprobador valida enlaces/anclas locales y huellas de copias registradas. Resuelve enlaces históricos desde su base original y admite únicamente referencias retiradas concretas con evidencia Git; un enlace roto nuevo o una copia alterada falla. No comprueba normativa, destinos HTTP ni comportamiento de la aplicación. El workflow incorpora el gate local; su configuración no demuestra que CI externo se haya ejecutado.


## Relevo detenido2026-10-09

Goal pausado: [informe y continuación](relevo-claude-20261009.md), [prompt con gobernanza vigente](prompt-relevo-claude-20261009.md), [inventario y evidencia](evidencias/relevo-local-20261009.json). No se autoriza ejecución directa de Claude ni reanudar bloques por leer estos documentos.
