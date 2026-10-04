# Operación de seguridad e incidentes

Actualizado: 2026-10-03. Estado: procedimientos propuestos, pendientes de responsables, herramientas y simulacros.

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

Medir detección, contención, retirada, recuperación y resolución; evitar que los indicadores incentiven cierre de denuncias sin revisar. Registrar hallazgos y tareas correctoras en el plan de seguridad. Ningún simulacro ha sido ejecutado todavía.


## Ensayo local de limpieza de copias con worker/Beat

`python -m scripts.probe_export_retention_worker` se ejecuta en el contenedor app de desarrollo, con PostgreSQL/Redis y worker reales. Rechaza PRODUCTION. Crea un expediente operativo sintético, Proof pending y copias caducada/vigente: no simula identidad aprobada ni crea publicación. Comprueba purga de contenido vencido, preservación del vigente y auditoría; elimina exclusivamente su fixture al pasar. Fallo deja fixture para diagnóstico. No ejecutar sobre datos reales.

Para distinguir worker de Beat, detener Beat durante prueba manual; preservar resto de servicios:

```bash
docker compose stop beat
docker compose exec -T app python -m scripts.probe_export_retention_worker
docker compose up -d beat
docker compose exec -T app python -m scripts.probe_export_retention_worker --beat
```

En modo normal envía dos jobs y muestra sus IDs: cotejar received/succeeded en logs de worker. En modo Beat no publica jobs, espera hasta75s y emite task_ids vacío; cotejar envío purge-expired-private-copies en scheduler y resultado en worker. Observar proceso mediante sesión del comando, sin repetir por falta temporal de salida. Tiempo medido no es SLA ni carga:0.501s manual,61.352s automático en ensayo2026-10-04. Docker ejecuta código d2bb585/probe, migra hasta0018; servicios de DB/Redis y datos anteriores preservados. Ningún envío de email/proveedor, borrado físico/backups ni cumplimiento jurídico acreditado.
