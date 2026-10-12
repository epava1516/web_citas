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
