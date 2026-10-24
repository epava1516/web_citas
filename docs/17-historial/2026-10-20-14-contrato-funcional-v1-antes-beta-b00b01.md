# Contrato funcional de desarrollo — versión 1

Fecha: 2026-10-03. Estado: especificación base definida por delegación expresa del usuario. Este contrato define comportamiento requerido; la implementación y aceptación se registran en [seguimiento17](17-seguimiento-desarrollo.md), bajo el [contrato de ejecución](16-contrato-ejecucion-desarrollo.md). No autoriza contratación ni despliegue externo.

## Autoridad y precedencia

El usuario autoriza decidir los pendientes buscando equilibrio y una experiencia familiar para quienes usan LoquoSex, Destacamos y MálagaCitas. Este documento cierra las decisiones funcionales de la primera versión. Sus decisiones sustituyen propuestas y preguntas anteriores sobre estos mismos puntos; conservarlas como contexto histórico, no como pendientes duplicados.

Se mantienen los acuerdos explícitos del usuario: toda España, inglés, una publicación por persona también bajo agencia, CP recomendado, control global de imágenes/teléfonos, observación de duplicados sin suspensión inmediata y preparación para monetizar con tarifas posteriores.

La delegación no permite inventar identidad del operador, comprar servicios, dar por cumplida la normativa ni declarar verificadas integraciones. Los pendientes externos se enumeran al final.

Formulación aclarada2026-10-09: desarrollo local autorizado desde 2026-10-03; [ejecución v1.6](16-contrato-ejecucion-desarrollo.md) consolida aceptación técnica con datos sintéticos y preparación de producción separada. Proveedores, políticas e identidades reales condicionan producción; los mecanismos locales deben funcionar y probarse con fixtures explícitos. [Copia anterior](17-historial/2026-10-09-14-contrato-funcional-v1-antes-consolidacion-contrato.md). El comportamiento MVP y sus objetivos se conservan.

## 1. Producto, territorio y lenguaje

Directorio nacional de perfiles/anuncios de personas adultas, gestionados directamente o por agencias, con descubrimiento por tipo, categoría, texto y geografía y contacto externo.

Interfaz, correos esenciales y mensajes de sistema en español e inglés. Español por defecto, selector persistente. Rutas públicas localizadas `/es/` y `/en/`; nombres de personas y lugares no se traducen arbitrariamente. Slugs con IDs internos estables para evitar perder enlaces al renombrar.

Un anuncio tiene descripción principal con idioma declarado y descripción alternativa opcional escrita por anunciante. No enviar textos a traductores externos ni traducir automáticamente en MVP. Si falta traducción, mostrar texto original y aviso discreto. Búsqueda sobre las descripciones públicas disponibles con configuración por lengua; no prometer encontrar sinónimos entre idiomas automáticamente.

Canonicalización, sitemap y `hreflang` según versiones realmente disponibles; evitar duplicados indexables solo por envoltura traducida con contenido idéntico. Nunca indexar áreas privadas o borradores.

## 2. Catálogo inicial y contenido

Tipo de perfil declarado para navegación: mujeres, hombres y opción trans, con asignación voluntaria y sin inferencias biométricas. Una mujer trans puede indicar mujer y etiqueta trans opcional; no exigir clasificación incompatible con su identidad. El dato puede tener especial sensibilidad: justificar finalidad, base jurídica y exposición antes de operar con datos reales. No presentarlo como servicio ni exigirlo para verificar edad.

Categorías iniciales:

| ID | Categoría | Oferta admitida en MVP |
| --- | --- | --- |
| CAT-001 | Modelaje | Fotografía, eventos y presentación de trabajos, con autorización de imágenes |
| CAT-002 | Acompañamiento social | Conversación, cenas, eventos y planes sociales sin oferta sexual |
| CAT-003 | Masajes de bienestar | Masaje relajante, deportivo no clínico y otras técnicas no sexuales, sin afirmaciones sanitarias no acreditadas |

«Premium» es visibilidad comercial, no categoría ni garantía de calidad de la persona. No crear «acompañantes de lujo» como duplicado de categoría: se puede describir posicionamiento sin generar otra publicación.

Servicios iniciales configurables: fotografía/eventos para modelaje; conversación, acompañamiento a cena/evento y planes culturales para acompañamiento; masaje relajante, deportivo no clínico y técnicas de bienestar admitidas para masajes. Catálogo administrado, versionado y traducido; no tags libres que creen nuevos servicios sin revisión.

Atributos filtrables: idiomas, días de disponibilidad, franja horaria, recepción/desplazamiento cuando corresponda, WhatsApp/Telegram, perfil con verificación específica y disponibilidad reciente. «Disponible ahora» es opt-in, caduca a las cuatro horas y requiere renovación explícita; no implica respuesta garantizada. No añadir filtros por raza, etnia o nacionalidad al MVP. Altura, peso u otros datos profesionales solo opcionales y pertinentes al modelaje, no filtros generales del directorio.

Contenido público inicial: fotos no explícitas, descripción sin oferta de actos sexuales y contacto autorizado. Excluir pornografía, desnudos íntimos explícitos, ofertas sexuales remuneradas, captación de personas para explotación, trabajo/alquiler del sector, terapias sanitarias no acreditadas, videollamadas adultas y venta de packs de contenido en esta versión. Tampoco valen eufemismos para publicar una oferta excluida.

Fundamento material: la [Ley General de Publicidad, art. 3](https://www.boe.es/buscar/act.php?id=BOE-A-1988-26156) incluye entre la publicidad ilícita la que promueva la prostitución. La existencia de competidoras o un aviso de «citas» no resuelve la admisibilidad de un anuncio. Este alcance conservador debe contrastarse sobre categorías, textos y operación real por asesoría antes de lanzamiento.

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

Una publicación activa por persona en toda la plataforma, sin duplicados por ciudad, categoría o agencia. Permitir varios servicios/categorías pertinentes en la misma publicación. Historial y revisiones no se muestran como anuncios activos adicionales.

Obligatorio: nombre público/alias, título, descripción, categorías/servicios, idioma, localidad/municipio, teléfono principal autorizado, al menos una foto aprobada y estado de verificación requerido. Tarifas admiten importe/moneda/duración/concepto, «desde» o «consultar»; la fila «consultar» no exige importe.

Opcional: descripción en otro idioma, CP, zona controlada, idiomas de atención, disponibilidad, tarifas múltiples, WhatsApp y Telegram. Email de cuenta privado; contacto por correo no público en MVP. No incluir URLs arbitrarias u otros canales en el campo de contactos; moderar su inclusión en texto para evitar eludir reglas.

Contacto público: teléfono y botones de WhatsApp/Telegram habilitados por anunciante. Antes de publicar explicar exposición y posibilidad de copia. Verificar control del teléfono; un número de agencia puede repetirse solo en sus publicaciones autorizadas. No anunciar protección total frente a scraping ni guardar contenido de conversaciones externas.

Ubicación: comunidad → provincia → municipio/localidad; no seleccionar libremente combinaciones incompatibles. Ciudad/localidad obligatoria; CP opcional con recomendación destacada y validación de correspondencia. Barrio/zona opcional. Sin domicilio, puerta ni coordenadas exactas.

Una ubicación principal. Zonas de desplazamiento se registran aparte; visita temporal cambia ubicación/vigencia sin duplicar anuncio. La precisión filtrable también es observable; comprobar riesgo de CP de baja población antes de exponerlo. No hay mapa o solicitud de geolocalización en MVP.

Fotos: hasta ocho aprobadas por anuncio, máximo inicial diez MiB por archivo y cuarenta megapíxeles, JPEG/PNG/WebP estáticos; sin GIF animado, SVG o PDF en fotos. Valores configurables a calibrar con pruebas de capacidad. Derivados públicos recodificados sin EXIF, originales privados según retención. Sin vídeos en MVP.

## 5. Publicación, verificación y moderación

Moderación híbrida: validaciones automáticas técnicas y de duplicación más aprobación humana para primer anuncio, cambios sensibles y conflictos. No delegar decisión final de casos dudosos exclusivamente en clasificador automático.

Verificar correo y teléfono; comprobar mayoría de edad y autorización de publicación de cada representado antes de activar anuncio. Preferencia para proveedor externo que devuelva evidencia mínima de comprobación; candidato Yoti, sujeto a cobertura, contrato, coste y modalidad. No aprobar por defecto estimación facial, comparación biométrica ni conservación propia de documentos. El mecanismo de identidad/titularidad se revisa aparte: prueba de edad no verifica todos esos extremos.

Guardar identificador de comprobación, resultado, fecha y versión de procedimiento; los documentos originales no van a logs ni a la carpeta de documentación. Si el proveedor no satisface el flujo, ese requisito queda sin cumplir: no sustituirlo por una casilla para lanzar.

Estados: borrador → procesando → pendiente de revisión → publicado. Pausado, rechazado, retirado y caducado son estados explícitos. Cambios sensibles producen nueva revisión: fotos, descripción, categorías/servicios, tarifas, gestor y contactos. Una revisión menor de horario/zona solo se publica si valida reglas y no hay señales de conflicto. La versión aprobada anterior permanece salvo retirada, compromiso o riesgo que exija pausar.

Vigencia inicial treinta días, renovación gratuita con confirmación de datos. Renovar no crea anuncio nuevo ni compra posición. Caducado no aparece en búsqueda/sitemap. Revisión de historial no impide borrado/retención legalmente procedente.

Duplicación: comparación global exacta/visual, independientemente de cuenta/número/tipo. No suspender cuenta inmediatamente por imagen; permitir correcciones y hasta tres revisiones/borradores pendientes por persona, sin crear personas ficticias para eludir límite. Conflictos entre perfiles no se publican mientras se revisan. Cuotas por agencia y velocidad de creación configurables, distintas de la unicidad de personas.

La carga total de una agencia nueva se limita inicialmente a diez perfiles pendientes, ampliables tras revisión de autorizaciones/capacidad. Las cargas fallidas y reintentos no consumen perfiles extra; registrar intentos sin conservar copias redundantes.

Denuncia sin registro, formulario limitado contra abuso, canal privado de contacto opcional y acuse cuando se facilita. Razones y reclamación trazables. Casos de menores, explotación o contenido no consentido prioritarios; restringir preventivamente contenido ante indicio creíble según procedimiento, sin esperar observación de bots.

Organización mínima antes de producción: moderador identificado con sustituto, alertas de casos urgentes y acceso restringido de emergencia. Objetivo interno inicial: revisar ordinarios en dos días laborables; alertar al responsable de casos urgentes al recibirlos. No prometer atención humana 24/7 si no existe cobertura ni tratar estos objetivos como sustitutos de plazos legales.

## 6. Búsqueda y experiencia familiar

Portada con selector territorial/categoría y acceso visible a publicar, entrar y gestionar. Tarjetas con foto, alias/título, zona, tarifa resumida y etiquetas concretas de contacto/verificación/promoción.

Filtros combinables: tipos de perfil declarados, categorías, servicios, territorio, CP, idiomas, disponibilidad y canal. OR dentro de una selección múltiple, AND entre dimensiones. Servicios con selector «cualquiera/todos»; por defecto cualquiera, con explicación visible. Texto sobre título/descripciones públicas disponibles.

Orden: con texto, relevancia; sin texto, fecha real de publicación/renovación, con desempate estable. Promociones solo dentro de resultados compatibles. No actualizar fecha editorial al comprar destacado. Paginación, veinticuatro resultados por página inicialmente, consultas indexadas y límites.

Favoritos incluidos con cuenta de visitante; no hay perfil público del visitante, reseñas o historial personal de búsquedas. Favoritos son privados, eliminables y sujetos a retención/derechos. No crear filtros de «verificado completo»: mostrar qué se comprobó realmente.

Interfaz responsive única, sin separar portales móvil/escritorio. Formularios guiados con pasos: datos/ubicación → contactos/tarifas → fotos → revisión/envío. Borrador guardado y errores claros. Navegación y publicación básica funcionan con HTML; HTMX mejora interacción.

## 7. Monetización preparada

Lanzamiento funcional gratuito, sin cobros activos. Preparar promociones configurables con estos tipos, familiares respecto a Destacamos:

| Tipo | Duración inicial configurable | Comportamiento |
| --- | --- | --- |
| Premium | Treinta días | Bloque patrocinado de máxima visibilidad dentro de filtros compatibles |
| Top | Diez días | Bloque patrocinado secundario |
| Autosubida | Siete o treinta días | Elevación temporal programada con frecuencia y cupos configurables |

Los precios no se inventan ni se muestran como cero/gratis: oferta sin precio/configuración válida no se vende. Promociones identificadas como patrocinadas, rotación equilibrada, sin prometer contactos o ranking SEO. Comprar no evita verificación/moderación ni permite más anuncios por persona.

Modelo preparado: producto/version, precio/moneda/impuestos, duración, pedido, intento de pago, estado de cobro y derecho de promoción. Importe fijado servidor al pedir, no recalculado retroactivamente cuando cambie tarifa. Idempotencia y webhooks firmados al integrar pasarela; interfaz de proveedor y modo de pruebas, sin cobro real en v1.

No monedero/créditos, suscripciones recurrentes o pagos por servicios de anunciantes en MVP. Elegir pasarela compatible con sector y definir devoluciones/fiscalidad/condiciones antes de activar ventas. Si anuncio se retira o pausa, no sigue promocionado; política de tiempo/reembolso pendiente de activación comercial y no se resuelve arbitrariamente en código.

Las autosubidas no crean revisiones o clones; su ejecución y ranking deben ser medibles y no recalcular todo el catálogo por tarea. Lo observado en competidoras informa duración/tipos, no acredita conveniencia de sus precios o textos legales.

## 8. Pantallas y alcance del MVP

MVP: primera versión usable y operable, no una demo sin controles.

| Pantalla/flujo | Resultado esperado |
| --- | --- |
| Inicio y listados | Elegir categoría/zona, buscar, filtrar, paginar y guardar favorito |
| Ficha pública | Consultar fotos, descripción, tarifas, contactos autorizados y denunciar |
| Registro/acceso/recuperación | Verificar correo, iniciar sesión y recuperar acceso con límites |
| Verificación/representación | Conocer requisitos y completar controles sin exponer identidad |
| Publicar/editar | Guardar borrador, añadir datos/fotos y enviar a revisión |
| Panel particular | Ver estado, motivo de revisión, pausar, renovar o retirar |
| Perfil/panel de agencia | Ver equipo y personas asignadas, gestionar una publicación por persona |
| Favoritos/cuenta | Gestionar preferencias privadas, sesiones, MFA y privacidad |
| Moderación | Revisiones, coincidencias, denuncias, decisiones y reclamaciones |
| Administración | Catálogos, territorios, productos inactivos y auditoría restringida |
| Legal/ayuda | Condiciones, privacidad, cookies, publicación, derechos y denuncias |

Incluidos: tarifas, fotos, favoritos, agencias, ES/EN, filtros, verificación, moderación, privacidad y preparación comercial.

Fuera de v1: mapa/geolocalización, chat interno, reseñas, reservas, vídeos, packs, pagos entre usuarios, traducción automática, app móvil, microservicios y cobros reales. Documentar futuras ampliaciones sin construirlas por anticipación.

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

Orden vigente de ejecución: [contrato de ejecución](16-contrato-ejecucion-desarrollo.md). Sustituye la secuencia inicial que sigue por entregas cruzadas CR-01 a CR-10, gate de separación GS-01, terminación frontend/backend y validación final común. Los criterios funcionales y gates de producción se mantienen.

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
