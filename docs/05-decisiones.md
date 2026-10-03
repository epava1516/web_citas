# Decisiones y preguntas pendientes

Actualizado: 2026-10-03.

Estado vigente: el usuario delega cerrar las decisiones. [Contrato funcional v1](14-contrato-funcional-v1.md) consolida la especificación y sustituye estados históricos pendientes sobre los puntos resueltos. Pendientes externos en su sección 12.

## Registro de decisiones

| ID | Estado | Decisión | Motivo |
| --- | --- | --- | --- |
| DEC-001 | Confirmado | Documentación normalizada en `docs/` | Petición expresa del usuario |
| DEC-002 | Confirmado | Planificar antes de implementar | Petición expresa del usuario |
| DEC-003 | Confirmado | Monolito modular con renderizado público en servidor | Base aceptada por el usuario el 2026-10-03 |
| DEC-004 | Confirmado parcialmente | Django como framework; versiones y dependencias exactas pendientes | Base aceptada; falta validar compatibilidad y soporte |
| DEC-005 | Propuesto | Separar identidad privada y perfil público | Reducir exposición de información |
| DEC-006 | Propuesto | Personas participantes y representadas exclusivamente adultas | Riesgos propios del servicio |
| DEC-007 | Pendiente | Política de contenido y verificación | Condiciona producto, proveedores y moderación |
| DEC-008 | Confirmado | PostgreSQL como base principal | Base aceptada por el usuario |
| DEC-009 | Confirmado parcialmente | Redis como broker de tareas; caché compartida según necesidad | Configuración, durabilidad y recuperación pendientes |
| DEC-010 | Confirmado | No incorporar MongoDB | Usuario lo descarta expresamente el 2026-10-03 |
| DEC-011 | Confirmado | Plantillas Django y HTMX para interacción puntual | Base aceptada por el usuario |
| DEC-012 | Confirmado | Celery con Redis para trabajos | Base aceptada; configuración y garantías pendientes |
| DEC-013 | Confirmado | Caddy como proxy HTTPS | Base aceptada por el usuario |
| DEC-014 | Confirmado | Pillow, almacenamiento compatible con S3, Docker Compose, CI/CD y observabilidad; CDN según necesidad | Base aceptada; proveedores, herramientas concretas y versiones pendientes |
| DEC-015 | Confirmado | Equivalencia funcional de perfiles, servicios y categorías y búsqueda textual/geográfica | Petición del usuario; catálogo exacto pendiente |
| DEC-016 | Propuesto | Separar árbol administrativo, barrios/zonas y códigos postales | CP no equivale a barrio ni a municipio |
| DEC-017 | Confirmado | Controles antiduplicación por imágenes y teléfonos | Petición del usuario |
| DEC-018 | Propuesto | SHA-256 en servidor, teléfono E.164 y restricciones de integridad en PostgreSQL | Detectar igualdad exacta y proteger frente a publicaciones simultáneas |
| DEC-019 | Pendiente parcialmente | Fotos compartidas y anuncios activos por persona; teléfono compartido gestionado por agencia | Se concreta modelo de agencia; quedan excepciones y cardinalidades |
| DEC-020 | Confirmado | Teléfono compartido entre personas anunciado desde el mismo perfil de agencia | Criterio indicado por el usuario; verificación y transiciones pendientes |
| DEC-021 | Confirmado | Detección exacta y visual de imágenes, incluyendo recortes | Usuario acepta el enfoque por capas; bibliotecas y umbrales pendientes |
| DEC-022 | Confirmado | No bloquear inmediatamente la cuenta por duplicación de imágenes; observar intentos y volumen de perfiles | Usuario solicita obtener señales de automatización |
| DEC-023 | Propuesto | Permitir borradores limitados y retener publicaciones sospechosas para revisión | Observar comportamiento sin publicar contenido conflictivo |
| DEC-024 | Confirmado | Toda España y accesibilidad en inglés | Usuario concreta territorio e idioma adicional; traducción de anuncios pendiente |
| DEC-025 | Confirmado | Una publicación por persona/modelo; agencias gestionan varias personas, una publicación por cada una | Usuario concreta cardinalidad; controles visuales apoyan detección sin garantizarla |
| DEC-026 | Confirmado | Ciudad/localidad obligatoria, CP opcional recomendado encarecidamente | Usuario concreta precisión mínima |
| DEC-027 | Confirmado | Preparación para monetización comparable a referencias, tarifas por definir tras estudio | No implica activar cobros ni aprobar planes específicos |
| DEC-028 | Definido por delegación | Moderación híbrida, revisión humana y conflictos pendientes sin suspensión automática | Concretado en contrato v1 |
| DEC-029 | Definido por delegación | ES/EN, descripción alternativa opcional sin traducción automática | Concretado en contrato v1 |
| DEC-030 | Definido por delegación | Contacto público autorizado por teléfono/WhatsApp/Telegram; email de cuenta privado | Concretado en contrato v1 |
| DEC-031 | Definido por delegación | Lanzamiento gratuito y productos Premium/Top/Autosubida preparados sin venta activa | Tarifas y contratación de pagos posteriores |
| DEC-032 | Definido por delegación | Catálogo inicial de modelaje, acompañamiento social y masajes no sexuales; contenido no explícito | Ley General de Publicidad condiciona equivalencia con referencias; revisión jurídica pendiente |
| DEC-033 | Definido por delegación | MFA de agencias/equipo, autorización individual y transferencia revisada | Concretado en contrato v1 |
| DEC-034 | Definido por delegación | MVP con favoritos, sin mapas/chat/reseñas/vídeos ni cobros reales | Concretado en contrato v1 |
| DEC-035 | Confirmado | Condiciones de publicación y apartado legal público que expliquen responsabilidades, normas y postura de la plataforma | Confirmación del usuario; especificación en documento 15 |
| DEC-036 | Confirmado | Desarrollo cruzado frontend/backend y tests tempranos; terminación separada al estabilizar interacciones, bajo un contrato de inicio a final | Petición del usuario; documento 16 fija gate GS-01 y validación final |

La aceptación de la base tecnológica no resuelve las preguntas funcionales o legales ni constituye una instrucción para empezar a implementar. La fase actual sigue siendo planificación.

## Preguntas prioritarias

La tabla siguiente es histórica: la delegación posterior resuelve decisiones funcionales en contrato v1. No volver a presentar estos puntos como preguntas abiertas salvo que el usuario cambie el alcance. Identidad del operador, contratación y evidencias reales siguen pendientes externos.

| ID | Pregunta | Qué condiciona |
| --- | --- | --- |
| PRE-001 | ¿Modelos profesionales, acompañamiento social, servicios sexuales o varias categorías? ¿Contenido explícito? | Legalidad por territorio, política de contenido, SEO y proveedores |
| PRE-002 | Toda España e inglés confirmados. ¿Anuncios traducidos por autor, automáticamente o conservados en idioma original? | Búsqueda, contenido y SEO multilingüe |
| PRE-003 | Agencias admitidas para gestión compartida. ¿Qué pruebas de autorización, miembros y límites tendrá cada gestor? | Propiedad, autorización, roles y verificación |
| PRE-004 | Monetización comparable pendiente de estudio: ¿qué planes y reglas, duración, orden, pagos y condiciones? Tarifas pueden fijarse después | Facturación y ordenación |
| PRE-005 | ¿Quién moderará y con qué capacidad y horario? | Viabilidad operativa y respuesta a incidentes |
| PRE-006 | Referencias identificadas: LoquoSex, MálagaCitas.es y Destacamos. ¿Qué ventaja concreta priorizamos? | Prioridades de producto y SEO |
| PRE-007 | ¿Equipo, experiencia, presupuesto operativo y fecha objetivo? | Stack, proveedores y alcance del MVP |
| PRE-008 | ¿Qué contactos se admitirán y serán públicos o estarán tras acceso? | Privacidad, abuso y conversión |
| PRE-009 | ¿Cómo verificar edad, titularidad y autorización sin conservar datos excesivos? | Proveedor, controles y retención |
| PRE-010 | ¿MFA obligatorio para agencias y qué recuperación admitiremos? | Protección de cuentas gestoras |
| PRE-011 | ¿Se mantienen publicaciones sospechosas pendientes de revisión y cuántos borradores/cargas se permiten? | Observación de cuentas y abuso |
| PRE-012 | ¿Quién atiende incidentes y qué RPO/RTO y capacidad de moderación necesitamos? | Recursos, presupuesto y operación |

## Plan de seguridad preparado

Documentados paquetes IMP-001 a IMP-011 y gates G-01 a G-08 en `11-plan-seguridad-validacion.md`, y procedimientos OP-001 a OP-009 en `12-operacion-seguridad.md`. Todos pendientes de ejecución. Pedir documentación no equivale a seleccionar herramientas, aprobar umbrales o comenzar implementación.

## Próximos entregables

Lista de cierre del contrato funcional en [Decisiones para el contrato de desarrollo](13-cierre-contrato-desarrollo.md): CON-001 a CON-012. Diferencia decisiones de alcance, elecciones técnicas delegables y condiciones previas a producción.

1. Resolver categorías, territorio y tipo de anunciante.
2. Definir política de publicación y flujo de moderación/verificación.
3. Cerrar MVP y modelo de datos con campos públicos y privados.
4. Comparar stacks y proveedores con fuentes oficiales y costes.
5. Registrar arquitectura elegida mediante ADR.
6. Preparar plan de implementación, despliegue y criterios de lanzamiento.

La aplicación, infraestructura y controles siguen sin implementar.
