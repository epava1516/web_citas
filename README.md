# Directorio — desarrollo
Contrato y seguimiento en [docs](docs/README.md). Datos sintéticos, sin cobros reales.

## Inicio local
```sh
cp .env.example .env
uv sync --python 3.12 --locked
docker compose up -d --wait db redis
uv run python manage.py migrate
uv run python manage.py bootstrap
uv run python manage.py seed_catalog
DJANGO_DEBUG=1 uv run python manage.py runserver 127.0.0.1:8000
```
Configuración local coincide con `.env.example`; exportar variables al cambiarlas. Base obligatoriamente PostgreSQL.

## Docker
```sh
docker compose build
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py bootstrap
docker compose run --rm app python manage.py seed_catalog
docker compose run --rm app python manage.py collectstatic --noinput
docker compose up -d app worker beat caddy
```
Abrir http://localhost:18080/es/ (Caddy sirve CSS y Gunicorn HTML). El runserver sirve CSS en desarrollo usando DJANGO_DEBUG=1.

## Demostración sintética

```sh
read -rsp 'Contraseña de demostración: ' DEMO_PASSWORD
export DEMO_PASSWORD
uv run python manage.py seed_demo
unset DEMO_PASSWORD
```

Con Docker, después de construir/migrar:

```sh
read -rsp 'Contraseña de demostración: ' DEMO_PASSWORD
export DEMO_PASSWORD
docker compose run --rm -e DEMO_PASSWORD app python manage.py seed_demo --credentials-file /app/media/private/demo-credentials.json
mkdir -p .ai
docker compose cp app:/app/media/private/demo-credentials.json .ai/demo-credentials.json
chmod 600 .ai/demo-credentials.json
unset DEMO_PASSWORD
```

El archivo privado contiene accesos y claves TOTP sintéticos; no se imprime ni se versiona. Repetir conserva cambios existentes. [Contenido y límites de la muestra](docs/contratos/07-datos-sinteticos.md).

## Verificación
```sh
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv run ruff check .
```
No despliegue público hasta gates legales/operativos y técnicos documentados. Configuración production rechaza simuladores y cobros reales.

Comprobación de descubrimiento de la muestra inicial Docker: `uv run python scripts/probe_demo_discovery.py` (Chromium del sistema, Caddy localhost:18080, dos fichas públicas de seed_demo). Es de solo lectura; presupone ese estado de muestra y no reinicia datos si posteriormente se han cambiado. La regresión aislada usa pytest/PostgreSQL y no depende de conservar la muestra principal.

Probe de caducidad con Redis/worker real: `docker compose exec -T app python < scripts/probe_expiry_worker.py`; con Beat sin envío manual: `docker compose exec -T app python - --beat < scripts/probe_expiry_worker.py`. Solo desarrollo: crea registros sintéticos aislados, sin revisión aprobada y siempre inelegibles públicamente; no resetea la muestra. Contrastar logs worker/Beat con el estado/evento PostgreSQL. Celery ignora resultados: el probe consulta el estado real, no interpreta AsyncResult.get como finalización.

Probe privado CR-08 de la muestra Docker: `uv run python scripts/probe_demo_lifecycle.py`. Lee credenciales sintéticas de `.ai/demo-credentials.json` sin imprimirlas; requiere favoritos vacíos del visitante y particular publicado. Guarda/elimina un favorito y prueba disponibilidad/pausa/reanudación/cancelación, terminando con ficha publicada sin disponibilidad; añade historia de acciones y no resetea datos. Si falla, revisar estado antes de repetir.
