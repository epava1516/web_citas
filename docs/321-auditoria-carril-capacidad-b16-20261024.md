# B16-359 — Auditoría terminal del carril de capacidad

La ejecución 20261024-154224-43b1e770 terminó sin fallos ni errores: **297 PASS y 9 SKIP de 306 casos únicos**. Tiempo pytest del runner 17882,737 segundos (4 h 58 min 3 s); JUnit 17879,386 segundos. El resultado PASS del comando no convierte las omisiones en pruebas aprobadas ni acepta B16 o capacidad de producción.

Se contrastaron journal, JUnit y selección del [prerregistro](319-prerregistro-carril-capacidad-b16-20261024.md). Coinciden los 306 nodeids y SHA256 5a4d9a49eea06f168959a40483a3303e7d8b2d0e7806cae36220a2cb72cefef2. Hay 297 reportes call aprobados, un skip durante call y ocho skips durante setup; ningún reporte failed. No son sólo 298 pruebas recogidas.

Las 1723 fuentes del manifiesto congelado conservan sus hashes. Se verificaron además la ausencia del runner, del temporal y de contenedores por etiqueta propia; el runner registra retirada de PostgreSQL y Redis. Avisos terminales del runner y supervisor confirmados como sent. El mecanismo de retorno conserva el mismo objetivo e historial; la compactación cuenta con un nuevo elemento completado persistido, distinto de un mero ACK.

## Escenarios largos actuales

| Escenario | Ejecución actual |
|---|---:|
| Orgánico, 1000 perfiles | 575,086 s |
| Orgánico, 10000 perfiles | 5494,444 s |
| Promocionado, 1000 perfiles | 788,934 s |
| Promocionado, 10000 perfiles | 7833,472 s |

Estos tiempos son de escenarios completos de QA, no latencia HTTP del usuario ni medición contractual de capacidad. Sus diferencias frente al 22 de octubre no constituyen un antes/después causal de una optimización.

## Omisiones y cobertura pendiente

Los nueve SKIP conservan su disposición individual y guardia inspeccionada en la [auditoría](evidencias/b16-capacity-terminal-audit-20261024.json): calibración beta HTTP; entrega completa; perfil de etapas; reconexión nativa; preflight del proxy y purga; perfil profesional; selección TCP concurrente; selección TCP; atribución de fuentes. Son instrumentos que requieren controladores o activaciones explícitos. No se activan automáticamente por esta auditoría ni se presentan como evidencia positiva del escenario.

Las once exclusiones oficiales del perfil siguen separadas. B16 requiere todavía conciliar requisito por requisito los resultados funcionales, omisiones, exclusiones y límites de reutilización entre versiones. Los diagnósticos opt-in no sustituyen obligaciones aplicables ni obligan a repetir cargas históricas aceptadas sin una incertidumbre concreta.

## Alcance pendiente y decisiones del usuario

Se mantienen los [acuerdos posteriores](320-acuerdos-alcance-b10-prioridades-20261024.md): resolver B10 en este contrato conforme a MOD-09; B14/B15/B17 como deuda propuesta para el siguiente, pendiente de formalización; priorizar allí los recorridos; aplazar el frente específico de optimización QA hasta la etapa estable/productiva. La reconstrucción completa del grafo y el inventario diferencial permanecen al final del contrato actual. Seguimos en alfa, B16 abierto, 13/18 puntos aceptados localmente.
