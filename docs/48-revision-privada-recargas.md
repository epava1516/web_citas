# Revisión privada de recargas: contrato de implementación

Diseño pendiente de implementar. No habilita publicación ni acredita revisión humana.

## Autoridad y ámbito

Permiso específico de revisión de recargas, MFA vigente y exclusión del sujeto, gestores y agencias actuales/históricos, autor del caso y decisores de la retirada. La revisión usa el ámbito de la ejecución que retiró la imagen, pero no reabre ni resuelve automáticamente el expediente original. Cambios de gestión exigen recalcular conflictos bajo bloqueos.

El registro candidato debe conservar uploaded_blob además de Photo: una referencia que se sustituye durante una retirada no debe heredar decisiones sobre los bytes anteriores. Detectar y consultar nunca confieren permiso para rehabilitar. No confiar en IDs recibidos sin revalidar persona, archivo, disposición activa y estado de preparación/historial.

## Consulta auditada

GET muestra formulario con motivo y metadatos mínimos, sin bytes históricos. POST autorizado crea lectura durable ligada a actor, candidato, motivo, fecha y huella de la autoridad y de ambos recursos. Solo después entrega imágenes mediante rutas privadas ligadas a esa lectura. No reutilizar una lectura de otro actor ni una huella anterior; MFA/roles/conflictos y versión se comprueban otra vez al abrir.

Huella incluye Photo/Blob de la carga, Blob conservado de retirada, ejecución/disposición, persona/gestión/derechos, estados de retirada/archivos y firmas. Lecturas y decisiones no recuperan archivos purgados ni confieren acceso general al expediente. Cache privada/no-store; una retirada durante espera del bloqueo debe devolver404. No se revocan bytes ya entregados.

## Decisión independiente

Resultados: mantener retirada, falso positivo visual y autorizar uso actual en el ámbito revisado. Cada decisión exige lectura actual, motivo privado, referencia de evidencia, clave idempotente y versión. La autorización solo afecta al candidato revisado; no publica el anuncio ni elimina decisiones ordinarias de duplicados. No autorizar por similitud visual sola.

Persistir decisión con vínculos a lectura y recursos; conservar historia y posibilidad de revisión motivada. Nueva autoridad sobre el archivo, cambio de bytes, nueva rectificación o gestión relevante invalidan decisiones anteriores. Dos revisores concurrentes no pueden resolver simultáneamente versiones distintas sin conflicto explícito.

## Publicación e interfaz

Validador central bloquea candidatos activos pendientes o confirmados, incluso si se fuerzan estados de publicación. Envío, aprobación, reanudación, renovación, ficha e imágenes públicas comparten la regla. La carga sigue aceptada para observación; no suspender cuentas automáticamente. El editor muestra estado pendiente genérico ES/EN, sin revelar SHA, expediente o motivos privados.

Recorridos: gestor carga → ve revisión pendiente → moderador independiente consulta auditada → revisa ambas imágenes → decide → gestor ve resultado mínimo → publicación vuelve a pasar moderación ordinaria si corresponde. Mantener cola privada separada de Match; acceso histórico por finalidad explícita.

## Verificación requerida

HTTP y servicio: permisos/MFA/conflictos, ausencia de bytes antes de auditoría, lectura cruzada/obsoleta, idempotencia y versiones, revalidación de uploaded_blob, cambios de autoridad por archivo/persona, concurrencia real PostgreSQL, retirada durante lectura y publicación mientras se decide. Navegador móvil ES/EN y resultados visibles persistidos. Integrar registros en inventarios/exportaciones y conservar evidencia según política final pendiente.
