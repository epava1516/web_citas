# N09R — corrección del acceso privado tras esperar el plan

Aceptación local limitada a la frontera seleccionada; N09 sigue abierto, con 8/13 bloques obligatorios aceptados. Alpha/noindex se mantiene. No se atribuye aceptación a comandos o runbooks de N10.

## Problema y corrección

La comprobación del permiso precedía al bloqueo PostgreSQL de ProcessingPurposePlan. Un operador cuyo permiso se retiraba durante la espera podía descifrar el contenido antes de una denegación tardía; la repetición idempotente incluso devolvía el cuerpo privado.

Se vuelve a autorizar después de adquirir el plan y antes de descifrar en la rama nueva. Se conservan la guarda final, el actor y sus epochs originales, el parámetro de permiso específico del ejecutor, transacciones y orden de bloqueos. El cambio son dos líneas en apps/safety/processing_review.py. Revisión independiente y revisión propia acotadas, sin bloqueantes observados; no constituyen garantía universal de seguridad.

## Evidencia y comparación

Original `20261026-190208-b39509bf`: 2 PASS y 2 FAIL, 77,902 s de JUnit. Candidata `20261026-191554-da2f750f`: 10 PASS, cero FAIL/ERROR/SKIP, 139,136 s de JUnit. Ambos conservaron 1.786 huellas. La candidata contiene los cuatro diagnósticos byteidénticos y seis pruebas originales de revisión y ejecución.

| Escenario | Antes: contenido/resultado | Después: contenido/resultado | QA antes (s) | QA después (s) |
|---|---|---|---:|---:|
| Creación autorizada | 1 descifrado; returned | 1 descifrado; returned | 9.879 | 9.408 |
| Repetición autorizada | 1 descifrado; returned | 1 descifrado; returned | 9.313 | 8.616 |
| Creación revocada | 1 descifrado; PermissionDenied | 0 descifrado; PermissionDenied | 8.725 | 8.032 |
| Repetición revocada | 1 descifrado; returned | 0 descifrado; PermissionDenied | 8.845 | 8.337 |

Los tiempos por escenario incluyen preparación, espera real, oráculos y limpieza; son tiempos QA y no latencias normales de la aplicación. Las baterías tienen distinto número de casos, por lo que sus totales no miden una regresión ni una mejora de rendimiento. No se declara aceleración causal.

Los cuatro casos observaron espera PostgreSQL con conexiones distintas y permiso inicialmente cacheado. Los negativos de la candidata produjeron PermissionDenied antes de contents: cero llamadas, cero retornos privados y ningún cambio SQL/medios/caso. El control de creación conservó exactamente Action+Read y sus vínculos; la repetición conservó el mismo Read y cuerpo sin escrituras. Las seis regresiones originales pasaron, incluida ejecución con review_permission=False. No es una prueba HTTP ni de proveedores.

La auditoría posterior confirmó identidades de fuentes y documentos congelados, huella del grafo, oráculos, recursos desechables ausentes y Telegram PASS entregado. El original fallido se conserva. No se repitió QA válida tras reanudar.

## Custodia y continuación

Archivo duradero: [evidencia compacta](evidencias/n09-r-procesamiento-preprivado-20261026.tar.gz), 14 entradas, SHA-256 `2832140fd9859c9e0dc9e6f6e7c1824a799e76461379bc7b7c4a20f3197d7141`. Incluye auditorías, fuente original/candidata e instrumento y resultados saneados; excluye logs crudos, credenciales y cambios laterales.

Pendiente antes de entrega: incorporar este resultado al grafo y al censo de 139 IDs, comprobar custodia y alcance Git. La corrección de esta frontera no cierra automáticamente N09. N10/N11/N15 continúan pendientes; N02 residual al final del desarrollo y N12–N14 condicionados. La limpieza completa de artifacts permanece como última acción de N15, tras el resumen duradero acordado.
