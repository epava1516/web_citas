# Plantilla ORM de página: equivalencia inicial

[Recibo](cr09-page-query-template-n1-20261016.json). Ejecución150322-5eeb04f2: **4PASS**, pytest95,45s. Sólo prototipo en tests; ningún módulo de producto cambiado.

La copia controlada de `_state_page` sustituye únicamente sus dos hidrataciones fijas porIDs. El contexto lee documento vigente y clona una consulta anotada no ejecutada con los IDs frescos. Plantilla LRU8 porversión, sin filas/resultados/autoridad retenidos. Selección, snapshot, conteo, orden, prefetch y guardas se conservan.

Equivalencia de24comparaciones: tresestados(clean/dirty/paused), cuatro rutas(listado/búsquedaESEN), páginas1/2 cuando válidas. Cuerpo exacto con timestamp firmado fijo sólo en test, IDs/count/no-store y generaciones de marcas idénticos. Trescontroles existentes comprueban reemplazo documental, categoría inactiva y caducidad frente a comportamiento nativo. Construirhelper no ejecutaSQL; caché recibehits, mantiene _result_cacheNone y estructura original intacta al clonar/cambiarversión.

Controlador4CPU/3584MiB yPG1CPU/1536MiB propios, Redispropio, kernel nativesealed y dependencias congeladas. Unidadterminal0,fuentes/PIDs/start_ticks/temporales/contenedores verificados independientemente. No prueba todavía concurrencia ni rentabilidad ni matriz100/1000/10000. Siguiente: preregistrar comparación balanceadaA/A/C con GCnormal, SQLcontado y CPUbackend real, rechazando candidato sin ahorro consistente. No nuevacarga contractual antes de ese resultado.
