# Apartado legal público y condiciones de publicación

Fecha: 2026-10-03. Estado: alcance confirmado; especificación y borradores sujetos a datos reales del operador y revisión jurídica antes de producción.

## Objetivo confirmado

El usuario confirma que la plataforma debe publicar un apartado legal accesible que explique su postura y reglas frente a contenidos/servicios prohibidos. Los anunciantes aceptarán condiciones de publicación con responsabilidades por el contenido que aportan. La implementación y aceptación local se consultan en [seguimiento17](17-seguimiento-desarrollo.md) y [contrato de cuentas/legal](contratos/01-cuentas-legal.md); la existencia de pantallas y textos sintéticos no sustituye los datos del operador ni la revisión jurídica pendiente.

Este documento amplía el contrato funcional v1. La responsabilidad del anunciante no sustituye las obligaciones propias del operador, ni la aceptación convierte un contenido ilícito en lícito. No llamar consumidor automáticamente a cualquier profesional/agencia.

## Páginas y acceso

Rutas equivalentes en español e inglés bajo `/es/legal/` y `/en/legal/`, enlazadas permanentemente desde footer, ayuda y formularios relevantes, sin exigir registro. Cada documento muestra título, versión, publicación, entrada en vigor, idioma y enlace descargable/imprimible. No presentar textos legales incompletos como definitivos en producción.

| Documento/ruta relativa | Contenido necesario |
| --- | --- |
| `aviso-legal/` | Identidad y datos exigibles del operador, domicilio/contacto y demás información aplicable según actividad |
| `condiciones-de-uso/` | Funcionamiento, acceso, cuentas, roles, seguridad, suspensión, reclamaciones y derechos que no se excluyen |
| `condiciones-de-publicacion/` | Obligaciones de anunciante/agencia, autorización, imágenes, duplicados, edición y retirada |
| `politica-de-contenido/` | Categorías admitidas y ejemplos comprensibles de contenido prohibido; aplicación a texto, fotos, servicios y contactos |
| `privacidad/` | Tratamientos reales, finalidades, bases, derechos, retención, encargados/destinatarios y transferencias |
| `cookies/` | Tecnologías reales y finalidades, duración, terceros y gestión de preferencias cuando se requiera |
| `seguridad-y-proteccion/` | Postura pública sobre adultos, consentimiento, suplantación, explotación y acceso a ayuda; sin exponer detalles internos de detección |
| `denuncias-y-reclamaciones/` | Notificación de contenido presuntamente ilícito, revisión de decisiones, requisitos y contactos |
| `derechos-de-datos/` | Cómo ejercer derechos y solicitar retirada de datos/imágenes, con información y verificación proporcionales |
| `condiciones-comerciales/` | Antes de activar cobros: planes, duración, precios/impuestos, pagos, cancelaciones, desistimiento/devoluciones aplicables y reclamaciones |

Las traducciones deben revisarse para equivalencia. No introducir una cláusula automática que niegue derechos al lector de la versión inglesa. Publicar también versión/idioma exactos aceptados por cada usuario.

## Postura pública: borrador de texto

> Esta plataforma permite publicar anuncios de modelaje, acompañamiento social y masajes de bienestar dentro de sus normas y de la legislación aplicable. Solo admitimos personas adultas y contenido publicado con autorización de las personas representadas y de los titulares de sus derechos.
>
> No admitimos publicidad de servicios sexuales remunerados, explotación, coacción, suplantación ni imágenes publicadas sin autorización. Estas reglas se aplican al contenido real del anuncio, aunque se utilicen expresiones indirectas.
>
> Revisamos publicaciones, atendemos denuncias y podemos restringir contenidos o cuentas conforme a nuestras condiciones y a las obligaciones legales aplicables. Puedes denunciar un perfil o solicitar ayuda desde los enlaces de cada ficha y del apartado legal.

Borrador para adaptar al nombre real, mecanismos y capacidad implementados. «Revisamos» solo se usa en la web cuando el flujo exista y se cumpla. No afirmar «todos los perfiles son auténticos», «seguridad garantizada», «cumplimos toda la legislación» o «no somos responsables de nada».

## Condiciones de publicación: obligaciones a redactar

1. El anunciante declara ser mayor de edad y publicar datos veraces; no suplanta identidad ni evade restricciones creando cuentas o perfiles duplicados.
2. Tiene autorización para representar a cada persona y para publicar las fotos/textos. La agencia debe acreditar esa representación mediante el flujo definido; aceptar las condiciones no es por sí solo evidencia de autorización de terceros.
3. No publica menores, explotación, coacción, contenido no consentido, ofertas sexuales remuneradas o material excluido por la política. No usa enlaces, contactos o eufemismos para eludir prohibiciones.
4. Mantiene datos de contacto autorizados y vigentes. Una publicación por persona; teléfonos de agencia compartidos solo en perfiles gestionados legítimamente.
5. Corrige datos y atiende verificaciones/reclamaciones. Notifica cambios de representación y respeta revocación sin retener el control del perfil.
6. Concede únicamente la licencia necesaria para almacenar, procesar, adaptar técnicamente y mostrar contenido en la plataforma. No autoriza automáticamente promoción externa, venta de imágenes o entrenamiento de modelos.
7. Asume responsabilidad por incumplimientos propios en los términos legalmente procedentes. Las consecuencias no excluyen derechos imperativos ni responsabilidades del operador. No imponer multas, indemnización ilimitada o renuncia a reclamar por defecto.
8. Puede recibir rechazo motivado, retirada de contenido, limitaciones o suspensión proporcionadas, con revisión de decisión cuando corresponda. Los duplicados visuales no ocasionan suspensión automática de la cuenta por sí solos.

Revisión jurídica necesaria de licencias, consecuencias y diferencias entre usuarios profesionales/consumidores. No copiar condiciones de una competidora ni tratar sus cláusulas como validadas.

## Aceptación y declaraciones en producto

### Registro

- Casilla sin premarcar: «He leído y acepto las condiciones de uso», con enlace y versión vigente.
- Información de privacidad resumida junto al formulario y enlace al texto completo. Informar no equivale a obtener consentimiento para todas las finalidades.
- No añadir marketing como aceptación obligatoria del registro. Sin marketing en MVP.

### Alta de anunciante/agencia

- Aceptación específica de condiciones de publicación y política de contenido, no solo navegación de un enlace.
- Explicación de representación, mayoría de edad y autorización de imágenes; comprobación efectiva por flujo separado.
- Activación de contactos públicos con información de exposición. No mezclarlo con permisos de marketing, cookies o usos promocionales adicionales.

### Envío de anuncio y cambios sensibles

- Resumen de contenido, servicios, contactos, tarifas y precisión de ubicación.
- Declaración expresa sin premarcar sobre datos veraces y derechos/autorización del contenido de la revisión enviada.
- Validación en servidor de condiciones aceptadas y verificaciones exigidas. No permitir eludir aceptación manipulando petición o reenviando un borrador antiguo.
- Si faltan documentos vigentes o hay conflicto, no publicar automáticamente. La aceptación no desactiva moderación.

### Cambios de condiciones

Versiones inmutables y fecha efectiva. Notificar cambios importantes según normativa/relación contractual; pedir nueva aceptación cuando corresponda y ofrecer salida/retirada sin ocultar el cambio. No aplicar modificaciones retroactivas silenciosas ni renovar consentimientos específicos por el mero uso de la web.

## Modelo de datos y trazabilidad propuesto

| Entidad | Datos mínimos |
| --- | --- |
| Documento legal | Tipo, versión, idioma, texto/snapshot, hash de integridad, fechas y estado borrador/publicado/retirado |
| Aceptación contractual | Cuenta, rol/agencia cuando proceda, documento/idioma exacto, instante UTC, flujo y revisión/acción relacionada |
| Declaración de publicación | Actor, revisión del anuncio, texto/version de declaración y fecha |
| Autorización de representación | Persona representada, gestor autorizado, alcance, referencia a comprobación, fecha y revocación |
| Consentimiento de tratamiento cuando aplique | Finalidad específica, información mostrada, acción, estado y retirada; separado del contrato |

Registro servidor, integridad y conservación por finalidad. No guardar IP, user-agent o fingerprint por defecto solo por «prueba legal»; cualquier incorporación necesita justificación y retención. El hash del documento acredita integridad técnica, no prueba por sí solo identidad del aceptante ni convierte el registro en firma electrónica cualificada.

No editar el texto de versiones ya aceptadas. Evitar guardar contratos repetidos completos por usuario: conservar snapshot versionado y referencia. Derechos/supresión pueden exigir conservación restringida de ciertas evidencias con justificación, no permanencia pública.

## Denuncias, solicitudes y reclamaciones

En cada ficha botón «Denunciar», que identifica automáticamente perfil/revisión. Formulario sin registro obligatorio: razón, URL/referencia, explicación y contacto opcional para reclamaciones generales. Si se formaliza notificación de contenido ilícito bajo DSA, recoger los elementos exigidos por el art. 16 —incluida identificación/contacto cuando proceda y sus excepciones— y explicación de buena fe. No afirmar que el contacto siempre puede omitirse en ese procedimiento formal.

Separar denuncia de contenido, reclamación contra una decisión y ejercicio de derechos de datos. Permitir entradas sencillas sin confundir procedimientos/plazos. No publicar denuncias ni identificar al denunciante frente a otros usuarios salvo obligación o necesidad jurídicamente justificada.

Acuse y seguimiento cuando hay canal de respuesta; prioridad a menores, explotación e imágenes no consentidas. Decisiones motivadas y vía de revisión aplicable. Cooperación con autoridades por procedimiento definido, sin prometer cesión automática de todos los datos ante cualquier reporte.

## Criterios de aceptación de desarrollo

- Todas las páginas se abren sin sesión en ES/EN, son legibles en móvil y se pueden imprimir/guardar.
- Documento público enlazado coincide con versión/idioma aceptado; las versiones anteriores pueden recuperarse por quien las aceptó según política.
- Registro/publicación rechazan aceptación ausente, manipulada o versión inválida de forma controlada.
- Cambio importante activa flujo de notificación/nueva aceptación configurado; un fallo no simula aceptación.
- Denunciar no exige crear cuenta y envía a cola adecuada sin exponer datos a terceros.
- Información de privacidad por capas y consentimientos específicos separados del contrato/cookies.
- No hay placeholders de operador, servicios no implementados o garantías generales de legalidad en textos finales de producción.
- Pruebas cubren concurrencia, versiones, idioma, agencia/actor, revocación y borrado/conservación de evidencias.

## Entregables finales y fuentes

Entrega técnica local: páginas ES/EN, versiones y mecanismos de aceptación, registro de evidencias, formularios/colas de denuncia y derechos, decisiones y procedimiento de ensayo coherentes con textos/datos sintéticos identificados. Aplicar los criterios técnicos anteriores sobre la versión común, sin exigir datos reales del operador o dictamen jurídico para probar el mecanismo.

Preparación de producción: textos definitivos con datos reales y revisión jurídica, traducciones revisadas y procedimiento operativo real coherente con lo publicado. Mantener los controles de aceptación y evidencias ya verificados. Publicar políticas sin mecanismos no satisface este alcance; fixture no acredita aprobación jurídica. Separación conforme a [contrato16 v1.6](16-contrato-ejecucion-desarrollo.md#11-entregables-y-definición-de-terminado).

- [LSSI: identificación e información contractual](https://www.boe.es/buscar/act.php?id=BOE-A-2002-13758).
- [DSA: condiciones y notificación de contenido](https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX%3A32022R2065).
- [AEPD: deber de informar y separación del consentimiento](https://www.aepd.es/preguntas-frecuentes/2-tus-obligaciones-como-responsable-del-tratamiento/6-el-deber-de-informacion).
- [Ley General de Publicidad](https://www.boe.es/buscar/act.php?id=BOE-A-1988-26156).

Implementación y aceptación local actuales: [seguimiento17](17-seguimiento-desarrollo.md) y [contrato de cuentas/legal](contratos/01-cuentas-legal.md). Textos productivos siguen pendientes de completar y revisar. [Copia anterior a consolidación](17-historial/2026-10-09-15-apartado-legal-publico-antes-consolidacion-contrato.md) conserva la redacción y estado originales; no es una declaración vigente de ausencia de implementación.
