# Operación de seguridad e incidentes

Procedimientos originales: 2026-10-03. Revisión técnica local: 2026-10-19. Los mecanismos/simulacros propios y sus límites se concilian por OP001–009 en [auditoría100](100-auditoria-seguridad-tecnica-local.md) y [acta B-B09](actas/09-bb-aceptacion-tecnica-local-20261019.md). Responsables, custodia y procedimientos reales de producción siguen pendientes.

## Preparación

Antes de producción definir contactos del operador, operaciones, moderación, privacidad y proveedores y sus sustitutos; canal seguro de coordinación; inventario de servicios y credenciales; acceso de emergencia controlado; capacidad de retirar anuncios y revocar sesiones; ubicación de backups y claves. No registrar secretos o datos personales reales en este documento.

Cada procedimiento genera registro restringido de inicio, hechos, decisiones, responsables, acciones y cierre. Capturar evidencias mínimas con finalidad y plazo, sin copiar datos sensibles indiscriminadamente.

## OP-001 — Cuenta comprometida

1. Recibir reporte y comprobar control por procedimiento de recuperación; no basarse únicamente en teléfono/nombre públicos.
2. Restringir cambios sensibles y revocar sesiones/tokens afectados; no borrar evidencias necesarias.
3. Revisar cambios de contacto, miembros de agencia, perfiles, fotos y publicaciones realizados durante el intervalo.
4. Restaurar gestión autorizada y revalidar contenido afectado; si hay duda, mantenerlo pendiente.
5. Recuperar acceso/MFA de forma segura, notificar mediante el flujo apropiado y evaluar si hubo acceso a datos personales.
6. Documentar causa, reparación y medidas preventivas. Si afecta agencia, comprobar todos los recursos accesibles desde esa cuenta.

## OP-002 — Menores, explotación o imágenes sin autorización

1. Asignar prioridad y responsable; no esperar observación de comportamiento de bots.
2. Restringir contenido/acceso según procedimiento y urgencia, purgando derivados públicos cuando corresponda.
3. Revisar cuenta, autorización y publicaciones relacionadas con acceso mínimo.
4. Aplicar protocolo jurídico para posible contenido ilícito y comunicación a autoridades; no redistribuir material ni descargarlo sin criterio definido.
5. Comunicar decisiones y habilitar revisión cuando corresponda, protegiendo identidad de denunciante y afectado.
6. Cerrar con motivo y conservación justificada. No reponer material automáticamente por pago, reintento de tarea o reclamación sin revisar.

## OP-003 — Duplicados y posible automatización

1. Registrar coincidencias e intentos; distinguir hash exacto, similitud y teléfono compartido autorizado.
2. Mantener límites y aplicar política de borrador/publicación acordada; esa política sigue pendiente.
3. Analizar cadencia y contexto de agencia, descartando reintentos técnicos.
4. Moderar titularidad sin atribuírsela al primer uploader y sin revelar cuentas relacionadas al solicitante.
5. Solicitar corrección/comprobación o restringir según señales y revisión; registrar motivos y reclamación.

## OP-004 — Saturación o denegación de servicio

1. Identificar qué satura: entrada, consultas, cargas, workers, broker, almacenamiento o envíos de verificación.
2. Aplicar límites/cupos y priorizar funciones esenciales; pausar admisión de trabajos pesados si es necesario.
3. Mantener autenticación, autorización y estado de revisión al degradar servicios; no usar excepciones que publiquen material sin controles.
4. Revisar costes y alertas de proveedores; ampliar recursos solo con diagnóstico.
5. Recuperar cola de forma idempotente y analizar causa y umbrales. No eliminar trabajos o datos a ciegas.

## OP-005 — Secreto expuesto o servicio comprometido

1. Aislar componente/acceso comprometido y preservar registros mínimos necesarios.
2. Revocar y rotar credenciales afectadas, incluidos tokens de almacenamiento, broker, base y CI/CD según alcance.
3. Si una clave afecta sesiones o firmas, evaluar invalidez y mecanismos de transición; no mantener tokens comprometidos por comodidad.
4. Reconstruir desde artefactos confiables y revisar cambios de configuración/datos.
5. Determinar exposición de datos y activar OP-006 cuando proceda; eliminar filtración del historial público no sustituye rotación.
6. Verificar servicios y accesos antes de reabrir; documentar correcciones y revisión independiente según gravedad.

## OP-006 — Brecha de datos personales

1. Registrar momento de conocimiento y delimitar datos, afectados, accesos y medidas de contención.
2. Involucrar al responsable de privacidad/operador y evaluar riesgo y deberes de notificación conforme a `06-marco-legal.md`.
3. Aplicar plazos pertinentes sin esperar información perfecta si la norma exige notificación; justificar decisiones y retrasos cuando corresponda.
4. Preparar comunicación clara mediante canal definido, sin divulgar más datos de los necesarios.
5. Documentar incluso decisiones de no notificar, reparación, seguimiento y medidas para evitar repetición.

Este procedimiento no implica notificar toda incidencia ni sustituye la evaluación jurídica del caso.

## OP-007 — Restauración y recuperación

1. Fijar causa, alcance y punto de recuperación; obtener backups y claves mediante acceso autorizado.
2. Restaurar en entorno aislado y comprobar integridad de PostgreSQL, archivos y referencias.
3. Reconciliar retiradas, supresiones, cambios de permisos y decisiones posteriores al backup antes de publicar.
4. Reconstruir cachés y derivados necesarios; no restaurar contadores/colas como si fueran estados de negocio.
5. Reanudar tareas idempotentes sin duplicar correos, publicaciones o pagos.
6. Verificar flujos críticos, errores, permisos y exposición de archivos antes de abrir tráfico.
7. Registrar tiempo real de recuperación y pérdida de datos frente a RTO/RPO; corregir desviaciones.

## OP-008 — Retirada y derechos de datos

1. Comprobar solicitud y legitimidad sin pedir documentación desproporcionada.
2. Inventariar datos asociados: cuenta, perfil, anuncios, medios, contactos, eventos y proveedores.
3. Retirar exposición pública y limpiar índices/cachés/derivados; aplicar borrado, bloqueo o conservación justificada por tipo de dato.
4. Gestionar referencias compartidas sin borrar material autorizado de terceros indiscriminadamente.
5. Registrar obligaciones pendientes en proveedores/backups y asegurar reconciliación al restaurar.
6. Responder según procedimiento de derechos y plazos aplicables, sin prometer control sobre copias ajenas.

## OP-009 — Actualizaciones y accesos

Cadencia pendiente de definir: revisar versiones soportadas, vulnerabilidades y avisos de proveedores; priorizar parches según exposición; probar en entorno separado y desplegar con recuperación disponible. Inventariar acceso de personal, revocar al cambiar funciones y comprobar permisos de emergencia.

Distinguir parches urgentes de cambios de funcionalidades; no aplazar una vulnerabilidad explotable hasta una futura versión de producto. Mantener registro de despliegues, dependencias y configuración relevante.

## Simulacros y seguimiento

Realizar antes de lanzar: restauración completa, toma de cuenta de agencia, retirada urgente y caída de worker/broker. Repetir cuando cambien componentes o aparezcan fallos que lo justifiquen; periodicidad ordinaria pendiente.

Medir detección, contención, retirada, recuperación y resolución; evitar que los indicadores incentiven cierre de denuncias sin revisar. Registrar hallazgos y tareas correctoras en el plan de seguridad. La ausencia de simulacros correspondía al estado inicial. La evidencia técnica local posterior de recuperación, retirada urgente, revocación y colas se delimita por procedimiento en auditoría100; no equivale a simulacro jurídico, recepción externa ni preparación del personal real.


## Ensayo local de limpieza de copias con worker/Beat

El comando vigente se lanza desde el host con la configuración local de desarrollo y Docker disponibles:

```bash
docker compose build worker beat
uv run python -m scripts.probe_export_retention_worker launch
```

El launcher crea una base PostgreSQL retention_probe_UUID y una cola Redis del mismo nombre. Levanta worker y Beat temporales, migra únicamente esa base y ejecuta fixtures sintéticos. Los modos internos fixture/state/dispatch/worker/beat rechazan una base fuera de ese prefijo; las operaciones de tareas exigen cola igual a la base. PRODUCCIÓN prohibida y adaptadores de derechos/avisos disabled. No detener ni sustituir los servicios principales.

Por tanda se crean dos copias (caducada/vigente), dos imágenes WebP cifradas por copia y filas sintéticas de persona, revisión, fotos y auditoría. Proof pending; no son una comprobación de identidad, revisión humana ni decisión real de derechos. La revisión está en draft, sin publicación ni originales físicos. El ensayo comprueba snapshots cifrados de DB y filas de origen; no verifica archivos originales, WAL, réplicas o backups.

Primero se envía la tarea real a Redis y se coteja resultado1; repetición resultado0 y fechas de purga idénticas. JSON e imágenes caducados vacíos, copias vigentes y metadatos de Blob comparados por digest de bytes antes/después, filas de acceso/descarga/action/proof/fotos conservadas. Después se crea una segunda tanda y se observa Beat sin dispatch manual, conservando la tarea e intervalo60s de la aplicación; los otros schedules no se cargan en este Beat aislado. Logs received/succeeded del worker y envío del scheduler deben coincidir con IDs de tareas. Result backend/ignore_result se habilitan solo dentro de procesos de ensayo, no en configuración de aplicación.

El launcher elimina contenedores/base y vacía la cola temporal en finally incluso si falla; el estado de timeout se imprime minimizado para diagnóstico. Observar el proceso mediante sesión del comando; no repetir mientras sigue vivo. El nombre temporal se incluye en resultado para comprobar eliminación posteriormente. No datos reales ni comunicación externa.

El ensayo histórico de JSON del 2026-10-04 utilizó el comando anterior sin argumento y --beat sobre servicios principales:0.501s manual y61.352s automático, código histórico d2bb585/safety0018. Estos comandos se sustituyen por launch y no deben copiarse para la versión actual. La evidencia nueva de imágenes se registra por separado en docs/18; no ampliar retroactivamente el alcance de la histórica.


Ensayo físico de supresión local: `uv run python -m scripts.probe_media_erasure_worker launch`. Crea DB/cola/worker/Beat media_probe_UUID, PNG original/WebP derivado sintéticos y archivos vigentes de control; identidad pending/plan-ejecución fixture, no decisión acreditada. Worker manual y Beat60s de la aplicación; cleanup de DB/contenedores/cola y archivos solo del namespace del probe. Evidencias finales en docs/30/18. No S3/versiones/CDN/backups comprobados.

## Estáticos en actualizaciones locales Docker

El build recoge estáticos en la imagen, pero Compose monta static_data persistente en /app/staticfiles y Caddy lo lee desde ese volumen. Recrear app no sustituye el contenido existente del volumen. Tras reconstruir/recrear y aplicar migraciones, ejecutar `docker compose exec -T app python manage.py collectstatic --clear --noinput` y verificar el archivo servido por Caddy contra el SHA-256 de static/app.css. No borrar el volumen para actualizar CSS. El vaciado con `--clear` se limita a `STATIC_ROOT`, que debe ser exclusivo de archivos estáticos recopilados; nunca debe contener medios privados o archivos de usuarios. Ejecutar durante mantenimiento, antes de reabrir tráfico, y verificar después los cinco activos y los archivos obsoletos. No se ejecuta sobre los servicios normales como parte de los probes locales.

Detectado durante supresión de cuenta: los14 archivos fuente coincidían host/app/worker/Beat, pero el CSS HTTP de Caddy seguía siendo anterior. collectstatic copió128 archivos y dejó2 sin cambios; comprobación62078 terminal0 confirmó CSS servido igual a fuente, evidencia supresion-cuenta-runtime.json. La futura automatización de despliegue en B-B debe incluir esta fase antes de aceptar la versión; health200 por sí solo no demuestra que los estáticos coincidan.

## Permisos de revisión independiente de portabilidad

La migración0085 crea el permiso `safety.review_portability`. La semilla sintética `seed_demo` no lo asigna automáticamente; las pruebas lo conceden expresamente a un segundo usuario. Para reproducir el flujo local, configurar mediante administración un revisor distinto del autor con `safety.review_rights_request`, `safety.execute_rights_request` y `safety.review_portability`, además de MFA y ausencia de conflicto de interés. El responsable de preparar/generar sigue sujeto a asignación y permisos propios; tener el permiso independiente no permite aprobar la selección propia ni sustituye lectura del expediente, fuente o prueba vigente.

La preparación de entrega debe comprobar este reparto de responsabilidades y documentar quién administrará sus permisos; no dar el permiso a todas las cuentas como solución a una pantalla vacía. Esta nota describe la configuración técnica local; operadores reales, proveedores y preparación de producción siguen pendientes.


### Actualización y rollback de estáticos verificados, 2026-10-19

[Ensayo BB06 propio](evidencias/bb06-static-update-terminal-20261019.json): un volumen con CSS de fecha posterior a la imagen de rollback conserva los bytes antiguos con collectstatic normal. `--clear --noinput` restablece los cinco activos por SHA y elimina un JS obsoleto (HTTP404), conservando un control fuera de STATIC_ROOT. Configuración Caddy idéntica, imagen v11 inmutable y recursos propios eliminados; fuentes/Telegram verificados. El [primer fallo de arranque](evidencias/bb06-static-startup-failure-20261019.json) queda conservado.

La comparación por fecha está descrita en la [documentación oficial de Django](https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/). Por ello health200 o recrear el contenedor no bastan para aceptar una actualización/rollback. Esta evidencia se limita a activos; migración de esquema y recuperación de datos conservan sus pruebas separadas.
