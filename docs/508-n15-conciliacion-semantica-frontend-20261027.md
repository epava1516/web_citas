# N15 — conciliación semántica de la entrega de frontend

La [entrega507](507-n15-base-y-contratos-frontend-20261027.md), enviada en
`7cca6fc`, está incorporada al grafo reconstruido en [503](503-n15-grafo-total-reconstruido-y-verificado-20261027.md).
La [verificación independiente](evidencias/n15-grafo-frontend-verificacion-20261027.json)
contrasta el grafo publicado, las fuentes, las identidades, las comunidades y
las salidas. No se ha repetido extracción completa, QA ni medición de aplicación.

| Medida | Después del inventario505 | Después de la entrega507 |
| --- | ---: | ---: |
| Fuentes del corpus | 2189 | 2193 |
| Nodos | 17188 | 18335 |
| Relaciones dirigidas, con multiplicidad | 76824 | 79311 |
| Comunidades | 757 | 758 |
| Identidades actuales de acciones | 444 | 444 |
| IDs originales preservados | 443 | 443 |
| Nodos AST completos preservados | 11126 | 11126 |
| Relaciones AST completas preservadas | 56021 | 56021 |

SHA256 del corte posterior:
`4483d564a931f894e9c2d45b4a3848ba9c11151ede8a32633bf755c1b358ba42`.
Se incorporaron 170 contratos de ruta, 687 retornos exteriores, 110 formularios,
129 plantillas y 36 guardas. Las 170 rutas enlazan a su handler AST y a su
identidad actual del inventario. Las guardas globales constan con sus límites;
su presencia no afirma que toda respuesta atraviese todos los middleware.

El delta conserva exactamente los nodos y la multiplicidad de las relaciones
AST del corte completo inicial, sin extremos inexistentes, pérdida de miembros
de hiperaristas o nodos fuera de comunidades. Las fuentes del manifiesto y las
huellas de las salidas coincidieron en la auditoría. Se retiraron dos declaraciones
documentales sustituidas; una referencia histórica conserva su identidad con
procedencia anterior explícita, sin fingir una fuente actual.

El JSON completo sigue en `graphify-out/graph.json`; el HTML representa comunidades.
Las estadísticas de rankings anteriores conservan su corte histórico. Consumo
nativo no disponible: no se informa como cero. Este delta no añadió delegaciones.
El censo N15 mantiene 35 tareas nativas, con V1 nuevo cero e histórico ocho.

Este documento y el certificado describen el corte de entrega507 y se incorporarán
con el resumen y el acta en la conciliación documental final. No se presupone que
el grafo ya contenga un archivo creado después de esa auditoría.

N15 permanece abierto: quedan acta y registro Git, resumen duradero y limpieza
íntegra de `artifacts` como última operación obligatoria. La aceptación de los
otros once bloques y la [deuda viva](deuda-pendiente-viva.md) conservan sus límites;
N02 no pasa a PASS y N12–N14 no se activan. Alpha/noindex sigue vigente.
