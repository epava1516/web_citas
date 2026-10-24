# Graphify: instalación, uso y límites

## Referencia del estado actual — 2026-10-24

El corte verificable del grafo actual se consulta en `graphify-out/GRAPH_VERIFICATION.json`, `SOURCE_MANIFEST.json` y `ESTADO_ACTUAL.md`; [seguimiento17](17-seguimiento-desarrollo.md) fija el estado de ejecución. Las instalaciones, cifras y revisiones de 2026-10-04/09/11 conservadas abajo son antecedentes fechados, incluidos los apartados que entonces se denominaron vigentes. No describen automáticamente el grafo, la versión instalada o los permisos actuales.

Las actualizaciones recientes distinguen AST dirigido, semántica seleccionada y cobertura global; el sello registra sus límites. Consultar un grafo o conservar sus nodos no acredita lectura semántica completa, pruebas funcionales, capacidad o aceptación de beta. El historial de coste y la incidencia de delegación se conservan; las instrucciones posteriores y el contrato de ejecución rigen las invocaciones actuales.

## Capturas históricas en Open Notebook — conciliación 2026-10-24

La [conciliación295](295-conciliacion-informe-grafo-historico-b00-20261024.md) distingue el informe histórico del11/10 de sus ocho fragmentos de nodos/relaciones. Cuatro fragmentos contienen controles sin escapar dentro de cadenas y no son JSON estricto, pese al encabezado «sin pérdida de atributos». El inventario estructural preserva esos valores y sus posiciones; no demuestra identidad con los bytes del graph.json original, lectura semántica de los registros ni restaurabilidad. No se reparan rutas o etiquetas por conjetura ni se importa el grafo antiguo al actual. Los originales capturados se conservan intactos.

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

## Grafo limpio del alfa desde cero — 2026-10-20

Por instrucción expresa del usuario, se eliminaron todos los directorios Graphify detectados en los worktrees registrados, incluidas cachés, memorias, snapshots, copias históricas y alias. También se retiró el archivo de traslado que contenía el grafo anterior de este checkout y del alfa. No se guardó una copia de los grafos eliminados. El ledger numérico de consumo se conserva aparte en `docs/evidencias/graphify-consumo-historico-20261020.json` del checkout inicial, sin contenido de nodos/aristas y sin incorporarse al corpus. Las referencias de archivo/huellas en evidencias históricas siguen describiendo su corte original; ese archivo de grafo fue retirado ahora por el usuario.

Fuente única vigente: `/home/felidae/proyectos/web_modelos_mod08_vps`, commit `920ea36b6f4d0e8c0a60d030730de5aed1cf1781`. El checkout inicial conserva su rama/código y cambios del usuario. Corpus explícito de **1410 fuentes actuales**: **1226 código**, **129 plantillas**, **14 configuración/activos** y **41 documentos**. Excluidos `.ai`, seguimiento cronológico, historial, evidencias antiguas, comprimidos, propuestas y fuentes descartadas, secretos, medios, entornos y dependencias instaladas. No expandir citas excluidas. `.graphifyignore` fija la frontera y la detección ordinaria confirmó cero entradas históricas. Las dos plantillas token se revisaron como código estático sin credenciales y se incluyen.

Extracción AST íntegramente nueva sin caché; lectura y razonamiento semántico nuevos de los41documentos con citas/huellas verificadas. Resultado: **10,972 nodos, 55,014 relaciones dirigidas, 501 comunidades**, en capas de aplicación/interfaz/documentación/configuración/pruebas/herramientas. MultiDiGraph conserva relaciones paralelas. Las 170rutas declaradas conectan con las plantillas; cero nombres URL explícitos sin resolver. Cero extremos ausentes, **174 referencias externas/sin resolver** y **126 autorrelaciones** conservadas como límites, no defectos acreditados. Semántica seleccionada, sin prometer cada proposición documental ni exhaustividad dinámica.

Estado: Alpha técnico local aceptado según acta10 del2026-10-20, producciónG01–08 pendiente según acta11; MOD09 mantiene deuda de rendimiento. Pruebas incluidas como fuentes no se convierten en PASS por aparecer en el grafo. No nuevas pruebas de aplicación/cargas/aceptaciones/despliegues ni cambios de producto. Sin llamadas Claude ni API LLM externa; consumo nuevo nativo no medido. Avisos de pasos y verificaciones por Telegram con recibos.

Grafo canónico y salidas en `graphify-out/` del alfa, accesibles también desde `graphify-out/` de este checkout mediante enlaces a las mismas salidas actuales: `graph.json`, `graph.html`, `GRAPH_REPORT.md`, `CORPUS_POLICY.json`, `SOURCE_MANIFEST.json`, `GRAPH_HEALTH.json`, `GRAPH_VERIFICATION.json` y `RESET_RECEIPT.json`. No snapshots previos. La receta/fragmentos de `rebuild/` pertenecen únicamente a esta generación.

## Actualización contractual B00–B01 del 2026-10-20

Antes de adaptar el contrato se incorporaron semánticamente el DAFO y el roadmap nuevos. Después se refrescaron trece documentos: producto01, taxonomía09, contrato14, apartado15, ejecución16, CR04/06/07/08/10, DAFO98, roadmap103 y [consolidación104](104-consolidacion-contrato-beta-b00b01-20261020.md). Dos extracciones nativas de sólo lectura, con revisión independiente de huellas y citas; ninguna invocación Claude V1 ni consumo nativo inventado. La consulta global de Open Notebook es contraste externo parcial, no la extracción semántica del grafo ni una auditoría exhaustiva del corpus.

Resultado dirigido actual: **11.016 nodos, 55.047 relaciones y 1.413 fuentes**. Se comprobaron69citas literales del refresco final; no se reextrajo AST porque el código no cambió. Sin expansión a historial/evidencias ni copia de grafos anteriores. Se conserva la pertenencia anterior de los nodos restantes y se añade una comunidad documental Beta:501grupos no vacíos, sin nueva detección global. El HTML vuelve a generarse como vista agregada por superar5000nodos. Los fragmentos de reconstrucción inicial conservan su corte; no describen por sí solos esta actualización incremental.

El contrato1.1 está consolidado documentalmente y la implementación beta sigue pendiente. El corte original del alfa, sus actas y su aceptación no cambian. [Evidencia de alcance del refresco](evidencias/b00b01-grafo-actualizacion-20261020.json).
