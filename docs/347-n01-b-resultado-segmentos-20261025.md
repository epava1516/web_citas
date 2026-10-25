# N01B — Referencia de segmentos con100perfiles fijos

25deoctubrede2026. [Prerregistro346](346-n01-b-prerregistro-segmentos-20261025.md), corte72c5514, run20261025-083656-adcd31ae. Un casoPASS,0FAIL/ERROR/SKIP;60peticiones verificadas en10segmentos, seis muestras por segmento. [Auditoría independiente](evidencias/n01-b-diagnostico-auditoria-20261025.json) y [archivo original](evidencias/n01-b-diagnostico-evidencia-20261025.json). N01 yN04siguen abiertos;N00aceptado1/13,alfa.

## Observación instrumentada

Primera significa primera medida de ese segmento después de preparación y segmentos anteriores; no cachéOS/PG fría garantizada. Posteriores son cinco muestras del mismo escenario/población. El orden ES→EN y de segmentos es fijo. No atribuir mejoras por calentamiento ni diferencias causales de idioma. No son un antes/después de candidato, p95,20RPS oTCP.

| Idioma | Segmento | Primera(ms) | Mediana5posteriores(ms) | Min–maxposteriores(ms) | SQLprimera/posteriores | Ruta |
| --- | --- | ---: | ---: | --- | --- | --- |
| es | listing | 795.828 | 229.477 | 218.601–352.980 | 29/29 | fallback |
| es | page2 | 238.989 | 217.692 | 205.294–372.355 | 29/29 | fallback |
| es | profile | 238.876 | 207.750 | 187.815–433.774 | 29/29 | fallback |
| es | empty | 104.566 | 73.490 | 72.851–98.939 | 17/17 | state |
| es | detail | 65.431 | 57.784 | 47.125–68.728 | 22/22 | None |
| en | listing | 246.573 | 249.565 | 233.684–448.103 | 29/29 | fallback |
| en | page2 | 306.344 | 271.828 | 213.053–397.024 | 29/29 | fallback |
| en | profile | 255.742 | 243.949 | 201.539–405.786 | 29/29 | fallback |
| en | empty | 67.054 | 93.003 | 85.311–122.524 | 17/17 | state |
| en | detail | 42.964 | 47.972 | 34.942–53.773 | 22/22 | None |

## Hallazgo y límites de atribución

Las36peticiones de listado/página2/perfil usaron fallback con motivo state_unknown_over_limit;12búsquedas vacías usaron state/trusted_state. La ficha no expone ese marcador. El instrumento no forzó una ruta ni sustituyó state_page. La fixture bulk y la ausencia de worker/Beat en este diagnóstico son condiciones relevantes; el resultado no identifica por sí solo un defecto de aplicación ni latencia del camino de estado preparado.

Hay que distinguir explícitamente en la próxima ficha una población con preparación/actualización nativa de estados de una población con estados desconocidos o pendientes, verificar los marcadores y conservar el fallback seguro. No cambiar datos/gates sólo para obtener una cifra menor ni atribuir crédito de worker real a una llamada de mantenimiento síncrona. No repetir otra vez este lote sin una hipótesis nueva y prerregistro.

## Verificación y conservación

Paso pytest:57.552s, con fixture y todas las muestras; no latencia de una petición. Los1507SHAejecutables previos, instrumento nuevo y documentos/grafo congelados permanecieron intactos hasta la auditoría. Caso y tres fases setup/call/teardown exactos,60muestras completas, oráculos200/no-store/idioma/privacidad/IDs/orden/conteo sin fallo. PostgreSQL17/Redis7.4 propios retirados y temporal ausente por inspección independiente; Telegramterminalsent.

Lint, documentación, Django, migraciones y nativo pasaron. Se conservaron errores auxiliares de formato de informes semánticos: STATUS mayúscula y pendientes del proyecto en unresolvedissues; autores corrigieron sólo los informes y la verificación correctiva pasó. No hubo FAIL de producto en este lote. Los originales están en la evidencia de prerregistro, no se borran para dar apariencia de ejecución única verde.

El nuevo código es únicamente el instrumento de diagnóstico; no se modificó producto. N01A no es una base equivalente para porcentaje de mejora porque difieren número/orden de muestras e instrumentación. La tabla antes/después obligatoria de cada bloque se emitirá al cerrarlo con referencia/candidato comparables, o ausencia de base declarada. La deN00 permanece en343.

Promociones, profundidad grande, filtros combinados, otros tamaños, estados negativos, worker/navegador/carga y ocho grupos restantes siguen con sus límites y fichas pendientes. Este resultado no cierra N01 oN04 ni acepta producción.
