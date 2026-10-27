# Skills SEO y preparación de MCP Google — 26 de octubre de 2026

Instalación autorizada en conversación lateral mediante petición adjunta. Complementa la preparación de cinco fases; no continúa ni modifica el contrato principal, no abre beta y no acredita SEO productivo.

## Skills instaladas y adaptación

Repositorio [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), licencia MIT, commit fijo `e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b`.

| Skill | Versión metadata | Ruta |
| --- | --- | --- |
| seo-audit | 2.2.2 | `/home/felidae/.codex/skills/seo-audit` |
| site-architecture | 2.1.0 | `/home/felidae/.codex/skills/site-architecture` |
| schema | 2.0.2 | `/home/felidae/.codex/skills/schema` |
| programmatic-seo | 2.1.0 | `/home/felidae/.codex/skills/programmatic-seo` |

Instaladas mediante el helper oficial `skill-installer/scripts/install-skill-from-github.py`, con cuatro valores de `--path`, `--method download` y `--ref` fijado. No se ejecutó npx ni se instaló otra suite/CLI; no dependemos de la sintaxis múltiple del ejemplo npx. Los cuatro nombres existen actualmente; no se sustituyó schema por una skill distinta.

Se leyeron sus SKILL.md y se revisó su alcance. No se cargaron indiscriminadamente las referencias ni se ejecutaron evals upstream. Se conserva LICENSE en cada instalación. El helper no copia plugins, MCP, herramientas ni hooks del repositorio completo.

Adaptación local explícita al inicio de cada SKILL.md: sólo para web_modelos, consultar primero la política del proyecto y AGENTS/contrato vigentes; conservar alpha noindex, privacidad y alcance. El contenido upstream restante se conserva. Hashes upstream/instalado y cuatro diffs están en `skill-installation.json` y `*-local.patch` del directorio de preparación. Una actualización upstream debe revisar/reaplicar esa adaptación; no actualizar ciegamente.

Política central: `/home/felidae/.codex/skills/web-modelos-engineering/references/seo-policy.md`. Enlazada desde la referencia crecimiento de la skill propia. No se modificó AGENTS.md mientras el hilo principal trabaja. El manifiesto de cinco fases conserva sus hashes como evidencia histórica; la versión efectiva posterior de las referencias se identifica en el manifiesto SEO.

Las nuevas skills están instaladas en disco y validadas; estarán disponibles en el siguiente turno. Si otro hilo no las muestra, leer sus rutas explícitas o refrescar sesión. No afirmar que el catálogo de una conversación ya cargada las ha incorporado.

## Política SEO establecida para este proyecto

Alpha mantiene noindex; ninguna checklist genérica autoriza eliminarlo o abrir accesos. htmx actual observado2.0.11; htmx4 es dirección futura documentada. La configuración no migra frontend. Reutilizar contratos/evidencias SEO existentes en docs04 y259 con el seguimiento vigente; sus estados iniciales pueden ser históricos.

| Superficie | Política de preparación |
| --- | --- |
| Portada/categorías | Futuras candidatas sólo con contenido e inventario elegible y útil; sin landings vacías/duplicadas; alpha noindex |
| Anuncios/perfiles | Elegibilidad, privacidad y autoridad de publicación también en títulos, sitemap y JSON-LD; no inferir autorización de indexar de la existencia de una fila |
| Filtros | Limitar combinaciones y rastreo; canonical sólo de equivalentes reales; no generar miles de páginas de atributos o ubicaciones sin valor |
| Paginación | URL y enlaces HTML propios; canonical por página cuando corresponda, no páginas2+ a1 automáticamente |
| Cuenta y rutas privadas | Fuera de sitemap; noindex complementa, no sustituye permisos y aislamiento |
| Retirados/revocados/caducados | Retirada local inmediata de navegación, sitemap y marcado; conservar semántica contractual404/410/otra aplicable; sin redirecciones indiscriminadas a portada |
| ES/EN | Canonical/hreflang/sitemap coherentes; no inventar traducciones ni convertir fallbacks en páginas duplicadas para SEO |

Conservar respuestas contractuales: búsqueda válida vacía200, formulario inválido400, página fuera de resultados404. La orientación de Google sobre facetas no cambia estos casos automáticamente.

JSON-LD sólo describe contenido visible/autorizado. Mantener WebPage existente; no tratar personas como Product, inventar ratings/reseñas/ofertas o prometer rich results. Antes de añadir tipos, comprobar consumidor y soporte Google actual. Serializar con escape adecuado y CSP; HTML crudo puede contener JSON-LD servido por Django, mientras una extracción textual que omite scripts no demuestra ausencia. No enviar HTML privado a validadores públicos.

Los consejos upstream de3clics, longitud de títulos/descripciones, densidad de enlaces, subcarpetas, IDs/slugs o únicoH1 son heurísticas, no gates ni motivos automáticos para reescribir URLs. `seo-audit` contiene afirmaciones categóricas sobre locales/noindex/schema y menciona herramientas retiradas: contrastar documentación oficial actual y no importar esas recomendaciones como requisitos. No hay nueva tarea de contenido programático ni SEO competitivo.

[Google explica que noindex necesita rastreo para ser leído](https://developers.google.com/search/docs/crawling-indexing/block-indexing); robots no protege datos privados ni garantiza desindexación. La [guía de paginación](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading) trata páginas sucesivas como URLs propias. [Canonical](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) es una señal, y [marcado válido no garantiza rich results](https://developers.google.com/search/docs/appearance/structured-data/sd-policies). Estas referencias no autorizan abrir alpha.

## Evaluación MCP: Search Console

Fuente comunitaria MIT [AminForou/mcp-gsc](https://github.com/AminForou/mcp-gsc), corte `d49eea9e5efb5eb645b722249303179b2c150b49`, paquete declarado `mcp-search-console0.4.1`. Revisión acotada de README, pyproject y rutas de configuración/autorización/registro/gestión de herramientas de gsc_server.py; no auditoría completa ni validación funcional.

- Requiere propiedad explícita verificada y autorización de lectura, proyecto Google/API y credenciales. OAuth desktop o cuenta de servicio son alternativas pendientes; no se ha creado ninguna ni leído credenciales existentes.
- En el corte revisado, `SCOPES` pide `webmasters`, no `webmasters.readonly`. No hay variable de entorno observada que lo cambie. El campo scopes del cliente MCP no cambia el scope hardcoded de la librería Google.
- `GSC_ALLOW_DESTRUCTIVE=false` protege add/delete de sitio y delete_sitemap, pero `submit_sitemap` llama a la API sin ese guard; `manage_sitemaps` puede invocarlo. No presentar ese flag como modo completo de sólo lectura.
- Plantilla preparada con allowlist list_properties/get_search_analytics/get_sitemaps/inspect_url_enhanced y exclusión de altas/bajas/envío/gestión/reauthenticate. La allowlist cliente limita exposición de herramientas, no el alcance del token en Google. Antes de habilitar, resolver perfil de autoridad mínima y posible adaptación readonly revisada; no se parcheó ni ejecutó upstream.
- El módulo crea directorio de tokens al importarse y puede migrar un token antiguo. Por eso el análisis usó AST/texto, sin importar ni arrancar el servidor.

La plantilla propone futura cuenta de servicio con propiedad limitada y placeholders de rutas; no es una decisión adoptada de credenciales. Alternativa OAuth documentada: client secret desktop y tokens privados fuera de repo, consentimiento y scope revisados antes de conectar. La [documentación de autorización Google](https://developers.google.com/webmaster-tools/v1/how-tos/authorizing) describe scopes y requisitos; no se autorizó acceso a ninguna propiedad.

## Evaluación MCP: PageSpeed/CrUX

Fuente comunitaria MIT [ncosentino/google-psi-mcp](https://github.com/ncosentino/google-psi-mcp), corte `076bf1be1867e292137a00a1c4aafe420a3cf8e4`. Revisión acotada de README y configuración/registro/cliente Go; la implementación C# no se auditó. No binario descargado, instalado ni ejecutado; no handshake ni consulta Google.

- Servidor Go observado exige GOOGLE_PSI_API_KEY al arrancar, vía flag/env/.env. Preferir env y cwd aislado sin .env de la app; no pasar key en argumentos.
- Aunque [PSI API permite algunas consultas sin key](https://developers.google.com/speed/docs/insights/v5/get-started), esto no significa que el servidor revisado pueda arrancar sin ella.
- Pendientes URL pública autorizada, proyecto/API PSI, key restringida y cuotas; para CrUX directo, API habilitada y permisos de key, además de datos públicos suficientes. Google recomienda CrUX directo para datos de campo ante la futura retirada de ese contenido de PSI.
- Cada consulta comunica URL/origen a Google; no usar localhost, staging privado, URLs firmadas o perfiles/datos sensibles. Datos CrUX y resultados Lighthouse se mantienen separados; sin datos de campo no hay medición real de usuarios.
- Primera futura allowlist sólo analyze_page; analyze_pages y CrUX quedan deshabilitados hasta su alcance explícito. STDIO, sin servidor HTTP, servicio compartido o descarga/auto-update automático de binarios. Fijar versión/huella y verificar protocolo antes de activar.

## Plantillas y estado efectivo

Directorio `/home/felidae/.local/share/web-modelos-engineering-codex/seo-20261026`:

- `mcp-disabled.example.toml`: dos secciones enabled=false, sin secretos reales; GSC con fuente fijada por commit y rutas pendientes, PSI con binario pendiente. No fusionado en `/home/felidae/.codex/config.toml`.
- `marketingskills/`, `mcp-gsc/`, `google-psi-mcp/`: fuentes públicas acotadas y metadatos de procedencia; no instalaciones de servidor. No ejecutar archivos descargados por su presencia.
- `skill-installation.json`, cuatro patches y manifiesto: trazabilidad de instalación/adaptación.
- `verify-installation.py`, `verification.json` y `notifications.json`: evidencia local de preparación.

No hay herramientas GSC/PSI en el catálogo de esta sesión. Ambos quedan **evaluados y preparados, no instalados, registrados, conectados ni funcionalmente verificados**. No se han usado claves, tokens, APIs Google, cuentas, herramientas de envío/indexación ni datos reales. Configuración de cliente contrastada con [referencia oficial de Codex](https://learn.chatgpt.com/docs/config-file/config-reference): enabled=false y enabled_tools/disabled_tools; la sintaxis no acredita ejecución.

## Verificación terminal y alcance

PASS_INSTALLATION_ONLY: cuatro validaciones oficiales de SKILL.md;22archivos upstream contrastados por identificador Git blob (SHA1 usado sólo para identidad de objetos, no como firma o garantía de seguridad), SHA256 de archivos adaptados, referencias locales existentes, TOML parseable, dos servidores deshabilitados, allowlist GSC contrastada con AST. Sin importar el servidor ni abrir navegador/API/BD. Recibo Telegram terminal confirmado y conservado. La verificación no demuestra mejora SEO, compatibilidad de MCP real, seguridad integral ni producto listo.

Sin cambios de app, dependencias, CI, AGENTS, grafo, servicios o contrato; sin commits/push ni repetición de QA válida. Esta tarea sólo añade este registro al repositorio y crea/adapta las skills y materiales aislados indicados. Los cambios simultáneos del hilo principal quedan intactos.
