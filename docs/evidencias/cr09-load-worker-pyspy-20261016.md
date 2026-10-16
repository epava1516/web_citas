# Cuatro workers reales bajo carga — diagnóstico py-spy

[Recibo verificable](cr09-load-worker-pyspy-20261016.json). Captura correctiva PASS: ocho trazas py-spy0.4.2/100Hz/GIL/speedscope, cuatro workers sync propios, dos ventanas de12s. Todas tool0 y PID/start_ticks vivos idénticos al acabar cada captura. Unidad terminal0; CI145637-953c2407 conserva FAIL por p95 instrumentado. Fuentes congeladas y limpieza independiente de runner/hijo/temporales/PG/Redis comprobadas.

Selector corregido une hijos de todos los hilos del árbol propio; los controles demuestran un hueco real del selector anterior, sin probar la causa del fallo145039. Se conserva el árbol exacto observado. Sin cambios app/Yama/permisos, capturas ajenas ni otros perfiladores.

2735muestras iniciales y2882intermedias. Porcentaje de muestras que incluyen al menos un frame de cada grupo (grupos inclusivos y solapados; no sumar):

| Grupo | Inicial | Intermedia |
|---|---:|---:|
| Compilador SQL | 35.2% | 32.7% |
| Construcción de consultas | 21.2% | 23.9% |
| Expresiones ORM | 17.8% | 19.0% |
| Formularios | 33.8% | 30.3% |
| Plantillas | 24.1% | 22.1% |
| psycopg | 12.1% | 10.9% |

PublicationContext.__init__ aparece en42,5%/45,4%, read_publication_values30,9%/32,0%, state_page55,7%/59,1%. El perfil conserva una distribución parecida; no demuestra una inicialización exclusiva ni la causa de la cola/p95. Las ventanas empiezan aproximadamente al inicio−0,5s y+30s: arranque efectivo del muestreador posterior al lanzamiento, sin precisión inventada. GIL filtra esperas sinGIL; estos porcentajes no son cuotas de tiempo total ni de CPU PostgreSQL.

| Carga | p95 observable | Errores | Interpretación |
|---|---:|---:|---|
| Limpia131431 |0,862172866s|0/1200|FAIL|
| Intento145039 sin attach efectivo |0,738744505s|0/1200|CI PASS, captura FAIL|
| Diagnóstico145637 con attach |0,938076341s|0/1200|Instrumentado, CI FAIL|

Generador válido,1200completadas/0timeouts/0pendientes en la instrumentada. No comparación causal entre tiempos ni aceptación. No corrección de producto desde estos porcentajes: contrastar consultas/formularios concretos con experimentos ya descartados antes de proponer un candidato. N3/CR09 y reproducibilidad siguen pendientes.
