# Regresión común actual interrumpida — 2026-10-16

Fuente `96ae5bd285e00cb5afb348f41c6e5c35d8c77656`, ejecución `20261016-162002-472b6009`, selección prevista 3626 casos. Resultado **ERROR**, no aceptación N3/CR09.

El journal systemd acredita `oom-kill` a las 18:07:08 UTC; unidad terminal con salida 1, MainPID 0 y ControlGroup vacío. MemoryPeak 3758751744 bytes bajo MemoryMax 3584 MiB, swap 0. El runner recibió señal 15 durante pytest tras 6408,29 segundos. No se produjo JUnit final.

El journal por fases conserva 3427 casos con setup/call/teardown PASS, ocho casos fallidos y 67 omitidos. Otros tres sólo registraron setup PASS; 121 no aparecen. No sumar los incompletos ni omitidos como aprobados. Fuentes, ausencia del temporal, identidad ausente de runner/hijo y ausencia de contenedores PG/Redis declarados comprobadas independientemente antes de editar. Detalles, errores originales, omisiones y huellas de artefactos en [recibo JSON](cr09-common-current-regression-original-20261016.json).

Los ocho fallos: un guard de mutación de archivo, cinco paridades/liberación de RateForm y dos aserciones SQL de membership dirty. Los tres casos en curso eran capacity_chain_explain, capacity_chain_inline_http y rights_access_scope_inventory[True]. La concurrencia de estos casos no demuestra cuál agotó memoria; no atribuirlo al producto ni al hardware sin diagnóstico.

Inspección inicial posterior al cierre: Django BaseInlineFormSet.__init__ añade la FK a self.form._meta.fields mediante append si la lista es mutable. RateForm.Meta.fields es una lista y rate_valid la utiliza como contrato de valores. Esto concuerda con el campo revision adicional mostrado por el fallo, pero requiere control aislado antes de corregir. El guard de archivo contrasta tamaño, inode y timestamps; el test sobrescribe bytes de igual longitud, por lo que aún debe comprobarse la resolución temporal observada. Las pruebas membership compararon cuerpos y conteos antes de fallar en una aserción global de forma SQL; no confundir esto con una causa ya demostrada.

Siguiente trabajo: controles separados de cada mecanismo; preservar selección completa y límites, diagnosticar consumo antes de reanudar casos pendientes. No repetir ciegamente la batería ni aumentar memoria. Carga contractual limpia anterior sigue INVALID por demora máxima del generador; los cortos favorables no cierran ese criterio.
