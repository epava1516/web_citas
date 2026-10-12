# MOD-08 — diagnóstico profesional y control, 2026-10-12

El transporte original cumple las etapas locales de entrega en el último control.
No se ha demostrado una mejora HTTP causada por la candidata ni un techo de rendimiento.
El usuario confirmó cambios de alimentación/modo de energía e indicó «Alterní».
No conocemos el estado energético de cada ejecución: el salto no es atribuible al código.
Las cuotas Docker no fijan la frecuencia de CPU. No se cambió la política del host.

| Ejecución | Navegación p95 (s) | JSON p95 (s) | Binario p95 (s) |
| --- | ---: | ---: | ---: |
| Original anterior, 212056-311e7b34 | 3,389665 | 8,961067 | 9,033017 |
| Candidata, 223037-dceb3990 | 1,730212 | 4,379374 | 4,657655 |
| Control original, 225032-2c80329e | 1,626706 | 3,864846 | 3,840579 |
| Límite | 2 | 5 | 5 |

Máximos entre dos casos concurrentes; 384 navegaciones y 20 descargas por tipo/caso.
Fuente 16 MiB, originales aproximadamente 64 MiB y partes aproximadamente 8 MiB.
Datos sintéticos, cuotas idénticas, PostgreSQL real y WSGI normal sin perfiladores.
Solapamientos, cuerpos y comprobaciones funcionales exigidos pasan.
Los dos últimos runners declaran DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3.
Esto no acepta capacidad global, N3 ni todo MOD-08. El fallo anterior se conserva.

## Deliberación y candidata retirada

Sala .ai/rooms/mod08-profesional-20261012 cerrada: dos revisiones Claude y dos Notebook,
con correcciones y consumo conservados. Opiniones externas no son pruebas.
Las muestras py-spy existentes muestran el camino sellado, no dominancia del fallback.
Los tiempos inclusivos no se suman como ahorros.

Se probó compartir un cliente SDK entre los dos workers de una sola operación,
serializando construcción y cerrando tras join. Sin cachear autoridad ni resultados.
Se conservaron tumbas, descargas, cifrado, hashes, errores y lecturas frescas.
Puertas reales PostgreSQL/RustFS: 139 PASS en 200,80 s y 139 PASS en 198,94 s.
AB/BA de 20 pares por ensayo: ahorro mediano 60,475 ms y 55,158 ms,
19/20 y 17/20 pares favorables. Beneficio micro, sin prueba de beneficio HTTP.
Candidata: HTTP 1 PASS en 920,367 s; control original: 1 PASS en 911,695 s.
Sin emparejamiento no afirmar regresión causal; tampoco aceptar mejora global.

Candidata retirada, cuatro archivos restaurados exactamente al baseline comprobado.
Trabajo previo preservado. [Patch retirado](mod08-s3-client-sharing-retirada-20261012.patch).

## Herramientas y límites

pyperf 2.10.0 instalado sólo en venv diagnóstico; dependencias de app sin cambios.
Memray 1.20.0 y py-spy 0.4.2 existentes. Scripts y artefactos reproducibles:
artifacts/diagnostics/s3-sdk-20261012/.
Constructor SDK, 20 muestras por brazo: sesión nueva 114 ± 56 ms;
sesión caliente 4,24 ± 0,68 ms. Advertencias de inestabilidad conservadas.
Memray separado, tres construcciones: 18.487/1.330 asignaciones,
204.032.346/1.420.939 bytes acumulados. Preparación caliente fuera del Tracker;
no incluye memoria retenida ni equivale a peak RSS. Flamegraphs oficiales,
símbolos nativos incompletos. pyperf system show parcial por ausencia de irqbalance;
no se instaló el servicio ni se afinó el host. Sesión persistente no integrada.

[Boto3: clientes y concurrencia](https://docs.aws.amazon.com/boto3/latest/guide/clients.html),
[Session y concurrencia](https://docs.aws.amazon.com/boto3/latest/guide/session.html),
[Tracker oficial Memray](https://bloomberg.github.io/memray/api.html).

## Evidencia y siguiente condición

HTTP: artifacts/capacity-environment/20261011-223037-dceb3990 y
20261011-225032-2c80329e. N2: artifacts/local-ci/20261011-222112-86c35687 y
20261011-222655-5cb316f9. Auditoría independiente de 1.405 huellas por ejecución
antes de documentación; recursos propios retirados.
[Resumen estructurado](mod08-s3-profesional-20261012.json).

Antes de comparar causalmente: fijar alimentación/modo energético y registrar
su estado; repetir control/candidata emparejados sólo con hipótesis justificada.
Hay margen local, pero no estabilidad demostrada frente a la variación anterior.
