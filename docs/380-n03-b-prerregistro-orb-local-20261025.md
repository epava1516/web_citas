# N03B — contraste acotado de características ORB del origen

25/10/2026. Alfa, N03 abierto, 3/13 bloques aceptados. Grafo previo focal de379/341/README/seguimiento verificado:1979 fuentes,18599 nodos,81290 relaciones; SHA56e296811750226932e20855ec064d59e49348ed07f588d3cde9da6057d14851. Inspección directa del detector confirma extracción ORB del origen repetida por candidato. El borrador aislado no está integrado ni validado.

## Hipótesis y criterio previo

Reutilizar características ORB del origen únicamente dentro de una invocación de detect_matches, preparadas al primer candidato perceptual y ligadas por identidad a su imagen inmutable. Sin índice, límite de candidatos, caché global ni cambio de locks, exclusiones, persistencia o record_match. Mantener confirm_match por candidato y API previa. Referencia vigente primero; candidata sólo después de comprobarla.

Instrumento tests/test_similarity_prepared_reference.py: corpus sintético denso de100 originales distintos del helper original, seis invocaciones completas con inserciones nuevas; antes de cada una se borran sólo Match del origen y se restablece comparison_complete, fuera del reloj. Primera muestra separada y cinco posteriores. PostgreSQL real/Redis propios, serial, sin worker; eager falso después de preparar fixtures. No mide cola, subida, capacidad ni p95. RNG diagnóstico1847 antes de cada pareja y OpenCV un hilo idénticos en ambas pasadas; no equivale a mezcla productiva natural.

Preservar conjunto exhaustivo esperado de candidatos y exclusión del mismo sujeto. Comparar SHA del corpus, todos los campos MatchResult y pares método/score persistidos por SHA del candidato: igualdad exacta entre muestras y entre versiones, sin usar PK como identidad. Esperado100 confirmaciones,200→101 extracciones ORB (2N→N+1). SQL no mayor que referencia. Algoritmo geométrico y umbrales deben ser idénticos por comparación AST; comprobar fallback, bajas características, API y arrays de sólo lectura con pruebas reales de OpenCV. La integración del detector debe aceptar el keyword y conservar resultados persistidos.

Relojes: wall y CPU de hilo de detect_matches completos, incluyendo observadores idénticos; consultas y tiempo execute mediante execute_wrapper; pico Python por operación y máximo RSS del proceso, no memoria nativa exacta. Publicar mediana/rango de cinco posteriores y primera aparte. Exigir mejora clara de CPU y wall posteriores sin regresión funcional/SQL; no aceptar por conteo solo. Preservar límites originales corpus<128MiB y RSS<1GiB. La retención acotada de características ORB_MAX_FEATURES puede añadir memoria Python: declarar delta medido y comprobar que no crece entre llamadas; sin ampliar límites originales.

## Ejecución y decisión

Congelar referencia de fuentes y dependencias antes de ejecutar. Runner oficial: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_similarity_prepared_reference.py`. Una pasada referencia y una candidata, mismo instrumento; conservar errores y avisos terminales de Telegram. No repetir adaptativamente para buscar significación. Separar QA de tiempos de aplicación. Verificar fuentes sin cambios, JUnit y retirada de recursos propios.

Por decisión expresa del usuario: si no hay mejora clara, conservar implementación vigente, documentar evidencia y posponer esta optimización al final del desarrollo; avanzar al siguiente punto. Tiempos actuales aceptables en alfa. No encadenar nuevas hipótesis marginales. El diferimiento no es PASS ni elimina correcciones funcionales/seguridad o conciliación N03/N07. MOD09 restante sigue diferido. Sin proveedores, datos reales ni apertura.
