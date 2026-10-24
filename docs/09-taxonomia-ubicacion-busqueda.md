# Taxonomía, ubicación y búsqueda

Consolidación posterior, 2026-10-20: [contrato14 v1.1](14-contrato-funcional-v1.md) y [matriz B00–B01](104-consolidacion-contrato-beta-b00b01-20261020.md) sustituyen la taxonomía profesional para beta por perfiles personales románticos. Mantener geografía y una publicación por persona; no crear servicios obligatorios. Atributos físicos voluntarios y preferencias privadas son ámbitos distintos y requieren contrato antes de persistirse. Las categorías y pendientes de las secciones siguientes son diseño histórico en los puntos sustituidos.

Actualizado: 2026-10-03. Estado: alcance general confirmado; modelo detallado propuesto.

Nota de lectura, 2026-10-09: diseño inicial conservado. El catálogo, ES/EN, cardinalidades y semántica de filtros se concretaron en [contrato14](14-contrato-funcional-v1.md), [contrato de borradores](contratos/04-borradores-catalogo-geografia.md) y [contrato de descubrimiento](contratos/08-descubrimiento.md), con aceptación local [CR-07](actas/02-cr07-local.md). La cobertura nacional real y su dataset/licencia siguen pendientes; próximos pasos únicamente en [seguimiento17](17-seguimiento-desarrollo.md).

Acuerdo posterior: toda España, ciudad/localidad obligatoria y CP opcional recomendado encarecidamente. Interfaz accesible en inglés; traducción de anuncios y lenguas de búsqueda pendientes. Una publicación por persona, también bajo agencia; desplazamientos y cambios de ubicación no justifican duplicarla.

## Alcance confirmado

El usuario quiere almacenar tipos de personas/perfiles, servicios y categorías equivalentes a las referencias revisadas, con filtros similares, búsqueda por descripción y ubicación diferenciada por comunidad autónoma, provincia, ciudad y zona. Sugiere código postal como precisión de zona; su equivalencia con barrio no está confirmada.

La intención de equivalencia funcional no aprueba automáticamente cada etiqueta literal, categoría de riesgo, campo sensible o contenido explícito. El catálogo definitivo debe normalizarse y comprobarse con la política de publicación y el marco legal.

## Taxonomía propuesta

Separar persona representada, cuenta gestora, perfil público y anuncio. Una agencia o cuenta no se debe modelar como si fuera necesariamente la persona del anuncio. Publicación por terceros y cardinalidades siguen pendientes.

| Concepto | Modelo propuesto | Notas |
| --- | --- | --- |
| Tipo de perfil/persona | Clasificación declarada para navegación | Familias equivalentes a los grupos de las referencias; lenguaje, opciones y tratamiento jurídico pendientes |
| Categoría | Catálogo con ID estable, slug y nombre visible | Acompañamiento, modelaje, masaje u otras categorías que se acuerden; no usar identidad personal como tipo de servicio |
| Servicio | Catálogo y relación con anuncio | Estado ofrecido/no ofrecido/no informado; evitar interpretar todas las etiquetas visibles como seleccionadas |
| Modalidad | Presencial, online y otras que se acuerden | Independiente de categoría; no inferirla del título |
| Atributo | Campo tipado con opciones y aplicabilidad | Idiomas, disponibilidad, canales y otros; no un conjunto indiscriminado de tags libres |
| Promoción | Entidad de visibilidad temporal | Diferente de categoría y verificación |
| Verificación | Estado derivado de un procedimiento | No editable libremente por anunciante |

Usar identificadores que no dependan de los nombres visibles, alias para variaciones de escritura y reglas de campos por categoría. Mantener una matriz de equivalencias con las referencias y estados: admitido, pendiente o excluido. Trabajo, alquiler, terapias sanitarias, vídeos y contenido explícito necesitan decisiones propias; no se incorporan sin definirlos.

## Ubicación: árbol administrativo y código postal

Árbol administrativo propuesto: país → comunidad o ciudad autónoma → provincia → municipio. La interfaz puede denominar «Ciudad / localidad» al selector, pero debe guardar una referencia inequívoca. Si se necesita distinguir núcleos dentro de un municipio, añadir entidad de localidad; no equiparar siempre ciudad, localidad y municipio.

Dentro de municipio, zonas/barrios mediante catálogo controlado cuando exista una fuente fiable. Código postal separado: no tratarlo como hijo único de barrio ni asignar un solo código por municipio. Modelar asociaciones verificadas entre municipios/localidades y códigos postales; permitir varias correspondencias cuando los datos lo requieran. Barrios y zonas postales no son la misma delimitación.

La estructura debe contemplar comunidades uniprovinciales, ciudades autónomas y denominaciones oficiales/alternativas sin inventar provincias o municipios para completar selectores.

### Datos candidatos

- Territorio: tipo, código oficial, nombre, alias, slug y referencia administrativa padre.
- Municipio: código INE, provincia y estado de vigencia.
- Localidad: municipio y código oficial si existe; opcional según necesidad.
- Zona: municipio/localidad, denominación, fuente y estado; sin aceptar duplicados libres como ubicación canónica.
- Código postal: país y código como texto. Para España validar cinco dígitos y conservar ceros iniciales; el formato no demuestra existencia ni correspondencia.
- Asociaciones postales: código, municipio/localidad y fuente/fecha de actualización; no deducir municipio solo por prefijo postal.
- Ubicación de anuncio: municipio, localidad/zona opcionales, CP opcional coherente, precisión pública y vigencia si hay desplazamientos temporales.

Propuesta inicial: una ubicación principal por anuncio. Distinguir ubicación principal, desplazamientos y zonas atendidas. Anunciar atención en toda una provincia no significa estar físicamente en cada municipio. La publicación en varias ubicaciones queda pendiente para evitar anuncios duplicados.

### Privacidad

No recoger domicilio ni coordenadas exactas solo para poder filtrar. El CP puede reducir la zona a muy pocas personas o viviendas; evaluar exposición por contexto. Separar datos que sirven para filtrar y los que se muestran públicamente, dejando clara su utilización: si un filtro revela un CP asociado a un perfil, ese dato es observable aunque no se imprima en la ficha.

No garantizar anonimato por usar CP. La precisión permitida y el eventual mapa deben definirse antes de implementar. Por defecto propuesto: municipio/zona aproximada, sin puerta, domicilio o pin exacto.

## Búsqueda y filtros

- Búsqueda textual sobre título y descripción pública de la versión aprobada; idiomas de búsqueda pendientes.
- Filtros estructurados por perfil, categoría, servicios admitidos, comunidad, provincia, municipio/localidad, zona y CP.
- Selectores dependientes; cambiar provincia limpia municipios y zonas incompatibles. Seleccionar CP resuelve las opciones compatibles, sin escoger arbitrariamente una localidad.
- Combinar texto y ubicación mediante AND. Propuesta para opciones múltiples: OR dentro de una dimensión; servicios «cualquiera» o «todos» debe definirse expresamente y mostrarse en interfaz.
- Resultados limitados a anuncios públicos, vigentes y aprobados, con paginación y orden estable para desempates.
- Estado vacío claro y ampliación voluntaria de zona; no devolver anuncios de otra ciudad silenciosamente.
- Relevancia textual y promociones son reglas distintas. Si se monetiza el orden, etiquetar promociones y definir cómo se combinan con filtros.

No incluir cuentas privadas, verificaciones, contactos no públicos o versiones pendientes en índices de búsqueda. No almacenar un historial personal de búsquedas por defecto; los términos podrían revelar información sensible.

## Implementación propuesta con PostgreSQL

Full-text search para texto, con índices GIN y relevancia; evaluar `pg_trgm` para autocompletar, alias y tolerancia a errores. Definir tratamiento de acentos, sinónimos, términos y lenguas con pruebas representativas. Las extensiones y configuración siguen pendientes.

Índices sobre ubicaciones, estados y relaciones de categorías/servicios según consultas reales; comprobar combinaciones y paginación con planes de ejecución y pruebas de carga. Evitar un único filtro textual sobre descripciones para conceptos ya estructurados.

No necesitamos PostGIS solo para filtrar por código postal. Distancias reales, proximidad o mapas pueden justificarlo más adelante con datos geográficos autorizados. Distancia entre centroides no equivale a distancia exacta de un anunciante ni debe presentarse como tal.

## SEO propuesto

Rutas canónicas legibles por categoría y territorio, con identificadores internos estables. No crear automáticamente páginas indexables para cada combinación de servicios, CP y texto. Priorizar páginas útiles con inventario y contenido propio; fijar reglas para facetas, duplicados, paginación y retirada.

## Fuentes y gestión de datos geográficos

- [INE: municipios y códigos por provincias](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177031&idp=1254735976614&menu=ultiDatos): candidato para referencias administrativas; revisar actualización y condiciones de reutilización.
- [Correos: información de códigos postales y correspondencias](https://www.correos.es/es/es/herramientas/codigos-postales/detalle?query=30205%2C+ESP&searchtype=001): referencia postal. Consultar una herramienta no autoriza extraer o redistribuir masivamente su base de datos.
- [PostgreSQL: búsqueda de texto](https://www.postgresql.org/docs/current/textsearch.html).
- [PostgreSQL: trigramas](https://www.postgresql.org/docs/17/pgtrgm.html).

Seleccionar dataset o proveedor geográfico por cobertura, licencia, mantenimiento y coste. Registrar origen y versión, importar de forma repetible, detectar cambios y conservar referencias históricas cuando proceda. No hay datos descargados ni licencia seleccionada.

## Decisiones pendientes

1. Catálogo exacto de perfiles, categorías y servicios y sus equivalencias.
2. Fuente autorizada de códigos postales y zonas; criterio de «ciudad/localidad».
3. CP obligatorio u opcional y precisión observable permitida por contexto.
4. Una o varias ubicaciones por anuncio y manejo de viajes.
5. Reglas de filtros múltiples, relevancia, promociones y caducidad.

No se ha implementado esquema, importación ni buscador.
