# Restauración sin reintroducir datos retirados o suprimidos

Estado: implementación parcial local; reaplicación de efectos y ensayo de restauración completa pendientes. Fecha:2026-10-06. Requisitos: OP-007/OP-008, seguridad11 y contrato16. No sustituye políticas de conservación definitivas ni acredita backups reales.

## Problema y fuentes existentes

Una copia anterior a una supresión puede recuperar campos de cuenta, anuncios, originales, derivados, sesiones y autorizaciones ya retirados. ErasureExecution conserva plan/acción/prueba/ámbito y resultado cifrado; MediaErasure conserva ejecución/Blob/rutas cifradas/estado. Esas filas dentro del mismo backup antiguo no bastan para conocer decisiones posteriores. No interpretar jobs completados del backup como prueba de que los archivos recién restaurados siguen eliminados.

La reconciliación exige evidencia posterior al punto restaurado, almacenada fuera de ese conjunto de copias. Reutilizar UUID estables y decisiones ejecutadas; no derivar una prohibición del estado mutable de un anuncio ni de un plan preparado sin ejecución. Diferenciar retirada, supresión, rectificación y rehabilitación por recurso y ámbito.

## Registro externo y autoridad

Preparar un registro de eventos versionado, firmado y cifrado fuera del backup de negocio, con secuencia y comprobación de integridad. Datos mínimos: ID de evento/operación y ejecución, ámbito tipado, referencias estables de sujeto/recurso, versión y acciones ejecutadas por finalidad. No incluir texto de solicitudes, teléfonos, correos, motivos o documentos. Las referencias siguen siendo datos privados: acceso reservado, retención definida y claves disponibles para recuperación.

Registrar un outbox durable en la transacción de la ejecución. La copia independiente recibe eventos mediante exportación idempotente y registra el último número confirmado. No prometer atomicidad entre PostgreSQL y archivos externos: si el outbox no se ha exportado, el punto de reconciliación no está completo y la recuperación no puede abrir exposición. Guardar checkpoints verificables fuera del backup para detectar truncación, eventos omitidos o retroceso; una firma válida del último evento disponible no demuestra que no falten eventos posteriores.

Adaptador local: artefacto reservado en volumen/directorio independiente para ensayos sintéticos. Almacenamiento externo real pendiente de configuración del operador. No instalar proveedor ni declarar la copia local como respaldo independiente ante pérdida del servidor.

## Puerta de recuperación

1. Restaurar PostgreSQL y medios en namespace aislado, con aplicación pública y worker/Beat de negocio detenidos; entregas externas desactivadas.
2. Verificar manifest de backup, claves, versiones y checkpoint externo. Falta de integridad/clave/checkpoint bloquea reconciliación y apertura, con error sin datos privados.
3. Reconstruir la lista de operaciones posteriores al punto restaurado desde el registro independiente. Comparar ámbito, orden y evidencia ejecutada; no reproducir formularios originales ni crear nuevas aprobaciones.
4. Reaplicar efectos por recurso/finalidad con idempotencia: anonimización/borrado de campos propios, retirada de exposición y revocación de sesiones/autorizaciones. Conservar recursos compartidos autorizados de terceros. Una rehabilitación válida posterior prevalece solo en su ámbito exacto.
5. Comprobar originales y derivados realmente presentes. Reencolar destrucción física en la cola aislada aun cuando el backup contenga un job antiguo completado; referencias y auditoría de recuperación deben identificar esta nueva instancia sin reescribir la ejecución original.
6. Invalidar índices/cachés/derivados públicos y no restaurar colas o sesiones antiguas como autoridad. Recalcular tareas pendientes desde estados reconciliados, sin reenviar avisos ni reactivar publicaciones automáticamente.
7. Emitir resultado reservado con secuencia/checkpoint aplicado, operaciones/reintentos y pendientes. Solo permitir habilitación cuando no existan recursos expuestos sujetos a retirada pendiente; fallos físicos deben conservar bloqueo y trabajo recuperable.

No confiar solo en fecha local: usar IDs y secuencia verificable. No borrar globalmente un Blob compartido por una retirada acotada. La política de destrucción de evidencia y del registro de recuperación requiere definición específica; no prometer conservación indefinida.

## Ensayo requerido

Crear datos sintéticos publicados y compartidos, tomar backup real PostgreSQL/medios, ejecutar retiradas/supresiones/revocaciones reales del servicio y exportar el registro posterior. Restaurar la copia antigua en otra base y otro directorio; demostrar que antes de reconciliar contiene el dato viejo y que permanece inaccesible. Después demostrar ausencia de exposición/archivos propios retirados, terceros legítimos conservados, sesiones anteriores rechazadas y replay sin duplicación. Probar eventos omitidos/firma alterada/checkpoint atrasado/clave incorrecta, fallo físico y reintento, decisiones posteriores sobre el mismo recurso y medios compartidos.

Medir RPO/RTO y recursos del ensayo; objetivos del contrato funcional son RPO1h/RTO8h, todavía sin acreditación. La medición local no prueba recuperabilidad de proveedor ni disponibilidad de claves fuera del servidor.

## Dependencias pendientes

Modelo/outbox/registro/checkpoints, exportador seguro, reconciliación idempotente por finalidad, puerta de recuperación, pruebas PostgreSQL/archivos reales y documentación operativa. Inventarios deben incluir estas dependencias al introducirlas. Implementar después de finalizar la regresión0097, manteniendo el alcance completo CR-09 y las fases restantes.

## Comprobación inicial del registro

Implementado `scripts/recovery_ledger.py`: cuerpos cifrados con Fernet, firma HMAC-SHA256 con clave separada, secuencia encadenada y checkpoints. El verificador comprueba la cadena completa y el checkpoint esperado antes de devolver contenido descifrado. El checkpoint esperado debe obtenerse de una autoridad independiente del backup y del propio paquete; este módulo no implementa todavía esa custodia. Persistir el registro codificado para que un reintento no genere otro ciphertext.

Dieciocho pruebas sintéticas verifican ida/vuelta, sufijo posterior a un checkpoint, alteración, omisión, truncación, reordenación, duplicación, claves incorrectas y retroceso. [Evidencia](evidencias/restauracion-registro-codec.json). No son un ensayo PostgreSQL ni acreditan outbox, reconciliación, eliminación física o recuperación completa. Los archivos nuevos no forman parte de la regresión393 ya recolectada; sus fuentes existentes permanecen intactas salvo la excepción documentada del probe.

Se rechaza reutilizar la clave de cifrado como clave de firma incluso tras decodificarla. Límite agregado de paquete: 16 MiB, además de 64 KiB por registro y 10.000 eventos. Se prueban también registros malformados con firma válida y que un paquete incompleto se rechaza antes de cualquier descifrado. Estos límites requieren paginación con checkpoints independientes para historiales superiores; no truncar eventos para ajustar un paquete.

## Recibo transaccional en copia aislada

Preparado modelo `RecoveryOutbox` y migración0098, ligado uno a uno a la ejecución y protegido contra borrado en cascada. La ejecución crea en su misma transacción un recibo cifrado minimizado con UUID, ámbito, referencias y finalidades ejecutadas/pendientes. PostgreSQL aislado: una prueba pasó en38,86s, demostrando rollback de supresión ante fallo al insertar el recibo y replay sin duplicar evento. [Evidencia y límites](evidencias/recuperacion-outbox0098.json), [parche preparado](evidencias/recuperacion-outbox0098.patch).

No aplicado a la aplicación principal: depende primero de las correcciones de autoridad0097 y del fin de la regresión original. Este recibo todavía no contiene todos los efectos por recurso necesarios para reconciliar una restauración; no usarlo como autorización suficiente. Faltan registro en inventarios, exportación independiente, custodia de checkpoints y ensayo real PostgreSQL/medios.

Inventarios incorporados en la copia aislada: el perfil registra eventos asociados a su persona; la cuenta incluye los propios y de personas vinculadas, excluyendo el mismo procedimiento para no invalidar su preparación. Proyección opaca: no descifra eventos, pero su huella detecta alteraciones del ciphertext. Dos pruebas PostgreSQL correctas en46,98s verifican rollback/replay, exclusión propia, visibilidad desde otro procedimiento y censo65. [Evidencia](evidencias/recuperacion-inventarios0098.json). Dos intentos anteriores fallaron por preparación incorrecta del test (transacción ausente y sujeto ya suprimido); ambos quedan registrados. No se relajaron esas restricciones. El caso con inventario de perfil no vacío todavía no está probado. Parche0098 actualizado; requiere aplicar primero autoridad0097.

Verificación adicional de perfil y cuenta: dos pruebas correctas43,60s en copia aislada, incluyendo recibo de perfil no vacío, proyección opaca sensible al ciphertext y exclusión de otra persona. [Evidencia](evidencias/recuperacion-perfil0098.json). No demuestra destrucción de medios compartidos. Iniciada regresión ampliada de supresión/ámbitos/revocaciones en la misma copia; fuente congelada en `/tmp/recovery-scope-regression0098-source.json`, resultado pendiente.

## Referencias concretas en segunda copia aislada

Snapshot `/tmp/web-modelos-recovery-effects0098` añade captura de IDs antes de ejecutar efectos: tokens/códigos/favoritos del sujeto, desafíos/invitaciones del perfil, anuncios/revisiones, exportaciones vigentes y fotos con distinción de Blob compartido. Conserva versiones mínimas finales de sesión, MFA, derechos y gestor, y operación de medios. Las referencias permanecen cifradas. Dos pruebas correctas47,96s comprueban cuenta/perfil, tokens, exportación exacta, favorito propio y conservación del favorito ajeno. [Evidencia](evidencias/recuperacion-referencias0098.json), [parche incremental sobre outbox0098](evidencias/recuperacion-referencias0098.patch).

La regresión ampliada63573 sigue ejecutándose sobre la primera copia y no acredita estas referencias nuevas. Primera invocación del test nuevo se lanzó desde cwd incorrecto y no ejecutó pruebas; corregida posteriormente, resultado terminal correcto. Falta reconciliador tipado, referencias/rutas de destrucción física y ensayo de medios compartidos, exportación/custodia independiente y restauración real. No usar este esquema como reconciliación completa ni restaurar automáticamente un permiso de representación.

Referencias de medios preparadas en segunda copia: cada trabajo creado por la ejecución aporta UUID, Blob y rutas originales/derivadas al recibo cifrado, antes de que la purga física borre sus rutas transitorias. El recibo sigue siendo dato privado sujeto a conservación definida, acceso reservado y eventual destrucción; no conservar rutas indefinidamente. Prueba55319 en marcha (`/tmp/recovery-media0098.xml/log`) con destrucción física y regresiones de medios; fuente congelada en `/tmp/recovery-media0098-source.json`. [Preparación y límites](evidencias/recuperacion-medios0098-preparacion.json). No acredita todavía restauración desde backup antiguo.

Resultado medios55319 terminal0: ocho pruebas correctas94,36s, fuente sin cambios. Comprueban borrado físico de originales/derivados sintéticos, referencias cifradas persistentes tras purgar el trabajo, rechazo de Blob/ruta compartida, fallo físico/reintento y ausencia de resurrección por procesamiento concurrente. [Resultado](evidencias/recuperacion-medios0098-resultados.json). Estas comprobaciones no restauran un backup y no prueban aún un registro externo.

Regresión ampliada de la segunda copia80899 iniciada: supresión por ámbitos y revocaciones además del registro/referencias/medios; resultado pendiente en `/tmp/recovery-effects-regression0098.xml/log`. Fuente estable hasta terminal. La batería63573 anterior no sustituye este resultado.

Primera copia63573 terminal0: 42 pruebas correctas; manifiesto sin cambios. [Evidencia](evidencias/recuperacion-recibo-regresion0098.json). El resultado cubre recibo/inventarios y supresión por ámbitos/revocaciones, pero no las referencias concretas y rutas de la segunda copia.80899 permanece pendiente para esas modificaciones.

## Productor persistente de registros firmados0099

Tercera copia aislada `/tmp/web-modelos-recovery-ledger0099`: migración0099 añade secuencia única y registro codificado al outbox, más estado global de cadena. `prepare_batch` serializa productores mediante advisory lock transaccional PostgreSQL, valida la cadena previa y sus vínculos al evento/ejecución, firma y cifra registros nuevos una sola vez y guarda estado/registros en la misma transacción. Inventarios incluyen la metadata codificada y detectan alteraciones sin descifrarla. El estado global contiene UUID/secuencia/huella de infraestructura; no es un permiso de acceso a los eventos privados.

Una prueba PostgreSQL correcta40,73s comprueba dos productores concurrentes, replay idéntico, clave incorrecta, alteración y conservación del estado tras rechazo. No observa `pg_blocking_pids`; no equiparar este ensayo a las carreras instrumentadas anteriores. [Evidencia](evidencias/recuperacion-productor0099.json), [parche incremental](evidencias/recuperacion-productor0099.patch).

El productor deja `exported_at` vacío: todavía no existe confirmación de almacenamiento independiente. Su checkpoint es interno, insuficiente para detectar que el backup y su propia cadena han retrocedido juntos. Faltan configuración explícita/custodia de claves externas, exportador durable y autoridad independiente de checkpoints, reconciliador y ensayo real de restauración. Antes de producción, definir paginación que respete límites de verificación; la generación falla antes de persistir un paquete que exceda dichos límites. No integrarlo sobre una fuente distinta sin comprobar manifiestos y dependencias0097→0098→0099.

## Preparación consolidada revisable

[Parche único0099](evidencias/recuperacion-consolidada0099.patch) y [manifiesto](evidencias/recuperacion-consolidada0099-manifiesto.json) reúnen correcciones de autoridad, outbox/inventarios, referencias de recursos/medios y productor. `git apply --check` correcto sobre workspace; no aplicado. Cinco pruebas correctas71,63s sobre la tercera copia tras normalizar imports/formato, con huellas estables. Ruff, Django check y ausencia de migraciones pendientes correctos. [Resultados](evidencias/recuperacion-consolidada0099-resultados.json). La verificación no es regresión completa de autoridad ni restauración. Integrar tras terminal de la regresión original y comparar hashes; después verificar afectados/runtime en la versión integrada. Los parches incrementales anteriores se preservan como historia, no aplicarlos además del consolidado.

Regresión80899 terminal0: 43 pruebas correctas, huellas de la segunda copia estables. [Evidencia](evidencias/recuperacion-referencias-regresion0098.json). Incluye referencias/medios y supresión por ámbitos/revocaciones, pero no productor0099 ni restauración desde copia antigua.

## Adaptador local de registro/checkpoint

Implementado `scripts/recovery_store.py`, separado del productor aún aislado. Requiere directorios existentes0700, separados para registros y checkpoint; archivos0600, rechazo de enlaces simbólicos, publicación mediante archivo temporal/fsync y bloqueo POSIX del checkpoint. Firma del checkpoint separada por contexto de firma respecto a los eventos. Valida secuencia/registro antes de avanzar; si se interrumpe entre registro y checkpoint, un reintento idéntico recupera la operación sin sobrescribir un registro incompatible. No inicializar automáticamente ante checkpoint ausente: la inicialización exige genesis explícito.

Veintiséis pruebas correctas (adaptador más codec), incluyendo persistencia/reapertura, concurrencia/replay, interrupción, omisión/alteración, permisos/enlaces y límite agregado durante carga. [Evidencia](evidencias/recuperacion-almacen-local.json). El locking es POSIX local, no distribuido. Directorios en el mismo host no acreditan copia externa. No se conecta aún al outbox ni actualiza `exported_at`; no aplica efectos de restauración. Los archivos nuevos no están incluidos en la regresión393 ya recolectada.

Integración consolidada0099 aplicada al workspace tras resultado original393 y comparación de hashes. Regresión integrada13474 en marcha; runtime sin actualización todavía. Ruff global detectó un orden de imports pendiente en erasure_execution, mientras Django/migraciones pasan. Mantener fuente estable hasta terminal y corregir después; no interpretar aplicación del parche como aceptación de restauración.

## Exportador conectado en cuarta copia aislada

`recovery_ledger_export.export_batch` conecta productor y almacén. Requiere invocación fuera de una transacción de negocio, prepara registros en transacción comprometida, serializa exportadores PostgreSQL y guarda cada registro/checkpoint durable antes de actualizar `exported_at`. No prometer atomicidad entre sistemas: una escritura de archivos puede sobrevivir al rollback de la confirmación de base. `RecoveryStore.confirm` valida un registro anterior contra el checkpoint actual para recuperar ese intervalo sin duplicar evento. Checkpoint ausente o cadena de negocio retrocedida/incompatible bloquean confirmación; no reinicializar autoridad automáticamente.

Nueve pruebas correctas38,04s en cuarta copia con PostgreSQL real y archivos sintéticos, incluyendo ejecución genuina del servicio, fallo después de commit de archivo antes de confirmación DB, reintento, replay, checkpoint ausente y retroceso de base. [Evidencia](evidencias/recuperacion-exportador0099.json), [parche preparado](evidencias/recuperacion-exportador0099.patch). No aplicado mientras13474 prueba el workspace estable. No acredita almacenamiento off-host ni ensayo pg_dump/restore completo.

## Recibos tipados antes de reconciliar

`scripts/recovery_receipts.py` valida esquema, finalidades ejecutadas/pendientes, ámbito del sujeto, referencias y versiones mínimas; rechaza campos inesperados, IDs malformados, booleanos usados como versiones, referencias duplicadas y rutas absolutas/con traversal. Un Blob compartido no puede figurar en un trabajo físico de borrado. La validación respeta supresión parcial de medios con revisión exclusiva pendiente y el caso de copia transitoria de cuenta sin revocación de sesión. No sustituye verificación de propiedad contra los datos restaurados.

Dieciséis pruebas sintéticas correctas; separadamente dos pruebas PostgreSQL correctas47,64s aceptan recibos producidos realmente por servicios de cuenta/medios. [Evidencia](evidencias/recuperacion-recibos-tipados.json). No es una suite única de18 ni aplica aún recuperación. Invocación inicial de servicio con cwd incorrecto no ejecutó pruebas, corregida antes del resultado final. [Parche exportador actualizado](evidencias/recuperacion-exportador-tipado0099.patch) preparado sin aplicar; reemplaza la preparación anterior del exportador, no aplicar ambos. Workspace bajo13474 sin alteraciones de sus fuentes importadas.

## Comprobación de propiedad previa a efectos

`recovery_ownership.validate_ownership` exige transacción, valida recibo tipado y comprueba referencias existentes contra sujeto/persona: tokens/códigos/favoritos, desafíos/invitaciones, anuncios/revisiones, exportaciones y fotografías. Protege Blob/rutas compartidos y detecta vínculos de foto/Blob incompatibles. No muta datos ni archivos y no habilita exposición.

Dos pruebas PostgreSQL correctas44,77s verifican referencia legítima de servicio, favorita ajena rechazada sin alteración, archivo compartido bloqueado sin borrar y exigencia de transacción. [Evidencia](evidencias/recuperacion-propiedad0099.json). Se usa base sintética actual, todavía no restaurada con pg_dump. Faltan comprobación durante restauración real, aplicador de efectos, trabajos físicos recuperables y puerta operativa de aislamiento. Nuevos archivos no seleccionados/importados por13474; sus fuentes originales siguen intactas.

Entrega integrada0099: regresión13474 terminal124 correctas814,02s; exportador aplicado y estilo normalizado después. Verificación final48 correctas73,11s y runtimeDocker0099 con16 huellas/UID10001/health/migraciones correctos. [Resultado](evidencias/recuperacion-final0099-resultados.json). Operación de comprobación documentada en [docs85](85-operacion-registro-recuperacion.md). Restauración completa pendiente: no hay aún reaplicación de efectos ni ensayo pg_dump/medios.
