# Decisiones para cerrar el contrato de desarrollo

Actualizado: 2026-10-03. Estado: lista de cierre, no contrato final aprobado.

Actualización: el usuario delega decisiones; los puntos funcionales se resuelven en [Contrato funcional v1](14-contrato-funcional-v1.md). Las tablas/listas posteriores se conservan como checklist histórico. Pendientes externos en la sección 12 del contrato.

## Interpretación

Se entiende contrato de desarrollo como especificación de alcance, reglas funcionales, arquitectura, entregables y criterios de aceptación. Si se necesita además contrato mercantil con un proveedor, definir partes, precio, pagos, propiedad intelectual, responsabilidades, mantenimiento y condiciones con revisión jurídica.

La base tecnológica está aceptada. El principal trabajo pendiente es cerrar comportamiento, alcance y operación. No exigir resolver todos los ajustes técnicos antes de desarrollar: sí identificar quién los decide, cuándo y con qué evidencia.

## Decisiones de alcance necesarias antes del contrato final

| ID | Decisión | Qué debe quedar escrito | Recomendación inicial, no aprobada |
| --- | --- | --- | --- |
| CON-001 | Países, idiomas y operador | Territorio destinatario, idiomas de interfaz/contenido y responsable del servicio | España, interfaz en español; validar si es lanzamiento local o nacional |
| CON-002 | Categorías y contenido | Catálogo exacto y exclusiones; servicios, atributos y contenido explícito admitido; exclusivamente adultos | Matriz normalizada con equivalencias a referencias, sin copiar todas sus categorías automáticamente |
| CON-003 | Cuentas y representación | Particulares/agencias, personas por gestor, miembros de equipo, permisos, autorizaciones y transferencias | Agencia gestiona perfiles individuales; un gestor activo por persona salvo excepción justificada |
| CON-004 | Perfil y anuncio | Cuántos anuncios activos por persona, categorías y ubicaciones; vigencia, renovación, pausa y eliminación | Un anuncio activo por persona inicialmente, con actualización y promociones separadas; pendiente de compatibilidad con catálogo |
| CON-005 | Publicación y duplicados | Cuándo se publica, qué cambios requieren revisión, qué se observa y qué se retiene | Revisión previa, borradores limitados y conflictos pendientes sin suspender automáticamente cuenta |
| CON-006 | Verificación | Edad, contacto, representación y fotos; manual/externa, datos mínimos y recuperación | Verificación proporcional separada por finalidad; MFA de gestores de agencia propuesto |
| CON-007 | Campos, contactos y geografía | Campos obligatorios/opcionales, tarifas, medios, canales públicos, zona/CP y ubicación principal/desplazamientos | Contacto externo, ubicación aproximada y tarifas estructuradas; no domicilio exacto |
| CON-008 | Búsqueda y orden | Filtros múltiples, relevancia, promociones, caducidad y páginas SEO | PostgreSQL, paginación y orden estable; no indexar todas las combinaciones |
| CON-009 | Monetización | Gratis/pago, destacados, suscripción, renovaciones, devoluciones e impuestos | Elegir publicación gratuita con destacados o lanzamiento sin cobros; no asumir ninguna opción |
| CON-010 | MVP y experiencia | Páginas/flujos, administración, funciones incluidas/excluidas y wireframes | Listados/fichas, publicación guiada, gestión y moderación; chat, reseñas y reservas posteriores propuestos |
| CON-011 | Recursos y operación | Presupuesto, volumen objetivo, disponibilidad, moderación, soporte y respuesta a incidentes | Dimensionar con capacidad real del equipo y pruebas, no con cifras de competidoras |
| CON-012 | Entrega y aceptación | Hitos, plazo, pruebas, evidencias, documentación y gestión de cambios | Entregas por módulos con demostración y criterios verificables; aceptación no basada solo en aspecto visual |

Estos puntos pueden resolverse por grupos. No convertir recomendaciones en acuerdos sin confirmación. No reutilizar «como la competidora» como requisito final: enumerar reglas y ejemplos concretos.

## Selecciones técnicas que pueden resolverse al preparar la base

Desarrollo/operaciones puede proponer versiones soportadas y compatibles, dependencias exactas, servidor WSGI/ASGI, herramientas de calidad y CI/CD y estructura de repositorio. Registrar mediante ADR las elecciones significativas.

Límites de archivos/trabajos, ventanas de abuso, umbrales visuales e índices deben tener valores iniciales configurables y pruebas; los valores finales pueden calibrarse durante implementación. No aplazar reglas funcionales de propiedad/publicación bajo la etiqueta de «ajuste técnico».

Proveedores de alojamiento, almacenamiento, correo y verificación deben evaluarse antes de implementar integraciones específicas por compatibilidad contractual con la actividad, coste y privacidad. Si pagos van en MVP, seleccionar y comprobar su viabilidad al cerrar esa parte del contrato, no al final del desarrollo.

## Condiciones antes de operar con datos reales o publicar

La revisión jurídica del contenido y tratamientos debe preceder al desarrollo de flujos que dependan de su admisibilidad. Contratos de proveedores, textos finales sobre tratamientos reales, mecanismos de derechos, retención, formación y procedimientos se completan y verifican antes de operar con datos reales según lo aplicable. El cumplimiento de todos los gates se exige para producción, no para crear scaffolding con datos sintéticos.

Las tareas de seguridad y operación están en `11-plan-seguridad-validacion.md` y `12-operacion-seguridad.md`. No confundir firma del alcance con acreditación de cumplimiento o seguridad.

## Estructura del futuro contrato funcional

1. Objetivo, usuarios, territorios y glosario.
2. Alcance del MVP y exclusiones.
3. Roles y matriz de permisos.
4. Modelo de entidades y campos públicos/privados.
5. Catálogo de perfiles, categorías, servicios y atributos.
6. Estados y reglas de publicación, verificación, duplicados y moderación.
7. Geografía, búsqueda, filtros, ordenación y SEO.
8. Flujos/pantallas y criterios de accesibilidad.
9. Monetización e integraciones, si entran en alcance.
10. Arquitectura, seguridad, privacidad y operación.
11. Capacidad objetivo, presupuesto y pruebas de carga.
12. Hitos, entregables, aceptación y procedimiento de cambios.

Cada regla debe tener ejemplo y criterio comprobable, y cada requisito enlazar pruebas/entregable. Las decisiones pendientes solo pueden mantenerse si no bloquean una fase y tienen responsable/plazo; no ocultar ambigüedades centrales en anexos.

## Estado actual

Acuerdos posteriores del usuario:

- Toda España y accesibilidad en inglés.
- Catálogo equivalente a competidoras; nombres, equivalencias y límites concretos requieren propuesta de catálogo, no volver a preguntar de forma genérica qué tipo de web se quiere.
- Perfiles independientes/agencias según modelo documentado; una publicación por persona/modelo, agencias con una por cada representado.
- Moderación necesaria, mecanismo por discutir.
- Ciudad/localidad como mínimo obligatorio y CP opcional recomendado encarecidamente.
- Preparar monetización comparable a referencias; planes y tarifas tras estudio. La estructura debe distinguir oferta comercial configurable, vigencia de promoción, pedido/pago y permisos, sin decidir aún sus reglas ni activar cobros.

No se ha preparado contrato final ni iniciado desarrollo. Las alternativas históricas de la tabla anterior quedan subordinadas a estos acuerdos.

## Lista reducida de pendientes

1. **Moderación y verificación:** revisión manual/automática/híbrida, momento de publicación, cambios que se revisan, edad/autorización, personal responsable y respuesta a denuncias. Mantener pendiente el contenido conflictivo mientras se observa la cuenta sigue propuesto.
2. **Catálogo definitivo:** preparar equivalencias de categorías, servicios y atributos de referencias, campos obligatorios/opcionales y reglas sobre fotos/vídeos y contenido explícito. La intención de equivalencia no fija admisibilidad jurídica de cada opción.
3. **Inglés:** interfaz bilingüe confirmada; definir si anuncios los traduce el autor, un sistema o se muestran en idioma original. Si se automatiza, revisar calidad, coste y privacidad del proveedor antes de enviar texto.
4. **Agencias:** comprobar autorización de cada modelo, transferencia/salida de agencia, miembros del equipo y sus permisos. No queda pendiente permitirlas ni cantidad de publicaciones.
5. **Contactos:** teléfono, WhatsApp, Telegram, correo u otros; decidir cuáles se admiten y si son públicos o requieren iniciar sesión. «Contacto» significa cómo un visitante habla con la persona/agencia, no datos legales privados.
6. **Monetización:** estudiar planes/promociones, duración, reglas de orden, límites, pagos, cancelaciones y condiciones. Tarifas configurables después; preparación no significa implementar cada sistema de créditos o suscripciones de competidoras.
7. **MVP/pantallas:** MVP es la primera versión utilizable que se entrega. Cerrar si incluye favoritos, mapas, vídeos, reseñas/chat y pagos o si quedan para más adelante. Pantallas son las páginas y pasos: buscar, ver ficha, registrarse, publicar/editar, gestionar agencia y moderar. Bocetos y ejemplos permitirán comprobar alcance sin fijar diseño visual al detalle ahora.
8. **Operación y entrega:** presupuesto mensual de infraestructura/servicios, quién atiende denuncias/incidentes, plazo e hitos y criterios para aceptar la entrega. Definir tolerancia a caída y pérdida de datos para elegir backups y recuperación. No se exige al usuario elegir manualmente todos los parámetros técnicos.
9. **Cierre legal y proveedores:** identificar operador y seleccionar proveedores compatibles con actividad, contratos/datos y licencias geográficas; revisar política de contenido y verificaciones. Documentos finales y pruebas completas son gates de producción, no requisitos para escribir código con datos sintéticos.

Números exactos de cargas, umbrales de similitud e índices se calibran durante desarrollo; no son nuevas decisiones de producto que deban bloquear el contrato.
