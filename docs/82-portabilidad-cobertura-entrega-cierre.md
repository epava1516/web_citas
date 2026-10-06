# Portabilidad: vincular cobertura, entrega y respuesta final

Estado vigente: cobertura/entrega0094 y respuesta independiente/cierre0095–97 implementados y verificados localmente. Regresión original393 correcta;124 pruebas de integración posterior y48 de recuperación/exportación finales correctas en ejecuciones separadas. RuntimeDocker0099 actualizado. [Seguimiento vigente](17-seguimiento-desarrollo.md) y [resultados](evidencias/recuperacion-final0099-resultados.json). CR-09 y el contrato completo siguen abiertos. Los hallazgos/diseños/resultados posteriores se preservan como historial; las menciones antiguas de “sin implementar”, “activa” o “runtime pendiente” no prevalecen sobre este estado.


## Hallazgos comprobados en código

- `rights_responses.issue` admite únicamente `progress` y `representation_complete`; no existe respuesta final de portabilidad.
- `rights_portability_export.generate` incrementa la versión del expediente una vez. `validate_export_binding` valida selección y prueba históricas usando la versión anterior, y exige que la exportación pertenezca a la versión actual.
- El payload existente declara `partial=True`, `simulation=True` y revisión final pendiente. Su contenido se reconstruye al verificar la firma: cambiar estos literales sin versionar invalidaría exportaciones anteriores.
- La cobertura aprobada 0093 conserva lecturas originales y prueba/fuente de su versión. Su aprobación aún no se consume al generar una entrega ni autoriza cerrar el expediente.

## Integración requerida

1. Añadir consumo auditado de cobertura aprobada antes de usar su contenido. Validar autor responsable, revisor independiente actual, permisos, épocas originales, prueba/ámbito/canal, caducidad, última cobertura/selección, firma de la decisión y IDs originales de todas las lecturas. Compilar cobertura estricta nuevamente. No confiar en `complete` del borrador.
2. Vincular la exportación a esa aprobación mediante evidencia persistente protegida, con hashes del cuerpo cifrado, selección, fuente, decisión y lecturas originales. La generación parcial existente conserva su contrato; la entrega con cobertura debe tener esquema/firma versionados y validación compatible de exportaciones anteriores.
3. Separar validación histórica de ejecución de autorización actual. Después del incremento de versión, reconstruir la fuente histórica con la versión original para verificarla, sin tratar una prueba histórica como prueba actual para emitir una nueva respuesta final.
4. Preparar respuesta final específica con referencia protegida a exportación y cobertura, estado de entrega/acuse y explicación pública de alcance y exclusiones. Las notas/evidencias privadas, HMACs, valores de terceros y contactos operativos no se copian al texto público.
5. Exigir autorización y lectura vigentes de expediente/respuestas en la versión de cierre. Si requiere nueva comprobación de identidad/ámbito, iniciarla explícitamente; no alterar la prueba original ni asignar artificialmente su versión.
6. Revisión independiente de la respuesta final ligada a su texto cifrado, versión, entrega y cobertura exactas. Registrar aceptación y cierre atómicos con clave global: reintento idéntico no duplica respuesta, aviso ni transición; revocación durante una espera deniega sin efectos.
7. Preservar plazos, cronología, auditoría y acuses históricos. El cierre no debe romper la descarga autorizada de la entrega durante su vigencia: revisar expresamente su dependencia actual de `case.version`, implementando una compatibilidad histórica limitada y autorizada, sin omitir validaciones.
8. Mantener marcada cualquier identidad/comunicación sintética. Una aprobación técnica sobre fixtures no acredita revisión legal humana ni preparación real de producción.

## Evidencia de aceptación necesaria

- PostgreSQL: generación ligada a cobertura completa, denegación de parcial/rechazada/obsoleta, corrupción de firma/cuerpo/IDs, replay y caducidad.
- Concurrencia observada: generación y cierre ante cambio de permiso/sesión/MFA/prueba/ámbito/canal/fuente/aprobación, con conexiones distintas y bloqueo identificado.
- HTTP/Chromium ES/EN perfil/cuenta: preparación, lectura independiente, entrega privada y revisión/respuesta/cierre; GET sin cuerpos privados, CSRF y móvil.
- Descarga/acuse antes y después del cierre, sin ampliar acceso a sujetos ajenos ni reactivar transporte caducado.
- Inventarios no vacíos de nuevas dependencias, purga por worker/Beat reales, restauración y conservación de auditoría.
- Regresión conjunta de implementación y Docker sobre fuente estable; documentar limitaciones de CI separadamente.

No añadir la opción de cierre al formulario hasta que el recorrido completo y sus validaciones estén implementados.

## Reintentos de respuesta final y permisos actuales

La inspección de `rights_responses.issue` muestra que la recuperación de una respuesta existente por clave sucede antes de las comprobaciones de versión y lecturas completas. Ese orden no debe copiarse como autorización suficiente del nuevo cierre: una firma histórica acredita qué se emitió, pero no los permisos actuales del solicitante de un reintento.

El nuevo flujo debe cargar el actor vigente después de adquirir los bloqueos, comparar las épocas originales de sesión/MFA y comprobar permisos, asignación y ámbito antes de devolver incluso una respuesta ya registrada. Un reintento admitido debe conservar exactamente la respuesta, el aviso, la transición y sus referencias originales; no exigir una segunda transición ni crear lecturas que sustituyan las que autorizaron el cierre. La validación de entrega histórica y la autorización actual de consulta siguen siendo controles distintos.

Pruebas específicas pendientes: repetir la misma clave después del cierre y comprobar ausencia de efectos adicionales; repetirla tras revocar permiso, sesión o MFA y comprobar denegación; reutilizarla con otro actor, expediente, texto, entrega o cobertura y comprobar conflicto. Ejecutar también revocaciones durante un bloqueo PostgreSQL observado. Esta sección es una condición de implementación y aceptación futura, no una corrección ya aplicada al servicio existente.

## Escalabilidad de la puerta de revisión: pendiente comprobado por inspección

Actualización2026-10-06: el bucle descrito debajo es el diagnóstico original. Fuentec0f58fc sustituye su replay por validate_coverage_pages compartido con evidencia histórica, una fuente y lecturas subordinadas en lote. Reproducción44 reconstrucciones y regresión0,11 pruebas PG integradas y19 de bloqueos/revocaciones correctas en runs separados; [evidencia](evidencias/portabilidad-cobertura-validacion-lote0110.json), [runtime](evidencias/portabilidad-cobertura-lote-runtime0110.json). IDs/firmas/propósitos/huellas/épocas y checks finales conservados, sin lecturas de sustitución. Medición con1500 revisiones/binarios/recorrido completo todavía pendiente; no confundir esta corrección con aceptación de volumen. La cola vigente sigue en17.

`require_complete_reads` recorre cada lectura y llama `inspect_page`; esa función consume una inspección de selección y reconstruye `source_copy` antes y después. Con P páginas y S tamaño de fuente, la revalidación repite trabajo sobre la fuente aproximadamente P veces. Es una inferencia del código, no una medición de latencia ni una prueba de carga. La batería de volumen existente contiene 1500 revisiones, pero todavía no pasa por esta puerta de cobertura.

Antes de aceptar grandes historiales, validar todos los registros originales bajo una única fuente bloqueada y una autorización fresca, reutilizando la fuente y las estructuras preparadas dentro de la transacción. La refactorización debe verificar cada firma original, propósito, page_digest, prueba, actor y épocas sin crear lecturas de sustitución. Conservar la revalidación de autoridad/fuente al final. No resolverlo aumentando indiscriminadamente el timeout Gunicorn actual de45s, omitiendo páginas o aceptando únicamente contadores.

Añadir mediciones PostgreSQL con historial grande y binarios, número de consultas, duración y memoria de la revisión completa. Documentar recursos y distinguir tiempo instrumentado de latenciaHTTP. Si se decide procesar en worker, el trabajo debe volver a comprobar autoridad/fuente/prueba al ejecutar y antes de registrar resultado, con estado visible y sin aprobación anticipada. Esta optimización permanece pendiente; las pruebas correctas de expedientes pequeños no acreditan el rendimiento de historiales grandes.

## Consumo auditado inicial: verificación pendiente

`rights_portability_coverage_use.consume_approved_coverage` registra coverage_use antes de descifrar cobertura, reproduce la decisión aprobada con su clave y lecturas originales, comprueba épocas actuales del revisor independiente y del autor y consume la selección aprobada mediante auditoría subordinada. Recompila estrictamente y revalida fuente/prueba/autoridad antes de retornar. No genera exportación ni respuesta, ni cambia versión/plazos/estado. Pruebas PostgreSQL perfil/cuenta46621 terminal0:2 correctas74,22s, auditoría/replay/IDs originales/corrupción/denegación tras revocación verificados. Evidencia `evidencias/portabilidad-cobertura-consumo.json`. Carreras observadas de consumo93183 terminal0:8 correctas130,96s,24 deseleccionadas; reintento/revocaciones/corrupción/caducidad durante espera comprobados para cuenta. Variantes de revocación del autor21071 terminal0:3 correctas61,73s,32 deseleccionadas; permisos/sesión/MFA del autor deniegan ambos consumidores tras bloqueo observado. Evidencias separadas; no sumar las ejecuciones como una regresión conjunta. Runtime, entrega y cierre siguen pendientes. Rendimiento de historiales grandes y carreras observadas siguen pendientes.

## Preparación de validación histórica de exportaciones

Se separa `rights_portability_coverage_page.coverage_page`: reconstruye el mismo resultado escalar/binario y resumen a partir de una fuente, evaluación, selección y cobertura ya validadas. `inspect_page` conserva autorización, auditoría previa al descifrado, revalidación final y comparación del registro page_digest; delega únicamente la proyección de la página. Sesión29043 terminal0:6 pruebas correctas113,32s de inspección/consumo perfil/cuenta. Evidencia `evidencias/portabilidad-cobertura-reconstruccion-paginas.json`.

Esta separación prepara la comprobación de todas las firmas/huellas originales contra una única fuente para la vinculación histórica de exportaciones. Todavía no sustituye el bucle actual de require_complete_reads, no acredita mejora medida de rendimiento ni permite descargar una exportación tras cerrar el expediente. La integración histórica deberá comprobar cada propósito, actor, versión, épocas, prueba, cobertura y página, además de su firma y page_digest, y mantener la autorización actual de entrega separada.

## Validador histórico inicial: pendiente de prueba

`rights_portability_coverage_evidence.validate_approved_coverage` recibe expediente con versión original y fuente ya bloqueada/auditada. Revalida evaluación y selección aprobadas, cobertura firmada vigente, aprobación independiente y sus épocas actuales; comprueba IDs originales en el orden exacto del censo, auditoría subordinada de selección, propósito/firma de cada lectura y page_digest reconstruido, y firma/resultado de la aprobación. No inicia nueva autorización de identidad ni sustituye lecturas. Requiere transacción y autorización/auditoría previa del llamador; todavía no conectado a descarga/exportación. Sesión36140 terminal0:2 pruebas perfil/cuenta correctas71,59s; reconstrucción equivalente y corrupción de huella denegada. Evidencia `evidencias/portabilidad-cobertura-evidencia-historica.json`. No acredita cierre ni rendimiento de grandes historiales.

## Exportación cubierta0094: integración en verificación

El binding existente incorpora FK protegidas opcionales a aprobación de cobertura y acción de consumo, junto a hashes de cobertura/ciphertext/decisión/IDs originales. Exportaciones anteriores conservan campos vacíos y firma/payload originales. Generación con coverage_review_id consume y verifica aprobación antes de generar; exige coincidencia de selección, acota caducidad y firma los nuevos vínculos. Payload versionado covered-portability-v1 declara cobertura completa de selección/exclusiones y respuesta final pendiente; mantiene simulation=True. No incluye fundamentos privados ni cierra expediente.

Descarga reconstruye y valida evidencia histórica de cobertura y acción de consumo antes de aceptar firma/transporte. Replay no admite quitar o cambiar aprobación. Inventarios perfil/cuenta incluyen las nuevas referencias/huellas. Migración0094 generada, makemigrations limpio; aún no aplicada al runtimeDocker. Sesión13860 terminal0:2 pruebas perfil/cuenta correctas84,66s; generación/replay/descarga y corrupción del vínculo verificadas. Evidencia `evidencias/portabilidad-exportacion-cubierta.json`. Descarga tras cierre, autorización de cierre, binarios incluidos, inventarios no vacíos/races/frontend y regresión común pendientes.

## Interfaz de entrega cubierta: en verificación

El formulario privado permite seleccionar cobertura aprobada del mismo autor/expediente. GET enumera solo IDs/versiones y no descifra cuerpos ni crea auditoría de lectura. POST pasa approval ID al servicio; este comprueba selección, última cobertura y evidencias actuales. Se conserva copia parcial explícita sin cobertura. La pantalla explica ambos alcances y que la copia no emite respuesta final ni cierra. Queryset conserva referencias históricas vivas para permitir replay; la pertenencia a la versión actual se decide en el servicio. Sesión19709 terminal0:2 pruebas perfil/cuenta correctas86,58s,2 deseleccionadas. GET privado, creación/replay HTTP, descarga, CSRF y anonimato comprobados; evidencia `evidencias/portabilidad-exportacion-cubierta-http.json`. Recorrido móvil aprobación→entrega11353 terminal1:4 fallos110,54s, SynchronousOnlyOperation en la prueba al consultar Django dentro de Playwright. Sesión de autor preparada antes del navegador y cobertura elegida por label real del formulario; código funcional sin cambios. Repetición Chromium ES/EN perfil/cuenta52877 terminal0:4 correctas133,26s. Recorrido aprobación→entrega cubierta y ancho390 comprobados; evidencia `evidencias/portabilidad-exportacion-cubierta-movil.json`.

## Inventarios y corrupción de nuevos vínculos: en verificación

Sesión47086 comprueba entradas no vacías de RightsExportPortabilityBinding para perfil/cuenta y sensibilidad de state_digest a cada uno de los seis campos nuevos0094. Al alterar referencia de aprobación/consumo o huella de cobertura/ciphertext/decisión/IDs, la descarga debe devolver404 y revertir su nuevo RightsExportDownload. Restaurar los campos debe restablecer huella y descarga. No se usa descifrado de cobertura para el inventario. Sesión47086 terminal0:2 pruebas perfil/cuenta correctas96,61s,2 deseleccionadas. Seis alteraciones por sujeto cambian inventario y deniegan descarga sin acuse nuevo; restauración de campos devuelve huella/descarga. Evidencia `evidencias/portabilidad-exportacion-cubierta-inventarios.json`; no acredita restauración de backups ni cierre.

## Imagen incluida en entrega cubierta: en verificación

Se prepara una nueva selección binaria con inspección real de bytes por autor, lectura binaria independiente y aprobación de selección antes de cubrir campos/omisiones y aprobar cobertura completa. Sesión89692 verifica generación por servicio y formularioHTTP, JSON privado, descarga individual SHA256 y paquete, más integridad/inventarios existentes. Fuente y fotos sintéticas; binarios se leen realmente. Sesión89692 terminal0:2 correctas114,29s,4 deseleccionadas. Imagen incluida, SHA256, paquete y corrupción de vínculos comprobados; evidencia `evidencias/portabilidad-exportacion-cubierta-binarios.json`. No confundir los casos anteriores de todas las imágenes excluidas con esta variante incluida. Runtime0094 en preparación; carreras de exportación cubierta y cierre siguen pendientes.

## Runtime0094 y concurrencia cubierta

Build84773/migrate38909/recreate32842 terminal0. Migración0094 aplicada; check/migrate-check/makemigrations limpios y health18080 correcto2749 terminal0. Doce hashes coinciden host/app/worker/Beat y UID10001 en los tres servicios92171 terminal0. Evidencia `evidencias/portabilidad-exportacion-cubierta-runtime0094.json`.

Sesión76104 verifica32 carreras de generación/descarga × perfil/cuenta × reintento/prueba/fuente/ciphertext de cobertura/permisos y sesión del revisor/canal/caducidad. Se observan pg_blocking_pids de dos conexiones distintas contra un tercer holder antes de mutar. Sesión76104 terminal1:30 correctas y2 fallidas565,68s. Los dos fallos corresponden a permiso del revisor revocado durante descarga: acceso denegado403, contrato exige404. Se convierte PermissionDenied a Http404 en download, dentro de la transacción para conservar rollback del acuse. Repetición93397 terminal0:4 correctas97,25s,28 deseleccionadas; generación/descarga perfil/cuenta corregidas. Evidencia `evidencias/portabilidad-exportacion-cubierta-permiso-carreras.json`. Regresión conjunta0094 sesión48910 en marcha, fuente congelada; actualización Docker60655 en curso. Runtime0094 previo no acredita esta corrección. Sin cierre de expediente ni aceptación común.

## Estado de entrega y acuses: límites del modelo actual

La inspección de modelos confirma que RightsExportDownload registra clave, exportación, imagen/parte opcional, actor opcional y fecha. Su transacción confirma una respuesta de descarga autorizada del servidor; no acredita que la persona haya leído, reconstruido o aceptado todos los paquetes. No tiene channel_digest propio ni una confirmación explícita de recepción de exportación. No convertir un recuento de descargas en acuse completo.

RightsResponseAcknowledgement acredita únicamente la confirmación explícita de una respuesta a través del canal del expediente; no identifica la exportación ni sus partes. La revisión final deberá distinguir copia disponible, descargas autorizadas, confirmación explícita de recepción y aviso simulado/desactivado. Si el flujo incorpora confirmación de exportación, ligarla a exportación y canal exactos, conservar las referencias y verificar cada parte requerida; no reutilizar automáticamente el acuse de respuesta como acuse de copia.

La disponibilidad/entrega necesaria para emitir respuesta y cerrar deberá quedar definida explícitamente en el servicio y en su interfaz, sin condicionar artificialmente el cierre a una lectura supuesta ni dar por real el transporte simulado. Las pruebas deben demostrar esos estados y los límites de su evidencia. Esta decisión de implementación sigue pendiente de ejecutar; no acredita cumplimiento jurídico ni envío real.


## Transición de autorización después de exportar: requisito del vínculo final

Inspección de rights_verification.initiate/receive_event: iniciar una nueva prueba incrementa case.version una vez y aceptar su resultado independiente la incrementa de nuevo. La prueba nueva termina ligada a esa versión actual. La exportación0094 conserva la prueba anterior y su case_version posterior a generar; por tanto una nueva comprobación bloquea la descarga actual incluso antes del cierre. No actualizar export.case_version ni la prueba original para hacerlas pasar como actuales.

La preparación final debe persistir referencias protegidas a exportación, cobertura y nueva prueba actual, junto a versiones de expediente/respuestas, canal, actor y épocas. La validación de la entrega anterior puede reconstruir un snapshot de expediente con export.case_version para verificar su evidencia histórica; esto solo es admisible dentro de una autorización actual auditada y no concede descarga por sí mismo. La compatibilidad posterior al cierre deberá apoyarse en la respuesta final aprobada y su vínculo exacto, y seguir comprobando caducidad, ámbito, canal, fuente, prueba original y autoridades de selección/cobertura. No basta aceptar resolved ni permitir cualquier incremento de versión.

La aprobación final debe comprobar la nueva prueba vigente y lecturas actuales de expediente/respuestas, revisar el texto y las referencias exactas con un actor independiente, y revalidar todos los vínculos bajo los bloqueos canónicos antes de emitir respuesta/aviso/cierre atómicos. El inventario y la retención deben incorporar esa dependencia. Estas condiciones siguen pendientes de implementación y verificación.

Validador de texto público compartido rights_response_text integrado en respuestas existentes:73973 terminal0,22 correctas92,08s, incluye tipos inválidos, confirmación booleana, contactos/enlaces y regresión PostgreSQL de respuestas/acuses. No concede revisión legal, autoridad de cierre ni protección automática contra cualquier dato de tercero escrito en prosa; la revisión independiente sigue requerida.


## Preparación y revisión de respuesta final0095–96: estado técnico vigente

RightsPortabilityResponseDraft conserva FK protegidas a exportación/cobertura/nueva prueba, versiones de expediente/respuestas, épocas del autor, huellas y texto cifrado con caducidad acotada. prepare exige comprobación nueva posterior a la exportación y lecturas actuales, permiso responder/ejecutar/asignación/ámbito, registra portability_draft antes de reconstruir entrega histórica y conserva estado/plazos. Reintentos validan texto y referencias exactos. Texto dañado genera ValidationError controlado.

final_draft_read exige actor independiente con permisos y épocas vigentes, prueba actual y lecturas completas; audita antes del descifrado y revalida preparación original usando las épocas del autor. RightsPortabilityResponseReview protege esa lectura original, decisión y huellas exactas; record revalida lectura y preparación, controla reintentos/corrupción y no emite respuesta ni cierra. Inventarios perfil/cuenta incorporan ambas dependencias sin exponer texto/ciphertext. Tarea de purga configurada60s/lote100 limpia solo texto caducado y conserva metadatos; comprobada mediante invocación directa PostgreSQL, todavía no worker/Beat real.

Pantallas preparación/revisión y descubrimiento paginado desde expediente implementados. Verificaciones HTTP separadas y Chromium90513:4 correctas130,50s ESEN×perfil/cuenta390px; autor prepara, revisor descubre/consulta/aprueba y GET retira texto, sin overflow ni modificación de plazos. Identidad/sesiones/hechos sintéticos, navegador real. Evidencias respuesta correspondientes en docs/evidencias. No acredita rechazo completo, concurrencia observada, emisión/cierre, descarga después de cierre, runtime0095–96, regresión íntegra ni revisión legal real.

## Cierre0097: implementación y verificación parcial vigente

El cierre ya está implementado mediante RightsPortabilityClosure, con referencias protegidas a acción, respuesta y aprobación independiente. Reconstruye el snapshot exacto del borrador y revalida firmas, fuente, pruebas, canal y épocas originales frente a la autoridad actual. Emisión, aviso en cola y resolución ocurren en una transacción; conserva fechas y plazos. La validación histórica no concede autoridad por sí sola y ninguna decisión rechazada permite cerrar.

La descarga posterior solo admite la exportación referenciada por ese cierre, con versiones y canal exactos. Después de auditar el intento, valida el cierre y la evidencia original de exportación; no modifica el payload firmado ni acepta cualquier expediente resolved. Descargar no confirma automáticamente recepción de la respuesta. El aviso en cola no es un envío real.

Verificación separada: batería67236,5 correctas141,74s PostgreSQL/HTTP aprobado-rechazado×perfil-cuenta, inventarios no vacíos y sensibilidad/restauración de huella, descarga JSON posterior y frontera histórica50→51. Chromium móvil,4 correctas139,04s ESEN×perfil-cuenta hasta cierre y descarga. Ambas usan datos e identidades sintéticos; no sumar como suite única ni extrapolar a proveedores reales. Carrera de cierre2766 actualmente activa con12 variantes de cuenta; resultado pendiente. Binarios posteriores al cierre, runtime0095–97, worker/Beat y regresión común siguen pendientes. Este apartado actualiza el estado de implementación descrito anteriormente, sin aceptar CR-09 íntegro.


## Actualización operativa0097 y aceptación pendiente

Cierre observado2766 terminal0:12 carreras cuenta correctas227,04s; entrega binaria63942 terminal0:1correcta63,35s, JSON/WebP/ZIP y corrupción con rollback de auditoría. Docker0095–97 aplicado, trece hashes host/app/worker/Beat iguales, UID10001 y health/check/migraciones correctos. Purga worker/Beat62469 terminal0: cuatro tareas exactas, caducado/vigente, replay y referencias conservadas; recursos aislados eliminados y ausencia verificada. Estos resultados actualizan los pendientes operativos descritos antes; son ejecuciones separadas y no una suite única.

Regresión393 original74215 aún activa. Se confirmaron por reproducciones independientes defectos de autoridad en respuestas antiguas, ejecución de supresión y acciones generales. Correcciones en snapshots con resultados28/48/27 y permisos específicos30 correctos por separado; batería conjunta50660 activa. Ninguna corrección aplicada al workspace/runtime todavía. Los recorridos0097 correctos no acreditan seguridad global, aceptación CR-09 ni preparación de producción. Estado vigente y evidencias en seguimiento17/auditoría83.


## Diagnóstico de primera página con1500 revisiones — 2026-10-06

Ensayo5bc4f8f sobre aplicaciónc0f58fc: source_copy real de PostgreSQL9893757bytes, primera inspect_page nativa con764 consultas/11,529s/pico Python41651227bytes instrumentados;1 prueba correcta74,44s. [Evidencia](evidencias/portabilidad-cobertura-primera-pagina-grande0110.json). Preparación conserva hechos/identidad sintéticos explícitos y la lectura auditada; no hay simulación de DB ni equivalencia a proveedor/revisión jurídica. No contiene aprobación completa, cierre o descarga de ese expediente. El coste observado dirige la optimización de preparación del origen; no usar el tiempo bajo tracemalloc como p95 HTTP ni el pico Python como RSS. Revisión/entrega/cierre/binarios grandes y capacidad siguen pendientes; siguiente paso vigente en17.
