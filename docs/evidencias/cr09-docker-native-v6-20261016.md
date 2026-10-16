# Imagen propia v6 de la agrupación integrada

Fuente7ec6f51, etiqueta `web-modelos-cr09-native:20261016-v6`, ID `sha256:621e0209f989d69a18da7c28843694dac749d41bc4dd93e272cccfac2eeb0c4b`. Construcción y comprobación real terminales0. Los hashes de publication_state/public_validation dentro de la imagen coinciden con el host. No se sustituyen etiquetas normales ni se publica.

PostgreSQL17.11 propio, migración0022 aplicada, MARK conservadora y tres triggers restaurados coincidentes con sus fuentes; helpers rechazados ausentes. Cuatro workers4sync/timeout60s preparados antes del health200. Python3.12.15/Django5.2.17/Gunicorn23.0.0/psycopg3.3.6/Celery5.6.3. UID10001/rootro/capdropall/no-newprivileges/tmpfs64MiB; app2CPU1536MiB y PG1CPU1536MiB/swap0/pids128, red interna sin puertos publicados.

Kernel native-sealed, fuente9cecbd34… y binario16dcc1cf…: además de11comparaciones válidas/negativas del smoke, batería completa **118PASS11,48s** en esta imagen, sin red y con herramientas pytest aisladas. JUnit118/0/0/0, ID de imagen y hashes de fuentes comprobados independientemente. No bytecode del host en apps/config/scripts/tests. Contenedores/red/PIDs runtime y contenedor de paridad ausentes; imagen retenida. [Recibo](cr09-docker-native-v6-20261016.json).

Esto no es una carga p95 ni N3. El arnés HTTP histórico corre Gunicorn del host, cuya identidad nativa se registra separadamente; no se atribuirán sus tiempos a esta imagen. Se conserva configuración y presupuesto del corto limpio anterior para evaluar el cambio integrado.
