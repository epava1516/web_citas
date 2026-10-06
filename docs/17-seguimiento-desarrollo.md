# Seguimiento de ejecución del contrato

Actualizado: 2026-10-06. Corte documental: código de purga `72ff79a`, código desplegado `9be0044`, migración Docker `0109`. [Contrato completo](16-contrato-ejecucion-desarrollo.md).

## Estado vigente para reanudar

**Este documento es la entrada única de reanudación.** El historial no define trabajo pendiente ni procesos activos. El contrato conserva BASE → CR01–10 → GS01 → BF/BB → C; CR09 continúa abierto.

| Estado | Alcance y evidencia |
| --- | --- |
| Verificado localmente | BASE y CR01–08. No equivale a aceptación de producción. |
| Recorridos locales entregados | Acceso y portabilidad con revisión/cierre/descarga; rectificación de perfil/cuenta con respuesta/revisión/cierre. [Matriz por derecho](88-matriz-cierre-derechos.md). |
| Respuestas parciales entregadas | Supresión, limitación y oposición: preparación, consulta auditada, revisión independiente, emisión y acuse; perfiles/cuentas, publicación/calendario, medios y concurrencia en el alcance probado. No cerrar íntegramente estos derechos ante pendientes. |
| Integración entregada | Núcleo `72ff79a`:26 pruebas PostgreSQL correctas de purga, limitación/oposición, supresión, rectificación y portabilidad. [Resultados](evidencias/conservacion-borradores-finales0109.json). No es regresión completa del repositorio. |
| Docker verificado | App/worker/Beat fuente `9be0044`, migración0109 y43 archivos coincidentes; PostgreSQL/columnas, UID10001, rutas, salud HTTP y CSS correctos. [Runtime](evidencias/conservacion-borradores-finales0109-runtime.json). |
| Purga automática verificada | Borradores caducados no emitidos, lote≤100; vigentes/evidencia emitida/auditoría conservados. Worker y Beat reales sobre PG/Redis/cola/prefijo aislados; repetición/automatismo/retirada del entorno comprobados. [Operación](evidencias/conservacion-borradores-finales0109-worker-beat.json). Conservación jurídica integral y otros artefactos siguen pendientes. |
| En desarrollo local | Evaluación/revisión auditada de destinatarios para supresión/limitación/oposición. Fuente ligada a ejecución vigente y permisos reconsultados; notificaciones, pantallas y consumo en respuesta final pendientes. [Alcance90](90-comunicaciones-derechos-ejecutados.md). 3 variantes PostgreSQL correctas y 1 regresión de extracción de candidatos de rectificación; [evidencia](evidencias/comunicaciones-derechos-evaluacion.json). Sin integración HTTP ni despliegue. |
| Fases posteriores | CR10, GS01, BF, BB y C pendientes como fases. Ya existe frontend/backend de los recorridos cruzados; esto no acepta sus fases separadas. |

## Próximo trabajo y criterio de salida

1. Completar comunicaciones por finalidad de supresión/limitación/oposición con sus ejecuciones y pendientes, reutilizando inventarios/revisión existentes; no reabrir purga0109 ni recorridos entregados salvo defecto/requisito concreto.
2. Completar los requisitos residuales de CR09 en [auditoría83](83-auditoria-pendientes-cr09.md): conservación/destrucción por finalidad, comunicaciones/destinatarios, atención/escalado, rendimiento y censo operacional real. La prioridad de esta lista no elimina ningún requisito del contrato.
3. Integrar evidencia de la misma versión contra todos los requisitos para aceptar CR09; continuar CR10 → GS01 → BF/BB → C. No saltar gates ni sustituirlos por porcentajes.

Las fuentes operativas siguen sin censo completo: asociación al sujeto, contenedores históricos, host/correo y cachés/backups. Las capturas cifradas parciales no eliminan esos pendientes. Proveedores/identidad/entrega externos y revisión jurídica no se acreditan con fixtures ni simuladores. CI externo pendiente por facturación/límite; no equivale a un resultado funcional.

## Avance ponderado vigente

| Alcance | Avanzado | Pendiente |
| --- | ---: | ---: |
| CR09 | 68,25% | 31,75% |
| Contrato completo | 60,2375% | 39,7625% |

Fuente de cálculo: [v3](evidencias/avance-ponderado-v3.json); método y cortes anteriores en [medición86](86-medicion-avance-contrato.md). Pesos estables, CR09 pesa15% del contrato. Estimación de ingeniería por alcance entregado, no horas ni aceptación formal. La entrega0109 completa el pendiente operativo de esos borradores; no aumenta automáticamente porcentajes por sus pruebas. BASE/CR01–08 son9/15 hitos verificados localmente; ese60% de hitos no es el porcentaje ponderado.

## Cómo mantener el seguimiento sin fragmentarlo

- Actualizar este estado y el próximo paso en cada entrega o cambio relevante; no acumular nuevos «estados vigentes» al final del archivo.
- Registrar requisito → implementación/commit → evidencia/versión → pendiente/criterio de aceptación. Mantener separados workspace, Git, runtime y aceptación integral.
- Guardar la cronología en [historial](17-historial-desarrollo.md); sus referencias «activo», «pendiente» o «no aplicado» no son instrucciones de reanudación.
- La matriz88 conserva componentes y recorridos verificados; la auditoría83 conserva requisitos residuales; docs86 explica el cálculo. Estos documentos enlazan este seguimiento para el próximo paso y runtime vigente, sin mantener otra cola de ejecución.
- Reabrir un componente solo por defecto reproducible, regresión demostrada o requisito concreto pendiente. Documentar motivo y alcance; integrar código compartido no revoca su aceptación anterior.
- Una repetición de pruebas se justifica por cambios/fallos/incertidumbre nuevos. No sumar baterías distintas ni anunciar un proceso como vivo sin comprobarlo.

Claude3/3 consumidas; continuar localmente. No publicar la web, contratar proveedores ni utilizar datos reales. Esta consolidación documental no cambia el contrato, el porcentaje ni la aceptación.
