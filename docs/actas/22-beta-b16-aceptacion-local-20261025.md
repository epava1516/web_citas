# Acta22 — Aceptación técnica local B16

B16 queda aceptado técnicamente en local para la candidata sintética integrada, el25deoctubrede2026. Decisión de Codex tras conciliación de requisitos, versiones, omisiones, capacidad aplicable y continuidad. Quince de18puntos aceptados localmente: B00–B13 y B16. B14/B15/B17 permanecen sin aceptación técnica; B15es opcional. El proyecto sigue en alfa y no se autoriza apertura.

## Identidad y evidencia por requisito

La [matriz final](../evidencias/b16-final-candidate-reconciliation-20261025.json) fija1507fuentes ejecutables, dependencias e instrumentos porSHA desde el prerregistro370y commit8f68fc8; documentación posterior no cambia esos bytes. El manifiesto original completo conserva1723fuentes. PostgreSQL17, Redis7.4, objetos y proxy reales locales; imagen soporte inmutablef50e2f01874ebbd1147261160c6058c64bf2e8d26d50b2446c7549d2692b947b, fuentes e intérprete readonly. Identidad, pagos y sujetos son sintéticos. Los manifiestos identifican migraciones/datasets/instrumentos; HEADno los sustituye.

| Requisito B16 | Evidencia y límite aceptados |
| --- | --- |
| Contrato coherente AD01–AD11 | [322](../322-conciliacion-requisitos-b16-20261024.md), [329](../329-revision-semantica-testigos-b16-20261024.md) y matriz final:45funciones con aserciones revisadas y huellas vigentes; AD08opcional no implementado. Las filas se solapan y no son pruebas nuevas. |
| Verificación integrada y focal | [315](../315-regresion-funcional-terminal-correctiva-b16-20261024.md): original3697PASS/3FAIL/129SKIP; correctiva23PASS, conciliación3700PASS/129SKIP. ERRORoriginal conservado. No ejecución única verde de3829casos. |
| Cambio posterior de señal | [317](../317-registros-historicos-senal-publicacion-b16-20261024.md) y329: guarda de registros históricos, puenteAST, focales y worker/Beat; no repetición funcional completa posterior. |
| Omisiones y exclusiones | [316](../316-conciliacion-omisiones-b16-20261024.md), [321](../321-auditoria-carril-capacidad-b16-20261024.md), [335](../335-conciliacion-final-candidata-b16-20261025.md):129SKIPfuncionales y9de capacidad conservados, ocho testigos funcionales suplementarios;121diagnósticos/prototipos sinPASS. Once exclusiones dispuestas con pruebas exactas, puentes o sustitución de alcance, sin inventar oncePASSactuales. |
| Recorridos ES/EN y transporte | [318](../318-matriz-rutas-vigente-b16-20261024.md),329y[330](../330-conciliacion-exclusiones-b16-20261024.md):matriz10000/ocho condiciones, navegador actual, seisTCPy transporte8MiBactuales; no cobertura universal de navegador desdeHTTP. |
| Capacidad pública aplicable | [332](../332-auditoria-http-corto-b16-20261025.md) y[334](../334-auditoria-http-contractual-b16-20261025.md):corto1200y contractual18000respuestas/15subidas, p95observable410,559ms, generador y contabilidad conformes;8CPU/8GiB/swap0, sinOOM y limpieza independiente. Contenido:68oráculos antes/después, no cuerpos íntegros archivados de todas las muestras. |
| Selección y exportación privadas | [Disposición TCP](../evidencias/b16-selection-tcp-disposition-20261025.json):31páginas por sujeto solapadas, p95<2s y autoridad/separación/completitud. [Acta21](21-beta-b10-disposicion-local-20261024.md):FAILtemporal de cobertura/JSON/binario bajo MOD09, integridad preservada; noPASSglobal de ese flujo. |
| Observación, recuperación y continuidad | [Auditoría operativa](../evidencias/b16-operational-gates-reconciliation-20261025.json):testigos originales60/26/21/5/2reaparecen aprobados en353con huellas de pruebas vigentes; grupos solapados. Cinco restauraciones reales conservan propiedades de autoridad, replay, medios, retirada deDBy publication_authorized=false. [Actas14](14-beta-b12-aceptacion-local-20261021.md)/[15](15-beta-b13-aceptacion-local-20261021.md) conservan límites de cada familia. |
| Conservación, avisos y versión | Auditorías315/317/321/330/332/334conservan fuentes, negativos, integridad y retirada; Telegramsent.370notificó terminal y reactivó mismo objetivo con consumo conservado; ninguna batería nueva por redactar esta acta. |

## Deuda aceptada individualmente y exclusiones

Se conserva la disposición B10/MOD09: objetivos2s/5s y FAILde cobertura/JSON/binario, crecimiento deBlob, densidad de confirmación/registro, retención, concurrencia y cola. No bloquean esta aceptación local conforme a la excepción expresa, ni se convierten en mejora o capacidad ilimitada. Deben figurar en el inventario diferencial y próximo roadmap.

B14carece de proveedores elegidos/integrados; guardias locales no acreditan identidad, edad o recepción externas reales. B15no está implementado, con diseño/persistencia/consentimiento pendientes. B17/G01–G08conservan operador, personas, custodia externa, políticas definitivas y revisión jurídica/seguridad independientes; ninguna prueba sintética los satisface. Los diagnósticos opt-in no activados siguen sinPASSy no se usan para afirmar sus escenarios particulares.

No se ha identificado un defecto crítico pendiente en el alcance local conciliado de acceso, publicación o pérdida de datos; esta conclusión se limita a los recorridos y evidencias enumerados, no certifica seguridad o legalidad global. El mantenimiento del puente de versiones evita atribuir una regresión única a fuentes que no se ejecutaron juntas.

## Obligaciones finales del contrato

Esta acta acepta B16, no el objetivo completo ni la apertura de beta. Restan reconstrucción completa desde cero del grafo, diferencial del inventario original I01–I28, integración de ese inventario y acta final del contrato con las disposiciones restantes. Los refrescos dirigidos previos no cumplen la reconstrucción. El proyecto permanecerá en alfa después de ese cierre.
