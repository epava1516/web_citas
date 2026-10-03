# Seguridad, privacidad y moderación

Actualizado: 2026-10-03. Estado: requisitos y controles propuestos; no implementados.

El inventario normativo, entregables y análisis de aplicabilidad se desarrollan en [Marco legal](06-marco-legal.md).

Las tareas, dependencias, pruebas y criterios de producción se desarrollan en [Plan de seguridad](11-plan-seguridad-validacion.md). Los procedimientos de incidentes y recuperación están en [Operación de seguridad](12-operacion-seguridad.md).

## Riesgos específicos

Suplantación, publicación sin autorización, presencia de menores, explotación o coacción, filtración de identidad, exposición de contactos, acoso, extracción masiva de datos y archivos maliciosos. Priorizar estos riesgos al diseñar el producto.

## Controles propuestos

- Autorización en servidor por propietario y rol; comprobar acceso a objetos, fotografías y evidencias privadas.
- MFA para administración, privilegios mínimos y auditoría de acciones sensibles.
- Sesiones seguras, protección CSRF cuando corresponda, validación de entradas, escape de contenido y límites de abuso.
- Comprobar tipo real, tamaño y dimensiones de imágenes; recodificar derivados y eliminar metadatos EXIF, incluida geolocalización. No ejecutar archivos subidos.
- Acceso restringido a originales y verificaciones; URLs temporales para material privado cuando corresponda.
- Mostrar únicamente contactos seleccionados para publicación. Explicar que un contacto o una imagen públicos pueden ser copiados; no prometer impedirlo por completo.
- No registrar contraseñas, tokens, documentos o contenidos sensibles en logs.
- Pruebas de permisos, abuso de cargas, recuperación y retirada de contenido.
- Actualizaciones, gestión de incidentes, copias y restauraciones comprobadas.

## Controles de seguridad adicionales para el lanzamiento

Evaluación del 2026-10-03. Propuestas pendientes de implementación y validación. La detección de duplicados no sustituye estos controles.

| ID | Riesgo | Control propuesto | Evidencia requerida |
| --- | --- | --- | --- |
| SEC-001 | Acceso a anuncios, originales o documentos de otra cuenta/agencia | Denegar por defecto; autorización por objeto, gestor y rol en cada operación, incluyendo tareas de fondo | Pruebas cruzadas entre cuentas, agencias y miembros revocados |
| SEC-002 | Robo de cuenta y recuperación abusiva | MFA obligatorio en administración y gestores de agencia propuesto; recuperación segura, códigos caducables, límites de intentos y revocación de sesiones | Pruebas de reutilización de códigos, recuperación y cambio de factor |
| SEC-003 | Cambio fraudulento de contactos o gestor | Reautenticación para cambios sensibles, verificación del nuevo canal y auditoría; política de transferencia explícita | La edición no hereda verificación antigua ni elude moderación |
| SEC-004 | Código malicioso en descripciones y mensajes | Texto plano inicialmente o sanitización estricta de formato permitido; escape HTML, CSRF y CSP ajustada a recursos necesarios | Probar contenido en ficha, panel de moderación y correo, incluidos fragmentos HTMX |
| SEC-005 | Archivo malicioso o consumo excesivo al procesar | Lista de formatos, tipo real, límites de bytes/píxeles, nombre interno y recodificación; workers limitados y actualizados | Archivos corruptos, extensiones falsas y consumo excesivo rechazados |
| SEC-006 | Filtración por almacenamiento/caché | Archivos privados separados, autorización para URLs temporales y caché de respuestas públicas exclusivamente | No se recuperan documentos mediante rutas públicas, miniaturas o otra sesión |
| SEC-007 | Saturación y costes por automatización | Límites por cuenta y acción, cuotas de cargas/borradores, concurrencia de trabajos y presupuesto de envíos; protección de borde según necesidad | Prueba de saturación, degradación controlada y alertas |
| SEC-008 | Acceso a red interna mediante URLs externas | Propuesta: cargas de archivos sin importación desde URL; si se añade, controles SSRF y restricciones de salida | No se accede a metadatos de nube ni servicios internos |
| SEC-009 | Compromiso de infraestructura o dependencia | Secretos externos a imágenes, redes privadas, privilegios mínimos, actualizaciones y revisión de dependencias/imágenes | Configuración de producción comprobada; servicios internos no públicos |
| SEC-010 | Pérdida de datos o incidente sin respuesta | Backups cifrados separados, recuperación documentada, alertas y revocación de accesos | Restauración real y simulación de incidentes |
| SEC-011 | Abuso de moderadores o soporte | Acceso mínimo a evidencias, registro de consultas/cambios, prohibir cuentas compartidas | Accesos atribuibles y revocables; soporte no cambia titularidad sin procedimiento |
| SEC-012 | Publicación o promoción por tareas/webhooks duplicados | Revalidar estado y permisos, idempotencia, firma de webhooks si hay pagos y validación servidor de importes | Reintentos y eventos fuera de orden no duplican cobros ni publican retirados |

### Cuentas y agencias

Recomendar MFA también a particulares; mecanismo concreto pendiente. No reducir MFA a un SMS sin analizar riesgos ni permitir que soporte lo retire solo con datos públicos. Si se añaden miembros de agencia, cuentas personales y roles; evitar compartir contraseña. Notificaciones de seguridad se diseñarán como flujo propio del producto, sin incorporar información sensible innecesaria al mensaje.

Cambiar de agencia, teléfono, identidad o fotografías puede invalidar verificaciones relacionadas. Revocar permisos al salir de una agencia y comprobar tareas pendientes que todavía pudieran modificar anuncios.

### Archivos y dominios

Propuesta inicial para fotografías: JPEG, PNG y WebP validados, sin SVG/HTML aportados por usuarios. Los documentos de verificación requieren otro flujo y política; no habilitar PDF por imitación de una competidora sin necesidad. Considerar análisis antimalware según formatos y riesgo, sin tratar un escáner como garantía de inocuidad.

Servir medios aportados por usuarios desde un origen separado, sin cookies de sesión ni permisos innecesarios. URLs temporales son credenciales portadoras durante su vigencia: no incluirlas en logs o analítica. Evitar que nombres de archivos y rutas revelen identidad legal.

### Abuso y observación

La observación de cuentas sospechosas acordada no desactiva límites ni autoriza publicar conflictos; ver [antiduplicados](10-unicidad-antiduplicados.md). IP o teléfono compartidos no demuestran bot. No exponer a solicitantes qué cuentas coinciden.

Reducir extracción masiva mediante límites y detección sin prometer impedir copia de contenido público. No usar `robots.txt` como defensa de acceso. Acceso a documentos y paneles se controla con autenticación y autorización.

### Configuración de producción

Desactivar debug, configurar hosts/orígenes admitidos, cookies Secure/HttpOnly/SameSite según flujo y HTTPS. Confiar en cabeceras de proxy solo desde el proxy controlado. Validar redirecciones de acceso para evitar destinos arbitrarios. Ajustar HSTS después de asegurar cobertura HTTPS de los dominios afectados.

No exponer PostgreSQL, Redis, cola ni paneles de métricas. No montar el socket Docker en la aplicación. Datos reales y backups no pasan al entorno de pruebas. Encripción de discos/backups y separación de claves no eliminan el riesgo de una aplicación comprometida: siguen siendo necesarios permisos y minimización.

### Verificación antes de lanzar

Priorizar pruebas de autorización entre agencias, recuperación, cambios de titularidad, subidas, publicación concurrente, cachés privadas, retirada y restauración. Revisión independiente de seguridad propuesta antes de producción por sensibilidad del dominio; alcance y presupuesto pendientes. Un escaneo automático no acredita por sí solo seguridad.

Ningún control figura implementado. Convertir esta matriz en criterios verificables de aceptación, con responsable y evidencia al desarrollar.

Fuentes técnicas oficiales consultadas:

- [OWASP: autorización](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
- [OWASP: autenticación multifactor y recuperación](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html).
- [OWASP: carga de archivos](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
- [OWASP: protección SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).
- [Django: checklist de despliegue](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).

## Protección de datos

Marco: RGPD y LOPDGDD. Revisar además LSSI y obligaciones del Reglamento de Servicios Digitales (DSA) según la clasificación efectiva del servicio y las excepciones aplicables.

El contenido podría revelar vida sexual u orientación sexual, categorías especiales de datos. Es una posibilidad que requiere análisis del tratamiento real; no clasificar automáticamente todas las fotografías o todos los anuncios como datos especiales. Antes de tratar estas categorías hay que identificar tanto una base del artículo 6 como una excepción válida del artículo 9 del RGPD.

Preparar inventario de tratamientos, finalidades, destinatarios, bases jurídicas y retención; información de privacidad; contratos con encargados; gestión de derechos; respuesta a brechas y evaluación de transferencias. Evaluar y documentar si procede una evaluación de impacto y un delegado de protección de datos; no dar por supuesta su obligatoriedad o su ausencia.

Verificación de edad e identidad: elegir un mecanismo proporcional, evitando almacenar copias de documentos si basta una evidencia mínima. Definir acceso, conservación, borrado y garantías del proveedor. No decidir reconocimiento facial ni biometría por defecto.

Diseñar retirada de anuncios y medios, purga de cachés y derivados y caducidad de copias de seguridad; documentar excepciones de conservación justificadas. No prometer eliminación inmediata de copias ajenas o de motores de búsqueda.

Cookies sujetas a consentimiento: bloquear antes de autorización, ofrecer aceptación y rechazo al mismo nivel y permitir revocación. Preferir una primera versión sin rastreadores innecesarios.

## Moderación

Propuesta: revisión antes de publicar y revisión de cambios relevantes. Definir qué modificaciones requieren nueva aprobación y qué versión permanece visible durante la revisión.

Diseñar un canal accesible de notificación, triaje urgente para menores, explotación o imágenes no consentidas, retirada o bloqueo, motivación de decisiones y revisión de reclamaciones según obligaciones aplicables. Conservar evidencias únicamente con finalidad, acceso y plazo justificados.

La verificación de una cuenta no demuestra por sí sola la autorización de todas las personas fotografiadas. Debe existir un procedimiento para esa autorización y para reclamaciones de terceros.

## Fuentes oficiales

Consultadas el 2026-10-03. Este documento no acredita cumplimiento ni sustituye la revisión del modelo concreto.

- [LOPDGDD, BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2018-16673).
- [LSSI, BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2002-13758).
- [Categorías especiales y bases de legitimación, AEPD](https://www.aepd.es/preguntas-frecuentes/2-tus-obligaciones-como-responsable-del-tratamiento/5-bases-legitimadoras-del-tratamiento/FAQ-0215-cuales-son-las-bases-de-legitimacion-para-el-tratamiento-de-las-categorias-especiales-de-datos).
- [Privacidad desde el diseño, CEPD](https://www.edpb.europa.eu/topics/ai-and-technology/privacy-by-design-and-by-default_en).
- [Guía de cookies, AEPD](https://www.aepd.es/guias/guia-cookies.pdf).
- [Evaluación de riesgos, AEPD](https://evalua-riesgo.aepd.es/).
- [DSA y contenido ilegal, Comisión Europea](https://digital-strategy.ec.europa.eu/en/factpages/tackling-illegal-content-online-digital-services-act).
