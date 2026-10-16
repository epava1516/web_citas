FROM python:3.12.15-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --python /usr/local/bin/python
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
RUN uv venv --python /usr/local/bin/python /opt/canonical-build \
    && uv pip install --python /opt/canonical-build/bin/python 'Cython==3.0.12'
COPY scripts/build_canonical_kernel.py scripts/canonical_artifacts.py /app/scripts/
COPY apps/safety/_canonical_kernel.pyx /app/apps/safety/
RUN /opt/canonical-build/bin/python scripts/build_canonical_kernel.py
FROM python:3.12.15-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --chown=app:app . /app
COPY --from=build /app/apps/safety/_canonical_native /app/apps/safety/_canonical_native
RUN python -c "from apps.safety.canonical_kernel_loader import kernel_identity; assert kernel_identity()['mode'] == 'native-sealed'"
RUN mkdir -p /app/media/private /app/media/delivery /app/staticfiles && chown -R app:app /app/media /app/staticfiles
USER app
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60", "--access-logfile", "-", "--logger-class", "config.gunicorn_logging.SafeAccessLogger"]
