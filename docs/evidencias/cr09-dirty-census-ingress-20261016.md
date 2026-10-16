# Diagnóstico separado tras el censo dirty

Run004422-7ee64fc7,SHAced95b1/producto6daa170,**FAIL187,14s**instrumentado. [Recibo](cr09-dirty-census-ingress-terminal-20261016.json). Mismoescenario/cuotas/kernel native-sealed,4sync,10000sintéticos,Celery2+Beat/subida.1200IDscliente/WSGI/Gunicorn emparejados,0parseerrors,1200completas0errores/timeouts/omisiones/pendientes,subida302/generadorválido. Fuentesexactas ycleanupindependientes.

| p95 HTTP s | Último limpio | Diagnóstico |
| --- | ---: | ---: |
| Mezcla completa | 0,904873942 | 0,880657885 |

No mejora/regresión causal: observaciónWSGI/SQL/GC yCPUcgroups1Hz sólo en diagnóstico. No aceptación/reproducibilidad.

| Media por petición | 0–5s,100 | 15–60s,900 |
| --- | ---: | ---: |
| HTTP ms | 901,987 | 229,388 |
| Antes WSGI ms | 680,820 | 44,022 |
| WSGI ms | 221,408 | 185,554 |
| CPU thread ms | 110,638 | 101,357 |
| SQL ms,inclusivo | 99,514 | 74,339 |

81lentas>=0,8s,todasemitidasprimeros5s. El98,667%deesperainicialpreWSGIcoincide conintervalosdetodoslos4procesosocupados;no prueba exclusivacola/causa. En10primerossegundos todosocupados9,769s. CierreWSGIposteriorarecepciónpuededarresiduonegativo;sumasSQL/GCinclusivasnoaditivas. PG0,619coresiniciales/0,472estables,sinthrottle;controllers2,202/2,075incluyegenerador/Celery/observador. NoPSI/causadehardwareafirmados.

Ocupantes d3/d20/d21durantearranque:selecciónquery95c3…117,367/118,117/109,410ms;conteoc3f3…113,945/58,512/79,153ms. Callerpage455/454,la búsqueda emplea ORexterno entreestadoelegible-nodirty yIDsnativos. Evidenciaactual para uncontraste finito de membershipIN(UNION) enRRpropio, conservando poblaciónexterna/filtros/ranking/DISTINCTnecesario/página/guardiafinal. Noalterarproyeccióndirty niriactivarhíbridodescartado. Revisión lógica nativa sincontraejemplo bajoUUIDnon-null yconjuntosexactos,pero ROIaúnno demostrado.

Contrasteaislado iniciado encr09-population-union-contrast-20261016,sinappmodificada. Reutilizastate_pagecompleto/listado/búsqueda/sincoincidenciaslimpio/dirty1,3bloquesAB/BA;nootraHTTPhastaresultadopositivoyparidad. Siinconcluso/rechazadoconservarsinbarridoparámetros.

Cleanup:controlador/hijo/4workers/Celeryausentes,temporalretirado,PG/Redispropiosausentes,unitMainPID0/ControlGroupvacío;sinserviciosnormales. CR09/N3abiertos.

Resultado posterior: contraste terminal 004909-87f1581a, 1 PASS funcional; candidato descartado por empeorar listado/búsqueda. Ver [comparación](cr09-population-union-20261016.md). No nueva carga HTTP.
