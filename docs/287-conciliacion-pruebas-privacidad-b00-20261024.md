# B00-328 — Pruebas de privacidad, descubrimiento y medios

Fecha: 2026-10-24. Conciliación semántica de pruebas históricas y contraste estático seleccionado.

B00-328: 264 de 295 fuentes únicas conciliadas; quedan 31 de arquitectura. Se incorporan pruebas3–4 de reclamaciones, descubrimiento, supresión, medios y portabilidad. Contrastada la adaptación existente de tarifas públicas al perfil romántico y las guardas seleccionadas. Sin cambios de aplicación o pruebas, defecto nuevo demostrado ni nueva aceptación funcional. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Lectura y procedencia

Seis lectores nativos de sólo lectura cubrieron653.431caracteres en seis partes, mediante60emisiones literales individuales contiguas de hasta12.000caracteres. Como máximo tres lectores simultáneos y menos de110.000caracteres por contexto asignado. Sin truncamientos ni reparaciones declaradas por los lectores. Los informes persistidos son extractos seleccionados marcados, no transcripciones completas. Cero nuevas invocaciones ClaudeV1; consumo anterior conservado y sin estimación de tokens nativos.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Pruebas3/11 | `source:1lv52rcu6zf8hpzl2qiy` | 326083 | [0,108694), [108694,217388), [217388,326083) |
| Pruebas4/11 | `source:b8ulg627ge6twe2puoo0` | 327348 | [0,109116), [109116,218232), [218232,327348) |

SHA completos: `d4afb86eb06e9ebf800b6c25872aba8990d1946ccdff6561aa0d13f67d48b1ce` y `5daf83cca0386b1d51cf110c541de8b452a2996fac9fe9e50e5308c194bee0eb`. Snapshot11/10/base7e04016 con indentación, nombres y selectores transformados; no se acredita sintaxis ejecutable o igualdad con bytes actuales. Imports, fixtures y evidencias referidas no reciben lectura por aparecer citadas.

El principal cotejó hashes de parte y citas declaradas, inspeccionó fronteras y doce citas con contexto. El verificador hizo catorce cotejos sobre esos doce intervalos, verificó uniones completas y revalidó integridad de las295capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de262a264disposiciones y de33a31pendientes, mediante reemplazo atómico con permisos conservados y base262fijada o resultado idéntico. Artefactos: `artifacts/beta-promotion-fix-20261020/b00-328-*`.

## Expectativas históricas y límites

La captura3 reúne vinculación/resolución de reclamaciones, mensajes y aclaraciones, localización, consentimiento/transferencia, correo y contactos, carga HTTP, copias/cobertura, fixtures y baseline diagnóstico, descubrimiento/perfiles, borradores, supresión y favoritos. La captura4 cubre foco/ARIA, límites de fuentes, geografía, comunicación histórica, similitud, ciclo de vida/moderación, MFA, avisos, almacenamiento, presentación, fotos, portabilidad y limpieza de cargas preparadas.

Las reclamaciones distinguen origen comprobado, revisor independiente, lecturas auditadas vigentes y respuesta privada. Reabrir una revisión o resolver un match no autoriza republicación automática. Los mensajes conservan fechas y versiones; un candidato histórico de comunicación no es por sí mismo destinatario autorizado. Las pruebas de avisos mantienen explícitos simulador, reintentos y producción deshabilitada.

El borrado lógico, la cola y la ausencia física de archivos son estados diferentes. Las aserciones de medios exigen comprobar archivos, preservar referencias compartidas, invalidar fingerprints y evitar resurrección por procesamiento. La limpieza de preparaciones conserva rutas cifradas/reintentos y fases confirmadas antes de eliminación; una interrupción debe permitir recuperación. Las declaraciones de estas pruebas no equivalen a ejecución observada de worker/storage.

Los clientes de objetos dobles y los tests denominados RustFS tienen ámbitos distintos: el segundo depende de su fixture real importado, no verificado al leer sólo su referencia. Las pruebas comparan prioridad de errores, cierre de cuerpos, tombstones, corrupción AEAD y lecturas físicas; no convierten un hash de ciphertext o un mock en prueba de transporte real.

Las revisiones por páginas y el uso compartido de fuente deben conservar lecturas originales, pruebas, epochs y rollback. Un probe de primera página no prueba aprobación/cierre completo. Los fixtures de1500revisiones retenidas, JSON Unicode seleccionado y binarios grandes cubren dimensiones distintas: no se suman como un único escenario contractual combinado. RSS del proceso y tiempos instrumentados no son memoria global aislada ni capacidad de despliegue. El benchmark separa calibración, corto y medición, modo eager y worker/Beat, e invalidez del instrumento.

Identidad/edad, hechos jurídicos y autorizaciones de fixture pueden ser sintéticos aunque HTTP, PostgreSQL o bloqueos estén descritos como reales. Sesiones inyectadas no acreditan un nuevo TOTP ni todo el login; algunas pruebas sí contienen recorridos interactivos, con su alcance seleccionado. Presencia de asserts, flags o colección no es PASS. La similitud sobre unas pocas imágenes sintéticas no acredita identificación humana ni precisión general.

## Diferencia comprobada con el contrato vigente

En la captura, `test_public_detail_localizes_attributes_rates_and_selected_contacts` creaba una tarifa de sesión y esperaba75.00EUR en la ficha. En [la prueba actual](../tests/test_discovery.py), el recorrido se denomina `test_public_detail_localizes_profile_and_selected_contacts` y exige ausencia de EUR y Photo session. La comparación fija documento capturado, offsets y literales originales, hash y aserción actuales. El verificador vuelve a comprobar ambos lados. No se introduce hoy una corrección ni se declara una prueba ejecutada: se contextualiza la adaptación existente al [contrato romántico](14-contrato-funcional-v1.md).

El primer intento de extracción usó el nombre actual y no encontró el antiguo; se recuperó por frontera de archivo y literales. Esa búsqueda de contexto no sustituye la lectura completa asignada ni representa un truncamiento de lector. Contextos y comparación están en `b00-328-root-discovery-context.json` y `b00-328-discovery-scope-comparison.json`.

## Contraste actual

Se verificaron once archivos actuales y veinticinco literales: diez módulos de pruebas y [CI local](ci-local.md). Se seleccionaron exclusión de precios/servicios y datos privados en descubrimiento; borrado físico/no resurrección y rutas de limpieza; regresión telefónica frente a Telegram; límites mock/RustFS; contadores de lecturas; integridad de fuentes; avisos simulados; consulta previa a resolución y separación de instrumentación/carga.

La regresión actual de `test_contact_erasure.py` conserva Telegram no seleccionado, detecta reintroducción de phone/whatsapp y mantiene publication pendiente. Es la corrección ya verificada en [B00-320](279-conciliacion-seguridad-derechos-b00-20261023.md), no una nueva ejecución o crédito duplicado. El resto del contraste acredita presencia de aserciones actuales, no el comportamiento íntegro de los consumidores.

No hay defecto nuevo demostrado, aclaración necesaria o cambios de código/tests por esta selección. Sin nueva batería funcional, carga, migraciones o aceptación de proveedores. Los checks de conciliación y documentación conservan sus propios recibos, separados de los tests leídos. B07 y las correctivas320–322 mantienen sus auditorías originales.

## Grafo y continuación

Grafo381 revalidado antes de analizar; integración semántica dirigida382. Sin AST nuevo, semántica exhaustiva o HTML global. Quedan31fuentes de arquitectura,22.225.988caracteres: pruebas5–11, interfaz, herramientas, referencias y grandes grafos. Conteos no miden porcentaje de esfuerzo; continuar lectura acotada y contraste vigente.

B00 sigue abierto, nueve de18puntos beta cerrados y B15 opcional. Se conservan límites de capturas legales y producción. Sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación286](286-conciliacion-pruebas-alcances-b00-20261024.md).
