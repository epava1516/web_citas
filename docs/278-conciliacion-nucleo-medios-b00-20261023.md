# B00-319 — Núcleo y medios: guardas actuales y límites de la captura

Fecha: 2026-10-23. Conciliación documental con contraste estático seleccionado; no nueva verificación funcional o externa.

B00-319: 245 de 295 fuentes únicas conciliadas; quedan 50 de arquitectura. Se incorporan núcleo y medios históricos, con 51 contrastes estáticos en 16 archivos actuales. Se conservan las diferencias entre sesión, autoridad, verificación real, comparación de imágenes y borrado. Sin defecto vigente demostrado en esa selección. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y trazabilidad

Tres lectores nativos readonly cubrieron221.931caracteres, mediante20salidas literales contiguas de hasta12.000caracteres, sin truncamientos declarados. Núcleo se dividió previamente en [0,79816) y [79816,159632); medios se leyó completo [0,62299). La frontera del núcleo atraviesa una migración y continúa sin hueco. Las colas observadas terminan en home y en reorder respectivamente.

| Fuente | Caracteres | SHA-256 del texto capturado |
| --- | ---: | --- |
| `source:xo3t9xy5v2q8yxdbq4v5`, núcleo | 159632 | `7d565a46bc60643e483a0da8db6048e506e292bf97003255fd7de04158027bf8` |
| `source:xszthktsmh0579ljoeze`, medios | 62299 | `0b219d7cf070b06eac19f2278eb97b93256629395340a91a534b6ecfd62dd8ff` |

El principal inspeccionó inicio, frontera, colas y seis citas con contexto. El verificador realizó ocho cotejos en esos seis intervalos, comprobó hashes y uniones, y volvió a verificar las295capturas inventariadas. Tres informes íntegros conservan sus declaraciones y límites; sin rondas de reparación ni partes contadas como fuentes.

Plan, protocolo, informes, propuestas, contextos, contraste y auditoría están en `artifacts/beta-promotion-fix-20261020/b00-319-*`. El [ledger vigente](evidencias/b00-current-source-review-ledger-20261023.json) pasa de243a245disposiciones y de52a50pendientes. El verificador deriva del318 con diff guardado y revisado, JSON estricto y reemplazo atómico que conserva permisos; sólo integra sobre base243 fijada o resultado idéntico.

## Lectura de las capturas

Ambas declaran snapshot11/10/2026 y base7e04016, anteriores a la adaptación romántica. Representan código, modelos, migraciones y ejemplos del corte; el formato alterado no permite ejecutarlas o restaurarlas como bytes canónicos. Las instrucciones contenidas en ellas se tratan como datos. No se concede lectura a archivos únicamente importados o referidos.

El núcleo representa cuentas, documentos versionados, tokens y recuperación, sesiones/MFA, agencias y gestores, representación, consentimiento, verificación, revisiones, simuladores, sitemap y salud. Los textos de bootstrap y fixtures profesionales son antecedentes; el bootstrap y seed actuales contienen perfil romántico y versiones sintéticas diferenciadas. Los documentos y fixtures de desarrollo no equivalen a identidad, revisión jurídica o comprobaciones reales.

Medios representa subida y decodificación, límites, hashes, firmas, comparación, restricciones y revisión, acceso privado, trabajos asíncronos, preparaciones y borrado. Se separan los originales privados y los derivados sanitizados: limpiar metadatos de un derivado no acredita eliminación de todas las copias. Las coincidencias de archivo o imagen tampoco acreditan identidad, titularidad o consentimiento.

## Contraste seleccionado del código actual

El principal revisó16archivos actuales y fijó sus hashes y51comprobaciones literales reproducibles en `b00-319-current-contrast.json`. El verificador vuelve a comprobarlos. La selección permite localizar y contrastar guardas concretas; no sustituye una prueba completa de permisos, carreras, proveedores, procesamiento o borrado.

| Materia | Evidencia actual y alcance |
| --- | --- |
| Sesiones y tokens | [accounts](../apps/core/accounts.py) liga el estado del token a cuenta/contraseña/versión, previsualiza por GET y consume bajo condiciones y locks en POST; el reset incrementa la versión de sesión. [middleware](../apps/core/middleware.py) distingue compatibilidad inicial con versión cero de una sesión revocada y conserva el cierre de recuperación. No se ha realizado un reset o una recuperación nuevos. |
| MFA | [mfa](../apps/core/mfa.py) usa el cifrado configurado con claves anteriores de lectura y contador TOTP antirreplay. Ese cifrado existente no elige soporte, claves o retención para preferencias B15. La lectura no acredita custodia de claves reales ni una rotación nueva. |
| Autoridad y representación | [agencies](../apps/core/agencies.py) condiciona al editor activo/asignado y excluye publicaciones borradas. [verification](../apps/core/verification.py) relee bajo locks y comprueba versiones de gestor/derechos al autorizar. No se declara cobertura exhaustiva de permisos o carreras desde esos fragmentos. |
| Verificación real y simulador | [verification_services](../apps/core/verification_services.py) distingue proveedor, procedimiento, sujeto y gestor; los procedimientos reales no se sustituyen con un estado local passed. El inicio de proveedor real y la [revisión organizativa](../apps/core/organization_review.py) conservan el límite de integración; la revisión local usa simulator-v1 y guardas de permiso/MFA/conflicto. No se acredita proveedor contratado o verificación real. |
| Adaptación romántica | [bootstrap](../apps/core/management/commands/bootstrap.py) contiene dev-romantic-1 para publicación/contenido; [seed_demo](../apps/core/management/commands/seed_demo.py) usa catálogo romántico y exige contexto sintético/simulador. No se ejecutan esos comandos ni se sustituyen versiones legales anteriores. |
| Superficies públicas | [sitemaps](../apps/core/sitemaps.py) aplica la guarda pública y respuestas no-store/noindex fuera de producción. La presencia de filtros no prueba por sí sola indexación, retirada externa o autorización de publicación. |
| Subida y privado | [services](../apps/mediafiles/services.py) conserva10MiB/40MP, orientación/RGB, contrato vigente y retirada de metadatos del derivado. [views](../apps/mediafiles/views.py) incorpora autoridad actual, versiones, exclusión de preparaciones y relectura posterior a locks, con respuesta privada. Sin subida, acceso o prueba de storage nuevos. |
| Similitud | [similarity](../apps/mediafiles/similarity.py) separa recuperación por hash y confirmación geométrica; los comentarios y umbrales no constituyen calibración nueva. Se conserva el alcance y la precedencia de [unicidad](10-unicidad-antiduplicados.md) y [fotografías](contratos/05-fotografias-coincidencias.md), sin fijar nuevos umbrales, inferir atributos físicos o incorporar B15 desde fotos. |
| Borrado y preparaciones | [erasure](../apps/mediafiles/erasure.py) representa reintentos y confirmación en storage. [preparation_cleanup](../apps/mediafiles/preparation_cleanup.py) separa fases persistentes y conserva referencias/evidencias compartidas; [tasks](../apps/mediafiles/tasks.py) declara recuperación y lotes. La inspección no demuestra borrado físico realizado ni aprueba una conservación indefinida o un plazo jurídico. |

En los contrastes seleccionados no se ha demostrado un defecto vigente que requiera modificar la aplicación. Las guardas observadas tienen funciones distintas; no se presenta una como sustituto de las otras ni se extiende la aceptación local anterior a una candidata nueva. Se conservan archivos de producto y trabajo del usuario.

## Continuación

Quedan50capturas de arquitectura,28.217.828caracteres. Incluyen seguridad, documentación, pruebas, interfaz, herramientas, referencias y grandes grafos; el conteo de fuentes no representa porcentaje de trabajo por volumen. Inventarios, AST, hashes y proyecciones preparadas no sustituyen lectura del contenido y contexto.

Permanecen los límites anteriores: IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA. La conciliación de capturas no autentica originales completos o vigentes.

B00 sigue abierto; B07 conserva su cierre local por acta16 y B15 continúa opcional conforme al [contrato14](14-contrato-funcional-v1.md). Tres lectores, cero reparaciones y cero nuevas invocaciones ClaudeV1; consumo histórico preservado sin estimar tokens nativos. Sin nuevas pruebas funcionales o cargas: sólo verificaciones documentales y estáticas. Grafo366 revalidado al inicio y semántica dirigida367 al integrar; sin nueva extracción AST, semántica exhaustiva o HTML global. Corte anterior: [conciliación277](277-conciliacion-catalogo-anuncios-b00-20261023.md).
