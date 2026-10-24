# Vigencia del catálogo durante validación nativa

Fecha:2026-10-20. Estado: correctiva verificada en alcance local con52casos únicos cubiertos; sin aceptación beta.

El contrato romántico valida categoría y ausencia de servicios/tarifas antes de construir DetailsForm. La prueba histórica accedía a initial.categories/services, retirados del formulario público, y fallaba antes de comprobar su garantía temporal. Se conserva esa garantía mediante mutación explícita después de inicializar el formulario: desactivar la categoría vigente o añadir una relación de servicio prohibida. No se reintroducen campos profesionales en el panel.

Se modifica sólo tests/test_native_submission_relation_reads.py; el producto permanece intacto en esta primera reproducción. PostgreSQL obligatorio. El primer caso mantiene exactamente una lectura por cada pertenencia categories/services/travel_areas; los otros dos exigen rechazo vigente tras mutación. Una reproducción negativa se preservará antes de corregir, sin convertirla en aceptación funcional.

Si se confirma, revisar orden de validate_profile_contract frente a guardas privadas e inicialización de campos. Conservar exclusión de preparación rights-stage, historial rectificado y revisión privada; evitar consultas duplicadas por perfil o lecturas fuera del snapshot del contexto. Verificar nativo/contexto/publicación y pruebas afectadas antes de aceptar. No capacidad, beta ni apertura; corto TCP20RPS sigue FAIL.

## Reproducción negativa y candidata

182919-e96bbda9:1PASS/2FAIL/0ERROR/0SKIP en56,03s. Ambas mutaciones terminaron DID NOT RAISE ValidationError; el contador de pertenencias pasó. Auditoría beta-catalog-reproduction-negative-audit-20261020.json confirma fuentes congeladas, producto idéntico a182339, limpieza y recibo1792521046254711986-2067687 sent. Se conserva el negativo; PASS de auditoría no es aceptación funcional.

Candidata: mover una única llamada validate_profile_contract a después de DetailsForm.is_valid, antes de contactos. Así la validación nativa observa catálogo/pertenencias vigentes tras inicializar campos, sin duplicar lecturas; PublicationContext conserva su snapshot de solicitud. Las guardas rights-stage, historial rectificado y revisión privada preceden esa llamada, conservando sus rechazos específicos. No se modifica su autorización ni se publica preparación privada.

Focal prevista: native_submission_relation_reads, photo_disposition_authority, rectification_uploads, beta_profile_contract, public_validation_context, publication_pending_batch y submissions completos; PostgreSQL/Redis/Chromium reales locales, dos workers, snapshots/broker aislados. Resultado pendiente, no aceptación común ni global.

## Focal y correctiva del instrumento

183249-592bd6b5:51PASS/1FAIL/0ERROR/0SKIP en160,64s. El rechazo esperado de ambos cambios de catálogo ocurrió; el caso services falló después por observed=[True,True] frente a[True]. La escritura de pertenencia puede construir otro DetailsForm durante refresco de publicación; el hook instrumentaba también ese lector. Auditoría beta-catalog-focal-instrument-negative-audit-20261020.json conserva fuentes congeladas, único delta de producto submissions.py, limpieza y recibo1792521360482456893-2097895 sent. No declarar ese run PASS.

Se limita la mutación a self.instance is revision, objeto exacto de la llamada nativa bajo prueba; se mantiene el rechazo ValidationError y observed==[True]. Producto idéntico a183249. Repetir native_submission_relation_reads completo (tres casos) y reutilizar los seis archivos restantes sólo tras comprobar igualdad exacta de sus fuentes y622fuentes de producto, selección, terminal y ausencia de SKIP. Esta reutilización no convierte el negativo anterior en PASS ni sustituye regresión amplia.

## Cierre local de la correctiva

183847-cb56f54c:3PASS/0FAIL/0ERROR/0SKIP en54,81s, archivo completo con hook acotado. Auditoría beta-catalog-three-terminal-audit-20261020.json confirma fuentes actuales iguales a congeladas, contenedores/temporal/procesos retirados y recibo1792521613768522436-2142844 sent.

La auditoría beta-catalog-scoped-reuse-audit-20261020.json acredita52casos únicos cubiertos: tres nuevos y49reutilizados de seis archivos, sin duplicar los dos casos del archivo repetido que ya pasaban.622fuentes de producto y todas las demás fuentes de pruebas/herramientas/configuración idénticas entre183249 y183847; sólo cambian el archivo de instrumento repetido y el ledger. Se verifican terminales/limpieza/recibos de ambos cortes. No existe una ejecución única52PASS:183249 permanece ERROR51/1; la cobertura conjunta queda identificada como reutilización acotada.

Se comprueba rechazo tras cambio de catálogo/servicios durante formulario, una lectura por pertenencia, autoridad de imágenes privadas, aislamiento de preparación, contexto/snapshot y contrato romántico. El único delta de producto frente al corte anterior es submissions.py (SHA c34e384db0bc8327f12f136e196c07c3e2dbdeba3407277583f11553d08f1148); las otras621fuentes permanecen iguales. Queda pendiente corregir los otros grupos de118 y ejecutar después el común necesario y regresión amplia pertinente. No N3 global ni capacidad; no se cambia el corto TCP negativo.
