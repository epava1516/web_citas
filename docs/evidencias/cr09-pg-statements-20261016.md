# Planificación y ejecución originales en servidor

Run113341-a119335e, fuented559f96:FAILinstrumentado1prueba189,18s. Extensión real/trackplanningverificados,60snapshots/3831identidades,0desalojos/reset estable/deltasno negativos. Fuentes,PID/start_ticks,temporal ycontenedores propios retirados verificados. [Recibo](cr09-pg-statements-20261016.json).

| Medición | p95(s) | Tipo |
|---|---:|---|
| Primer corto | 0,675688 | LimpioPASS |
| Repetición | 0,880357 | LimpioFAIL |
| Servidor instrumentado | 1,188000 | Noaceptación |

| Ventana objetivo | Intervalo real(s) | Planificación agregada(ms) | Ejecución agregada(ms) | Bloquesleídos |
|---|---|---:|---:|---:|
| [0, 1] | -0.194–1.004 | 456.020 | 1002.117 | 2 |
| [1, 2] | 1.004–2.010 | 515.303 | 1021.195 | 0 |
| [2, 5] | 2.010–5.039 | 566.593 | 1231.789 | 0 |
| [5, 15] | 5.039–15.220 | 482.386 | 4324.846 | 0 |
| [15, 60] | 15.220–60.441 | 2978.997 | 17065.943 | 25 |

Ventanas contiguas, límites por snapshot yno por cohorteexacta. Agregan aplicación/subida/worker/Beat yutilidades; tiempoelapsednoCPU, ejecuciones se solapanentrebackends. No dividir porrequestscomo si fueraatribuciónindividual, ni restar delSQLcliente que tiene población/distintafrontera. Máximosporquerysondesde reset, no máximosde intervalo. SQLnormalizado queda sóloartefactosignorados; recibo usa huellas.

Se confirma coste original de planificación de hidrataciones: estructura25JOIN/16SELECT máximo100,072ms, dosplanes/0,846msejecución hasta2s enesegrupo. Otras estructuras dehidratación tienen mezcla planificación+ejecución; no todas equivalentes enparams/cardinalidad. Selección debúsqueda alcanza127,842msejecución conplanificaciónmáxima1,105ms hasta2s. Por tanto nohayúnico cuello que pueda atribuirse aPython, planificación o disco.

Además aparece mantenimientoenbackground `listings_publication_mark(ARRAY(SELECT...missing/stale...))`:primerllamado37,133msplanificación/89,206msejecución. Elcódigo de0020.MARK ejecuta cuerpo de fanout aunconarrayvacío, sin guard inicial. Hipótesis delimitada nueva: una entrada vacía/null no produceIDs/efectos y podría retornar antes del INSERT/UNION/joins. Falta confirmar ahorro enfunción yconsulta completa; noimplementar migración ni atribuir todoel pico a estallamada. Laevidencia no conserva cardinalidad delarraydeesallamada concreta.

Siguiente control: funciónoriginal frente copia conreturnparaNULL/arrayvacío, sóloDBpropia; efectos/generación yfallosnoemptyidénticos, backendnuevo porbrazo para coste frío, coste de escaneo exterior incluido porseparado. Sin código productivo, sin nueva carga limpia o900. RegistrarROIantesdedecidir integración.
