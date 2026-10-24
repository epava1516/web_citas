# B16-366 — Revisión semántica de testigos AD01–AD11

La [conciliación322](322-conciliacion-requisitos-b16-20261024.md) asociaba nodeids a requisitos, pero advertía que la coincidencia nominal no demostraba cobertura semántica. Se revisan ahora cuerpos y aserciones de45referencias a funciones en22archivos, con variantes parametrizadas de la batería funcional20261024-094540-3a6ec8ac. La [matriz de testigos revisados](evidencias/b16-semantic-witness-review-20261024.json) registra criterio, razonamiento, líneas, SHA de archivo/AST, aserciones literales y nodeids realmente aprobados. AD08 permanece opcional/no implementado, nunca PASS.

| Criterio | Evidencia semántica revisada |
|---|---|
| AD01 | MigrationExecutor ida/vuelta conserva revisión/categoría/tarifa eIDs; legado privado, borrador actual limpio y publicación con tipo sin indicar. |
| AD02 | POST profesional400sin mutación; Chromium ES/EN390/1280verifica teclado, errores, recarga y geografía; fotos reales WEBP sin EXIF, lectura privada y retirada. |
| AD03 | Filtros profesionales400/recuento0; paginación positiva exacta y estable; detalle/contactos seleccionados; exclusión inmediata en directorio/ficha/foto/favoritos/sitemap con tercero intacto. |
| AD04 | Reuso deFKsin compartir autoridad; consentimiento/agencia frescos; paridad de bytes con regla nativa antes/después de cambios; fuentes ejecutadas versionadas. |
| AD05 | Navegador conserva aprobado durante edición, rechazo/corrección y nueva revisión; pausa/reanuda/renueva/retira; particular y editor con MFA/asignación actuales. |
| AD06 | Ventana disponible alrededor de4h, reintento sin extensión, vencimiento sinBeat; renovación conservaID/revisión, confirmación y acción única en carrera; replay no republica retirada. |
| AD07 | Filtros/etiquetas/rotación/páginas exactos; bumpconcurrente único; fallo de auditoría revierte concesión; worker/Beat reales y restauración sin reactivar promoción suprimida. |
| AD08 | Opcional, no implementado; persistencia/claves/retención y utilidad sin decidir. |
| AD09 | Dos representados con teléfono compartido mantienen autoridad separada; edad/consentimiento/gestión/MFAactuales y rechazo de simuladores en producción. |
| AD10 | Cuerpo legal previo y aceptación conservados; publicación requiere nuevo documento y autorización directa; flujos ES/ENdirectos/invitados rechazan versión obsoleta y transferencia invalida autoridad. |
| AD11 | Supresión/recuperación scopedcon tercero intacto; recibo/plan ajenos o alterados rechazados; archivo reintroducido vuelve pendiente; copia histórica compatible y rechazo de drift/daño/autoridad vencida; restauración comercial conserva evidencia sin exposición. |

Se amplía el mapeo inicial con test_photos y test_beta_exposure_worker, ambos aprobados en353y con archivo idéntico al actual. El segundo realmente inicia Celery/Beat en procesos propios y cola aislada: cuatro trabajos explícitos, nueva víctima caducada porBeat, reconsulta comercial posterior y estado editorial intacto. El original beta-exposure-worker-proof.json es PASS; hashes de ambos logs y terminación de procesos coinciden. Identidad/pago siguen sintéticos, no proveedores reales. La prueba de restauración comercial inyecta aserciones en el hijo real de restauración; no se sustituye por una llamada síncrona a tareas.

## Reutilización y diferencia de versión

El contraste contra todas las fuentes de producto/plantillas/estáticos del manifiesto353encuentra una sola diferencia: publication_signals.py. El archivo del commit original coincide con la huella congelada. AST de schedule_refresh conserva íntegro el cuerpo anterior salvo la guarda nueva model._meta.apps is not apps; también añade la importación del registro global. La ruta de modelos activos conserva callback y deduplicación; los registros históricos/aislados dejan intencionalmente de encolar una tarea del esquema activo.

La [correctiva317](317-registros-historicos-senal-publicacion-b16-20261024.md) aporta negativos previos,9PASS, relaciónM2M real trascommit, invalidación/404con modelo histórico y reparación posterior porBeat/worker. Los triggers y la regla nativa no se cambiaron. Este puente justifica reutilización acotada de los testigos sobre modelos activos; no dice que la batería funcional completa se haya vuelto a ejecutar. Los tresFAIL originales de mensajeCLI y su correctiva se mantienen separados, igual que las omisiones y la capacidad. Esta revisión tampoco acredita automáticamente todas las obligaciones antiguas deCR09/N3.

## Pendiente antes de B16

Conciliar las once exclusiones oficiales, conservar la disposición de todos losSKIP y fijar la candidata final con producto/dependencias/migraciones/datasets/instrumentos y límites de reutilización. La matriz aporta evidencia semántica local para los criterios enumerados; no convierte las aceptaciones de apertura/proveedores o capacidad universal en aprobadas. B16 permanece abierto. El cierre final también exige reconstrucción completa del grafo y actualización diferencial del inventario; no se han realizado por este refresco dirigido.
