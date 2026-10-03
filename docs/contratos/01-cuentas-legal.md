# CR-01 — Cuentas y documentos, interfaz v1

Prefijo /es o /en. HTML SSR con POST y CSRF; errores de entrada 400, permisos privados redirigen a login, exceso de intentos 429. No parámetro next externo.

| Ruta relativa | Métodos | Acceso | Resultado |
| --- | --- | --- | --- |
| /account/signup/ | GET/POST | público | formulario; respuesta genérica 200 tras alta válida o email existente |
| /account/login/ | GET/POST | público | credenciales genéricas; sesión solo con correo confirmado; 302 panel |
| /account/logout/ | POST | sesión | cierre y 302 inicio; GET 405 |
| /account/recover/ | GET/POST | público | respuesta genérica; reset solo cuenta activa/confirmada |
| /account/resend/ | GET/POST | público | genérica; reenvío invalida código previo |
| /account/token/{uuid}/{token}/ | GET/POST | secreto correo | GET no consume; POST confirma/cambia contraseña; inválido/caducado/repetido 400 |
| /account/accept/ | GET/POST | sesión | actualización de condiciones; conserva aceptaciones anteriores |
| /account/ | GET | sesión confirmada + documentos vigentes | panel privado no-store |
| /legal/ y /legal/{slug}/ | GET | público | documentos vigentes del idioma, 404 inexistente |

Alta: email normalizado, contraseña mínima 12 + validadores Django, aceptación de condiciones y lectura del aviso de privacidad, versiones terms/privacy ocultas comprobadas servidor. La lectura del aviso no equivale a consentimiento de tratamientos opcionales. Role/staff/verificación nunca se aceptan desde POST. Correo cuenta no es contacto público.

Aceptación: usuario/documento exacto/versión/idioma/acción/fecha; unicidad por documento y acción. ES/EN de la misma versión permiten continuidad del acceso. Traducción antigua respecto a versión publicada más reciente no permite eludir aceptación: operación privada bloqueada hasta traducción vigente. Nuevas versiones obligan a actualización antes de operaciones privadas. Documentos de desarrollo dev-1 requieren revisión jurídica; bootstrap no funciona en producción.

Tokens: 256 bits aleatorios, SHA-256 almacenado; 24 horas confirmar, 1 hora recuperar. Huella HMAC de estado de usuario invalida tras cambio email/contraseña. Uso protegido por bloqueos PostgreSQL usuario → token; reenviar invalida previos; reset no confirma correo ni eleva rol; sesiones previas quedan invalidadas por hash de contraseña. GET mantiene estado para escáneres de correo. Política same-origin conserva CSRF y evita filtrar referer a otros orígenes.

Límites iniciales por IP pseudonimizada HMAC y operación: alta/recuperar/reenviar 5 por 15 minutos; login 10; consumo token 15. Proxy real y límites por cuenta adicionales se completan en endurecimiento; no confiar en X-Forwarded-For por defecto. Correo locmem en tests, consola en local, SMTP configurable. Fallo SMTP no cambia respuesta ni revela existencia; alerta técnica sin dirección/token bruto y reenvío disponible.

Wireframes: registro → confirmación genérica → enlace de correo → confirmación POST → acceso → panel. Recuperación → respuesta genérica → enlace → nueva contraseña → acceso. Documentos accesibles desde alta y cabecera; controles privados sin cache.
