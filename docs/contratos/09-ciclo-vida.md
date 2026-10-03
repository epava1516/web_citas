# CR-08 — Favoritos y ciclo de vida, diseño pendiente de implementación

Estado: propuesta interna compatible con el contrato funcional; no evidencia de funcionamiento. Se implementará tras cierre CR-07. ES/EN SSR y PostgreSQL, acciones POST con CSRF; GET no cambia estados.

## Favoritos privados

Una relación única cuenta/anuncio, independiente de rol particular/agencia/visitante. Añadir y eliminar de forma idempotente, solo de la propia cuenta. No perfil público de visitante, historial de búsqueda ni avisos al anunciante. Lista privada no cacheada. Para anuncios no elegibles mostrar solamente una referencia privada genérica eliminable, sin alias, descripción, contactos ni imágenes antiguas; no seguir exponiendo contenido retirado por conservar un favorito. Denegación de acceso cruzado y concurrencia de alta necesarias. Retención/exportación/borrado conectarán con CR-09 y B-B.

Rutas previstas: /favorites/ GET; /listing/{id}/favorite/ POST (añadir un anuncio elegible); /favorites/{id}/remove/ POST (eliminar relación propia). Ninguna identidad de favorito/usuario se incorpora al listado público.

## Acciones de publicación

Panel privado del gestor vigente y asignado, controles por anuncio. Persona representada conserva revocación/transferencia independientes existentes. Acciones previstas: pausa, reanudación, renovación con confirmación explícita de datos, retirada y disponible ahora. La retirada aquí significa quitar exposición, no acreditar eliminación de todos los datos conservados; derechos/borrado tienen flujo separado.

- Pausa: published → paused; elimina disponibilidad inmediata. No borra revisión aprobada ni fotos privadas.
- Reanudación: paused → published solo si todavía vigente, validación completa y revisión actual aprobada, sin restricciones pendientes. No prolonga vigencia ni fecha editorial.
- Renovación: confirmación explícita, conserva Listing/Person/approved_revision; nueva vigencia de treinta días y fecha real de renovación para ordenar, nunca promoción pagada. Revalida edad/autorización/gestor/agencia/contactos/catálogo/fotos y conflictos. No renueva retirados ni sustituye revisión humana pendiente.
- Caducidad: tareas pueden pasar published vigente agotado → expired, nunca publicar. El servicio público ya excluye expires_at agotado sin depender de que haya corrido Beat. Tareas atrasadas deben comprobar estado y vigencia actuales, evitando caducar una renovación posterior.
- Retirada: published/paused/expired → withdrawn, elimina disponibilidad. Repetir retirada no crea anuncios ni vuelve a activar contenido. Volver a publicar requiere nueva revisión aprobada, no una tarea antigua.
- Disponible ahora: opt-in exclusivo de published elegible, hasta cuatro horas desde confirmación; cancelar disponible de forma explícita. No promete respuesta. Reintento de la misma acción no amplía el periodo. Pausa/retirada/revocación/conflicto/caducidad dejan de mostrar disponibilidad.

## Versiones, permisos e historia

Cada acción serializa persona/gestor y anuncio; revalida permiso, gestor y revisión dentro del bloqueo. Preparar versión del ciclo de vida y clave de acción única con payload/actor/gestor: reintento exacto conserva resultado, claves reutilizadas con otro contenido o formularios obsoletos no sobrescriben cambios. Decisiones de moderación/revocación/transferencia/conflicto deben invalidar los formularios previos. Eventos de acción conservan actor, operación, instante y transición sin duplicar datos personales de la ficha.

Código esperado: éxito302 a panel propio; acceso no autorizado404/403 conforme a contratos existentes; formulario inválido400; versión/estado incompatible409. Nunca aceptar campos públicos del anuncio como parte de una renovación sin revisión; la confirmación renueva una revisión aprobada exacta.

## Aceptación pendiente

Servidor y navegador móvil ES/EN: alta/eliminación/lista privada de favoritos, aislamiento, repetición y concurrencia. Panel particular/agencia/editor autorizado: pausa/reanudación, renovación conservando ID y revisión, caducidad por reloj/tarea, disponible4h, retirada y formulario/tarea obsoletos. Verificar búsquedas, ficha y derivados tras cada retirada de exposición; ningún proceso antiguo republica. Documentar servicios de tareas y rutas definitivas al implementar, y corregir este diseño si la evidencia exige ajustes compatibles.
