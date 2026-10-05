# Consulta paginada de fuentes de copia privada

Estado: consulta paginada verificada localmente. Parte de CR-09; no aprobación paginada ni generación completa desde páginas.

## Comportamiento

La preparación existente ofrece POST inspect_page para revisiones, aceptaciones legales, favoritos, comprobaciones y representación histórica del sujeto comprobado. Cada página contiene hasta10 entradas; una entrada individual puede ser grande. GET nunca recupera contenidos de consultas anteriores. La paginación presenta fuentes seleccionadas, no completa el inventario de derechos.

## Autoridad y auditoría

Se conservan locks del expediente/perfil y las comprobaciones de asignación, lectura previa, prueba, permisos/MFA y conflictos. RightsAction copy_page_read registra actor, versión, motivo cifrado y firma de sección/página/fuente; misma clave compatible no duplica acción. El cursor firmado caduca1h y liga actor/sesión/MFA/expediente/versión/prueba/huella de toda la fuente/sección. Página posterior exige cursor válido; cambios de fuente o ámbito rechazan sin auditoría nueva. La autoridad se vuelve a comprobar antes de devolver datos.

## Separación respecto a entrega

Una página no crea RightsExportPreview ni autoriza generate. La generación existente exige su preview completo y copia revisada completa. Se informa expresamente de consulta de sección; no presentar páginas leídas como aceptación de todo el documento. Próximo trabajo: revisión/redacción persistente por páginas, acreditación de cobertura completa, deriva y generación desde decisiones versionadas.

## Límites actuales y pruebas

source_copy aún materializa toda la fuente para comprobar la huella; esta entrega acota entradas visibles, no memoria de toda la inspección. Batería84527 terminal0:2 PostgreSQL correctas36,19s, XML /tmp/copy-inspection-pages.xml:25 revisiones en páginas10+10+5, replay, cambio de fuente, ausencia de preview completo y rechazo de generación, POST/GET privado y cursores alterados/otra sección. Móvil, carreras, secciones adicionales y aceptación conjunta siguen pendientes. No proveedor de identidad real ni cumplimiento jurídico integral acreditados.

Regresión84563 terminal0:15 correctas115,18s con exports y cuenta. Batería54849 terminal0:9 correctas76,57s de secciones, datos ajenos, sesión/MFA/caducidad/prueba/permisos y revocación durante lectura (inyección controlada, no concurrencia entre conexiones).53110 terminal0:2 móvil ESEN correctas43,48s, login/MFA→primera página→siguiente→reload POST idempotente→GET limpio y texto largo con CSS externo. Unicidad global de clave tiene savepoint y ValidationError controlado; prueba de lookup obsoleto inyectado con constraint PostgreSQL real, sin afirmar concurrencia.90052 activa regresión común sobre versión actual.

Concurrencia30696 reproduce fallo de sesión anterior admitida tras espera observada (1 fallida30,62s). Corrección conserva versiones de sesión/MFA del actor al entrar y compara tras locks con actor fresco.64764 terminal0:5 correctas52,71s en escenarios con tres conexiones PostgreSQL (holder y dos workers), bloqueos observados mediante pg_blocking_pids recursivo. Cambios de prueba/permisos/versiones inyectados como fixtures concurrentes, sin acreditar proveedor ni procedimiento externo de revocación.

Aceptación local de consulta:91711 terminal0,30 correctas198,45s sobre versión corregida, incluidas carreras y móvil ESEN. Runtime32765:4 hashes iguales app/worker/Beat, UID10001, check/migraciones/health200 y CSS servido coincidente tras collectstatic. Evidencias copia-consulta-paginada-regresion.json y copia-consulta-paginada-runtime.json. Sigue pendiente revisión/aprobación persistente por páginas e inventario integral; no CR09 completo ni producción acreditada.
