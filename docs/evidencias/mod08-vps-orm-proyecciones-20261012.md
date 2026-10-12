# MOD-08: investigación profunda de proyecciones ORM

## Resultado y corrección de prioridad

La recomendación inicial de sustituir objetos de categorías, servicios y áreas
de viaje por valores es válida para datos poblados, pero no explica el cuello
actual. tests/capacity_target_fixture.py:populate crea 1500 revisiones mediante
bulk_create y 16 Photo/Blob; no crea sus relaciones categories, services,
travel_areas ni rates. Las FK municipality, postal_code y zone quedan nulas.
Los párrafos que hablan de servicios en las descripciones no son relaciones
del catálogo. No modificar esa carga para aparentar una mejora del objetivo.

La atribución Scalene a rights_copy_revision_batches incluye el fetch del
cursor de revisiones. No es el coste exclusivo de crear objetos de catálogo,
y el recuento Memray de allocations en Model.__init__ no cuenta modelos.

La prueba local de las revisiones muestra un ahorro de decenas de milisegundos
en ese punto. Es una optimización complementaria candidata; este ensayo no
demuestra una reducción del request completo ni la consecución del SLO.

## Prueba realizada y alcance

Ejecución `mod08-orm-research-20261012-104909`, código de aplicación congelado
en `9c23783` (SHA completo en JSON), Python 3.12.15, Django 5.2.17,
modelos reales del proyecto y PostgreSQL propio, con esquema parcial sintético.
Cada contenedor: 1 CPU y 512 MiB, swap configurada a cero, raíz de sólo lectura,
sin capacidades, no-new-privileges, red interna sin puertos publicados.
App uid/gid del usuario; PostgreSQL uid/gid 70. No otros servicios utilizados.

Se comparan 15 vueltas alternando el orden de los candidatos, tras una
comprobación inicial de igualdad. El temporizador no incluye esa comprobación
posterior ni la captura inicial del texto SQL. No hay perfilador durante las
vueltas. Las consultas de relación siguen usando el array UUID parametrizado,
lotes de 1000/500, mismos filtros y orden; seis consultas por variante.

| Mediana wall local | Modelos actuales | Tuplas mínimas | Tuplas con todos los campos |
| --- | --- | --- | --- |
| Relaciones vacías, 1500 revisiones | 35.112 ms | 37.258 ms | 33.588 ms |
| Relaciones pobladas, 18000 filas | 321.055 ms | 149.865 ms | 123.894 ms |
| Lectura de revisiones, 1500 filas | 218.949 ms | No ensayado | 162.530 ms |

| Mediana CPU del proceso local | Modelos actuales | Tuplas mínimas | Tuplas con todos los campos |
| --- | --- | --- | --- |
| Relaciones vacías | 22.976 ms | 20.791 ms | 20.259 ms |
| Relaciones pobladas | 247.714 ms | 94.868 ms | 72.653 ms |
| Lectura de revisiones | 121.309 ms | No ensayado | 72.846 ms |

Las relaciones vacías no tienen objetos que eliminar: la diferencia de 1.524 ms
entre modelos y tuplas completas no demuestra un ahorro útil; las mínimas
fueron incluso más lentas. Hay dispersión apreciable en las muestras, que se
conservan. No deducir de este ensayo que conservar más columnas sea más rápido
en general. El caso poblado es una carga contrafactual: cuatro relaciones por
tipo y revisión, no la carga del benchmark HTTP actual.

La lectura principal incluye 16,555,500 bytes de texto sintético, 36 columnas,
los tres LEFT JOIN y FOR UPDATE OF listings_revision en ambas variantes.
Mantiene iterator(chunk_size=1000) y la transacción. Se comprobó igualdad de
todos los valores retornados. La revisión de SQL encontró una diferencia:
Django sustituye las tres PK de los modelos unidos por las FK de Revision
en values_list. Ambas salidas tienen 36 posiciones, pero los conjuntos de
expresiones SQL no son idénticos. Como las tres relaciones son nulas aquí,
esa sustitución no cambia estos valores; no prueba igualdad integral de sellos.
El ORDER BY por posición generado para values_list representa created_at;
las filas resultan en el mismo orden creado/UUID. El ahorro local mediano es
56.419 ms; incluye la extracción de atributos del modelo a tuplas en la
referencia. No es una medida exclusiva de Model.__init__ ni de source_copy.

El esquema parcial no implementa las migraciones completas, triggers o todas
las FK. No prueba autorización, sellos, concurrencia con escritores,
caducidades, lectura física de imágenes ni equivalencia integral del dominio.
El límite de CPU es distinto al del benchmark HTTP: no extrapolar estos números
al p95 bajo 8 CPU ni multiplicarlos por llamadas supuestas.

Dos intentos previos se conservaron y no se usan: el primero incluía renderizado
SQL repetido en los tiempos; el segundo falló al construir la columna generada
de búsqueda en el esquema parcial. Se corrigió el instrumento, no la aplicación.
Las tres ejecuciones eliminaron sus contenedores y red propios; la final verificó
ausencia y checksum del resultado. No se modificó ninguna etiqueta de imagen.

[Evidencia compacta y muestras](mod08-vps-orm-proyecciones-20261012.json).
Fuentes reproducibles y registros completos permanecen sin versionar en
artifacts/vps-preparation/orm-projection-research; hashes en el JSON.

## Diseño posible y límites técnicos

[Django 5.2](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#values-list)
mantiene el orden de campos indicado en values_list. El
[código de Django](https://github.com/django/django/blob/stable/5.2.x/django/db/models/query.py)
distingue ModelIterable, que llama from_db, de ValuesListIterable, que entrega
tuplas. La optimización elimina construcción de modelos y manejo de atributos;
no elimina ejecutar SQL, transferir texto ni convertir JSONField.

No unir categorías, servicios y municipios en una sola consulta: las múltiples
relaciones M2M pueden multiplicar filas. Conservar las consultas separadas y
la asignación exacta por copy_parent; no usar distinct para ocultar duplicados.
Los consumidores de esas tres relaciones sólo requieren slug/slug/code.

Una variante conservadora devuelve tuplas de todos los campos originalmente
seleccionados, preservando entradas a las comprobaciones SQL. Una variante
mínima de dos columnas por relación cambia el conjunto de datos registrado y
requiere demostrar que los controles siguen cubriendo la misma frescura.
No decidir esa equivalencia sólo por igualdad del JSON final.

rights_validation_seal.recording anota y registra las filas SQL consumidas;
rights_source_fingerprint incluye tablas de catálogo y sus relaciones con
xmin/ctid. Además, el receptor post_init de rights_validation_seal recoge
expiries de instancias cargadas. values_list omite esas instancias y señales.
[Django documenta esas señales](https://docs.djangoproject.com/en/5.2/ref/signals/#post-init).
Las tres clases de catálogo y Revision no contienen EXPIRY_FIELDS actuales,
pero una conversión general de modelos perdería esa garantía en otros casos.
No desconectar señales globalmente ni modificar sus receptores para acelerar.

source_copy es el único consumidor productivo directo de los atributos de lote.
Un cambio para revisiones exige adaptar batches, el ensamblaje del diccionario,
contact_data y image_inventory: actualmente esperan atributos de objetos.
Es posible mantener revisiones como modelos y sólo proyectar catálogos,
pero ese cambio no resolverá esta carga vacía.

Photo/Blob requieren un análisis separado: image_inventory necesita id,
posición, fechas, estado y dimensiones; la lectura auditada posterior mantiene
sus objetos bloqueados y archivos físicos. No mezclar esa lectura con una
proyección de inventario ni usarla para omitir verificaciones.

## Comprobaciones necesarias antes de integrar

1. Igualdad de source_copy y sus bytes canónicos, con datos vacíos/poblados,
   filas históricas inactivas, múltiples relaciones, nulos y límites 999/1000/1001.
2. Misma selección y orden de filas, aislamiento por revisión/listado y ausencia
   de consultas adicionales; conservar bloqueos del usuario y revisiones.
3. PostgreSQL con migraciones reales y pruebas concurrentes de bloqueo,
   inserción/edición/reasignación; no inferirlo del esquema parcial.
4. Pruebas negativas de sellos y source_fingerprint frente a modificaciones de
   campos de catálogo, relaciones, claves, permisos y vigencia temporal.
5. Confirmar equivalencia de contact_data, inventario y valores convertidos;
   después ejecutar las puertas necesarias y medir HTTP sin perfiladores.

No se ha aplicado una optimización a la aplicación. El siguiente candidato
de esta familia es la materialización de las revisiones completas, cuyo
beneficio esperado debe comprobarse en el flujo real. La primera propuesta
de catálogos pierde prioridad para el SLO actual. No hay aceptación global/N3.
