# CR09 — detalle con snapshot RR: correctivas y ROI

El prototipoRC queda descartado por exposición de estados combinados. La variante corregida adquiere RRREADONLY propio antes del documento y mantiene hidratación, guard y render efectivo en la misma instantánea; en transacción heredada conserva el detalle nativo del llamador. Es un cambio explícito de política transaccional, no una afirmación de equivalencia de tiempos de lecturaRC. El reloj de caducidad sigue vivo. No se almacenan resultados de publicación entre peticiones.

## Concurrencia y garantías

La revisión nativa aislada [informe](cr09-detail-context-review-agent-20261016.json) entregó dos inversiones de orden. Codex verificó ambas con writersPGindependientes y un único commit atómico entre SELECTanotado/prefetch: foto incompleta→completa+conflicto; aceptación no-publicable→publish+revocación de todos los grants. En ambas, nativeA/B404 pero el negativoRC200; corregidaRR404. Primer fallo original [recibo](cr09-detail-context-snapshot-original-20261016.json), fuente y SQLpropios conservados, sin exposición de producción.

`100321-f83e2d54`:**9PASS110,45s**: dos negativosRC, dos correctivasRR, cuatro ámbitos (éxito/errorrender/heredadasRC-RR con restauración) y paridad18comparacionesESEN+UUIDausente. [Recibo](cr09-detail-context-snapshot-corrective-20261016.json). No llamar a los negativosRC casos seguros por su PASS.

`100847-a1f9a6a9`:5PASS y1FAILdeharness (argumento extra), no fallo funcional demostrado. Pasan localización/catálogo, holdprivacidad/republicaciónforzada, render con commit posterior al guard (cuerpoA íntegro/siguiente petición404), reloj de expiración y sesiónautenticada. Procedencia/PRODUCTION completada por separado tras corregir sólo la llamada, `101127-8c466967`:1PASS. [Fallo conservado](cr09-detail-context-guards-original-20261016.json), [correctiva](cr09-detail-context-guards-corrective-20261016.json). No se presentan como unrun6PASScomún niN3.

## Medición de la variante corregida

`101339-7fdb297e`:1PASS123,67s,288lecturas medidas+108warm,10ksintéticos yPGpropio. Mismo protocoloA/A/C y umbrales previos:ABC/BCA/CAB,6warm+16medidas/brazo/ruta, GCnormal concollectantesdelwarmúnicamente, firma/payload reales con componente temporal fijo para comparar cuerpos. SinTCP/Gunicorn/concurrencia/Beat/subida niDBcpu/RSS.

| Ruta | Referencia A/A | RR corregido | Ahorro wall | Ahorro CPU | SQL |
|---|---:|---:|---:|---:|---:|
| es | 84.553ms | 60.967ms | 27.89% | 25.47% | 36→27 |
| en | 82.106ms | 66.163ms | 19.42% | 16.93% | 36→27 |

ControlesA/Aestables y3/3bloques no-regresión enambasrutas. Supera>=10%ahorromediowall,CPUregresión<=5%,A/A<=10%wall/CPU. [Muestras y alcance](cr09-detail-context-rr-roi-20261016.json). No comparar causalmente sus números con el otro runRC; cambian corte/datos/ruido. Las cinco consultas adicionales frente al prototipoRC son parte del coste de la variante medida, sin retirar garantías para recuperar ese coste.

Fuentes congeladas,PID/start_ticks,temporales,contenedores y cgroups verificados independientemente en los runs. Python3.12.15/native-sealed/PG17.11 y cuotas previas. Sin datos reales/producción/proveedores. El informe del agente es entrada revisada; losPASSson deCodex. ConsumoClaudeanterior intacto.

## Integración y siguiente puerta

Se adopta el enfoqueRRpara integración local. Se separa el renderer común y el fallback nativo para evitar duplicar plantillas/reglas. Se conserva en tests la función anterior completa como referencia; la varianteRRde los controles debe ejecutar la función productiva, mientras el constructorRCqueda sólo como negativo. Los controles deparidad/carreras/ámbito/privacidad pasan a suite normal.

La prueba integrada posterior debe verificar estas fuentes reales y reutilizar las pruebas del contexto compartido/listado sin sumar cortes comoN3. Sólo entonces preparar imagen identificada y corto limpio. No se atribuye27,89%/19,42%al requestmix global ni al p95. Último corto limpio sigueFAIL1,052089655s. CR09/N3/global permanecen abiertos.
