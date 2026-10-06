# Auditoría de pendientes para aceptación CR-09

Fecha:2026-10-06. Referencia vinculante: contrato16 y seguimiento17. Este inventario conserva el alcance completo; no sustituye la aceptación con porcentajes ni permite pasar a CR-10 antes de completar sus dependencias. Es una auditoría técnica de evidencia local, no una revisión jurídica.

| Requisito | Evidencia actual | Falta para demostrar cierre |
| --- | --- | --- |
| Portabilidad cubierta con respuesta independiente y cierre | Servicios0095–97, pruebas HTTP/móvil/carreras y descarga JSON/WebP/ZIP;393 originales y124 integradas por separado; runtime0099 | Aceptación integral por finalidad y rendimiento/variantes pendientes; fuente original393 y versión integrada124 son alcances distintos |
| Purga de texto final caducado | Ensayo corregido62469 terminal0: worker y Beat automáticos, cuatro tareas exactas, referencias/contenido vigente y reintentos conservados, limpieza independiente confirmada | Verificado localmente; no acredita política de conservación jurídica integral ni proveedor externo |
| Acceso, rectificación, supresión, limitación y oposición completos | Flujos parciales e inventarios documentados en24,27–35,43,49,55–66 | Matriz por tipo/finalidad que vincule ejecución exacta, revisión independiente, respuesta, descarga cuando proceda y cierre; no usar cierre genérico sin evidencia |
| Conservación y destrucción por finalidad | Planes y calendario de revisión; inventarios detallados | Alcances y disparadores ejecutables, conservación reservada, destrucción y dependencias compartidas; probar historial, revisión vencida y reintentos. Una fecha de revisión no es una política jurídica aprobada |
| Restauración sin reintroducir datos suprimidos | Outbox, referencias, productor/exportador, checkpoint y preflight locales implementados;48 pruebas finales de recuperación | Aplicador tipado de efectos y ensayo de restauración de base/archivos desde copia anterior; reconciliar antes de habilitar exposición y tareas; demostrar exclusión de datos retirados y preservación de datos ajenos |
| Cachés, sesiones, logs, CDN y backups | Inventarios declaran estos recursos pendientes | Identificar cada recurso, adaptador y regla de retención; pruebas locales de invalidación/recuperación y separación explícita de proveedores no contratados |
| Comunicación y destinatarios | Acuse privado, confirmación explícita y outbox; transporte desactivado o simulado | Evidencia por canal/destinatario, gestión de fallos y comunicación de efectos del derecho; identidad/envío reales quedan sujetos a integración externa, sin declarar simulación como recepción real |
| Atención urgente y escalado | Cola persistente/reconocimiento y conciliación worker/Beat verificados por partes (docs37) | Matriz de atención/escalado y pendientes operativos externos; no interpretar reconocimiento como lectura, asignación ni resolución |
| Rendimiento de expedientes grandes | Mediciones instrumentadas de generación JSON/binarios y observaciones de validación repetida (docs67,80,82) | Medir consultas, duración, memoria y latencia de preparación/revisión/cierre/descarga cubiertos; optimizar conservando firmas originales, permisos y fuente vigentes |
| Aceptación integral | Baterías locales parciales; CI reciente sin pruebas por facturación | Misma versión para regresión requerida, contratos y evidencias; ninguna fase posterior se considera aceptada por componentes iniciales |

## Secuencia inmediata

1. Esperar terminal de regresión74215, log/XML `/tmp/portability-response-common0097`; no reiniciar por demora. Corregir fallos reales y repetir escenarios afectados.
2. La batería conjunta50660 de las tres correcciones pasó87 casos599,82s con664 huellas estables. Tras terminal74215, comparar basehash e integrar el parche consolidado sin sobrescribir trabajo; verificar afectados/runtime antes de aceptar entrega. El aislamiento Beat ya fue corregido y el ensayo62469 pasó.
3. Preparar entrega parcial revisable0097 con autoría autorizada y pruebas registradas; no implica aceptación CR-09.
4. Completar la matriz restante por derecho/finalidad y ejecutar los flujos pendientes, restauración y rendimiento; después aceptación CR-09 y CR-10→GS-01→B-F/B-B→C conforme al contrato16.

El inventario `pending` de los servicios es evidencia de alcance todavía abierto. No eliminar esas marcas para aparentar cumplimiento; deben cambiar únicamente cuando implementación y verificaciones demuestren el requisito.

## Revisión estática de autoridad en servicios anteriores

`rights_responses.issue` comprueba MFA y permisos con el objeto User recibido antes de adquirir los bloqueos del expediente. Después usa `permitted`, que comprueba conflictos pero no reconsulta sesiones/MFA/permisos. El replay devuelve la respuesta existente antes de revisar asignación y lecturas actuales. `erasure_execution.execute` conserva un patrón semejante de comprobación inicial sobre el objeto recibido. Esto contrasta con `fresh_authority` de los servicios nuevos, que recupera User y compara épocas después de bloquear.

Es un riesgo observado por inspección, no una vulnerabilidad reproducida ni evidencia de explotación. Pendiente reproducir retirada concurrente de permisos/sesión/MFA con objeto cargado antes de la espera y permisos cacheados; comprobar emisión nueva y replay, sin efectos parciales. La corrección debe distinguir permisos necesarios para progreso y ejecución, admitir los replays legítimos ya documentados y revalidar autoridad actual. No imponer execute_rights_request a una respuesta de progreso solo por reutilizar un helper. Fuente congelada durante regresión74215; después añadir reproducción y corregir si confirma el defecto, antes de aceptar CR-09.

## Resultado de las reproducciones de autoridad

Las seis variantes de emisión/replay de respuestas fallaron en63,13s sobre fuente original: permisos, sesión y MFA revocados durante bloqueo observado no impidieron devolver la respuesta. La corrección en snapshot aislado pasó28 pruebas130,48s, incluyendo esas seis y las regresiones existentes; todavía no integrada en workspace/runtime.

Las seis variantes de ejecución/replay de supresión también fallaron en75,80s sobre fuente original, devolviendo ErasureExecution tras revocar autoridad. Corrección preparada en el mismo snapshot, con batería propia95670 en ejecución. No extrapolar resultados de respuestas a supresión ni marcar ninguna corrección integrada por haber pasado en una copia.

El ensayo de purga corregido62469 pasó worker y Beat automáticos con cuatro tareas exactas, preservación de referencias y limpieza independiente verificada. Este pendiente operativo concreto queda verificado localmente; el resto de conservación/restauración permanece abierto.

Actualización conjunta:50660 terminal0,87 correctas599,82s,664huellas del segundo snapshot estables. Parche consolidado y manifiesto en evidencias/correcciones-autoridad0097.patch y -manifiesto.json; git apply --check correcto. Correcciones aún no integradas mientras74215 permanezca activa. No aceptar seguridad global ni CR-09 por este resultado parcial.

Actualización de integración: regresión original393 correcta; consolidado0099 aplicado con huellas verificadas. Autoridad ya corregida en workspace, runtime todavía anterior.13474 prueba integrada en marcha; un import desordenado pendiente de corregir tras terminal. Outbox/referencias/medios/productor incorporados, pero exportación independiente y restauración real siguen abiertas. Los estados anteriores de “no aplicado” se conservan como historial.

Entrega parcial0099: autoridad integrada y runtime actualizado,124 pruebas integradas y48 finales de recuperación/exportación correctas en ejecuciones separadas. Ruff/Django/migraciones/health correctos. Outbox, registro, exportador y comprobación operacional implementados localmente. Pendientes de restauración: aplicador tipado, destrucción recuperable tras backup viejo, aislamiento/cachés/tareas y ensayo real pg_dump/medios/RPO-RTO. El resto de la matriz CR-09 continúa abierto.
