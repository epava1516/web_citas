# Aislamiento de broker entre casos de CI

Regresión original: 3.476 PASS/22 FAIL/129 SKIP, 3.627 pruebas distintas; cuatro subTest explican estadísticas JUnit. Evidencia original preservada. Redis propio acumuló 1.911 tareas; muestra de 1.000 refresh_publication_state.

Control causal 025610-dcab715e: 1PASS, 1.000 tareas permiten inspección y 1.001 bloquean sin consumir. Control nuevo broker 025146-14254ec0: dos consumidores originales PASS. Primera corrección 030003-d2d6e91a:20PASS/2FAIL por productor con pool antiguo. Corrección de pools 031854-3e804dce:4PASS. Misma versión contra22 originales 032029-91cbdb8e:22PASS/0FAIL/0SKIP. Herencia real a subproceso y publicación de nueva generación 033807-4eb6fd2d:3PASS/0SKIP. Cada ejecución con fuentes y limpieza verificadas independientemente y recibos retenidos en esta carpeta. Primer causal omitido por variable filtrada conservado, no PASS funcional.

Runner añade --isolate-test-broker explícito; plugin exclusivo de CI verifica etiqueta y puerto Redis local, asigna generación aleatoria por caso y renueva pools entre casos. Subprocesos heredan generación. No se eliminan mensajes previos ni se cambia límite/eager/semántica de producto. Probado serial; no acreditado aislamiento xdist. Los controles de dos casos usan estado de módulo y requieren orden serial (perfil actual), no son garantía bajo distribución arbitraria.

Grafo AST actualizado con los instrumentos y controles; clustering antes de la siguiente batería, sin extracción semántica completa de docs. AST0 tokens de modelo; consumo histórico no reportado preservado. No medición nueva de p95, no aceptación CR09/N3. Próximo: batería común serial con corrección vigente, omisiones y controles separados, y medición contractual válida.
