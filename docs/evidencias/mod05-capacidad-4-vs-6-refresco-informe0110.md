# MOD05: comparación 4/6/6/4 en topología normal con refresco

**Cuatro bloques VALID. Filtro de 30 s PASS en los cuatro, también con 4 workers. Efecto 6 frente a 4 FAIL en ambos pares → seis workers no se adoptan.** No es el gate de 60 s ni el contractual de 900 s. Ejecución autorizada expresamente por el usuario el 2026-10-08 («Autorizo la propuesta 4/6 de refresco»), solo para estos cuatro bloques. Trabajo de Claude Code (Claude Opus 5.5).

## Escenario y fuentes

[Propuesta](mod05-capacidad-4-vs-6-refresco-propuesta0110.json), [runner](mod05-capacidad-4-vs-6-refresco-runner0110.py), [revisor por bloque](mod05-capacidad-4-vs-6-refresco-revisor0110.py) ([log](mod05-capacidad-4-vs-6-refresco-revisor0110.log)), [análisis](mod05-capacidad-4-vs-6-refresco-analisis0110.json) con su [script](mod05-capacidad-4-vs-6-refresco-analisis-script0110.py) y [artefactos originales](mod05-capacidad-4-vs-6-refresco-artefactos0110.tar.gz).

- **Topología `normal_worker_beat`:** worker (`--concurrency=2`) y Beat propios con los comandos de compose y el calendario completo. Tareas no eager. Redis db 15 propia, prefijo de cola único y fase de Beat fijada 5 s antes de la carga.
- **Fuente:** `c82a746` más la corrección local de la marca sin señal del procesado de imagen y las fuentes de arnés de esta preparación (sin commit; huellas congeladas en el manifiesto del runner y verificadas sin cambios por el revisor en cada bloque). El resultado corresponde a **topología normal con esa corrección juntas**: no se separa la contribución de cada una.
- **Carga:** 10.000 anuncios del fixture repetido, 20 RPS durante 30 s, 600 dinámicas y 1 upload por bloque, timeout de 65 s, una carga y un servidor activos a la vez. Solo varía `--workers` de Gunicorn.

## Resultados

| Bloque | Workers | Terminadas en 30 s | p95 observable | Errores | Listado / Búsqueda / Ficha WSGI (ms) | D (ms) | 20D+U/60 | Upload |
|---|---|---|---|---|---|---|---|---|
| 1 | 4 | 595/600 | 0,507 s | 0 | 230,6 / 259,9 / 94,5 | 195,0 | 3,905 | 0,29 s |
| 2 | 6 | 595/600 | 0,567 s | 0 | 264,1 / 290,4 / 122,3 | 225,6 | 4,517 | 0,27 s |
| 3 | 6 | 594/600 | 0,547 s | 0 | 265,0 / 287,1 / 123,9 | 225,3 | 4,511 | 0,30 s |
| 4 | 4 | 595/600 | 0,500 s | 0 | 232,8 / 260,5 / 93,9 | 195,7 | 3,918 | 0,24 s |

- **Validez:** generador válido y contabilidad reconciliada, 0 no emitidas, 0 pendientes finales y 0 timeouts en todos los bloques, sin paradas por recursos.
- **Veredicto del arnés por bloque:** PASS (p95 < 0,8 s y errores < 1 %). Pendientes en el cierre de la ventana: 5–6 (≤ 20).
- **Competencia ajena del host:** CPU residual 2,18–2,55 cores, rango 0,38 ≤ 0,5 → comparación dentro del límite. Durante la emisión, la app usó ≈1,96–1,99 cores, PostgreSQL compartido ≈1,33–1,39 y el worker/Beat propio 0,02–0,06.
- **Efecto 6 frente a 4 (criterio prefijado):** completaciones +0,0 % / −0,2 % (se exigía ≥ 10 %); el p95 no baja, sube; D sube un 15,7 % / 15,1 % (límite 10 %). **FAIL en ambos pares.** Con 6 workers síncronos, cada request tarda más con la misma CPU disponible; no se atribuye a una causa concreta.

## Refresco MOD05 medido

| Bloque | Ejecuciones (origen) | Wall / CPU de hilo total | Marcas limpiadas | Demora marca→limpieza | Muestras de carga con sucios | Lecturas sucias |
|---|---|---|---|---|---|---|
| 1 | 6 (beat 2, web 1, worker 3) | 0,83 s / 0,26 s | 3 | 0,19–0,46 s | 0/31 | 9/400 |
| 2 | 6 | 1,11 s / 0,27 s | 3 | 0,22–0,60 s | 2/31 | 12/400 |
| 3 | 6 | 1,11 s / 0,29 s | 3 | 0,23–0,49 s | 0/31 | 10/400 |
| 4 | 6 | 1,12 s / 0,29 s | 3 | 0,22–0,51 s | 0/30 | 11/400 |

- **Ejecuciones:** cada bloque registra 9 marcas, contando remarcas. El origen `worker` corresponde a refrescos encolados por tareas del propio worker, como `process_blob` o el refresco tras el procesado.
- **Procesado de imagen:** `process_blob` se ejecutó en el worker, 4,7–5,8 s de pared y 0,55–0,66 s de CPU, fuera de la petición de upload.
- **Demora:** es una cota superior en el reloj de la base. Con las muestras a 1 Hz, las marcas casi nunca coinciden con un muestreo.
- **Escenario anterior (descriptivo, no causal):** el diagnóstico de 30 s sin worker/Beat tenía 346/400 lecturas sucias y el upload ocupaba un worker web 5,67 s.

## Decisión y límites

- **Seis workers:** no se adoptan; el criterio prefijado falla.
- **Cuatro workers:** siguen siendo la referencia. En la topología normal, con la corrección de la marca sin señal, superan el filtro de 30 s con margen: p95 ≈0,50 s y 20D+U ≈3,9 < 4.
- **Contraste descriptivo con el escenario eager:** allí había 346/400 lecturas sucias, un upload de 5,67 s en petición y bloques FAIL. Aquí hay ≈10/400 lecturas sucias y un upload de ≈0,27 s. La diferencia es compatible con que la topología eager añadía coste que la topología desplegada no tiene. No se cuantifica causalmente y no cambia los resultados anteriores, que conservan su escenario y veredicto.
- **Alcance:** controles de 30 s en un host compartido. No acreditan el gate de 60 s, el contractual de 900 s ni capacidad de producción. W ≈3,9 deja poco margen para 4 workers en carga sostenida; la estabilidad se tiene que medir.
- **Limpieza:** el revisor liberó los cuatro bloques y la verificación final fue correcta: bases de bloque y compartida retiradas, medios eliminados, PIDs web/worker/Beat ausentes, Redis db 15 vacía y fuentes sin cambios. El aviso del runner `owned_processes_with_output_path_absent=False` correspondía al propio revisor, todavía vivo en ese instante; la comprobación posterior no encontró procesos.

CR09 y GS01 siguen abiertos; porcentajes, contrato y umbrales sin cambios. Para avanzar a la aceptación hace falta que el usuario decida si el gate de 60 s y el contractual de 900 s se ejecutan en `normal_worker_beat`, y una autorización expresa para el gate de 60 s.
