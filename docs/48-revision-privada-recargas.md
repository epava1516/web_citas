# Revisión privada de recargas: contrato de implementación

Implementación conectada: consulta auditada, decisión independiente, interfaz ES/EN y bloqueo central de publicación. 49 pruebas conjuntas pasaron antes del refuerzo de autoridad; 7 pruebas afectadas pasaron después de ese refuerzo. No se suman ni acreditan una regresión común de la versión final. Docker actual verificado con PostgreSQL, hashes iguales, UID 10001 y health 200. No acredita revisión humana, exportación integral, retención final ni cierre de CR-09.

## Autoridad y ámbito

Permiso específico de revisión de recargas, MFA vigente y exclusión del sujeto, gestores y agencias actuales/históricos, autor del caso y decisores de la retirada. La revisión usa el ámbito de la ejecución que retiró la imagen, pero no reabre ni resuelve automáticamente el expediente original. Cambios de gestión exigen recalcular conflictos bajo bloqueos.

El registro candidato debe conservar uploaded_blob además de Photo: una referencia que se sustituye durante una retirada no debe heredar decisiones sobre los bytes anteriores. Detectar y consultar nunca confieren permiso para rehabilitar. No confiar en IDs recibidos sin revalidar persona, archivo, disposición activa y estado de preparación/historial.

## Consulta auditada

GET muestra formulario con motivo y metadatos mínimos, sin bytes históricos. POST autorizado crea lectura durable ligada a actor, candidato, motivo, fecha y huella de la autoridad y de ambos recursos. Solo después entrega imágenes mediante rutas privadas ligadas a esa lectura. No reutilizar una lectura de otro actor ni una huella anterior; MFA/roles/conflictos y versión se comprueban otra vez al abrir.

Huella incluye Photo/Blob de la carga, Blob conservado de retirada, ejecución/disposición, persona/gestión/derechos, estados de retirada/archivos y firmas. Lecturas y decisiones no recuperan archivos purgados ni confieren acceso general al expediente. Cache privada/no-store; una retirada durante espera del bloqueo debe devolver404. No se revocan bytes ya entregados.

## Decisión independiente

Resultados: mantener retirada, falso positivo visual y autorizar uso actual en el ámbito revisado. Cada decisión exige lectura actual, motivo privado, referencia de evidencia, clave idempotente y versión. La autorización solo afecta al candidato revisado; no publica el anuncio ni elimina decisiones ordinarias de duplicados. No autorizar por similitud visual sola.

Persistir decisión con vínculos a lectura y recursos; conservar historia y posibilidad de revisión motivada. Nueva autoridad sobre el archivo, cambio de bytes, nueva rectificación o gestión relevante invalidan decisiones anteriores. Dos revisores concurrentes no pueden resolver simultáneamente versiones distintas sin conflicto explícito.

## Publicación e interfaz

Validador central bloquea candidatos activos pendientes o confirmados, incluso si se fuerzan estados de publicación. Envío, aprobación, reanudación, renovación, ficha e imágenes públicas comparten la regla. La carga sigue aceptada para observación; no suspender cuentas automáticamente. El editor muestra estado pendiente genérico ES/EN, sin revelar SHA, expediente o motivos privados.

Recorridos: gestor carga → ve revisión pendiente → moderador independiente consulta auditada → revisa ambas imágenes → decide → gestor ve resultado mínimo → publicación vuelve a pasar moderación ordinaria si corresponde. Mantener cola privada separada de Match; acceso histórico por finalidad explícita.

## Verificación requerida

HTTP y servicio: permisos/MFA/conflictos, ausencia de bytes antes de auditoría, lectura cruzada/obsoleta, idempotencia y versiones, revalidación de uploaded_blob, cambios de autoridad por archivo/persona, concurrencia real PostgreSQL, retirada durante lectura y publicación mientras se decide. Navegador móvil ES/EN y resultados visibles persistidos. Integrar registros en inventarios/exportaciones y conservar evidencia según política final pendiente.

## Estado de implementación

Modelo de lectura y decisión, permiso específico y review_version (safety0057). Servicio bloquea ámbito/agencias/persona/anuncio/caso/candidato/revisión/Blob, excluye sujetos/gestores/proponentes/decisor original y exige autoridad original passed. No usa la vigencia temporal de aquel proof como comprobación nueva de identidad; en producción rechaza procedimientos simulados. Consulta almacena actor/motivo/huella; decisión exige lectura propia y versión actual, cifra motivo/referencia, admite reintento exacto y no acepta falso positivo visual para bytes idénticos. Cambios de archivos/firmas/gestión/derechos/prueba original invalidan autoridad de decisión.

Rutas nuevas: moderation/photo-reuse/ (cola paginada), <candidate_id>/ (GET sin imágenes, POST inspect o decide), <candidate_id>/reads/<read_id>/<side>/ (uploaded/withdrawn). MFA de sesión vigente en todas. Bytes solo para actor de lectura actual después de locks/reconsulta; Cache-Control private/no-store. HTTP muestra resultado registrado y enlace de dashboard para rol; editor muestra aviso genérico y validate_submission comparte bloqueo con publicación/reanudación. Inventario incluye lecturas y decisiones como dependent_evidence.

Servicios iniciales:3 correctas31.83s, ledgers sintéticos persistidos; no prueba de proveedor ni aprobación humana. Batería actual45876/XML /tmp/private-photo-reuse-http-publication.xml en curso: servicios/HTTP, imágenes, control del sujeto y moderación/fotos. Fuente funcional congelada; un aviso Ruff por separación de imports de test requiere corregirse tras terminal. Modelo/migración safety0057 todavía no aplicado en Docker. Pendientes: casos de concurrencia PostgreSQL, navegador móvil ES/EN, CSRF/roles obsoletos/bytes cambiados, recorrido real de ejecución previa, exportación/retención/legado, evidencia y commit.

Batería HTTP/publicación terminal:15 correctas67.04s, sin fallos/errores/omisiones, sobre ledgers sintéticos y servicios reales locales. Ampliación de navegador80833 en curso, Chromium390x844 ES/EN, sesión Django de test (no autenticación de proveedor), imágenes decodificadas y decisión visible antes de reload. Ruff limpio tras corregir import de test. No incluir aún resultado de navegador ni concurrencia.

Primera ampliación de navegador falla en lanzamiento (2 correctas/2 fallidas41.77s) por ejecutable por defecto ausente. Se alinea con chromium-browser explícito de otras pruebas; repetición92160 en curso. No acreditar navegador hasta terminal. Refuerzo comprueba cambio de firmas con lectura/version vigentes para aislar invalidación de huella.

Navegador final17968:4 correctas46.77s, cero fallos/errores/omisiones, incluyendo ES/EN390x844. Imágenes decodificadas tras auditoría; decisión visible antes y después de recarga; sin desbordamiento. Primeras dos invocaciones se conservan como fallidas por configuración de Chromium y uso de eval en el test. No sumar baterías. Concurrencia real y recorrido desde ejecución de rectificación siguen pendientes. Build Docker iniciado/safety0057 runtime pendiente.

Runtime local safety0057 aplicado y app/worker/Beat recreados: hashes review/submissions coinciden, check sin incidencias y health200. No se acepta todavía: faltan decisión obsoleta visible, negativos/CSRF, concurrencia y flujo desde ejecución previa antes de cierre/commit.

Aviso explícito cuando la huella de una decisión anterior cambia; errores de decisión visibles incluso sin imágenes.4 pruebas correctas49.06s con CSRF/MFA caducada y lectura obsoleta, además de ESEN móvil. Pruebas de carreras96782 en curso: pg_blocking_pids sobre peticiones/transacciones reales, ejecución local de redacción y decisiones concurrentes. No acreditar resultado hasta terminal. Docker previo no contiene última UI.

Primera batería de carreras:1 correcta/1 fallida37.81s. Retirada durante lectura pasa; observación de dos decisores se amplía de bloqueo directo a cadena recursiva de bloqueos PostgreSQL. Repetición20484 en curso; no afirmar dos decisiones verificadas todavía.


La prueba desde una rectificación realmente ejecutada encontró tres fallos (tres variantes correctas, cinco excluidas, 115,53 s): archivos legados listos sin firma perceptual no pasaban al detector privado exacto. Se ha movido esa detección antes del retorno por firma ausente. La igualdad SHA no requiere firma visual; las comparaciones regionales siguen requiriéndola. Repetición en curso con la fuente funcional corregida; el Docker previo aún no contiene este cambio ni el último aviso de decisión obsoleta.


## Estado actual de verificación

Las carreras PostgreSQL finalizaron con 2 pruebas correctas en 31,98 s: petición de imagen bloqueada durante retirada real local devuelve 404; dos decisores sobre la misma versión producen una decisión y un conflicto. El flujo de rectificación ejecutada y recarga terminó con 6 variantes correctas en 122,31 s (cinco casos excluidos por selección; la variante de rechazo termina antes de ejecutar). Autoridad de identidad de desarrollo simulada, procesamiento y transacciones locales reales.

Docker final reconstruido y recreado: el servicio, vistas, validador, detector y plantilla coinciden entre host y contenedor; check sin incidencias, safety0057 vigente, UID 10001, health 200. La batería conjunta de 49 pruebas sigue en ejecución. Los resultados parciales anteriores no se suman ni sustituyen esa aceptación. Exportación completa, conservación por finalidad y casos legados continúan pendientes dentro del contrato.


Auditoría adicional pendiente de corregir: la autoridad original se obtiene antes de esperar los bloqueos de ámbito. Recargar ejecución y proof después de esos bloqueos para evitar que una lectura preparada con status passed se admita si la autoridad cambia mientras espera. Verificar con transacciones realmente bloqueadas PostgreSQL; no acreditar este caso mediante la huella sola ni aceptar entrega antes de probarlo. Batería 28575 actual aún activa, fuente congelada hasta su terminal.


Batería conjunta28575:49 correctas419,13 s, sin fallos/errores/omisiones; anterior al refuerzo de autoridad. Nueva carrera reprodujo el fallo: consulta bloqueada registra lectura tras cambiar proof a pending (1 fallida23,63 s; 2 excluidas). locked ahora recarga ejecución/proof/propuesta después de adquirir locks de ámbito. Batería de carreras/autoridad/HTTP/Chromium ESEN75572 activa; no acreditar corrección hasta terminal ni usar49 anteriores como regresión de esta versión.


### Revisión privada de recargas: verificación local parcial

Consulta auditada, decisión independiente versionada/cifrada, UI móvil ES/EN y bloqueo central de publicación implementados con safety0057.49 conjuntas correctas419,13 s antes del refuerzo de autoridad;7 finales afectadas correctas75,37 s después, no sumar. Carrera nueva reprodujo lectura admitida tras cambio proof durante espera (1 fallida23,63 s); corregida reconsulta después de locks y verificada denegación sin lectura durable. Retirada real local durante lectura y dos decisores sobre una versión también cubiertos. Docker/check/migraciones/UID10001/health200/hashes verificados, normalización de formato sin cambio semántico requiere última reconstrucción. Identidad y autoridad humanas siguen simuladas en pruebas, no proveedores reales. [Detalle](48-revision-privada-recargas.md) y [evidencia](evidencias/revision-privada-recargas.json). Exportación integral, retención/legado, cuenta/comunicaciones/cierre y resto contrato pendientes; CR09 abierto, Claude3/3.


Normalización Ruff final sin cambio semántico; rebuild99273/recreate40292 terminal0 y hash del servicio igual en host/app/worker/Beat f5ded763210fe07d1f9d12e79067b12323d0e5ad4e1d374736ff3dab06de0998. No pruebas activas. Entrega lista para commit/push de desarrollo, no aceptación completa CR09 ni producción.


## Integración de autoridad en planes de supresión

La huella seleccionada ahora incluye review_version del candidato y encrypted_reason de la decisión. El contenido cifrado solo participa en HMAC interno; no se descifra ni aparece en metadatos de pantalla. Un plan existente requiere preparar y revisar de nuevo si cambian esos recursos o se registra una lectura posterior. No se eliminan auditorías por esta incorporación ni se declara conservación definitiva.

La reproducción previa dio 2 fallos/1 caso correcto41,46 s: versión y motivo no invalidaban fuente; nueva lectura sí. Batería conjunta de inventario/planes/carreras96333 en curso, resultado pendiente. [Evidencia](evidencias/inventario-revision-recargas.json).


Inventario de revisión de recargas:17 conjuntas correctas149,41 s, cero fallos/errores/omisiones PG/Chromium. Incluye cambios de versión/motivo/lectura, rechazo antes de execute sin eliminar archivos, aislamiento de otro perfil y ausencia de motivos/ciphertext en manifest. review_version y encrypted_reason participan en HMAC interno seleccionado, sin descifrar ni entregar su contenido. Reproducción previa2 fallidas/1 correcta41,46 s conservada. Docker build88611/recreate86940/check/health200/hashes host-app-worker-Beat verificados; sin migración nueva. No acredita inventario/exportación integral ni política final de conservación. Claude3/3; CR09/contrato abiertos.
