# Imagen propia v9 — cierre de representación integrado

Fuente `f4125c9934cb856cd3e6dc38aad16e51772822b6`. Imagen local `web-modelos-cr09-native:20261016-v9`, ID `sha256:38272bd00161ae3f7601b033120518ee4a01b9faab343e6d9a1a9d9d09d4633d`. Build y runtime PostgreSQL real **PASS**. [Recibo verificable](cr09-docker-native-v9-20261016.json).

Incluye la corrección privada del replay HTTP. La huella del módulo `rights_responses.py` coincide entre host e imagen. La petición anónima a respuestas devuelve302 al login; el cierre y replay autenticados están probados por los [siete casos CI separados](cr09-representation-http-replay-fixed-20261016.md), no por ese redirect.

DEBUG=False explícito; PostgreSQL17.11 y migración0022, MARK y tres funciones conservadoras exactas, helpers rechazados ausentes. Cuatro workers preparados antes de salud200; UUID inexistente404. Listado/búsqueda ES/EN y detalle individual/agencia ES/EN: ocho rutas200/no-store y cuatro destinos firmados exactos. Once casos de paridad nativa ejecutados; evidencia118 de v6 conservada por identidad completa del kernel, sin ejecución nueva de esos118.

Python3.12.15/Django5.2.17/Gunicorn23.0.0/psycopg3.3.6/Celery5.6.3. App2CPU/1536MiB y PG1CPU/1536MiB, swap0/pids128, afinidades0–3/4. UID10001, raízRO, capdropALL/no-new-privileges, red interna sin puertos publicados y medios privados tmpfs64MiB. Identidad de la siembra simulada explícitamente y eager sólo en ese proceso; HTTP/PG/kernel reales locales. No prueba recepción externa ni worker/Beat.

Unidad terminal0/MainPID0; fuentes congeladas, identidad de imagen, cuotas y ausencia de app/PG/red comprobadas independientemente. Artefactos completos en `artifacts/cr09-docker-native-v9-20261016/`. Imágenes v8/v9 retenidas; sin push/despliegue. No nueva métrica: último corto limpio0,862172866sFAIL. N3 y CR09 siguen abiertos.
