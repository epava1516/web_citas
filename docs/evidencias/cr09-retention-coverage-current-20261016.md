# Conservación: conciliación finita de tareas y efectos

La auditoría parte de las18 tareas del manifiesto efectivo del ensayo Beat real3978e752, no de todos los nombres parecidos del repositorio. Se conserva el [índice anterior](cr09-retention-policy-crosswalk-20261016.json); su campo `continuation_20261016` añade referencias actuales sin reescribir el corte original. Los cuerpos registrados, las pruebas que llaman a los auxiliares y los journals crudos se contrastaron separadamente.

| Conciliación | Antes | Actual |
|---|---:|---:|
| Tareas con llamadas candidatas enlazadas a journals v3 y archivo de test idéntico | 15/18 | 15/18 |
| Tareas adicionales con evidencia posterior pertinente | Sin conciliar en este índice | 3/18 |
| Total con algún enlace verificable | 15/18 | 18/18 |
| Aceptación integral conservación/N3 | Pendiente | Pendiente |

Estos números describen trazabilidad, no porcentaje de requisitos satisfechos. Una llamada PASS puede pertenecer a una rama que no ejecuta la purga: se revisaron expresamente los retornos del test de cobertura. Para actualizar esa evidencia se ejecutaron sólo `reference_page=True` en perfil/cuenta: [2PASS83,77s](cr09-retention-access-coverage-20261016.json), purga del cifrado vencido e idempotencia. La rama `reference_page=False` retorna antes de esas aserciones; no se cuenta como prueba de este efecto.

Las otras dos coincidencias posteriores se reutilizan: [caducidad e idempotencia](cr09-expiry-dispatch-terminal-20261015.json) y [objetos huérfanos con PostgreSQL/RustFS reales](cr09-orphan-retention-20261016.md). Sus archivos de prueba actuales y módulos de tarea son idénticos a los registrados. En las18 filas se encontraron journals con setup/call/teardown PASS y huellas exactas; esto no acredita automáticamente todos los auxiliares o dependencias transitivas.

## Finalidad, disparador y excepción comprobados en el alcance descrito

| Grupo y tareas | Contenido/plazo de ensayo | Retención o efecto que debe distinguirse |
|---|---|---|
| Diez purgas de borradores: decisiones de campo, inventario y cobertura de acceso, respuestas de acceso/portabilidad, cobertura/selección/evaluación de portabilidad, información y revisión de páginas | `expires_at<=now`, sin `purged_at`; vaciado de su campo cifrado, lotes100 | Conservan filas y vínculos de auditoría. El caso de borrador final `RightsAction` añadido a la purga de acceso distingue no emitido, emitido y legado emitido; no extrapolar esa excepción a cada modelo temporal. |
| Entrega de confirmación de cuenta | Enlace cifrado vencido; lotes100 | Revalida tras bloqueo, vacía sólo `encrypted_delivery`; conserva confirmación/propuesta/auditoría. |
| Reconciliación de revisiones de conservación | Plan con finalidades retain/review y fecha sintética; calendario reparable | No borra datos ni autoriza por sí sola prolongación o destrucción. Pruebas de plan manipulado, calendario parcial, revisión independiente e idempotencia. |
| Preparaciones y borrado de medios, dos tareas | Preparación descartada/vencida; trabajo pendiente o fallido con `next_attempt_at` vencido | Mantiene referencias compartidas, evidencia y rutas compartidas; eliminación física y reintentos se prueban mediante auxiliares reales. Incluye interrupción/procesamiento concurrente en sus pruebas originales. No equivalen a borrar sólo una fila. |
| Exportaciones temporales | Exportación vencida no purgada; lote1000 | Vacía carga/partes/imágenes y llama al borrado de objetos; conserva fuente y auditoría. Se reutilizan pruebas de skip_locked/reintento/no resurrección y los controles específicos de transporte/objetos; el antiguo43PASS por sí solo precede la integración del borrado físico de objetos. |
| Caducidad de anuncios | Publicado y vencido | Expira y audita una vez; futuro y pausado permanecen. No elimina datos del anunciante. |
| Entregas privadas del proxy | Vencimiento, generación revocada o exportación vencida/purgada; lote1000 | Elimina bytes preparados y conserva auditoría. Limpieza de ficheros huérfanos del proxy es distinta del repositorio cifrado. |
| Objetos cifrados huérfanos | Más de un día de gracia sintético y sin referencia Image/Part | HEAD404 del huérfano; objeto referenciado intacto y descifrable; RECOVERY_MODE o almacenamiento desactivado impiden barrido; repetición0. No prueba una espera real de24h ni despacho horario. |

El archivo comprimido del [43PASS original](conservacion-finalidad-ci-propio-20261009.json) se verificó por SHA y JUnit real:43/0fallos/0errores/0skips, diez archivos de test idénticos. Se preserva su alcance; el cuerpo posterior de `purge_expired_exports` cambió, por lo que no se convierte esa ejecución antigua en prueba de la integración de objetos. El módulo actual de tareas sí coincide con los journals v3 aplicables del índice.

## Límites y siguiente comprobación

Sigue pendiente la conciliación por recurso/finalidad de las excepciones y respaldos pertinentes, la aplicabilidad de dependencias cambiadas y la versión común N3. La evidencia de [Beat17 tareas](cr09-retention-worker-beat-20261016.md) acredita transporte/ejecución, con efecto explícito de expiración; no demuestra contenido de todas las purgas. El horario de huérfanos no se ha observado ni se cambió para acelerar una prueba.

Los plazos y bases del fixture son técnicos y sintéticos. No son política legal definitiva ni destrucción real. Próximo paso acotado: enlazar la rama de respaldo/restauración con conservación y supresión, usando el ensayo PG real ya ejecutado y las correctivas posteriores; no repetir restauración por rutina ni aceptar que un tombstone sea un backup.

La ejecución nueva tuvo fuentes congeladas y limpieza independiente: controlador/pytest/temporal/contenedores propios ausentes. Se conserva el fallo previo134112-fcd7c975 por formato documental antes de tests. Sin cambios productivos, proveedores, datos reales ni nuevas mediciones de capacidad. P95limpio0,862172866FAIL, CR09/N3 abiertos.
