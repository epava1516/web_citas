# B07 — memoria del procesamiento terminal

B07-294: eliminada una decodificación JSON duplicada y liberadas referencias temporales del controlador. Reproducción terminal aislada con informe idéntico byte a byte: pico RSS de134.246.400 a96.276.480bytes;79pruebasPASS. No reproduce OOM histórico ni acepta293; B07 abierto, ocho de18.

## Evidencia y límites

Después de auditar293, consultar grafo340 porArchiveSink (BFS2,32nodos,12mostrados por presupuesto) y contrastar scripts/check_capacity_environment.py y scripts/capacity_artifacts.py, se preparó una reproducción finita del procesamiento terminal. Usa el JUnit293 original SHA2565635c08bed1b99fbaaca550597e08b85e2e8da17fb8981bd80310d35b9f549e8, XML, dos decodificaciones del mismo proof y ArchiveSink reales. Docker imagen385, usuario local, rednone, raízreadonly,128MiBRAMswap0,0,1CPU, límite180s y limpieza por nombre. Sin PostgreSQL, HTTP ni simulación de verificación del producto: prueba aislada de procesamiento de artefactos.

La versión mínima completa sin OOM con picoRSS132145152bytes. La versión con importaciones reales también termina0 y OOMKilledFalse, picoRSS134246400bytes. Los dos comandos esperaban OOM: sus aserciones fallan y se conservan como EXIT1, con Telegramsent. El primero también usa comparación de error Docker sensible a mayúsculas; ausencia actual confirmada y segunda limpieza corregida. No ocultar esos negativos ni presentarlos como reproducción del fallo293. La identidad exacta del cgroup histórico no ha podido acreditarse con metadata conservada; OOM temporal sigue como correlación.

## Corrección acotada

El modo corto/contractual decodificaba dos veces el mismo JSON: la primera instancia quedaba en report y la segunda en proof. Ahora reutiliza report[proof_key]. Antes de recoger recursos y serializar el informe, libera referencias locales XML y propiedades; el informe conserva su prueba. No cambia escenario, emisor, GC, puertas, duración,workers,recursos ni cuotas. La ruta funcional conserva su decodificación original.

El replay corregido ejecuta las expresiones AST reales de reutilización y liberación desde el controlador actual; importa el módulo completo y procesa el mismo JUnit con ArchiveSink. Termina0,OOMKilledFalse y conserva el report.json byte a byte respecto al replay con importaciones reales; SHA256674cc6676b61b42cfb7162e0d79b2b6cdbfb73ca7f1cdf8ca8c9f3892fa99dd5. PicoRSS96276480bytes frente a134246400 de la ejecución anterior. El pico no es una medición de memoria global ni equivalencia de todo el controlador; prueba esta retención/serialización aislada. No atribuir causalidad histórica desde esa reducción.

Guardas79PASS10,95s en tests/test_vps_capacity_handoff.py y tests/test_capacity_artifacts.py; Ruff controladorPASS. Recibos terminales Telegram de todas las ejecuciones conservados. Producto628 intacto; originales293 y replay inicial intactos. Sin nuevas invocacionesClaudeV1 (ocho históricas), consumo preservado.

## Siguiente decisión

Actualizar AST del único controlador cambiado y semántica dirigida antes de cualquier nueva congelación. Falta demostrar el controlador completo con estos cambios, informe final, recursos y limpieza. El resultado293 sigue no aceptado y no se convierte en PASS por reconstrucción. No repetir automáticamente una carga900s; revisar presupuesto y corrección terminal antes de decidir una nueva ejecución. B07 continúa abierto y el objetivo completo conserva su alcance.
