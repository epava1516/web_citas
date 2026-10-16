# Diagnóstico de carga: selección de workers fallida

[Recibo](cr09-load-worker-pyspy-original-20261016.json). Control previo py-spy attach propio: tool0/199muestras, proceso objetivo vivo tras duración y recogido al terminarlo. Ningún cambio de Yama, permisos ni versión.

El intento real `20261016-145039-c676f65f` terminó con controlador1: el selector de descendientes no encontró master con exactamente cuatro hijos. Causa sin demostrar; cero capturas y ningún perfilador adjuntado. El finally dejó terminar el CI y su limpieza. No cambiar el selector a búsqueda global de procesos ni capturar servicios ajenos.

| Carga | p95 observable | Resultado |
|---|---:|---|
| Limpia anterior131431 |0,862172866s|FAIL|
| Intento diagnóstico145039, sin attach efectivo|0,738744505s|CI PASS / diagnóstico FAIL|

La carga completó1200/1200, sin errores/timeouts/pendientes y sin razones de invalidez, cuatro workers sync. No cambio de producto entre ambas muestras ni atribución causal al código/hardware. Unidad terminal/MainPID0, fuente congelada y ausencia independiente de runner/hijo/temporales/PG/Redis verificadas. No repetición automática/900 ni aceptación CR09/N3: falta explicación y serie de reproducibilidad definida.

Siguiente paso técnico: comprobar el selector en árbol Gunicorn desechable propio sin carga contractual, conservando esta negativa antes de repetir ningún diagnóstico. La señal de alineamiento apareció; la captura falló antes de seleccionar PIDs.
