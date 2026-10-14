# CR09: correctiva del bloque 3

La regresión de 9b0353fc conserva 2 fallos de navegador y 22 errores de preparación de RustFS. Los bloques 1, 2 y 4 pasaron con integridad y limpieza verificadas; esto no declara CR09/N3.

Las dos pruebas de catálogo localizado pasaron aisladas sin cambios (20261014-080817-da45ec4d). Se añade una espera por la desaparición del botón de publicación antes de la recarga real, manteniendo la comprobación posterior y los invariantes ORM. La correctiva pasó en ES/EN (20261014-081005-7f9f024b). La superposición de navegación es una hipótesis compatible, no una causa demostrada por la reproducción aislada.

La imagen RustFS exacta ausente fue restaurada sin cambios de aplicación. Los tres archivos afectados pasaron: 55 pruebas, cero fallos, errores u omisiones (20261014-081149-bb907f5a). Los 22 errores históricos se preservan. Los recibos JSON correspondientes conservan versión, integridad, resultados y limpieza.

Queda repetir el bloque 3 completo y reconciliar la correspondencia de versiones, omisiones y criterios antes de aceptar CR09. Los resultados aislados no sustituyen ese gate.
