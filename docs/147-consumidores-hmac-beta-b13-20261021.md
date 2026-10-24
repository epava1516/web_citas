# B13 — Cierre estático de consumidores HMAC

Estado: PASS estático local, no aceptación B13 ni autorización de rotación. Siete de18puntos cerrados. Continúa el [censo143](143-inventario-claves-hmac-beta-b13-20261021.md).

El grafo vigente presenta368relaciones entrantes a crypto.digest y rights.fingerprint; son pistas de navegación, no un censo transitivo acreditado. scripts/secret_consumers.py añade un análisis AST separado: resuelve llamadas entre funciones propias, imports relativos, alias de imports de función/módulo, reexportaciones y wrappers; calcula rutas mínimas inversas a esos dos helpers. Las rutas se refieren a símbolos y fuentes/lineas, nunca a valores de claves ni argumentos de ejecución.

Preparación actual:383funciones consumidoras resueltas y308fuentes Python de apps, excluyendo migraciones.14634llamadas no resueltas en el conjunto analizado incluyen llamadas ordinarias y de librerías: no equivalen a14634consumidores HMAC pendientes. No importa ni ejecuta los módulos examinados, no carga settings ni accede a DB, Redis, proveedor o entorno secreto. Produce huellas de todas las fuentes examinadas y no exporta literales del código.

complete_transitive_coverage=false y retirement_authorized=false son incondicionales. Dispatch dinámico, callbacks, alias asignados, reflexión, inicializadores de módulos, framework/terceros y datos históricos quedan fuera. No se interpreta una ruta AST como rama alcanzada en ejecución ni como campo persistente clasificado. Rebinding ambiguo y parámetros que sombrean helpers no deben inventar enlaces.

Verificación prevista:11casos del nuevo cierre más6del inventario de productores existente, todos unitarios estáticos sin integración PostgreSQL necesaria. Incluye fuentes actuales, alias/relativos, ciclos, wrappers, parámetros/variables que sombrean, reexportación sin ejecutar código, literales ausentes de salida y raíz ausente como error. Se conserva cualquier negativo y se confirma Telegram terminal. El grafo se refresca antes de congelar la selección.

Siguiente trabajo B13: clasificar consumidores por dominio persistente y respuesta de revocación/revalidación, respaldar los flujos afectados con pruebas de rotación y documentar credenciales/retención externa. No rehash de evidencia inmutable, retirada de readers antiguos ni cambio de SECRET_KEY por ejecutar este inventario.

## Resultado terminal

17PASS/0FAIL/0ERROR/0SKIP,3,620sJUnit (12,33s mostrados por pytest con aviso terminal). [Auditoría](evidencias/b13-hmac-consumers-terminal-audit-20261021.json) y [cierre estático completo](evidencias/b13-static-hmac-consumers-20261021.json). Fuentes frescas y TelegramPASS confirmados. Ninguna DB o servicio iniciado: estas pruebas no reciben crédito de integración PostgreSQL. Los once casos del cierre y seis del registro anterior pasan juntos.

El resultado contiene383consumidores resueltos,308huellas de fuente y14634llamadas ordinarias/no resueltas del conjunto analizado. Incluye rutas estáticas a publicación, recibos, entrega de derechos y rectificación; no se concluye por ello que cada rama se ejecute ni que pueda revocarse sin una revisión del dominio. Producto existente intacto: sólo módulo de inventario y pruebas nuevos. La clasificación de campos, política de revocación/revalidación y retención histórica permanece pendiente; B13 sigue abierto7/18.
