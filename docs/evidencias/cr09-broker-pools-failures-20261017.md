# Verificación de los 22 fallos originales

[Recibo](cr09-broker-pools-failures-20261017.json). Ejecución 032029-91cbdb8e: 22 PASS, cero fallos y omisiones, mismos nodeids de la regresión original. Plugin opt-in usa generaciones por caso y renueva pools entre casos, conserva mensajes anteriores hasta retirar Redis exclusivo. Aserciones y producto sin cambios. Fuentes y limpieza verificadas independientemente.

Control causal real 1000/1001, control entre casos con backlog preservado, publicación en cola actual y dos jobs verifican mecanismo y corrección local. Primera versión 20PASS/2FAIL preservada. No convierte regresión original en PASS; pendiente ejecutar batería común con instrumento vigente, controles de herencia/subprocesos, omisiones y medición contractual válida. CR09/N3 abiertos.
