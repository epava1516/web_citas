# MOD-08 — perfil8CPU del VPS, autorizado 2026-10-12

El usuario autoriza elevar4CPU al máximo8CPU del servidor para medir el efecto de
la cuota asignada. [FAIL4CPU conservado](mod08-vps-medicion-servidor-20261012.md).
No modificación de aplicación, kernel, workers o umbrales. Perfil explícito
`--cpu-budget 8`;4 por defecto conserva compatibilidad y referencia histórica.

| Servicio | CPU4 | CPU8 | RAM(MiB), ambos |
|---|---:|---:|---:|
| PostgreSQL | 1.5 | 3 | 3072 |
| Aplicación | 1.75 | 3.5 | 3968 |
| Objetos | 0.5 | 1 | 512 |
| Redis | 0.1 | 0.2 | 384 |
| Proxy | 0.1 | 0.2 | 128 |
| Controlador | 0.05 | 0.1 | 128 |
| Total | 4 | 8 | 8192 |

Cgroups `cpu.max`,RAM/swap se verifican realmente por servicio/controlador; sumas
contrastadas con presupuesto declarado. Sólo4/8 aceptados;8 requiere topología
propia de objetos y no permite captura/reutilización de baselines diagnósticas.
El host debe ofrecer afinidad suficiente. Recibos y reports identifican
`cpu_budget_cores` y si corresponden al perfil original4CPU.

Ruff y120 pruebas rápidas PASS/2.91s, incluyen separación de cuatro modos en
ambos presupuestos, conservación de memoria/banderas de workload, rechazo de
presupuestos no autorizados y topología ajena. No equivalen a cuotas reales.
Próxima puerta obligatoria preflight8CPU, luego probe8 y measure8 sin perfiladores;
fuentes congeladas durante cada proceso, recursos propios y datos sintéticos.
Sólo repetir una vez si cumple. No atribuir latencias instrumentadas a aceptación,
no ensayos especulativos y no aceptación global/N3 por etapas.

Aplicación/kernel e imágenes probadas del ciclo4CPU se conservan; sólo cambian
elección/verificación de cuotas y metadatos del instrumento. RAM,swap,storage,
1500revisiones/16MiB/64MiB,dos casos,384lecturas y20descargas/tipo/caso,8MiB por
paquete,concurrencia/autoridad/EOF y umbrales2s/5s/5s permanecen.

Resultado real8CPU pendiente. Una mejora grande, reproducible con el mismo
código, apoyaría efecto de cuotaCPU; no demostraría causa única de hardware
ni autoriza inferir prestaciones del portátil con energía variable.

## Ejecuciones terminadas y auditadas

SHA medido `5d9002839e24d2e925407b9c78ac67b86182e7a5`, incluye c46d0e1.
Python3.12.15, kernel native-sealed e imágenes idénticos al ciclo4CPU;
aplicación sin cambios. Manifiesto1411fuentes
`6224171a09a1a0420ff0b07748075ba17cce6779caf155556a87dd1300fbd75c`.
[Resumen estructurado](mod08-vps-perfil-8cpu-20261012.json).

| Modo | ID propio | Resultado | Prueba(s) | Duración test(s) |
|---|---|---|---:|---:|
| preflight | 20261012-022903-d38c2a39 | READY_NOT_CAPACITY | 1PASS | 71.333 |
| probe | 20261012-023302-d31db703 | NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY | 1PASS | 42.885 |
| measure | 20261012-023609-aa06db69 | FAIL_DELIVERY_STAGE_LIMITS | 1FAIL | 2050.766 |
| diagnose | 20261012-031633-f088a71b | PROFILE_DIAGNOSTIC_NOT_CAPACITY | 1PASS | 1601.224 |

Cero errores/skips. Measure conserva seis incumplimientos, no se repite al fallar.
Auditorías independientes confirman fuentes intactas, archivo completo y ausencia
real de seis contenedores propios, red y volumen al terminar. RAM agregada8GiB,
swap/OOM propios0, almacenamiento propio acotado. Cotas conservadoras de memoria
measure4221202432bytes y diagnose3011399680bytes, ambas<6GiB.
La aserción de latencias falla antes de algunas verificaciones exteriores; éstas
se contrastaron independientemente en `independent-delivery-contract.json`, sin
atribuirlas a aserciones que no llegaron a ejecutarse. Los workers completaron
ambos casos, integridad/cuerpos/autorizaciones y concurrencia conservadas.

### p95 sin perfiladores, segundos

| Etapa | 4CPU A | 4CPU B | 8CPU A | 8CPU B | Límite |
|---|---:|---:|---:|---:|---:|
| Guardar binario | 1.997628 | 1.945690 | 1.695901 | 1.724495 | 5 |
| Leer selección | 1.656140 | 1.653232 | 1.475302 | 1.497210 | 2 |
| Inspección binaria | 1.638473 | 1.644180 | 1.354550 | 1.390970 | 2 |
| Guardar cobertura | 3.010549 | 2.970579 | 2.704440 | 2.683346 | 5 |
| Leer cobertura | 3.829796 | 3.835592 | 3.523783 | 3.547708 | 2 |
| Descargar JSON | 10.732150 | 10.565686 | 7.115129 | 7.060256 | 5 |
| Descargar binario | 10.334944 | 10.442426 | 7.099972 | 7.011104 | 5 |

384lecturas de cobertura y20descargas/tipo/caso; demás conteos31selecciones y
20guardados/inspecciones. Peor p95: navegación mejora7.51%, JSON33.70%, binario
32.01%. La cuotaCPU influye, pero no demuestra hardware como única causa.
No atribuir diferencias del portátil al código: energía alternaba con cargador.
No aceptación global/N3 ni aceptación de etapas8CPU.

### Diagnóstico separado

Diez capturas py-spy0.4.2 nativas100Hz con idle y PG25ms; cinco completas y cinco
parciales (11errores de muestreo en total), todos los procesos py-spy terminan0,
errores de validez vacíos. Deben conservarse las limitaciones de muestreo.
Resolución offline sólo para direcciones del Python exacto, no bibliotecas ajenas.

| Captura de descarga8CPU | Hilo principal esperando futuros(%) | Espera psycopg(%) | SHA256 trabajadores(%) |
|---|---:|---:|---:|
| JSON inicial | 52.83 | 21.00 | 45.67 / 34.13 |
| JSON proxy | 58.87 | 24.76 | 46.36 / 40.00 |
| Binario inicial | 48.55 | 24.19 | 43.64 / 44.33 |
| Binario proxy, parcial | 55.72 | 26.27 | 37.50 / 43.09 |

Son porcentajes de muestras de tiempo de pared por hilo, incluyendo espera, no
CPU ni partición de p95. Capturas incluyen cierre del observador; SQL diferencial
incluye otros workers del mismo rol y tiempos anidados solapados. No sumar tiempos
ni convertir ClientRead en CPU del servidor. SHA-NI no expuesto por el huésped:
hipótesis de coste nativo, no ahorro garantizado ni argumento para omitir hashes.
En esta ejecución posterior app/PG/controlador tienen afinidad0..7; system.slice
sin cuotaCPU de padre observada. No prueba histórica de todo el intervalo measure.

El usuario autoriza ahora investigaciones adicionales gratuitas y separadas con
Scalene/Memray. Pendiente atribuir CPU/asignaciones en hipótesis acotadas, comprobar
una corrección concreta y sólo después repetir measure limpio. No ensayos ciegos.
