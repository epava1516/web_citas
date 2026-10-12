# MOD-08: integración de lectores SQL por conjunto, 2026-10-12

Candidata autorizada por «procede», posterior a la
[investigación aislada](mod08-vps-hashes-conjunto-20261012.md).
La migración 0118 añade ocho funciones SQL STABLE SECURITY INVOKER con search_path
fijado. Los productores, triggers, hashes almacenados y formato v1 no se modifican.
No hay caché: los lectores recalculan el hash completo de cada fila física fresca.
Los campos añadidos al esquema permanecen incluidos en to_jsonb de la fila.
Sólo created_at se normaliza explícitamente a UTC; las otras fechas conservan
la representación del llamador, sin un SET TimeZone global en el helper.

Las siete consultas de fuentes y la consulta de eventos permanecen separadas.
Se conserva la comparación completa de cadena, el bloqueo del head, la frescura
READ COMMITTED entre sentencias, el pipeline y su fallback/orden de errores.
Los nombres SQL de resultados cambian; los sellos se generan y reproducen con
las consultas nuevas. El hash de código de rule_version incluye el módulo nuevo,
por lo que no se presenta un sello antiguo como equivalente al código cambiado.
No se añade autoridad ni privilegio de escritura; los helpers son invoker, nunca
SECURITY DEFINER. No se afirma atestación completa de funciones contra un propietario
malicioso: la frontera de confianza previa se conserva.

## Pruebas reales y fallos conservados

| Ejecución propia | Resultado | Alcance |
| --- | --- | --- |
| mod08-sql-bulk-validation-20261012-122328 | 73 PASS, 368,506 s | siete familias, eventos/tombstone, zonas/formatos, corrupción, permisos, concurrencia, pipeline/replay |
| mod08-sql-bulk-integration-20261012-123213 | 29 PASS / 5 FAIL, 317,533 s | fechas extremas/NULL/Unicode/segunda fecha, cambio de esquema, reinstalación, runtime y sellos; cinco rechazos de preparación |
| 20261012-124120-9fcf64f8 | ERROR antes de pytest | /usr/bin/time ausente; launcher corregido para usar resource, sin instalar ni cambiar la aplicación |
| 20261012-124328-d32cfcb2 | 6 PASS, 135,547 s | cinco ensayos rechazados antes, ahora con LOGIN real atestado, más controles SQL históricos y actuales |

Los cinco FAIL exigían el adaptador de CI con migrador ci y contenedor/puerto
propios comprobados; el contenedor genérico de investigación era inadmisible.
No se modifica ni se elude esa guarda. La repetición utiliza local_ci_settings,
contenedor web-modelos-ci-pg con etiqueta y puerto loopback reales, comprobados
por el adaptador oficial. No se fija manualmente CAPACITY_ENVIRONMENT_VERIFIED.
Los casos vuelven a crear toda la exportación sintética aprobada mediante servicios;
identidad/verificador simulados explícitamente, PostgreSQL y autenticación reales.
La manipulación de metadatos, pérdida de ACL y expiración de prueba no aceptan el sello.

Las dos primeras baterías usan contenedores PG/app propios, 1 CPU/512 MiB cada uno,
sin swap, red interna y montaje de fuentes readonly. La última limita pytest a CPU0
y 4 GiB de espacio virtual; PostgreSQL a CPU1/1 CPU/512 MiB sin swap. Máximo RSS de
los hijos del launcher 310364 KiB: no es un pico agregado de todos los contenedores.
No se ejecutan cargas en paralelo ni se usan servicios productivos. Limpieza de
contenedores/redes verificada en todas las ejecuciones, incluso fallos.
En la última ejecución el manifiesto de fuentes previo/posterior es idéntico.

Son pruebas del worktree previo al commit: HEAD b33998a más cambios locales,
no una medición de b33998a limpio. [Recibos compactos y huellas de aplicación](mod08-vps-lectores-conjunto-20261012.json).
Los XML e instrumentos completos permanecen en artifacts/vps-preparation.

## Instrumentos y siguiente medición

Se conservan los controles de expresión directa anteriores como diagnóstico histórico.
Los filtros de py-spy/PG y spans reconocen las funciones nuevas. EXPLAIN incluye
set_hash como lector actual y native_hash como productor escalar anterior; cinco
rondas rotadas, igualdad exacta y diferencias de forma registradas, sin forzar
que Function Scan tenga la misma forma que los controles. No cambia el presupuesto
15 s/SQL, 90 s/hijo ni la siembra 64/304 de los instrumentos anteriores.

Pendiente el ciclo secuencial preflight8 → probe8 → measure8, fuentes congeladas.
La medición tendrá todos los perfiladores inactivos. Se registrarán p95 por caso,
fallos, duración total, SHA, versiones, límites y limpieza. Sólo repetir si cumple;
si falla, conservar y diagnosticar por separado. Misma RAM8GiB, almacenamiento
propio≤20GiB, sin swap, SLO navegación2s/JSON5s/binario5s. No aceptación global/N3.

La referencia HTTP8CPU es 20261012-023609-aa06db69, anterior tanto a estos lectores
como a la corrección del codec. La nueva medición describe el resultado conjunto:
no separa causalmente ambos cambios. El 39,19 % aislado es mediana de consulta,
no p95 HTTP ni reducción predicha de la duración total. La repetición de consultas
puede acumular ahorro y reducir contención; la magnitud sigue pendiente de medir.
No se atribuyen diferencias del portátil al código: su perfil energético cambiaba
al alternar el cargador. Se registrará la identidad de imagen reconstruida y el
montaje readonly del código medido, sin ocultar que el ID difiere de la referencia.
