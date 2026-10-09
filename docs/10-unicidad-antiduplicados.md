# Unicidad y prevención de anuncios duplicados

Actualizado: 2026-10-03. Estado: controles por imágenes y teléfonos confirmados; política y diseño detallado propuestos.

Nota de lectura, 2026-10-09: evaluación de diseño inicial conservada. Las menciones inferiores a controles sin implementar, algoritmos sin aprobar y políticas propuestas describen ese corte. La implementación y los límites locales se documentan en [fotografías/coincidencias](contratos/05-fotografias-coincidencias.md), [verificación/representación](contratos/03-verificacion-representacion.md) y [moderación/publicación](contratos/06-moderacion-publicacion.md). Alcance funcional en [contrato14](14-contrato-funcional-v1.md); aceptación y pendientes vigentes en [seguimiento17](17-seguimiento-desarrollo.md). La coincidencia visual no acredita identidad ni autoriza suspensión automática.

Acuerdo posterior: una publicación por persona/modelo. Las agencias pueden gestionar varias personas con una publicación por cada una, sin excepción de duplicidad por persona. Las coincidencias visuales son señales de apoyo, no garantía de unicidad de personas. Pendientes: verificar representación y resolver transferencias o reclamaciones sin duplicación.

## Requisito confirmado

Evitar duplicación de anuncios usando unicidad/detección por hashes de imágenes subidas y teléfonos. No se ha fijado todavía si cada coincidencia bloquea publicación ni el alcance de la unicidad (cuenta, persona, anuncio activo o plataforma).

## Separar objetivos

- **Integridad:** impedir duplicados definidos por reglas exactas, incluso ante peticiones simultáneas.
- **Detección:** encontrar reutilización o similitud para revisión.
- **Almacenamiento:** evitar copias físicas innecesarias sin confundirlo con permiso de uso.

Una coincidencia de foto no demuestra autoría, fraude o identidad. Un teléfono compartido tampoco demuestra que dos perfiles representan la misma persona. Decidir política para agencias y terceros antes de imponer exclusividad global.

## Imágenes

Propuesta: SHA-256 calculado en servidor sobre los bytes recibidos, durante lectura limitada; no confiar en el hash suministrado por el cliente. No usar SHA-1 como nueva elección para este control.

Guardar algoritmo, hash, tamaño y versión de procesamiento. Comparar en PostgreSQL con índice. El mismo fichero genera la misma huella; recodificación, metadatos o modificaciones pueden producir otra. Por tanto, SHA-256 detecta duplicados exactos de archivo, no todos los duplicados visuales.

Segunda señal propuesta: hash de píxeles normalizados tras decodificar, aplicar orientación y fijar representación; versionar el algoritmo. Permite detectar parte de las variaciones de contenedor/metadatos, pero no garantiza detectar recortes, compresión o cambios visuales. Mantener límites de dimensiones, memoria y ejecución en procesamiento.

Evaluación posterior opcional: hash perceptual para similitud de imagen. No equivale a reconocimiento facial ni se propone identificar biométricamente personas. Calibrar umbrales sobre muestras autorizadas, medir falsos positivos y revisar coincidencias aproximadas; no bloquear automáticamente por parecido.

### Reglas propuestas

| Coincidencia | Acción propuesta |
| --- | --- |
| Misma foto repetida dentro de una revisión del anuncio | Rechazar la repetición o informar que ya está añadida |
| Misma foto al crear otra revisión del mismo anuncio | Permitir referencia existente, sin crear copia innecesaria |
| Foto reutilizada por el mismo perfil en otro anuncio | Aplicar reglas de anuncios activos; orientar a editar/renovar si es duplicado |
| Foto exacta en otro perfil/cuenta | Marcar conflicto y revisar autorización; no indicar al solicitante datos del otro perfil |
| Similitud perceptual | Señal de revisión, con procedimiento de reclamación |

Los archivos compartidos no deben exponer originales ni cruzar permisos. Si se deduplica físicamente, separar objeto de almacenamiento y relaciones de uso/autorización; borrar solo cuando no haya referencias válidas y lo permitan los plazos. Alternativa inicial más simple: mantener almacenamiento aislado y usar hashes únicamente para detección. Selección pendiente.

## Detección frente a recompresión y recorte

Evaluación del 2026-10-03 a petición del usuario. Propuesta, sin algoritmo aprobado ni benchmark realizado.

| Técnica | Caso que puede cubrir | Límite |
| --- | --- | --- |
| SHA-256 del archivo | Bytes idénticos | Cambia al recomprimir o modificar el archivo |
| Hash de píxeles normalizados | Diferencias de metadatos o contenedor si los píxeles normalizados coinciden | La recompresión con pérdida puede alterar píxeles |
| Hash perceptual global, por ejemplo pHash/PDQ | Similitud tras cambios de tamaño, recompresión y algunas variaciones visuales | La robustez depende de transformación y umbral; no asumir resistencia a recortes grandes |
| Hash resistente a recortes o huellas de regiones | Coincidencias parciales tras recortar | Recorte extremo, pérdida de detalle, fondos compartidos y segmentación pueden fallar |
| Descriptores locales SIFT/ORB con verificación geométrica | Comprobar si regiones de una imagen corresponden a otra | Más coste; pocos detalles o fondos repetidos pueden producir ambigüedad |

ImageHash ofrece hashes perceptuales y una variante resistente a recortes. OpenCV documenta correspondencias locales y homografía: es una técnica candidata para confirmar coincidencias parciales, no una garantía específica para nuestro catálogo. PDQ es otra opción de hash visual; no es requisito ni requiere compartir imágenes con Meta para ejecutar una implementación local.

### Propuesta de flujo

1. SHA-256 para igualdad exacta.
2. Huellas globales y regionales para recuperar candidatos de similitud en todo el catálogo, entre cuentas, agencias y teléfonos distintos.
3. Si hay indicio de recorte, comparación local y comprobación geométrica solo de candidatos, limitada por tiempo y recursos.
4. Conflictos entre perfiles pasan a revisión antes de publicar. La similitud no otorga titularidad a quien subió primero ni acredita identidad de la persona.

No filtrar candidatos solo por teléfono, agencia o categoría, ya que eso permitiría evadir detección cambiándolos. Tampoco exigir coincidencia de hash global para acceder a comprobación de recorte: un recorte puede cambiar mucho esa huella.

Procesar en Celery y guardar versión de algoritmo, huellas y evidencias de coincidencia en acceso restringido. No comparar cada imagen contra todas mediante verificación local: elegir recuperación indexada según volumen y medir candidatos omitidos y coste. Una huella perceptual se compara por distancia o segmentos, no por una restricción SQL de igualdad como `UNIQUE`.

Validar con imágenes autorizadas y transformaciones controladas: distintas calidades JPEG, redimensionado, recortes con distinta área conservada, espejo, rotación, marcas de agua y cambios de color. Incluir negativos difíciles: fotografías distintas de la misma sesión, fondos parecidos, plantillas y zonas poco detalladas. Medir precisión, sensibilidad, falsos bloqueos y latencia antes de fijar umbrales. No prometer un porcentaje de acierto sin esa evaluación.

El objetivo es identificar reutilización de fotografías, no reconocer personas mediante sus caras. No se propone reconocimiento facial ni un modelo genérico de parecido semántico como prueba de que dos imágenes son la misma fotografía.

Fuentes oficiales:

- [ImageHash: métodos perceptuales y resistentes a recortes](https://github.com/JohannesBuchner/imagehash/blob/master/README.rst).
- [OpenCV: correspondencias y verificación mediante homografía](https://docs.opencv.org/4.12.0/d1/de0/tutorial_py_feature_homography.html).
- [PDQ: implementación y comparación de huellas](https://github.com/facebook/ThreatExchange/blob/main/pdq/README.md).

## Teléfonos

Normalizar en formato internacional E.164 mediante biblioteca mantenida, indicando país cuando el usuario introduce formato nacional. Evitar reglas caseras basadas solo en quitar espacios o prefijos. Guardar identidad canónica del teléfono y presentación pública por separado.

Validación de formato/rangos no acredita que el número esté asignado, activo o bajo control del usuario. Si se requiere verificación, usar código con caducidad, intentos limitados y restricciones de envío; el control actual tampoco demuestra identidad ni evita números reciclados.

Modelar teléfono y sus asociaciones autorizadas con cuenta/perfil/anuncio. Un mismo teléfono debe tener una única representación normalizada en el catálogo, pero eso no implica que solo pueda asociarse a una persona. Distinguir teléfono principal, alternativos y canales que reutilizan el mismo número.

### Reglas pendientes

- ¿Un número queda reservado a una cuenta o puede autorizarse en varias?
- ¿Se admite un teléfono de agencia compartido por varios perfiles?
- ¿Un perfil puede tener anuncios activos en distintas categorías/ubicaciones?
- ¿Qué ocurre al cambiar de teléfono, cerrar una cuenta o reasignarse un número?

Propuesta mientras se resuelve: coincidencia telefónica entre cuentas o anuncios activa revisión y no publica silenciosamente otro duplicado. Si se acuerda un solo anuncio activo por persona, aplicar esa restricción al perfil/persona, no confiar únicamente en teléfono.

## Gestión compartida mediante agencia

El usuario establece como criterio que, cuando varias personas compartan teléfono de gestión, el gestor se defina como agencia y publique los anuncios a través del mismo perfil de agencia. Esta regla concreta el caso de teléfono compartido entre anunciantes diferentes.

Modelo propuesto:

- Cuenta privada del gestor → perfil de agencia → perfiles individuales representados → anuncios de esas personas.
- Teléfono de gestión asignado a la agencia, referenciado por sus anuncios; no crear cuentas independientes para reutilizar el número sin autorización.
- Perfil individual conserva identidad pública, fotos, servicios, tarifas y verificaciones propios. El perfil de agencia no fusiona a todas las personas en una sola ficha.
- Mostrar quién gestiona el anuncio y diferenciar agencia de anunciante independiente.
- Declararse agencia no evita la verificación de personas representadas, derechos de imagen ni autorización de gestión.
- El teléfono de agencia puede repetirse en sus publicaciones legítimas; imágenes de personas distintas siguen sometidas a controles de reutilización.

La unicidad de la persona representada debe evaluarse entre agencias y cuentas independientes: crear una agencia no permite duplicar un perfil existente. Definir reclamación de titularidad, salida de agencia y transferencia de gestión sin duplicar anuncios ni perder controles.

Restricción propuesta: un teléfono de gestión pertenece a un gestor autorizado activo —independiente o agencia—, con varias publicaciones permitidas solo dentro de la política de ese gestor. Registrar roles y asociaciones explícitos; no resolverlo únicamente con un `UNIQUE` sobre el teléfono de cada anuncio.

Pendiente: pruebas requeridas para agencias, miembros del equipo y sus permisos, anuncios simultáneos por persona y gestión de números reasignados. Un teléfono alternativo de la persona no debe crear automáticamente otra cuenta o perfil duplicado.

## Garantías en PostgreSQL

- Unicidad del teléfono canónico en entidad de teléfono.
- Unicidad de asociación de foto por revisión y de otras relaciones donde corresponda.
- Restricciones de anuncios activos según política aprobada; PostgreSQL permite índices únicos parciales.
- Las comprobaciones de aplicación sirven para explicar errores; la base de datos protege frente a carreras. Resolver conflictos de integridad con transacciones y respuestas controladas.
- No basar un índice parcial en la hora actual: expresar estado/vigencia mediante datos y transiciones controladas. Las columnas de otras tablas no pueden usarse sin más como predicado de un índice de anuncios.
- No imponer un hash global único en cada fila de fotografía si necesitamos reutilizar una imagen en revisiones legítimas. Si hay catálogo de objetos, definir ahí unicidad y en tablas de uso los permisos.

## Flujo propuesto

1. Normalizar teléfonos y comprobar conflictos al guardar datos de contacto.
2. Recibir archivo en zona privada con límites y calcular SHA-256.
3. Validar imagen y producir señales adicionales en trabajo de fondo.
4. Registrar coincidencias sin publicar material pendiente.
5. Aplicar restricciones exactas y enviar conflictos de propiedad/similitud a moderación.
6. Revalidar al publicar dentro de transacción; las ediciones y cambios de teléfono deben recorrer controles equivalentes.
7. Registrar decisión, motivo y revisión, con accesos y conservación definidos.

No existe una garantía de detectar todos los duplicados: distintos teléfonos, fotos modificadas o textos reescritos pueden evadir señales. Se podrá añadir similitud textual como señal si aporta valor medido, sin sustituir permisos y moderación.

## Privacidad y retención

Hashes y relaciones de coincidencia pueden ser datos personales vinculables; no considerarlos anónimos por defecto. Un hash simple de teléfono es susceptible de enumeración. Si se necesita una clave de comparación protegida, evaluar HMAC con secreto separado, rotación y acceso restringido; no sustituye la necesidad de proteger el teléfono original.

No informar públicamente qué otras cuentas usan teléfono o fotografía. Evitar mensajes que permitan enumerar registros mediante consultas repetidas. No incluir contactos o hashes sensibles completos en logs.

Las huellas de contenido retirado o cuentas cerradas necesitan finalidad, plazo y base jurídica propios. No conservarlas indefinidamente por prevención de fraude sin analizar proporcionalidad. Revisar retención y borrado en [marco legal](06-marco-legal.md).

## Validación requerida antes de producción

Casos: formatos equivalentes de teléfono, país ambiguo, número compartido autorizado, cambios/reasignación, duplicado exacto de imagen, mismo contenido con metadatos distintos, revisión legítima, falso positivo, borrado con referencias y dos publicaciones simultáneas. Verificar que conflictos no filtran datos de terceros y que un fallo de procesamiento no publica fotos sin revisión.

## Fuentes oficiales

- [Python: hashlib y SHA-256](https://docs.python.org/3.13/library/hashlib.html).
- [Google libphonenumber: normalización y validación](https://github.com/google/libphonenumber). La biblioteca Python concreta y versión quedan pendientes.
- [PostgreSQL: creación de índices, unicidad y predicados](https://www.postgresql.org/docs/current/sql-createindex.html).

No se ha implementado ningún control. El usuario acepta el enfoque por capas de detección exacta y visual; bibliotecas, umbrales y política de publicación quedan pendientes. No se aprueba bloqueo global automático.

## Observación de cuentas y automatización

El usuario acepta detectar duplicados visuales y pide no bloquear inmediatamente por imagen, para observar cómo actúan las cuentas y cuántos perfiles intentan crear. No interpretar esa autorización como permiso para publicar automáticamente contenido conflictivo o registrar actividad sin límites.

### Separar decisiones

- **Cuenta:** puede continuar operando con límites; una coincidencia por sí sola no suspende automáticamente el acceso.
- **Borrador:** propuesta de permitir creación y edición limitada para observar intentos.
- **Publicación:** propuesta de conservar anuncios/fotos conflictivos en revisión. Esta propuesta no está aún aprobada expresamente.
- **Integridad:** las restricciones exactas siguen impidiendo duplicados donde la política los prohíba. Registrar el intento rechazado no requiere persistir otro perfil o archivo.

Esta sección precisa las reglas anteriores: «rechazar repetición» o «detener publicación» no significa suspender la cuenta. Para una repetición dentro del anuncio, conservar un evento de intento sin añadir otra copia.

### Señales propuestas

| Señal | Registro mínimo propuesto | Interpretación |
| --- | --- | --- |
| Intentos de perfil/anuncio | Cuenta, tipo de acción, resultado y fecha | Contar intentos, incluidos los rechazados; no solo filas creadas |
| Duplicación de imágenes | Referencias internas, método/version, coincidencia y resultado | Repetición exacta o similitud; acceso restringido |
| Cadencia y volumen | Contadores por ventanas temporales | Picos o automatización posibles; no prueba concluyente |
| Cambios de contactos | Evento y asociación interna, sin número completo en logs | Posible evasión, cambio legítimo o gestión compartida |
| Verificación y moderación | Estados y decisiones | Contexto de autorización y corrección de conflictos |

Combinar señales: una agencia legítima puede crear muchos perfiles, y un usuario puede reenviar un formulario por problemas de conexión. Distinguir reintentos técnicos de nuevas acciones mediante idempotencia cuando proceda. La duplicación de foto o rapidez no demuestra que sea un bot ni que cometa fraude.

### Respuesta gradual propuesta

1. Registrar evento y continuar con límites de recursos.
2. Mostrar advertencia útil o solicitar corrección, sin revelar otras cuentas vinculadas.
3. Si acumula señales, reducir frecuencia o pedir comprobación adicional proporcional.
4. Moderador revisa conflictos y decide publicar, rechazar contenido o restringir cuenta.

Definir razones y vía de revisión de decisiones. Una puntuación automática sería apoyo, no prueba definitiva. No enviar correos o avisos externos a terceros como parte de esta observación sin diseñar y autorizar el flujo correspondiente.

### Límites y privacidad

Mantener límites de peticiones, cargas, espacio y tiempo de cómputo desde el inicio: observar no significa permitir creación ilimitada ni desactivar defensas. No retrasar respuesta a indicios de menores, explotación o imágenes no consentidas para recopilar comportamiento.

No incorporar seguimiento externo, fingerprinting del dispositivo ni reconocimiento facial para este fin. Si se necesita usar IP por seguridad, definir finalidad, acceso y plazo y considerar conexiones compartidas; no convertir IP común en prueba de misma persona.

Documentar base jurídica y necesidad de eventos antifraude, conservación por finalidad, acceso restringido y borrado. Evitar guardar descripciones, fotos o teléfonos completos en cada evento. Los eventos y relaciones entre cuentas pueden ser datos personales; su conservación no es indefinida.

### Operación y validación

Persistir eventos necesarios en PostgreSQL con acceso restringido; contadores temporales pueden estar en Redis. Un fallo de telemetría no debe permitir publicación que requería revisión ni impedir reconstruir decisiones esenciales. Definir qué eventos son transaccionales y cómo se recuperan; no confundir contadores efímeros con evidencia duradera.

Probar reintentos, agencias autorizadas, actividad de varias cuentas, falsos positivos y saturación de la cola. Umbrales, ventanas, duración de observación y capacidad de moderación pendientes; no establecer cantidades arbitrarias como criterio de bot.
