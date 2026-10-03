# ADR-001 — Base técnica
Estado: aceptado, 2026-10-03.
Django 5.2 LTS, Python 3.12, PostgreSQL 17, Redis 7.4, Celery 5.6, Gunicorn WSGI. Versiones exactas Python en uv.lock; actualización controlada y auditoría, sin rangos resueltos en producción. Base modular SSR y mejora HTMX local en flujos posteriores, no SPA.
Django LTS ofrece soporte prolongado y Python 3.12 es compatible: [versiones Django](https://www.djangoproject.com/download/), [compatibilidad](https://docs.djangoproject.com/en/5.2/releases/5.2/). Celery/Redis: [documentación oficial](https://docs.celeryq.dev/en/stable/getting-started/introduction.html).
Dependencias adicionales: Argon2 contraseñas, pyotp TOTP, Pillow/ImageHash medios, django-storages S3. Tests pytest-django/PostgreSQL y Playwright, Ruff y pip-audit. Docker no root; desarrollo privado ligado a loopback. Producción se endurece en B-B, no se acredita por este scaffold.
El host tiene Python 3.9; usar uv con Python 3.12 instalado. No SQLite como sustituto de PostgreSQL.

Cifrado TOTP Fernet con cryptography50.0.2; rango actualizado tras auditoría de vulnerabilidades. Auditoría continua obligatoria, sin fijar rangos antiguos por costumbre.
