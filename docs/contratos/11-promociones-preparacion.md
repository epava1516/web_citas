# CR-10 — Contrato de preparación comercial

Fecha:2026-10-06. Estado: especificación preparada; módulo no implementado ni aceptado. Vinculantes: contrato funcional14 §7 y ejecución16 §4/§13. No cambia el alcance, activa ventas ni acredita proveedor, fiscalidad o condiciones comerciales. La cola y aceptación vigentes están en seguimiento17.

## Entrega independiente inicial: catálogo sin datos de clientes

Preparar primero productos/versiones, administración, validaciones y previsualización ES/EN. Este tramo no necesita pedidos, cuentas de clientes, derechos nuevos ni cambios en permisos/modelos/estados/rutas de CR09. No implementarlo mientras el ensayo actual mantenga congelada la aplicación. Su documentación sí puede prepararse durante la verificación.

| Identificador propuesto | Tipo | Duración inicial | Presentación |
| --- | --- | ---: | --- |
| premium_30 | Premium |30 días| Bloque patrocinado principal dentro de filtros compatibles |
| top_10 | Top |10 días| Bloque patrocinado secundario |
| autosubida_7 | Autosubida |7 días| Elevación programada; frecuencia y cupo requieren configuración |
| autosubida_30 | Autosubida |30 días| Igual comportamiento, otra duración |

Identificador estable y versión positiva; textos de producto ES/EN, tipo, duración positiva y configuración de frecuencia/cupo para autosubidas. Una versión utilizada por pedidos de prueba será inmutable; publicar configuración nueva crea versión nueva y no modifica snapshots anteriores. Evitar notas libres de clientes en el catálogo.

Precio, moneda y configuración de impuestos empiezan sin configurar. Importes decimales, nunca float; importe configurado debe ser positivo, moneda soportada explícitamente y cálculo de impuestos validado por servidor. La falta de precio/impuestos/configuración no significa gratis ni permite vender. Previsualización muestra «Pendiente de configurar / Configuration pending»; no obtiene valores del visitante para calcular un pedido. Los importes de fixtures de pago serán inequívocamente sintéticos, separados de la configuración comercial real.

Administración únicamente por cuenta activa autorizada y MFA/sesión vigentes, incluida revalidación después de bloqueos; GET no modifica catálogo. Previsualizar no concede promoción. Se definirán rutas/formularios y permisos concretos junto a la implementación, contrastados con código y pruebas; los nombres de esta tabla todavía no son interfaces desplegadas.

Cierre de este tramo: PostgreSQL real, editar/previsualizar ES/EN, validación de configuración incompleta, usuario sin permiso, CSRF, persistencia tras recargar y concurrencia de publicación de versión. No requiere proveedor ni pago real. No acepta CR10 completo ni GS01.

## Integración cruzada posterior: pedidos y promoción de prueba

La segunda entrega depende de publicación/elegibilidad, agencias/gestor, retiro/caducidad, descubrimiento y tratamiento de nuevos datos personales en CR09. Antes de crear pedidos/intentos/derechos, actualizar su correspondencia con acceso/rectificación/supresión/conservación/restauración; no introducir tablas de cliente fuera del censo ni declarar completo un derecho que no las cubra.

Pedido fija en servidor producto/versión, importe/moneda/desglose, duración, anuncio/persona, comprador y versión de gestor; idempotencia ligada a actor y contenido exactos. Un replay idéntico conserva pedido/derecho, una clave con otro contenido produce conflicto. Cambio posterior de tarifa no recalcula el pedido. Particular/agencia mantienen una publicación por persona; un producto no cambia esa regla ni la revisión aprobada.

Adaptador de pagos exclusivamente de pruebas en v1: éxito, fallo, pendiente, repetición y evento inválido deterministas, marcados como simulación en datos y entorno de desarrollo. No conectar una pasarela real, enviar eventos externos o cobrar. El evento se asocia al intento/pedido y comprueba autenticidad, importe, moneda y estado antes de conceder; duplicados/concurrencia no duplican derechos. No tratar un resultado recibido desde el navegador como pago confirmado. La integración real futura debe verificar firmas/webhooks y secretos fuera de logs, con proveedor compatible contratado y políticas aprobadas; queda fuera de aceptación real de v1.

Concesión revalida comprador/gestor/elegibilidad y estado actual después de bloqueos. Pausa, retirada, caducidad, falta de consentimiento o publicación inválida eliminan exposición promocionada. Transferir gestión no autoriza automáticamente al comprador anterior ni convierte el anuncio en otro. La política de tiempo remanente/reembolso sigue pendiente comercial: registrar el hecho y suspender exposición, sin implementar reembolso o extensión arbitrarios.

Premium/Top se muestran en bloques identificados como patrocinados, siempre después del mismo filtro de visibilidad/territorio/categoría/búsqueda que el resultado público. Rotación equilibrada y desempate estable; no filtrar IDs privados mediante conteos. Mantener separado orden comercial de fecha editorial y relevancia orgánica. Autosubida cambia únicamente su señal comercial, sin clonar anuncio, crear revisión ni alterar publicado/renovado. Tarea idempotente por derecho/ventana temporal, frecuencia/cupos configurados y lectura acotada de candidatos; una tarea anterior no reactiva retirados o derechos caducados.

## Evidencia exigida para CR10 completo

1. Catálogo y previsualización reales; sin venta ante precio/configuración ausentes.
2. Particular y agencia crean pedido de prueba del anuncio permitido; usuario ajeno, gestor revocado y claves conflictivas rechazados.
3. Evento de prueba válido concede una sola promoción; fallo/pendiente/firma inválida/importe distinto no conceden; reintentos y carreras PostgreSQL sin duplicados.
4. Patrocinio explícito ES/EN/móvil, filtros compatibles, rotación, paginación sin repetir fichas ni ocultar reglas orgánicas; ningún contenido pendiente/retirado sale por promoción.
5. Pausa/caducidad/retiro/transferencia y tarea antigua detienen exposición; snapshots comerciales y auditoría conservan su significado.
6. Nuevos datos personales incorporados a derechos, conservación y recuperación antes de aceptar su cobertura; sin pagos por servicios de anunciantes, créditos, recurrencias o reservas.
7. Docker, contratos concretos de rutas/formularios/eventos y batería integrada sobre misma versión; declarar adaptador de pruebas y gates externos pendientes. Solo entonces considerar aceptación CR10 y requisitos GS01.
