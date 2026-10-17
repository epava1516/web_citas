# Control causal de acumulación

[Recibo](cr09-broker-accumulation-20261017.json). 025610-dcab715e: 1 PASS, cero fallos y omisiones, 1,862 s pytest. Publicación real de refresh_publication_state mediante Celery/Redis exclusivo, namespace aleatorio. 1.000 mensajes permiten inspección; 1.001 producen bounded_read_limit sin consumir; eliminar sólo namespace del control restaura inspección. Límite de producto intacto. Fuentes, temporal, PIDs y contenedores comprobados independientemente. Primer intento 025448 omitido por variable filtrada, conservado.

Demuestra mecanismo causal del bloqueo, no identifica todos los productores de la batería ni corrige su aislamiento. Dos consumidores originales aprobaron previamente con broker nuevo (025146-14254ec0). Falta aislar estado entre casos, comprobar frontera y consumidores y ejecutar regresión vigente; no aceptación CR09/N3.
