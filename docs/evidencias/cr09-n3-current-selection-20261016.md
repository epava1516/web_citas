# Selección actual para regresión común — colección, no ejecución

[Recibo completo](cr09-n3-current-selection-20261016.json). Colección161507-46e1852c, salida0:3626casos/604archivos seleccionados,3628antesdeexcluir2nodosHTTP. Ningún caso funcional ejecutado. Archivo de nodeids completo comprimido y SHA conservados en artefactos del run; sin selección argv de nodeids gigantes.

| Inventario | Archivos |
|---|---:|
|Planv3particionado|501|
|Planv3separado|2|
|Actual|606|
|Realmente nuevos|103|
|Anteriores modificados|15|
|Retirados|0|
|Selecciónregressionactual|604|

Se mantienen exclusiones explícitas del runner: short/measuredHTTP, publication_state_tcp y rights_portability_large_history. No aceptar capacidad/latencias omitidas por esta colección. El contractual limpio152034sigueINVALID yel diagnóstico155052no lo sustituye. La excepción provisional MOD09 no elimina requisitos funcionales de exportación.

Setenta archivos contienen llamadas pytest.skip: razones/ubicaciones están inventariadas, pero colección no evalúa esos cuerpos ni acredita cuántos se omitirán. Incluyen diagnósticos explícitos, pruebas que exigen herramientas nativas y escenarios de revisión de contenido. Todo skip real necesita clasificación en el terminal; no aceptar N3 con omisiones necesarias. Conservar controles cerrados sin confundir prototipos rechazados con código entregado.

PostgreSQL/Redis reales propios, dependencias/nativo/gates del runner,fuentes congeladas y limpieza independiente de PIDs/start_ticks/temporales/contenedores verificadas. La imagen RustFS fijada faltaba al preparar regresión; se restauró por digest exacto1803faef… y su IDf6b22807… está comprobado, sin cambiar la fixture ni usar proveedor real de datos.

Siguiente batería funcional: mismos604archivos/3626casos con tres workers xdist porarchivo y snapshots de bootstrap aislados porrun/worker. Límites habituales del controlador/PG/Redis y de cadaobjetoRustFS, sincargasdeaceptación concurrentes; previo a arrancar registrar commit ycondición de salida. Regresión con exclusiones es componente de N3, no N3 integral por sí sola.
