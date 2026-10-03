# Interfaces comunes v1
GET /health/: público, JSON status ok o unavailable, 200/503; prueba conexión DB sin detalles internos.
GET /es/ y /en/: HTML SSR, idioma explícito y sesión compartida; entorno local noindex, sin trackers.
Seguridad: CSRF middleware, sesión HttpOnly/Lax, CSP same-origin, frame denied. Objetos privados nunca bajo una ruta estática servida públicamente.
Infra: Redis broker tareas JSON por IDs; PostgreSQL datos negocio; simuladores externos deshabilitados en producción.
Wireframe inicial: cabecera idioma/acceso → contenido principal → ayuda/legal; formularios con label, error y acción; confirmación separada del envío.
