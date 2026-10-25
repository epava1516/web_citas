# N07A — prerregistro de medios, publicación y ciclo de vida

25 de octubre de2026. Alfa, base4bd9a59. N05 cerrado,6/13bloques obligatorios aceptados; N07 en curso, sin aceptación anticipada. Contratos340/354 y roadmap341 vigentes. No se buscan optimizaciones marginales: se conservan los tiempos aceptables y se corrigen defectos funcionales o de seguridad demostrados.

## Corte y unidades

Antes de analizar N07 se contrastó el grafo final de N05:2009fuentes,19079nodos,82391relaciones y913comunidades, SHA0e1d369d2000c84b3dfc3437c2490390419419b623292c157b10a65b0d58e761; cero diferencias de fuentes. Es extracción focal AST/semántica nativa acumulada, no reconstrucción semántica exhaustiva. El inventario contiene39IDs:17rutas,7tareas,1comando propio,1runbook,6entradas Beat,6dispatch y1conexión de señales. Los IDs se conservan aunque una línea se haya desplazado.

Las fuentes directas de siete IDs difieren del censo original por los cambios aceptados N03 en services.py/tasks.py. El puente debe conservar antes/después y alcance; no declarar identidad byte a byte. N03/393 cubre productor, procesamiento, recuperación, generaciones y retención finita; N04/396 descubrimiento; N05/399 transporte/navegador; N06/377 cuenta y representación. La revisión nativa es entrada de investigación, no evidencia de PASS. Codex contrasta fuentes, oráculos y JUnit originales antes de reutilizar resultados. No repetir por mera actualización documental. N09/N10 conservan derechos, purga/retención y operación compartidos.

## N07A: carrera reordenación frente a retirada

Hipótesis aún no confirmada: reorder consulta una foto activa antes de tomar el bloqueo del gestor y la revisión. Si una retirada confirma durante esa espera, la lista activa posterior puede no contenerla y next puede producir un error interno. La comprobación debe devolver una denegación controlada y conservar la retirada, orden y versión; no reintroducir la foto.

Instrumento nuevo tests/test_photo_reorder_remove_race.py, dos casos ES/EN. PostgreSQL real del runner propio; fixture scenario/photo_environment y dos imágenes sintéticas nativas. Se mantiene un bloqueo real de Person, se inicia POST reorder en otra conexión y se comprueba pg_blocking_pids. Una envoltura pasa íntegramente por locked_manager_person y sólo observa el PID; no sustituye autoridad, HTTP, reloj ni datos. Con el bloqueo retenido se ejecuta el POST remove real y se confirma; reorder continúa después. Oráculos:404sin streaming, fotografía retirada inaccesible, compañera conservada, posiciones intactas y un solo incremento de edit_version debido a remove. El primer resultado se preserva aunque falle; sólo después se aplica un candidato mínimo y se contrasta.

Comando previsto: `.venv/bin/python scripts/run_local_ci.py --profile focused --workers 1 --test tests/test_photo_reorder_remove_race.py`. Verificar opciones reales antes de ejecutarlo; timeout de pytest≤900s. Sin broker externo ni datos reales; eager de preparación declarado, no prueba de cola. Guardar SHA de producto/prueba/fixtures/dependencias y resultados originales; runner notifica al terminar tras limpieza. La duración de pytest es QA, no latencia de reordenación ni mejora temporal. Criterio: cero errores internos en la carrera demostrada y ninguna pérdida de guardas o efecto adicional. Regresión focal de fotos/autoridad según cambio, sin toda QA por rutina.

## Siguientes lotes sujetos a revisión

N07B prepara un diagnóstico acotado en worktree aislado para llenar la incertidumbre de worker/Beat de publicación: PostgreSQL/Redis propios, prefork real con rol restringido, señales tras commit, invalidación bulk/rawSQL y lectura pública inmediata durante retraso. Copiar sin acelerar las cadencias nativas refresh30s/expiry60s; una llamada manual de sweep no acredita su cadencia horaria. Identificar tiempos de cola/ejecución/reparación y backlog/edad sin presentarlos como SLA. El diseño final y sus fuentes se revisan y congelan antes de medir; esta propuesta no es ejecución ni aceptación.

Queda conciliar39disposiciones, revisión/apelación y colas, gestión de fotos, lifecycle, renovación/autosubida y retiradas, comandos y tareas compartidas. La tabla final incluirá tiempos disponibles antes/después, muestras y límites; sin base equivalente la mejora será no evaluable. No se abre beta ni se cambia proveedor.
