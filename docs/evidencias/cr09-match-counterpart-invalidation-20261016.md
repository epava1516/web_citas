# Corrección: invalidación de lectores indirectos de coincidencias

Se reprodujo un defecto de exactitud: dos anuncios publicados tienen una coincidencia marcada conflict entre sus fotos. Los estados almacenados los excluyen. Al retirar una foto mediante QuerySet.update, el otro anuncio vuelve a ser visible según la regla nativa; el trigger anterior sólo marcaba al propietario de la foto y mantenía el negativo obsoleto de la contraparte. La guardia de página no puede reparar una fila que ya fue omitida de la población.

Reproducción013910-8797a518: **2FAIL51,07s**, ambas orientaciones de la coincidencia. La respuesta almacenada difiere del HTML nativo; la foto de la contraparte sigue válida. Fallos íntegros conservados. No se demostró divulgación de datos indebida; el defecto observado es omisión/resultado público inconsistente.

## Cambio

Migración `0020_publication_match_counterparts` amplía la función DBexistente `listings_publication_mark` por una arista Match en ambos sentidos. Conserva todos los IDs directos, incluye contrapartes de las fotos de todas las revisiones afectadas y deduplica/ordena IDs antes del upsert. Se conserva marked_at inicial y se renueva generation. No se depende de señales, del worker ni del refrescador para exactitud. No se modifica la regla nativa ni el contrato de permisos.

La ampliación es global en el punto de marcado, porque la clasificación ordinary_matches también depende de la revisión, su historia de rectificación y la relación de preparación de imagen. Arreglar sólo Photo dejaría otros lectores indirectos sin marcar. No se propaga recursivamente: el nativo no lee la elegibilidad almacenada de vecinos, sino sus fotos/revisiones/historia. El fanout conservador puede marcar vecinos que no cambian; no se presume gratis ni se elimina por ahora invalidación de borradores.

La migración marca todos los anuncios existentes para reparar negativos que podrían estar ya obsoletos. El reverso restaura la función anterior y vuelve a invalidar; no se presenta el esquema antiguo como correcto para escrituras posteriores.

## Evidencia

[Recibo de fuentes, casos y limpieza](cr09-match-counterpart-invalidation-terminal-20261016.json). Las siguientes son selecciones separadas, no una ejecución N3 ni una suma usada para aceptar CR09:

| Run | Resultado | Alcance |
| --- | --- | --- |
| 014353-34c196fa | 47PASS496,70s | Cuatro regresiones nuevas, publicación existente, concurrencia, locks y rollback |
| 015314-70e862e8 | 10PASS131,61s | Borrado/movimiento de foto, extremos Match, historia, preparación, generación, rollback y upgrade |
| 015724-0956e142 | 2PASS/2FAIL71,45s | Pasan movimiento de revisión y escrituras opuestas; fallan dos supuestos de borrado de revisión publicada |
| 020003-dbfc825f | 2PASS55,58s | Supuestos de borrado corregidos: publicada protegida y cascada de borrador permitido |

Los dos fallos de015724 son errores del test: Submission yModerationDecision impiden eliminar la revisión publicada conPROTECT. No se retira esa protección ni se borra evidencia para pasar. El test corregido exige ProtectedError y comprueba que la referencia publicada sigue intacta; después mueve el extremo Match a una foto de un borrador nuevo sin expediente y prueba su borrado/cascada. Se repiten sólo los dos casos afectados.

Controles funcionales: ambos extremos × foto retirada/revisión rights-stage; cambio de vuelta tras refresco; HTML nativo y almacenado iguales ESEN, incluido conteo. Controles de aristas: foto/revisión borrada, movimiento de Photo.revision yRevision.listing y cambio de extremo Match invalidan propietarios antiguos/nuevos y lector contraparte. Historia: creación/cambio/borrado de ejecución y relación de preparación de foto. Se usa ledger sintético persistido con FKs reales para semántica SQL; no acredita aprobación humana ni proveedor.

El bloqueo con refresco se observa mediante pg_blocking_pids antes de liberar el refrescador: la generación posterior permanece dirty y el resultado termina igual al nativo. Dos escrituras simultáneas opuestas completan sin perder marcas y el refresco drena. Cadena A–B–C comprueba que marcarA afectaA/B y no propaga aC, conserva antigüedad, renueva generación y revierte íntegramente dentro de rollback. No demuestra ausencia universal de deadlocks.

La prueba de upgrade vuelve al esquema0019 en PostgreSQL propio, crea el negativo obsoleto observado, aplica0020 sin refrescador y verifica que ya vuelve a incluir la contraparte; después reconstruye estado y drena. Restauración de esquema actual enfinally. No es un rollback/restauración productivo.

Fuentes originales congeladas verificadas antes de cada edición; migración idéntica en todas las correctivas. El archivo de controles creció después de los10PASS: sus funciones iniciales se contrastaron porAST sin cambios; después sólo se corrigieron los dos tests de borrado recién añadidos. Las tres fuentes entregadas están identificadas porhash. Python3.12.15,dependencias locked,PostgreSQL/Redis propios con cuotas del adaptador,kernel native-sealed. Controlador/hijo/temporal/contenedores ausentes y unidades terminales comprobados independientemente. Ruff/docs/Django/migraciones/herramientas nativas pasaron en los runs correspondientes.

## Límites y siguiente paso

Correctiva local aceptada en este alcance; CR09/N3 y el contrato completo siguen abiertos. **Sin nuevo p95**. El último corto limpio0,904873942sFAIL es anterior a0020; no acredita rendimiento de esta corrección. Falta medir coste del fanout y directorio corregido antes de repetición/carga larga. Dockerimagenv2 es anterior a0020: hay que reconstruirla/verificarla para entrega común. Sigue pendiente cerrar la trazabilidad de los demás criterios y N3 integrado.
