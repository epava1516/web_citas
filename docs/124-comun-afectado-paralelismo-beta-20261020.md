# Común afectado y comparación de trabajadores pytest

Fecha:2026-10-20. Estado: preparación, no resultado ni aceptación beta.

## Motivo y alcance

Tras cerrar focales119–123, el defecto real de vigencia de catálogo y las correcciones de fixtures/expectativas requieren una candidata común. Se compara además el número de trabajadores solicitado por el usuario. Se ejecutan archivos completos, sin reducir casos para obtener menor tiempo.

Selección única preparada de40archivos,363casos previstos:34consentimiento+52catálogo+48historial/dependencias+48rutas+174almacenamiento+6unitarias del preflight+1diagnóstico manual del detector. Los24casos reforzados de123 ya están incluidos en los grupos48+48, no se duplican. El número definitivo se concilia con colección, journal y XML. Todos los94nodeids FAIL/ERROR de155011 deben estar presentes y pasar; no basta comparar totales.

Es una selección afectada, no regresión global ni aceptación de beta/capacidad. El diagnóstico manual prueba un detector mediante mutación temporal en memoria, no funcionalidad del mutante. Las174pruebas de almacenamiento mezclan unitarias e integración: no todas son S3 físico.

## Protocolo previo

Dos ejecuciones secuenciales:2trabajadores y luego4, misma selección, mismas fuentes congeladas, misma historia de duración para ordenar archivos completos y mismo orden interno. Snapshot de fixtures e aislamiento por generación de broker habilitados en ambas. PostgreSQL/Redis nuevos por ejecución, bases separadas por trabajador, RustFS fijado y puertos privados dinámicos; no se cambia producto, Gunicorn4sync, cuotas de capacidad ni criterios HTTP. PostgreSQL/Redis del arnés no tienen límites Docker explícitos; no atribuirles cuotas de los ensayos de capacidad.

Se registra hardware/afinidad y versiones de imágenes sin secretos. No ejecutar otro gate, extracción de grafo o medición propia simultánea; no declarar el host aislado de tareas ajenas. El orden2→4 y las cachés del sistema compartidas limitan causalidad. Se reconstruyen fixtures/servicios por ejecución, sin borrar cachés del host. Un par permite comparar tiempos observados, no demostrar reproducibilidad global ni extrapolar a todos los perfiles.

Antes de empezar: grafo dirigido de fuentes afectadas y semántica real de decisiones/documentos, selección/historial conservados y huellas. Congelar hasta terminar ambos brazos; no modificar fuentes, ledger, allowlist ni grafo entre ellos. Los auditores sólo escriben evidencia documental, excluida del conjunto de fuentes del arnés.

## Evidencia y decisión

Cada brazo necesita todos los casos PASS,0FAIL/ERROR/SKIP, fases únicas por nodeid,94negativos originales revalidados, cursor físico preparado por fase y detección del mutante, mismos622archivos de producto, huellas intactas, servicios/temporales/procesos retirados y Telegram terminal con delivery:sent. Registrar tiempos de pytest y suma de pasos del gate, preparación y duración por archivo por separado. El journal vigente no identifica al trabajador de cada reporte: declarar esa distribución no disponible, sin inferirla desde el orden global. Comparar con fuentes idénticas y conservar cualquier fallo o empeoramiento.

No adoptar4sólo por tener más procesos. Si falla o no mejora de forma clara, conservar2y estudiar el cuello concreto; no ocultar problemas de concurrencia ni eliminar pruebas. Si mejora, describir sólo la ganancia observada y su alcance; cualquier cambio de default requiere valorar también memoria/aislamiento y la cola funcional frente a capacidad serial.

Quedan regresión amplia sobre candidata común, capacidad contractual y B00residual/B07–B17. Corto TCP20RPS sigueFAIL y900s bloqueado. Sin proveedores/publicación/pagos/datos reales. No declarar las actas históricas reaceptadas globalmente por esta comparación.


## Rechazo de argumentos y corrección previa

Primer lanzamiento:EXIT2 antes de crear run_id/servicios o ejecutar casos; no es un FAIL de pytest. El arnés admitía duración sólo en regression/functional y rechazó focused. Intento/stdout/huellas conservados con sufijo initial-cli-rejection y aviso terminal Telegram confirmado. La segunda ejecución no se lanzó.

Corrección acotada en run_local_ci: permitir ordenar focales funcionales paralelas; conservar rechazo de archivos capacity y escenarios LONG por ruta resuelta, de carril capacity y ejecución serial. Sin cambio de producto. Cinco comprobaciones CLI con rechazos esperados pasan, incluida ruta normalizada y llegada de una selección válida al control de historial;0casos ejecutados y ningún run_id creado. Evidencia beta-focused-duration-cli-guards-20261020.json con recibos enviados. No sustituyen la ejecución positiva común. Antes de reintentar se actualizan grafo y congelación; ambos brazos usarán el mismo arnés corregido.


## Terminales comunes y comparación auditados

192749-1b6418af (2workers) y193902-5d573925 (4workers):363PASS/0FAIL/0ERROR/0SKIP cada uno, mismos40archivos/nodeids y todas las fuentes congeladas idénticas. Los94negativos originales y52erroresRustFS pasan en ambos;622fuentes de producto idénticas. Auditorías beta-affected-common-two-terminal-audit-20261020.json, beta-affected-common-four-terminal-audit-20261020.json y beta-worker-comparison-20261020.json comprueban también argumentos distintos sólo en workers, mismo historial/orden interno, limpieza fresca y recibos reales.

| Medida | 2workers | 4workers | Reducción observada |
| --- | ---: | ---: | ---: |
| Proceso pytest (uv/xdist incluidos) |624,180s|349,882s|43,95%|
| Tiempo JUnit |622,263s|347,997s|44,08%|
| Suma pasos del gate |640,066s|365,714s|42,86%|
| Runner completo, limpieza/aviso incluidos |653,955s|379,667s|41,94%|

Un solo par en orden2→4, con cachés/host compartidos: mejora observada en esta selección, no causalidad aislada ni reproducibilidad global. No hay comparación de RSS ni distribución efectiva por trabajador. Se eligen4explícitos para la próxima regresión funcional amplia; default general6y producto4sync intactos. Capacidad sigue serial. Recibos de tests1792525123147586677-2469309 y1792525522035410118-2547350, auditorías1792525133427541148-2544721/1792525532144781855-2598415 y comparación1792525592952567860-2604692, todos sent.

El común confirma las correctivas en una candidata única, incluido el arnés de focales por duración; no reescribe el negativo155011 ni acredita los demás miles de casos. Próximo125:regresión funcional amplia persistente, justificada por adaptación compartida y defecto real de catálogo ya corregido. Corto TCP sigueFAIL,900s bloqueado y beta global pendiente.
