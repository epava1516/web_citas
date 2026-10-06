# SEO y competitividad

Actualizado: 2026-10-06. Estado: implementación técnica parcial local; estrategia y aceptación integral pendientes.

## Diseño técnico

- HTML público rastreable, URLs estables, títulos y descripciones pertinentes.
- Sitemap limitado a páginas públicas canónicas y publicadas.
- Estrategia explícita para filtros, paginación, duplicados y anuncios retirados; evitar generar combinaciones ilimitadas indexables.
- Páginas geográficas únicamente cuando tengan inventario y valor real; no crear páginas vacías para captar búsquedas.
- Imágenes optimizadas, dimensiones declaradas y rendimiento medido con usuarios reales cuando exista tráfico suficiente.
- Datos estructurados solo si representan contenido real y cumplen las políticas del tipo utilizado; no prometer resultados enriquecidos.
- Áreas privadas protegidas mediante autenticación. `robots.txt` no es un control de acceso.

## Particularidades del sector

Evaluar las políticas de buscadores para contenido adulto y la clasificación real de las páginas antes de diseñar adquisición, indexación y marcado. No asumir que esta plataforma tendrá la misma visibilidad que un directorio generalista.

Conservar coherencia entre SEO y privacidad: no exponer información privada para obtener posicionamiento. Una página pública puede aparecer en buscadores y ser copiada por terceros.

## Ventaja competitiva

Referencias identificadas por el usuario: LoquoSex, MálagaCitas y destacamos.net. Revisión preliminar en [referencias de competencia](07-referencias-competencia.md). Comparar relevancia de resultados, anuncios actualizados, confianza y verificación, velocidad, facilidad de publicación y contacto, moderación y soporte. No hay mediciones comparativas realizadas.

Métricas propuestas: anuncios válidos activos, tiempo hasta publicación, búsquedas sin resultados, contactos iniciados sin guardar su contenido, denuncias y tiempo de resolución, rendimiento móvil y tráfico orgánico cualificado. La instrumentación debe respetar la privacidad.

No garantizar posiciones ni superioridad competitiva. Establecer objetivos medibles tras estudiar mercado y capacidad operativa.

## Fuentes

- [Core Web Vitals y búsqueda, Google](https://developers.google.com/search/docs/appearance/core-web-vitals).
- [Guía SEO para desarrolladores, Google](https://developers.google.com/search/docs/fundamentals/get-started-developers).


## Implementación local y operación

SEO-PREP-01 aporta title/description/canonical/hreflang de catálogo y fichas públicas; filtros/privados noindex, desarrollo noindex y versiones de contenido reales según revisión aprobada. [Evidencia](evidencias/seo-publico-preparacion0110.json).

SEO-PREP-02 añade `/robots.txt`, `/sitemap.xml`, `/sitemaps/directory.xml` y `/sitemaps/listings/<page>.xml`. URLs absolutas desde PUBLIC_ORIGIN configurado, nunca desde Host. Cada candidato se verifica con publicly_visible; estados retirados/caducados/revisión privada/consentimiento revocado no aportan URLs públicas. Los idiomas comparten la misma función de disponibilidad que canonical/hreflang: una ficha sin traducción diferente solo aparece en su idioma original. No se incluyen búsquedas, contactos, pendientes ni rutas privadas. No se inventan lastmod.

Cada documento de anuncios procesa100 candidatos (hasta200 URLs de idioma); índice con máximo50000 referencias incluyendo catálogo, HTTP503 si se supera la capacidad, sin truncar URLs silenciosamente. La paginación por offset puede desplazarse si cambia el inventario entre peticiones; se reconstruye en cada petición con no-store y vuelve a validar visibilidad. Consulta y latencia a gran volumen siguen sujetas al gate de rendimiento; la paginación no lo acredita por sí sola.

Desarrollo: robots bloquea todo y documentos XML tienen X-Robots-Tag noindex/nofollow. Producción: robots declara sitemap y excluye prefijos privados ES/EN; no sustituye autenticación ni las políticas noindex de las páginas. No activar producción con proveedores/identidad/legalidad ficticios. La rama de robots de producción se prueba como política, no como verificación de proveedor real.

HTTP PostgreSQL5 y navegador móvil1 correctos en runs separados; [evidencia](evidencias/sitemaps-preparacion0110.json). Acabado visual, landings geográficas, mediciones comparativas y aceptación GS01/BF/BB siguen pendientes. El marcado de fichas públicas se entrega en SEO-PREP-03 descrito abajo. Runtime y cola vigentes en [seguimiento único](17-seguimiento-desarrollo.md).


## Datos estructurados de fichas públicas — SEO-PREP-03

Entrega completa local integrada/desplegada96b57cf. El JSON-LD describe un WebPage sobre un Person usando exclusivamente el alias público y título/descripción de la revisión aprobada, idioma disponible y URL canónica desde PUBLIC_ORIGIN. No añade campos de contacto, tarifas, documentos, identificadores de cuenta, valoraciones, comprobaciones o fechas comerciales. No declara empresa/local físico, oferta o resultado enriquecido. La misma autorización de la ficha decide si hay página; retirados/caducados/consentimiento revocado no generan marcado. El fallback sin traducción, listados y rutas privadas no lo incluyen. Desarrollo conserva noindex.

El serializador escapa <, > y & y conserva JSON válido como bloque de datos application/ld+json; no relaja CSP, no ejecuta JavaScript ni carga dependencias externas. HTTP PostgreSQL, Chromium móvil ES/EN y regresiones SEO/sitemap:15 correctas,0 fallos/errores/omitidas sobre fuente36f4d57; comprobadas inyección de cierre de script, traducciones, privacidad y retirada. [Informe y huellas](evidencias/seo-estructurado-preparacion0110.json). [Runtime](evidencias/seo-estructurado-runtime0110.json):109 archivos coincidentes en3 servicios, checks/migraciones/HTTP/configuración; tiempos de integración/runtime observados desde inicio. Recursos de prueba retirados; no aceptación productiva, de capacidad ni fases GS01/BF/BB.

Semántica contrastada con [WebPage de Schema.org](https://schema.org/WebPage); contenido visible y ausencia de garantía de resultados conforme a las [directrices generales de datos estructurados de Google](https://developers.google.com/search/docs/appearance/structured-data/sd-policies). La condición de bloque inerte sigue el [elemento script del estándar HTML](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element), comprobada además en Chromium bajo nuestra CSP. No atribuir elegibilidad de búsqueda para contenido adulto ni superioridad competitiva a esta prueba local. No reabrir el marcado correcto para ampliar tipos sin un requisito concreto.
