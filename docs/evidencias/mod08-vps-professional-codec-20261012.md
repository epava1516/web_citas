# MOD-08 — diagnóstico profesional acotado del codec

El usuario autoriza herramientas gratuitas adicionales después del diagnóstico8CPU.
[Resultados previos8CPU](mod08-vps-perfil-8cpu-20261012.md) siguen FAIL.
[Datos estructurados](mod08-vps-professional-codec-20261012.json).

Se usaron por separado Scalene2.3.0 CPU-only y Memray1.20.0 con trazas nativas y
asignadores Python. Intérprete real de la aplicación3.12.15; site-packages de app
precede al venv de instrumentos, sin instalar en app ni modificar uv.lock.
No PG/py-spy/spans/cProfile simultáneos. Datos sintéticos64MiB y adaptador real
_HashedBodyReader, transporte BytesIO: no red, SQL ni autoridad real. No capacidad
HTTP ni sustituto de integración PostgreSQL/RustFS. Artefactos binarios locales
ignorados; no payloads/cifrados/claves en Git.

Memray localizó crecimiento/copia de bytearray en codec._read: ~1.711GB en extend
y~0.805GB en bytes por12verificaciones. Una candidata de una/dos lecturas completas
evita ese acumulador, conserva exactamente la secuencia de read y su fallback
para fragmentación. Se mantienen ciphertextSHA, AEAD, contexto, plaintextSHA,
compromisoEOF, tamaño y tombstones; ninguna caché de resultado/autoridad.

| Métrica sintética | Original | Candidata | Reducción |
|---|---:|---:|---:|
| Asignaciones acumuladas, Memray12iteraciones(bytes) | 4940078860 | 3229173652 | 34.63% |
| Pico adicional durante Tracker(bytes) | 5252230 | 4204993 | 19.94% |
| Mediana CPU sin perfilador(s),16pares alternados | 0.464518 | 0.447499 | 3.66% |
| Mediana pared sin perfilador(s),16pares alternados | 0.469251 | 0.455944 | 2.84% |

PicoTracker excluye buffers construidos antes: no RSS completo. Memray candidata
tardó más instrumentada; precisamente por eso no se usan esos tiempos para ahorro.
Comparación sin perfilador alterna orden para limitar sesgo, pero no prueba
causalidad de p95 real, cuotas8CPU ni elimina variación del host. Es una mejora
pequeña; no explica ni resuelve por sí sola los incumplimientos.

Scalene con filtro al módulo codec atribuye52.25% en código nativo muestreado visible al
digest.update del plaintext; extend/bytes suman8.07% nativo y2.78% sistema; la configuración incluye
preparación encrypt y filtra otras rutas: no porcentajes de CPU del request.
La primera captura sólo atribuyó al llamador; se añadió profile-all/profile-only
para resolver líneas. No extrapolar cifras a HTTP.

Primer helper memray-reader falló antes de Tracker por TypeError Path+str; se
conserva el fallo, se corrigió el paréntesis y se ejecutó después. Memray emitió
advertencias de corrección de símbolos malloc/free, conservadas localmente.

Corrección aplicada sólo en codec._read. Contrastes de lectores bytes/bytearray/
memoryview, fragmentación1/7/513/1026/1048576, truncamiento y excepciones tempranas/tardías
comparan salida, tipo, mensaje, tamaño/secuencia de read y posición contra el
lector anterior. Tests de crypto/verificación y transporte mock conservan orden de
fallos e integridad. Integración real y p95 limpios de esta corrección pendientes.

En paralelo un agente nativo escritor prepara Memray para peticiones marcadas de
cobertura en worktree aislado, con propiedad exclusiva de instrumentos y tests;
Codex revisa/integrará. Scalene Gunicorn necesita adaptación adicional: CLI suprime
JSON en hijos y start requiere inicialización, no se fuerza API privada ni se
anuncia soporte que no existe. Hipótesiscoverage: cuatro revisiones seriales
recorren una cadena creciente; no autoriza memoizar validación fresca.

Fuentes primarias consultadas: [py-spy](https://github.com/benfred/py-spy),
[Scalene](https://github.com/plasma-umass/scalene),
[Memray](https://github.com/bloomberg/memray).

Verificación local:111tests crypto/lectores/mock PASS,18reales excluidos en esa
ejecución;120tests de instrumentos PASS2.69s, Ruff y docs PASS. No integrar
los mocks como verificación de RustFS/PostgreSQL real; pendientes puertas reales.
