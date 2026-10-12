# Graphify: instalación, uso y límites

Fecha: 2026-10-04. Código analizado: `35b1f534`. Herramienta de desarrollo; no dependencia de la aplicación ni servicio de producción.

## Uso y límites vigentes — revisión documental 2026-10-09

Las secciones inferiores conservan la instalación, incidencia y análisis iniciales; sus cifras de corpus/grafo y límite Claude3/3 son históricos. [Contrato16 §15](16-contrato-ejecucion-desarrollo.md#15-delegación-sin-máximo-numérico--mod-03) elimina el máximo numérico desde el 2026-10-06, conservando todo el consumo previo y la obligación de usar el adaptador oficial. La incidencia original permanece registrada; esta revisión no añade llamadas Claude.

El [examen del 2026-10-09](evidencias/examen-graphify-20261009.json) consultó el grafo existente: 6.787 nodos, 32.151 relaciones y 200 comunidades; cero extremos ausentes y 88 autorrelaciones en el exportado. No fue una reconstrucción ni una auditoría funcional. Las referencias históricas a `ProjectedPublication` no describen el código vigente; se retiró con MOD-05. `ESTADO_ACTUAL.md` conserva un corte anterior a la aceptación local de lectura. Para estado actual prevalece [seguimiento17](17-seguimiento-desarrollo.md); para arquitectura, [docs02](02-arquitectura.md). Los datos globales del grafo no acreditan integridad de la extracción ni ausencia de pérdidas de relaciones.

La [revisión documental](evidencias/revision-documentacion-20261009.json) inventaría los enlaces de `17-historial/` que conservan la base original `docs/`, y su destino local resoluble. Esas copias tienen huellas registradas y se mantienen intactas; los enlaces a código retirado se identifican como referencias históricas sin destino vigente. El grafo completo no se ha actualizado por estas correcciones. Consumo de tokens de las consultas nuevas: no medido; se conserva el coste histórico, sin reemplazarlo por cero.

## Actualización local — 2026-10-11

Por petición directa del usuario, actualizado el grafo sobre `7e04016` con Graphify **0.9.64**, versión instalada en este equipo. Ejecutados `extract . --code-only --no-cluster --max-workers 2`, `cluster-only . --no-label` y `diagnose multigraph --json`, con `GRAPHIFY_NO_AUTO_REFRESH=1`. Se conserva el grafo previo en `/tmp/web-citas-graphify-backups/graphify-before-20261011.tar.gz`; Graphify también generó respaldo local en `graphify-out/2026-10-11/`.

Resultado final: **9.171 nodos, 39.230 relaciones y 314 comunidades**. Diagnóstico: cero extremos ausentes o colgantes, cero duplicados exactos y **122 autorrelaciones**. El agrupamiento transforma el grafo de extracción; sus cifras no prueban conservación de todas las relaciones originales. Se conservan nodos documentales previos, sin renovar su análisis semántico; se omitieron 334 documentos en esta extracción. Dos archivos SQL no aportaron nodos porque falta `tree_sitter_sql`; las plantillas `token.html` y `token_invalid.html` se omitieron por la heurística de datos sensibles. No se ejecutaron llamadas LLM ni se modificó la aplicación. HTML, informe y diagnóstico disponibles en `graphify-out/`, ignorado por Git. El paquete CLI no se actualizó en esta operación.

## Instalación y carga en la sesión

Fuente oficial: [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify), fuente inspeccionada `0b60d47e6cd9338c51143f39f35b6c45c8453385`. Paquete oficial PyPI **graphifyy**, comando `graphify`. Había una instalación CLI 0.8.32; se actualizó en un entorno uv aislado a **0.9.74**, sin alterar pyproject.toml/uv.lock de la aplicación.

```bash
uv tool install graphifyy==0.9.74
graphify install --platform codex
GRAPHIFY_NO_AUTO_REFRESH=1 graphify --version
```

Se revisaron find-skills y skill-installer. La fuente no contiene una carpeta instalable con SKILL.md: empaqueta `graphify/skill-codex.md` y referencias. Se utilizó su instalador nativo para obtener ambos en `/home/felidae/.codex/skills/graphify/`. Se leyó y aplicó el SKILL.md en esta sesión; no hizo falta reiniciar para ejecutar el procedimiento manualmente. El descubrimiento automático de la skill queda disponible en el siguiente turno; no se afirma haber recargado el catálogo de herramientas ni registrado un servidor MCP en caliente.

El CLI refrescó también copias preexistentes de las skills de Claude y OpenCode de 0.8.32 a 0.9.74, guardando SKILL.md.bak. No se modificó AGENTS.md, configuración de hooks ni el adaptador externo de arquitectura.

## Incidencia de delegación automática

La extracción `--code-only` es AST local y no utiliza LLM. **`cluster-only` sin `--no-label` sí puede autodetectar el CLI Claude y lanzar una llamada para nombrar comunidades, aunque no haya claves API.** El README y la skill no bastaban para descartar ese comportamiento del comando; se comprobó el código tras observar consumo en el informe.

En esta ejecución ocurrió una llamada de etiquetado automático: 64 comunidades, un lote con tamaño por defecto 100, respuesta completa; consumo registrado por Graphify **23.632 tokens de entrada y 890 de salida**, incluyendo caché según el contador del CLI. El prompt de esta ruta contiene nombres representativos de los nodos; el CLI puede añadir su contexto de proyecto. No se conserva un informe validado del adaptador ni se afirma conocer todo el contexto efectivo enviado.

La llamada eludió `scripts/claude-task`: **incumplimiento del procedimiento adoptado**, no revisión aceptada ni tercera delegación conforme. Se contabiliza conservadoramente como tercera invocación para agotar el límite 3/3 y continuar localmente sin otras llamadas Claude. Véase `.ai/tasks/desarrollo.md`. No hubo modificación del adaptador para resolverlo.

Para siguientes análisis, desactivar etiquetado automático explícitamente y no ejecutar las opciones semánticas, `label`, `update` sin código únicamente o hooks de reconstrucción automática.

## Ejecución reproducible local

```bash
GRAPHIFY_NO_AUTO_REFRESH=1 graphify extract . --code-only --max-workers 2
GRAPHIFY_NO_AUTO_REFRESH=1 graphify cluster-only . --no-label
GRAPHIFY_NO_AUTO_REFRESH=1 graphify diagnose multigraph
GRAPHIFY_NO_AUTO_REFRESH=1 graphify reflect --if-stale
GRAPHIFY_NO_AUTO_REFRESH=1 graphify explain publicly_visible
GRAPHIFY_NO_AUTO_REFRESH=1 graphify explain authorized_proof
```

La ejecución inicial de cluster-only no incluyó --no-label; es la incidencia anterior. El procedimiento recomendado sí lo exige. Con --no-label los nombres pueden quedar genéricos o proceder de etiquetas anteriores; no se presentarán como resultado de un nuevo LLM local.

Resultados locales en `graphify-out/`: graph.json, graph.html, GRAPH_REPORT.md, manifest.json, caché y lecciones. Excluidos de Git y del contexto Docker; se regeneran y no amplían la imagen de producción. El HTML se abre localmente; no se publicó ni contrató ningún servicio.

Corpus: **193 archivos de código**; se omitieron **91 documentos** con --code-only. No hay análisis semántico del contrato o contenido legal en este grafo. Se respetó gitignore; no se analizaron .env, medios privados, credenciales de demo ni resultados de delegación. Se omitieron siete archivos no clasificados (incluidos Dockerfile, Caddyfile, CSS y .env.example), y dos plantillas por la heurística de datos sensibles: token.html y token_invalid.html. Las plantillas y rutas dinámicas de Django no quedan verificadas exhaustivamente por AST.

Grafo: **1.185 nodos, 4.866 relaciones, 64 comunidades**. Informe: 83% EXTRACTED y 17% INFERRED; estas últimas son inferencias estructurales, no pruebas de comportamiento. No se detectan ciclos de importación en el grafo; eso no prueba su ausencia fuera del corpus o en imports dinámicos.

Diagnóstico sobre graph.json ya construido: cero extremos ausentes/colgantes, cero duplicados exactos y cero pares colapsados; **10 autorrelaciones**. No declarar «integridad perfecta»: el diagnóstico sobre el grafo final no mide pérdida de relaciones durante la extracción. Autorrelaciones y heurísticas se conservan como limitación, sin alterar código de la aplicación para satisfacer el grafo.

Se localizaron las diez autorrelaciones: métodos clean/__init__/save/create_option en accounts/agencies/core.models/discovery/forms/safety.views. La fuente llama `super().método(...)`; el AST ha representado esa llamada como relación del método consigo mismo. No es evidencia de recursión en la aplicación. Incluso una relación EXTRACTED requiere contrastar la resolución de símbolo antes de diagnosticar un defecto.

La repetición verificada con `cluster-only . --no-label` terminó correctamente y su informe registra cero tokens nuevos. El consumo anterior de etiquetado se conserva en esta acta y en el registro de delegación; cero tokens en el informe regenerado no borra ese consumo histórico.

## Consultas usadas para contrastar arquitectura

Se creó vocabulario desde etiquetas y se seleccionaron términos existentes:

- Visibilidad: publicly, visible, validate, submission, restriction.
- Derechos: authorized, proof, download, export.

Las consultas BFS con presupuesto 1.700 devolvieron 294 y 249 nodos, truncados; no se interpretaron como listado completo. Se estrechó con explain y se contrastaron los símbolos en código fuente.

`publicly_visible()` (`apps/listings/moderation.py:118`) es llamado por búsqueda (`discovery.py:236`), favoritos (`favorites.py:22,36`), ficha (`moderation_views.py:112`) y foto pública (`moderation_views.py:136`), y llama `validate_submission()` (`moderation.py:130`). Contrastado en fuente: comprueba estado/cabecera/caducidad y el validador incluye restricción activa, edad/representación/teléfono y requisitos del anuncio. Son conexiones EXTRACTED; no sustituye las pruebas HTTP ni la futura revisión de caché/CDN.

`authorized_proof()` (`apps/safety/rights_verification.py:65`) conecta con acciones de derechos y preparación de exportación. Contrastado: el proof queda ligado al scope/procedencia/caso/perfil/gestor/canal/versiones y el adaptador simulado no autoriza producción. La descarga tiene comprobaciones adicionales propias; no inferir una llamada directa a authorized_proof que el grafo no contiene.

Los nodos más conectados son User (137), Person (131), Revision (72), Listing (66), Agency (63) y RightsRequest (48). Son puntos de atención para cambios de permisos y versiones, no defectos por su grado. Una conexión entre el probe de retención y Person es coherente con el fixture sintético: no demuestra borrado completo del perfil.

## Resultado y continuación

Instalación y consultas verificadas; herramienta utilizable en esta sesión. El grafo ayuda a localizar dependencias. **No acredita seguridad global, cumplimiento jurídico, aceptación CR-09 o entrega completa.** La regresión común sobre 35b1f53 terminó con 285 passed y 1 failed en969.51s, sin skips. El fallo fue Page.reload «Not attached to an active page» en test_browser_listing_review_and_public_version; la reproducción aislada del código original pasó1/15.84s. Se añadió comprobación visible de la decisión y ausencia del formulario antes de iniciar recarga, conservando la prueba de persistencia y acceso público. No se presenta la reproducción aislada como286 pruebas correctas comunes ni se atribuye causa definitiva al navegador. Se continúa el contrato completo y la auditoría de requisitos pendientes, sin nuevas invocaciones Claude.

Verificación afectada tras sincronizar el navegador: **20 passed95.28s**, PostgreSQL/Chromium sin skips. Ruff, formato, manage.py check y diff-check pasan. La aplicación no se modificó por el grafo; no dar la común fallida por aprobada sumando esta batería.
