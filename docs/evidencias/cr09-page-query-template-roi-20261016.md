# Plantilla de consulta de página — ROI rechazado

[Recibo](cr09-page-query-template-roi-20261016.json). Ejecución150744-bc0cbd6f:1PASS307,09s significa que el experimento terminó, **candidato REJECTED**.864lecturas WSGI,72backendPGnuevos,10k sintéticos,cuatroalcances yseisbloquesA/A/Cbalanceados. Producto sin cambios.

| Alcance | A/B medio ms | C medio ms | Cambio tiempo | Cambio CPU app | Cambio CPU PG |
|---|---:|---:|---:|---:|---:|
| clean /es/ | 201.397 | 188.075 | -6.61% | -6.04% | -7.40% |
| clean /en/?q=synthetic | 212.914 | 213.575 | +0.31% | -2.30% | +3.71% |
| dirty /es/ | 245.918 | 239.911 | -2.44% | -6.47% | -1.19% |
| dirty /en/?q=synthetic | 283.527 | 283.934 | +0.14% | -0.76% | +0.15% |

Ningún alcance cumple todos los criterios prerregistrados. Listado limpio mejora tiempo pero CPUapp−6,04% no llega a−10% ycontroles inestables; búsqueda limpia no mejora y A/A total inestable. Listado pendiente−2,44%wall/−6,47%CPU no alcanza ambos umbrales. Búsqueda pendiente+0,14%wall/−0,76%CPU y sólo2/6bloques sinregresión. Dos alcances pendientes sí tienen controles estables; no atribuir todo el rechazo al ruido.

Se conservan resultados de fases, CPU PG precisa y huellas. Cuerpos HTTP iguales/no-store ymarcadores conservados porbrazo,GCnormal,sinpolítica deplanificador alterada/perfiladores. Preparación deconexión fuera delreloj,Python/buffersyausados. NoTCP/cuatro workers/Beat/upload ni p95. Fuentes congeladas ylimpiezaindependiente/terminal0 verificados.

No ampliarparidad/matriz ni integrar este candidato sin otro mecanismo demostrado. No repetirensayo porrutina; elresultadonojustifica cargaHTTP. El prototipo permanece sólo en tests paraauditabilidad. CR09/N3 yreproducibilidad delSLOsiguenabiertos.
