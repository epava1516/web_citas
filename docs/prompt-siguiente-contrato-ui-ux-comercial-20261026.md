# Prompt maestro adaptado: siguiente contrato de UI/UX y publicación comercial

Fecha: 26 de octubre de 2026. Adaptación del prompt aportado por el usuario. Complementa los [acuerdos del siguiente contrato](acuerdos-siguiente-contrato-ui-ux-comercial-20261026.md). Es una instrucción para preparar ese contrato, no su aprobación ni una orden de iniciar ahora su desarrollo. El contrato vigente conserva su alcance y seguimiento.

## 1. Rol y objetivo

Actúa como analista funcional, arquitecto de software y especialista en producto y UX/UI. Analiza los aspectos jurídicos con fuentes primarias vigentes y distingue lo verificable técnicamente de lo que requiere revisión profesional; no te presentes como abogado ni atribuyas al documento una validación jurídica inexistente.

Prepara el siguiente contrato y su roadmap para evolucionar la aplicación existente, empezando por UI/UX y por comprobar cómo y qué se publica y comercializa. No replantees el proyecto desde cero. El proyecto continuará en alpha: la aceptación de este contrato no autoriza beta, producción, contratación de proveedores, cobros ni uso de datos reales.

Distingue acuerdos confirmados, implementación existente con evidencia, propuestas y decisiones pendientes. No inventes identidades, precios, presupuesto, plazos, proveedores ni compromisos. Usa `[PENDIENTE DE DEFINIR]` y registra qué decisión falta y a quién corresponde.

## 2. Modelo de producto y alcance

Dirección añadida por el usuario: diseñar y reescribir el frontend con Django Templates y htmx4 sobre el backend existente, tomando como entrada el inventario final de relevo entregado en N15. No exigir conservar el diseño actual. Conservar los comportamientos y garantías inventariados y justificar cualquier adaptación del backend. Evaluar explícitamente la migración desde la versión htmx instalada y sus cambios de atributos, eventos e historial, además de CSRF y sondeos; validar sustituciones por recorridos antes de retirar pantallas anteriores. No convertir esta preparación en ejecución anticipada de la reescritura.

La plataforma ofrece clasificados de perfiles de personas adultas que buscan quedar románticamente. El anunciante rellena un perfil. La referencia a portales de encuentros sirve para comprender la estructura de clasificados y mecanismos de renovado, top y visibilidad; no implica anunciar encuentros sexuales, prostitución o servicios de escorts, ni copiar marcas, contenidos o identidad visual ajenos.

No conviertas amistad, actividades, comunidades, swipe, matching, mensajería interna, múltiples anuncios por cuenta, créditos, saldo o publicación gratuita en requisitos confirmados por aparecer en el prompt original. Contrasta su existencia y sus contratos actuales; cualquier ampliación requiere disposición expresa en la matriz. El canal de contacto se determinará a partir del producto y la implementación actuales.

La personalización por intereses físicos es una posibilidad futura, no un requisito aprobado para este contrato. Conserva la deuda documentada sobre consentimiento, almacenamiento y retirada; no infieras preferencias desde imágenes ni traslades automáticamente las de visitantes a cuentas.

## 3. Preparación y fuentes

Antes de fijar el alcance:

1. Leer las instrucciones del repositorio, el contrato vigente y su cierre cuando exista, el inventario diferencial de recorridos, el grafo y la deuda vigente. Registrar versiones y fecha del corte; usar el grafo para localizar relaciones y comprobar los hechos en sus fuentes.
2. Revisar las pantallas, componentes, reglas comerciales y pruebas existentes. Diferenciar comportamiento implementado, comportamiento verificado y carencias; no rehacer funciones aceptadas sin una necesidad documentada.
3. Consultar tanto NotebookLM como OpenNotebook local. Identificar notebooks, documentos y referencias concretas de SEO y legalidad. No declarar consultada una fuente inaccesible: registrar la carencia y mantener pendientes los requisitos dependientes.
4. Conciliar esas fuentes con la documentación del repositorio y con fuentes oficiales vigentes para las afirmaciones jurídicas. Documentar discrepancias, aplicabilidad y resolución; ninguna respuesta de notebook es por sí sola certificación de cumplimiento.

## 4. UI/UX Pro Max: uso requerido

Como tarea de preparación del contrato, instalar las skills oficiales `htmx-guidance`, `htmx-debugging`, `htmx-extension-authoring` y `htmx-upgrade-from-htmx2`, verificando disponibilidad, procedencia oficial, compatibilidad e instrucciones vigentes antes de instalar. Registrar fuente y versión/commit y comprobar que el agente puede cargarlas. Documentar cualquier ausencia o discrepancia; no afirmar instalación por haberla incluido en un roadmap. Comprobar también que UI/UX Pro Max sigue disponible e instalarla sólo si falta. Aplicar cada skill a las tareas pertinentes, sin imponer desarrollo de extensiones. La instalación pertenece a la preparación futura y no se ejecuta al guardar este prompt.

Usar la skill **UI/UX Pro Max**, leyendo su SKILL.md vigente. Aplicar sus búsquedas y criterios al producto real, registrando consultas, recomendaciones pertinentes y decisiones adoptadas o descartadas. Sus recomendaciones no sustituyen acuerdos, evidencia ni normas aplicables.

Detectar el stack existente antes de recomendar implementación; no introducir frameworks ni migraciones por defecto. Leer y preservar cualquier sistema de diseño existente. Para una dirección visual general, generar una propuesta coherente con `--design-system`; verificar su pertinencia antes de persistirla y no sobrescribir decisiones previas mediante `--force` sin autorización expresa.

La propuesta inicial será una estructura reconocible de clasificados, con modernización moderada: listados compactos, jerarquía clara, tipografía legible, efectos mínimos y componentes reutilizables. La densidad no debe sacrificar legibilidad, navegación con teclado ni controles táctiles. Colores, tipografías y variantes se validarán mediante prototipos, no quedan aprobados por este prompt.

Revisar móvil, tableta y escritorio, formularios y sus errores, foco, contraste, zoom, carga, vacío, rechazo, caducidad, acceso denegado y retirada. Definir criterios verificables de accesibilidad; separar objetivos técnicos de la determinación de exigibilidad legal.

## 5. Recorridos y reglas comerciales

Preparar y contrastar estos recorridos con la aplicación:

- Visitante: navegación geográfica, búsqueda, filtros, ordenación, paginación, ficha y contacto.
- Anunciante: cuenta y acceso, rellenado de perfil, fotos, previsualización, envío a moderación, corrección, publicación, renovación y retirada.
- Moderación: revisión, rechazo motivado, denuncias, permisos y trazabilidad.
- Comercial: oferta básica, renovado, top, destacados y autosubida cuando existan o se acuerden; información previa y seguimiento desde el panel.

Para cada mecanismo comercial definir: elegibilidad, coste o gratuidad por decidir, duración, intervalo, plazas, ámbito geográfico/categoría, orden y rotación, convivencia con otras promociones, identificación visual, activación, expiración, cancelación y efecto de moderación o retirada. Diferenciar renovación de visibilidad, renovación de vigencia y renovación de una contratación; no asumir cargos recurrentes.

Examinar administración, permisos, transacciones, cancelaciones y justificantes en el alcance realmente acordado. No elegir proveedor ni presentar adaptadores sintéticos como integración real. La integración futura de pagos tendrá dependencias y criterios separados de su representación en prototipos.

## 6. Mínimos de SEO y legalidad

Incorporar al roadmap y al contrato una matriz trazable con ID, fuente/plataforma/notebook/documento/referencia/fecha, requisito, aplicabilidad, superficie afectada, responsable, método de verificación, evidencia y estado.

Extraer de las fuentes los mínimos reales. Revisar especialmente decisiones de indexación y privacidad de perfiles, páginas públicas frente a privadas, búsquedas y filtros, metadatos, canonical, sitemap, idiomas y estados retirados cuando correspondan. No convertir esta lista orientativa en requisitos supuestamente obtenidos de los notebooks.

Para legalidad, investigar en fuentes oficiales la aplicabilidad de protección de datos, comercio electrónico, servicios digitales, consumo, propiedad intelectual, accesibilidad y pagos/facturación según las funciones y el operador. Examinar las categorías de datos efectivamente tratadas, incluidas preferencias que puedan revelar información especialmente protegida, sin asumir que toda preferencia tiene idéntica clasificación.

Concretar edad, términos, privacidad, cookies, personalización, moderación, denuncias, retirada y derechos según corresponda. Separar aceptación de términos, declaración de mayoría de edad y consentimientos específicos; no agruparlos como aceptación universal. El cifrado es una medida técnica, no una acreditación suficiente de cumplimiento.

Distinguir tareas del desarrollador y obligaciones del futuro operador, textos provisionales y definitivos, y puntos sujetos a validación jurídica. No afirmar cumplimiento global por disponer de avisos o superar pruebas técnicas.

## 7. Entregables y roadmap propuesto

Proponer bloques verificables, ajustados tras el análisis:

1. Conciliación de fuentes, alcance, deuda y matriz de requisitos.
2. Arquitectura de información, recorridos y reglas de publicación/comercialización.
3. Sistema de diseño y prototipos revisados, con aplicación documentada de UI/UX Pro Max.
4. Implementación de diferencias acordadas en superficies públicas.
5. Implementación de diferencias acordadas en panel y moderación.
6. Verificación de reglas comerciales y mínimos transversales de SEO, privacidad, legalidad y accesibilidad.
7. Integración, documentación, actualización del inventario y del grafo conforme al procedimiento acordado, y aceptación local en alpha.

SEO y legalidad intervienen desde el primer bloque: el sexto verifica su integración. No relegarlos a una revisión final.

Al terminar cada bloque entregar una tabla antes/después que muestre comportamiento, evidencia, diferencias y límites. Incluir tiempos de rendimiento anteriores y posteriores cuando haya comparación equivalente: escenario, entorno, datos, repeticiones y método. Si falta una referencia comparable, indicar «sin referencia comparable»; no inventar mejora ni confundir duración de QA con tiempo de la aplicación. Acompañar las diferencias visuales con capturas equivalentes cuando proceda.

## 8. Contrato y criterios de aceptación

Incluir como entregable una matriz de respuestas por ruta y método, enlazada al inventario de recorridos. Prepararla durante este contrato y exigir su conciliación con el último corte del desarrollo antes de la entrega final: entradas, rol y estado, código HTTP, redirecciones, tipo de contenido, plantilla/esquema, campos y valores admisibles, cabeceras relevantes y efectos secundarios. Cubrir las ramas aplicables de éxito, errores, permisos, retirada, caducidad y conflicto. Distinguir respuesta HTTP inicial de resultado asíncrono terminal, rutas de acciones internas y especificación de observación real. Documentar valores dinámicos con reglas y ejemplos sintéticos. Registrar esperado/observado, evidencia y versión/commit; marcar pendientes y exclusiones y conciliar altas, cambios y bajas, sin atribuir el estado actual al resultado final futuro.

Empezar por la matriz de requisitos y el índice contractual. Para cada unidad indicar alcance, dependencias, exclusiones, entregable, resultado esperado, comprobación, evidencia y condición de aceptación. Diferenciar prototipo, integración local, entorno controlado e integración externa real. No aceptar una función sólo porque se vea ni una validación general a partir de un muestreo limitado.

El índice debe cubrir objeto y precedencia documental, alcance/exclusiones, roadmap y dependencias, entregables, aceptación y subsanación, cambios de alcance, responsabilidades, seguridad y datos, licencias y acceso al código, reversibilidad, riesgos, deuda y cierre. Si procede formalizar contratación entre partes, incluir como pendientes identificación, precio/pago, propiedad intelectual, confidencialidad, garantía, mantenimiento, terminación y jurisdicción. No inventar una relación mercantil ni imponer cesión/licencia por defecto.

Las pruebas serán proporcionales al cambio y respetarán el procedimiento vigente de PostgreSQL, evidencias y notificaciones. No reabrir el programa general de optimización de QA aplazado a versión estable/productiva. Mantener la optimización marginal de MOD09 para el final del desarrollo; las correcciones funcionales y de seguridad necesarias conservan prioridad.

## 9. Secuencia de trabajo al preparar el contrato

Extrae primero acuerdos y evidencia existente; después identifica contradicciones y vacíos. Produce la matriz, el índice y el roadmap con dependencias y criterios. Formula únicamente las preguntas que impidan cerrar decisiones concretas y continúa el trabajo independiente. Redacta después el borrador, comprueba su coherencia con anexos y fuentes y presenta los puntos pendientes de decisión o revisión profesional.

No ejecutar este roadmap por la mera incorporación del prompt a documentación. La apertura de su desarrollo requerirá la instrucción correspondiente del usuario.
