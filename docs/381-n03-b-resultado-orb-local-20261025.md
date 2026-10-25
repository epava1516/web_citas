# N03B — reutilización local de características ORB aceptada

25/10/2026. Alfa, N03 abierto, N00/N01/N06 aceptados:3/13. Prerregistro380 y referencia anterior a integración, commit5562c03. El contraste muestra reducción del coste objetivo y tiempos locales, con paridad exacta; se adopta únicamente esta corrección. No se abre otra hipótesis marginal del detector.

## Cambio y garantías verificadas

prepare_query extrae una vez las características del origen, ligadas por identidad a la imagen y conservadas sólo durante detect_matches; arrays de sólo lectura y ORB_MAX_FEATURES800. Preparación perezosa en primer candidato perceptual. confirm_match mantiene API previa y admite el preparado; cada candidato sigue confirmado por separado. Sin caché global, índice, recorte de candidatos ni cambios en persistencia, locks, selección o exclusiones. Root comparó AST: cola geométrica íntegramente idéntica y todas las demás definiciones anteriores de servicios/similitud sin cambios. Imagen no se muta durante la llamada; disponibilidad de OpenCV estable durante ella.

Referencia20261025-175533-a061c196 y candidata20261025-180035-0ecdeb99:1PASS cada una. Mismo corpus de100 originales sintéticos distintos/densos,100 coincidencias esperadas, seis invocaciones con inserciones nuevas. Identidad de corpus/bytes/instrumento y SHA de todos los campos MatchResult y método/score persistidos iguales en las seis muestras de ambas versiones. Exclusión del mismo sujeto y comparison_complete verificados. Diferencias de fuentes:dos archivos de aplicación, nuevo test unitario y registro de trabajo; sin otro cambio ejecutable. Instrumento fija RNG diagnóstico1847 por pareja y OpenCV un hilo; no es tráfico productivo natural.

## Antes y después — aplicación

Unidad: una llamada completa detect_matches sobre el corpus denso100; reloj wall/CPU de hilo con observadores idénticos. Primera separada, mediana de cinco posteriores y rango; SQL medido con execute_wrapper, no comparar directamente con conteos históricos de otro observador.

| Métrica | Antes | Después | Diferencia |
| --- | ---: | ---: | ---: |
| Wall primera | 15,522 s | 12,901 s | −16,9 % |
| Wall posteriores, mediana | 14,954 s | 12,729 s | −14,9 % |
| Wall posteriores, rango | 14,761–15,314 s | 12,455–13,287 s | rangos separados |
| CPU hilo posteriores, mediana | 11,992 s | 10,129 s | −15,5 % |
| CPU hilo posteriores, rango | 11,761–12,367 s | 9,960–10,524 s | rangos separados |
| Extracciones ORB por llamada | 200 | 101 | −49,5 % |
| Confirmaciones / coincidencias | 100 / 100 | 100 / 100 | iguales |
| Consultas SQL por llamada | 1012 | 1012 | iguales |
| Pico Python posterior, mediana | 6016090 bytes | 6010513 bytes | −5577 bytes observados |
| RSS máximo proceso | 273356 KiB | 273208 KiB | sin aumento observado |

Pico Python primera6228745→6267437bytes (+38692), compensación acotada declarada en380 por vida de características del origen; posteriores5843942–6089868→5843291–6087760bytes, sin crecimiento progresivo observado. RSS<1GiB y corpus<128MiB preservados; tracemalloc no mide toda memoria nativa. No inferir p95, causalidad universal o capacidad de80000fotos. Pasadas secuenciales locales: el tiempo SQL también varía; la reducción determinista de99extracciones es atribuible al código, el porcentaje temporal se limita a este contraste. No extrapolar este ahorro a la subida de379.

## Validación y límites

Validación20261025-180404-86f68fb2:46PASS/0FAIL/ERROR/SKIP, test_similarity_prepared_features, test_image_similarity y test_photos. OpenCV real: recompresión, recortes, rotación, no relacionados, bajos detalles/tamaño cero, identidad errónea, fallback sin OpenCV y arrays intactos; API anterior y flujos originales privado/EXIF/reintentos/duplicado/retirada/alta concurrente conservados. Integración densa demuestra keyword y persistencia exacta. No se inyectó un modelo geométrico inválido: rama sin cambios por AST, sin atribuirle cobertura nueva.

Lint inicial de candidata falló por formato de import; corregido antes de congelación y repetición estática PASS, recibos conservados. No repetición funcional para buscar resultado favorable. Huellas congeladas1739referencia/1740candidata intactas durante sus ejecuciones; validación funcional misma candidata. PostgreSQL/Redis propios, namespaces del runner, sin worker en contraste, recursos/temp retirados e inventario independiente vacío; avisos terminales Telegram sent comprobados. QA separada de latencia: JUnit referencia184,343s/candidata165,933s y validación72,566s, incluidos corpus y aserciones; no equivalen a latencia de aplicación. Corpus1580874bytes idéntico.

N03 continúa: conciliar recuperación/reintentos de errores, retención y concurrencia con N07. MOD09 restante sigue diferido al final del desarrollo; tiempos actuales aceptables en alfa. La decisión del usuario se mantiene: una futura hipótesis sin mejora clara se pospone y se avanza; no equivale a PASS ni elimina correcciones funcionales/seguridad. Sin proveedores, datos reales ni apertura.
