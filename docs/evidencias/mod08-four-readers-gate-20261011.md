# MOD-08: candidata de cuatro lectores físicos

Gate PostgreSQL/RustFS real 20261011-072544-e4d007eb: 99 pruebas aprobadas sin fallos, errores ni omisiones. 1156 hashes y retirada propia verificados independientemente. Candidata21424e1; integración local para medición.

Máximo cuatro trabajos pendientes y cuatro lectores; preserva cada GET, EOF, contexto, tombstones, claves frescas, orden de errores y cierre. Prueba real28objetos/84GETs; segunda operación168GETs acumulados con ocho clientes cerrados. Negativos físicos y sellos enforced incluidos. Diagnóstico acotado a4workers con rechazo de un quinto.

La anterior concurrencia era2. Mayor concurrencia puede aumentar buffers, CPU y transportes; requiere medición completa bajo cuotas4CPU/8GiB. No ganancia temporal acreditada ni aceptación dos casos/N3.
