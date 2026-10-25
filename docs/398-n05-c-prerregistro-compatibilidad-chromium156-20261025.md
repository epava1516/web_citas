# N05C — contraste por cambio de navegador

Alfa,25deoctubrede2026,5/13; N05 abierto. No hay cambio de aplicación ni candidato de optimización.

## Evidencia nueva que justifica el contraste

N05B397 ha terminado en20261025-213715-0bcfabdc con4PASS/0FAIL/ERROR/SKIP,133,659sJUnit y1748huellas intactas. Mide entrega privada y sondeos en Chromium **156.0.8078.47**. La galería original306 registra Chromium **155**; los testigos anteriores de teclado no aportan una identidad156 verificable en sus propiedades. Esta diferencia de dependencia es relevante para heurísticas de imágenes diferidas, recursos y foco; no se presume equivalencia sólo por identidad de fuentes.

Las fuentes públicas/plantillas/JS siguen idénticas a B16 y el bloque de transformación de imagen es AST idéntico al de la galería anterior. Se preservan los valores históricos8→1imágenes iniciales y135824→11110bytes, sin presentarlos todavía como una ejecución actual156. La comprobación adicional no es una repetición por frescura documental.

## Selección exacta y oráculos

Reutilizar **sin modificar** tests/test_gallery_delivery_diagnostic.py (dos casos móvil/escritorio, ES/EN dentro de cada caso) y tests/test_form_error_focus.py (cuatro casos: público/privado×ES/EN, viewports320/390/1280). Seis casos seriales en total, PostgreSQL/Redis propios, Chromium/live_server/archivos reales y broker aislado. No relanzar toda la matriz de navegador.

Galería: misma fixture de ocho fotos, biografía de80líneas, dimensiones, orden y hashes locales; primera imagen inmediata, resto según atributo lazy existente; carga completa al recorrerlas, contenidos WebP idénticos a los archivos y404tras pausa aun con condicionales. Registrar versión real, peticiones/bytes iniciales y completos, CSS/JS entregados y comparación exacta con los datos originales. No variar biografía, tamaños, viewport o posición de galería para conseguir un conteo favorable. Si156 cambia su heurística, registrar el resultado y su límite antes de decidir; no inventar una mejora causal de código.

Teclado: originales de foco visible de errores, Enter/Tab, skip-link, asociación aria-invalid/describedby, ausencia de desbordamiento y de persistencia indebida de contraseña/razón. Público y privado en ES/EN, tres viewports por caso. No alterar validación, autofocus, seguridad de sesión/MFA/CSRF ni el helper síncrono de Django para facilitar PASS. No equivale a una certificación universal de accesibilidad de129plantillas.

## Medidas y ejecución

La galería mide cuerpos decodificados y dimensiones, no tiempo/LCP/bytes de red comprimida. Las propiedades de teclado son oráculos de interacción, no latencia. Mantener datos/técnicas previos; comparar con declaraciones de156 y conservar la historia155. La red es HTTP local sin emulación de Internet; no se acredita proxy o proveedor. RSS y recursos del runner se declaran sin confundir Python con la suma de hijos Chromium.

Comando previsto: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_gallery_delivery_diagnostic.py --test tests/test_form_error_focus.py`.

Antes: revalidar el corte actual, integración semántica focal de esta ficha/seguimiento y congelación de producto/dependencias/instrumentos. Después: seis casos completos sin FAIL/ERROR/SKIP, propiedades y JUnit originales, huellas intactas, limpieza de recursos propios y recibo Telegram terminal sent. Cualquier fallo se preserva y se atribuye; no se mezclan los4PASS de B y los seis de C como si fueran una sola batería integrada.

La primera referencia N05B213009 conserva3PASS/1FAIL de observación antes de subir en EN; la taxonomía genérica no permite confirmar su causa exacta. El observador corregido sincroniza la navegación y registra categorías sin exponer mensajes/cookies. Su4PASS posterior no convierte el original en PASS. La aplicación no cambió.

N05 necesita todavía el acta final por137IDs, muestreo justificado y tabla temporal/bytes antes-después con equivalencia explícita. Sin optimización marginal, cambio de formato, proveedor o apertura; el proyecto sigue en alfa.
