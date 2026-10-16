# Espera inicial y ocupación de procesos: reconstrucción sin otra carga

Revisión independiente nativa y análisis offline de los eventos ya conservados. No nueva prueba HTTP ni cambio de producto. Se emparejan1200 solicitudes con1201 intervalosWSGI por ejecución, incluida subida;se verifica ausencia de solapamiento porPIDsync. Integra el tiempo entre emisión yentradaWSGI en intervalos donde el número de solicitudes activas coincide con todoslosprocesos. [Datos y límites](cr09-occupancy-offline-20261016.json).

| Diagnóstico | Procesos | Espera inicial media | Coincidencia con todos ocupados | Resto no explicado por esa coincidencia |
| --- | ---: | ---: | ---: | ---: |
| 223005-7347b70d | 4 | 872,166ms | 860,977ms /98,717% | 11,189ms |
| 232822-f60cfe0d | 8 | 747,214ms | 733,379ms /98,148% | 13,835ms |
| 233806-75cf5a0a | 8 | 645,174ms | 632,310ms /98,006% | 12,864ms |

Cohorte100peticiones emitidas0–5s porrun. Porcentajes sobre suma de esperas de esas mismaspeticiones; no porcentajes deCPU ni de peticiones. Relación temporal compatible con acumulación por ocupación; no prueba exclusiva de causa, cola kernel ni timestampaccept. Parseo/cierre/transporte/trabajo no etiquetado/scheduling no están medidos; periodo no-all-busy no prueba trabajador disponible. WSGI/SQL/GCinclusivos, no sumar.

En233806 los ocupantesd20 y d9 concentran consultas deunknown(patrón167b7e…)170,758/241,023ms yselección(patrón95c3…)281,541/210,103ms. Launknown conservaantijoincorrelacionado sobre población juntoalORdirty. Esto permite estudiar costeconcreto, sin atribuir todo el segundo a unúnicocaller.

Hipótesis finita: si censo exacto demuestra cobertura/versiones vigentes en el **mismo snapshotRRpropio**, desconocidos son únicamente dirty intersectado conelquery. Contrastar sólocenso/unknown, manteniendo población/orden/proyección deshabilitadacondirty yguardiafinal. En transacción heredadaREADCOMMITTED la inferencia no es válida: una inserción o cambio deestado posterior alcenso puede ser observado porantijoinoriginal y omitido porlistadirty leídoantes. Mantenercaminooriginalallí.

La pieza existía dentro del prototipo c48002c deproyección/mezcladirty rechazado: no es idea inédita ni se reactiva ese prototipo completo. El nuevo contraste la separa de población/ranking y tiene como motivo las trazas deocupantes concretos. Aún sinresultado niaceptación.

La comprobación adicional deimagenpreexistente web-modelos-worker:latest ejecutó sólo import encontenedor propio sinred/read-only, conlímites; no contiene canonical_kernel_loader. No se usa como imagen deestaversión y no se modificóelservicionormal. Contenedor deinspecciónyaausente; no nuevaimagenconstruida.
