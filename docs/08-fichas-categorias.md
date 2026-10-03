# Publicaciones: categorías, campos, etiquetas y tarifas

Fecha de revisión: 2026-10-03. Estado: observación pública de una muestra, no catálogo exhaustivo ni requisitos aprobados.

## Método y cobertura

Se abrieron publicaciones individuales mediante Chromium headless y Playwright, leyendo DOM, campos, tablas y atributos de imágenes. En Destacamos se tomó la primera ficha enlazada en cada una de seis categorías; en LoquoSex tres publicaciones localizadas en portada; en MálagaCitas cuatro fichas de grupos/filtros diferentes. Es una muestra de conveniencia, con posible sesgo hacia anuncios destacados.

No se enviaron formularios, hicieron compras ni accedió a funciones privadas. No se guardan aquí nombres, teléfonos, usuarios de mensajería, fotos ni descripciones originales. Se usan códigos de muestra y el identificador público de publicación para trazabilidad; los listados cambian y las fichas pueden desaparecer.

Fuentes de entrada: [LoquoSex](https://www.loquosex.com/) y [Destacamos](https://www.destacamos.net/listings.html). Los hallazgos siguientes proceden de fichas individuales abiertas desde estas fuentes, no solo de sus listados. No se infieren servicios del título sin comprobar su categoría o marcado.

El usuario corrigió el dominio de MálagaCitas a [www.malagacitas.es](https://www.malagacitas.es/). Ese dominio es accesible; los fallos previos correspondían a `.com`. La revisión de `.es` se incorpora abajo.

## Destacamos: muestra por categoría

| Muestra | Categoría / entrada | ID público | Descripción resumida y atributos observados |
| --- | --- | --- | --- |
| D-01 | [Acompañantes](https://www.destacamos.net/1-chicas-escorts/listings.html) | 833507 | Presentación de varias personas, atención presencial, zona y disponibilidad. Ficha con idiomas, días, horario, edad, características físicas y profesión. |
| D-02 | [Masajes relajantes](https://www.destacamos.net/2-masajes-eroticos/listings.html) | 1236467 | Descripción de atención privada y masajes personalizados en dos idiomas. Ficha con idiomas, días, franja horaria, zona, edad y características físicas. |
| D-03 | [Terapias](https://www.destacamos.net/5-masajes-y-terapias/listings.html) | 87292 | Masaje deportivo y relajante, camilla y cita concertada. El texto incluye un intervalo horario concreto; la ficha lo resume mediante una franja genérica. Menos atributos que otras categorías. |
| D-04 | [Chicos de compañía](https://www.destacamos.net/7-chaperos-escorts-hombres/listings.html) | 1209531 | Presentación personal, masajes y desplazamiento descritos en texto libre. Datos de zona, edad, altura, peso y horario. |
| D-05 | [Videollamadas, chat y webcam](https://www.destacamos.net/6-linea-erotica-cibersexo-cams/listings.html) | 969565 | Oferta online, conversación, vídeos personalizados y packs de fotos en texto libre. Idiomas y canales externos; no se observó una plataforma de videollamada integrada. |
| D-06 | [Categoría trans y travestis del sitio](https://www.destacamos.net/3-travestis/listings.html) | 1229165 | Presentación, disponibilidad y experiencia anunciada en texto libre. Ficha con zona, idiomas, días, horario, edad, profesión y características físicas. |

Los términos de las categorías pertenecen al sitio observado; la taxonomía y el lenguaje de nuestro proyecto están pendientes.

### Estructura de ficha

En la muestra: categoría y territorio, título, teléfono y canales, zona, favoritos, compartir, fecha, contador de visitas, promociones, descripción, consejos de seguridad, atributos y denuncia con ID del perfil. Algunos atributos no están presentes en todas las fichas.

Campos observados en el conjunto: nombre público, teléfono, WhatsApp, Telegram, ciudad, zona, código postal, edad, idiomas, disponibilidad por días, horario, color de pelo, altura por intervalos, peso, profesión y nacionalidad.

Las etiquetas PREMIUM, TOP y Autosubidas indican visibilidad comercial, no verificación de identidad. Los canales aparecen como disponibilidad de contacto. Los favoritos no fueron activados ni se comprobó persistencia.

### Precios y servicios

No se observó una tabla de tarifas con importes por duración en las seis fichas abiertas. Los elementos HTML `table` extraídos no contenían filas de precios; no confundir tablas de maquetación vacías con una tabla comercial. Tampoco se identificó un precio estructurado visible en estas muestras.

Esto no demuestra que el sitio carezca de tarifas en otras publicaciones, imágenes o funciones privadas. Los precios de destacados descritos en condiciones comerciales son precios de la plataforma, no tarifas de los servicios anunciados.

Los servicios concretos de las muestras están principalmente en descripción libre. Los atributos de horario y disponibilidad sí tienen etiquetas propias. No afirmar que exista un catálogo uniforme de servicios seleccionados basándose en estas fichas.

## LoquoSex: muestra

| Muestra | ID público | Categoría real en ficha | Descripción resumida | Precio observado |
| --- | --- | --- | --- | --- |
| L-01 | 7165714 | Escort | Presentación personal, disponibilidad y oferta de acompañamiento en texto libre | «Consultar» |
| L-02 | 7208037 | Masaje | Camilla o tatami, masaje relajante/tántrico y atención personalizada; delimita parte de la oferta en la descripción | Precio mínimo: 50 €; sin duración estructurada |
| L-03 | 7182886 | Escort | El título anuncia modalidad online y conversación; sigue clasificado como Escort | «Consultar» |

Esta muestra cubre dos categorías reales, no tres: una modalidad anunciada en el título no constituye automáticamente una categoría independiente.

### Campos y secciones

Título, ID, categoría, edad, fecha, localidad, nacionalidad, sección de servicios, precio mínimo, contacto, descripción, avisos de seguridad y fotografías. No se extrajo una tabla HTML de precios en estas tres publicaciones.

### Catálogo de servicios y selección

La sección muestra quince etiquetas: 24h, Masajes, Fr Natural, Lesbisco, Sado BDSM, Hoteles / Domicilios, Beso en la boca, Griego, Duplex, Lluvia dorada, Viajes, Frances, Beso negro, Parejas y Fiestera. Se conservan aquí los rótulos del sitio para análisis de estructura; no son un catálogo aprobado del proyecto ni se desarrolla contenido descriptivo explícito.

**Hallazgo importante:** la lista textual completa aparece aunque no todos los servicios estén seleccionados. El DOM usa iconos `si.png` y `no.png` y atributos `alt` con SI/NO. Por tanto, extraer únicamente `innerText` atribuiría incorrectamente todas las opciones al anunciante.

En L-02 se comprobaron iconos afirmativos para Masajes, Hoteles / Domicilios y Frances y negativos para el resto del catálogo. No se interpreta esta selección como validación de la oferta real ni se resuelven por inferencia posibles diferencias con la descripción.

La distinción sí/no debe modelarse expresamente si adoptamos servicios estructurados. Debe poder distinguirse además «no indicado» de «no ofrecido».

## MálagaCitas: dominio `.es`

Se abrió una ficha por cada grupo principal y otra desde el filtro de masaje profesional. Este último es un filtro de características, no una cuarta categoría principal.

| Muestra | Entrada | ID público | Descripción resumida | Etiquetas de la ficha |
| --- | --- | --- | --- | --- |
| M-01 | [Chicas](https://www.malagacitas.es/) | 10070614 | Presentación personal, conversación y planes sociales; contacto por llamada o mensajería | Chicas con Whatsapp, Actividades fin de semana, Rostro visible, Latinas, Salidas y quedadas, Maduras |
| M-02 | [Trans](https://www.malagacitas.es/travestis) | 10045668 | Presentación personal, planes, deportes y viajes | Trans con Whatsapp, Latinas, Salidas y quedadas |
| M-03 | [Chicos](https://www.malagacitas.es/chicos) | 10060723 | Conversación, compañía y planes en texto libre | Chicos con Whatsapp, Actividades fin de semana, Salidas y quedadas, Latinos |
| M-04 | [Masaje profesional](https://www.malagacitas.es/masaje-profesional) | 77293 | Masajes en camilla, relajantes y varias técnicas; horario concreto y cita previa en descripción | Chicas con Whatsapp, Españolas, Maduras, Masaje profesional |

Rótulos reproducidos como etiquetas de análisis, no como clasificación aprobada de personas para nuestra app. Las credenciales o servicios declarados por los anuncios no se han verificado.

### Estructura observada

Título y zona, llamada/WhatsApp, edad cuando está informada, país representado con bandera, visitas, fotografías, indicación de fotos reales, descripción, bloque de características, ubicación, enlace de cómo llegar y denuncia. No todas las fichas tienen todos los valores. No interpretar edad ausente como edad cero ni como prueba de mayoría de edad.

En la portada se observan filtros de vídeo, WhatsApp, Telegram, idiomas, edad/nacionalidad, rostro visible, fines de semana, disponibilidad actual y desplazamientos. Son opciones de navegación; no todos aparecieron como etiquetas en las fichas muestreadas.

La interfaz ofrece búsqueda por dirección, mapa y geolocalización. No se otorgó permiso de ubicación ni se verificó exactitud de coordenadas. La publicación pasa por dominios de autenticación y administración separados; no se accedió al panel privado.

### Tarifas y servicios

En las cuatro fichas no se localizaron importes públicos estructurados ni tablas de precios; la extracción de elementos `table` fue vacía. Esto limita la observación a la muestra, no a todo el sitio.

La ficha de masaje enumera técnicas en la descripción y usa una etiqueta de masaje profesional. No se encontró una matriz de servicios sí/no equivalente a la de LoquoSex. Las descripciones de otras muestras están orientadas a presentación y compañía; no inferir servicios no expresados.

### Consecuencias propuestas

- Catalogar etiquetas mediante identificadores estables y nombres visibles, separando disponibilidad declarada de disponibilidad confirmada recientemente.
- Si se añade «disponible ahora», definir caducidad y actualización; no mantenerlo indefinidamente.
- Para mapa, usar zona aproximada por defecto y evaluar precisión, proveedor y exposición antes de implementar.
- Solicitar geolocalización del visitante solo por una acción explícita y con finalidad clara; evitar guardar coordenadas si basta una consulta puntual.
- La etiqueta de rostro visible no prueba identidad y fotos reales no sustituye autorización.
- Unificar cuenta, publicación y panel en nuestra experiencia; la autenticación compartida entre portales solo se justifica si acordamos varios portales.

## Taxonomía: observación frente a propuesta

Separar cinco conceptos:

1. **Categoría:** tipo de publicación.
2. **Modalidad:** presencial u online, recepción o desplazamiento, si finalmente se admite.
3. **Atributos:** idiomas, zona, disponibilidad y otros campos pertinentes.
4. **Servicios:** opciones anunciadas; catálogo sujeto a revisión de alcance y legalidad.
5. **Promociones y verificaciones:** estados generados por la plataforma; no etiquetas que cualquier anunciante pueda autoasignarse.

No trasladar automáticamente nacionalidad, rasgos físicos o categorías que puedan revelar información sensible. Evaluar finalidad, proporcionalidad y controles con el marco legal.

## Propuesta de tarifas para nuestra app

Aunque no se observó una tabla detallada en esta muestra, REQ-004 exige tarifas. Diseñarlas como datos separados de la descripción.

| Campo propuesto | Uso |
| --- | --- |
| Concepto | Nombre de la opción anunciada, sujeto a política de contenido |
| Modalidad | Si el alcance admite distintas modalidades |
| Duración y unidad | Minutos, horas u otra unidad definida; puede no aplicar |
| Importe decimal y moneda | Evitar errores de coma flotante |
| Tipo de precio | Exacto, desde o consultar; consultar no se convierte en cero |
| Condiciones | Información breve sobre suplementos o inclusiones cuando proceda |
| Orden y vigencia | Presentación y actualización |

Ejemplo **sintético**, sin extraer de un anunciante: «Sesión de masaje relajante — 60 minutos — 70 EUR — precio exacto». El ejemplo ilustra el esquema y no fija categorías admitidas, precios de mercado ni condiciones comerciales.

Separar tarifas anunciadas de los precios que cobra nuestra plataforma por publicar o destacar. No deducir duración a partir de un «precio mínimo» sin unidad.

## Consecuencias arquitectónicas propuestas

- Entidades distintas para categoría, atributo, servicio, tarifa, canal de contacto, disponibilidad, promoción y verificación.
- Definiciones de campos por categoría; evitar formularios idénticos con atributos irrelevantes o un JSON sin validación para todo el dominio.
- Una modalidad online puede coexistir con distintas categorías si así se define; no inferirla por palabras del título.
- Servicios normalizados con estado explícito y revisión; descripción libre complementaria.
- Borrador y versión pública aprobada también para tarifas, servicios, contactos y disponibilidad.
- Contrastar coherencia entre texto y campos antes de publicar; comunicar discrepancias al anunciante.
- URLs de ficha con identificador y slug, sin teléfono ni identidad legal en la URL de nuestro proyecto.

## Pendientes

- Ampliar MálagaCitas si se necesitan más muestras o estudiar su publicación privada; revisión pública inicial completada en `.es`.
- Ampliar muestra de LoquoSex a otras categorías si esas categorías interesan al MVP.
- Revisar fichas adicionales con precios detallados, si se localizan; no asumir que existen.
- Confirmar categorías, modalidades, campos públicos, personas/agencias y modelo de monetización.
- Decidir si se admite contenido online, contratación, vídeos o packs; observarlo en una referencia no lo incorpora al alcance.

La muestra describe contenido declarado y estructura pública, no autenticidad, autorizaciones, cumplimiento o calidad del servicio anunciado.
