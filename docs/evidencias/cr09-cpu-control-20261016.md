# Control breve de trabajo constante en CPU4

Proceso propio único,60muestras de100CRC32sobre1MiB idéntico, sinDB/Redis/serviciosnormales. Python3.12.15/afinidadCPU4/mem128MiB/swap0/tasks32;unidad terminal0/cgroupsinMainPID. [Recibo completo yhashdelprobe](cr09-cpu-control-20261016.json).

| Métrica | Resultado |
|---|---:|
| Wall medio por100MiB | 43,289ms |
| Coeficiente devariaciónwall | 11,606% |
| Coeficiente devariaciónCPUpropio | 11,182% |
| Primera mitad,wallmedio | 43,534ms |
| Segunda mitad,wallmedio | 43,045ms |
| Discrepancia entre medias de mitades | 1,131% |
| StealCPU4delta | 0ticks |
| Esperarunnablepropiaacumulada | 23,538ms |

CV no es discrepanciaA/A ni intervalo deconfianza. Las medias de30muestras por mitad son mucho más próximas que los valores individuales; este control no prueba inestabilidad de medias ni explica el41%delSQL. Medición cortaactualnoexplicalosensayosanteriores. VariaciónenCPUpropiocontrabajofijo sugiere factores que no requierenSQL, incluyendo el propio protocolo de observación, pero no identifica frecuencia/hardware/virtualización ni invalida retroactivamente latencias. 0steal no pruebaausenciadetodainterferencia. No aceptación delSLO ni modificación de recursosapp.

El primerintento terminóantesdetrabajo porque cpu.maxnoestabaexpuesto enelcgroupusuario; [fallo preservado](cr09-cpu-control-original-20261016.json). Correctiva registranot_exposed yusaunproceso/hiloafinadoaunaCPU; no se afirmaCFSquotaaplicada ni se cambia controladorpadre. Interfazderecursosinaccesiblenuncasepresentacomo0. El control noproponeretardosoperativos, ni repite variantesSQLfallidas.
