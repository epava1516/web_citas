# B07 — estado terminal durable del controlador

B07-295: launcher conserva identidad y estado terminal del controlador antes de limpiar; éxito exige exited/0 sin OOM. Tres sondas Docker distinguen normal,137 explícito y OOM real;89pruebasPASS. Sin carga contractual ni aceptación293; B07 abierto, ocho de18.

## Motivo y alcance

Contrato16§16 exige reutilizar controles válidos y ejecutar sólo los justificados por el cambio. Grafo341 consultado para launcher, BFS2 con816nodos, presupuesto500truncado; contraste directo del finally y success de scripts/run_capacity_environment.py y protocolos253/254. El controlador293 terminó137 y sinreport.json; la eliminación automática impidió recuperar identidad/State.OOMKilled para relacionar inequívocamente el OOM temporal del kernel.294 reduce retención aislada sin probar causa histórica. No se acepta293 ni se repite carga en este paso.

## Cambio

El launcher deja de usar --rm en el controlador; su finally ya elimina explícitamente todos los recursos por nombre y comprueba ausencia. Antes de eliminar, captura sólo id,status,running,exit_code,oom_killed,started_at,finished_at mediante plantilla Docker acotada; no exporta Config,State.Error,entorno,credenciales ni logs. Valida estructura y tipos; captura fallos por clase sin stdout/stderr. Guarda controller_terminal_state en launcher.json junto al resto de evidencia. Éxito exige exited,runningFalse,exit0,OOMFalse además de todos los controles anteriores. Timeout, falta de estado o137 no se convierten en PASS.

La captura es terminal, fuera de la ventana HTTP y del controlador medido. Sin cambios a CPU,RAM,swap,workers,fixture,generador,GC,puertas,uploads o duración. Sin cambio de producto. El controlador128MiB y la reducción294 se conservan.

## Verificación

89PASS9,88s: tests/test_capacity_failure_states.py, tests/test_capacity_preflight_contract.py y tests/test_vps_capacity_handoff.py. Incluyen identidad137/OOM, fallos de inspección sin filtrar stderr y rechazo de booleano mal tipado; pruebas de lifecycle y modos existentes. Ruff de launcher y guardasPASS.

Sondas Docker reales aisladas32MiBswap0/0,1CPU/rednone/readonly/usuario local/capdropimage385: (1) normalexit0,OOMFalse; (2) SystemExit137,OOMFalse; (3) bytearray128MiB bajo32MiB,exit137,OOMTrue. La función real captura IDs distintos y horas terminales. Retiene cada contenedor hasta inspección y después comprueba ausencia por nombre. No es carga, prueba PostgreSQL ni capacidad: verifica que el observador distingue dos causas que comparten código137. Artefacto terminal295-native-proof.json, avisos Telegramsent de cada comando.

Sin nuevos proveedores, publicación, sujetos reales ni invocacionesClaude; ochoClaudeV1 y consumo histórico preservados. Negativos293 y294 intactos.

## Siguiente

Actualizar AST de launcher y guardas, semántica dirigida y congelación antes de otra medida. Preparar una única validación contractual posterior a las correcciones294/295 sólo tras revisar presupuesto y reutilizar funcionales285/288/289 y corto291 válidos. Helpers nuevos deben recoger el recibo HOST antes de intentar leer un report posiblemente ausente, conservando datos terminales y prohibiendo reintento automático. El contrato completo sigue abierto y no se estrecha al PASS de estas sondas.
