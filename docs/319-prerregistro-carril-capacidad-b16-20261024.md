# B16-358 — Prerregistro del carril serial de capacidad

Estado al redactar: preparado, no ejecutado ni aceptado. Tras verificar la matriz357 se autoriza continuar la verificación necesaria del contrato con el carril ordinario capacity. No es un nuevo ensayo contractual de carga ni acepta SLO por el nombre de sus pruebas.

## Selección e identidad

Se esperan306nodeids únicos en59archivos: los archivos de este carril y las versiones pyproject/uv.lock coinciden con la colección352 del mismo día. Tres archivos cambiaron frente al testigo anterior del18/10; por tanto, aquél no basta como ejecución de la candidata actual. La selección real se verificará en journal/JUnit terminal, no se acreditará ejecución desde la colección reutilizada.

Hash SHA256 del conjunto esperado, codificado como json.dumps(sorted(nodeids)):

`5a4d9a49eea06f168959a40483a3303e7d8b2d0e7806cae36220a2cb72cefef2`

Comando sobre la candidata local:

```sh
.venv/bin/python scripts/run_local_ci.py --profile regression --regression-lane capacity --workers 1 --fixture-snapshots --isolate-test-broker --native-source /tmp/web-modelos-librdb-v2.4.0 --timeout 21600
```

El runner conserva sus exclusiones oficiales. Los306casos contienen verificaciones funcionales de instrumentos y escenarios acotados; cualquier SKIP y las11exclusiones oficiales requieren disposición aparte y nunca cuentan como PASS. No se interpretarán diagnósticos TCP de este carril como aceptación de capacidad contractual. PostgreSQL17/Redis7.4 locales, herramientas RDB fijadas y dependencias disponibles sin descargas ni proveedores; configuración efectiva e identidades se archivarán por el runner.

## Congelación, espera y retorno

Antes de lanzar: documentación y grafo dirigidos actualizados, diff revisado, preflight de imágenes/fuentes/selección/control y commit/push. Se congela el mapa completo de fuentes del runner y el protocolo por bytes/SHA. No modificar fuentes, .ai o .graphifyignore durante la ejecución. Los controles ignorados en artifacts guardan el identificador real, PID/start_ticks, recibos y fuentes. No reiniciar por una observación agotada.

La referencia histórica de este carril es3077s (~51min), no garantía de duración actual. La shell persistente emitirá aviso terminal después de limpieza. Antes de pausar el mismo goal se confirmarán arranque persistente y Telegram previo, y se informará en chat. Se conserva el procedimiento autorizado de reactivación del mismo objetivo al terminar, sin cambiar texto ni reiniciar consumo; los fallos del disparador se registran y avisan. La compactación sólo se solicita con goal pausado e hilo idle, conservando el relevo.

La anterior compactación353 no quedó confirmada por eventos. El control358 separa ACK de finalización y comprueba un nuevo item contextCompaction persistido en un turno completed, mediante paginación de historial sin reanudar el hilo. La [documentación oficial de App Server](https://learn.chatgpt.com/docs/app-server) distingue la respuesta inmediata de compact/start del ciclo posterior de eventos y ofrece thread/turns/list para leer el historial. El endpoint y la identidad del mismo goal se verifican antes de armar el control. No se afirmará compactación completada sólo por recibir ACK.

Al retorno: auditar conjunto exacto306, resultados únicos frente a subreportes, SKIP/FAIL/ERROR, fuentes, limpieza real y recibos. Conservar cualquier fallo y diagnosticar antes de otra batería. B16 sigue abierto hasta la matriz de requisitos, cobertura/capacidad aplicable y disposición de pendientes. B10 conserva su residual; B14 no tiene proveedores elegidos; B15 es opcional y B17 no autoriza apertura. Proyecto en alfa. Reconstrucción completa del grafo y diferencial del inventario son obligaciones finales posteriores.
