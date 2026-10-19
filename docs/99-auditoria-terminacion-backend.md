# Auditoría de terminación B-B — 2026-10-19

Estado: en curso; B-F aceptada en [acta08](actas/08-bf-aceptacion-tecnica-local-20261019.md), B-B/C abiertos. Requisitos literales en contrato16 §7. Grafo AST dirigido actualizado antes de revisar; no equivale a actualización semántica de toda la documentación. [Inventario de casos actuales](evidencias/bb-current-test-inventory-20261019.json) es localización de evidencia candidata, no aceptación automática por cantidad de pruebas.

| Punto | Evidencia localizada | Verificación pendiente |
| --- | --- | --- |
| BB01 consultas/búsqueda/paginación | N3 común, proyección mantenida, filtros/privacidad y carga limpia válida/repetida CR09 | Conciliar fuentes/alcance y objetivos; MOD09 sigue excepción provisional, sin repetir carga sin riesgo concreto |
| BB02 tareas/reintentos/caducidad/duplicados | N3 de ciclo, procesamiento, recuperación; positivos de recompresión/recorte/rotación y negativos sintéticos | Calibración y límites exactos; vincular worker/Beat reales y no extrapolar precisión a fotos reales. FAISS/CC05 permanece propuesta documentada |
| BB03 IMP001–011/seguridad/derechos/retención | Revisión técnica CR09 y pruebas actuales de permisos, cuentas, registros y retención | Matriz literal por IMP con implementación, evidencia y límites de producción; no confundir revisión técnica local con externa/jurídica |
| BB04 geografía | Dos casos previos de importación, rollback inicial e IDs idempotentes | Nueva regresión preparada para actualización versionada, renombrado/IDs/asociaciones y rollback sobre datos existentes; ejecutar los tres casos en PostgreSQL propio |
| BB05 adaptadores | Pruebas de verificadores/avisos/pagos sintéticos/objetos locales | Correspondencia de válido/fallo/pendiente, producción deshabilitada y aislamiento; ningún proveedor real acreditado |
| BB06 Docker/operación/recuperación | Imagen v11, BF05 Caddy/estáticos, restauración PG/medios y reconciliación actual | Revisar actualización de volumen estático persistente, migración/rollback, alertas y simulacros OP; delimitar cifrado/PITR/custodia y RPO/RTO sin ampliar alcance de dumps locales |
| BB07 sitemap/indexación | N3 sitemap/robots/SEO, retirada y navegador móvil | Leer reglas y pruebas, comprobar fuente vigente/privacidad/códigos y coherencia BF06 |

Prerregistro BB04: ejecutar `tests/test_geography_import.py` completo, **tres casos**, mediante runner oficial focused con PostgreSQL/Redis propios y kernel native-sealed. Se conserva el importador sin cambios; prueba nueva sobre fixture sintético del proyecto, nunca dataset nacional o servicio externo. Controlador4CPU0–3/3584MiB/swap0/pids512, PG1CPU4/1536MiB y Redis0,2CPU5/128MiB. Fuentes/selección/limpieza/Telegram verificables, sin modificar servicios normales. El PASS acotado no sustituye N3 de entrega.

BB04 verificado: [tres casos PASS](evidencias/bb04-geography-terminal-20261019.json), PostgreSQL real, fuentes/limpieza/Telegram comprobados; sin dataset nacional real. BB06 [prerregistro específico](evidencias/bb06-static-update-preregistration-20261019.json): validar volumen estático persistente con CSS más reciente que la imagen de rollback y archivo obsoleto; comparación de collectstatic normal frente a clear=True con HTTP/SHA. La regla por fecha procede de la documentación oficial de Django y del código instalado. No es integración de base de datos y no sustituye sus ensayos separados.

BB06 intento inicial [ERROR de readiness](evidencias/bb06-static-startup-failure-20261019.json), antes de medir: conexión reiniciada al arrancar Caddy no capturada por URLError. Recursos limpios/Telegram EXIT1. Corrección sólo de excepción transitoria de arranque, sin relajar comprobaciones; [prerregistro corregido](evidencias/bb06-static-ready-preregistration-20261019.json).

BB06 volumen estático corregido PASS: negativo esperado demuestra CSS más reciente/JS obsoleto conservados; clear=True restaura cinco SHA HTTP200 y obsoleto404. [Auditoría](evidencias/bb06-static-update-terminal-20261019.json), fuentes/limpieza/Telegram independientes. Runbook12 corregido para mantenimiento y STATIC_ROOT exclusivo; no cambios de app, esquema, cuotas ni servicios normales. Resto de BB06 sigue en revisión.

BB06 cifrado completo: el dump del ensayo previo no estaba cifrado aunque sí lo estaba el registro de reconciliación. Se conserva el control local original y se añade una variante que cifra el conjunto PostgreSQL/medios, elimina las copias temporales originales y restaura desde el archivo autenticado; clave errónea/alteración deben rechazarse antes de extraer. [Prerregistro de dos casos](evidencias/bb06-encrypted-backup-preregistration-20261019.json). Sólo fixture; sin nuevo gestor de backups, WAL/PITR, custodia externa, recuperación de claves ni garantías de producción.

BB06 copia completa cifrada [2PASS/0SKIP](evidencias/bb06-encrypted-backup-terminal-20261019.json), fuentes/PG/medios/limpieza/Telegram verificados. Comparación de escenarios locales independientes, sin atribuir diferencias a optimizaciones:

| Métrica | Control local sin cifrado de copia | Copia completa cifrada |
| --- | ---: | ---: |
| Restaurar y reconciliar | 5.012500621844083 s | 5.285660676192492 s |
| Edad máxima observada de copia | 6.54982328414917 s | 7.066380262374878 s |

Ambos escenarios respetan RTO8h/RPO1h del fixture, sin extrapolar cadencia/custodia productivas ni PITR. Siguiente control BB03/IMP009: [auditoría de avisos de dependencias congeladas](evidencias/bb03-dependency-audit-preregistration-20261019.json), sólo consulta pública de paquetes/versiones; no actualiza el lock.
