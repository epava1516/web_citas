# Directorio — desarrollo
Contrato y seguimiento en [docs](docs/README.md). Datos sintéticos, sin cobros reales.

## Inicio local
```sh
cp .env.example .env
uv sync --python 3.12 --locked
docker compose up -d --wait db redis
uv run python manage.py migrate
uv run python manage.py bootstrap
DJANGO_DEBUG=1 uv run python manage.py runserver 127.0.0.1:8000
```
Configuración local coincide con `.env.example`; exportar variables al cambiarlas. Base obligatoriamente PostgreSQL.

## Docker
```sh
docker compose build
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py bootstrap
docker compose run --rm app python manage.py collectstatic --noinput
docker compose up -d app worker caddy
```
Abrir http://localhost:18080/es/ (Caddy sirve CSS y Gunicorn HTML). El runserver sirve CSS en desarrollo usando DJANGO_DEBUG=1.

## Verificación
```sh
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv run ruff check .
```
No despliegue público hasta gates legales/operativos y técnicos documentados. Configuración production rechaza simuladores y cobros reales.
