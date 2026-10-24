# B07 — Evidencia de servicios fallidos antes de limpieza

B07-248 auditado: 44 pruebas PASS y preflight PostgreSQL/S3/Celery/Beat real PASS; limpieza y Telegram confirmados. Captura terminal añadida; causa247 desconocida, HTTP mixto1000 pendiente. 8 de 18, B07 abierto.

## Hallazgo y cambio

El control247 terminó antes de pytest con PostgreSQL detenido. La auditoría negativa verificó fuentes, protocolo y limpieza. Docker events del intervalo no devolvió registros y journalctl kernel no devolvió entradas OOM; esa ausencia no prueba que no hubiera OOM. No se conoce aún la causa.

El arnés ahora consulta el estado de cada servicio antes de eliminarlo cuando existe un error de ejecución. Conserva únicamente estado, running, exit code, OOMKilled e instantes de inicio y fin. No exporta configuración, entorno, argumentos privados ni el campo Error del daemon. Una inspección fallida o un timeout se registran por servicio y permiten continuar con los demás y la limpieza. Es observación posterior al fallo, sin cambiar cuotas, tiempos, generador, workers, oráculos o producto. No recupera retroactivamente el estado ya eliminado en247.

## Verificación y límites

Ruff PASS y 44 pruebas PASS en 9.00 s: nuevo caso de servicio detenido con exit137 y OOMKilled=true, hermano ausente, timeout y continuación; más guards existentes del arnés. El caso usa un ejecutor controlado y no acredita un arranque real PostgreSQL. Recibos de calidad y pytest: delivery sent. Los resultados247 y el primer fallo de auditoría se conservan. Producto628 del corte B13 intacto.

Siguiente acción: preflight propio con PostgreSQL17, imagen local inmutable y recursos autorizados; conservar estado terminal si falla. No repetir automáticamente la carga ni atribuir el problema al producto sin evidencia. La aceptación de B07 sigue pendiente según contrato16, roadmap103 y matriz180.

## Preflight248 auditado

Ejecución `20261022-144015-1b6de486`: READY_NOT_CAPACITY, un caso PASS en 70.789 s de JUnit, sin errores ni saltos. PostgreSQL17, Redis7.4, S3/proxy propios y generación/purgado mediante Celery/Beat reales locales; datos sintéticos. El preflight usa dos workers Gunicorn: no acredita los cuatro ni la carga HTTP del protocolo219. Auditoría `artifacts/beta-promotion-fix-20261020/startup248-preflight-audit.json`: 1700 fuentes congeladas coincidentes, producto628 intacto, cuotas kernel8CPU/8GiB/swap0 y ausencia actual de todos los recursos comprobada por nombre exacto; proceso finalizado. Avisos de prueba y auditoría entregados.

El arranque exitoso no identifica la causa247. No declarar corregido PostgreSQL ni convertir247 en PASS. La captura de estado es una mejora diagnóstica cubierta por prueba controlada; en este preflight exitoso no se ejercitó una terminación fallida real. La siguiente ejecución pertinente será el HTTP mixto1000 con esta instrumentación, mismo escenario y criterios originales, preservando ambos resultados; requiere nuevo prerregistro y congelación, sin subir recursos o umbrales.
