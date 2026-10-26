# N08 — aceptación local de favoritos, SEO y exposición comercial sintética

26 de octubre de2026. Alfa. N08 queda aceptado localmente con los escenarios y límites descritos: **8/13 bloques obligatorios** (N00,N01,N03,N04,N05,N06,N07,N08). El objetivo completo sigue activo; N09 es el siguiente bloque. N02/MOD09 restante mantiene el diferimiento expreso al final del desarrollo, sin PASS temporal. N12–N14 siguen condicionados; no se abre beta ni producción.

## Conciliación de alcance y criterios

Se revisaron los **17 identificadores originales**, sin renumerarlos:15rutas, una tarea y una entrada Beat, familiasI07/I08/I19. La [matriz final](evidencias/n08-disposiciones-finales-20261026.json) conserva el registro histórico y separa sus huellas de las fuentes actuales. La [auditoría de aceptación](evidencias/n08-aceptacion-verificacion-20261026.json) concilia ocho criterios, fuentes, resultados originales, correcciones y límites; no sustituye las pruebas por una revisión de código.

| Grupo / IDs | Evidencia y disposición | Límite |
| --- | --- | --- |
| Favoritos /3 | Lectura privada con páginas24, todas las páginas0/1/10/100, dueño/ajeno, revocado como placeholder persistido, NULL/revisión ajena denegados. Alta/baja conservan funciones/decoradores originales y testigos de replay, concurrencia, permisos y navegador. Contraste412 acepta sólo la optimización de lectura. | El recuento incluye favoritos no disponibles; ocultarlos no significa borrarlos. |
| Robots y sitemap /4 | Índice por candidatos, páginas100/101 reales, alternates/origen/idiomas/retirada, queries y límites; XML exacto en pares412 y diez regresiones originales actuales, incluidas tres navegaciones. Robots/índice/directorio conservan funciones AST. | No acredita millones de entradas, capacidad de producción ni latencia de navegador. |
| Documentos públicos /2 | Referencia410:202documentos sintéticos,0/1/10/100activos por idioma, orden/contexto/enlaces, inactivo/otro idioma404 y todas las columnas intactas tras GET. | Sin certificación jurídica ni contenido real de operador. |
| Pedido y detalle sintéticos /2 | Historial25 por todas las páginas0/1/10/26/100 separado de opciones0/1/10/100. Referencia415 y originales de precio snapshot, evento firmado, replay, consumo único, permisos, CSRF y carreras conciliados. | El formulario privado no promete toda la elegibilidad de compra: el servicio la revalida al escribir. Cien filas preparadas no son cien compras nativas. |
| Catálogo/versiones/editar/previsualizar /4 | Páginas50, productos0/1/10/51/100 y versiones1/10/51/100, ES/EN, NULLdistinto de cero, GETsin cambios. Diez POST nativos generan ocho auditorías; replay de publicación sin nuevo efecto; permisos revocados y originales26casos conservados. | Publicar una configuración no activa ventas ni concede promociones. |
| Autosubida y Beat /2 | Originales de cuota/ventana/lote100/carreras, más416:worker restringido prefork2,5SUCCESSreales con rolSQL, startup/replay separados y dos ticks nativos60s; revocado sin subida, estado editorial intacto y limpieza comprobada. | Sólo un hijo ejecutó tareas; caso nuevo con dos derechos, original101es funcional síncrono, no latencia worker100 ni capacidad/SLA. |

Los ocho criterios auditados son: cobertura17IDs; autoridad/retirada/exposición privada; conteos/orden/paginación/idiomas; idempotencia/auditoría/snapshots comerciales sin pagos reales; autosubida acotada y etapa asíncrona nativa; presupuestos y mediciones equivalentes; conservación de FAIL/SKIP y cadena de fuentes; aislamiento/limpieza/notificaciones sin ampliar alcance. No se ha identificado un defecto crítico abierto de acceso, exposición o pérdida de datos en este alcance aceptado. N09/N10 conservan sus responsabilidades generales de privacidad, retención y operación; N11 la regresión integrada y N15 el inventario final.

## Cambios y resultados preservados

El único cambio de aplicación N08 es [A2/412](412-n08-a2-resultado-contraste-por-lotes-20261026.md), ya integrado en0d7a3a3: hidratar y validar mediante `PublicationContext` nativo exclusivamente los objetos de la página de favoritos y del slice de sitemap. Se valida y renderiza la misma instancia; contexto nuevo por petición, sin cachear autoridad. Páginas0/1 conservan el camino original. Los demás handlers, decoradores, helpers, modelos, migraciones, settings y calendarios no cambian.

| Lote | Resultado original | Qué acredita |
| --- | --- | --- |
| A/410,004939-72f06ea0 |3PASS434,775sQA |300GET/50segmentos dentro322Clientglobal; referencia24/100/legal; SQLdebug descartado y contador global canónico. |
| A2/412,014812-0d85aaca |13PASS321,638sQA |72GETobjetivo pareados,118GETpropios dentro167Clientglobal; paridad completa y seis presupuestos411cumplidos, diez originales actuales. |
| B/415,030555-20d5ac97 |3PASS1FAIL82,271sQA |Tres casos comerciales válidos:396GET/66segmentos+30GETnegativos+10POST=436Clientpropios/globales. Cfalló antes de la fixture; el lote completo no es PASS. |
| C/416,031404-bfa5f7d6 |1PASS175,906sQA |Sólo el caso C corregido, cinco ejecuciones reales y dos ticks Beat; cero Client. No se repitió B. |

Son ejecuciones distintas; **no una batería integrada de20PASS**. Se añadieron diez casos explícitos entre cuatro instrumentos; A2también ejecutó diez originales ya existentes. Los77testigos históricos seleccionados de16módulos conservan sus resultados y fuentes; no son77ejecuciones nuevas ni87pruebas nuevas por sumar esas diez repetidas. La batería histórica amplia conserva su discrepancia de3833declarados/3829elementos reales,3FAILy129SKIP, y los puentes correctivos aceptados del contrato anterior.

El primer C comprobaba eager antes de que la fixture nativa lo habilitase. Se movió la misma aserción después de `setup`; sólo se repitió C. El original, su fallo y la fuente corregida se conservan. No hay corrección de aplicación B/C ni ganancia de QA atribuida al pasar de un lote a otro.

## Antes y después de rendimiento

Pared en milisegundos. Filas pareadas412: misma base/datos/estado/idioma y versiones de handler seleccionadas realmente, primera observación separada y mediana de cinco posteriores. Presupuestos anteriores al candidato:50%menos consultas,20%menos mediana de pared, sin aumento de CPUmediana; todos los seis objetivos y los controles pequeños cumplen. Las tablas completas de412conservan primera/rangos/CPU; RSSdel proceso observado≤318,383MiB frente a protección1GiB, no memoria por variante.

| Acción / estado | Mediana5 antes (ms) | Mediana5 después (ms) | Diferencia (ms) | Cambio | SQL antes→después |
| --- | ---: | ---: | ---: | ---: | --- |
| Favoritos100, página1, ES normal |2217,110|244,720|−1972,391|−88,962%|563→30|
| Favoritos100, página1, EN normal |2141,365|210,281|−1931,084|−90,180%|563→30|
| Favoritos100, página1, ES uno revocado |2034,547|222,085|−1812,462|−89,084%|546→30|
| Favoritos100, página1, EN uno revocado |2163,705|207,346|−1956,360|−90,417%|546→30|
| Sitemap100, normal |9009,700|375,775|−8633,925|−95,829%|2402→18|
| Sitemap100, uno revocado |9292,321|277,708|−9014,613|−97,011%|2385→18|

Para las superficies sin candidato nuevo no se inventa un después ni un porcentaje. Las referencias siguientes mantienen el código y separan poblaciones/estados/etapas; no se comparan causalmente contra412.

| Acción / escenario | Antes de otro candidato | Referencia actual (ms) | Después de otro candidato / mejora |
| --- | --- | --- | --- |
| Alta de favorito y replay, dos estados n1 en regresión412 |Sin par equivalente|106,023/102,949;42/39SQL|No medido / no evaluable|
| Baja propia de favorito, n1 en regresión412 |Sin par equivalente|19,207;12SQL|No medido / no evaluable|
| Robots desarrollo / índice vacío / directorio, n1 separados412 |Sin par equivalente|1,529 /58,395 /2,003|No medido / no evaluable|
| Índice legal100 ES/EN, mediana5,1SQL |Sin par equivalente|10,226/8,759|No medido / no evaluable|
| Detalle legal ES/EN con100activos, mediana5,1SQL |Sin par equivalente|2,982/3,466|No medido / no evaluable|
| Historial100 página1de25 ES/EN, mediana5,9SQL |Sin par equivalente|58,935/42,734|No medido / no evaluable|
| Detalle pedido ES/EN, mediana5,6SQL |Sin par equivalente|24,941/15,778|No medido / no evaluable|
| Formulario100anuncios /100productos ES/EN, mediana5,8SQL |Sin par equivalente|53,137/42,648 y44,543/52,704|No medido / no evaluable|
| Catálogo100 /versiones100 página1de50 ES/EN, mediana5 |Sin par equivalente|27,467/26,870 y53,613/40,944|No medido / no evaluable|
| Edición /vista previa borrador ES/EN, mediana5,8SQL |Sin par equivalente|27,502/25,224 y21,177/27,568|No medido / no evaluable|
| Tarea preencolada /replay /dos ticks Beat, n1por etapa |Sin par equivalente|397,838 /288,758 /233,881 /191,542|No medido / no evaluable|

Los tiempos del Client y de tarea no son transporte, navegador, tiempo humano ni latencia de proveedor. CPUde proceso/hilo no incluye PostgreSQL. La cola se documenta aparte en416:2860,428mscon arranque;9,226msreplay;17,444/8,009msBeat. La separación observada de ticks es59,971952s, no un SLA. No se suman observadores anidados ni se usan segundos de QAcomo latencia. Los tamaños, primeras observaciones, rangos y demás páginas están en los anexos originales, no sustituidos por esta selección resumida.

## Reproducibilidad, entrega y continuación

La conciliación comprueba1.507fuentes B16:1.498idénticas y nueve variantes de alcance ya aceptado. Entre A2/B/C coinciden631fuentes de aplicación/configuración/plantillas; Aprevio sólo difiere en los dos handlers contrastados. `person_queryset` es ASTidéntico al N01D pese al cambio del módulo `agencies.py` por el panel N06. Las fuentes nuevas B/C sólo añaden instrumentos de QA; ninguna migración o modificación de servicios existentes.

[Auditoría B](evidencias/n08-b-comercial-auditoria-20261026.json), [auditoría C](evidencias/n08-c-autosubida-auditoria-20261026.json), [manifiesto de entrega](evidencias/n08-bc-cierre-manifiesto-20261026.json) y [reproducción segura](evidencias/n08-bc-cierre-reproduccion-20261026.tar.gz). El paquete conserva fuentes, prerregistros, congelaciones, resultados sanitizados, fallo original y corrección, sin logs, comandos de pasos, credenciales ni salidas de sistema. Los paquetes previos410/412se conservan separados. El grafo final focal de este bloque se archiva antes del push; no sustituye la reconstrucción completa N15.

Se aplicaron `django-expert`, `django-reviewer` y `django-celery-expert` en sus ámbitos, conservando la revisión independiente de Codex. Las seis skills aparecen en el catálogo actual. Los MCP nuevos no exponen herramientas en esta sesión; no se afirma acceso ni conexión a base con credenciales descubiertas. El perfil Django dummy no acredita esquema real; la evidencia PostgreSQL procede del arnés desechable autorizado. Cambios laterales del usuario quedan fuera del commit propio salvo los cambios de seguimiento expresamente propios.

Se avanza a **N09: derechos, moderación, avisos y limpieza**, familiasI20/I21/I23/I25, coordinando N02/N07/N10. Mantener la decisión de no prolongar optimizaciones marginales con tiempos alfa aceptables. N11 conciliará la candidata integrada; N15 reconstruirá el grafo completo una vez antes del diferencial e inventario de relevo frontend, sin ejecutar la futura reescritura ni activar condiciones/proveedores/apertura.
