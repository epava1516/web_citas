# Censo previo y desconocidos dirty: contraste aislado

Motivo: [ocupación reconstruida](cr09-occupancy-offline-20261016.md) y consultas unknown de170–241ms dentro de ocupantes iniciales concretos. La pieza se separa del prototipo anterior de proyección/merge dirty rechazado; población, orden, guardiafinal y proyección deshabilitada con dirty permanecen. No se reactiva el prototipo completo.

[Recibo y108lecturas](cr09-dirty-census-contrast-terminal-20261016.json),run002739-852c62f5,SHA23a19a5 con testnuevo incluido en hashes iniciales ycommiteado posteriormente. **1PASS106,25s**. PostgreSQL10ksintéticos/kernel native-sealed; limpio ydirty1/listado/búsqueda/sincoincidencias,3bloquesAB/BA×3repeticiones porbrazo y conexiónnueva porbrazo. El test ejecuta state_page completo ycompara conteo/ID/orden exactos. SinHTTP/carga/perfiladores.

| Media wall ms | Actual | Censo/unknown |
| --- | ---: | ---: |
| Limpio listado | 180,787 | 211,772 |
| Limpio búsqueda | 230,131 | 211,241 |
| Limpio sin coincidencias | 55,970 | 52,039 |
| Dirty1 listado | 310,410 | 264,346 |
| Dirty1 búsqueda | 407,764 | 319,523 |
| Dirty1 sin coincidencias | 74,062 | 75,580 |

Dirty medios porbloque actual→censo:251,386→214,909;275,053→201,290;265,797→243,250ms. CPUdirtylistado162,461→132,776ms;dirtybúsqueda187,563→156,049ms. Sincoincidencias no mejora. El camino limpio es lógicamente igual:variaciones temporales deéste no son cambio causal. Beneficio aislado suficiente para controles siguientes, no promesa de p95.

Revisión independiente nativa confirmó la identidad lógica dentrodeRRpropio: cobertura/versiones completas implica !Exists=False, porloque unknown se reduce a dirty intersectado con elquery. **Fuera deRRpropio no es equivalente:** nueva fila/versión puede aparecer entrecenso yconsulta enREADCOMMITTED. Implementación eventual debe limitarla a trusted_snapshot=True y mantener originalsinconsultaextra en inheritedRC. El instrumentodecontraste no se usó dentrode transacciónheredada y no es implementación deentrega.

Antes de adoptar faltan paridades RR/inherited, faltantes/versiones,checked/filtros/multiplicidad/límites y concurrencia pertinente. Fuentecongelada verificada independientemente; controlador/hijo/temporal/contenedores propiosausentes; unidadexit0/MainPID0/ControlGroupvacío. No appmodificada ni p95nuevo.
