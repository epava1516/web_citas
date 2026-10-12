# MOD-08: investigación de hashes por conjunto, 2026-10-12

La candidata conservadora es sustituir la invocación escalar por fila por una
función SQL que devuelve los hashes de un conjunto. Continúa leyendo y hasheando
cada fila fresca; no guarda hashes ni reutiliza autoridad basada sólo en el head.
No se ha cambiado la aplicación ni demostrado una mejora HTTP.

## Evidencia aislada

SHA de aplicación: `11e33c147b6d7d096297d3fd112fb4a8562c72bf`.
Ejecución `mod08-sql-helper-research-20261012-120342`, Python 3.12.15,
PostgreSQL 17.11. Dos contenedores propios de 1 CPU y 512 MiB cada uno,
swap deshabilitado, red interna sin puertos publicados, datos sintéticos.
No es la topología de capacidad de 8 CPU. Sin perfiladores durante los tiempos.

Tabla parcial de 2500 filas seleccionadas y 50 de otro caso. Función productora
actual extraída del código; lector LOGIN restringido, SECURITY INVOKER/STABLE.
20 rondas por variante con orden rotado, reloj de execute y fetch completo.
La mediana incluye consulta y transferencia al cliente; no es p95 de request.

| Variante | Mediana de consulta | Reducción frente a escalar |
| --- | ---: | ---: |
| Función escalar actual | 59,975 ms | — |
| Función que procesa el conjunto | 36,469 ms | 39,19 % |
| Expresión directa, control | 34,887 ms | 41,83 % |

Resultados idénticos en 4 zonas horarias × 3 DateStyle, con Unicode, números,
fechas nulas y otra columna timestamptz. Una modificación ordinaria del propietario
cambió el hash y fue detectada. Ningún fallo de ensayo; limpieza verificada de
ambos contenedores y su red. Los sondeos iniciales de pg_isready sin respuesta
corresponden al arranque, antes de ejecutar el ensayo.

La dispersión es apreciable: escalar 52,638–93,859 ms, conjunto 33,399–67,902 ms.
No se extrapola este 39,19 % al endpoint, ni se suman medianas de consultas para
prometer segundos. Los planes posteriores no muestran lecturas físicas ni spills.
Function Scan oculta el plan interno y estima 1000 filas frente a 2500 reales;
materialización, memoria y planificación requieren comprobarse con el corpus real.

[Evidencia estructurada](mod08-vps-hashes-conjunto-20261012.json) conserva muestras,
planes, definición, hash del productor, SHA de instrumentos y recibo de limpieza.
Instrumentos y recibo completo permanecen en artifacts/vps-preparation/sql-helper-research.

## Cómo corregirlo y qué probar primero

1. Preparar helpers de prueba para eventos y las siete familias reales. Mantener
   columnas físicas completas, representación v1, scope, orden y snapshots actuales.
   El helper fija search_path una vez y normaliza created_at explícitamente a UTC.
   No fija TimeZone para toda la función: alteraría la representación de otras fechas
   que hoy se convierten a JSON en el contexto del llamador.
2. Comparar exactamente contra el productor en todas las familias no vacías,
   borrados, extras, duplicados, revisiones, NULL, formatos/zonas y search_path hostil.
   Comprobar cadena completa, tickets, roles, funciones y detección de cambios con
   head intacto, concurrencia y cambios de esquema. El ensayo parcial no acredita esto.
3. Evaluar planes y memoria bajo los límites existentes; preservar sellos SQL,
   derechos de ejecución y modelo de confianza. No quitar SET o declarar IMMUTABLE
   sobre lecturas de tablas sólo para conseguir inlining.
4. Sólo tras esa equivalencia, integrar la candidata y medir HTTP sin perfiladores
   con la historia real sintética. Si cumple, repetir una vez. Conservar cualquier
   fallo y diagnosticarlo por separado. No hay aceptación global/N3 en este ensayo.

Esta corrección reduce sobrecoste de llamadas; sigue siendo O(N). Es posible que
su impacto HTTP sea pequeño. La candidata inline anterior no mejoró el p95 medido;
esta prueba no revoca ese resultado ni atribuye diferencias del portátil al código.

## Opciones que requieren otro diseño

Una columna generada almacenada desplazaría cálculo a escritura y se recalcula con
UPDATE ordinario. PostgreSQL 17 exige expresiones inmutables de la fila y no permite
escribir directamente esa columna. No es un reemplazo inmediato: añadirla cambia
el to_jsonb de toda la fila, puede introducir autorreferencia y exige versionar la
representación, migrar/backfill, mantener cadenas previas y acreditar cobertura de
columnas futuras y cambios de funciones. No se ha medido su rendimiento.

Reutilizar una validación porque coincide el head es insuficiente: los tests actuales
exigen detectar cambios del propietario en fuentes/eventos aunque el head no cambie.
Un bloqueo del head tampoco bloquea automáticamente escrituras en otras tablas.

## Fuentes primarias

- [Inlining de funciones SQL](https://wiki.postgresql.org/wiki/Inlining_of_SQL_functions): los SET impiden inlining ordinario.
- [CREATE FUNCTION](https://www.postgresql.org/docs/17/sql-createfunction.html): contexto, permisos y propiedades de funciones.
- [Volatilidad](https://www.postgresql.org/docs/17/xfunc-volatility.html): semántica de snapshots STABLE.
- [Columnas generadas](https://www.postgresql.org/docs/17/ddl-generated-columns.html): cálculo en escritura y restricciones.
- [Bloqueos](https://www.postgresql.org/docs/17/explicit-locking.html): alcance de bloqueos PostgreSQL.
