# N03F2 — prerregistro de crecimiento histórico con cohorte actual fija

Alfa, N03 abierto, 3/13. Posterior a la corrección F1 aceptada en390 y commit fa64767. Este lote mide una obligación pendiente; no busca otra optimización marginal ni modifica aplicación.

## Población y oráculos

Tres casos seriales PostgreSQL/Redis propios: 0/10/100 Photos históricas, N+1 revisiones históricas incluyendo origen vacío. Dos Blob ready y dos Photos actuales permanecen fijos. Histórico comparte esos mismos bytes; cambia sólo la cardinalidad retenida. Original sintético640×480, candidato recortado20% y JPEG70 antes de derivadoWebP98. Firmas/archivos preparados fuera de relojes. Ledger sintético nativo clasifica histórico, sin aprobación humana ni proveedor.

Seis invocaciones completas detect_matches por cohorte, primera separada y cinco posteriores; antes de cada una se reinician únicamente Match y flag del origen actual fuera de reloj. OpenCV un hilo y RNG1847 declarados. Un candidato elegible, una confirmación ORB real, un Match exacto; comparar hash del corpus y resultado canónico entre las tres cohortes, no sólo dentro de cada una. Histórico, revisiones, ledger, Blob y bytes intactos. El selector antes despacha sólo query y después ninguno, una SQL nativa por selector. Transporte capturado explícitamente; no acredita ejecución de cola.

## Medidas y límites previos

Pared, CPU del hilo y consultas/tiempo execute numérico por detector y selector antes/después; sin SQL ni datos de sujetos. Primera muestra aparte, mediana/rango de cinco posteriores y cardinalidades. RSS high-water del proceso menor1GiB, corpus menor128MiB. Timeout global900s, sin extrapolación a80000, p95/SLA, HTTP, worker/Beat ni proveedores. No se infiere aceleración: misma aplicación, histórico distinto. Si aparecen costes sin mejora clara, registrarlos y avanzar conforme a decisión del usuario; conservar cualquier fallo funcional como fallo.

## Ejecución y evidencia

Comando: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_media_retained_population.py`.

Antes de ejecutar: grafo focal semántico de esta ficha y AST del instrumento, congelación de fuentes completas. Preservar resultado original incluso si falla. Verificar JUnit3 casos sin skips, propiedades completas18muestras, igualdad entre cohortes y ausencia de recursos propios, namespace ajeno intacto, aviso terminal Telegram confirmado. El tiempo de QA no es latencia de aplicación. No repetir por documentación o frescura. N03 sólo podrá cerrarse tras conciliación final por acción y testigos equivalentes.
