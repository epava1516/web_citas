# N00 — Contraste del inventario y priorización de escenarios

25deoctubrede2026. Ejecución autorizada del [contrato340](340-contrato-recorridos-optimizacion-alpha-20261025.md) y [roadmap341](341-roadmap-recorridos-optimizacion-alpha-20261025.md). Estado: evaluación inicial producida, pendiente de aceptación independiente y conciliación semántica. N00 en curso;0/13bloques aceptados, tres condicionados. Alfa.

## Base y contraste

El corte previo al hito coincide porSHA con las1927fuentes del grafo vigente, sin extracción afectada pendiente antes de este análisis. La [matriz legible por máquina](evidencias/n00-matriz-acciones-prioridades-20261025.json) registra la huella del grafo, inventario338 y fuentes de cada fila. Las1507fuentes ejecutables de la candidata aceptada B16 siguen idénticas; también coinciden todas las huellas relacionadas del censo, comandos Django y manuales operativos. No se ha ejecutado HTTP, base de datos, proveedor o handle administrativo al hacer este contraste.

No hay declaraciones añadidas, modificadas o retiradas frente a338en este corte. Se conserva su censo en lugar de volver a presentar sus datos como descubrimientos nuevos. La igualdad de fuentes permite conservar las evidencias en su ámbito original, sin atribuir PASS individual a cada acción ni aceptar rendimiento no medido. Las fuentes de documentación340/341yseguimiento cambian después del corte por inicio autorizado y aclaración de prioridad.

| Unidad del inventario | Filas retenidas |
| --- | ---: |
| route | 170 |
| task | 27 |
| own_command | 15 |
| framework_command | 31 |
| runbook | 11 |
| admin_pattern | 16 |
| admin_global_action | 1 |
| beat | 25 |
| dispatch | 14 |
| signal_connection | 1 |
| template | 129 |
| javascript | 3 |

Las filas son unidades distintas y no un total de funcionalidades o de pruebas. Una conexión de señales contiene tres tipos de evento; no se inventan tres declaraciones. Los25disparadoresBeat no son25tareas nuevas. Plantillas/fragmentos yJavaScript participan en recorridos; no se cuentan como acciones de negocio independientes. Admin registra únicamente auth.group y su acción global conserva permisos/confirmación, sin ejecutarla.

## Criterio de prioridad

Primero se contendría cualquier defecto crítico demostrado de autoridad, publicación o pérdida de datos. No se ha demostrado uno nuevo por este contraste de identidad. Después se priorizan dependencias compartidas, consecuencias de regresión, incertidumbre de medición y coste conocido. No hay datos reales de frecuencia o conversión: se registran como desconocidos. Ninguna posición se deduce de centralidad del grafo o de cuántas horas dure QA.

MOD09 tiene incumplimiento temporal medido y excepción provisional vigente; debe trabajarse en N02 y no se elimina del contrato. Su conocimiento no prueba que sea el recorrido de mayor impacto global ni le da prioridad absoluta. La versión1.0 del roadmap lo adelantaba por una decisión técnica de planificación;1.1remite el orden a este contraste y a N01. I14conserva también su deuda de cardinalidad/densidad sin índice impuesto.

## Primera selección para prerregistro N01

Orden provisional de grupos, no mediciones ejecutadas ni aceptación anticipada de bloques. Los defectos demostrados, prerrequisitos y contención de recursos pueden alterar el orden con evidencia. Cada ficha N01 debe seleccionar acciones/variantes concretas, tamaños, permisos, oráculos, muestras y presupuestos; no se autoriza una batería grande por esta lista.

| Grupo | Bloque | Escenario | Familias | Motivo y límite |
| --- | --- | --- | --- | --- |
| S01 | N04 | Discovery segmentation | I01/I02/I03/I04/I05 | Shared public handler, filtering and state-page/promotion selection; existing aggregate budget/witness permits bounded comparison, individual scenarios remain uncertain. |
| S02 | N07 | Publication and asynchronous consistency | I13/I15/I16/I17/I24 | Authority/invalidation shared by public surfaces; preserve withdrawal under worker delay and distinguish job latency from Beat cadence. |
| S03 | N09 | Private rights/decisions/outbox/purge | I20/I21/I23/I25 | High consequence of authority/retention regression; prior witness reused only in exact scope, new cost grouping needs N01. |
| S04 | N06 | Account and profile operations | I09/I10/I11/I12/I18 | Core authoring/authority dependencies and explicit method/control variants; no new real-provider claims. |
| S05 | N05 | Image/browser delivery | I06/I26 | Bytes and browser interaction differ from Django mixed HTTP latency; existing gallery comparison is scoped. |
| S06 | N02 | MOD09 private export decomposition | I22 | Known2s/5s timing FAIL under explicit provisional exception; substantive work required, but no automatic precedence over common/shared authority paths. |
| S07 | N03 | Media processing and density | I13/I14 | Distinct-original and dense-match witnesses show growth sensitivity; end-to-end queue/upload and runtime cardinalities remain uncertain. |
| S08 | N08 | Secondary exposure and synthetic orders | I07/I08/I19 | Consistency with discovery/lifecycle, growth and private/public separation; no inferred traffic frequency. |
| S09 | N10 | Operational cross-cutting costs | I27/I28 | Isolated commands and recovery footprints; reuse bounded operational witnesses, prioritize changed dependency when encountered. |

## Disposición de I01–I28

Todas las acciones de cada familia conservan fuentes, dependencia estática, variantes/métodos disponibles, autoridad requerida, riesgo si hay regresión, evidencias y huecos de rendimiento en JSON. Son condiciones a preservar y verificar, no afirmaciones nuevas de que todos los permisos funcionan. Los cierres de profundidad dos y el registro offline no son un trace de ejecución.

| ID | Familia | Bloque | Grupo N01 | Límite de evidencia actual |
| --- | --- | --- | --- | --- |
| I01 | Listado orgánico | N04 | S01 | Mezcla vigente y oráculos; no p95 exclusivo de listado ni todas las poblaciones. |
| I02 | Listado promocionado | N04 | S01 | Promociones sintéticas; prioridad/páginas/autoridad, no compra ni autosubida bajo toda carga. |
| I03 | Búsquedas y filtros | N04 | S01 | Combinaciones ciudad/perfil/idioma/texto con oráculo; no producto cartesiano de todos los filtros. |
| I04 | Paginación | N04 | S01 | Páginas inicial/intermedia/última y vacíos; no todas las páginas grandes ni p95 por página. |
| I05 | Ficha pública | N04 | S01 | Ficha participa en tercios de mezcla; agregado no equivale a p95 individual. |
| I06 | Entrega de imágenes | N05 | S05 | Entrega/privacidad y carga inicial de galería; sin presupuesto universal de transferencia o red. |
| I07 | Favoritos | N08 | S08 | Exposición y retirada en favoritos con tercero intacto; sin presupuesto individual de latencia. |
| I08 | SEO y documentos públicos | N08 | S08 | Textos versionados, superficies y SEO locales; textos sintéticos no revisión jurídica ni medición de cada sitemap. |
| I09 | Cuenta y sesión | N06 | S04 | Autoridad de cuenta/sesión y aceptación vigentes en escenarios; sin entrega de identidad externa real. |
| I10 | Seguridad y verificación | N06 | S04 | Guardias locales/MFA y rechazo de simuladores; proveedores reales no elegidos ni integrados. |
| I11 | Panel del anunciante | N06 | S04 | Panel/perfil simple, navegación y actores probados; no presupuesto de cada cardinalidad de panel. |
| I12 | Edición del perfil | N06 | S04 | Perfil romántico, rechazo de campos profesionales e historia privada preservada; UI/autoridad no p95 de guardado. |
| I13 | Subida de fotografías | N03/N07 | S02/S07 | 15subidas302conPhoto/UploadAttempt en borradores distintos; no procesamiento asíncrono entero desde302. |
| I14 | Procesamiento fotográfico | N03 | S07 | Detector1000Blob/5positivos3,20s y100densos14,39s; no80koriginales, ingestión/cola completa o índice adoptado. |
| I15 | Gestión de fotografías | N07 | S02 | Fotos WEBP/sinEXIF, lectura privada/retirada/revisión por escenarios; no medición completa de transferencia/ordenación. |
| I16 | Revisión y publicación | N07 | S02 | Revisión/publicación ESEN, rechazo/corrección, actores y worker/Beat reales; tiempos humanos excluidos. |
| I17 | Ciclo de vida | N07 | S02 | Ventana4h, renovación idempotente, carreras, caducidad y retirada sin esperarBeat; sin p95 por operación. |
| I18 | Agencias y representación | N06 | S04 | Representados con teléfono compartido y autoridad separada; no identidad/representación externa real. |
| I19 | Gestión comercial sintética | N08 | S08 | Derechos/rotación/rollback y fixtures comerciales; no ventas, pasarela ni compra concurrente reales. |
| I20 | Denuncias y reclamaciones | N09 | S03 | ColaSQL30/210→10/10y revocación/retirada/urgencia; no latencia de cada decisión ni cobertura humana real. |
| I21 | Derechos y rectificación | N09 | S03 | Autoridad fresca antes de descifrado, derechos y recuperación por escenario; no aceptación jurídica global. |
| I22 | Exportación y portabilidad | N02 | S06 | Dos sujetos1500revisiones/16MiBJSON/64MiBoriginales:FAILtemporal actual conservado, integridad verificada; selección31páginas p95<2s. |
| I23 | Avisos y comunicaciones | N09 | S03 | Outbox/reintento y dos caídas locales; primer intento no recepción email/SMS externa. |
| I24 | Publicación en segundo plano | N07 | S02 | Guardia de modelos históricos y reparación actual14→0marcas; autoridad inmediata separada de convergencia; backlog no universal. |
| I25 | Limpieza y recuperación | N09 | S03 | 16purgas/limpiezas conciliadas y5restauraciones actuales; noPITR/custodia externa/recifrado exhaustivo o todas las cardinalidades. |
| I26 | Navegador y entrega web | N05 | S05 | Geografía local sinXHR, teclado/ESEN y galería8→1imagen inicial; noSLO browser completo con red/dispositivo reales. |
| I27 | Infraestructura transversal | N10 | S09 | Cuotas8CPU/8GiB/swap0y recursos propios; no aislamiento del host ni capacidad universal o cada endpoint a20RPS. |
| I28 | Operación administrativa | N10 | S09 | 15comandos y registroAdmin offline; no ejecutar comandos destructivos niCRUDAdmin; responsables/custodia/apertura pendientes. |

## Disposiciones particulares y límites

Los31comandos del framework se separan por ámbito: herramientas de operación frente a QA/generación de proyectos. Inventariarlas no abre el contrato QA aplazado ni autoriza ejecutarlas sobre datos ajenos. Las pruebas de producto justificadas siguen siendo obligatorias. B14/B15/B17 conservan N12/N13/N14condicionados; no se activan por iniciar este contrato.

La evaluación es estructural y de evidencias ya aceptadas; no mide tráfico, costes de proveedor, capacidad de destino o todas las combinaciones de estado. No se identifican defectos funcionales por un nombre de ruta o dependencia. No se acepta N00 únicamente porque un generador emita JSON: se requiere verificar cobertura frente al censo y muestras de enlaces a fuente/autoridad, y conciliar los documentos nuevos en el grafo.

Próxima acción: verificación independiente de esta matriz y actualización semántica focal; después prerregistro N01 del primer grupo S01/descubrimiento, manteniendo el resto de acciones pendientes y las garantías originales.
