# Diagnóstico del orden comercial global restringido a candidatos

Fecha:2026-10-20. Estado: paridad inicial8PASS y extremo selectivo1PASS auditados, nueve testigos conciliados; sin producto adoptado. B07–B09 pendientes; cortoTCPFAIL y900s bloqueado.

## Evidencia y mecanismo

La [conciliación del corto existente](evidencias/b07-existing-clean-tcp-reconciliation-20261020.json) vincula1200IDs HTTP200 con sus registros de servicio:400listado113,739s,400búsqueda116,071s y400detalle19,605s. Total249,414s/60s=4,157segundos de servicio ofrecidos por segundo, descriptivo con cuatro workers. Tiempos superpuestos: no son CPU ni una descomposición exacta de cola. Censo97muestras:94con0PublicationDirty y3con1;54pendientes eraHTTPen vuelo. No demuestra ausencia de todo transitorio entre muestras. No repetir el corto para medir una rama49sin evidencia de activación.

Perfil115651:33execute por ruta, FETCH excluido de sus tiempos. Planes calientes de derechos19–20ms son ejecución total, no coste aislado de pertenencia. El inclusivo comercial80–127ms no se suma con sus componentes. [111](111-contraste-materializacion-derechos-beta-20261020.md) y [112](112-contraste-materializacion-uuid-beta-20261020.md) siguen rechazados.

Hipótesis distinta: quitar sólo order__listing_id__in=population del fetch de live_entitlements en una copia experimental de _snapshot_order_population. Mantener iterator500, UUID, autoridad, instante, prioridades, hash diario, desempates, población SQL final, snapshot propio y guarda nativa. El orden total global restringido a candidatos debería preservar orden relativo y etiquetas aunque existan huecos. Premium sobreTop, bumps iguales y orgánicos requieren testigos; no es un beneficio demostrado.

Riesgo principal: los derechos globales pueden ser muchos más que la consulta estrecha. Transferencia, ordenación, mapaJSON y memoria podrían empeorar. No aplicar globalmente ni iniciar directamente un ROI10k basándose sólo en el corpus casi universal favorable. Revisión nativa de sólo lectura encontró plausible la semántica, sin autoridad de aceptación ni pruebas ejecutadas.

## Primer diagnóstico acotado

Instrumento explícito tests/beta_global_rights_parity_diagnostic.py, excluido de colección ordinaria por su nombre. Copia exactamente el helper fijadoSHA79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e y cambia sólo ese filtro. Sin cambios de producto. Reutiliza las comprobaciones existentes contra referencia nativa congelada, sin importar funciones con nombres coleccionables.

Ocho casos previstos: matriz completa49con derechos solapados, búsquedas/tipos y todas sus páginasESEN/dos días; tres revocaciones individual/propietario/editor; snapshot concurrente y siguiente petición; dos filtroschecked conmarca pendiente; transacción heredadaREADCOMMITTED. PostgreSQL/Redis propios, un worker, sin otra integración. Los casos son testigos de paridad y autoridad, no rendimiento. La transacción heredada debe seguir evitando el helper incluso experimental. No declarar bytes idénticos globales desde la comparación deIDs/etiquetas de la matriz.

Después del resultado: auditar fuentes congeladas/nodeids/fases/recursos/PID/Telegram. Antes de cualquier adopción o ROI costoso, ampliar extremos explícitos: sin patrocinados interiores con muchos exteriores; Premium/Top/bump exteriores y no publicables; marcas iguales y solapamientos; población muy selectiva con abundantes derechos exteriores. Medir cardinalidades, planes/FETCH y memoria separados de controles. No usar un PASS de ocho casos como cierre de todos esos extremos.

Sólo si ese diagnóstico justifica continuar, prerregistrar ROI A/A/C balanceado10000/2000 con controles limpios, mismos recursos y criterios111/112: A/A estable≤10%, mejora wall≥10% en ambas rutas, CPUapp/PG≤105% y4de6bloques no regresivos. Debe incluir además consulta selectiva y presupuesto de memoria antes de ejecutar. Ningún umbral se rebaja por obtener negativo. Sin cache persistente de autoridad, límites arbitrarios, cambio de cuotas o simulación de proveedores reales.


## Paridad inicial comprobada y extremo selectivo preparado

213833-09ff4c65:8PASS/0FAIL/0ERROR/0SKIP. La [auditoría terminal](evidencias/beta-global-rights-parity-terminal-audit-20261020.json) verifica los ocho nodeids exactos y tres fases, freeze/freshsource,622archivos de producto idénticos, limpieza/PID yTelegram. La auditoría se ejecutó tras salida real del runner. No se acredita rendimiento, memoria ni todos los extremos.

Nuevo caso explícito test_global_rights_outside_selective_population:50perfiles sintéticos en total,49de agencia y56derechos comerciales (12Premium/16Top/28autobump), con solapamientos y timestamps iguales por parejas. Dos anuncios se retiran y otros dos caducan después de emitir sus derechos; deben seguir existiendo derechos exteriores comercialmente vigentes. Se comparan seis cohortes (todos, vacío, sólo orgánicos, mixta, bumps+orgánicos y un solo orgánico), cada una con/sin búsqueda textual:12comparaciones. Población y derechos en la misma transacciónRRREADONLY; contrastar candidato y helper original con referencia nativa congelada por IDs, orden y etiquetas. Exigir cero derechos interiores y56globales en cohortes orgánicas/vacía. No confundir56derechos con56perfiles.

Ejecutar sólo ese nuevo nodeid, un worker y PostgreSQL/Redis propios. Los ocho previos no necesitan repetición por una función adicional sin efectos al importar: conservar su reutilización sólo si el prefijo de bytes previo a la nueva declaración reconstruye exactamente SHA del archivo en213833 y el resto de fuentes ejecutables sigue intacto, salvo libro/allowlist declarados. Esta conciliación no es una ejecución única de9casos. Si falla un criterio, ampliar la prueba afectada.

Este caso no mide aún el coste de56derechos frente a0interiores ni la memoria global grande. Cualquier ROI/adopción sigue condicionado al diagnóstico selectivo de cardinalidad/coste/memoria y sus presupuestos previos. No lanzar el contraste10k niTCP por lograr paridad únicamente.


### Negativo de preparación conservado

214436-5a76e4fa:0PASS/1FAIL/0ERROR/0SKIP,42,369sJUnit. La [auditoría negativa](evidencias/beta-global-rights-selective-first-negative-audit-20261020.json) confirma que el caso no llegó al orden: populate49incluye un perfil individual y deja48de agencia, frente49esperados. Fallo de preparación del instrumento, no evidencia de defecto del producto ni paridad negativa. Freeze/product622/limpieza/PID/Telegram confirmados antes de editar.

Corregir sólo prepare_population49→50 en la nueva función:50perfiles totales,49de agencia,56derechos previstos; no se debilita la aserción49 ni se elimina la cohorte de índice48. Repetir únicamente ese nodeid. Prefijo de los ocho casos anteriores sigue reconstruyendo su SHA exacto. Aún sin resultado del extremo ni coste/memoria/ROI.


## Extremo selectivo comprobado y decisión

215057-a1cc4608:1PASS/0FAIL/0ERROR/0SKIP,77,043sJUnit. La [auditoría](evidencias/beta-global-rights-selective-terminal-audit-20261020.json) confirma12comparaciones,56derechos globales, fuentes/product622/limpieza/PID/Telegram y reutilización estricta de los ocho iniciales mediante reconstrucciónSHA del prefijo y AST de una única declaración añadida. Conciliación9testigos (1nuevo+8reutilizados), nunca una ejecución única9PASS. El negativo de preparación permanece conservado.

Cohortes sin/con texto: todos45publicables/52derechos propios; vacía0/0; orgánica13/0; mixta8/11; bumps+orgánicos13/8; orgánico único1/0. Siempre56derechos globales. Orden/IDs/etiquetas idénticos al original y referencia nativa en cada comparación. No equivale a rendimiento medido: demuestra también la amplificación de cardinalidad en consultas con0derechos propios.

Se difiere la adopción global y el ROI10k: riesgo de trabajo ajeno a la consulta sin beneficio demostrado. El híbrido basado en COUNT tampoco se adopta: un conteo exacto adicional cuesta y global≤candidatos no garantiza pocos derechos exteriores. Son decisiones de diseño, no un benchmark negativo ni una prueba de regresión de latencia. Se conserva el filtro original y se prepara [128](128-diagnostico-proyeccion-etiquetas-beta-20261020.md), que evita ampliar derechos y comprueba otra hipótesis SQL acotada. Sin producto nuevo ni capacidad aceptada.
