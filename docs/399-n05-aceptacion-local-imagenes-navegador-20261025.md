# N05 — aceptación local de imágenes y navegador

25 de octubre de2026. Alfa. N05 queda verificado localmente en los escenarios seleccionados, **sin cambio de aplicación**. N00/N01/N03/N04/N05/N06 aceptados: **6/13 bloques obligatorios**. Base d6580c6 y huellas completas en las congelaciones. No se acredita apertura, proveedor o capacidad universal.

## Requisitos y disposición por unidad

Contrato340, criterios354/S05 y roadmap341/N05: bytes, calidad, caché, entrega pública/privada, imágenes diferidas, recursos, validación, teclado/idiomas y sondeos. [Prerregistro397](397-n05-prerregistro-entrega-privada-sondeos-20261025.md) y [contraste398](398-n05-c-prerregistro-compatibilidad-chromium156-20261025.md). Codex verificó137IDs del censo: cinco rutas,129plantillas y tres JS;138fuentes directas idénticas a B16. No son137funciones independientes ni137PASS de navegador. Evidencias: [matriz por ID](evidencias/n05-final-action-matrix-20261025.json), [verificación de aceptación](evidencias/n05-acceptance-verification-20261025.json), [entrega y sondeos](evidencias/n05-b-reference-audit-20261025.json) y [compatibilidad156](evidencias/n05-c-compatibility-audit-20261025.json).

La matriz final conserva cada ID, origen, grupo, autoridad, fuente y propietarios. El muestreo cubre elementos compartidos y recorridos seleccionados; no asigna latencia individual a cada plantilla. La revisión nativa aportó152citas contrastadas con sus snapshots y seis citas del observador corregido; la aceptación es decisión independiente de Codex con fuentes/JUnit/propiedades.

| Unidades | Decisión y evidencia | Límite / dueño conservado |
| --- | --- | --- |
| R_public_photo | Conservar código. Galería actual Chromium156: cuatro contextos ES/EN móvil/escritorio, hashes/dimensiones/orden exactos y404tras pausa | No todos los tamaños/colas ni LCP; N04 conserva descubrimiento |
| R_private_photo | Dos casos actuales ES/EN: subir, preview, recargar, seis GET autenticados, condicional200, anónimo302 y retirada404 | Móvil y gestor titular; proceso eager explícito, no broker/worker. N07 conserva gestión del medio |
| R_match_image / R_moderation_photo | Fuentes y guards conservados, testigos previos de rol/MFA/COI donde corresponden | No nuevo tiempo aislado por cada rol. N07 conservado |
| R_photo_reuse_image | Fuente y testigos de permiso/MFA/actor, versión y recibo de lectura conservados | No tiempo individual de autorización; N09 conserva dominio/retención. La imagen sigue siendo el derivado WebP |
|129plantillas | Unidades por grupo: shell1, cuenta/panel24, comercial6, descubrimiento/galería3, edición/moderación14, sondeos3, derechos/operación78 | Representantes de UI compartida y fuentes idénticas; no afirmar129renderizados nuevos. N06/N07/N08/N09 conservan su comportamiento propio |
| form-errors.js | Fuente y bytes intactos; seis casos actuales incluyen cuatro de foco público/privado ES/EN y18observaciones | Foco visible, Enter/Tab, asociaciones y estado; no certificación universal WCAG |
| geography.js / search-geography.js | Fuentes/eventos DOM estándar intactos; testigos previos de dependencias geográficas conservados | Sin modificación de estos scripts o nuevo coste atribuido; no se ejecuta toda combinación DOM en156 ni se promete compatibilidad universal |

Las cinco rutas sirven derivado/FileResponse/WebP, no un original: el muestreo de cuerpos y transporte público/privado representa esa etapa compartida. No sustituye las autorizaciones distintas de moderación, pares y reintroducción ni adjudica el tiempo del gestor a sus guards. Los testigos del contrato anterior permanecen aceptados con sus límites, sin reabrirlos ni convertir inspección de fuente en nueva ejecución.

Puentes de fixtures: el bloque AST de lectura/decodificación/thumbnail/WebP es idéntico al de galería; N03 delimita cambios de process/detect_matches/similitud/recovery y sus regresiones. Siete imágenes de galería son fixtures ready explícitas; la primera usa el pipeline nativo. Publication_signals coincide con B16 aunque difiera del corte de galería. El guard posterior de exportación MOD09 no es byteidéntico al antiguo: N05 no reclama nueva generación/worker y usa transiciones controladas para medir UI. Se conservan esos límites.

## Resultado actual de entrega privada y sondeos

RunB `20261025-213715-0bcfabdc`: **4PASS/0FAIL/ERROR/SKIP**,133,659sJUnit,1748huellas intactas. PostgreSQL/Redis/archivos/Chromium reales, HTTP local sin emulación de red. No hay cambio de código de aplicación.

Privado: imagen WebP de640×480, sinEXIF,9344bytes y hashes idénticos entre ES/EN; cuerpo servido igual al derivado almacenado y distinto del original. Dos respuestas visibles inicial/recarga, seis API y un condicional por idioma, con private/no-store/nosniff. Anónimo sin seguir redirecciones302sin imagen; nueva petición tras retirada404sin imagen. La retirada no se confunde con purga inmediata de los archivos retenidos.

| Idioma | Subida→preview observado (s) | Recarga→preview (s) | Primer API (ms) | Mediana5API (rango ms) | Bytes/cuerpo |
| --- | ---: | ---: | ---: | ---: | ---: |
| es | 1.376 | 0.342 | 212.760 | 101.944 (96.217–139.426) | 9344 |
| en | 1.152 | 0.261 | 185.797 | 141.820 (120.377–148.220) | 9344 |

Tiempos observados del cliente, incluyendo Playwright/lectura del cuerpo donde corresponde. La subida incluye procesamiento eager de fixture, no latencia de cola ni backend aislado. Primera no es caché OS fría. RSS Python high-water máximo351404KiB; no suma la memoria de hijos Chromium.

Sondeos: cuatro XHR del trabajo por idioma: queued×2→running→rejected. Las transiciones usan claim/finish_attempt del dominio y dispatch sustituido de fixture; **no** son evidencia de ejecución de worker, generación o causa automática de revocación. Intervalos ES3,085–3,154s; EN3,068–3,134s, contra atributo nativo every3s, sin imponer un SLO3,000s. Máximo de un XHR del trabajo simultáneo. Tras terminal,6,506s sin peticiones nuevas; contexto sin JavaScript legible y cero sondeos. Sin export/download nuevo.

| Idioma | Solicitud | Estado | Duración observada ms | Cuerpo decodificado bytes |
| --- | ---: | --- | ---: | ---: |
| es | 1 | queued | 110.353 | 456 |
| es | 2 | queued | 57.091 | 456 |
| es | 3 | running | 133.068 | 455 |
| es | 4 | rejected | 62.565 | 185 |
| en | 1 | queued | 111.655 | 450 |
| en | 2 | queued | 85.708 | 450 |
| en | 3 | running | 44.962 | 456 |
| en | 4 | rejected | 40.345 | 170 |

No mezclar duraciones de estados distintos para inferir rendimiento de un estado o p95. Recursos200observados y SHA iguales a archivos actuales: app.css12412bytes, form-errors.js962bytes yHTMX52182bytes en la página de sondeos. Identidad de encoding observada; bytes decodificados, no tráfico comprimido. El observador distingue304sin cuerpo nuevo, pero esas observaciones actuales de recursos fueron200. No cargar el peso de HTMX a fichas que no lo usan.

## Contraste del navegador actual

Se encontró una dependencia relevante: la galería306 registraba Chromium155; los testigos antiguos de foco no fijaban identidad156 verificable. Por ello se ejecutaron **sin modificar** seis casos representativos, no toda QA. RunC `20261025-215001-a15f20f3`: **6PASS/0FAIL/ERROR/SKIP**,110,320sJUnit y1748huellas intactas. Chromium156.0.8078.47 confirmado, mismo ejecutable por defecto antes/después.

Galería: ES/EN×390×844/1280×800, una foto inicial11110bytes y ocho completas135824bytes, mismos ocho hashes y dimensiones que el testigo155. Primera inmediata, siete lazy;404tras pausa con condicionales. Sin cambiar biografía, imágenes o heurística para favorecer el resultado.

Foco: cuatro casos público/privado×ES/EN, viewports320/390/1280 y18observaciones con errores enfocados. Enter/Tab, skip-link, outline visible, aria-invalid/describedby, no desbordamiento y no persistencia indebida de contraseña/razón comprobados. El caso público original desactiva la validación HTML del formulario para observar el rechazo del servidor; no se presenta como prueba de todos los validadores del navegador. No se modifica el comportamiento del producto.

## Antes y después de N05

La reducción de galería procede de la optimización anterior306, conservada actualmente. N05 añade referencias sin candidato de aplicación. Para tiempos sin base comparable no se inventa un porcentaje.

| Acción / medida | Antes disponible | Después / referencia actual | Diferencia y límite |
| --- | ---: | ---: | --- |
| Galería, imágenes iniciales |B09antes:8|B09después yN05C156:1|−7/−87,5%, optimización anterior confirmada, cuatro contextos |
| Galería, bytes iniciales decodificados |135824|11110|−124714/−91,82%, misma fixture y cuerpos; no ahorro total si se recorren todas |
| Galería completa, cuerpos/dimensiones |8/135824bytes|8/135824bytes y hashes exactos|Sin cambio de calidad/codec introducido por N05 |
| Entrega privada ES, mediana5API |Sin base temporal equivalente|101,944ms|No evaluable como mejora; cliente+lectura,9344bytes |
| Entrega privada EN, mediana5API |Sin base temporal equivalente|141,820ms|No evaluable; condiciones/idioma no son versiones de candidato |
| Subida→preview ES/EN |Testigo funcional, sin tiempo aislado|1,376/1,152s|No evaluable; eager explícito, no cola real |
| Recarga→preview ES/EN |Sin base temporal equivalente|0,342/0,261s|No evaluable; nueva observación del cliente |
| Sondeos de estado |Funcional y every3s, sin intervalos aislados|3,068–3,154s; cuatro XHR por idioma|Referencia actual; cero nuevos durante6,506s terminales, no mejora causal |
| CSS/form-errors en contexto representado |12412/962bytes|12412/962bytes|Iguales; HTMX sólo donde realmente se entrega |
| Teclado/estado/privacidad |Testigos anteriores con límites|Cuatro casos de foco156 y actuales de entrega/sondeos|Sin latencia individual ni certificación global inventadas |

Los133,659s de B y110,320s de C son QA de **ejecuciones distintas**; no se suman como una batería integrada de diez casos ni como latencia de la aplicación. La tabla conserva medidas originales y las nuevas referencias, sin comparación causal entre herramientas, estados o versiones de navegador distintas.

## Fallos conservados, auditoría y deuda

PrimeraB `20261025-213009-1fb88e99`:3PASS/1FAIL,128,601sJUnit. PrivadoEN falló antes de subir, con taxonomía genérica Error/Error del observador tras navegación. Su causa exacta no se pudo confirmar; no se afirma un defecto de aplicación. Se preservó el original, se sincronizó la navegación con networkidle/expect_navigation y se añadió clasificación por etapa sin mensajes privados. Todos los errores siguen invalidando la muestra; guardas/datos/HTTP/bytes/calendario no se sustituyeron. El4PASS posterior no convierte el original en PASS. Los errores originales históricos306 también permanecen separados.

Codex comprobó fuentes,152citas del inventario y seis del observador corregido,137IDs, JUnit/propiedades actuales y originales seleccionados. Uno de los archivos antiguos tiene tres fallos ajenos a los37casos seleccionados: no es un archivo global verde. Auditorías de B/C confirman recursos etiquetados y temporales propios ausentes y Telegram terminal sent. Browser/contextos/hilos se cierran en los finales de los casos aprobados; no se afirma un censo global de procesos ajenos.

Decisión: conservar aplicación y costes observados. No hay candidato justificado que requiera cambiar formato, caché, JS o permisos; tiempos aceptables en alfa, sin optimización marginal forzada. Persisten límites de muestra, loopback, cliente/instrumentación, ausencia de proxy/proveedor/Internet/LCP/p95 y de certificación universal. Cada ID tiene disposición trazable; no se ocultan pendientes obligatorios de N05 con un diferimiento genérico.

N07 mantiene medios/publicación/lifecycle, N09 dominio de derechos/retención y N11 candidata integrada. N02/MOD09 conserva su diferimiento expreso al final y N12–N14 sus condiciones. No se abre beta ni producción. **Siguiente: N07**, porque N06 ya quedó aceptado por377.
