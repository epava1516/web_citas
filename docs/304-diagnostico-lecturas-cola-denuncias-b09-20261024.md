# B09-343 — Diagnóstico de lecturas de la cola de denuncias

B08 está aceptado por acta18. B09 comienza desde el grafo401 revalidado: 14.038 nodos y 60.289 relaciones, sin huellas obsoletas. La consulta BFS orientativa quedó truncada; el análisis siguiente procede del contraste directo de safety.views.queue/permitted, conflict_of_interest, Report y plantilla de cola. No se afirma extracción global nueva.

## Hipótesis y prerregistro

La cola actual consulta el estado y la autorización general, obtiene denuncias con listing/person/agency y filtra cada una con permitted. Para una denuncia a una agencia, reported_agency no está precargada y la pertenencia del revisor se consulta individualmente. Hipótesis: esas dos familias de lecturas crecen con el número de filas. No es todavía una medición ni un defecto de autorización demostrado.

Se añade tests/test_report_queue_read_cost.py, dos casos de 10/100 denuncias sintéticas a una agencia, permisos y MFA reales y PostgreSQL obligatorio. El resultado HTTP debe conservar todos los IDs y su orden frente al oráculo permitted actual, cabecera privada y ausencia del cuerpo cifrado o descifrado en HTML. Sólo la petición se mide; preparación y oráculo quedan fuera. Se registran recuentos de SQL, lecturas cuyo FROM principal es Agency/AgencyMember y tiempo descriptivo; nunca SQL, parámetros o cuerpos. Los registros se crean como fixture, no mediante el flujo de denuncia pública: no atribuir validación de ese flujo a este diagnóstico.

Runner local oficial, un archivo y un worker, timeout600s por comando, PostgreSQL/Redis propios. Dos PASS indicarían equivalencia funcional e instrumento ejecutado; no una optimización o presupuesto de rendimiento satisfecho. No se modifica aplicación ni se prueba un índice sin plan. Tras inspeccionar JUnit/fuentes/limpieza/Telegram se elegirá el cambio o se descartará la hipótesis.

## Entrega de imágenes: observación inicial

El listado y la ficha usan public_photo. process genera un derivado WebP con máximo1600x1600 y calidad85; no hay todavía medición aquí de bytes, tamaño de transferencia, LCP o efecto de nuevas variantes. No cambiar formatos ni almacenamiento/purgas por esta observación aislada. Las reglas de publicación y acceso a fotografías deben conservarse en cualquier contraste posterior.

B09 sigue abierto. Once de18puntos cerrados; B10/B11 y B14–B17 mantienen sus alcances, B15 opcional. No nueva carga contractual ni aceptación conjunta B16.

## Resultado auditado

Ejecución20261024-053209-77dfeca3: dos PASS, sin fallos, errores ni omisiones;51,559s sumados de casos JUnit. [Auditoría de referencia](evidencias/b09-report-queue-read-baseline-20261024.json):1713fuentes congeladas e iguales al terminar, limpieza de contenedores/temporal/proceso y recibo Telegram confirmados.

| Denuncias | Permitidas y orden correcto | Consultas de la petición | Lecturas principales Agency | Lecturas principales AgencyMember |
| --- | --- | --- | --- | --- |
|10|10|30|10|10|
|100|100|210|100|100|

La hipótesis de N+1 queda confirmada en este escenario: una lectura de agencia y otra de pertenencia por denuncia. El incremento de90filas añade180consultas. No se extrapola a otros tipos de denuncia. Los tiempos de una única petición por tamaño fueron0,598/0,344s, respectivamente; calentamiento y demás efectos no están controlados para atribuir coste temporal, por lo que no demuestran escalado de latencia ni ahorro posible. La ausencia del cuerpo privado y el orden se comprueban funcionalmente, sin publicar SQL o parámetros.

## Cambio que debe contrastarse

El siguiente incremento debe eliminar las lecturas repetidas conservando la selección completa y el oráculo permitted. Antes de trasladar exclusiones a SQL, probar actor/individuo/sujeto denunciados, propiedad de agencia, pertenencias activas e inactivas, perfil particular/representado, objetivo legacy sin manager_version y estados received/reviewing/restricted/upheld según permisos. La agencia denunciada excluye cualquier pertenencia; el conflicto de la agencia del perfil sólo considera membresía activa. No unificar ambas reglas ni precortar filas antes de resolver conflictos. Mantener permiso/MFA y controles frescos de consulta privada; no sustituir inspect o la revisión final por una decisión de cola.

La comparación posterior conservará este instrumento y ambos tamaños, separando consultas, forma de selección y pruebas de autoridad. No se justifica añadir un índice sin EXPLAIN real. Los campos privados que la plantilla no usa son otra candidata de lectura, todavía sin contraste. Imágenes/activos y observación del backlog/fallback siguen dentro de B09. No se ha aplicado optimización de aplicación ni cerrado B09.

Corrección posterior: [305](305-seleccion-sql-cola-denuncias-b09-20261024.md) verifica18pruebas y reduce30/210consultas a10/10con el mismo instrumento. Los resultados de343 describen la referencia previa; la cola está optimizada en este alcance y B09 sigue abierto para entrega y backlog.
