# Reconciliación pendiente de exclusiones de regresión

El perfil regression excluye dos nodos HTTP short/measured y dos archivos:
`test_rights_portability_large_history.py` y `test_publication_state_tcp.py`.
La partición cubre todos los otros 495 archivos sin pérdidas/solapamientos.
Estas exclusiones declaradas no equivalen a PASS ni omiten requisitos por sí solas.

El historial grande excluido prueba transporte de 8 MiB con 1.500 revisiones y
usa tracemalloc para diagnóstico de memoria; no debe usarse como medición limpia
p95. El flujo cerrado de 1.500 revisiones sí pasó en el bloque 2, pero no es la
misma selección ni acredita automáticamente sus aserciones de umbral/transporte.

La matriz TCP excluida son seis controles secuenciales 100/1.000/10.000 y
repeated/diverse; su encabezado declara que no es capacidad. Existe evidencia
histórica positiva mod05-tcp-matriz-revisada0110, fuente 55d97bc. Su cobertura
requiere comparación pertinente con la versión actual, sin repetirla por rutina.

El archivo contractual HTTP mantiene functional incluido; short/measured quedan
fuera. El archivo original de intento 2
mod05-contractual-normal-intento2-artefactos0110.tar.gz contiene manifests/result
coherentes en c82a7468b83b83a1d2161a728a28f8c509cfb804, fuentes intactas y
limpieza verificada. Es evidencia histórica positiva de carga contractual.
La versión actual difiere en publication_signals, publication_state, media
services, configuración/rutas. La comparación posterior de huellas reales confirma que
el instrumento cliente coincide; el SHA Git histórico no incluía todos sus
cambios locales. No se atribuye su PASS
histórico automáticamente a la versión final. Hay riesgo concreto compartido
que exige revisar diferencias y el gate de carga pertinente al N3.

MOD-09 permite continuar con la deuda de latencia de exportaciones grandes;
no acepta global/N3 ni sustituye el gate de listado/búsqueda/ficha. No se
reabre la optimización pesada aplazada. Tras el bloque 3 y controles opt-in,
preparar gate limpio con los recursos/topología/criterios autorizados y versión
congelada; conservar cualquier fallo y diagnosticar por separado, sin ensayos
simultáneos ni cadena de variantes especulativas.
