# N06A — prerregistro de atribución de inicio de revisión

25 de octubre de 2026. N00/N01aceptados2/13; N06 iniciado en S04-B, no aceptado. Sin candidato de aplicación. Fuentes previas al hito revalidadas contra el grafo de aceptación N01:1946fuentes, sin discrepancias, AST/semántica focal previa exactos. Se preservan criterios354 y límites355.

## Hipótesis y alcance

N01D observó116consultas al iniciar revisión y116/124en el escenario de rechazo/corrección. La fuente views.start conserva comprobación previa de person_queryset, locks de gestor/persona/listing, cuota y create_draft. Éste copia datos/fotos y registra process_blob.delay al confirmar; publication_signals programa refresh_publication_state. La fixture photo_environment activa Celery eager. Parte del coste HTTP podría ser trabajo encolado ejecutado inmediatamente por la configuración de prueba; no se atribuye todavía el total a clonación ni a una cola real.

No cambiar flags eager, tareas, permisos, datos u oráculos para aparentar mejora. Clasificar las consultas de la ejecución original antes de elegir un candidato. No se está optimizando ni recortando QA.

## Selección, datos y oráculos

Instrumento `tests/test_listing_start_cost_baseline.py::test_listing_start_query_attribution`, dos variantes approved/rejected_correction. Reutiliza fixture published y llama los cuerpos originales, sin editarlos:

- `tests/test_revised_listings.py::test_revised_version_keeps_approved_snapshot_and_reuses_bytes`
- `tests/test_revised_listings.py::test_rejection_preserves_public_version_and_rate_ids_are_isolated`

Titular y moderador sintéticos, correo example.invalid, ES y perfil de la fixture de publicación con su foto original; revisión/corrección conserva los mismos datos y byte compartido. La segunda variante incluye su tarifa histórica privada para comprobar que el formulario no la altera. No es contenido comercial público ni un cambio del modelo romántico. Creación de fixtures y llamadas HTTP ajenas a listing/start quedan fuera del intervalo medido, pero se ejecutan las aserciones originales de instantánea, privacidad, rechazo, aislamiento, fotos y contenido público.

Esperar2casos y3muestras de POST302: una revisión publicada y dos inicios en la variante de rechazo/corrección. Mantener mismo orden y una pasada diagnóstica, no percentiles. El número de consultas previo es contexto, no gate exacto entre lotes con calor/orden diferentes.

## Instrumentación y presupuesto diagnóstico

Medir pared instrumentada de Client.request y ejecución/número de consultas de su conexión PostgreSQL. Clasificador de stack usa sólo nombres/rutas estáticos de código, nunca variables locales ni SQL/valores de sujetos: photo_task_eager, state_task_eager, create_draft, manager_authority y request_other. Prioridad explícita de tareas sobre funciones interiores; toda consulta entra en exactamente una etapa. Clasificar verbos mediante lista fija y contar sólo identificadores de tabla conocidos del modelo. Una consulta con joins puede contribuir a varias tablas; sus ocurrencias no se suman como consultas distintas.

Presupuesto de validez:100%de consultas particionadas sin pérdida/duplicación, estado302 de los tres inicios, números finitos y no negativos, ninguna supresión de tareas y todos los oráculos originales aprobados. No hay candidato ni presupuesto temporal nuevo inventado; futuras comparaciones obedecen354 y deben congelar referencia por estado/etapa antes del candidato. No exigir SQL116/124 si el calentamiento del lote cambia el conteo; explicar cualquier diferencia, sin atribuirla a optimización.

El coste del clasificador está incluido en pared y excluido del reloj de execute; tiempos no equivalen a los de N01D sin ese observador. No guardar SQL, parámetros, paths de petición, UUID, mensajes de excepción ni cuerpos. Propiedades sólo con etiquetas estáticas, números y bandera eager.

## Entorno y ejecución

Antes de medir: integrar AST del instrumento y semántica del protocolo, verificar y congelar fuentes completas/dependencias/migraciones/instrumentos/grafo/imágenes. Runner oficial focused serial, PostgreSQL17/Redis7.4 propios y librdbv2.4.0; sin flags de carga ni observerHTTP adicional. Timeout900s por comando es protección, no SLO. Sin cuotas dedicadas, tráfico concurrente, worker/Beat real ni frío controlado. Preservar la configuración eager de la fixture y declararla, sin presentar simuladores o tareas inmediatas como prueba de cola real.

Al terminar: auditar2casos/3muestras, campos permitidos, conservación de fuentes, particiones/verbos, configuración eager, limpieza y Telegram terminal. Si la atribución deja fuera trabajo relevante o es ambigua, registrar ese límite y preparar el siguiente contraste antes de decidir una corrección. No cerrar N06 con este diagnóstico; se cubrirán sus familias y variantes. Tabla antes/después de bloque al cierre, con base comparable o límite explícito.
