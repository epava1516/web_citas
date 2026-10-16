# Control con separación fija — no adoptar

Run115208-3d3d0ec6, fuentea1f73ba:1PASS92,56s funcional/diagnóstico. Ocho controles/18backends nuevos, fuentes/limpieza independientes. [Recibo](cr09-empty-mark-quiescent-20261016.json).

| Primeraoperación | ActualA/B | Candidato | Cambio observado | A/A |
|---|---:|---:|---:|---:|
| direct_empty | 22.784ms | 4.553ms | -80.02% | 50.47% |
| complete_mark_stale | 45.386ms | 38.376ms | -15.45% | 41.23% |

A/A50,47/41,23%>10%; ahorrocompleto15,45%<20%. No cumple prerregistro. Contadores delcgroupPG muestran0nr_throttled enlas18operaciones; no respalda lahipótesis de cuotaarrastrada duranteesosintervalos, sin excluir variación delhost/planificación/backend. La pausa150msnoespolíticaoperativa ysu coste está enarm_total_seconds. No ensayar otras pausas, no migración ni carga limpia.

El CPUregistrado agrega todoslosprocesos delcgroupPG ylosbordesdelectura, noCPUporconsulta. No inferircausaúnica o extrapolación alHTTP. Elguardvacíosigueprototipo, funciónproductiva0020restauradaintacta. Últimosp95limpios0,675688PASS/0,880357FAIL;CR09/N3 abiertos.

Siguiente diagnóstico finito, sinDB/Redis ni más variantes SQL: observar trabajoCPUconstante propioenCPU4, CPUdelproceso frenteawall/schedstat/cpu.stat/stealagregado. Puede detectar dispersión externa alSQL; una negativa no descarta todoslosfactoresdeentorno ni explica retroactivamente losensayos. Mantener cuotas ynoinstrumentar servicios normales.
