# Imagen local v10: corrección RateForm integrada

Fuente `ee2d550`, imagen `web-modelos-cr09-native:20261016-v10`, ID `sha256:04b48f46291d3403e08b369b2a68279f3d45b0b303ea0dad1c45318b5c856234`. Build y verificación corregida **PASS**. [Recibo](cr09-docker-native-v10-20261016.json).

El módulo de formularios coincide por SHA256 entre host e imagen. Se comprueba que RateForm declara exactamente concept/mode/amount/duration_minutes en una tupla y que instanciar RateFormSet no modifica esa declaración. Las ocho rutas públicas responden200/no-store; cuatro destinos firmados son correctos. Salud200, detalle inexistente404, cuatro workers preparados, DEBUG0, once paridades nativas, migración0022 y funciones conservadoras verificadas.

Primer intento de verificación FAIL preservado: aserción de nombres de campos incorrecta en el instrumento; wrapper no conservaba stderr del hijo, así que la causa exacta de ese subprocess no se da por probada. Correctiva exclusivamente del verificador y repetición sobre la misma imagen, sin rebuild. Recursos sintéticos propios; PG real17.11, app2CPU/1536MiB, PG1CPU/1536MiB, swap0, red interna sin puertos, UID10001/rootRO/capdrop/no-new-privileges. Unidad terminal0, freeze, identidad de imagen, cuotas y ausencia de contenedores/red/PID comprobados independientemente.

No push ni nueva medición de capacidad; no prueba de worker/Beat o replay autenticado en contenedor. No aceptación N3/CR09. Imágenes previas conservadas.
