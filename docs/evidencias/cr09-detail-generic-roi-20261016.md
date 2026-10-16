# Detalle genérico — ahorro insuficiente, no integrar

Run121637-13c66df7, fuente4735d3b:1PASS196,13s porparidad/compleción,1296lecturas/72backends/12bloques. Fuentes/limpieza independientes. CPUmedida en runtime ns delbackend propio, sin CPUcgroup ni estimación desdecursor. [Recibo ycomparaciones](cr09-detail-generic-roi-20261016.json).

| Caso | Primeras6 referencia→C | Ahorrofirst6 | Todas18 referencia→C | Ahorroall18 | CPUbackendall18 |
|---|---:|---:|---:|---:|---:|
| ES | 96.700→83.025ms | 14.14% | 72.175→68.372ms | 5.27% | -21.32% |
| EN | 98.931→81.369ms | 17.75% | 74.353→69.514ms | 6.51% | -20.70% |

A/AES estable;ENfirst6CPUaplicación difiere15,53% ynoesestable. Noalcanzafirst6>=20% ni all18>=10%, aunquebajaCPUbackend21%yambasrutas tienen10/12y11/12bloques favorables. Warmwall sube1,89/2,46%,dentrode5%;SQL27enA/B/C. No relajarumbralesniatribuir ahorroCPUaHTTP. Noimplementarpolítica/listado/global ni lanzarcortolimpio;conservarcandidatoparaantecedente, no repetirbuscandoPASS.

Las18lecturas secuenciales sobrebackendnuevo no equivalen a worker/proceso frío ni capacidadconsubida/Beat. AltoCPUaplicaciónmedido permanece40–45ms frente7–12msbackendporlecturaestable/all18. NoestimarPythoncomototal−SQL; ya haycontadorespropios. Siguiente:perfilmuestreadosólocódigoactualdel detalle paraatribuirCPUrestante;sinplanexperimentalgenérico ni otroprofiler/observador simultáneo. Herramientaaisladafijadapy-spy0.4.2 disponible.
