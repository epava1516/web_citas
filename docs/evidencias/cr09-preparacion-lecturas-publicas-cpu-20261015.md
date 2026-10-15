# Preparación ampliada: CPU integrada y decisión

Run `20261015-145504-091e1959`, SHA `8232613`:1PASS101.27s. Mismo diagnóstico que `142111-875169c8`:72peticiones sintéticas secuenciales, seis casos×12 más control inicial, backend propio con comprobación identidad/cgroup/starttime, sin estadísticasPG. Fuentes y limpieza independiente verificadas.

| CPU backend por petición(ms) | Antes | Candidata |
|---|---:|---:|
| listing es | 56.667 | 60.000 |
| listing en | 38.333 | 44.167 |
| search es | 81.667 | 81.667 |
| search en | 82.500 | 81.667 |
| detail es | 27.500 | 25.000 |
| detail en | 22.500 | 11.667 |
| Media |51.528|50.694|

Resultado mixto. FichaEN calentada reduce media de22.5→11.667ms (fotos12.5→3.333); fichaES27.5→25ms incluye calentamiento de nuevas familias. Listados empeoran y búsquedas casi no cambian. No atribuir esa variación completa al cambio ni inferir p95 desde la media o elegir sólo la fichaEN como resultado global. El diagnóstico de tres brazos demuestra ahorro aislado, pero no la representatividad de toda la carga. Cuantización100Hz/proc/12peticiones limita precisión.

Decisión: los9controles específicos,69ampliados,11retirada/privacidad y la disminución localizada justifican UNA carga corta limpia para decidir retener/retirar la ampliación. No afirmar mejora agregada causal ni elevar cuotas/concurrencia. El limpio anterior7.423942sFAIL permanece; no repetir salvo cumplimiento y no aceptar15min/N3 desde esta etapa. Si la nueva carga falla, conservar fallo y diagnosticar por separado; ningún barrido automático.
