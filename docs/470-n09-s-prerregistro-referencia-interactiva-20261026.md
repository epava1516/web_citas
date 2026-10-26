# N09S — prerregistro de la referencia interactiva de máquina

Estado: diseño anterior a ejecución, sin medida nueva ni cambio de producto. Base `bdb74d9`, corrección R y conciliación de 139 IDs entregadas. La [brecha de 469](469-n09-conciliacion139-y-brecha-medicion-interactiva-20261026.md) sigue abierta: 8/13 bloques aceptados; N09 no está aceptado. Alpha/noindex.

## Requisito, selección y unidades

Completar la referencia normal seleccionada de S03A, separando snapshot, validación y transacción del tiempo humano, proveedor y preparación. Se aplican contrato340 y criterios354. No hay candidata de optimización ni umbral temporal nuevo: primero se obtiene una referencia con paridad funcional y efectos exactos. Se preservan A–R, sus originales fallidos y sus aceptaciones limitadas; no repetir esas campañas por añadir esta instrumentación.

El corte anterior al análisis es el grafo de 469: 2.118 fuentes, 20.797 nodos, 85.618 relaciones, SHA-256 `9ab5bac83de305965b69a864e94440e9a0f934193c85aa848ab81861e7d906e0`. Una consulta BFS recuperó 676 nodos y mostró 23 con presupuesto de 900 tokens; no se supone revisado lo omitido. Se contrastaron directamente los servicios y las preparaciones nativas de los tres recorridos. Antes de ejecutar se integrarán el AST del instrumento y la semántica de este protocolo, y se congelarán fuentes, instrumentos, dependencias y documentos.

Instrumento: `tests/test_owned_interactive_rights_profile.py`, tres casos explícitos, seriales y con PostgreSQL propio real. La preparación usa funciones de pruebas existentes, no historias nuevas de personas ni casos creados mediante atajos de autorización.

| Caso | Preparación nativa fuera de medida | Etapas normales seleccionadas | Oráculos |
| --- | --- | --- | --- |
| processing_plan | `test_processing_review.prepared`; cuenta con plan de restricción y revisor independiente autorizado | Cola de derechos ES/EN con un expediente elegible; inspección nueva y repetición exacta; aprobación nueva y repetición exacta | IDs visibles exactos, cuerpo nativo y vínculos Action/Read/Review, independencia, misma PK/cuerpo en replay y cero efectos repetidos; cuenta y archivos conservados |
| rectification | `test_rectification_review.independent_case`, propuesta nativa de cambio de alias, revisor asignado y prueba vigente | Preview de fuente, inspección de propuesta, aprobación nueva y repetición exacta | Cambio propuesto exacto; SourceRead/ProposalRead/Action/Review y sus vínculos; sólo version+1/scope_status unverified del expediente al revisar; sin ejecutar rectificación ni modificar publicación |
| complaint | `test_complaint_resolutions.listing_case(rejected=False)` e inspección nativa completa de texto/fotos antes de resolver | Cola ES/EN abierta, resolución upheld nueva y repetición exacta, cola ES/EN resuelta | Sólo Complaint.status/version y Action+Resolution+Notice una vez; fuente/publicación intacta, cuerpo cifrado nativo correcto, replay sin efectos y expediente resuelto ausente de la cola |

La cohorte es un expediente o propuesta nativa por caso, sobre las identidades/catálogos sintéticos de directory y photo_environment. No clonar volumen ni aumentar cardinalidad tras ver tiempos. Las decisiones humanas ya están representadas por entradas sintéticas explícitas y no se cronometra a una persona. El Notice se guarda localmente; este caso no acredita envío ni procesa el outbox.

## Observaciones y fronteras

Cada operación nueva que escribe se observa una vez. Cada GET seguro o replay idempotente se observa en una primera llamada separada y cinco posteriores con el mismo estado útil. No combinar la creación y el replay ni idiomas o estados para calcular un valor favorable. Diseño esperado: 66 observaciones en 16 grupos de etapa —26 de procesamiento, 9 de rectificación y 31 de reclamación—, sin contar preparación, snapshots, oráculos o QA. El instrumento se revisará contra esta selección antes de congelar; una discrepancia debe resolverse antes de lanzar, no omitiendo etapas silenciosamente.

Medir `perf_counter` y CPU del proceso alrededor del callable real; `connection.execute_wrapper` cuenta sentencias y acumula el tiempo SQL observado sin conservar texto ni parámetros. La pared incluye la transacción del servicio o el handler Client, según la etapa, y su trabajo Python/cifrado/materialización. Los BEGIN/COMMIT que el driver no exponga no se inventan en el contador SQL. Consumo y comprobación del resultado no perezoso, snapshots y preparación se separan de la ventana medida. No sustituir funciones por stubs ni medir un oráculo en lugar de la aplicación.

Para Client conservar estado, bytes, idioma efectivo, IDs/orden y private/no-store; verificar que no sea una redirección de login. Es el handler Django local, no transporte de proxy, navegador o TLS. Para servicios conservar únicamente métricas, contadores y hashes de identidad del resultado cuando proceda; nunca contenido privado, ciphertext, claves, IDs, cookies, SQL ni parámetros en propiedades JUnit. JSON finito, sin NaN/Infinity.

Los primeros tiempos no se llaman caché fría: fixtures y sesiones ya han calentado componentes. No vaciar cachés compartidas. Registrar hardware/cgroup disponible y límites de observación; no afirmar aislamiento de carga del host ni SLA de destino. CPU corresponde al proceso cliente/Python, no incluye automáticamente la CPU del servidor PostgreSQL. La instrumentación tiene sobrecoste no cuantificado. Mediana/rango sólo de las cinco observaciones posteriores homogéneas, sin p95/p99 o mejora causal.

## Integridad, ejecución y limpieza

Comparar filas de todos los modelos instalados y relaciones through, incluidos permisos y sesiones, antes y después, excluyendo sólo las PK nuevas legítimas y los campos exactos del único padre que deba cambiar. No excluir tablas completas para ocultar efectos. Los replays conservan el snapshot íntegro. Comprobar archivos por contenido, tamaño, mtime y modo; no hacer pasar creación de auditoría legítima por cambio de perfil. Mantener estado/fechas/firmas/retención del resto de filas, fuente y publicación. Los resultados deben incluir oráculos explícitos antes de declarar el caso correcto.

Runner oficial focused, `--workers 1`, sólo el archivo de tres casos, parser local fijo `/tmp/web-modelos-librdb-v2.4.0` en commit `bc5f295c98b40c2c33099d9d72ab30ce9e595dc7`, timeout del comando de pruebas 900 s. PostgreSQL17-alpine y Redis7.4-alpine desechables propios, con versiones/huellas verificadas por el runner; no conectar credenciales Django a MCP ni a bases persistentes. Sin worker/Beat nuevo, despliegue, proveedores, migraciones de entorno persistente, cambios CI o carga activa.

Criterio: tres PASS sin FAIL/ERROR/SKIP en la selección explícita; todas las etapas previstas con métricas finitas y oráculos; fuentes intactas durante la prueba; recursos propios retirados y recibo terminal Telegram comprobado. El registro no es una mejora de rendimiento; sólo da referencia para decidir si existe cambio justificado. Un fallo de instrumento y un defecto reproducido de producto se distinguen y conservan. No debilitar oráculos para cerrar N09.

Toda ejecución de prueba o gate avisa por el wrapper vigente; el runner notifica tras limpieza. Se estima un lote de minutos, no una espera de horas; si evidencia real muestra una prueba muy larga se aplicará el protocolo de persistencia/Telegram/relevo y pausa autorizada, sin sondeos del modelo durante horas. No iniciar una segunda copia por perder la observación de la primera.

## Límites y continuación

La cola de derechos materializa elegibles antes de paginar a 50; una muestra de un expediente no acredita coste acotado con backlog grande. La cola de reclamaciones toma 100 candidatos antes de comprobar permisos por objeto; esta referencia no demuestra cobertura o coste de un histórico mayor. No se extrapolan tiempos entre estas familias, los otros 52 derechos, todos los modelos de purga o todas las combinaciones de permisos. Las pruebas de autoridad ya aceptadas permanecen como evidencia independiente.

Después se auditarán métricas, fuentes y oráculos reales, se documentará la tabla de referencia/resultado posterior sin inventar candidata y se decidirá la suficiencia de N09 con la matriz de 139 IDs. N10 conserva sus 12 obligaciones compartidas y su inventario propio; N11 conciliará regresión común e incertidumbres de fuente; N15 mantiene grafo completo, inventarios, acta y limpieza final completa de artifacts. N02 residual al final; N12–N14 condicionados. Ninguna de esas obligaciones se cierra por este prerregistro.
