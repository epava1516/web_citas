# Arranque Gunicorn: revisión acotada de preload

[Probe aislado](cr09-preload-source-audit-20261016.json), fuentee55b282: intérprete nuevo importa config.wsgi con socket.connect/connect_ex bloqueados. Cero intentos de conexión, cero conexiones Django abiertas y un único thread. Formularios y public_validation ya importados;config.urls/discovery y loader canónico no importados. Sin petición HTTP ni compilación de plantillas. No prueba seguridad general de extensiones nativas tras fork.

Fuente instalada Gunicorn23:Arbiter.setup llama app.wsgi antes del fork si preload_app;Worker.init_process normalmente llama load_wsgi antes de post_worker_init y run. [Árbitro oficial23](https://github.com/benoitc/gunicorn/blob/23.0.0/gunicorn/arbiter.py). Django recomienda evitar consultas en ready; el probe acredita sólo esta importación concreta. [Django5.2](https://docs.djangoproject.com/en/5.2/ref/applications/).

Los workers ya cargan WSGI antes de aceptar solicitudes; todos entraron al comienzo del intervalo en diagnósticos anteriores. Preload simple no elimina por sí solo trabajo lazy de rutas/plantillas/SQL. Beneficio para el atasco no demostrado: no cambiar runtime ni ejecutar otroclean por esta opción. No precarga de autoridad ni calentamiento fuera del escenario.

Desajuste pendiente: Dockerfile predetermina2workers/45s; corto usa4sync/65s y8sync es experimental aislado fallido. compose no sustituye el comando. Requiere topología real común y verificada antes de aceptación; no cambiarla a8 ni prometer capacidad a partir de pruebas parciales.

No p95nuevo: referencia4sync1,218890sFAIL y8nativo1,792941sFAIL conservadas. No aplicación/Docker/servicios modificados; CR09/N3 abiertos.
