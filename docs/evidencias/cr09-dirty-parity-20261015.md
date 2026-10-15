# Proyección dirty: paridad parcial demostrada, beneficio insuficiente para integrar

Run220642-5af6161c, base85a5abe, prototipo preservadoc48002c en worktree aislado; **1PASS168.23s**. [Recibo](cr09-dirty-parity-terminal-20261015.json). Python3.12.15, PostgreSQL propio,10k sintéticos; mismos límites controller4CPU/3584MiB, PG1CPU/1536MiB y Redis0.2CPU/128MiB. Ningún dato/servicio normal. Fuentes congeladas idénticas verificadas antes de modificar; root/child ausentes, temporal/contenedores propios retirados, MainPID0/ControlGroupvacío.

40combinaciones de5mutaciones,4textos y páginas1/2/última aplicables. Tres bloques alternos por combinación: count eIDs ordenados iguales en las240lecturas de ambos brazos. Estado completo/versionado con1dirty; incluye cambiofecha, fechanula, texto con término nuevo, ocultar y volverapublicar. Se mide state_page real con cobertura, nativo desconocido y guardia/hidratación final, conexión fría porbrazo y corte temporal fijo. Referencia: AST de _state_page extraído de85a5abe, resto del módulo del mismo entorno. No es HTTP, capacidad ni p95; no acredita ES/ENHTML, revocación, expiración o concurrencia completa.

|Media wall por grupo|Referencia|Prototipo|
|---|---:|---:|
|Fecha|347.40ms|349.90ms|
|Ocultar|259.02ms|244.05ms|
|Fecha nula|347.57ms|331.90ms|
|Volver a publicar|316.57ms|298.07ms|
|Texto|386.34ms|362.59ms|
|Conjunto|331.38ms|317.30ms|
|CPUthread conjunto|143.88ms|149.43ms|

Wall medio−4.25%, CPUthread+3.86%; bloque0empeora324.46→328.82ms, bloque1 328.71→303.40ms, bloque2 340.97→319.69ms. No beneficio consistente suficiente para asumir complejidad/riesgo y completar toda la matriz de integración. **No integrar ni ejecutar cargaHTTP del prototipo.** Paridad sólo en casos enumerados; no se declara equivalencia general.

Siguiente diagnóstico separado: perfilar CPUthread del lector actual preservado,6lecturas reales con10k/dirty1, distinguiendo SQLwall yCPUclienteSQL. No nuevo candidato ni parámetros. Perfil instrumentado no es tiempo limpio; costes inclusivos solapados. Último p95limpio sigue1.118772sFAIL en f9f404d. CR09/N3 abiertos.
