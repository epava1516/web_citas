# Corrección de ejecución: cerrar recorridos completos

Fecha: 2026-10-06. Autorización: petición del usuario de terminar la fragmentación y desatascar el desarrollo. No cambia el alcance de docs16 ni permite cerrar funciones parciales.

## Diagnóstico contrastado

La copia de perfil de `rights_exports.source_copy` ya contiene cuenta del sujeto, revisiones, contactos, categorías/servicios, localización, tarifas e inventario de imágenes; `rights_account_copy.source` contiene la proyección propia de cuenta. La nueva consulta por campo vuelve a tratar parte de esos datos. `rights_access_scope_inventory` cataloga todos los campos concretos, incluidos credenciales, claves técnicas y referencias: ese censo no determina por sí mismo qué se debe entregar al solicitante. Exigir aprobación manual de cada columna y añadir persistencia/revisión/interfaz como hitos aislados multiplicó trabajo y no cerró el derecho. Los registros no proyectados y datos compartidos sí requieren tratamiento real; no se pueden ignorar para conseguir verde.

## Decisión ejecutiva vinculante para la continuación

Se sustituye la secuencia de entregas auxiliares por **CR09-END-ACCESS**, una única entrega de copia, revisión, respuesta, cierre y descarga. Los componentes de docs88 ya verificados se congelan en alcance: se integran, no se amplían salvo defecto reproducible o requisito concreto. No crear otra familia de modelos/colas/pantallas para cada paso ni una revisión manual por columna. No borrar helpers existentes ni migraciones; conservar compatibilidad y trabajo previo.

La unidad de revisión será un paquete de acceso coherente: copia existente e información aprobadas, suplemento de datos realmente ausentes, y decisiones de alcance/exclusión que pueda comprobar otro actor. El inventario técnico se utilizará para contrastar origen y descubrir omisiones. La correspondencia de datos ya proyectados se calculará en servidor; no pedir decisiones duplicadas sobre el mismo dato. Los campos desconocidos o personales no cubiertos bloquean cobertura, mientras credenciales/referencias internas necesitan una política explícita y verificable, no una entrega automática ni un contador usado como sustituto de criterio.

La revisión existente de respuesta se extenderá para consultar y aprobar ese paquete exacto. Solo introducir persistencia adicional si un vínculo no puede conservarse con los artefactos existentes; registrar esa necesidad. Emisión/cierre deberá consumir esa aprobación, incrementar versiones, crear respuesta/outbox y resolver exclusivamente acceso de forma atómica e idempotente. Descarga posterior comprobará cierre/recibo/prueba/vigencia/confidencialidad. No sustituir acceso completo por respuesta progress o por un cierre parcial que oculte desarrollo pendiente.

## Trabajo restante dentro de la única entrega

1. Integrar copia/información/contabilidad/suplemento e identificar la cobertura semántica real: datos ya copiados, datos adicionales y exclusiones fundamentadas. Tratar procedimiento actual y recursos realmente mantenidos por la aplicación; proveedores no contratados no equivalen a recursos externos verificados.
2. Vincular paquete y su origen a borrador/revisión de respuesta existentes, con consulta independiente del contenido y límites exactos.
3. Implementar cierre tipado de acceso, interfaz de ejecución y descarga privada después del cierre utilizando los controles existentes.
4. Ejecutar batería de aceptación del recorrido perfil/cuenta con PostgreSQL y navegador ES/EN, permisos, cambios de origen, revocación, reintento/concurrencia y confidencialidad. Usar fixtures comunes; evitar reconstruir todos los recorridos anteriores para probar cada cambio menor. Mantener las regresiones necesarias y no sustituir integración por simuladores.
5. Actualizar Docker/documentación y emitir una única evidencia del recorrido. Solo entonces marcar acceso cerrado localmente y pasar directamente a rectificación, supresión y limitación/oposición; después aceptación global CR09, CR10 y restantes fases del contrato original.

No intercalar entregas de nuevas utilidades ni ampliar escenarios por hipótesis. Se permiten checkpoints de código en desarrollo, pero no presentarlos como hitos funcionales cerrados. Las esperas deben corresponder a un proceso confirmado vivo y no justificar reiniciar pruebas. Un fallo requiere corregir y repetir lo afectado; un verde sobre una pieza previa permite seguir.

## Evidencia requerida para terminar CR09-END-ACCESS

Un titular sintético de perfil y otro de cuenta recorren comprobación, copia, revisión independiente, respuesta, cierre y descarga; la copia y el texto coinciden con la versión aprobada y explican exclusiones. El caso queda resuelto y las versiones avanzan una sola vez; reintentos no duplican respuesta/aviso. Acceso ajeno, MFA/sesión revocados, origen/revisión alterados o vencidos y descargas de otra autoridad quedan bloqueados. GET no revela contenido interno que requiera lectura auditada. La aceptación es de todo el recorrido, no suma de pruebas de módulos. Simulaciones/proveedores/CI externo pendientes se identifican sin acreditarlos como reales.

El contrato completo sigue activo. Este documento cambia el método de ejecución, no declara el derecho ni CR09 terminados.
