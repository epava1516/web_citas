# CR-07 — Descubrimiento, interfaz en curso

GET /{es|en}/ conecta listado y filtros SSR. GET únicamente, datos reales PostgreSQL; formulario incorrecto400, página fuera de resultados404. No normalizar una página inválida hacia otra silenciosamente. Sin historial personal de búsquedas ni trackers. Cache-Control no-store mientras se conserva retirada inmediata.

Wireframe: portada/listado → formulario de texto/categoría/territorio → resultados compatibles → tarjeta/ficha pública; vacío ofrece cambiar filtros/ampliar área voluntariamente, sin introducir otra ciudad por defecto. Idioma explícito en URL; categorías/servicios ES/EN y descripción alternativa cuando corresponde.

Campos GET: q (máximo200), profile/category/service, services_mode any/all (defecto any), region/province/city/zone/postal_code, language/day/time_slot/channel, reception/travel/available; selecciones múltiples. OR dentro de dimensión, AND entre dimensiones; servicios all requiere cada servicio seleccionado. Catálogo activo; ubicación incompatible rechazada. CP filtrable únicamente cuando public_safe; no usar CP privado para descubrir personas por triangulación.

PostgreSQL full-text: título con pesoA, descripciones públicas con pesoB; configuración spanish/english según idioma de cada texto y consulta en ambos idiomas. Solo approved_revision; ningún borrador/contacto/cuenta en vector. Con texto orden por relevancia y fecha real, desempate UUID; sin texto fecha real y UUID. Veinticuatro por página, page entero positivo hasta100000. Enlaces mantienen selecciones; entrada inválida no produce resultados.

La elegibilidad completa se revalida antes de contar/paginar, incluida autorización revocada, vigencia, verificación, campos/catálogos/contacto/fotos y conflicto confirmado. Implementación inicial examina todos los candidatos compatibles; esto garantiza conteos correctos pero todavía no cumple el objetivo de carga. Optimización por lotes/índices/proyección e invalidación pendiente B-B, conservando esta semántica y sin truncar resultados arbitrariamente. No se acredita rendimiento por pruebas pequeñas.

Pendientes CR-07: ficha ES/EN completa/canales/atributos/tarifas, etiquetas de comprobaciones concretas, selectores dependientes, navegación/paginación positiva de múltiples páginas, pruebas de ranking/privacidad combinadas y cierre común. SEO/estilo final y rendimiento siguen B-F/B-B; promociones solo CR-10. Cobertura geográfica de muestra, no España completa acreditada sin dataset autorizado.
