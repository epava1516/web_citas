# Imagen propia v8 — plantilla de detalle integrada

Fuente `9d122b06b42b9eb704568870a9329da8d4f1af8b` (producto de lectura af914b9). Imagen local `web-modelos-cr09-native:20261016-v8`, ID `sha256:cab33d24a2412881bc3bfb0e718decb8c662c75ee74c6ffff4c13c2d5ba58512`. Build y runtime PostgreSQL real **PASS**. [Recibo verificable](cr09-docker-native-v8-20261016.json).

La pasada final usa `DJANGO_DEBUG=0` explícito y contrasta `settings.DEBUG=False`; la primera pasada satisfactoria con configuración de desarrollo por defecto se conserva en `artifacts/cr09-docker-native-v8-20261016/initial-default-debug`, sin atribuirle esa comprobación. Se reutilizó la misma imagen para la segunda verificación, sin recompilar.

| Comprobación | Resultado final |
|---|---|
| Código y etiqueta de revisión | Hashes host/imagen coincidentes; fuentes congeladas comprobadas |
| PostgreSQL y esquema | 17.11, migración0022; MARK y tres funciones conservadoras exactas; helpers rechazados ausentes |
| Arranque | Cuatro workers preparados antes de la sonda explícita de salud200 |
| Navegación sintética | Listado/búsqueda ES/EN y detalle individual/agencia ES/EN:8 rutas200/no-store |
| Destinos de denuncia firmados | Cuatro detalles ligados al listing/revision exacto |
| Negativo | UUID inexistente404 |
| Kernel nativo | native-sealed, once comparaciones ejecutadas en v8 |
| Limpieza | App/PG/red propios ausentes, sin volúmenes persistentes creados |

Python3.12.15/Django5.2.17/Gunicorn23.0.0/psycopg3.3.6/Celery5.6.3. Identidad completa del kernel idéntica a v6/v7: fuente9cecbd34… y binario16dcc1cf…. Se comprobó la evidencia118PASS de v6 y se conserva por identidad, sin presentarla como ejecución nueva en v8.

App2CPU/1536MiB, PG1CPU/1536MiB, swap0/pids128 cada uno, appafinidad0–3/PG4. UID10001, raízRO, capacidadesALL retiradas/no-new-privileges; red interna sin puertos publicados. Datos y credenciales sintéticos en tmpfs desechables, medios64MiB; nada se escribe en medios normales del host. La siembra usa simulación local de identidad y eager sólo en su propio proceso, no representa verificación real de identidad ni prueba worker/Beat. HTTP, PostgreSQL y kernel sí son reales locales.

Se conservan imágenes v7 y v8; sin push, despliegue o proveedores. No mide p95 Docker ni acredita N3/CR09. Último corto limpio del host0,862172866sFAIL, sin repetición ni900 tras ese fallo. La imagen elimina una discrepancia de versión de runtime; no resuelve por sí sola el requisito de rendimiento.
