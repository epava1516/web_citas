# Correctivas de la regresión amplia y eficiencia de pruebas

Fecha:2026-10-20. Estado: diagnóstico y corrección abiertos; no aceptación beta. Base: regresión funcional155011-55618b9c, fuentes congeladas y auditadas antes de modificar. No repetir la batería completa mientras sus causas sigan sin resolver.

## Resultado conciliado

3454nodeids únicos:3238PASS,38FAIL,56ERROR,122SKIP; cuatro subreportes PASS adicionales elevan el contador JUnit a3458, aunque XML conserva3454testcases. Auditoría beta-broad-functional-negative-terminal-audit-20261020.json verifica fuente actual igual a la congelación, procesos/temporal/recursos declarados retirados, selección funcional/exclusiones oficiales y reciboTelegram1792519659101555188-988609. Los dos workers recogieron exactamente los mismos3454nodeids. No sumar subreportes como pruebas únicas.

El primer intento del auditor esperaba3458elementosXML y falló; el correctivo distingue el contador JUnit de las cuatro subpruebas y concilia el journal con los3454testcases reales. Su negativo y sus notificaciones quedan preservados. La auditoría PASS verifica integridad de un resultado negativo, no acepta la funcionalidad.

## Descomposición y criterio de corrección

- 52errores muestran docker run RustFS125; la inspección local posterior confirma ausente la imagen fijada sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c. Reproducir de forma focalizada, reponer exactamente esa dependencia de pruebas y añadir preflight temprano. No sustituir almacenamiento real por simulador ni convertir errores en SKIP.
- Los otros cuatro errores de preparación y cinco fallos incluyen consentimiento200 frente302. Revisar formularios actuales, autoridad y fixtures antes de atribuir causa; conservar revocación/concurrencia y representación independiente.
- El resto comprende expectativas de catálogo/tarifas/formularios, aislamiento de migraciones, localización/navegador y límites de la segunda fase nativa. Distinguir compatibilidad histórica privada de la exposición romántica actual; no reintroducir categorías profesionales ni relajar guards para pasar tests.

Tres revisiones nativas de sólo lectura han contrastado esos grupos independientes contra código, contrato14 y la evidencia negativa; no ejecutaron pruebas ni editaron archivos. Codex decide cambios e integra; ninguna propuesta de agente es evidencia. Sin escritores concurrentes, sin pruebas de agentes, sin ClaudeV1 ni cambios externos. Registrar resultados/consumo disponible sin inventarlo.

## Secuencia y verificación

1. Auditar cierre negativo y preservar fuentes/recibos: realizado.
2. Restaurar dependencia local fijada y añadir detección de requisitos antes de ejecutar casos costosos. Verificar negativa temprana y almacenamiento real positivo, manteniendo --pull=never en las pruebas.
3. Aplicar sólo correcciones justificadas tras revisión del comportamiento objetivo. Probar cada grupo con PostgreSQL y navegador/servicios locales reales cuando corresponda; notificar y auditar cada terminal.
4. Reparto de pruebas: ya hay2workers, snapshots y orden por historial. Los tiempos observados por archivo alcanzaron~927s y un caso grande~817s; no son nuevas medidas de producto. Separar preparación repetida y carga independiente sólo con aislamiento demostrado. Comparar configuraciones de pytest sin modificar recursos ni topología del benchmark del producto.
5. Ejecutar común afectado tras focales; repetir regresión amplia sólo cuando las causas anteriores y las incertidumbres que lo exijan estén resueltas. Una batería rápida no sustituye la aceptación completa.

Antes de medir o congelar una correctiva, actualizar el grafo de sus fuentes y documentación; no declarar actualización semántica exhaustiva desde AST. Datos sintéticos, no proveedores/publicación/gasto. B00residual y B07–B17 siguen pendientes; seis puntos cerrados pertenecen a sus cortes locales y deben revisarse si se demuestra una regresión que contradiga un criterio aceptado. Corto TCP20RPS sigue FAIL y900s bloqueado.

## Avance de correctivas, corte posterior

- Dependencia RustFS fijada repuesta; preflight temprano verificado con seis unitarias, negativo real de colección y una prueba S3 real positiva. No se declara resueltos por esa prueba todos los52errores originales.
- [Consentimiento119](119-correctivas-consentimiento-beta-20261020.md): payloads vigentes por idioma,34PASS auditados en su corte, sin modificar autorización de producto.
- [Catálogo120](120-vigencia-catalogo-validacion-beta-20261020.md): defecto temporal real reproducido y corregido en submissions.py;52casos únicos cubiertos mediante3nuevos+49reutilizados con igualdad de fuentes y producto auditada. Dos negativos preservados, sin convertirlos en PASS.
- Pendientes: fixtures de historial privado/tarifas y fingerprint, revisiones, dependencias relacionadas, migración histórica, rutas/límites de segunda fase, localización y navegador. Las propuestas readonly deben verificarse focalmente; no repetir todavía la batería amplia. Comparación nueva2vs4workers pendiente, sin porcentaje de aceleración.

La corrección real de catálogo obliga a revalidar la garantía de vigencia nativa vinculada a B02/B06;120 la comprueba en su alcance local con contexto y guardas privadas. Las actas anteriores conservan su corte; queda pendiente integrar los grupos restantes en la verificación común y global. No nueva aceptación beta ni de capacidad.


## Cierre focal y candidata común pendiente

Historial121:48PASS auditados. Rutas122:48PASS auditados. Revisiones readonly posteriores motivaron dos refuerzos de cobertura, no un defecto de producto demostrado: drenaje migratorio y exigencia independiente de cursor preparado tras revocación. Almacenamiento123:199PASS auditados (174+24reforzados+1diagnóstico), todos los52erroresRustFS originales pasan y no quedan contenedores propios. Los terminales se conservan por corte; no sumarlos como una única ejecución. El único defecto de producto corregido en estos grupos sigue siendo vigencia temporal del catálogo120.

Siguiente124:común afectado40archivos/363casos previstos sobre candidata única, incluyendo los94nodeids negativos originales, y comparación secuencial2vs4workers con mismas fuentes/selección/historial. La aceleración nueva sigue sin medir. Regresión amplia y capacidad aún pendientes; corto TCP sigueFAIL.


## Común actual auditado y siguiente regresión

124:363PASS/0FAIL/0ERROR/0SKIP con2workers y otros mismos363con4, mismas fuentes/selección/historial; todos94negativos originales pasan en cada brazo, no sólo coincidencia de totales. Producto622idéntico, recursos/temporales/PID/Telegram verificados. Proceso pytest624,180→349,882s:43,95%menos observado en un par; no extrapolación causal ni beta global. RechazoCLI previo preservado/corregido antes de ejecutar.

Las causas focales de38FAIL/56ERROR han sido verificadas en una candidata común. Es necesario125, regresión funcional amplia con4workers y las mismas exclusiones oficiales/carril capacidad separado; no repetir cargas limpiasTCP que siguenFAIL. Previsión3460nodeids (3454anteriores+6unitariaspreflight), colección y terminal pendientes. Los122SKIP históricos deben revisarse y conservarse como omisiones, nunca PASS.


## Regresión125 negativa y residual126

195459-bacfc549 auditado:3331PASSúnicos+4subreportes/7FAIL/0ERRORpreparación/122SKIP,3460nodeids exactos, fuentes/limpieza/Telegram confirmados. Todos94negativos originales y362comunes ordinarios pasan. Los siete nuevos fallos son expectativas de mensaje sobre historial rectificado, en un único archivo. Mantener el rechazo histórico antes del contrato romántico; no cambiar producto para volver a la prioridad vieja.126prepara corrección de una expectativa y archivo completo15casos, con verificaciones posteriores al punto donde fallaba. Sin aceptación beta/capacidad ni nueva batería amplia hasta justificar necesidad.


Correctiva126 concluida:212138-85190e87,15PASS auditados; cobertura conciliada3338PASSúnicos/122SKIP por15nuevos+3445reutilizados con prueba SHA/AST/dependencias. Véanse126 y sus dos evidencias. Se conservan negativos125 y primer focal; no aceptación de capacidad/beta.
