# B16-354 — Regresión funcional terminal y correctiva de guardas CLI

La ejecución común `20261024-094540-3a6ec8ac` terminó con resultado ERROR, conservado íntegro: 3829 casos únicos, 3697 PASS, 3 FAIL y 129 SKIP; cuatro subreportes PASS adicionales no son casos nuevos. Pytest duró 15619,481 segundos según el runner (4 h 20 min); el resumen pytest informa15617,33s y JUnit15616,910s, relojes distintos. Las cuatro pruebas de selección de trabajadores coinciden con el conjunto esperado. Las1722fuentes congeladas coinciden con el lanzamiento y con la auditoría anterior a la corrección. Los commits durante la espera y las adendas documentales no cambian esos bytes; HEAD de lanzamiento920ea36 conserva su identidad histórica, master evolucionó por checkpoints y obligaciones expresas del usuario.

## Diagnóstico y corrección

Los tres fallos son arguments4/7/9 de test_invalid_benchmark_selection_stops_before_service_commands. En todos, el runner ya rechazaba la selección con SystemExit2 y sin ejecutar comandos de servicios; la aserción final esperaba el mensaje anterior a la incorporación del escenario nativo mixto aislado. Se reemplaza únicamente ese literal esperado en tests/test_benchmark_owned_redis.py. No se cambian runner, permisos, selección válida, producto ni criterios de rechazo.

La regresión focal del archivo completo `20261024-140904-a428539f` acredita23PASS/0FAIL/0ERROR/0SKIP, JUnit0,487s; el runner también aprueba Ruff, documentación, Django y ausencia de migraciones pendientes. Son guardas unitarias con servicios locales preparados por el runner, no una prueba de integración funcional de Redis por estos23casos. Fuentes, retirada de contenedores y temporal y recibo Telegram confirmados.

La [conciliación verificable](evidencias/b16-functional-terminal-corrective-20261024.json) reconstruye el archivo anterior por bytes con una sola sustitución, confirma que las otras1721fuentes son idénticas y que los23casos focales pertenecían a la selección original. La cobertura conciliada es3700PASS/129SKIP, sin fallos pendientes en esa selección. Esto no es una ejecución única3829PASS ni transforma el ERROR original en PASS.

## Omisiones, limpieza y continuidad

Las129omisiones reales están enumeradas individualmente en artifacts/beta-promotion-fix-20261020/b16-354-skip-dispositions-pending.json con motivo, fase y huella de fuente. Su disposición por requisito/evidencia sigue pendiente; no cuentan como PASS. Tampoco se aceptan los306casos de capacidad ni las11exclusiones oficiales por esta ejecución.

El supervisor terminó, runner y proceso pytest ya no existen; PostgreSQL/Redis por etiqueta y temporal propio ausentes. Telegram terminal ERROR y correctivo PASS enviados; el disparador reactivó el mismo goal sin crear otro ni reiniciar consumo. La identidad de cada resultado se conserva y no se repite la batería larga por la sola corrección de mensaje.

## Duraciones y optimización futura

El mayor caso territorial10000 consumió9793,097s; el plan confirmado10000,5719,782s; el contrafactual10000,4442,236s (sumas de fases por caso). Son costes de pruebas completas con preparación, oráculos y trabajo de aplicación mezclados, no latencias HTTP. Los archivos nuevos no tenían estimación histórica y el reparto loadfile mantiene seis casos de plan en un trabajador: cuello de planificación identificado, sin cuantificar aún ahorro posible. Se conserva historial real para futuras planificaciones en artifacts/beta-promotion-fix-20261020/b16-354-observed-duration-history.json. Antes de cambiar preparación o producto, atribuir costes por etapa y preservar independencia, autoridad y completitud de los oráculos.

B16 sigue abierto para conciliar omisiones, capacidad aplicable y matriz de requisitos. B10 conserva deuda residual pendiente; B14 depende de proveedores no elegidos, B15 es opcional y B17 no autoriza apertura. Trece de18puntos cerrados localmente. La entrega permanecerá en alfa. La reconstrucción completa del grafo y el diferencial de inventario son obligaciones finales posteriores, no ejecutadas por esta correctiva.
