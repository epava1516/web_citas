# Producto y alcance

Actualizado: 2026-10-03.

Especificación vigente: [Contrato funcional v1](14-contrato-funcional-v1.md), definida por delegación expresa del usuario. Sustituye las propuestas posteriores en puntos resueltos: MVP, catálogo, publicación, cuentas, contactos y monetización preparada.

## Requisitos confirmados

| ID | Requisito |
| --- | --- |
| REQ-001 | Web de anuncios clasificados para modelos y acompañantes. |
| REQ-002 | Registro de usuarios. |
| REQ-003 | Los usuarios pueden registrar sus anuncios. |
| REQ-004 | Anuncios con descripciones, fotos, tarifas y vías de contacto. |
| REQ-005 | Proyecto dockerizable y preparado para una puesta en producción sencilla. |
| REQ-006 | Seguridad y cumplimiento de protección de datos española y europea desde el diseño. |
| REQ-007 | Buen SEO y aspiración a superar a las competidoras. |
| REQ-008 | Documentar lo relevante de forma normalizada en `docs/`. |
| REQ-009 | Planificar y debatir antes de implementar la aplicación. |
| REQ-010 | Usar LoquoSex, MálagaCitas y destacamos.net como referencias de producto; análisis en `07-referencias-competencia.md`. |
| REQ-011 | Almacenar tipos de personas/perfiles, servicios y categorías equivalentes a las referencias; catálogo exacto y reglas pendientes. |
| REQ-012 | Búsqueda por descripción y filtros por comunidad autónoma, provincia, ciudad/localidad y zona. |
| REQ-013 | Considerar código postal para precisión geográfica de zona; relación con barrios y obligatoriedad por concretar. |
| REQ-014 | Prevenir anuncios duplicados mediante controles por hashes de fotografías y teléfonos normalizados; alcance de exclusividad y excepciones pendientes. |
| REQ-015 | Si varias personas comparten un teléfono de gestión, definir al gestor como agencia y publicar sus anuncios a través del mismo perfil de agencia. |
| REQ-016 | Detectar duplicados visuales, incluidas versiones recomprimidas/recortadas, con evaluación de coincidencias y falsos positivos. |
| REQ-017 | Evitar bloqueo inmediato de cuenta por coincidencia de imágenes; observar intentos, volumen de perfiles y señales de automatización. El comportamiento de publicación queda definido como propuesta en `10-unicidad-antiduplicados.md`. |
| REQ-018 | Cobertura de toda España desde el lanzamiento; web accesible también en inglés. Estrategia de traducción de anuncios pendiente. |
| REQ-019 | Una publicación por persona/modelo; una agencia puede gestionar varias, una por cada persona representada. No es excepción para duplicar anuncios de una misma persona. |
| REQ-020 | Ubicación obligatoria como mínimo hasta ciudad/localidad; CP recomendado encarecidamente, opcional. |
| REQ-021 | Preparar el sistema para monetización comparable a las referencias, sin fijar aún tarifas, planes, pagos o reglas de activación. |
| REQ-022 | Apartado legal público ES/EN con postura de la plataforma, normas y canales de denuncia/derechos, y condiciones de publicación aceptadas expresamente por anunciantes con registro de versión. |

## MVP propuesto

- Registro, verificación del correo, acceso, recuperación y cierre de cuenta.
- Gestión de anuncios propios: borrador, envío a revisión, publicación, pausa y retirada.
- Fotografías con validación, ordenación y eliminación.
- Tarifas estructuradas: importe decimal, moneda y concepto; unidades pendientes de definir.
- Contactos elegidos explícitamente por la persona anunciante, con explicación de su exposición pública.
- Listados, búsqueda y filtros geográficos con páginas de detalle.
- Panel de moderación y gestión de denuncias, con decisiones registradas.
- Flujo de verificación de mayoría de edad, autorización para publicar y derechos sobre las imágenes; mecanismo pendiente.
- Gestión de privacidad y derechos de las personas.

Propuesta: reservar chat, reseñas, reservas, pagos y recomendaciones personalizadas para fases posteriores, salvo que el modelo de negocio los haga imprescindibles.

## Modelo de dominio preliminar

Separar cuenta privada, perfil público y anuncio. Se admite gestión de varias personas desde un mismo perfil de agencia cuando comparten teléfono de gestión. Cada persona representada debe mantener sus datos y verificaciones separados; ver `10-unicidad-antiduplicados.md`. Una publicación por persona/modelo, tanto independiente como representada por agencia. Versiones, archivo y renovación no crean otra publicación activa de esa misma persona. Transferencias, miembros de agencia y verificaciones siguen pendientes.

Entidades candidatas: cuenta, perfil público, anuncio, fotografía, tarifa, contacto, ubicación, comprobación de verificación, denuncia, decisión de moderación y registro de auditoría. Registrar consentimientos cuando sean la base aplicable y otras autorizaciones con su finalidad y versión; no usar un consentimiento genérico para todo.

La identidad legal y las evidencias de verificación no forman parte del perfil público. La ubicación inicial propuesta es ciudad o zona, sin domicilio ni coordenadas exactas.

## Condiciones de lanzamiento propuestas

Definir contenido admitido, territorios y tratamiento de anuncios de acompañamiento o servicios sexuales. Propuesta: participación y personas representadas exclusivamente adultas, prohibición de explotación, coacción, suplantación e imágenes sin autorización. No se ha definido todavía si se admite contenido explícito.

Estas condiciones requieren procedimientos operativos y mecanismos comprobables, no solo una casilla de aceptación.
