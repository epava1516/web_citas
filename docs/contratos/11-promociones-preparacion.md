# CR-10 — Contrato de preparación comercial

Fecha:2026-10-06. Estado: catálogo completo integrado y verificado localmente en df88067; CR10 comercial no aceptado. Evidencias/cola vigentes en seguimiento17. Vinculantes: contrato funcional14 §7 y ejecución16 §4/§13. No cambia el alcance, activa ventas ni acredita proveedor, fiscalidad o condiciones comerciales. La cola y aceptación vigentes están en seguimiento17.

## Entrega independiente inicial: catálogo sin datos de clientes

Preparar primero productos/versiones, administración, validaciones y previsualización ES/EN. La metadata del catálogo no necesita pedidos ni cuentas de clientes. Su auditoría identifica al operador y requiere correspondencia con derechos, descrita al final. MOD01 permite preparación en worktree aislado. El ensayo grande16353 ya terminó correctamente y su congelación está levantada. PERF-INSPECCIÓN-02 y catálogo están cerrados localmente; consultar seguimiento17 para el siguiente trabajo.

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


## Auditoría del catálogo y dependencia de derechos

Implementado originalmente en d772ea0 e integrado/verificado localmente en df88067: PromotionCatalogueAudit registra actor, versión de producto, operación, edit_version, fecha y SHA256 del contenido canónico. No conserva nombres/contactos del cliente ni cuerpo libre de solicitud. El evento se inserta en la misma transacción que el cambio; fallo de auditoría debe revertir el cambio. Replay de publicación vigente no añade evento. Los servicios soportados son la vía de escritura; no se acredita protección contra modificaciones directas de DBA.

El actor es dato personal: censo de cuenta y perfil sujeto incluye únicamente sus eventos como dependent_evidence, con revisión requerida y digest sensible a cambios. La configuración del catálogo no concede autoridad sobre otros operadores. Esto introduce dependencia explícita con fuentes de CR09 y exige regresiones de acceso/conservación/aislamiento antes de integrar. No fija automáticamente plazo legal ni borrado; esos mecanismos requieren la decisión de finalidad y conservación ya prevista. Migración catalog0003 aplicada en PostgreSQL local; regresiones de derechos y aislamiento correctas. No acredita conservación jurídica integral.


## Ejecución reproducible de gates pendientes

Rama aislada, scripts/verify_promotion_catalogue.py (1657f1f): ejecutor utilizado en bases PostgreSQL desechables; informes revisados en seguimiento17. Después de la carga activa indicada en seguimiento17 y de revisar su resultado, usar el intérprete .venv del proyecto principal y pasar --env-file con su .env y --output con directorio privado nuevo absoluto de /tmp. El ejecutor exige fuentes confirmadas en Git; crea una base promotion_gate_UUID y la base de tests correspondiente, aplica migraciones reales y ejecuta catálogo/auditoría/móvil junto con regresiones de avisos, dependencias de inventario y ámbito de copia. Captura logs privados, JUnit, commit y SHA256 de artefactos; elimina únicamente las dos bases de su invocación y verifica ausencia. No altera ni borra la base principal. PostgreSQL desechable no significa servicios externos aislados/verificados: worker/Beat no se prueban en esta batería, los fixtures conservan sus adaptadores explícitos.

Gate positivo requiere migration_exit=0, pytest_exit=0, cleanup_verified=true y revisión del JUnit y su alcance; phase_accepted permanece false. Ruff/compilación del ejecutor son comprobaciones estáticas, no evidencia de ejecución, restauración o limpieza real. La migración y las regresiones compartidas deben pasar antes de integrar la rama y verificar Docker.


## Interfaces del catálogo implementadas en rama aislada

Interfaces ce4729e integradas en df88067 y comprobadas localmente. Prefijo /{es|en}/operations/promotion-products/. Todas las operaciones requieren cuenta activa, MFA habilitado, versiones de sesión/MFA vigentes y permiso catalog.manage_promotion_products. El servidor reconsulta autoridad; ocultar navegación no sustituye autorización. Datos de catálogo privados, respuestas de pantalla con no-store/noindex; sin rutas de compra ni concesión de promociones.

| Ruta relativa y nombre | GET | POST |
| --- | --- | --- |
| vacío, promotion_products | Listado paginado50 y formulario | Crear producto y primer borrador;302 a edición |
| {product_uuid}/, promotion_product_versions | Versiones paginadas50 | Crear borrador siguiente bajo bloqueo de producto;302 a edición |
| {product_uuid}/versions/{number}/, promotion_version_edit | Edición de borrador; publicada sin formulario editable | Guardar datos válidos con edit_version esperado;302 a preview |
| {product_uuid}/versions/{number}/preview/, promotion_version_preview | Duración, configuración pendiente/completa y patrocinio de muestra | Publicar configuración con edit_version esperado;302 al mismo preview; replay actual conserva estado/auditoría |

Producto: slug obligatorio, único, máximo64; kind obligatorio entre premium/top/autobump. Versión: nombres ES/EN obligatorios máximo100, duration_days entero positivo; amount decimal positivo o ausente, currency EUR o ausente, tax_rate decimal0–100 o ausente; bump_interval_minutes/daily_bump_limit enteros positivos opcionales únicamente para autosubida. edit_version entero positivo oculto, ligado a versión persistida; el cliente no fija producto/version/published_at/is_current/actor. Configuración incompleta puede publicarse como configuración pendiente, siempre sellable=false. No equivale a activación comercial.

Entrada inválida de formulario:400 sin mutación. Conflicto de edición/configuración publicada o contador inválido de release:409. Producto/versión inexistentes:404 tras autorización. Sin login:302 al login; sin autoridad:403. Métodos distintos de GET/POST:405. POST exige CSRF; GET no crea auditoría ni cambia estado. Los contadores/paginación son del catálogo privado autorizado.

Pruebas ejecutadas correctamente en el gate inicial: GET privado sin efectos, acceso GET/POST directo denegado tras retirada del permiso, formularios inválidos sin cambio, publicación simultánea de dos versiones conserva ambas configuraciones y exactamente una vigente. Junto a replays/CSRF/MFA/revocaciones/aislamiento/auditoría/móvil, deben pasar sobre la misma versión de rama antes de integrar.


El ejecutorcd0da56 requiere credenciales PostgreSQL, pero si falta SAFETY_ENCRYPTION_KEY genera una clave Fernet efímera para esta invocación de datos sintéticos. No escribe esa clave en archivos/logs ni modifica la aplicación principal; base/resultados personales permanecen desechables. El primer arranque abortó antes de crear bases por la exigencia innecesaria de esa clave. Esto no acredita configuración de cifrado productiva.

## Cierre local verificado

Catálogo integrado, migraciones aplicadas y Docker comprobado. Evidencia inicial40 casos correctos, repetición dirigida4 correctos y dependencia común22 correctos son runs separados, sin aceptación N3. Informes: [corregidos](../evidencias/promociones-catalogo-gates-corregidos0110.json), [integración](../evidencias/promociones-catalogo-integracion0110.json), [runtime](../evidencias/promociones-catalogo-runtime0110.json). El catálogo nunca concede promoción ni activa venta. La segunda entrega comercial y los gates de fase/producción permanecen pendientes.
