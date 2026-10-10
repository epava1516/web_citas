# MOD-08 — snapshots de bootstrap por worker

Opt-in: `scripts/run_local_ci.py --fixture-snapshots`. El consumidor real es
la fixture `directory`: conserva `seed_demo` como fallback y cachea únicamente
el bootstrap sintético de directorio, PostgreSQL y medios. No incluye lecturas,
aprobaciones, cobertura ni decisiones de derechos. Las pruebas de aceptación
siguen ejecutando sus lecturas reales.

La primera llamada con base vacía crea una plantilla PostgreSQL y copia medios
bajo el temporal privado del runner; las siguientes recrean la base de ese worker
con `CREATE DATABASE … TEMPLATE`, después de cerrar conexiones Django. Se exige
cero conexiones en `pg_stat_activity`; no se termina ningún backend. La plantilla
rechaza conexiones y permanece en el contenedor desechable hasta su retirada.
Los medios se copian a cada `tmp_path` de prueba: mutarlos no modifica la plantilla.
La fixture respeta cualquier preparación previa de datos mediante fallback al
constructor original, en vez de borrarla para forzar el snapshot.

Guards: settings `local_ci_settings`, PostgreSQL loopback/usuario `ci`, nombre
exacto `test_promotion_gate_ci[_gwN]`, identificador propio del run y medios dentro
de su temporal. Fuera del opt-in no se clona ni elimina una base. Caché aislada por
run/worker y hash de fuentes apps/config/fixtures más configuración relevante de
claves, proveedores, almacenamiento y hashers. Los secretos se usan en el hash,
nunca se imprimen.

Selección finita PostgreSQL antes de ejecutar: `test_directory_snapshot.py` entero
más `test_discovery.py` entero, `--workers 2 --fixture-snapshots`, PG17/Redis7.4
propios, nativos propios según runner; cero skips, fuentes congeladas, JUnit y
retirada comprobada. La prueba específica modifica usuario/medio, reproduce flush
del teardown y comprueba restauración exacta sin segunda invocación del constructor,
y separación de nombres de plantilla por worker. Fuera de esa selección el caso
PG específico se reserva explícitamente; su skip no acredita el control.

N1 puro ejecutado: fallback y rechazo de entorno ajeno, 2 PASS, 0,27s (un caso
PG no seleccionado). No acredita integración, aislamiento PostgreSQL ni rendimiento.
PG de la selección anterior pendiente; no se declara PASS ni ahorro medido.

Reserva coordinada con principal: misma selección completa de ambos archivos,
incluye fallback con usuario preexistente y rechazo de alias normal. Ejecutar con
runner desacoplado, recursos propios sin cargas, 7.200s por paso. Árbol a1ea
congelado desde lanzamiento hasta resultado terminal; hashes del runner son fuente
autoritativa, resultados negativos y limpieza se conservan.

Terminal N2 `20261010-122727-3d9c84f3`: **15 PASS, cero fallos/errores/skips,
78,881s JUnit**; fuentes sin cambios, PG/Redis propios retirados con inspect exacto.
Incluye todos los casos del directorio y la reconstrucción DB/media, fallback
preexistente y guards. [Evidencia saneada](evidencias/mod08-fixture-snapshots-n2-20261010.json).
No se declara reducción medida de tiempo ni capacidad/SLO/N3; el ahorro estructural
verificado es que la segunda restauración no vuelve a ejecutar `seed_demo`.

Refuerzo de propiedad del recurso: antes de clonar, `docker container inspect`
comprueba nombre exacto `web-modelos-ci-pg-<run>`, etiqueta de run, estado Running
y publicación 5432 en el host/puerto de la conexión Django. La verificación se
cachea por run/worker/container/puerto. N1 puro del refuerzo: seis casos PASS,
0,16s, incluye etiquetas/puertos ajenos rechazados y caché aislada por worker.
No se repite la N2 de quince casos: algoritmo de clonación/restauración intacto;
este refuerzo añade una precondición de identidad comprobada mediante dobles en N1.
