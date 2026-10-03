# Referencias de producto y competencia

Fecha: 2026-10-03. Estado: revisión pública preliminar.

La revisión de fichas individuales, campos, servicios y precios se desarrolla en [Publicaciones por categoría](08-fichas-categorias.md).

## Encargo y método

El usuario identifica LoquoSex, MálagaCitas y destacamos.net como referencias de lo que desea replicar. Se realizan búsquedas web por nombre y dominio y lecturas de páginas públicas. La herramienta de búsqueda no acredita resultados específicos de Google ni posiciones en ese buscador.

No se crean cuentas, envían formularios ni realizan compras. No se copian contactos, fotografías o anuncios individuales a esta documentación. Tras autorización del usuario se complementó la extracción con Chromium headless y Playwright. No se ha realizado auditoría visual completa, medición de rendimiento, evaluación de seguridad ni revisión de paneles privados. La extracción de HTML no prueba que las funciones descritas estén operativas.

## Referencias observadas

### LoquoSex

Dominio revisado: [www.loquosex.com](https://www.loquosex.com/). Se descarta usar resultados de dominios homónimos como evidencia del sitio solicitado.

La portada ofrece registro, acceso, publicación, búsqueda textual y filtros por categoría, provincia, ciudad y barrio. Los listados incluyen precio, edad, ubicación y contacto, con etiquetas TOP y autorrenovación. También hay enlaces geográficos y legales.

El HTML público incluye un preregistro que solicita identidad, documentos, selfie y empadronamiento, y formularios de códigos por correo. Esto describe la interfaz expuesta, sin confirmar su funcionamiento o justificar esa recogida de datos para nuestro proyecto.

Fuente: portada enlazada arriba; [condiciones de uso](https://www.loquosex.com/condiciones-de-uso/) localizadas como referencia para una revisión posterior completa.

### Destacamos

Dominio accesible: [www.destacamos.net](https://www.destacamos.net/). La variante sin `www` produjo error en la herramienta.

La portada ofrece categorías, navegación territorial, publicación gratuita, registros de profesional y cliente, favoritos y ocultos. Presenta enlaces diferenciados a versiones móvil y escritorio y a políticas legales.

Fuente: portada. No se ha comprobado persistencia de favoritos u ocultos ni completado registro.

La [entrada de publicación](https://www.destacamos.net/pre-submit.html) requiere acceso o registro profesional.

Las [condiciones de contratación](https://www.destacamos.net/content.php?id=21) describen publicación con título, descripción, teléfono y ciudad, verificación telefónica, fotografías y opciones de visibilidad Premium, Top y autosubidas. También contemplan perfiles adicionales y créditos. Es información declarada por el sitio, no un flujo probado ni una aprobación jurídica de sus condiciones.

En el [listado de Málaga](https://www.destacamos.net/localidad-M%C3%A1laga/listings.html) aparecen modalidades promocionales, canales WhatsApp/Telegram, favoritos y etiquetas de fotos reales. La etiqueta no demuestra cómo se verifican las imágenes.

### MálagaCitas

Dominio correcto confirmado por el usuario: [www.malagacitas.es](https://www.malagacitas.es/). Accesible con herramienta web y Chromium headless, HTTP 200. Los intentos anteriores sobre `.com` fallaron y no sirven para evaluar esta referencia.

La portada incluye navegación a chicas, trans y chicos, búsquedas por palabras, filtros de características, localidades y una interfaz para mapa/geolocalización. Publicar y editar enlazan a autenticación externa en `auth.spaincitas.com` y panel en `admin.malagacitas.es`; no se ha iniciado sesión.

Se revisaron cuatro publicaciones individuales: tres grupos principales y una del filtro de masaje profesional. Campos, etiquetas y precios observados en [fichas por categoría](08-fichas-categorias.md). Las afirmaciones de fotos reales o cumplimiento legal son declaraciones del sitio, no verificaciones nuestras.

## Comprobaciones con navegador headless

Herramientas: Playwright Python con Chromium, el 2026-10-03. Primera lectura con viewport de 390 × 844 y agente de escritorio; segunda lectura de Destacamos con emulación iPhone 13. No confundir reducir viewport con emular dispositivo móvil.

- LoquoSex: portada HTTP 200. La ruta de preregistro redirige a `/?prm_open=1`; el DOM contiene campos de identidad y carga de documentos. No se envió el formulario ni se comprobó el servidor de validación.
- Destacamos: portada HTTP 200 y diálogo visible de declaración de mayoría de edad. La entrada de publicación muestra formulario de acceso. Con emulación móvil, la raíz redirige a `/listings.html`; es una diferencia observada de navegación que requiere considerar consistencia de URLs si se estudia su SEO. No se ha auditado su canonicalización.
- MálagaCitas: `.com` produjo timeouts; el dominio correcto `.es` fue confirmado después y permitió revisar portada, grupos y fichas individuales.

Se guardaron capturas y lecturas temporales fuera del repositorio para inspección; no constituyen un archivo de anuncios ni se incorporan datos de personas a `docs/`. La evidencia duradera de planificación es este resumen.

## Lectura para nuestro producto

Las siguientes son recomendaciones propias, no funcionalidades ya aprobadas ni características atribuidas a todos los competidores.

| Necesidad | Propuesta | Impacto arquitectónico |
| --- | --- | --- |
| Encontrar anuncios por territorio | Provincia, ciudad y zona normalizadas | Tablas de ubicación, índices y rutas públicas canónicas |
| Explorar | Tarjetas, filtros, paginación y ficha completa | Django renderiza HTML; HTMX mejora interacciones |
| Publicar y mantener | Formulario por pasos, borrador, fotos y revisión | Estados explícitos, permisos y versión aprobada |
| Contactar | Canales elegidos por anunciante | Separar contactos privados de los autorizados para exposición |
| Confianza | Verificaciones con significado visible | Edad, contacto y autorización se comprueban por separado |
| Visibilidad de pago | Destacados con inicio, fin y reglas claras | Entidades de promoción separadas del anuncio; pagos pendientes |
| Retención de visitantes | Favoritos y ocultación opcionales | Preferencias potencialmente sensibles; evaluar necesidad y privacidad |
| Gestión | Cuenta y perfil público separados | Roles de visitantes, anunciantes, agencias y moderadores pendientes |

## Oportunidades propuestas

- Una interfaz adaptable a móvil y escritorio con las mismas URLs y funciones.
- Publicación guiada, errores claros y conservación segura de borradores.
- Ubicaciones y tarifas estructuradas que eviten ambigüedad y resultados duplicados.
- Indicadores de verificación específicos, sin prometer que todo un perfil es fiable por una sola comprobación.
- Expiración y confirmación de vigencia para reducir anuncios abandonados.
- Moderación, denuncias y retirada con procedimientos medibles.
- Imágenes ligeras y listados paginados; no cargar todo el catálogo en portada.

Son objetivos del proyecto. No se afirma que las competidoras carezcan de ellos ni que nuestra futura implementación las supere sin mediciones.

## Consecuencias para alcance y legalidad

Las referencias concretan un directorio del sector adulto; no confirman por sí solas que el usuario apruebe todas sus categorías, contenido explícito, trabajo, alquiler, videollamadas o cobros. Resolver expresamente estos puntos.

No replicar textos legales, identidad visual, fotografías ni datos de usuarios. No asumir cumplimiento por la existencia de políticas o por el funcionamiento de una competidora. Diseñar nuestras condiciones sobre nuestros tratamientos, responsabilidades y operación efectiva; ver [marco legal](06-marco-legal.md).

No inferir stack, tráfico, rentabilidad, seguridad o eficacia SEO a partir del aspecto o de puntuaciones automáticas de terceros. Para comparativas posteriores: definir tareas, observar su ejecución y medir con un método reproducible.

## Preguntas derivadas

1. ¿Publicación por particulares, agencias o ambos?
2. ¿Perfiles estables con anuncios/promociones asociados, o anuncios independientes?
3. ¿Territorio inicial Málaga o toda España?
4. ¿Publicación gratuita con destacados de pago, o un modelo distinto?
5. ¿Qué categorías exactas se admiten y cuáles quedan fuera del MVP?
