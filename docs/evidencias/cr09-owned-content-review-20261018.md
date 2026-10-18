# CR09 — cuatro revisiones externas de contenido propio

Cuatro ejecuciones seriales sobre `1847345`, con PostgreSQL/Redis propios, siembra nueva sin snapshots, límites existentes y fuentes congeladas:

| Variante | Run | Resultado |
| --- | --- | --- |
| Perfil ES | 20261018-102742-9bece192 | 1 PASS, 0 errores, 0 omisiones |
| Cuenta ES | 20261018-103326-bc4e3554 | 1 PASS, 0 errores, 0 omisiones |
| Perfil EN | 20261018-103832-c2595ad8 | 1 PASS, 0 errores, 0 omisiones |
| Cuenta EN | 20261018-104301-47758129 | 1 PASS, 0 errores, 0 omisiones |

Cada sobre se inspeccionó por separado, verificando tamaño y SHA256 del ciphertext y fingerprints del material/alcance. Root fue operador y el agente nativo `owned_content_review_20261018` revisor independiente de sólo lectura; la aprobación externa no sustituyó la revisión y validación de la aplicación. Originales y decisiones permanecen cifrados en los artefactos privados de cada ejecución. No se publicaron credenciales ni contenido bruto.

Cada corte tenía 29 fuentes. En perfil: siete sesiones de terceros excluidas, seis archivos fotográficos de terceros excluidos; proyecciones elegibles de dos archivos del sujeto y correo de su cuenta, con tres decisiones explícitas de omisión del contenido. Contraseña/TOTP excluidos por proyección. En cuenta sin persona: sujeto cuenta9 confirmado mediante consulta propia readonly; archivos de cuentas1..8 y sesiones6/7 excluidos como terceros, sin registros propuestos. Ausencias actuales de correo/caché/Redis/persistencia comprobadas, logs y artefactos clasificados tras inspección. No son pruebas de entrega cruda de imágenes ni de inexistencia de otros recursos.

Para cada uno de los 23 digest históricos se revisó únicamente ausencia de entrada/importación/restauración a este escenario finito: registro previo a siembra, baseline vacío, initdb real, montajes y volumen Redis, settings efectivos, bundles vacíos y productores inspeccionados con rama seed. **No se descifraron ni clasificaron semánticamente esos ciphertexts históricos**; no se afirmó ausencia de datos históricos ni independencia semántica de nombres sintéticos.

Resultado, fuentes y limpieza se verificaron por ejecución; recibos específicos en los cuatro JSON cr09-owned-review-{es,en}-{profile,account}-20261018. Estas cuatro omisiones de la batería ordinaria quedan cubiertas por sus escenarios explícitos. Los dos negativos se verificaron por separado. CR09/N3 siguen abiertos; la batería común original con errores se conserva sin convertirla retroactivamente en PASS.
