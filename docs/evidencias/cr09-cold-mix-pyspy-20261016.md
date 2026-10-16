# Captura del primer request de un proceso — evidencia parcial

`20261016-132226-55f803a5`: **1 FAIL/100,42s**. Py-spy0.4.2 escribió la traza y terminó1 con ECHILD; no se transforma enPASS. Hijo independiente comprobado:72lecturas completas,0error,hashes de cuerpo iguales a referencias del padre,DEBUGFalse. Fuente y limpieza verificadas independientemente. [Recibo](cr09-cold-mix-pyspy-20261016.json).

Wall y CPU de aplicación instrumentados en ms; primera lectura de cada ruta frente a media de11posteriores. No son medición limpia ni p95.

| Ruta | Primera wall | Posteriores wall | Primera CPU app | Posteriores CPU app |
|---|---:|---:|---:|---:|
| /es/ | 359.34 | 210.13 | 175.00 | 120.53 |
| /en/ | 256.89 | 201.93 | 127.93 | 113.27 |
| /es/?q=photography | 251.32 | 210.74 | 123.99 | 111.39 |
| /en/?q=synthetic | 254.84 | 224.96 | 141.19 | 120.80 |
| /es/listing/:id/ | 89.42 | 73.21 | 47.18 | 43.41 |
| /en/listing/:id/ | 76.10 | 61.45 | 40.39 | 33.75 |

La primera petición real fue listadoES, con24muestrasGIL; las otrascinco69muestras y las66posteriores662. En la primera,11muestras incluyen renderizado de plantillas,6renderizado de formularios y8_state_page; son marcos inclusivos solapados y pocos datos, no porcentajes precisos de CPU. **No hay marcos de loader/get_template en la primera petición**: la hipótesis de compilación fría de plantillas de formulario queda sin respaldo y no se cambia startup por esta pista. La traza posterior sí muestra mucho trabajo en PublicationContext/prefetch, pero no identifica por sí sola el exceso inicial ni justifica otra microoptimización.

Preparación estática de producción, sin referencias ni conexiónDB del hijo antes de la primera petición; buffersPG ya usados. Sin TCP/cuatro workers/Beat/subida ni observadorPG/SQL/GC superpuesto. No inferir tiempoPG como wall−CPUapp; no descartar muestrasfallidas ni repetir carga limpia.

Revisión del [código oficial py-spy0.4.2](https://github.com/benfred/py-spy/blob/v0.4.2/src/main.rs#L417): tras escribir la traza consulta try_wait del hijo; la duración limitada permite finalizar captura con el hijo todavía vivo y el lanzador después lo termina. Posible corrección del instrumento a validar primero en proceso mínimo propio, sin actualizar versión/lock ni cambiar permisos. Debe registrar explícitamente ese teardown y comprobar finalización de todas las lecturas antes, PID/start_ticks y ausencia de procesos/zombis después; salida0 de py-spy sola no acredita salida normal del hijo. No se ejecutó esa variante todavía.
