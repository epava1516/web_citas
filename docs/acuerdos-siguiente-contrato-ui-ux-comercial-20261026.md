# Acuerdos para el siguiente contrato: UI/UX, oferta comercial, SEO y legalidad

Fecha: 26 de octubre de 2026. Registro solicitado por el usuario en conversación lateral. Es una entrada para preparar el siguiente contrato después del contrato340 de recorridos y optimización; no sustituye el contrato vigente ni abre nuevos bloques de ejecución. El proyecto permanece en alpha.

## Dirección acordada

Actualización del26deoctubre: se plantea la reescritura integral del frontend con Django Templates y htmx4, conservando el backend y sus garantías y admitiendo ajustes justificados por nuevos recorridos. N15 del contrato340 entregará el inventario final de rutas, respuestas y comportamientos que deben preservarse. El siguiente contrato contrastará esa base con los nuevos diseños para decidir reutilización, sustitución, eliminación y cambios necesarios. La migración htmx requiere verificación específica; esta decisión no aprueba por defecto Tailwind, Alpine.js ni librerías auxiliares y no inicia ahora la reescritura.

El siguiente trabajo comenzará por UI/UX, unido a comprobar cómo y qué se publica y cómo se presenta la oferta comercial. El producto es una web de clasificados de perfiles que buscan citas románticas: el anunciante completa un perfil; no anuncia encuentros sexuales. La interfaz debe expresar ese modelo.

Los mínimos de SEO y legalidad definidos en NotebookLM y OpenNotebook local deberán incorporarse al roadmap y al contrato como requisitos de aceptación, desde el diseño.

Se acuerda usar la skill **UI/UX Pro Max** para el diseño y revisión de experiencia. Su uso debe documentar recomendaciones y decisiones y respetar el stack y trabajo existentes. El [prompt maestro adaptado](prompt-siguiente-contrato-ui-ux-comercial-20261026.md) desarrolla las instrucciones para preparar el contrato, sin abrir su ejecución. El prompt original aportado es material de referencia: sus funcionalidades adicionales no se convierten automáticamente en alcance aprobado.

## Orden propuesto para concretar con el contrato

### Preparación de skills

Incluir en la preparación del siguiente contrato la instalación de las skills oficiales de htmx indicadas: `htmx-guidance`, `htmx-debugging`, `htmx-extension-authoring` y `htmx-upgrade-from-htmx2`. Verificar previamente su disponibilidad, origen oficial, instrucciones de instalación y compatibilidad con htmx4 y el agente utilizado; registrar procedencia y versión o commit instalado. Si un nombre o paquete no está disponible, documentar la discrepancia sin sustituirlo silenciosamente ni declarar instalada una skill ausente. La instalación se realizará al preparar ese contrato, no se ha ejecutado mediante esta anotación.

UI/UX Pro Max ya está disponible en esta sesión: comprobar su disponibilidad y versión en el entorno de ejecución del futuro contrato, y conservarla o instalarla si falta. Las cuatro skills de htmx se usarán según la tarea; disponer de la de extensiones no obliga a desarrollar extensiones. Los MCP y las bibliotecas Python/JavaScript son dependencias distintas y no quedan instalados ni aprobados por esta lista.

1. Perfil público: datos, fotos, ubicación, intención romántica, contacto y límites de contenido.
2. Publicación: completar perfil, previsualizar, enviar a moderación, corregir y publicar.
3. Oferta comercial: publicación básica, renovado, top y destacados; definir disponibilidad, precio, duración, límites y efecto exacto sobre el orden. Son decisiones por concretar, no funcionalidades nuevas aprobadas por este documento.
4. Experiencia del visitante: búsqueda, filtros, listado y ficha; identificación de promociones y reglas de ordenación.
5. Panel del anunciante: estado, rechazo, caducidad, renovación, promociones y retirada.
6. Contraste de prototipos y recorridos con la implementación: registrar diferencias visuales y funcionales y convertirlas en trabajo verificable.

Entregables propuestos: recorridos y prototipos revisados, reglas comerciales documentadas, matriz de diferencias con la aplicación y criterios de aceptación. El detalle y la secuencia final se fijarán al redactar el contrato.

## SEO y legalidad: fuentes y trazabilidad obligatorias

Antes de cerrar el contrato, consultar ambos repositorios de conocimiento: NotebookLM y OpenNotebook local. Identificar los notebooks y documentos pertinentes, extraer sus mínimos y conciliar divergencias con la documentación vigente del proyecto. No asumir que un resumen de notebook acredita por sí mismo una obligación legal actual.

Cada requisito debe registrar:

| Campo | Contenido exigido |
| --- | --- |
| Identificación | ID estable y clasificación SEO o legalidad |
| Fuente | Plataforma, notebook, documento, referencia concreta y fecha de consulta |
| Criterio | Requisito concreto y condición de aplicabilidad |
| Superficie | Pantalla, ruta, contenido o comportamiento afectado |
| Verificación | Comprobación y evidencia necesarias para aceptarlo |
| Estado | Implementado, pendiente, conflicto por resolver o pendiente de validación jurídica |

La revisión debe concretar qué información se publica y qué páginas se indexan, cómo aparecen las promociones y dónde se presentan avisos y consentimientos, según las fuentes que se recuperen. Estas categorías orientan la extracción; no constituyen una lista exhaustiva ni requisitos legales ya verificados.

Puntos de partida locales: [SEO04](04-seo.md), [marco legal06](06-marco-legal.md), [apartado público15](15-apartado-legal-publico.md), [conciliación259](259-conciliacion-seo-seguridad-comercial-b00-20261023.md) y [conciliación266](266-conciliacion-lopdgdd-riesgo-marco-legal-b00-20261023.md). Contrastar vigencia normativa y determinar qué extremos requieren validación jurídica al preparar el contrato.

Estado de esta documentación: **no se han consultado NotebookLM ni OpenNotebook local en esta conversación; no hay todavía extracción, conciliación ni aceptación de sus mínimos**. Su consulta y trazabilidad quedan como requisito de preparación del siguiente contrato.

## Respuestas de rutas en el estado final del desarrollo

Acuerdo adicional del usuario: definir qué devuelve cada ruta en la última versión del desarrollo. Preparar en el siguiente contrato la matriz y su método de verificación; la versión final deberá actualizarse contra el código y la evidencia del corte de entrega, sin presentar el estado alpha actual como resultado final futuro.

Vincular cada entrada al inventario de recorridos y distinguir rutas HTTP de acciones, tareas y procesos internos. Para cada ruta y método registrar parámetros y entradas, autenticación/rol, precondiciones y estado de los objetos, código HTTP, redirección y destino cuando corresponda, tipo de contenido, plantilla o esquema de respuesta, campos/valores permitidos y significado, cabeceras relevantes y efectos persistidos o tareas desencadenadas. Cubrir éxito, validación, ausencia, acceso denegado, retirada/caducidad, conflictos y fallos aplicables; documentar diferencias por idioma cuando existan.

Los valores dinámicos se describirán mediante tipos, reglas, rangos o enumeraciones y ejemplos sintéticos, no mediante datos reales ni valores únicos fijados artificialmente. Para HTML describir también el estado y contenido funcional observable; para archivos, formato y propiedades; para operaciones asíncronas, separar la respuesta inicial del resultado terminal.

Incluir resultado esperado frente al observado, referencia a código y prueba/evidencia, versión/commit y fecha. Lo no ejecutado o sin evidencia se marcará explícitamente; una especificación no cuenta como verificación. Conciliar rutas añadidas, modificadas y eliminadas y justificar exclusiones. Este acuerdo no autoriza iniciar ahora una batería global ni alterar el contrato vigente.

## Deuda y límites conservados

- Conciliar la deuda al cierre del contrato vigente; este acuerdo no declara aceptado ningún bloque pendiente.
- Mantener la optimización marginal pendiente de MOD09 para el final del desarrollo, conforme a la decisión del usuario. Los fallos funcionales o de seguridad conservan su tratamiento necesario.
- Mantener el contrato general de medición y optimización de QA aplazado hasta la primera versión estable/productiva, según el acuerdo previo.
- Personalización por intereses físicos: posibilidad futura; su inclusión no queda aprobada aquí. Conservar el consentimiento separado y las decisiones pendientes sobre persistencia, retención y retirada recogidas en la [deuda336](336-deuda-siguiente-contrato-y-cierre-alpha-20261025.md).
- No se autoriza publicar, abrir beta/producción, contratar proveedores ni utilizar datos reales.

Este registro documenta acuerdos y propuestas de alcance; no es un contrato ejecutable ni una certificación de cumplimiento.


## Deuda heredada visible — acuerdo del 27 de octubre de 2026

El usuario confirma que la siguiente etapa será UI/UX/Front y exige conservar e informar la deuda pendiente en cualquier consulta futura de pendientes. El [registro vivo de deuda](deuda-pendiente-viva.md) conserva N02/MOD09 aplazado al final del desarrollo y N12/B14, N13/B15, N14/B17 condicionados, además del contrato general de QA aplazado hasta la primera versión estable/productiva. Consultarlo junto con el seguimiento: pasar al frontend o cerrar el contrato340 no elimina estas entradas ni las convierte en PASS. El siguiente contrato debe enlazar el registro y distinguir deuda heredada de alcance ejecutable; su inclusión documental no activa implementación, proveedores ni apertura.
