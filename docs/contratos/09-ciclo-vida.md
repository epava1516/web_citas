# CR-08 — Favoritos y ciclo de vida, diseño pendiente de implementación

Estado: CR-08 en curso; favoritos implementados y verificados localmente, acciones de ciclo de vida implementadas y en verificación dirigida. CR-07 cerrado localmente en acta02. ES/EN SSR y PostgreSQL, acciones POST con CSRF; GET no cambia estados.

## Favoritos privados

Una relación única cuenta/anuncio, independiente de rol particular/agencia/visitante. Añadir y eliminar de forma idempotente, solo de la propia cuenta. No perfil público de visitante, historial de búsqueda ni avisos al anunciante. Lista privada no cacheada. Para anuncios no elegibles mostrar solamente una referencia privada genérica eliminable, sin alias, descripción, contactos ni imágenes antiguas; no seguir exponiendo contenido retirado por conservar un favorito. Denegación de acceso cruzado y concurrencia de alta necesarias. Retención/exportación/borrado conectarán con CR-09 y B-B.

Rutas previstas: /favorites/ GET; /listing/{id}/favorite/ POST (añadir un anuncio elegible); /favorites/{id}/remove/ POST (eliminar relación propia). Ninguna identidad de favorito/usuario se incorpora al listado público.

## Acciones de publicación

Panel privado del gestor vigente y asignado, controles por anuncio. Persona representada conserva revocación/transferencia independientes existentes. Acciones previstas: pausa, reanudación, renovación con confirmación explícita de datos, retirada y disponible ahora. La retirada aquí significa quitar exposición, no acreditar eliminación de todos los datos conservados; derechos/borrado tienen flujo separado.

- Pausa: published → paused; elimina disponibilidad inmediata. No borra revisión aprobada ni fotos privadas.
- Reanudación: paused → published solo si todavía vigente, validación completa y revisión actual aprobada, sin restricciones pendientes. No prolonga vigencia ni fecha editorial.
- Renovación: confirmación explícita, conserva Listing/Person/approved_revision; ventana desde siete días antes de caducar, nueva vigencia de treinta días y fecha real de renovación para ordenar, nunca promoción pagada. Revalida edad/autorización/gestor/agencia/contactos/catálogo/fotos y conflictos. No renueva retirados ni sustituye revisión humana pendiente.
- Caducidad: tareas pueden pasar published vigente agotado → expired, nunca publicar. El servicio público ya excluye expires_at agotado sin depender de que haya corrido Beat. Tareas atrasadas deben comprobar estado y vigencia actuales, evitando caducar una renovación posterior.
- Retirada: cualquier estado salvo withdrawn → withdrawn, elimina disponibilidad. Repetir retirada no crea anuncios ni vuelve a activar contenido. Volver a publicar requiere nueva revisión aprobada, no una tarea antigua.
- Disponible ahora: opt-in exclusivo de published elegible, hasta cuatro horas desde confirmación; cancelar disponible de forma explícita. No promete respuesta. Reintento de la misma acción no amplía el periodo. Pausa/retirada/revocación/conflicto/caducidad dejan de mostrar disponibilidad.

## Versiones, permisos e historia

Cada acción serializa persona/gestor y anuncio; revalida permiso, gestor y revisión dentro del bloqueo. Preparar versión del ciclo de vida y clave de acción única con payload/actor/gestor: reintento exacto conserva resultado, claves reutilizadas con otro contenido o formularios obsoletos no sobrescriben cambios. Decisiones de moderación/revocación/transferencia/conflicto deben invalidar los formularios previos. Eventos de acción conservan actor, operación, instante y transición sin duplicar datos personales de la ficha.

Código esperado: éxito302 a panel propio; acceso no autorizado404/403 conforme a contratos existentes; formulario inválido400; versión/estado incompatible409. Nunca aceptar campos públicos del anuncio como parte de una renovación sin revisión; la confirmación renueva una revisión aprobada exacta.

## Aceptación pendiente

Servidor y navegador móvil ES/EN: alta/eliminación/lista privada de favoritos, aislamiento, repetición y concurrencia. Panel particular/agencia/editor autorizado: pausa/reanudación, renovación conservando ID y revisión, caducidad por reloj/tarea, disponible4h, retirada y formulario/tarea obsoletos. Verificar búsquedas, ficha y derivados tras cada retirada de exposición; ningún proceso antiguo republica. Documentar servicios de tareas y rutas definitivas al implementar, y corregir este diseño si la evidencia exige ajustes compatibles.


Dependencias comprobadas antes de implementar: moderation.decide cambia revisión/estado/fechas al aprobar; verification.revoke y transfer pausan mediante actualización queryset; match_review.resolve pausa ante conflicto. CR-08 debe incrementar/invalidar versión en estos puntos además de sus acciones propias, sin perder bloqueos existentes. Al aprobar una revisión nueva, limpiar disponible ahora: una confirmación asociada a la revisión anterior no acredita disponibilidad de la nueva. La fixture seed_demo modifica un estado para pruebas y no sustituye estos servicios.


Interfaz de favoritos implementada: GET /favorites/ solo cuenta autenticada, paginación24, private/no-store. POST /listing/{UUID}/favorite/ comprueba elegibilidad bajo bloqueo Person→Listing y crea relación única user/listing; reintento302 sin duplicar. GET de alta405; anónimo requiere acceso. POST /favorites/{ID relación}/remove/ consulta exclusivamente user actual; éxito302, ID ajeno/inexistente o repetición tras eliminar404, conservando efecto idempotente de eliminación. El UUID del anuncio retirado no aparece en la entrada genérica: solo ID privado de la relación propia para poder borrarla. No avisos al anunciante ni datos de otras cuentas.

Pantallas: enlace Favoritos/Favorites en navegación autenticada, botón de guardar desde ficha elegible y lista privada con botón eliminar. Lista sin elementos y anuncios no disponibles tienen mensajes ES/EN. Migración listings0009 añade Favorite y unicidad. Este avance no implementa pausa/renovación/retirada/disponibilidad ni cierra CR-08.

Logs Gunicorn: rutas favorites y favorite se reducen a /private-operation/, sin ID de relación/anuncio o parámetros. Verificación local:4 pruebas finales servidor/navegador/concurrencia y4 de logs; ciclo de vida pendiente.


Implementación de ciclo de vida en verificación: GET/POST /listing/{UUID}/manage/, gestor vigente con permisos de agencia/editor existentes. ActionForm key UUID/version/operation/confirm, errores de formato400 y estado/versión/clave incompatible409, éxito302; panel/respuestas de error private/no-store y logs /private-operation/. LifecycleAction único key conserva actor/gestor/versión/operación/confirmación/estado previo y resultante, además de referencia a la revisión aprobada exacta. Reintento exacto no modifica estado aunque luego haya otra acción; payload distinto409. No reutiliza la renovación como edición de datos aprobados.

Ventana de renovación gratuita: últimos siete días de vigencia o caducado; evita cambiar fecha editorial continuamente mediante renovaciones anticipadas. Renovar pausado conserva pausa, caducado elegible vuelve a publicado; retirado necesita nueva revisión. Retirada cancela revisiones draft/processing/pending del gestor actual, impidiendo aprobación atrasada. Los borradores nuevos pueden iniciar nuevo recorrido de revisión; tareas de fotos no publican.

Moderación, revocación/transferencia y decisiones de coincidencias incrementan lifecycle_version; revocación/transferencia lo hacen también sobre anuncios ya pausados. Nueva revisión aprobada borra disponibilidad anterior. expire_listings cada60s toma hasta1000 candidatos y expire_one bloquea cada anuncio con skip_locked, revalida estado/fecha actual antes de caducar y nunca publica; una renovación posterior a la selección no caduca por tarea atrasada. Tarea devuelve número de cambios; disponibilidad pública se comprueba por timestamp aunque no se haya ejecutado Beat. Migraciones listings0010/0011 aplicadas localmente. Beat/worker real, agencias/editor y cierre común todavía pendientes.


Historia reforzada: listings0012 permite actor nulo exclusivamente para acción automática expire y guarda approved_revision. Caducidad y evento se escriben en la misma transacción; repetición/concurrencia no duplican eventos. Historial antiguo conserva referencia vacía cuando no se registró, sin reconstruir evidencia inventada. Panel muestra hasta20 acciones recientes del manager_version actual, con sistema/gestor y fechas, sin identidades de actores ni datos del gestor anterior. Incluye instante de fin de disponibilidad. Retención del historial y ejercicio de derechos continúan pendientes en CR-09/B-B. Seis pruebas ciclo de vida passed33.02s; tres finales historia/concurrencia de caducidad/Chromium passed20.93s.

Operación local verificada: worker/Redis y Beat realizan caducidad con evento único en registros sintéticos aislados inelegibles; scripts/probe_expiry_worker.py reproduce ambos modos sin producción. Resultado Celery ignorado por configuración: verificar estado PostgreSQL y logs, no inferir terminación por .get. Pruebas nuevas de editor/MFA/revocación, carrera renovación/caducidad y renovación móvil pasan19.06s. Regresión común y cierre CR-08 aún pendientes.
