# MOD-08 pieza 10 — baseline de diagnóstico, diseño y restricción

Actualización16:56UTC: implementación privada AEAD/captura/restauración en rama integrada, con22PASS N2 (1caso real PG/media/RustFS positivo/adversariales y21guards); captura a escala1500 y ganancia temporal todavía pendientes. Las decisiones siguientes describen el diseño original y sus restricciones vigentes; no son aceptación de capacidad.

Inspección: `test_capacity_delivery_profile` construye un expediente mediante
`prepare_target` y ejecuta `run_case(diagnostic=True, full=...)`. El recorrido hace
31 lecturas de selección, 16 lecturas binarias y todas las páginas de cobertura
antes de generar/exportar/cerrar. Esas lecturas HTTP crean evidencia real: el
constructor no inventa read_ids. `--delivery-profile` ya es exclusivo con el modo
de entrega completa; el perfil declara overhead y no emite aceptación de SLO.

Decisión en este corte: **no cachear autoridad ni insertar estados aprobados**.
La reutilización de una aprobación previa puede servir para perfilar etapas
posteriores de la misma versión, pero no equivale a probar el recorrido completo.
El límite implementado en `run_case` captura después de todas las lecturas y
aprobaciones reales y antes de generación. La pieza10 sigue pendiente de captura
y reutilización a escala; las restricciones siguientes permanecen obligatorias.

## Snapshot aprobado, únicamente diagnóstico

Punto de captura: después de la decisión real de cobertura, con sus lecturas y
selección binarias reales, antes de generación de exportación. Guardar PostgreSQL
más todos los medios en un artefacto privado de sólo lectura; identificar
expediente/IDs de evidencia en un contexto privado separado del manifest público.
Los secretos sintéticos de receipt/sesiones/clave jamás van a JUnit o al manifest.

Clave de caché: hash de todas las fuentes de reglas/serialización/validación y
migraciones, versiones Django/PostgreSQL y librerías pertinentes, configuración
sin secretos expuestos (su huella sí), forma canónica, versión de tablas/triggers,
semilla/identidad/sizes del dataset, SHA-256 de dump y de cada medio. Cualquier
cambio invalida; no convertir una firma antigua ni reetiquetar su versión como nueva.
El snapshot guarda las expiraciones originales y un límite de uso igual al mínimo
de proof, assessment, selection, coverage y receipt. No renueva ni extiende ninguno.

Restaurar exclusivamente en PG/media propios del nuevo run y worker, verificando
container/nombre/label/puerto y cero conexiones ajenas, sin terminate. Mantener
snapshot fuente inmutable, copiar los medios a destinos propios y conservar los
límites de recursos. El controlador debe contabilizar explícitamente almacenamiento
y memoria del snapshot y de su copia antes de admitir este modo: no esconderlos
fuera de sus cuotas. La creación/restauración queda fuera de la etapa perfilada y
sus tiempos/bytes se declaran por separado.

Antes del primer request: validar SHA-256 real de dump/medios, fuente completa y
su digest, permisos/actividad/versiones de actor y autoridad/prueba actuales,
expiraciones, integridad de todas las evidencias con los validadores originales y
cadenas/triggers/roles vigentes cuando corresponda. Los tickets de otro run no se
reutilizan. No editar tiempos, version, pruebas, firmas, RateWindow ni read_ids.
Crear un cliente actual sólo si no modifica el origen auditado; la validación de
fuente detectará cualquier deriva. Preservar estados de rechazo y de purga reales.

Si falla cualquier comprobación, registrar CACHE_REJECTED con causa minimizada y
volver al constructor/recorrido completo real. Un cache hit se registra explícitamente
como diagnóstico de etapas posteriores con preparación reutilizada. Nunca como
lecturas nuevas, aprobación nueva, N2 del recorrido, N3, capacidad ni PASS de SLO.
Un flag futuro para baseline debe ser incompatible con --delivery-complete y todas
las modalidades de aceptación y rechazar la combinación antes de crear recursos.

## Por qué no activar ahora el snapshot aprobado

La finalidad inmediata es comparar cambios tecnológicos. Esos cambios modifican
precisamente canónica, firmas, código de validación, esquema y roles; por el criterio
anterior invalidan el baseline. Revalidar una aprobación de versión vieja no puede
recrear las decisiones humanas ligadas a firmas/fuentes cambiadas. La caducidad
máxima observada de proof/assessment/selection/coverage es de 24 horas y el uso debe
seguir el mínimo real, sin prórroga. Tampoco está implementada la contabilidad del
nuevo artefacto en el controlador ni su aislamiento de aceptación. No hay evidencia
de ahorro neto reproducible que justifique asumir esos riesgos en este corte.

Alternativa con dependencia menor: cachear únicamente **inputs** de `populate`
(textos sintéticos y bytes de las 16 imágenes deterministas, semilla/dimensiones/
Pillow/formato versionados) o la base previa a cualquier RightsRequest/prueba/
lectura/aprobación. Luego ejecutar prepare_target y todas las lecturas reales. El
bootstrap de directory ya tiene un snapshot por worker en pieza9, pero no se extiende
al controlador de capacidad sin contabilizarlo. Esto ahorra construcción repetida
de inputs; no pretende eliminar las 1.509 páginas ni afirmar ahorro de 85→10 minutos.

## Criterio finito de una futura implementación

Prueba en PG propio y medios reales: baseline construido por recorrido real;
restauración mantiene bytes/IDs y fuente; mutaciones de usuario/rol/prueba/origen,
expiración real, dump/imagen corruptos y versión distinta producen rechazo y fallback;
workers y copias de medios independientes; snapshot fuente no mutable; flags de
aceptación incompatibles; evidencia diagnóstica rotulada y retirada exacta. Medir
build/capture/restore/validate de forma comparable y adoptar sólo con ahorro neto.
Para inputs, verificar bytes/textos iguales al constructor original y que ninguna
tabla de derechos/aprobación forma parte de la caché. No se ha ejecutado esta
selección ni se declara PASS: esta entrega es diseño y restricción de alcance.
