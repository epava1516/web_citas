# Diagnóstico de proyección SQL de etiquetas comerciales

Fecha:2026-10-20. Estado: diez casos PASS auditados; reducción SQL y paridad comprobadas; contraste129 rechaza adopción, producto intacto. B07–B09 pendientes; cortoTCPFAIL y900s bloqueado. Continúa la decisión de [127](127-diagnostico-orden-global-derechos-beta-20261020.md).

## Hipótesis y límites

El helper comercial ya calcula promotions(UUID→Premium/Top) en el mismo snapshot que el orden. Después el SELECT recupera _promotion_priority medianteCASE sobre posiciónJSON para volver a construir esas etiquetas. Comprobar si ese SELECT repite el mapaJSON y si seleccionar sólo IDs permite reducir parametrización manteniendo orden. Es una hipótesis de estructura SQL: no ahorro HTTP demostrado. El perfil previo sólo registra2–3ms propios globales dejson.iterencode y el plan de página aplicaResult a24filas; no afirmar evaluar todas las condiciones en10000filas ni sumar inclusivos para prometer10%.

Copia experimental de _snapshot_order_population y _state_page, fijadas porSHA de sus módulos. Conservar consulta original de derechos filtrados, iterator500, UUID, cálculo/rotación, población, conteo y guarda nativa. Adjuntar el diccionario existente al QuerySet final después deorder_by, exclusivamente como dato de la petición. La página propiaRR lee ese atributo antes de clonar y selecciona sólo identificadores; limita etiquetas aIDs seleccionados. Mapa vacío es distinto de ausencia. Callback sin atributo e aislamiento heredado conservan prioridadSQL. Mantener _promotion_priority para consumidores existentes. Sin COUNT adicional, derechos globales, caché persistente, nuevas cuotas o cambio de servidor.

Riesgos: prolongar la vida del diccionario hasta finalizar la página puede aumentar pico de memoria; atributos privados se pierden al clonar QuerySet; mezcla de claves UUID/texto o lectura fuera del snapshot rompería etiquetas. No adoptar sin paridad y coste/memoria. No mover autoridad a datos de otra petición ni omitir la guarda nativa.

## Protocolo inicial prefijado

Instrumento separado tests/beta_promotion_label_projection_diagnostic.py, explícito y fuera de colección ordinaria. Dos casos de formaSQL (Premium y sóloautobump, este último con mapa vacío pero presente), cada uno sobre poblaciónListing yPublicationState. Comparar SELECTprioridad original frenteIDs planos: número de jsonb_extract_path_text, número de parámetrosJsonb y bytesJSON agregados deben reducirse estrictamente y seguir positivos; verificar orden y etiquetas. Los bytes son carga de parámetros, no ancho de banda TCP medido. No conservar SQL ni UUID en el resumen público.

Luego HTTPoriginal/candidato con misma fixture debe tener200, ruta state, bytes y patrocinio idénticos. El observador del helper debe demostrar atributo presente con1etiquetaPremium o0autobump; ausencia no sustituye ese último caso.

Ocho testigos adicionales reutilizan comprobaciones contra referencia nativa congelada/todas las páginas49, revocaciones individual/propietario/editor, frontera concurrente entre peticiones, checkedpendienteESEN y transacción heredada. Total10nodeids nuevos en una ejecución focal, un worker, PostgreSQL/Redis propios, snapshotfixture/broker aislado y ninguna otra integración. Los testigos se ejecutan con ambas funciones experimentales; no reclamar los nueve del candidato global127 como prueba de este cambio diferente.

Auditoría terminal de10nodeids exactos/fases, propiedades de ambas formasSQL, SHAactual==freeze,622producto idéntico, ausencia de recursos/PID y Telegram confirmado. Un fallo preserva negativo y exige diagnóstico antes de repetir. No iniciar ROI10k niTCP desde el simple PASS de integridad.

Sólo tras comprobar la reducción y paridad, valorar protocolo causal separado con umbrales111/112 y memoria observada, sobre fuente única. Hasta entonces no hay mejora de rendimiento acreditada, aplicación de producto ni cierre B07–B09/beta.


## Resultado auditado y siguiente comprobación

220121-9c5b3e67:10PASS/0FAIL/0ERROR/0SKIP,117,259sJUnit. La [auditoría terminal](evidencias/beta-label-projection-terminal-audit-20261020.json) confirma diez nodeids exactos, fases, hash único de candidata, fuentes/product622idénticos, limpieza/PID/Telegram y las cuatro formasSQL. Premium/autobump sobreListing/PublicationState: mapasJsonb3→1, expresionesJSON3→1 y126→42bytes para el único derecho sintético del caso. No extrapolar esos42bytes a2000derechos, ni llamar a esa reducción ahorroHTTP. Cuerpos/páginas/etiquetas y los ocho testigos nativos/privados pasan en el alcance prefijado.

No cambio de producto ni ROI demostrado. El siguiente contraste está prerregistrado en [129](129-contraste-proyeccion-etiquetas-beta-20261020.md), con controles limpios A/A/C y observaciones de memoria separadas.


Resultado posterior129: candidata no elegible; reducciónSQLno acredita mejoraHTTP. Se conserva este PASS de paridad, sin transformarlo en aceptación del cambio. Véase129 y su auditoría de152lecturas.
