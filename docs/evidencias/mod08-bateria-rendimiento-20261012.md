# MOD-08 — batería y rendimiento, 2026-10-12

Por petición del usuario se fijó performance mediante power-profiles-daemon y se
 desactivó el cambio automático por cargador/batería. Estado anterior: power-saver,
 automatismo activo. CPU EPP y plataforma quedaron en performance. No se forzaron
 frecuencias ni se desactivaron protecciones térmicas. Governor intel_pstate sigue
 mostrando powersave; la preferencia EPP comprobada es performance.

Escenario normal completo, código actual con transporte original, sin perfiladores:
artifacts/capacity-environment/20261011-232221-3fc0bca2.
1 PASS en 903,803 s; cero fallos, errores o skips.
DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3.

| p95 máximo entre casos | Resultado (ms) | Resultado (s) | Límite (s) | Margen (ms) |
| --- | ---: | ---: | ---: | ---: |
| Navegación | 1576,682 | 1,576682 | 2 | 423,318 |
| JSON | 4163,148 | 4,163148 | 5 | 836,852 |
| Binario | 3997,933 | 3,997933 | 5 | 1002,067 |

Dos casos concurrentes, 384 navegaciones y 20 descargas por tipo/caso,
fuente 16 MiB y originales aproximadamente 64 MiB; entregas por partes.
Mismas cuotas y comprobaciones del escenario anterior. Errores funcionales: ninguno.
Comprobación independiente de 1.405 huellas exactas antes de esta documentación.
Contenedores, volúmenes y red propios ausentes tras terminar.

Inicio: cargador desconectado, batería 49 %, performance, automatismo desactivado.
Final: cargador desconectado, batería 28 %, performance, automatismo desactivado.
Comprobaciones periódicas mantuvieron performance, sin degradación reportada.
Registros energy-start.json y energy-end.json guardados junto al resultado;
[resumen estructurado](mod08-bateria-rendimiento-20261012.json).

Se demuestra cumplimiento local en batería bajo esta configuración. No demuestra
estabilidad estadística entre ejecuciones, aceptación global/N3 ni qué fracción de
la diferencia histórica causó la energía. No hubo optimización de código en esta
prueba. El control previo sin energía identificada dio 1,626706/3,864846/3,840579 s:
variación mixta, no ahorro causal atribuible. No repetir indefinidamente sin hipótesis.
Perfil performance y automatismo desactivado se dejan como autorizó el usuario.
