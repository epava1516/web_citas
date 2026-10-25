# N06F — referencias actuales de transiciones restantes

25 de octubre de 2026. [Prerregistro373](373-n06-f-prerregistro-referencias-restantes-20261025.md), candidata9aed9afsin cambios de aplicación respecto a f03eea8. Ejecución20261025-162605-8a2766fc: **12 PASS, 0 FAIL/ERROR/SKIP**,120peticiones observadas y0rutas sin resolver. Once selectores originales; doce casos por la variante ES/EN de guía de perfil. Se conservan todas las fixtures/aserciones originales, sin recortes ni repetición adaptativa.

[Auditoría y actualización por acción](evidencias/n06-f-referencias-auditoria-20261025.json), [fuentes y reproducción](evidencias/n06-f-referencias-reproduccion-20261025.tar.gz). Las1736huellas permanecieron intactas hasta auditoría; selección exacta, métricas finitas/no negativas, conteos íntegros y ningún error del observador o excepción inesperada. PostgreSQL17/Redis7.4 propios y herramientas nativas fijadas. Inventario independiente sin contenedores/redes/volúmenes propios, temporal retirado, aviso terminal del runner confirmado sent.

## Antes y después de la referencia

| Cobertura de medición N06 | Antes, corte372 | Después de esta pasada | Límite |
| --- | ---: | ---: | --- |
| Acciones censadas |46|46|Mismos IDs, no funcionalidades nuevas|
| Rutas HTTP con alguna muestra |20/41|37/41|No significa todas las ramas/roles/idiomas o capacidad|
| Rutas sin muestra en estos lotes |21|4|Los cuatro listados de revisión siguen pendientes|
| Muestras nuevas de esta selección |0|120|Peticiones heterogéneas, no repeticiones equivalentes|
| Código de aplicación |f03eea8|Mismo código|Sin candidato ni mejora atribuible|

Se incorporan17rutas antes sin referencia. Para que la tabla incluya tiempos, se muestra la primera observación registrada de cada ruta nueva, con método/estado ySQL; no se escoge su mínimo ni se presenta como mediana o SLO. El conjunto completo por caso/ordinal está en la evidencia. Otras transiciones de la misma ruta pueden tener coste distinto.

| Ruta nueva | Antes equivalente (ms) | Primera observación | Tiempo actual (ms) | SQL | Mejora atribuible |
| --- | ---: | --- | ---: | ---: | --- |
| agency_appeal_submit | No medido | POST 302 | 36.748 | 18 | No evaluable |
| agency_appeal_review | No medido | GET 403 | 16.716 | 9 | No evaluable |
| manager_appeal_submit | No medido | POST 302 | 35.893 | 14 | No evaluable |
| manager_appeal_review | No medido | GET 403 | 17.397 | 9 | No evaluable |
| manager_review | No medido | GET 403 | 15.324 | 7 | No evaluable |
| revision_status | No medido | GET 404 | 20.746 | 8 | No evaluable |
| individual_create | No medido | POST 302 | 69.997 | 16 | No evaluable |
| person_verification | No medido | GET 200 | 76.537 | 13 | No evaluable |
| self_consent | No medido | POST 200 | 24.385 | 9 | No evaluable |
| representation_transfer | No medido | POST 302 | 66.532 | 15 | No evaluable |
| mfa_enroll | No medido | POST 200 | 190.826 | 11 | No evaluable |
| mfa_challenge | No medido | POST 200 | 20.931 | 10 | No evaluable |
| agency_invite | No medido | POST 302 | 14.780 | 12 | No evaluable |
| agency_revoke | No medido | POST 302 | 19.754 | 11 | No evaluable |
| agency_accept_invitation | No medido | POST 403 | 20.676 | 9 | No evaluable |
| resend | No medido | POST 200 | 15.719 | 10 | No evaluable |
| accept_current | No medido | POST 400 | 27.233 | 3 | No evaluable |

La primera observación de cada ruta no sustituye a las demás. Se conservan también peticiones mayores, como photo_uploadPOST302a1222,912ms y signupPOST200a625,599ms; no se descartan para mostrar sólo acciones rápidas. Algunas peticiones incluyen trabajo eager de la fixture; el origen y sus límites permanecen. No se identifica defecto ni se propone cambiar seguridad por el mero valor de una observación.

## Oráculos preservados y alcance

Pasan aceptación de nuevas condiciones conservando la anterior, reenvío que invalida token previo, reset de un uso/caducidad/sesión antigua invalidada, consentimiento/versiones y requisitos locales, teléfono compartido con sujetos distintos, MFA/replay/recuperación, edición sólo asignada y revocación, transferencia pendiente de revisión humana y rechazo de versiones antiguas, reclamaciones con revisión independiente sin autoaprobación/publicación y guía privada ES/EN compatible con la versión pública. El404trastransferencia y el200de revisión pendiente son transiciones diferentes y se conservan separadas.

Son oráculos originales ejecutados; no acreditan todas las combinaciones posibles. El observador mide Client.request durante call con SQL de esa conexión. No mide setup ordinario, servicios directos, Playwright, otras conexiones, trabajo asíncrono real o tiempo humano. Fixtures dinámicas pueden incluir operaciones adicionales dentro de call. Ningún proveedor real ni identidad/edad/teléfono/correo externo verificados por esta pasada. No p95/p99, carga o garantía productiva desde estas muestras.

QA separado: JUnit78,235s, incluido montaje/assertions/limpieza de tests; no es latencia de una operación. No hay comparación causal de aplicación ni reducción de QA declarada por completar referencias.

## Pendiente antes del cierre N06

Las cuatro rutas sin referencia son agency_appeal_queue,manager_appeal_queue,manager_queue yorganization_queue. Requieren ficha de crecimiento/selección/autoridad, no reutilizar una muestra de revisión individual como prueba del listado. Preservar top100existente y sus exclusiones, sin inventar paginación nueva ni ocultar límites. Después conciliar suficiencia de las variantes y responsabilidades compartidas; runbooksN10yprocesadoN03/N07siguen con sus trabajos propios.

Se actualiza la conciliación372sin reescribir su corte previo ni convertir una ruta con muestra en PASS universal. N06sigue abierto, N00/N01aceptados2/13, resto del contrato vigente. MOD09restante sigue diferido al final del desarrollo por decisión del usuario367. Alfa, sin apertura/proveedores/datos reales.
