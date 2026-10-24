# CR-04 — Borradores, catálogos y geografía, interfaz v1

## Objetivo beta consolidado el 2026-10-20

La [versión funcional 1.1](../14-contrato-funcional-v1.md) sustituye para beta el catálogo y formulario profesionales de las interfaces del alfa descritas más abajo. Implementación pendiente B02–B03: un recorrido «Mi perfil» con datos personales de presentación, ubicación, contacto y fotos; sin selección obligatoria de categorías/servicios ni filas de tarifas. Mantener borrador, revisión exacta, límites de fotos, ES/EN, geografía, permisos y concurrencia. La agrupación romántica se asigna por sistema; no reutilizar IDs profesionales con significado nuevo ni borrar historial.

Los atributos físicos son opcionales y requieren antes de su alta contrato de opciones/unidades, límites, visibilidad, valor desconocido y revisión. Preferencias del visitante son otro ámbito; no añadirlas al formulario del anunciante ni imponerlas para publicar. Las fotos no se usan para inferir rasgos. La representación existente conserva autorización individual y un perfil por persona, no por cuenta. [Matriz de adaptación y evidencia requerida](../104-consolidacion-contrato-beta-b00b01-20261020.md).

Contrato de campos beta: `profile_type` es opcional, valores vacíos/woman/man/trans/other y ninguna asignación automática. `show_trans_label` es un booleano de presentación independiente, predeterminado false: significa no mostrar esa etiqueta, no afirmar que la persona no sea trans. Sólo se publica cuando se marca expresamente y se aprueba la revisión. Puede combinarse con mujer, hombre u otro tipo, o con tipo sin indicar; no inferirlo de imágenes/texto. La opción de filtro trans reúne el tipo declarado trans y la etiqueta seleccionada, conservando OR dentro del filtro. Copia, rectificación, supresión y recuperación deben conservar su ámbito. No añade edad pública, biometría, raza, etnia ni nacionalidad.

Las rutas, cuatro pasos, campos profesionales y evidencias siguientes describen el alfa. No se ha aplicado una migración ni cambiado el comportamiento HTTP al consolidar este requisito. [Copia del contrato anterior](../17-historial/2026-10-20-04-borradores-catalogo-geografia-antes-beta-b00b01.md).

## Rutas y pasos

- POST /{es|en}/person/{id}/listing/start/: gestor autorizado, CSRF, crea o retoma anuncio/borrador; 302 al paso1, 404 ajeno, 409 cuota. Persona bloqueada en PostgreSQL: una Listing por persona mediante OneToOne, sin clones por ciudad/categoría/agencia.
- GET/POST /{es|en}/draft/{revision}/{step}/: privado, pasos1–4, 404 inexistente/ajeno, 409 revisión obsoleta/inmutable o edición concurrente, 400 datos inválidos. GET conserva datos, POST exitoso redirige al paso siguiente. Todos los POST validan gestor otra vez dentro de transacción.
- Paso1: título, descripción, ES/EN original/alternativa, tipo declarado, categorías/servicios, región/provincia/municipio, CP, zona, idiomas, disponibilidad y desplazamientos.
- Paso2: teléfono obtenido de PhoneClaim comprobada del gestor (no del POST), WhatsApp, usuario Telegram; aviso de exposición y obligaciones de publicación versionadas. Tarifas como filas.
- Paso3: fotografías, pendiente CR-05. Paso4: resumen privado, todavía sin envío/publicación hasta CR-05/06. No simular un envío completo.

Wireframe: barra de cuatro pasos → formulario con etiquetas/errores → guardar y continuar. Volver al paso anterior conserva datos. Revisión pendiente nunca es una ficha pública.

## Validación y concurrencia

Título120 caracteres, descripciones6000; texto plano escapado, enlaces/contactos fuera de campos específicos se rechazan. Catálogos activos, categorías y servicios compatibles. Tipos declarados woman/man/trans/other; idiomas ES/EN/FR/DE/IT/PT; días ISO1–7, franjas morning/afternoon/evening. No raza, etnia o nacionalidad como filtros.

Región/provincia/municipio coherentes, zona del municipio y CP asociado. CP opcional muy recomendado; se rechaza precisión no habilitada para exposición pública. No coordenadas/domicilio. Código postal conserva cinco dígitos y puede asociarse a varios municipios. JavaScript local filtra selectores y limpia selecciones incompatibles; sin JavaScript conserva validación completa servidor y selectores HTML.

`edit_version` evita que una pestaña sobrescriba otra. Revision mantiene manager_version y estado; solo draft vigente editable. Máximo tres revisiones draft/processing/pending por persona bajo el manager_version vigente. Start concurrente retoma la misma revisión, no incrementa cantidad de anuncios.

Tarifas: fixed/from con Decimal positivo; consult exige importe vacío, EUR fijado servidor; concepto80 caracteres, duración opcional1–10080 minutos. Formset máximo10 filas, adición/edición/eliminación. Restricción PostgreSQL evita fixed/from nulo o no positivo. La duración no implica reserva o pago por servicios.

Consentimiento del anunciante distingue lectura de privacidad, términos de cuenta, autorización del representado y obligaciones de publicación. Aceptación publish registra usuario, documento/idioma/versión y agencia cuando corresponde. Representación conserva tipo e ID gestor histórico, no solo gestor actual del perfil.

## Catálogo e importación

Módulos Django `apps.catalog` y `apps.listings` separados de cuentas/verificación. Categorías iniciales modeling/social/wellness; servicios administrados con slug estable y etiquetas ES/EN. `seed_catalog` es idempotente y bloqueado en producción: crea catálogo y dos ciudades DEMO, sin acreditar cobertura nacional.

`uv run python manage.py import_geography archivo.json` importa atómicamente un dataset local; metadatos source obligatorios: key, origin, license, version y synthetic booleano. Arrays regions/provinces/municipalities; postal_codes/zones opcionales. Relaciones mediante códigos estables: province.region, municipality.province, postal.municipalities, zone.municipality. Importación repetida conserva IDs; error de correspondencia revierte todo. Por defecto un CP importado tiene public_safe=false hasta evaluación de privacidad. Producción rechaza fuente sintética.

Metadatos declarados no prueban licencia/revisión jurídica ni cobertura. Dataset nacional autorizado sigue pendiente externo. Ver formato reproducible y casos de error en tests/test_geography_import.py; no consultar/extractar masivamente Correos sin permiso.

## Dependencias pendientes

Fotos y estados de procesamiento CR-05, aprobación y revisión inmutable CR-06, filtros/índice público CR-07. La interfaz sigue indicando esas partes pendientes; no sustituirlas por respuestas ficticias. Títulos, etiquetas y accesibilidad se refinan en B-F después de conectar todos los flujos.

Tras cambiar gestor, editar, consultar estado y enviar una revisión de manager_version anterior devuelve404, incluido el titular que vuelve a gestionar su propia persona. El histórico permanece para auditoría autorizada, sin copiar contactos/textos/fotos al nuevo gestor. Las revisiones antiguas no consumen la cuota de tres vigente; una corrección puede copiar una revisión del gestor actual.


Los conceptos de tarifas aplican la validación de texto público compartida (`RateForm.clean_concept`): teléfonos, URL/www y menciones se rechazan en el formulario y en la validación de publicación. No sustituyen los canales de contacto autorizados.
