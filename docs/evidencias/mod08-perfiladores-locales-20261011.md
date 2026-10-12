# MOD-08: captura nativa y PostgreSQL correlacionados

El usuario autoriza instalar y utilizar herramientas gratuitas. Se instalan fuera
de las dependencias de la aplicación, en
`/home/eduardo/.local/share/web-citas-diagnostics/venv`: py-spy 0.4.2,
Scalene 2.3.0 y Memray 1.20.0. La huella del ejecutable y las versiones quedan
en `installation.json` de ese directorio. No se conectan cuentas ni servicios
de pago. Se comienza por py-spy y PostgreSQL; los otros dos perfiladores se
reservan para capturas separadas si aparece una hipótesis de CPU o asignaciones.

El smoke local de py-spy produjo 199 muestras y cero errores. Las pruebas
existentes de WSGI, tiempos y separación de modos, ampliadas con las exclusiones
del perfilador, produjeron 80 PASS. Esto
comprueba el instrumento y sus controles, no rendimiento contractual.

El smoke nativo dentro de Docker, con rootfs de lectura, capabilities eliminadas
y `no-new-privileges`, produjo 199 muestras sin errores. La variante donde un
hijo inspecciona su padre, igual que en WSGI, produjo 210 muestras sin errores.
No se cambió Yama ni el filtro seccomp. Imagen de aplicación reconstruida con
el Dockerfile vigente: `sha256:2eb8c753ef9603750605cb88572a07f1680ae1113451c40fbd3229df733df6b0`.

Memray obtuvo una captura nativa del `unseal` real con un cuerpo sintético grande
y comprobó igualdad del resultado. Sus cifras no son el fixture contractual ni
un ahorro: sólo prueba que el instrumento funciona. Scalene queda instalado y
su CLI responde; no se ejecuta un perfil adicional sin hipótesis que lo justifique.

## Experimento registrado antes de medir

Se prepara el caso completo existente: 1500 revisiones, selección JSON cercana
a 16 MiB, originales reales cercanos a 64 MiB, todas las páginas leídas por HTTP,
aprobación real, generación Celery y entrega privada RustFS/Caddy. La instantánea
histórica no permite reutilización después de cambiar código: su política exige
una huella exacta. No se desactiva esa comprobación ni se fabrican aprobaciones.

El ejecutor añade `--native-profile` exclusivamente al modo de diagnóstico completo
y propio. Monta el binario en lectura, mantiene los límites del contenedor y no
añade capacidades ni modifica sysctls. PostgreSQL activa `pg_stat_statements`
con llamadas anidadas y tiempos de E/S de bloques en su contenedor desechable.
No cambia los privilegios del rol que ejecuta operaciones de negocio.

Las peticiones explícitamente marcadas obtienen pilas Python/nativas con hilos
inactivos incluidos a 100 Hz, PID del backend y un sondeo de `pg_stat_activity`
cada 25 ms. Además de la petición temprana de navegación, se marca el lote 301
para observar una cadena que ya ha acumulado lecturas reales. Las demás
peticiones mantienen la instrumentación previa; no son un control absolutamente
libre de instrumentos. Se conservan tiempos HTTP separados de los perfilados.

Límites: máximo 100 segundos y 4000 muestras de espera por captura; los plazos
del ejecutor y la retirada de recursos propios siguen vigentes. Los artefactos
no incluyen SQL literal, parámetros, cuerpos, variables locales ni datos reales.
Un fallo del instrumento invalida su captura; no equivale a resolver el bloqueo.

## Interpretación y condición de avance

`ClientRead` significa que PostgreSQL espera al cliente. Los sondeos pueden perder
esperas cortas; no miden directamente syscall o transporte. Los deltas de
`pg_stat_statements` son del intervalo y rol, pueden incluir Celery/Beat y sus
tiempos anidados se solapan. Los perfiles incluyen el hilo observador, que debe
separarse de los hilos del request. El perfilador, los temporizadores y las
estadísticas introducen costes: sus p95 no sirven como aceptación.

Se buscará una operación dominante concreta que pueda reducirse manteniendo
lecturas frescas, auditoría, bloqueo, purga y autorización. Sólo entonces se
implementará una candidata y se comprobará con equivalencia y PostgreSQL real,
seguida de una medición sin los nuevos perfiladores. No se atribuirá una mejora
a una población pequeña ni se declararán satisfechos 2s/5s con esta captura.

## Resultado retenido y corrección del instrumento

El recorrido real completo `20261011-194447-d2b6e378` terminó con 1 PASS
en 1192,608 s, fuentes sin cambios durante la ejecución y retirada de todos
sus recursos. Es `PROFILE_DIAGNOSTIC_NOT_CAPACITY`, no aceptación. Procesó
1500 revisiones, 1509 páginas y 384 grupos de cobertura.

| Medida HTTP separada de capturas nativas | Resultado | Objetivo | Pendiente |
| --- | ---: | ---: | ---: |
| Navegación, p95 de 382 muestras | 2,565728 s | 2 s | 565,728 ms |
| JSON, máximo de 3 muestras | 4,807344 s | 5 s | Debajo por 192,656 ms |
| Binario, máximo de 8 muestras | 5,124024 s | 5 s | 124,024 ms |

Las descargas son partes de unos 8 MiB, con dos autorizaciones frescas por
parte; no una petición única de 64 MiB. Los controles conservan la
instrumentación previa de fases. Una población y tres/ocho descargas no
satisfacen la aceptación ni permiten atribuir mejora frente a otra ejecución.
No se ha añadido una optimización productiva durante este experimento.

El coste observado de los enlaces de cadena aumenta: cuatro llamadas tempranas
procesaron 340 filas en 7,11 ms de ejecución agregada, frente a 9844 filas
en 182,869 ms en la captura tardía. Los tiempos anidados se solapan y no se
suman como ahorro. La captura tardía obtuvo 449 muestras del hilo principal
y sólo una muestra de espera Lock entre 144 sondeos: no demuestra un bloqueo
dominante ni excluye esperas cortas. El procesamiento local está repartido entre
hashes, copia de fuentes, comprobación canónica, descodificación y adaptación.
Las estadísticas globales pueden incluir otros workers. El throttling acumulado
del contenedor tampoco identifica por sí solo la causa de una petición.

Se detectaron límites de la primera versión: PID cerrado en el sondeo de
`binary_download_proxy` (esa captura de esperas es inválida), dos trazas con
un error de muestreo cada una y superposición de cProfile en descargas. Las
entradas SQL repetidas deben agregarse por usuario/queryid antes de calcular
deltas; no se interpretan sobrescribiéndolas en un diccionario.

La versión v2 enlaza el PID al ejecutar SQL, sigue reconexiones, registra
`toplevel` y mapas nativos y evita superponer cProfile al perfilador nativo.
No se ha repetido el recorrido completo con v2. Su prueba real restringida
`20261011-203718-27e0f6d5` terminó con 1 PASS en 33,057 s, siguió PID 89 y 91
sin errores y retiró sus recursos: `NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY`.
Se conservan dos intentos fallidos por configuración del propio probe
(`20261011-202214-64849ec7`, `20261011-202657-9bc54744`) y el probe
`20261011-203144-6489b7b1`, cuyo test pasó pero el launcher devolvió error
por faltar el nuevo resultado en su lista de salidas permitidas. Se corrigió
antes del último probe; no se reescribe ese historial como éxito.

La verificación local posterior de contratos, WSGI y temporizadores obtuvo
82 PASS. Los dos tests nuevos de separación del perfilador se añadieron
después de terminar el último probe; su huella histórica no representa estos
tests posteriores. Los cambios de producto previos permanecen conservados.

Siguiente decisión técnica: aislar una candidata con ahorro medible y garantías
de frescura demostradas, y compararla con control sin nuevos perfiladores.
No hay evidencia suficiente para prometer que eliminar unas consultas o
redistribuir CPU alcance por sí solo los 2 s. El bloqueo contractual sigue abierto.

## Separación de instrumentos posterior — controles sin hooks locales

Por petición del usuario se elimina también la instrumentación de fases que
seguía activa en navegación nativa. En modo `--native-profile`:

- Los controles HTTP no instalan `observe`, spans de fases, wrappers SQL,
  cProfile ni hooks de workers. Conservan la medida externa de tiempo HTTP.
- Las peticiones marcadas usan sólo py-spy y su observador PostgreSQL; no
  instalan ninguno de los instrumentos anteriores, incluida navegación.
- El controlador no activa cProfile, el diagnóstico SQL previo de fingerprint
  ni el perfil posvalidación en este modo.
- El modo legado conserva sus instrumentos para investigaciones explícitas
  separadas; no se borra evidencia histórica ni se mezclan ambos modos.
- Memray queda para pruebas aisladas de asignaciones y Scalene permanece
  instalado pero inactivo. No se agregan al recorrido HTTP ni al proceso de negocio.

PostgreSQL sigue teniendo estadísticas globales habilitadas en el contenedor
diagnóstico: estos controles no equivalen a un benchmark de aceptación sin
observadores. La aceptación debe usar el modo contractual normal, que ejecuta
`config.wsgi` sin perfiladores ni extensión añadida por el modo nativo.
No se ha repetido el recorrido completo ni se han recalculado los tiempos
históricos después de esta separación. Las pruebas de exclusión verifican
cierre del iterable y conservación de errores también en controles y navegación.

## Verificación completa posterior

Se completaron la repetición nativa separada y el escenario normal concurrente
sin perfiladores. Resultado normal: FAIL_DELIVERY_STAGE_LIMITS. Los p95
3,389665/8,961067/9,033017 s no cumplen 2/5/5 s. La posvalidación
cProfile se excluyó también del modo normal antes de medir. Los resultados
y la auditoría se conservan en [la evidencia posterior](mod08-metricas-separadas-20261011.md).
