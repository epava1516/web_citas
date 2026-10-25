# Roadmap del contrato alfa — recorridos y optimización

Versión1.3 de seguimiento,25deoctubrede2026. Vinculante para el alcance del [contrato340](340-contrato-recorridos-optimizacion-alpha-20261025.md), con ejecución autorizada posteriormente por el usuario. N00 aceptado por [343](343-n00-aceptacion-local-20261025.md) y N01 por [355](355-n01-aceptacion-local-20261025.md): **2/13bloques obligatorios aceptados**. Esta actualización registra aceptación y criterios354; no modifica alcance ni garantías. N12–N14 son tres bloques condicionados; no se cuentan como PASS por diferirlos. Los antiguos B00–B13/B16 mantienen su aceptación; los nuevos N no reutilizan su numeración ni su porcentaje.

## Orden y alcance

La primera posición es el inventario de recorridos. N00/N01 identifican escenarios y fijan bases/presupuestos; el orden entre N02–N10 se decide por impacto, riesgo, dependencias y coste contrastado, sin precedencia automática de MOD09 o procesamiento fotográfico. La selección inicial y sus límites se documentan en [N00:342](342-n00-inventario-priorizacion-20261025.md). Esa flexibilidad no elimina familias ni bloques. N11 concilia la candidata; N15 realiza la entrega final. N12–N14 conservan las condiciones de deuda336 y no activan producto o apertura.

Ruta de dependencias: N00 → N01 → N02–N10 → N11 → N15. N02–N10 dependen de N01 y pueden coordinar lotes independientes; la flecha de prioridad no obliga a esperar un bloque sin relación técnica. Cualquier trabajo condicionado que se active y cambie producto debe integrar su evidencia en N11 antes de N15. Si no hay insumos, su diferimiento no detiene los trabajos independientes.

No se promete fecha antes de N00/N01. Estimar por bloques tras conocer escenarios, fuentes, recursos y muestras; separar ejecución activa, espera de pruebas y dependencias externas. Mantener rango y actualizarlo con evidencia. No derivar latencia de aplicación ni duración futura sólo del número de archivos o casos QA.

## Matriz de ejecución

| ID | Prioridad | Bloque | Depende de | Estado inicial |
| --- | --- | --- | --- | --- |
| N00 | P0 | Inventario y selección fundada de escenarios | Base aceptada/condición expresa | Aceptado por343; alcance estructural |
| N01 | P0 | Línea base y presupuestos por escenario | N00 | Aceptado por355; criterios354 y bases/motivos por lote |
| N02 | P1 según N00 | Exportación y portabilidad: deuda MOD09 | N01 | Verificado localmente con límite: guard365 y evaluación367; optimización restante MOD09 diferida al final del desarrollo por decisión expresa del usuario, sin PASS temporal |
| N03 | P1 según N00 | Procesamiento y similitud fotográfica | N01 | Pendiente |
| N04 | P1 | Listado, búsqueda y ficha | N01 | Pendiente |
| N05 | P1 | Imágenes y experiencia de navegador | N01 | Pendiente |
| N06 | P1 | Cuenta, panel, edición y representación | N01 | En curso: atribución357, referencia encolada359 y representación369; crecimiento/panel y variantes restantes pendientes |
| N07 | P1 | Medios, publicación y ciclo de vida | N01 | Pendiente |
| N08 | P1 | Favoritos, SEO y exposición comercial sintética | N01 | Pendiente |
| N09 | P1 | Derechos, moderación, avisos y limpieza | N01 | Pendiente |
| N10 | P1 | Infraestructura y operación administrativa local | N01 | Pendiente |
| N11 | P0 aceptación | Candidata integrada y conciliación técnica | N02, N03, N04, N05, N06, N07, N08, N09, N10 | Pendiente |
| N12 | Condicionado | B14: proveedores y adaptadores reales | Base aceptada/condición expresa | Condición pendiente; no activado |
| N13 | Opcional condicionado | B15: recomendaciones por intereses físicos | Base aceptada/condición expresa | Condición pendiente; no activado |
| N14 | Condicionado a apertura futura | B17: preparación real y G01–G08 | Base aceptada/condición expresa | Condición pendiente; no activado |
| N15 | P0 cierre | Inventario diferencial, grafo y acta final | N11 | Pendiente |

## Entregables y condiciones de salida

### N00 — Inventario y selección fundada de escenarios

Familias: I01, I02, I03, I04, I05, I06, I07, I08, I09, I10, I11, I12, I13, I14, I15, I16, I17, I18, I19, I20, I21, I22, I23, I24, I25, I26, I27, I28.

Contrastar censo338/339 contra fuentes actuales y construir matriz por acción: autoridad, datos/estados, evidencia funcional/rendimiento, dependencias, coste/riesgo e incertidumbre. Ordenar con evidencia; frecuencia desconocida queda desconocida.

**Salida:** Las28familias y todas las acciones censadas tienen entrada y estado; diferencias e incertidumbres explícitas, prioridades justificadas y primera selección medible. Los controles/idiomas/plantillas no se suman como funcionalidades.

### N01 — Línea base y presupuestos por escenario

Familias: I01, I02, I03, I04, I05, I06, I07, I08, I09, I10, I11, I12, I13, I14, I15, I16, I17, I18, I19, I20, I21, I22, I23, I24, I25, I26, I27, I28.

Prerregistrar por lote las fichas del contrato340: fuentes, dataset, recursos, mezcla, oráculos, muestras, etapas y presupuestos. Reutilizar sólo testigos equivalentes. Planificar las mediciones de mayor riesgo antes de optimizar.

**Salida:** Cada escenario seleccionado tiene criterio anterior a su candidato y base comparable o razón concreta para medirla; ninguna propuesta111 se convierte silenciosamente en gate. Los lotes posteriores completan su ficha antes de ejecutarse.

### N02 — Exportación y portabilidad: deuda MOD09

Familias: I22.

Atribuir cobertura, lectura de originales, serialización/cifrado, paquetes JSON/binarios, cola y entrega. Comparar crecimiento, retención y concurrencia con sujetos separados y autoridad fresca; corregir coste demostrado y contrastar referencia/candidato.

**Salida:** Evaluación actual y decisiones verificadas, con integridad, completitud, separación y revocación preservadas. Objetivos2s/5s y FAIL previos visibles. La excepción MOD09 conserva su alcance; no se declara cumplimiento temporal si sigue fallando.

### N03 — Procesamiento y similitud fotográfica

Familias: I13, I14.

Medir recepción→cola→procesado→estado utilizable, recuperación/reintentos y detector/confirmación/registro por separado. Variar originales distintos, densidad de coincidencias, retención y concurrencia. Valorar índice sólo si el coste lo justifica.

**Salida:** Comparaciones reproducibles y paridad de positivos/negativos. Detector aislado no acredita subida completa ni capacidad80000fotos. Sin índice impuesto ni límites que oculten coincidencias; costes residuales identificados.

### N04 — Listado, búsqueda y ficha

Familias: I01, I02, I03, I04, I05.

Segmentar listado orgánico/promocionado, filtros y selectividad, páginas profundas, idioma y frío/caliente. Separar SQL, hidratación, render y carga limpia. Corregir sólo coste demostrado.

**Salida:** Paridad de IDs/orden/conteos/cupos/rotación, patrocinio y exclusiones; paginación completa y autoridad inmediata. Presupuestos aplicables verificados sin extrapolar la mezcla pública a cada variante.

### N05 — Imágenes y experiencia de navegador

Familias: I06, I26.

Medir bytes, variantes, caché y entrega pública/privada, imágenes diferidas, recursos, validación y consultas periódicas de exportación. Registrar dispositivo, red y concurrencia declarados; separar navegador y backend.

**Salida:** Calidad necesaria, permisos, accesibilidad/teclado, ES/EN y estados correctos; sin fuga de originales ni inferencia de p99 desde HTTP. Impacto de cada cambio contrastado con escenario y recurso equivalente.

### N06 — Cuenta, panel, edición y representación

Familias: I09, I10, I11, I12, I18.

Medir operaciones elegidas de sesión/verificación, panel, guardado/corrección y representación. Distinguir coste de formulario/servicio, transacción, evidencias e imágenes; conservar reintentos y borradores.

**Salida:** Regresión de autoridad y estados con sujetos/roles distintos, sesiones/MFA/CSRF y grants; sin convertir adaptadores sintéticos en verificación externa. Complejidad sólo se refactoriza por cambio/coste justificado.

### N07 — Medios, publicación y ciclo de vida

Familias: I13, I15, I16, I17, I24.

Completar gestión/revisión de fotos, publicación, renovación/autosubida, señales, invalidación, worker y Beat. Medir backlog/antigüedad y efecto de bulk/rawSQL y procesos retrasados. Coordinar la subida con N03 sin repetirla por rutina.

**Salida:** Retirada y revocación inmediatas en todas las superficies, publicación compatible, locks e idempotencia. Cadencias/timeouts no se presentan como SLA de extremo a extremo; recuperación y límites de recursos verificados donde se modifiquen.

### N08 — Favoritos, SEO y exposición comercial sintética

Familias: I07, I08, I19.

Medir superficies secundarias según tamaño, paginación, filtrado y permisos: favoritos, sitemap/documentos y operaciones sintéticas de exposición/pedido. Comprobar consistencia con descubrimiento y ciclo de vida.

**Salida:** Sin perfiles inelegibles, exposición privada o promociones reactivadas; conteos/ordenación y patrocinio coherentes. No cobros reales, proveedor o nuevas promesas comerciales.

### N09 — Derechos, moderación, avisos y limpieza

Familias: I20, I21, I23, I25.

Medir colas/decisiones y lecturas autorizadas, rectificación, reclamaciones, avisos/outbox, purga lógica/física y recuperación. Separar tiempo de máquina, espera humana y proveedor; coordinar exportación con N02.

**Salida:** Cobertura/evidencia/retención y retirada conservadas, sin doble efecto ni replays indebidos. Purgas vencidas y fallos de entrega observables; supuestos humanos/externos no se acreditan con sintéticos.

### N10 — Infraestructura y operación administrativa local

Familias: I27, I28.

Evaluar costes transversales y comandos/runbooks seleccionados: arranque, worker/broker, cifrado/firma/credenciales/proxy, copias/restauración, retorno e incidente. Distinguir15comandos propios,31Django y11recorridos.

**Salida:** Acciones operativas afectadas ensayadas en aislamiento, con autoridad, efectos, limpieza y recuperación documentados. Registro Admin/CLI no equivale a ejecución; no ejecutar comandos destructivos sobre datos o entornos ajenos. Sin SLA de destino inventado.

### N11 — Candidata integrada y conciliación técnica

Familias: I01, I02, I03, I04, I05, I06, I07, I08, I09, I10, I11, I12, I13, I14, I15, I16, I17, I18, I19, I20, I21, I22, I23, I24, I25, I26, I27, I28.

Integrar cambios aceptados, congelar fuentes/migraciones/dependencias e instrumentos y ejecutar regresión común pertinente. Conciliar testigos reutilizados, exclusiones y negativos, así como recursos/continuidad afectados.

**Salida:** Matriz requisito→acción→candidata→prueba→resultado→límite, con PASS/FAIL/ERROR/SKIP separados. Sin críticos abiertos de acceso/exposición/pérdida de datos en alcance aceptado; deuda individual, ninguna suma ficticia de ejecuciones.

### N12 — B14: proveedores y adaptadores reales

Familias: I10, I19, I23.

Conservar especificaciones y guardias locales; listar selección, autorización, credenciales y pruebas de fallos/revocación pendientes. Integración real sólo cuando existan proveedor elegido y autorización separada.

**Salida:** Si se activa: evidencia real en alcance autorizado y sin confundir simuladores. Sin insumos: diferido por condición, noPASS; no bloquea el núcleo local por la ausencia ya acordada.

### N13 — B15: recomendaciones por intereses físicos

Familias: I01, I02, I03, I09, I12.

Mantener decisiones de consentimiento/persistencia, cookies del visitante y posible almacenamiento cifrado de cuenta. Si se incorpora expresamente: definir atributos, ranking, desconocidos, utilidad, latencia, modificación/borrado y retirada antes de construir.

**Salida:** Sin decisión de activación: opcional diferido, noimplementado/noPASS. Si se activa: elegibilidad, consentimiento separado y búsqueda ordinaria disponibles; sin importación automática navegador→cuenta ni inferencia de fotos.

### N14 — B17: preparación real y G01–G08

Familias: I10, I20, I23, I25, I27, I28.

Mantener matriz de operador/textos, responsables/cobertura, proveedores/custodia, medios, abuso/capacidad, continuidad y revisiones independientes. Identificar qué requiere decisiones y evidencias reales.

**Salida:** Pendientes reales visibles, sin responsables o revisiones ficticios. Cualquier futura apertura necesita alcance y autorización expresa; ni terminar este contrato ni llamarlo beta la conceden.

### N15 — Inventario diferencial, grafo y acta final

Familias: I01, I02, I03, I04, I05, I06, I07, I08, I09, I10, I11, I12, I13, I14, I15, I16, I17, I18, I19, I20, I21, I22, I23, I24, I25, I26, I27, I28.

Conciliar estado de N12–N14; auditar entrega técnica, preservar grafo y reconstruir corpus final desde cero una vez. Actualizar diferencialmente338/339+censo manteniendo111 e IDs, integrar semántica y comprobar enlaces antes del acta y registroGit.

**Salida:** Todos los13bloques obligatorios tienen aceptación/evidencia suficiente;28familias y acciones dispuestas, condiciones/deuda explícitas. Grafo, fuentes, inventario y acta coherentes; alfa. No completar por documentación una obligación técnica sin ejecutar.

## Cobertura estable I01–I28

N00/N01 y N11/N15 son transversales. La tabla asigna cada familia al bloque técnico que debe analizarla; los solapamientos se coordinan mediante una ficha compartida, sin duplicar baterías o crédito de aceptación. Fuentes y límites de partida: [338](338-inventario-acciones-recorridos-alpha-20261025.md), [339](339-diferencial-inventario-recorridos-20261025.md) y [censo](evidencias/inventario-acciones-final-20261025.json).

| Familia | Recorrido | Bloque técnico |
| --- | --- | --- |
| I01 | Listado orgánico | N04 |
| I02 | Listado promocionado | N04 |
| I03 | Búsquedas y filtros | N04 |
| I04 | Paginación | N04 |
| I05 | Ficha pública | N04 |
| I06 | Entrega de imágenes | N05 |
| I07 | Favoritos | N08 |
| I08 | SEO y documentos públicos | N08 |
| I09 | Cuenta y sesión | N06 |
| I10 | Seguridad y verificación | N06 |
| I11 | Panel del anunciante | N06 |
| I12 | Edición del perfil | N06 |
| I13 | Subida de fotografías | N03/N07 |
| I14 | Procesamiento fotográfico | N03 |
| I15 | Gestión de fotografías | N07 |
| I16 | Revisión y publicación | N07 |
| I17 | Ciclo de vida | N07 |
| I18 | Agencias y representación | N06 |
| I19 | Gestión comercial sintética | N08 |
| I20 | Denuncias y reclamaciones | N09 |
| I21 | Derechos y rectificación | N09 |
| I22 | Exportación y portabilidad | N02 |
| I23 | Avisos y comunicaciones | N09 |
| I24 | Publicación en segundo plano | N07 |
| I25 | Limpieza y recuperación | N09 |
| I26 | Navegador y entrega web | N05 |
| I27 | Infraestructura transversal | N10 |
| I28 | Operación administrativa | N10 |

## Seguimiento y cierre

Al finalizar cada bloque, publicar tabla de antes/después por escenario/métrica y evidencias, conforme a la instrucción del usuario incorporada en contrato340. Debe mostrar tiempos anteriores/posteriores de aplicación, unidad, muestras y diferencias cuando sean comparables; consultas y estado son información adicional, no sustituyen los tiempos. Sin base equivalente se declara el límite; no se inventa mejora o porcentaje.

Cada bloque usa ficha prerregistrada y matriz de evidencia del contrato340. Se actualiza seguimiento17 al comenzar ejecución y tras cada resultado; la matriz de este documento conserva el orden y la trazabilidad. Verificaciones locales no acreditan proveedor real, cumplimiento jurídico, utilidad con personas o capacidad de destino.

La optimización específica de QA sigue aplazada hasta primera estable/productiva. El cierre de este roadmap conserva alfa; no depende de abrir beta, contratar proveedores o activar B15. Las nuevas excepciones de alcance no se aprueban sólo para aumentar el contador. Un obligatorio pendiente impide cerrar; MOD09 conserva su excepción expresa sin convertir FAIL enPASS.

## Decisión posterior del usuario — MOD09

Tras la evaluación [367](367-n02-d-resultado-y-diferimiento-mod09-20261025.md), sin mejora clara global, el usuario acepta los tiempos actuales en alfa y difiere la optimización restante de MOD09 al final del desarrollo. Conservar objetivos2s/5s, FAIL y pendientes de atribución/crecimiento/retención/concurrencia; no repetir batería para perseguir reducción ahora. Continuar con N06 ya abierto. Este diferimiento expreso no equivale a PASS ni elimina las restantes familias del contrato.
