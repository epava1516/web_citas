# Revisión de cierres locales y restos con graphify

Fecha: 2026-10-09. Revisión de relaciones y fuentes actuales; no ejecución funcional, cargas, migraciones ni despliegue. No altera aceptaciones ni la cola de desarrollo.

## Dictamen

Los recorridos revisados tienen conexiones útiles. El desarrollo ha retirado la antigua vía proyectada, pero conserva deuda de instrumental y preparaciones pendientes de integración operativa. No se acredita ausencia exhaustiva de código muerto ni un cierre integral del producto.

## Método y alcance

Grafo existente: 6787 nodos. Consulta BFS y explicación de publication_state.py, contrastadas con código y documentación vigentes. Expansión desde vocabulario: publication, projection, rights, inventory, benchmark, closed, experimental, purge. Las consultas amplias se truncaron; sus resultados orientan la revisión, no constituyen cobertura completa. Las lecciones aún prefieren ProjectedPublication por documentación histórica. Los 1009 caminos source_file distintos existen; esto no garantiza vigencia semántica. No se reconstruyó el grafo.

Se analizaron sintácticamente imports y referencias textuales de 707 ficheros Python en apps/config/scripts/tests, excluyendo migraciones. El rastreo conservador no encontró módulos de aplicación candidatos sin referencias bajo sus criterios; no analiza exhaustivamente funciones, llamadas dinámicas ni alcanzabilidad desde entradas. No permite declarar todo el código utilizado.

## Hallazgos

| Clasificación | Evidencia | Implicación |
| --- | --- | --- |
| Retirada efectiva | No aparecen imports de projected_publication, sql_publication o text_proof en apps/scripts/tests/config. Quedan nombres de migraciones0016 y dependencias0017. Contrato16 MOD05 registra retirada. | No se mantiene la implementación antigua como segunda vía de producto. Preservar migraciones y evidencias. |
| Componente conectado | discovery.py llama state_page; publication_state.py conserva validación nativa, instantánea y fallback. Configuración agenda refresco y barrido. | MOD05 tiene consumidores y mantenimiento; el fallback es garantía deliberada. |
| Derechos conectados | apps/core/urls.py contiene entradas de decisiones por campo, comunicaciones y preparación/revisión/cierre de portabilidad. config/settings.py agenda purgas de inventario/borradores. Matriz88 enlaza recorridos y evidencia. | Componentes reutilizables; cierre local no implica cobertura operativa integral. |
| Residuo concreto | scripts/benchmark_call_profile.py:51–54 reconoce ProjectedPublication.page/visible_ids, retirados. Solo tests/test_benchmark_profile_aliases.py importa CallProfile en Python actual. | Rama obsoleta y observador sin consumidor de diagnóstico actual encontrado. Candidato a retirar/simplificar; no defecto funcional demostrado. |
| Instrumental histórico conservado | tests/test_discovery_*profile*.py fuerzan/observan vía nativa explícitamente tras MOD05. publication_order_benchmark.py es consumidor de test_publication_state_tcp.py. | No confundir diagnóstico histórico con ruta operativa; separar conceptual u organizativamente diagnósticos y regresión. No borrar todo por antigüedad. |
| Preparación aún desactivada | PROMOTION_TEST_MODE requiere opt-in local; pagos reales rechazados y proveedor simulador prohibido en producción. Matriz88 mantiene CR10 sin aceptación. | Trabajo con destino definido, sin entrega operativa completa. No es código muerto por estar apagado. |
| Concentración de complejidad | safety/models.py1840 líneas, core/urls.py591, safety/views.py532, publication_state.py396. | Señal para revisión de mantenibilidad, no demostración por tamaño de mala arquitectura ni motivo suficiente para reescribir. |
| Evidencia y despliegue incompletos | Seguimiento17 conserva lectura aceptada en1a10ecf e integración, servicios normales73d28f6; capacidad positiva grande y expedientes pendientes. | Las verificaciones históricas no acreditan el runtime normal actualizado ni capacidad universal. |

## Recomendación

Prioridad de mantenimiento: decidir conservación del observador CallProfile y eliminar su rama obsoleta si se conserva; dar un criterio de uso a los diagnósticos históricos; actualizar semántica/memoria del grafo al próximo refresco autorizado. Continuar integraciones operativas solo con insumos de matriz83 o defecto demostrado. No borrar componentes de derechos, migraciones, pruebas de seguridad o evidencia por no estar cerrada la fase completa.

Fuentes: seguimiento17, contrato16 MOD05, matriz88, apps/listings/discovery.py, apps/listings/publication_state.py, apps/core/urls.py, apps/safety/tasks.py, config/settings.py, scripts/benchmark_call_profile.py y tests mencionados. Auditoría documental/estática; no se modifica código funcional ni se reabre una entrega aceptada.
