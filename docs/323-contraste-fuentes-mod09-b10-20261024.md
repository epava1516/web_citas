# B10 — Contraste actual de fuentes respecto a MOD-09

Se inicia la resolución acordada en [320](320-acuerdos-alcance-b10-prioridades-20261024.md) comparando el corte medido c92fe649a5a2c9e7365118f87fcaa710701857bb con las fuentes actuales. No se ejecuta todavía una nueva carga ni se afirma mejora temporal.

La [comparación AST y hashes](evidencias/b10-mod09-current-source-delta-20261024.json) cubre nueve módulos seleccionados de exportación, respuesta, privacidad, criptografía y similitud; no es un censo transitivo completo.

Hallazgos concretos:

- En rights_exports, la única función superior modificada es source_copy: incorpora content_contract y show_trans_label en cada revisión. Las cuatro clases de formulario se trasladaron a rights_copy_forms con compatibilidad ya verificada en B11. No hay un cambio directo de los algoritmos de generación en ese módulo que permita atribuirles una aceleración.
- Cambiaron respond, fingerprint, context y project en módulos de respuesta y privacidad. La identidad del exportador no basta para reutilizar sin contraste la medida antigua: sus dependencias y el contenido de la copia han variado.
- Cambiaron cipher y digest; debe examinarse su configuración y coste pertinente antes de comparar mediciones. No se relaja criptografía para cumplir un objetivo temporal.
- detect_matches sustituyó JOIN/DISTINCT por EXISTS para seleccionar blobs admisibles. La mejora pertenece al detector y no demuestra una exportación más rápida. ingest añade la guardia del contrato romántico.

La inspección del diff precisa esas dependencias: context añade una reautorización fresca después de un posible bloqueo; respond corrige el replay de representación resuelta, una rama distinta de la exportación ordinaria; fingerprint y project incorporan la clave HMAC de dominio y las claves de cifrado de retorno; cipher usa el constructor con rotación. Son garantías y compatibilidad de seguridad, no optimizaciones de latencia demostradas. No retirar la reautorización ni los controles de claves para mejorar tiempos.

Por tanto, es plausible que existan diferencias de rendimiento, pero no hay evidencia de una mejora global MOD-09. La siguiente decisión debe distinguir el detector de imágenes del recorrido de exportación, inspeccionar las dependencias modificadas y seleccionar una medición vigente comparable. Las mediciones pequeñas actuales de B10 no sustituyen el escenario de 1500 revisiones, dos casos concurrentes y sus cuerpos originales.

Se preservan la aceptación provisional MOD-09, los objetivos originales y el FAIL histórico. No se modifica el criterio ni se repite la carga para maquillar el resultado. B10 permanece abierto en este contrato; la justificación del extremo de similitud y la disposición final de su deuda siguen pendientes.
