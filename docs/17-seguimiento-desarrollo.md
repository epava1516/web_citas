# Seguimiento de ejecución del contrato

Actualizado: 2026-10-06. Corte documental: código de purga `72ff79a`, código desplegado `8a689fc`, migración Docker `0110`. [Contrato completo](16-contrato-ejecucion-desarrollo.md).

## Estado vigente para reanudar

**Este documento es la entrada única de reanudación.** El historial no define trabajo pendiente ni procesos activos. El contrato conserva BASE → CR01–10 → GS01 → BF/BB → C; CR09 continúa abierto.

| Estado | Alcance y evidencia |
| --- | --- |
| Verificado localmente | BASE y CR01–08. No equivale a aceptación de producción. |
| Recorridos locales entregados | Acceso y portabilidad con revisión/cierre/descarga; rectificación de perfil/cuenta con respuesta/revisión/cierre. [Matriz por derecho](88-matriz-cierre-derechos.md). |
| Respuestas parciales entregadas | Supresión, limitación y oposición: preparación, consulta auditada, revisión independiente, emisión y acuse; perfiles/cuentas, publicación/calendario, medios y concurrencia en el alcance probado. No cerrar íntegramente estos derechos ante pendientes. |
| Integración entregada | Núcleo `72ff79a`:26 pruebas PostgreSQL correctas de purga, limitación/oposición, supresión, rectificación y portabilidad. [Resultados](evidencias/conservacion-borradores-finales0109.json). No es regresión completa del repositorio. |
| Docker verificado | App/worker/Beat fuente `8a689fc`, migración0110 y62 archivos coincidentes; UID10001/PostgreSQL, Django/migraciones, salud HTTP/CSS y lectura real de cola normal correctos. Cola/prefijo normal intactos y RecoveryModeFalse. [Runtime](evidencias/historico-redis-runtime0110.json). Consultas de sesiones/avisos verificadas en sus entregas anteriores. |
| Purga automática verificada | Borradores caducados no emitidos, lote≤100; vigentes/evidencia emitida/auditoría conservados. Worker y Beat reales sobre PG/Redis/cola/prefijo aislados; repetición/automatismo/retirada del entorno comprobados. [Operación](evidencias/conservacion-borradores-finales0109-worker-beat.json). Conservación jurídica integral y otros artefactos siguen pendientes. |
| Comunicaciones integradas localmente | Supresión/limitación/oposición: evaluación/revisión, notificación mínima revisada a cuentas autorizadas, buzón/consulta/acuse auditado, reevaluación y consumo en respuesta final parcial. Migración0110. Batería integrada21 correcta, concurrencia/aislamiento2 correctas y móvil ES/EN1 correcta; [evidencia](evidencias/comunicaciones-derechos-integradas0110.json), [alcance90](90-comunicaciones-derechos-ejecutados.md). Docker0110 verificado; transporte externo/censo integral pendientes. |
| Censo de notificaciones integrado | RightsRecipientNotice incorporado a perfil/cuenta como evidencia dependiente opaca; sujeto propio, exclusión del procedimiento actual y cambios de estado comprobados.3 pruebas específicas y7 de integración correctas; [evidencia](evidencias/censo-avisos-derechos0110.json). Fuente2991e4e y Docker verificados; sin política nueva de conservación ni autorización de borrado. |
| Censo de sesiones caducadas integrado | Las sesiones propias todavía almacenadas se incluyen aunque hayan caducado; metadato de caducidad explícito, capacidades/ajenas excluidas y desconocidos bloqueados.1 prueba PG y2 recorridos integrados perfil/cuenta correctos; [evidencia](evidencias/sesiones-caducadas-retenidas0110.json). Fuente552e9b6 y Docker verificados; sin borrado/tarea nueva. |
| Lectura de colas limitada integrada | Censo Redis/Kombu real de colas/prioridades/reservados con límite previo a transferencia de256KiB/mensaje y8MiB agregados, preservando mensajes y ámbito.1 prueba correcta; [evidencia](evidencias/censo-colas-limites-bytes0110.json). Fuente43250d0 y Docker verificados; sin tarea nueva. |
| Calendario paginado integrado | Cursor firmado por usuario/filtro y caducidad, páginas50/lotes100 y autorización por fila. Recorrido sintético1100 entradas y móvil ES/EN:4 pruebas correctas;8 regresiones previas correctas. [Evidencia](evidencias/calendario-conservacion-paginacion0110.json). Docker cacfe94 verificado; no aceptación integral de rendimiento/conservación. |
| Autoridad de reconocimiento urgente corregida | Reconsulta tras bloqueos y antes de retorno, también replay;8 fallos previos y14 pruebas finales correctas. [Evidencia](evidencias/alertas-autoridad0110.json). Docker99e67a0 verificado; escalado integral continúa abierto. |
| Seguimiento interno de urgentes integrado | Alertas reconocidas no terminales visibles con responsable/asignación pendiente; filtro ES/EN, COI y recorrido móvil a consulta privada verificados.16 pruebas módulo y1 móvil ampliada en runs separados. [Evidencia](evidencias/alertas-seguimiento0110.json). Docker124df1a verificado; canal externo/escalado humano/rendimiento pendientes. |
| Correo console integrado localmente | Proyección MIME completa del formato de cuenta, vínculo titular/token y enlace oculto; integrado en operations.Mail/revisión existente.2 pruebas lector y2 recorridos de cierre/descarga perfil/cuenta correctos en runs separados. [Evidencia](evidencias/correo-console-integrado0110.json). Dockerbaf9009 verificado; cobertura histórica/otros formatos y censo integral abiertos. |
| Caché de aplicación sin almacenamiento | DummyCache explícita en app/worker/Beat nuevos; escrituras sintéticas no retenidas y contenedores previos retirados. [Runtime](evidencias/historico-redis-runtime0110.json). No elimina pendiente de copias históricas del host/backups/cachés externas. |
| Histórico Redis integrado localmente | Asociación exacta foto propia/DB0/cola y reservados, validador compartido, snapshots auditados PG perfil/cuenta y regresiones console correctos. operations.QueueHistory usa revisión existente; histórico parcial bloquea acceso completo. [Evidencia](evidencias/historico-redis-paquete0110.json). Docker8a689fc verificado; origen histórico no configurado en servicio normal y cobertura íntegra abierta. |
| Fases posteriores | CR10, GS01, BF, BB y C pendientes como fases. Ya existe frontend/backend de los recorridos cruzados; esto no acepta sus fases separadas. |

## Próximo trabajo y criterio de salida

1. Completar censo de recursos/destinatarios y conservación por finalidad de CR09: completar cobertura de otros formatos/histórico; contrastar persistencia Redis/backups y copias históricas del host/cachés externas. Snapshot Redis real capturado cifrado y examinado aisladamente ([evidencia](evidencias/redis-snapshot-origen0110.json)); falta asociación/diferencias de contenido, no basta igualdad de cantidades. AOF real capturado cifrado, prefijo40504424bytes íntegro inspeccionado incrementalmente ([evidencia](evidencias/redis-aof-lectura-incremental0110.json)): asociación tipada integrada en código del mismo paquete y verificada; completar censo restante; sufijo posterior, base/histórico y fechas originales siguen pendientes. [Configuración real parcial](evidencias/censo-configuracion-operativa0110.json) confirma estas fuentes, sin acreditar su contenido íntegro. Preservar comunicaciones0110/purga0109/recorridos entregados salvo defecto o requisito concreto.
2. Completar los requisitos residuales de CR09 en [auditoría83](83-auditoria-pendientes-cr09.md): conservación/destrucción por finalidad, comunicaciones/destinatarios, atención/escalado, rendimiento y censo operacional real. La prioridad de esta lista no elimina ningún requisito del contrato.
3. Integrar evidencia de la misma versión contra todos los requisitos para aceptar CR09; continuar CR10 → GS01 → BF/BB → C. No saltar gates ni sustituirlos por porcentajes.

Las fuentes operativas siguen sin censo completo: asociación al sujeto, contenedores históricos, host/correo y copias históricas/cachés externas/backups. Las capturas cifradas parciales no eliminan esos pendientes. Proveedores/identidad/entrega externos y revisión jurídica no se acreditan con fixtures ni simuladores. CI externo pendiente por facturación/límite; no equivale a un resultado funcional.

## Avance ponderado vigente

| Alcance | Avanzado | Pendiente |
| --- | ---: | ---: |
| CR09 | 69,05% | 30,95% |
| Contrato completo | 60,3575% | 39,6425% |

Fuente de cálculo: [v4](evidencias/avance-ponderado-v4.json); método y cortes anteriores en [medición86](86-medicion-avance-contrato.md). Pesos estables, CR09 pesa15% del contrato. Estimación de ingeniería por alcance entregado, no horas ni aceptación formal. La entrega0110 eleva únicamente el bloque de comunicaciones60→70 por su nuevo alcance interno entregado. Los demás pesos/grados no cambian; no aumentar porcentajes por repetir pruebas. BASE/CR01–08 son9/15 hitos verificados localmente; ese60% de hitos no es el porcentaje ponderado.

## Cómo mantener el seguimiento sin fragmentarlo

- Actualizar este estado y el próximo paso en cada entrega o cambio relevante; no acumular nuevos «estados vigentes» al final del archivo.
- Registrar requisito → implementación/commit → evidencia/versión → pendiente/criterio de aceptación. Mantener separados workspace, Git, runtime y aceptación integral.
- Guardar la cronología en [historial](17-historial-desarrollo.md); sus referencias «activo», «pendiente» o «no aplicado» no son instrucciones de reanudación.
- La matriz88 conserva componentes y recorridos verificados; la auditoría83 conserva requisitos residuales; docs86 explica el cálculo. Estos documentos enlazan este seguimiento para el próximo paso y runtime vigente, sin mantener otra cola de ejecución.
- Reabrir un componente solo por defecto reproducible, regresión demostrada o requisito concreto pendiente. Documentar motivo y alcance; integrar código compartido no revoca su aceptación anterior.
- Una repetición de pruebas se justifica por cambios/fallos/incertidumbre nuevos. No sumar baterías distintas ni anunciar un proceso como vivo sin comprobarlo.

Claude3/3 consumidas; continuar localmente. No publicar la web, contratar proveedores ni utilizar datos reales. Esta consolidación documental no cambia el contrato, el porcentaje ni la aceptación.
