# MOD-08: investigación de optimizaciones tras Scalene

Investigación web del 2026-10-12 contrastada con el código local y el
[diagnóstico válido](mod08-vps-scalene-cobertura-20261012.md).
Son candidatos y criterios de comprobación, no mejoras de latencia medidas.
No se modifica la aplicación ni se ejecuta otra medición en esta investigación.

## Decisión y orden

| Prioridad | Punto concreto | Candidato | Condición antes de aplicar |
| --- | --- | --- | --- |
| 1 | rights_copy_revision_batches.batches y source_copy | Proyectar únicamente valores de categorías, servicios y municipios de viaje | Misma agrupación por revisión, orden, duplicados, filtros y salida canónica; demostrar menor coste local |
| 1 | Consultas de revisiones y evidence_chain._source_rows_pipeline | Examinar planes y distinguir ejecución SQL de transferencia/materialización | Estadísticas propias por consulta y EXPLAIN con datos sintéticos; índices o reescrituras sólo si el plan demuestra necesidad |
| 2 | crypto.unseal | Separar descifrado de parseo JSON; evaluar parser nativo compatible | Mismos valores, precisión, Unicode, excepciones y comportamiento de claves/tokens; no sustituir globalmente json.loads |
| 3 | rights_exports._read_image_blob | Leer con buffers acotados en vez de reservar 10 MiB por original menor | Misma lectura física fresca, límite y errores; confirmar coste con benchmark del transporte real |
| Condicional | Repeticiones de unseal en inspección | Evitar materialización pura duplicada dentro de la operación | Comparar token recién leído y clave efectiva actuales, impedir mutación y limitar memoria; jamás reutilizar autorización ni validez de evidencia |
| Posterior | Python puro residual | Compilar una función concreta con mypyc/Cython | CPU Python dominante demostrada en esa función y contrato equivalente |

## Consultas y materialización

[Django 5.2](https://docs.djangoproject.com/en/5.2/topics/db/optimization/)
recomienda explicar consultas, seleccionar campos necesarios y usar values o
values_list cuando no hacen falta instancias. Aquí source_copy ya usa defer,
select_related, iterator y agrupación de cinco relaciones por lote. Añadir esas
técnicas sin revisar lo existente no constituye un cambio nuevo.

Los consumidores de copy_categories y copy_services sólo leen slug; los de
copy_travel_areas sólo code. Estos tres conjuntos son un primer candidato a
tuplas de identificador de revisión y valor, evitando instanciar objetos de
catálogo completos. La consulta de Photo/Blob tiene comportamiento de archivo
y no debe convertirse a tuplas indiscriminadamente. La consulta principal de
revisiones conserva sus bloqueos y campos usados por contact_data.

El porcentaje atribuido al archivo batches incluye su fetch del cursor; no
demuestra que construir objetos sea todo el coste. Hay que separar esa parte
del tiempo de PostgreSQL y de convertir resultados.

[pg_stat_statements](https://www.postgresql.org/docs/17/pgstatstatements.html)
ofrece llamadas, filas, tiempo de ejecución y bloques; no mide el coste de
construir objetos en Django. Contrastar esos datos con el tiempo del cliente.
[EXPLAIN ANALYZE y BUFFERS](https://www.postgresql.org/docs/17/using-explain.html)
permiten evaluar planes, filas y accesos. Ejecutarlos sólo en infraestructura
propia sintética, separados de la medición de aceptación.

[Django documenta](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)
que select_for_update con values debe seleccionar campos del modelo que se
quiere bloquear. Cualquier reducción de columnas debe preservar exactamente
el conjunto bloqueado, no sólo devolver el mismo JSON.

## Criptografía y JSON

crypto.unseal:35 contiene construcción de Fernet, encode, decrypt, decode y
json.loads. El perfil de esa línea no separa AES/HMAC del parseo. No permite
concluir que cambiar criptografía resolvería su coste.

[Fernet 50.0.2](https://cryptography.io/en/50.0.2/fernet/) autentica el mensaje
completo antes de exponer su contenido. No eliminar autenticación ni migrar
formatos por una atribución agregada. Las imágenes/exportaciones ya tienen
su propio codec: la limitación de memoria de Fernet no implica que todos los
archivos actuales estén cifrados mediante Fernet.

[orjson](https://github.com/ijl/orjson) admite entrada bytes y es un candidato
para parseo nativo, pero difiere de json en Unicode, números y JSON no estándar.
Su benchmark publicado no predice nuestra mejora HTTP. Probar entradas límite
y precisión, además de la carga sintética normal, antes de introducir un camino
rápido con fallback explícito. No cambiar dumps de seal: alteraría formatos.

[Psycopg](https://www.psycopg.org/psycopg3/docs/basic/adapt.html#json-adaptation)
permite personalizar JSON por conexión o cursor. En la instalación local,
Django JSONField.from_db_value usa su propio json.loads; cambiar el loader de
Psycopg no garantiza acelerar ese camino y puede romper su adaptación.

## Opciones que requieren otra evidencia

[Pipeline de Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html)
reduce rondas de comunicación; PostgreSQL sigue ejecutando en orden. El
proyecto ya lo usa en evidence_chain y rights_validation_seal. No paraleliza
el servidor y no debe mezclarse directamente con ServerCursor, que no está
implementado en pipeline según la documentación consultada. Ampliarlo sólo
si las rondas pequeñas dominan, preservando errores y orden de validación.

[mypyc](https://mypyc.readthedocs.io/en/stable/performance_tips_and_tricks.html)
se beneficia de operaciones y tipos nativos; depender intensamente de
bibliotecas Python interpretadas limita el beneficio. Compilar envoltorios de
ORM, I/O o criptografía nativa no elimina el trabajo de esas bibliotecas.
El kernel canónico del proyecto ya es nativo; no hay evidencia de fallback
dominante en estos perfiles.

No aumentar CPU por encima de las 8 autorizadas, ni añadir cachés de permisos,
ni omitir lecturas físicas/comprobaciones frescas. Tampoco cambiar a async
transforma por sí solo el trabajo secuencial de un request.

## Validación de un candidato

Elegir un cambio con evidencia, comprobar equivalencia sobre PostgreSQL y
datos sintéticos, y comparar coste del punto concreto antes de otra ejecución
completa. Después, preflight/probe/measure según el procedimiento, sin
perfiladores durante measure. Publicar p95 por caso y cuadro comparativo;
repetir una vez sólo si cumple. Ninguna hipótesis anterior demuestra que se
alcance el SLO ni autoriza aceptación global/N3.
