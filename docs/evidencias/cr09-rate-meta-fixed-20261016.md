# Campos de tarifas estables tras crear un formset

El control aislado en artifacts/cr09-rate-meta-control-20261016/result.json confirma que instanciar RateFormSet añadía revision a RateForm.Meta.fields, compartida por identidad con _meta.fields. rate_valid y submissions leen esa declaración como campos primitivos. La regresión común original conserva los cinco fallos posteriores a esa contaminación.

La declaración ahora es una tupla: Django crea una lista propia para el formset al añadir la FK y no modifica el contrato de RateForm. Los cinco casos de paridad/liberación existentes instancian primero RateFormSet y comprueban los cuatro campos exactos, validación nativa, memoización y liberación sin GC. Incluye excepción y controles de contexto público y envíos.

Ejecución propia 20261016-181006-15ef7810: **26 PASS, 0 FAIL, 0 SKIP**, 117,88 segundos de pytest, unidad terminal0. Fuentes congeladas, ausencia de temporal, identidades runner/hijo y contenedores declarados verificadas independientemente. Misma cuota3584MiB/swap0, PostgreSQL real, native-sealed, un worker. Evidencia completa en artifacts/local-ci/20261016-181006-15ef7810.

No nueva métrica HTTP ni aceptación N3/CR09. Siguen pendientes el guard de mutación, dos aserciones SQL, diagnóstico de memoria y casos no completados. La corrección cambia producto: reconciliar sus consumidores y runtime antes de aceptación integrada.
