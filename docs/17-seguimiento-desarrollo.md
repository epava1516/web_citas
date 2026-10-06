# Seguimiento de ejecución del contrato

Actualizado: 2026-10-06. Corte documental: HEAD `6e69666`, código desplegado `38140e9`, migración Docker `0108`. [Contrato completo](16-contrato-ejecucion-desarrollo.md).

## Estado vigente para reanudar

**Este documento es la entrada única de reanudación.** El historial no define trabajo pendiente ni procesos activos. El contrato conserva BASE → CR01–10 → GS01 → BF/BB → C; CR09 continúa abierto.

| Estado | Alcance y evidencia |
| --- | --- |
| Verificado localmente | BASE y CR01–08. No equivale a aceptación de producción. |
| Recorridos locales entregados | Acceso y portabilidad con revisión/cierre/descarga; rectificación de perfil/cuenta con respuesta/revisión/cierre. [Matriz por derecho](88-matriz-cierre-derechos.md). |
| Respuestas parciales entregadas | Supresión, limitación y oposición: preparación, consulta auditada, revisión independiente, emisión y acuse; perfiles/cuentas, publicación/calendario, medios y concurrencia en el alcance probado. No cerrar íntegramente estos derechos ante pendientes. |
| Integración entregada | `38140e9`: veinte pruebas PostgreSQL correctas, incluidas variantes móviles y portabilidad por acuse compartido. [Resultados](evidencias/limitacion-oposicion-final0108-en-desarrollo.json). No es regresión completa del repositorio. |
| Docker verificado | App/worker/Beat con fuente `38140e9`, migración0108 y40 archivos coincidentes; PostgreSQL, UID10001, rutas, salud HTTP y CSS verificados en la entrega. [Evidencia](evidencias/limitacion-oposicion-final-runtime0108.json). |
| Desarrollo local pendiente | Purga de borradores finales caducados no emitidos: cambios en modelos, tareas y respuestas; migración0109 y prueba nuevas. Tres pruebas PostgreSQL correctas, XML `/tmp/rights-final-draft-retention0109.xml`. **Sin commit ni despliegue; no incorporado a la aceptación de runtime0108.** |
| Fases posteriores | CR10, GS01, BF, BB y C pendientes como fases. Ya existe frontend/backend de los recorridos cruzados; esto no acepta sus fases separadas. |

## Próximo trabajo y criterio de salida

1. Terminar la entrega de purga en desarrollo: registrar evidencia trazable, verificar los ámbitos afectados y ejecución periódica real, aplicar0109 y contrastar fuente/runtime antes de declararla entregada. Preservar borradores ligados a respuestas emitidas y su auditoría. No repetir recorridos aceptados salvo cambios afectados.
2. Completar los requisitos residuales de CR09 en [auditoría83](83-auditoria-pendientes-cr09.md): conservación/destrucción por finalidad, comunicaciones/destinatarios, atención/escalado, rendimiento y censo operacional real. La prioridad de esta lista no elimina ningún requisito del contrato.
3. Integrar evidencia de la misma versión contra todos los requisitos para aceptar CR09; continuar CR10 → GS01 → BF/BB → C. No saltar gates ni sustituirlos por porcentajes.

Las fuentes operativas siguen sin censo completo: asociación al sujeto, contenedores históricos, host/correo y cachés/backups. Las capturas cifradas parciales no eliminan esos pendientes. Proveedores/identidad/entrega externos y revisión jurídica no se acreditan con fixtures ni simuladores. CI externo pendiente por facturación/límite; no equivale a un resultado funcional.

## Avance ponderado vigente

| Alcance | Avanzado | Pendiente |
| --- | ---: | ---: |
| CR09 | 68,25% | 31,75% |
| Contrato completo | 60,2375% | 39,7625% |

Fuente de cálculo: [v3](evidencias/avance-ponderado-v3.json); método y cortes anteriores en [medición86](86-medicion-avance-contrato.md). Pesos estables, CR09 pesa15% del contrato. Estimación de ingeniería por alcance entregado, no horas ni aceptación formal. El trabajo sin entregar de0109 no incrementa estos valores. BASE/CR01–08 son9/15 hitos verificados localmente; ese60% de hitos no es el porcentaje ponderado.

## Cómo mantener el seguimiento sin fragmentarlo

- Actualizar este estado y el próximo paso en cada entrega o cambio relevante; no acumular nuevos «estados vigentes» al final del archivo.
- Registrar requisito → implementación/commit → evidencia/versión → pendiente/criterio de aceptación. Mantener separados workspace, Git, runtime y aceptación integral.
- Guardar la cronología en [historial](17-historial-desarrollo.md); sus referencias «activo», «pendiente» o «no aplicado» no son instrucciones de reanudación.
- La matriz88 conserva componentes y recorridos verificados; la auditoría83 conserva requisitos residuales; docs86 explica el cálculo. Estos documentos enlazan este seguimiento para el próximo paso y runtime vigente, sin mantener otra cola de ejecución.
- Reabrir un componente solo por defecto reproducible, regresión demostrada o requisito concreto pendiente. Documentar motivo y alcance; integrar código compartido no revoca su aceptación anterior.
- Una repetición de pruebas se justifica por cambios/fallos/incertidumbre nuevos. No sumar baterías distintas ni anunciar un proceso como vivo sin comprobarlo.

Claude3/3 consumidas; continuar localmente. No publicar la web, contratar proveedores ni utilizar datos reales. Esta consolidación documental no cambia el contrato, el porcentaje ni la aceptación.


### 2026-10-06 — Conservación: purga de borradores finales sin emitir0109

Pendiente concreto encontrado tras respuestas nuevas: vigencia24h no eliminaba el texto cifrado. RightsAction incorpora purged_at y final_response nullable (PROTECT), migración0109. Emisión nueva de supresión/limitación/oposición y rectificación liga borrador a Response atómicamente; los emitidos mantienen texto/evidencia/replay para política de conservación posterior. purge_unissued_drafts procesa hasta100 caducados24h sin vínculo, bloquea expediente antes de acción, revalida después de espera y limpia solo encrypted_reason; fechas/IDs/digest/key/version quedan preservados. Histórico emitido sin FK se reconoce por acción firmada de emisión/cierre y Response exacta, se enlaza y no se purga. Vínculo ilegible/alterado conserva potencial evidencia para revisión operacional, no permite purga inferida. Consulta/revisión/otros artefactos y conservación jurídica integral siguen pendientes.

Se incorpora a tarea periódica existente purge_expired_access_response_drafts, después de finalizar su transacción original; mismo nombre/schedule/cola y retorno total de contenidos limpiados, sin tarea nueva. Sesión19311 exit0:3 casos57,36s. Preparación de ampliación no aplicada por AssertionError; sesión18673 repitió únicamente unused40,32s sin cambio: no avance adicional ni testnuevo. Corregido el parche con formato real, sesión43986 exit0:2 variantes51,28s, borrador vigente y lote100→1→0. Lote101 es volumen sintético de ledger en PostgreSQL, no101 ejecuciones autorizadas ni identidad real.

Sesión54333 terminal0: **26 passed312,68s** sobre fuente0109:4 purga,8 limitación/oposición,10 supresión,2 rectificación cuenta,2 portabilidad compartida. No sumar con preliminares. [Evidencia](evidencias/conservacion-borradores-finales0109.json). Ruff global/Django check/makemigrations--check/diff correctos. Sin pytest activo; próximos migración/runtime y worker/Beat automáticos de esta purga, pendientes integralesCR09 y resto contrato. Docker todavía38140e9/0108. Estimaciónv3 sin cambios, Claude3/3.
