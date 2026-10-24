# B07 — Preparación contractual del combinado

B07-292: habilitado el instrumento contractual combinado de10.000 perfiles tras corto291 auditado; 61 guardas PASS. Producto628, emisor y recursos conservados. La carga900s no se ha lanzado; B07 abierto, ocho de18.

## Base y decisión

Contrato16§16 exige equivalencia → integración → escala100/1000/10000 → cortoPASS → contractual. Se reutilizan funcionales285/288/289 y corto291 auditado:1200éxitos,0errores,p95 observable414,537ms,demoras2,442/5,979/17,680ms,upload302persistido,pendientes3/final0. Fuentes1705/producto628/protocolo/limpieza/notificaciones/compactación/reactivación comprobados. Consulta grafo337 BFS113nodos/13mostrados con presupuesto700truncado, contrastada directamente con16§16,251 y código; no lectura exhaustiva.

Se decide habilitar sólo contractual combinado10000:900s,20RPS,18000dinámicas,6000porcategoría y9000poridioma,15uploads separados uno/minuto. Habilitar no constituye ejecución ni aceptación. No repetir262/265, que corresponden a otra mezcla, ni funcionales285/288/289/corto291 válidos. No reinterpreta277INVALID ni identifica su causa.

## Cambio acotado

Cuatro archivos: scripts/run_vps_capacity.py, scripts/check_capacity_environment.py, tests/test_capacity_beta_http.py, tests/test_vps_capacity_handoff.py. Lanzador/controlador permiten contractual con combinado territorial sólo10000, sin observador, backlog, committed, mezcla alternativa, calibración deuploads ni diagnóstico generador. La duración contractual900 ya existía: se evita que la rama combinada la sobrescriba a6s. Conserva15uploads/60s y gates existentes. Funcional100/1000/10000 y corto10000 preservados. Producto628 y scripts/benchmark_async_transport.py sin cambios.

61guardasPASS en1,17s después de corregir dos errores de adaptación de las pruebas (una aserción aplicada al test committed equivocado y una aserción que aún suponía sólo corto). Primer resultado59PASS/2FAIL preservado y notificado; sin ejecutar carga nativa ante fallos. Revisado diff completo de los cuatro archivos. Ruff/AST/alcance y actualización dirigida del grafo se registran mediante sus recibos antes de congelar cualquier nueva carga.

## Recursos, presupuesto y siguiente puerta

Mismos4workers sync/1thread,PG17Redis7.4,workerBeat,seisroles8CPU8GiBswap0. Watchdog18000/app18600 y límite exterior real11500s, sin ampliar. El corto291 duró5717,964sJUnit incluida preparación: añadir840s de llegadas deja margen aritmético dentro del presupuesto existente; esto no garantiza duración futura ni rendimiento. No profiler/observador ni cambioGC; mismos límites de generador10/25/100ms,0noemitidas,timeout65s,drain70s,pendientescierre≤20/final0,p95observable<800ms,errores<1%,uploadsconformes. Oráculos68antes/después,96slots62rutas y fixture7000/3000 con2000derechos permanecen.

Antes de lanzamiento separado: protocolo prerregistrado, fuentes congeladas e imágenes verificadas; auditor adaptado a18000muestras/15uploads/900s; launcher persistente, avisosinicio/prepausa recibidos y cuatro procesos identificados. Pausar mismo goal, shellcompact/autoresume según AGENTS2026-10-21, sin sondeo delmodelo. FAIL/INVALID/ERROR detienen secuencia y se preservan; sin repetición automática. Auditar el resultado antes de aceptar. No publicación, contratación ni datosreales; proveedor sintético no acredita proveedor real. B07 sigue abierto y8de18; objetivo completo conserva su alcance original.
