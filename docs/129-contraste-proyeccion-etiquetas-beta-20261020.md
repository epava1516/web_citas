# Contraste finito de proyección de etiquetas comerciales

Fecha:2026-10-20. Estado: ejecutado y auditado; candidata rechazada, sin cambios de producto. Continúa [128](128-diagnostico-proyeccion-etiquetas-beta-20261020.md), diez casos auditados de paridad/formaSQL; no son evidencia de mejora HTTP. B07–B09 abiertos, cortoTCPFAIL y900s bloqueado.

## Hipótesis y variante exacta

Instrumento explícito tests/beta_label_projection_roi_diagnostic.py. Usa exactamente las dos copias experimentales de128, comprobando SHA del producto y hash de candidata contra su auditoría10PASS antes de preparar10000perfiles. Conservar filtro original de derechos, consumo del cursor, UUID, orden, población, conteo y guarda nativa. A/B ejecutan originales y C las dos copias, mediante los mismos dos dispatchers. La anotación de prioridad sigue disponible; sólo la página propiaRR consume el mapa local y selecciona IDs. No COUNTextra, derechos globales, cache persistente, cambios de autoridad o recursos.

El diagnóstico pequeño mostró tres parámetros/expresionesJSON frente auno. Comprobar si mejora tiempo completo con2000derechos: no extrapolar los42bytes de un derecho ni prometer10%. La vida extendida del mapa puede aumentar memoria; medirla por separado. No volver a ensayar las variantes rechazadas111/112 ni cambiar umbrales para esta candidata.

## Recursos y controles prefijados

10000perfiles/2000derechos Top/Premium sintéticos emitidos mediante servicios, misma fixture10000de111/112,20%promocionados, agencia/foto/geografía compartidas. No compras, datos reales ni proveedores. PostgreSQL/Redis propios, un workerpytest, mismas cuotas, fuente nativa fijada y READ_REPAIRdesactivado. Sin otra carga propia durante la medición; host compartido, sin aislamiento total supuesto. GCnormal y política comprobada antes/después, sin collect manual, desactivación o umbrales alterados.

ListadoES y búsquedaEN q=synthetic. Seis permutacionesABC/ACB/BAC/BCA/CAB/CBA por ruta. Backend físico nuevo por brazo, una lectura caliente fuera del control y tres lecturas medidas.36calentamientos+108controles, más8observaciones posteriores=152HTTPClient; no152tests ni cargaTCP. En todas las lecturas:200/no-store/ruta state, cuerpoSHA, recuento, IDs y patrocinio idénticos; primera página24filas con patrocinio y estado limpio.

Wall y CPUthread de aplicación por lectura. CPU real del backendPG propio mediante schedstat antes/después de cada bloque de tres lecturas; verificar PID/startticks/cgroup/propiedadDocker y cursor_tuple_fraction. Conexión, calentamiento, resolución de identidad y lecturas de metadatos fuera del reloj. Ningún profiler, wrapperSQL, contador o tracemalloc dentro de108controles.

## Criterios de decisión

Por cada ruta: A/A estable dentro10% en medianaswall/CPUapp y CPUbackend por lectura; medianaC al menos10% menor que promedio de medianasA/B; CPUapp/PGC como máximo105% de referencia; al menos4de6bloques sin regresiónwall. Exigir todos los criterios en ambas rutas. Son los mismos límites111/112. PytestPASS sólo significa integridad; eligible=false rechaza adopción, conservando negativo. No repetir una variante idéntica para cruzar umbral, elegir bloques favorables ni afirmar reproducibilidad general desde un ensayo.

## Observaciones posteriores y aceptación

Ocho lecturas observadas después de terminar todos los controles: por ruta y brazoA/C, una lectura sólo con wrapperSQL cuenta execute/parámetrosJsonb/bytesJSON y otra distinta sólo contracemalloc mide heapPython de la petición completa. No guardar SQL niIDs. La serialización adicional del observador SQL queda fuera de la lectura de memoria, para no contaminar el pico con diferente número de mapas. Exigir reducción estricta de parámetros ybytes en cada ruta, manteniendo firma. Execute excluyeFETCH; bytesserializados no son tráficoTCP. HeapPython observado no es RSS del servicio ni memoriaPG; revisar variación y vida del mapa antes de adoptar. Sin planes, profiler o cambios de planificador adicionales.

Resultado beta-label-projection-roi.json con todas las muestras/identidades, hash de ambos módulos/candidata y políticaGC. Auditoría independiente de métricas/criterios, nodeid/fases, igualdad de fuentes congeladas frenteactual,622producto intacto, recursos/PID yTelegram confirmado. Auditar antes de editar fuentes tras terminal. Elegibilidad positiva aún exige revisión de memoria, implementación local, regresión afectada y cortoTCPlimpio con todos sus presupuestos; no acepta automáticamente beta ni900s.

Los dos ensayos anteriores de igual fixture/diseño tardaron921–932sJUnit. Preparar ejecución con log persistente y verificar identidad del runner; previsión cercana a16min, sin garantía ni crédito de capacidad. Si la previsión cambia a espera muy larga, aplicar el procedimiento autorizado de aviso previo confirmado y pausa explícita; ninguna reactivación automática.


Revisión previa: el primer diseño mezclaba wrapperSQL ytracemalloc en cuatro lecturas. Se corrigió antes de ejecutar: separarlas añade cuatro lecturas,152en total. No es un negativo funcional ni cambio de umbral. Las mediciones del diseño anterior no se ejecutaron.


## Resultado auditado y rechazo

221617-820d771a:1PASS/0FAIL/0ERROR/0SKIP de integridad experimental,960,263sJUnit. [Auditoría](evidencias/b08-label-projection-roi-audit-20261020.json) recomputa muestras/criterios, reconstruye ambas copias conAST sin importar Django, confirma candidata idéntica a128,36bloques/108controles/8observadas=152lecturas, fuentes congeladas/freshsource,622producto intacto, backendpropio, limpieza/PID yTelegram1792535569604552652-3633213 enviado. La auditoría1792535627332252933-3736378 también fue enviada. El fallo de ps al desaparecer losPID fue sólo una observación de transición; resultado terminal leído y auditado después. No es otro fallo de pytest.

| Ruta | MedianaA | MedianaB | MedianaC | C frenteAB | A/A estable | Bloques no regresivos |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| ListadoES |328,168ms|317,055ms|345,804ms|+7,19%|sí|3/6|
| BúsquedaEN |338,155ms|396,743ms|358,424ms|−2,46%|no|5/6|

Ninguna ruta cumple todos los criterios. candidate_eligible=false: rechazada, sin aplicar al producto. No atribuir inestabilidad a causas externas no medidas ni rescatar sólo un bucketCPU favorable. CPUapp C/AB0,973listado/1,005búsqueda; CPUbackend1,019/0,711 no sustituyen estabilidad ni mejora mínima del tiempo completo.

Las observaciones separadas confirman3→1parámetrosJsonb y260673→86891bytesJSON en ambas rutas. HeapPython pico listado1160330→1353315bytes ybúsqueda1149093→1465677bytes; lecturas distintas deSQL ymemoria, sin serialización extra del observador dentrotracemalloc. No RSS ni memoriaPG, ni estimación robusta desde una observaciónA/C. La reducción de parámetros queda demostrada, pero no su beneficioHTTP.

Mantener producto original y condiciones111/112/129. No repetir idéntica variante para cruzar umbral ni cortoTCP por un cambio que no se adopta. B07–B09 siguen abiertos; cortoFAIL y900s bloqueado. El siguiente análisis revisará costeSQL/planificación/hidratación sobre fuentes y evidencia actuales, sin asumir que cambiar workers o cuotas resuelve los requisitos.
