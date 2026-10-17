# Regresión serial completa: fallo preservado

Ejecución `20261016-211855-8887f71c`, SHA `cd206c0b6fc509fa52e8a00be5b353f39dcb8f09`. [Recibo](cr09-common-serial-original-20261017.json).

3.476 PASS, 22 FAIL, 129 SKIP: 3.627 nodeids distintos y 3.627 elementos testcase, sin casos incompletos en el diario. Duración pytest 19.718,89 s. El atributo tests del JUnit indica 3.631 y hay 3.480 informes call aprobados: conciliado con los cuatro subTest aprobados de RoomControls.test_invalid_room_paths, además de su informe padre. Son 3.627 pruebas distintas y 3.476 pruebas aprobadas; no faltan cuatro casos. La previsión anterior de 3.626 era inexacta. Terminó antes del timeout de 21.600 s por comando.

18 fallos muestran explícitamente queues/bounded_read_limit: 16 en access_coverage_store y dos en portability_jobs. Cuatro variantes móviles de historical_logs muestran rechazo de paquete por original[blocked]; causa concreta pendiente de reproducir. Redis exclusivo observado en lectura con 1.911 mensajes; muestra acotada de 1.000, todos refresh_publication_state. No se consumió ni borró la cola ni se cambió su límite. Acumulación entre casos es hipótesis que requiere control causal.

Fuentes comparadas independientemente con source-hashes: iguales. Temporal, PID original del runner/hijo y los dos contenedores declarados ausentes; unidad terminal/MainPID0. Fallo original preservado; no aceptación CR09/N3. Las omisiones requieren conciliación y los seis controles de contenido aislado siguen pendientes de evidencia vigente.
