# B16-369 — Auditoría terminal del control HTTP corto

La ejecución `20261024-221417-1150e8ef` terminó con `BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL`: un caso, cero fallos, errores u omisiones; 5939,701 segundos JUnit (98 min 59 s). El [protocolo331](331-control-corto-http-vigente-b16-20261024.md) sigue siendo el prerregistro original y no se reescribe como aceptación.

Con 10000 perfiles sintéticos y 96 slots, la ventana de 60 segundos emitió y completó las 1200 peticiones previstas y una subida, sin errores, pérdidas, pendientes ni timeouts. El p95 observable fue 451,099 ms frente al límite estricto de 800 ms. El generador presentó p95 3,143 ms, p99 6,748 ms y máximo 33,356 ms, dentro de 10/25/100 ms. Todos los controles cortos originales resultaron verdaderos. Esto acredita esta ventana, no 900 segundos sostenidos.

Antes de editar documentación se contrastaron las 1723 fuentes del prerregistro, manifiesto original y árbol actual; coincidieron. Grafo, protocolo, especificación y ocho helpers también conservaron sus SHA. La propiedad JUnit coincide exactamente con el resultado HTTP del informe. El archivo completo se pudo leer: 74 miembros. La limpieza informada se contrastó independientemente mediante las etiquetas exactas de contenedores, redes y volúmenes: ninguno permanece.

El límite superior conservador de memoria propio fue 2282180608 bytes y el techo de almacenamiento 4865392640 bytes; todos los servicios registraron cero OOM y swap pico cero. Estos números no representan picos simultáneos ni capacidad universal. Los pagos, población y medios siguen siendo sintéticos. No hay atribución causal de mejora frente a otra imagen o entorno.

El envío terminal de Telegram figura confirmado. La [evidencia de auditoría](evidencias/b16-short-http-terminal-audit-20261025.json) conserva métricas, fuentes, limpieza y SHA del archivo. Queda conciliar la medición contractual de 900 segundos sobre la candidata actual antes de aceptar B16. No se ha lanzado otra batería por este resultado; B16 permanece abierto, 14/18 puntos cerrados y proyecto en alfa.
