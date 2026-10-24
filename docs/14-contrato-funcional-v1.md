# Contrato funcional de desarrollo — versión 1.1 hacia beta

Origen: 2026-10-03. Consolidación: 2026-10-20. Estado: especificación funcional vigente hacia beta, adaptada por instrucción expresa del usuario; implementación de los cambios en curso, sin aceptación beta. Este contrato define comportamiento requerido; la implementación y aceptación se registran en [seguimiento17](17-seguimiento-desarrollo.md), bajo el [contrato de ejecución](16-contrato-ejecucion-desarrollo.md). No autoriza contratación ni despliegue externo.

## Autoridad y precedencia

Las aclaraciones expresas del usuario del 2026-10-20 fijan el producto como clasificados de perfiles adultos que buscan citas románticas, sin anuncios de encuentros sexuales; incluyen renovación, Top y otras promociones, panel centrado en rellenar el perfil y posibles recomendaciones por gustos físicos. Las referencias LoquoSex, Destacamos y MálagaCitas informan mecánicas de clasificados; no aprueban su contenido, categorías, lenguaje o prácticas comerciales.

Esta versión sustituye el catálogo profesional, las tarifas de servicios y el recorrido correspondiente de la versión anterior. [Copia íntegra anterior](17-historial/2026-10-20-14-contrato-funcional-v1-antes-beta-b00b01.md), [matriz de decisiones y adaptación](104-consolidacion-contrato-beta-b00b01-20261020.md), [roadmap](103-roadmap-beta-clasificados-20261020.md). El [alfa aceptado](actas/10-entrega-tecnica-local-alpha-20261020.md) se conserva según su corte: adaptar el requisito no acredita que el código ya lo implemente ni reabre retroactivamente su aceptación.

Se mantienen los acuerdos explícitos del usuario: toda España, inglés, una publicación por persona también bajo agencia, CP recomendado, control global de imágenes/teléfonos, observación de duplicados sin suspensión inmediata y preparación para monetizar visibilidad con precios posteriores.

La delegación no permite inventar identidad del operador, comprar servicios, dar por cumplida la normativa ni declarar verificadas integraciones. Los pendientes externos se enumeran al final.

Formulación aclarada2026-10-09: desarrollo local autorizado desde 2026-10-03; [ejecución v1.6](16-contrato-ejecucion-desarrollo.md) consolida aceptación técnica con datos sintéticos y preparación de producción separada. Proveedores, políticas e identidades reales condicionan producción; los mecanismos locales deben funcionar y probarse con fixtures explícitos. [Copia anterior](17-historial/2026-10-09-14-contrato-funcional-v1-antes-consolidacion-contrato.md). Las garantías técnicas y objetivos no modificados se conservan. Las diferencias funcionales hacia beta se identifican en esta versión y en la matriz B00–B01.

## 1. Producto, territorio y lenguaje

Portal nacional de clasificados de perfiles de personas adultas que buscan citas románticas. El visitante consulta anuncios y contacta por los canales externos autorizados; el anunciante completa y mantiene su perfil y gestiona su exposición. No se exige matching recíproco, chat interno ni un perfil público del visitante.

La gestión directa es el recorrido principal. Se conserva la representación por agencias previamente autorizada, con una publicación por cada persona, consentimiento directo y controles vigentes; una agencia no ofrece servicios profesionales ni vende citas a través del perfil. Sus herramientas de equipo no complican el panel particular.

Interfaz, correos esenciales y mensajes de sistema en español e inglés. Español por defecto, selector persistente. Rutas públicas localizadas `/es/` y `/en/`; nombres de personas y lugares no se traducen arbitrariamente. Slugs con IDs internos estables para evitar perder enlaces al renombrar.

Un anuncio tiene descripción principal con idioma declarado y descripción alternativa opcional escrita por anunciante. No enviar textos a traductores externos ni traducir automáticamente en MVP. Si falta traducción, mostrar texto original y aviso discreto. Búsqueda sobre las descripciones públicas disponibles con configuración por lengua; no prometer encontrar sinónimos entre idiomas automáticamente.

Canonicalización, sitemap y `hreflang` según versiones realmente disponibles; evitar duplicados indexables solo por envoltura traducida con contenido idéntico. Nunca indexar áreas privadas o borradores.

## 2. Catálogo inicial y contenido

Tipo de perfil declarado para navegación: mujeres, hombres y opción trans, con asignación voluntaria y sin inferencias biométricas. Una mujer trans puede indicar mujer y etiqueta trans opcional; no exigir clasificación incompatible con su identidad. El dato puede tener especial sensibilidad: justificar finalidad, base jurídica y exposición antes de operar con datos reales. No presentarlo como servicio ni exigirlo para verificar edad.

Catálogo público de beta: perfiles para citas románticas. Modelaje, acompañamiento profesional, masajes y sus catálogos de servicios dejan de ser categorías de publicación. Profesión o aficiones mencionadas en la descripción no constituyen una oferta de servicios. No crear planes, servicios o nuevas categorías obligatorias para sustituir artificialmente los anteriores.

La adaptación B02 versionará el catálogo y revisará sus referencias antes de desactivar opciones antiguas. No renombrar un ID profesional para atribuirle retrospectivamente un significado romántico; conservar trazabilidad y bloquear la republicación automática de revisiones incompatibles. No borrar historial ni suprimir evidencias de autorización por cambiar categorías.

«Premium» y «Top» significan exposición comercial, sin garantía de identidad, conducta, disponibilidad o éxito romántico. La renovación y las autosubidas mantienen reglas distintas de vigencia y ordenación.

Atributos básicos de descubrimiento: tipo de perfil declarado, ubicación, texto, idiomas y canales autorizados. Días/franjas y «disponible ahora» son opcionales; sólo expresan información declarada para contactar o quedar, nunca una reserva o garantía de respuesta. Disponible ahora caduca a las cuatro horas y exige confirmación explícita. Recepción/desplazamiento profesional y tarifas no forman parte del perfil romántico.

Los atributos físicos pueden declararse voluntariamente para presentación y descubrimiento. Altura, complexión, color de pelo u ojos son ejemplos candidatos, no una lista de campos obligatorios ya implementada. Antes de añadir cada atributo se concretan opciones/unidades, finalidad, visibilidad y validación en CR04/CR07; «no indicado» no equivale a «no coincide». No inferir atributos de fotos, exigir medidas para publicar ni crear filtros por raza, etnia o nacionalidad. La comprobación privada de mayoría de edad y un eventual rango público de edad son datos distintos; no publicar fecha de nacimiento por esta ampliación.

Contenido permitido: presentación personal, intención romántica, fotografías no explícitas y canales de contacto autorizados. Excluir anuncios que propongan encuentros sexuales, remunerados o no; ofertas de servicios profesionales, precios por citas, pornografía, desnudos íntimos explícitos, explotación, coacción, suplantación, imágenes sin autorización, videollamadas adultas y venta de packs. No aceptar eufemismos o enlaces para eludir la política. El portal no promete controlar la vida privada de las personas fuera de los anuncios.

La política y los textos reales deben revisarse con la operación y el contenido antes de abrir a usuarios. La denominación «citas» o la ausencia de contenido explícito no acredita cumplimiento ni compatibilidad con proveedores.

## 3. Cuentas, personas y agencias

Roles: visitante, usuario registrado, anunciante independiente, titular de agencia, editor de agencia, moderador y administrador. Una cuenta puede tener permisos adicionales, sin autorizarse a sí misma privilegios de moderación.

- Independiente: representa una persona con una publicación activa.
- Agencia: perfil propio de organización gestora y varias personas, una publicación activa por persona. Mostrar «Gestionado por [agencia]» en ficha y tarjeta.
- Editor: invitación a su cuenta individual; gestiona anuncios asignados sin cambiar titular de agencia, ver documentos restringidos ni transferir personas.
- Titular: gestiona miembros y representación; sus facultades no sustituyen consentimiento de personas.
- Moderador: revisa contenido/denuncias, sin acceso indiscriminado a identidad legal.

MFA obligatorio para titular/editor de agencia, moderadores y administradores; disponible para particulares. Selección inicial: TOTP y códigos de recuperación protegidos; sin SMS como único segundo factor administrativo. Recuperación asistida con procedimiento trazable, no usando datos públicos como prueba.

Para representar una persona: agencia comprobada y autorización directa de la persona mediante flujo seguro, ligada a su verificación y a la finalidad de publicar. No solicitar exclusivamente a la agencia los documentos de todas las personas como única evidencia. Cada persona debe poder reclamar su perfil o revocar representación mediante canal propio aunque no tenga una cuenta de navegación.

Un gestor activo por persona representada. Transferencia requiere autorización directa y revisión; no crear perfil nuevo para trasladarlo. Se pausan las publicaciones afectadas mientras no haya gestor válido. Se conserva perfil/ID cuando sea procedente y se revocan accesos del antiguo equipo.

No afirmar que hashes de fotos permiten identificar de forma inequívoca a personas. Combinarlos con revisión/autorización, contactos y evidencias mínimas. Sin reconocimiento facial propio.

## 4. Anuncio, campos y ubicación

Una publicación activa por persona en toda la plataforma, sin duplicados por ciudad, tipo, preferencia o agencia. Cuenta y persona son entidades distintas: una agencia autorizada puede gestionar varias personas, una publicación por cada una. Historial, revisiones, renovación y promociones no crean anuncios activos adicionales.

Obligatorio para publicar: nombre público/alias, título, descripción personal y romántica, idioma, localidad/municipio, teléfono principal autorizado, al menos una foto aprobada y controles de verificación/autorización requeridos. La agrupación romántica se resuelve por el sistema, sin obligar a seleccionar categorías o servicios profesionales. El perfil no muestra tarifas por tiempo, por encuentro ni por servicios; los precios de promoción pertenecen al catálogo comercial del portal.

Opcional: descripción en otro idioma, CP, zona controlada, idiomas para comunicarse, disponibilidad declarada, atributos físicos definidos y habilitados conforme a la sección 2, WhatsApp y Telegram. Email de cuenta privado; contacto por correo no público en MVP. No incluir URLs arbitrarias u otros canales en el campo de contactos; moderar su inclusión en texto para evitar eludir reglas.

Contacto público: teléfono y botones de WhatsApp/Telegram habilitados por anunciante. Antes de publicar explicar exposición y posibilidad de copia. Verificar control del teléfono; un número de agencia puede repetirse solo en sus publicaciones autorizadas. No anunciar protección total frente a scraping ni guardar contenido de conversaciones externas.

Ubicación: comunidad → provincia → municipio/localidad; no seleccionar libremente combinaciones incompatibles. Ciudad/localidad obligatoria; CP opcional con recomendación destacada y validación de correspondencia. Barrio/zona opcional. Sin domicilio, puerta ni coordenadas exactas.

Una ubicación principal. Un cambio temporal de localidad cambia ubicación/vigencia sin duplicar anuncio; no publicar zonas de prestación de servicios como atributo del perfil romántico. La precisión filtrable también es observable; comprobar riesgo de CP de baja población antes de exponerlo. No hay mapa o solicitud de geolocalización en MVP.

Fotos: hasta ocho aprobadas por anuncio, máximo inicial diez MiB por archivo y cuarenta megapíxeles, JPEG/PNG/WebP estáticos; sin GIF animado, SVG o PDF en fotos. Valores configurables a calibrar con pruebas de capacidad. Derivados públicos recodificados sin EXIF, originales privados según retención. Sin vídeos en MVP.

## 5. Publicación, verificación y moderación

Moderación híbrida: validaciones automáticas técnicas y de duplicación más aprobación humana para primer anuncio, cambios sensibles y conflictos. No delegar decisión final de casos dudosos exclusivamente en clasificador automático.

Verificar correo y teléfono; comprobar mayoría de edad y autorización de publicación de cada representado antes de activar anuncio. Preferencia para proveedor externo que devuelva evidencia mínima de comprobación; candidato Yoti, sujeto a cobertura, contrato, coste y modalidad. No aprobar por defecto estimación facial, comparación biométrica ni conservación propia de documentos. El mecanismo de identidad/titularidad se revisa aparte: prueba de edad no verifica todos esos extremos.

Guardar identificador de comprobación, resultado, fecha y versión de procedimiento; los documentos originales no van a logs ni a la carpeta de documentación. Si el proveedor no satisface el flujo, ese requisito queda sin cumplir: no sustituirlo por una casilla para lanzar.

Estados: borrador → procesando → pendiente de revisión → publicado. Pausado, rechazado, retirado y caducado son estados explícitos. Cambios sensibles producen nueva revisión: fotos, descripción, tipo de perfil, atributos públicos habilitados, gestor y contactos. La migración de categorías antiguas también requiere revisión cuando cambie el contenido o significado público. Una revisión menor de horario/zona solo se publica si valida reglas y no hay señales de conflicto. La versión aprobada anterior permanece salvo retirada, compromiso o riesgo que exija pausar.

Vigencia inicial treinta días. Renovación gratuita con confirmación de los datos aprobados, disponible desde los últimos siete días o tras caducidad: conserva persona/anuncio/revisión, fija nueva vigencia de treinta días y fecha real de renovación para el orden orgánico. Un anuncio pausado conserva la pausa al renovar; uno caducado y elegible vuelve a publicado; uno retirado requiere nueva revisión. Renovar no crea anuncio ni compra Top o autosubida. Caducado no aparece en búsqueda/sitemap ni recomendaciones. Revisión de historial no impide borrado/retención legalmente procedente.

Duplicación: comparación global exacta/visual, independientemente de cuenta/número/tipo. No suspender cuenta inmediatamente por imagen; permitir correcciones y hasta tres revisiones/borradores pendientes por persona, sin crear personas ficticias para eludir límite. Conflictos entre perfiles no se publican mientras se revisan. Cuotas por agencia y velocidad de creación configurables, distintas de la unicidad de personas.

La carga total de una agencia nueva se limita inicialmente a diez perfiles pendientes, ampliables tras revisión de autorizaciones/capacidad. Las cargas fallidas y reintentos no consumen perfiles extra; registrar intentos sin conservar copias redundantes.

Denuncia sin registro, formulario limitado contra abuso, canal privado de contacto opcional y acuse cuando se facilita. Razones y reclamación trazables. Casos de menores, explotación o contenido no consentido prioritarios; restringir preventivamente contenido ante indicio creíble según procedimiento, sin esperar observación de bots.

Organización mínima antes de producción: moderador identificado con sustituto, alertas de casos urgentes y acceso restringido de emergencia. Objetivo interno inicial: revisar ordinarios en dos días laborables; alertar al responsable de casos urgentes al recibirlos. No prometer atención humana 24/7 si no existe cobertura ni tratar estos objetivos como sustitutos de plazos legales.

## 6. Búsqueda y experiencia familiar

Portada de clasificados con búsqueda territorial y por tipo de perfil, acceso visible a publicar, entrar y «Mi perfil». Tarjetas con foto, alias/título, zona y etiquetas concretas de contacto, comprobación y patrocinio; sin tarifas o servicios profesionales.

Filtros combinables: tipo de perfil declarado, territorio, CP permitido, idiomas, disponibilidad opcional y canal. Atributos físicos sólo después de definir e implementar su contrato específico. OR dentro de selección múltiple y AND entre dimensiones. Texto sobre título y descripciones públicas aprobadas. Categorías/servicios profesionales y sus parámetros dejan de ser filtros públicos; entradas antiguas deben tratarse explícitamente, sin relajar condiciones ni redirigir silenciosamente a resultados distintos.

Orden: con texto, relevancia; sin texto, fecha real de publicación/renovación, con desempate estable. Promociones solo dentro de resultados compatibles. No actualizar fecha editorial al comprar destacado. Paginación, veinticuatro resultados por página inicialmente, consultas indexadas y límites.

Favoritos incluidos con cuenta de visitante; no hay perfil público del visitante, reseñas o historial personal de búsquedas. Favoritos son privados, eliminables y sujetos a retención/derechos. No crear filtros de «verificado completo»: mostrar qué se comprobó realmente.

Interfaz responsive única, sin separar portales móvil/escritorio. Panel particular centrado en «Mi perfil»: completar datos y ubicación → contactos → fotos → revisar/enviar, con borrador guardado, previsualización privada y errores claros. La interfaz puede agrupar o guiar estos pasos sin imponer un número nuevo de pantallas. El anunciante no gestiona un catálogo profesional ni rellena tarifas de servicios. Estado, motivo de revisión y acciones de pausa, renovación y retirada permanecen accesibles; promociones son secundarias y no obligatorias. Navegación y publicación básica funcionan con HTML; HTMX mejora interacción.

### 6.1 Recomendaciones físicas opcionales

Posible ampliación B15, no requisito de aceptación de beta: perfiles que coincidan con preferencias físicas del visitante. Diferenciar atributos públicos declarados por el anunciante, filtros de búsqueda y preferencias privadas del visitante. El modo inicial propuesto usa preferencias explícitas y modificables; persistencia, catálogo exacto y reglas de ranking se decidirán antes de implementarlo. Este contrato no autoriza aprendizaje conductual, historiales íntimos persistentes ni inferencia por imágenes.

Recomendación, patrocinio y verificación deben identificarse por separado. Aplicar elegibilidad y retirada antes de mostrar o contar; excluir caducados, pausados y retirados aunque existan cachés o derechos promocionales. No relajar filtros obligatorios silenciosamente, inventar valores ausentes o prometer atracción recíproca. Sin resultados puede ofrecerse ampliar voluntariamente preferencias. No registrar gustos en logs, URLs públicas indexables o enlaces a mensajería.

Decisión posterior del usuario2026-10-23: ofrecer personalización opcional en la primera entrada, con decisiones diferenciadas de mayoría de edad/términos,cookies ypersonalización; configurable posteriormente y búsqueda normal disponible sin activarla. Para visitantes sin cuenta, recordar mediante cookies propias; contenido cifrado o identificador opaco y duración pendientes de diseño. Para cuentas registradas, evaluar preferencias cifradas en almacenamiento privado propio; no se decide aún entre base de datos y objetos. Prever modificación,borrado ydesactivación; no importar automáticamente preferencias del navegador a la cuenta. Cifrar no acredita por sí solo RGPD ni sustituye finalidad,base jurídica yconsentimiento aplicables. No se autoriza seguimiento conductual,inferencia desde fotos ni implementación inmediata. Catálogo,ranking,persistencia,claves yretención siguen pendientes. B15continúa opcional para beta.

## 7. Monetización preparada

Lanzamiento funcional gratuito, sin cobros activos. Preparar promociones configurables con estos tipos, familiares respecto a Destacamos:

| Tipo | Duración inicial configurable | Comportamiento |
| --- | --- | --- |
| Premium | Treinta días | Bloque patrocinado de máxima visibilidad dentro de filtros compatibles |
| Top | Diez días | Bloque patrocinado secundario |
| Autosubida | Siete o treinta días | Elevación temporal programada con frecuencia y cupos configurables |

Los precios no se inventan ni se muestran como cero/gratis: oferta sin precio/configuración válida no se vende. Promociones identificadas como patrocinadas, rotación equilibrada, sin prometer contactos o ranking SEO. Comprar no evita verificación/moderación ni permite más anuncios por persona.

Modelo preparado: producto/version, precio/moneda/impuestos, duración, pedido, intento de pago, estado de cobro y derecho de promoción. Importe fijado servidor al pedir, no recalculado retroactivamente cuando cambie tarifa. Idempotencia y webhooks firmados al integrar pasarela; interfaz de proveedor y modo de pruebas, sin cobro real en v1.

No monedero/créditos ni suscripciones recurrentes en beta. No pagos entre usuarios ni cobros por citas o servicios de anunciantes. La monetización preparada corresponde exclusivamente a visibilidad en el portal; autosubida no significa cargo recurrente. Elegir pasarela compatible con sector y definir devoluciones/fiscalidad/condiciones antes de activar ventas. Si anuncio se retira o pausa, no sigue promocionado; política de tiempo/reembolso pendiente de activación comercial y no se resuelve arbitrariamente en código.

Las autosubidas no crean revisiones o clones; su ejecución y ranking deben ser medibles y no recalcular todo el catálogo por tarea. Lo observado en competidoras informa duración/tipos, no acredita conveniencia de sus precios o textos legales.

## 8. Pantallas y alcance del MVP

MVP: primera versión usable y operable, no una demo sin controles.

| Pantalla/flujo | Resultado esperado |
| --- | --- |
| Inicio y listados | Elegir tipo/zona, buscar, filtrar, paginar y guardar favorito |
| Ficha pública | Consultar presentación personal, fotos, contactos autorizados y denunciar |
| Registro/acceso/recuperación | Verificar correo, iniciar sesión y recuperar acceso con límites |
| Verificación/representación | Conocer requisitos y completar controles sin exponer identidad |
| Publicar/editar | Guardar borrador, añadir datos/fotos y enviar a revisión |
| Mi perfil | Completar/editar un perfil, conocer estado y motivo; pausar, renovar o retirar; gestionar exposición por separado |
| Perfil/panel de agencia | Ver equipo y personas asignadas, gestionar una publicación por persona |
| Favoritos/cuenta | Gestionar preferencias privadas, sesiones, MFA y privacidad |
| Moderación | Revisiones, coincidencias, denuncias, decisiones y reclamaciones |
| Administración | Catálogos, territorios, productos inactivos y auditoría restringida |
| Legal/ayuda | Condiciones, privacidad, cookies, publicación, derechos y denuncias |

Incluidos hacia beta: perfil romántico, fotos, favoritos, representación autorizada, ES/EN, filtros básicos, verificación, moderación, privacidad, renovación y preparación de promociones. Recomendaciones físicas opcionales según sección 6.1. Las tarifas por servicios y el catálogo profesional quedan fuera del perfil.

Fuera de beta: mapa/geolocalización, chat interno, reseñas, reservas, vídeos, packs, pagos entre usuarios, traducción automática, app móvil, microservicios y cobros reales. Documentar futuras ampliaciones sin construirlas por anticipación.

Wireframes antes de implementar cada flujo, sin pedir al usuario decidir cada componente. Usar muestras sintéticas; no copiar anuncios o imágenes de personas de competidoras.

## 9. Arquitectura y selección de servicios

Base aceptada: Django, PostgreSQL, plantillas/HTMX, Celery/Redis, Pillow, Caddy, almacenamiento compatible con S3, Docker Compose, verificación automatizada local y observabilidad. [CI propio](ci-local.md), sin dependencia de pago ni despliegue automático. SHA-256 y huellas visuales/regionales con evaluación; sin MongoDB o reconocimiento facial propio.

Seleccionar versiones soportadas compatibles al preparar proyecto y registrarlas en ADR; no usar números de versión tomados de páginas históricas como decisión. Servidor WSGI inicial, candidato Gunicorn; ASGI solo si funciones lo requieren.

Primera instalación dimensionable: aplicación, workers y broker en servidor europeo; PostgreSQL separado preferentemente gestionado; objetos y backups fuera del servidor. Dos entornos, con pruebas protegidas y datos sintéticos. No alta disponibilidad de aplicación prometida en lanzamiento; diseñar para replicarla.

Candidatos de contratación, no contratados ni comprobados en este proyecto:

- OVHcloud europeo para cómputo/PostgreSQL/objetos, sujeto a servicio exacto, contrato y aceptación del contenido. [Contratos](https://www.ovhcloud.com/es/terms-and-conditions/contracts/).
- Bunny para distribución pública si las condiciones encajan. Su [política](https://bunny.net/acceptable-use/) admite contenido adulto legal sujeto a condiciones territoriales; no es autorización universal ni validación jurídica del catálogo.
- Yoti para comprobación de edad/evidencias mínimas; ofrece [soluciones para visitantes y creadores del sector adulto](https://www.yoti.com/adult-content-age-verification/), pero método, datos, biometría, transferencias y precio deben validarse.
- Correo transaccional vía SMTP/API configurable, sin promociones ni imágenes de anuncios en mensajes. Seleccionar proveedor tras aceptación del uso real; no asumir compatibilidad por limitar contenido del email.

Estas preferencias no bloquean scaffolding local con adaptadores y simuladores. No completar altas ni pagos sin datos/contratación del operador. Definir acceso de visitantes según contenido real y análisis normativo; aviso +18 no acredita edad ni sustituye obligaciones aplicables.

## 10. Operación y objetivos iniciales

Referencia de planificación para una posible producción futura: techo objetivo inicial de250EUR/mes de infraestructura recurrente, sin IVA, personal, asesoría, verificaciones por uso o pasarela. No es presupuesto disponible, precio cotizado ni autorización de gasto. El usuario indicó2026-10-09 que no dispone de dinero para CI: se usa infraestructura propia local. Una contratación futura requiere autorización y estimación real; no eliminar controles por coste silenciosamente.

Objetivos internos: RPO de una hora para datos de negocio, RTO de ocho horas ante incidente recuperable y vigilancia automatizada continua con responsables humanos definidos. No prometer SLA 24/7. Capacidad de alcanzar objetivos se comprueba con configuración y restauración; contratación debe encajar con presupuesto. Backups separados y cifrados, capacidad de recuperación de PostgreSQL al punto temporal y respaldo/versionado de medios con retención definida.

Prueba de carga inicial: diez mil anuncios sintéticos y veinte peticiones dinámicas por segundo durante quince minutos con mezcla de listados/fichas/búsquedas, además de cargas limitadas simultáneas. Objetivo servidor p95 inferior a 800 ms y errores inesperados inferiores al 1 % en entorno documentado. Son criterios de prueba propuestos por diseño, no previsión de visitas ni capacidad garantizada. Ajustar hardware/consultas hasta verificar o documentar cambio del objetivo.

Ejecución vigente: [criterios de lectura](16-contrato-ejecucion-desarrollo.md#16-consolidación-del-rendimiento-de-lectura--mod-04) y [arquitectura de estado almacenado](16-contrato-ejecucion-desarrollo.md#17-estado-de-publicación-almacenado--mod-05), consolidados en v1.6. El [marco de medición](criterios-revision-benchmark-carga.md) concreta población observable, generador, uploads, drain y gate corto completo previo a900s. Conservar recursos del ciclo; estado derivado aprobado, invalidación y evaluación nativa de lo no fiable son obligatorios. La prohibición anterior general de persistencia está sustituida. Los objetivos de carga siguen intactos; aceptación y límites se consultan en seguimiento17.

No contabilizar imágenes servidas por CDN como peticiones procesadas por Django. Medir frío/caliente y consultas difíciles. Objetivos frontend mediante pruebas móvil y Core Web Vitals cuando haya tráfico suficiente; no garantizar SEO por una puntuación de laboratorio.

Copias, retención, incidentes, seguridad y gates conforme a documentos 03, 06, 10, 11 y 12. No poner datos reales en logs, repositorio, pruebas o artefactos de CI.

## 11. Hitos y aceptación

La entrega del alfa queda aceptada en su corte y con sus límites. La continuación hacia beta sigue el [roadmap B00–B17](103-roadmap-beta-clasificados-20261020.md) y conserva las garantías del [contrato de ejecución](16-contrato-ejecucion-desarrollo.md). La secuencia original siguiente describe la entrega del alfa y no es una nueva cola; las referencias profesionales o a tarifas de servicios en ella quedan sustituidas para beta por las secciones anteriores. Los gates de producción se mantienen.

No hay fecha contractual de calendario: no se conoce disponibilidad de equipo. Se fija secuencia para no inventar una promesa:

1. Catálogo y wireframes, modelo de datos/roles, ADR y base Docker.
2. Cuentas/agencias, permisos, verificación con adaptador y recuperación.
3. Publicación, medios, tarifas, controles de duplicados y moderación.
4. Búsqueda nacional, ES/EN, favoritos, fichas y SEO técnico.
5. Promociones configurables inactivas y preparación de pagos.
6. Pruebas integradas/carga, revisión independiente, operación y ensayo de despliegue/restauración.

Cada hito incluye código, migraciones, pruebas significativas, documentación y demostración con datos sintéticos. No basta entregar pantallas: validar permisos, estados y recuperación. Gestión de cambios mediante nueva versión de contrato, señalando efecto en tiempo, coste y pruebas.

Gates de producción G-01 a G-08 siguen vigentes. La revisión independiente de seguridad se exige antes de producción; responsable/proveedor y coste aún externos. Hallazgos graves corregidos antes de operar; riesgos residuales documentados por el operador.

## 12. Pendientes externos y límites de la delegación

Ampliación confirmada: apartado legal público y aceptación específica de obligaciones de publicación, según [especificación del apartado legal](15-apartado-legal-publico.md). Incluye documentos ES/EN, reglas de contenido, denuncias, derechos y registros versionados. No exime al operador de sus obligaciones.

- Identidad y datos fiscales del operador, dominio definitivo, cuentas/contratos y credenciales reales.
- Revisión jurídica del catálogo concreto y tratamientos; privacidad, EIPD/DPD, contratos, retención y condiciones finales.
- Aceptación contractual y técnica de proveedores, costes reales y método de verificación que pruebe edad/autorización sin datos excesivos.
- Dataset postal/geográfico con licencia y correspondencias verificadas.
- Moderador, sustituto y responsables de incidentes, revisión de seguridad y disponibilidad del equipo para fecha de entrega.
- Tarifas, proveedor y condiciones comerciales para activar ventas; lanzamiento base sin cobros.

Son requisitos de preparación/producción. El desarrollo local está autorizado desde 2026-10-03 y se acepta con los mecanismos y pruebas técnicas del contrato 16; faltas de proveedor, identidad real o revisión jurídica no exigen reiniciar esa autorización ni impiden verificar localmente sus mecanismos. No permiten declarar listo para producción ni omitir controles técnicos pendientes.
