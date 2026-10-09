# Plan de seguridad, implementación y validación

Plan de requisitos del 2026-10-03. Revisión documental: 2026-10-09. El plan conserva sus controles, gates y criterios; la implementación y verificación local de cada alcance se consultan en [seguimiento17](17-seguimiento-desarrollo.md), [auditoría83](83-auditoria-pendientes-cr09.md) y [matriz88](88-matriz-cierre-derechos.md). No implica que todos los controles estén pendientes de código ni que estén aceptados integralmente. La revisión externa y producción siguen sujetas a sus gates.

## Propósito y alcance

Convertir los riesgos y controles de [seguridad](03-seguridad-privacidad.md), [legalidad](06-marco-legal.md) y [antiduplicados](10-unicidad-antiduplicados.md) en trabajo ejecutable. Cubre aplicación Django, agencias, medios, PostgreSQL, Redis/Celery, almacenamiento, proxy, despliegue, personal de soporte y proveedores.

Referencias SEC-xxx corresponden a la matriz de `03-seguridad-privacidad.md`; IMP-xxx identifica paquetes de implementación de este documento. Todos están pendientes. «Necesario» significa necesario para cubrir el riesgo en el alcance descrito; no convierte una propuesta de producto aún abierta en decisión aprobada.

## Responsabilidades propuestas

| Función | Responsabilidad | Persona asignada |
| --- | --- | --- |
| Producto/operador | Política de publicación, recursos de moderación, alcance y aceptación de riesgos residuales | Pendiente |
| Desarrollo | Permisos, flujos, integridad y pruebas | Pendiente |
| Operaciones | Secretos, redes, backups, despliegue, alertas y recuperación | Pendiente |
| Moderación/soporte | Autorizaciones, conflictos, reclamaciones y respuesta a indicios graves | Pendiente |
| Privacidad/asesoría jurídica | Bases jurídicas, retención, contratos y evaluación del modelo | Pendiente |
| Revisión de seguridad | Verificación independiente y seguimiento de correcciones | Pendiente |

Una persona puede asumir varias funciones, pero las acciones deben ser atribuibles a una cuenta individual. No compartir credenciales. Nombrar sustituto y contacto para incidentes antes del lanzamiento.

## IMP-001 — Modelo de amenazas y datos

Relaciona SEC-001, SEC-006, SEC-011 y LEG-001/002.

Trabajo:

- Diagramar navegador, proxy, aplicación, base, broker, workers, almacenamiento, correo, verificadores y administración, con límites de confianza.
- Inventariar datos y clasificarlos: públicos, privados de cuenta y restringidos de verificación/moderación. Los públicos siguen siendo datos personales cuando corresponda.
- Enumerar actores: visitante, particular, agencia, miembro de agencia si se admite, moderador, administrador, proveedor y atacante.
- Modelar uso indebido: robo de cuenta, cambio de teléfono, acceso cruzado, suplantación, duplicados, extracción masiva y agotamiento de recursos.
- Definir datos estrictamente necesarios y separar prueba de verificación de documentos originales.

Entregable: mapa de datos y flujos, inventario de activos y riesgos priorizados. Criterio: cada dato tiene finalidad, acceso y conservación; cada frontera tiene controles y pruebas asignados.

## IMP-002 — Autorización y agencias

Relaciona SEC-001, SEC-003, SEC-011.

Trabajo:

- Matriz rol × acción × recurso: consultar/crear/editar/publicar/retirar anuncio, ver fotos originales, gestionar contactos, consultar verificaciones y resolver denuncias.
- Denegación por defecto y control servidor por propietario/gestor en todas las rutas, fragmentos HTMX, exportaciones y tareas.
- Separar cuenta, agencia, persona representada y anuncio; asignaciones y permisos explícitos.
- Definir transferencia/salida de agencia, consentimiento de representación y revocación. Retirar permisos antes de permitir nuevo gestor.
- Moderación no necesita automáticamente acceso a todos los documentos; concederlo por función y finalidad.

Pruebas: cambiar ID en ruta/cuerpo, editar campos de gestor mediante petición manipulada, miembro revocado, descarga privada y tarea antigua tras transferencia. Criterio: ninguna operación expone o modifica recursos ajenos; los IDs difíciles de adivinar no sustituyen permisos.

## IMP-003 — Acceso, MFA y recuperación

Relaciona SEC-002 y SEC-003. MFA obligatorio en agencias sigue propuesto; administración con MFA forma parte del plan de seguridad.

Trabajo:

- Usar autenticación y hash de contraseñas soportados; seleccionar algoritmo y coste adecuados a hardware y versiones, sin criptografía propia.
- Verificar correo, limitar intentos y usar respuestas que no permitan enumerar cuentas mediante registro/recuperación.
- Elegir MFA y recuperación: códigos de respaldo protegidos, cambios de factor reautenticados y procedimiento de soporte sin saltos por datos públicos.
- Tokens/códigos aleatorios, caducidad, uso único y consumo atómico; no registrar códigos en logs.
- Revocar sesiones según política al recuperar cuenta/cambiar credenciales; pantalla de sesiones activas propuesta.
- En cambio de teléfono/correo, comprobar control del nuevo canal, notificar por flujo de seguridad diseñado y revisar verificaciones dependientes.

Pruebas: fuerza bruta limitada, código caducado/reutilizado, dos consumos simultáneos, recuperación de MFA, sesión antigua y redirección manipulada. Criterio: recuperación no debilita el acceso ni permite cambiar datos de otra cuenta.

## IMP-004 — Texto, formularios y enlaces

Relaciona SEC-004 y SEC-008.

Trabajo:

- Texto plano como candidato inicial; si hay formato, lista permitida y sanitización mantenida. Evitar marcar contenido de usuario como seguro sin validación.
- Escape en ficha, listados, panel, correos y fragmentos HTMX; no insertar HTML arbitrario con JavaScript.
- CSRF en operaciones autenticadas por cookies, métodos HTTP correctos y validación de origen/configuración.
- Consultas parametrizadas; validar filtros, ordenaciones, longitud y tamaño de solicitudes en servidor.
- Esquemas de enlaces permitidos y destinos de redirección controlados; evitar contenido activo en enlaces.
- Configurar CSP y cabeceras de seguridad según recursos reales, sin excepciones amplias por comodidad.
- Importación de imágenes por URL fuera del alcance inicial propuesto. Si se añade, revisar DNS, redirecciones, destinos internos y acceso a metadatos de infraestructura.

Pruebas: entradas maliciosas en todos los puntos de visualización, solicitudes CSRF, parámetros de orden manipulados y enlaces peligrosos. Criterio: contenido de usuario no ejecuta código ni altera consultas o flujos.

## IMP-005 — Cargas y procesamiento de medios

Relaciona SEC-005, SEC-006 y REQ-016.

Trabajo:

- Definir formatos aceptados, bytes máximos, píxeles, cantidad por anuncio y cuotas. Los valores se decidirán con necesidades y pruebas, no se inventan aquí.
- Carga privada, validación de tipo real, nombre generado, orientación y recodificación de derivados sin EXIF ni metadatos innecesarios.
- Separar fotos de documentos; documentos no admitidos hasta definir necesidad, formatos, análisis y retención.
- Workers con límites de memoria/CPU/tiempo, dependencias actualizadas y salida de red restringida cuando no se requiera.
- SHA-256, huellas visuales/regionales y comparación de candidatos conforme al plan antiduplicados. Algoritmos, licencias y umbrales pendientes.
- Guardar estado de procesamiento y revisión; un fallo no libera la foto a publicación.
- Archivos temporales con limpieza y cuotas; tareas no transportan documentos completos si basta referencia.

Pruebas: extensión engañosa, fichero corrupto, imagen de dimensiones desmesuradas, EXIF GPS, duplicados modificados, caída/reintento de worker y exceso de cuotas. Criterio: solo derivados aprobados se hacen públicos; no hay acceso cruzado ni publicación por fallo.

## IMP-006 — Almacenamiento, caché y retirada

Relaciona SEC-006 y LEG-002/006.

Trabajo:

- Separar permisos/orígenes de originales, documentos y derivados públicos; acceso privado cerrado por defecto.
- Enlaces temporales emitidos tras autorización, vigencia limitada, sin inclusión en telemetría o cabeceras de referencia innecesarias.
- No servir HTML/SVG de usuarios desde el origen autenticado. El dominio de medios no debe recibir cookies de sesión.
- Cachear solo respuestas aptas: excluir panel, originales, documentos, borradores y datos personalizados.
- Definir invalidación al editar/retirar y purga CDN; una foto pública no se vuelve privada solo cambiando su fila en la base.
- Eliminar derivados y objetos huérfanos; si hay deduplicación física, revisar referencias autorizadas antes de borrar.
- Aplicar conservación a backups y asegurar que una restauración respeta retiradas/supresiones; definir reconciliación de solicitudes posteriores al backup.

Pruebas: otra sesión no ve respuestas privadas cacheadas, enlace caducado, retirada en origen/CDN, cambio de permisos y restauración con solicitudes de borrado. Criterio: retirada interna efectiva y límites externos claramente documentados.

## IMP-007 — Publicación, unicidad y abuso

Relaciona SEC-007, SEC-012 y DEC-017 a DEC-023.

Trabajo:

- Máquina de estados explícita de borrador, procesamiento/revisión, publicado, pausado, rechazado y retirado; transiciones autorizadas.
- Versionar cambios relevantes; revalidar publicación tras cambios de fotos, gestor, teléfono, servicios o tarifas.
- E.164 y catálogo canónico de teléfonos, asociaciones autorizadas y restricciones de integridad acordadas.
- Proteger frente a carreras con transacciones/restricciones, no solo «buscar antes de insertar».
- Registrar intentos sin bloquear inmediatamente cuenta por coincidencia; publicación pendiente y borradores limitados siguen propuesta por resolver.
- Límites por acción y cuenta, con protección de borde complementaria. Definir comportamiento al caer Redis y preservar límites críticos.
- Observación con eventos mínimos y contadores, sin fingerprinting ni reconocimiento facial; actividad elevada no prueba bot.
- Si hay promociones/pagos: importe calculado en servidor, evento firmado, idempotencia y estados de pago separados de autorización de publicación.

Pruebas: dos publicaciones simultáneas, reintentos, agencias válidas, evasión con otro número, fallo de contador, tareas duplicadas y eventual webhook repetido. Criterio: no hay publicación inválida o cobro duplicado por carreras; carga limitada incluso bajo observación.

## IMP-008 — Moderación y protección de personas

Relaciona SEC-011, LEG-001/003/005/006.

Trabajo:

- Política de contenido, edad, autorizaciones, perfiles de agencia y material explícito definida por alcance/territorio.
- Cola con prioridades, responsables y capacidad; la observación de bots no retrasa indicios graves.
- Canal de denuncia accesible, razones de decisión, revisión y procedimiento de titularidad de imágenes/perfiles.
- No dar la propiedad de una imagen a quien la subió primero. Verificación de teléfono distinta de identidad o autorización.
- Registrar accesos a evidencias y cambios; descargas restringidas y evitar circulación por correo o herramientas no evaluadas.
- Procedimiento de órdenes de autoridades y posible material ilícito, sin conservación indiscriminada.

Pruebas: denuncia de tercero, salida de agencia, titularidad disputada, retirada urgente y revisión de un falso positivo. Criterio: cada caso tiene responsable y resultado trazable; no se exponen datos del denunciante o cuentas relacionadas.

## IMP-009 — Infraestructura y despliegue

Relaciona SEC-009.

Trabajo:

- Entornos separados y datos sintéticos en pruebas; permisos de infraestructura por función.
- Docker sin privilegios, sin socket del host, imágenes mínimas y versiones soportadas; configurar filesystem de solo lectura donde sea compatible.
- Secretos en mecanismo de ejecución/gestión con rotación, acceso limitado y procedimiento de filtración.
- Caddy/HTTPS, hosts y orígenes admitidos, cookies seguras, confianza en proxy y cierre de debug.
- PostgreSQL, Redis y observabilidad en redes privadas; credenciales diferenciadas según tareas. Separar caché y broker por políticas de memoria si ambos usan Redis.
- CI/CD con permisos mínimos, sin secretos en contribuciones no confiables, dependencias bloqueadas y revisión de imágenes/licencias/vulnerabilidades.
- Migraciones y rollback compatibles con esquema; no asumir que volver a una imagen restaura datos.

Pruebas: configuración de despliegue, puertos públicos previstos, ausencia de secretos en artefactos/logs y ensayo de actualización/rollback. Criterio: exposición y permisos coinciden con el inventario; despliegue repetible y recuperable.

## IMP-010 — Telemetría, incidentes y continuidad

Relaciona SEC-007, SEC-010 y LEG-009.

Trabajo:

- Métricas de latencia, errores, autenticación, cargas, cola, almacenamiento, base y coste de proveedores; umbrales y responsables definidos tras medición.
- Logs estructurados con IDs internos, sin tokens, credenciales, documentos, teléfonos completos o textos sensibles.
- Auditoría de acciones sensibles separada de diagnóstico; proteger contra modificaciones y registrar acceso con conservación definida.
- Backups cifrados de datos/archivos/configuración necesaria, fuera del alcance de borrado de la aplicación; recuperar claves por procedimiento protegido.
- Fijar objetivos RPO/RTO y probar restauración completa en entorno aislado.
- Procedimientos en [operación e incidentes](12-operacion-seguridad.md), con contacto de guardia/sustituto y evaluación jurídica de notificaciones.

Pruebas: caída de servicio, indisponibilidad de broker, compromiso de credencial, recuperación completa y detección de datos sensibles en logs. Criterio: alerta llega al responsable y recuperación cumple objetivos medidos.

## IMP-011 — Cumplimiento y proveedores

Relaciona todos los LEG-xxx.

Trabajo: cerrar territorios/contenido/operador, registro de tratamientos, bases y categorías especiales, evaluación EIPD/DPD, retención, derechos, contratos/transferencias, textos informativos reales y compatibilidad contractual con el sector. Establecer fuentes geográficas con licencia. Revisar analítica, cookies, mapas y recursos externos antes de incorporarlos.

Evidencia: documentos versionados, contratos y procedimiento de derechos probado. Las evidencias con datos reales se guardan en repositorio restringido, no en `docs/`. Criterio: no quedan tratamientos sin finalidad, base, acceso o plazo; las conclusiones jurídicas están documentadas por el responsable correspondiente.

## Orden de ejecución propuesto

1. IMP-001/011 y decisiones de producto: datos, contenido, agencias y publicación.
2. IMP-002/003/004: permisos y acceso antes de exponer formularios.
3. IMP-005/006/007/008: medios, publicación, duplicados y moderación.
4. IMP-009/010: despliegue, observabilidad y recuperación, preparándolos durante el desarrollo.
5. Pruebas integradas, carga representativa, revisión independiente y correcciones.

## Criterios de salida a producción

| Gate | Condición | Estado |
| --- | --- | --- |
| G-01 Alcance | Políticas, territorios, roles y publicación resueltos | Pendiente |
| G-02 Privacidad | Datos, contratos, retención y derechos revisados | Pendiente |
| G-03 Acceso | Pruebas de permisos, recuperación y cambios sensibles pasan | Pendiente |
| G-04 Medios | Validación, almacenamiento privado y retirada comprobados | Pendiente |
| G-05 Integridad/abuso | Concurrencia, límites y observación comprobados | Pendiente |
| G-06 Operación | HTTPS, secretos, redes, alertas y restauración comprobados | Pendiente |
| G-07 Moderación | Personal, procedimientos y respuesta a casos prioritarios preparados | Pendiente |
| G-08 Revisión | Hallazgos que permitan acceso ajeno, filtración, toma de cuenta o publicación ilícita resueltos; restantes riesgos documentados y aceptados por responsable | Pendiente |

No declarar listo basándose solo en que «las pruebas pasan» si falta capacidad operativa, configuración real o análisis legal. No existe fecha de producción aprobada.

## Registro de evidencias

Plantilla por control: ID, versión/commit, entorno, fecha, responsable, procedimiento, resultado, enlace restringido a evidencia, hallazgo, corrección y reevaluación. Estados: pendiente, en curso, implementado, verificado o no aplicable justificado. Los ejemplos y este plan no son evidencias de implementación.

Fuentes técnicas y jurídicas: enlaces oficiales en `03-seguridad-privacidad.md`, `06-marco-legal.md` y `10-unicidad-antiduplicados.md`. No se añade una garantía de cumplimiento o de ausencia de vulnerabilidades.
