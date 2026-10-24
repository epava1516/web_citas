# B00-330 — Derechos, copias y comprobación vigente de supresión

Fecha: 2026-10-24. Conciliación semántica y corrección vigente de autorización temporal.

B00-330: 268 de 295 fuentes únicas conciliadas; quedan 27 de arquitectura. Se incorporan pruebas7–8 de rectificación, orígenes retenidos, denuncias, conservación y copias. Corregida supresión ordinaria con comprobación caducada tras lecturas: dos fallos reproducidos y35pruebas PostgreSQL aprobadas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Defecto reproducido y corrección

La corrección de [excepciones329](288-conciliacion-excepciones-recuperacion-b00-20261024.md) dejó una hipótesis acotada para la supresión ordinaria. `authorized_inventory` comprobaba la prueba antes de reconstruir la fuente; después `erasure_execution.execute` preparaba referencias de recuperación y creaba la acción sin volver a comprobar su vigencia. La recarga final del actor no sustituía la comprobación de identidad/ámbito.

La [nueva regresión](../tests/test_erasure_execution_freshness.py) construye el plan y los recursos reales de la fixture PostgreSQL. Avanza únicamente el reloj del consumidor de pruebas después de una lectura efectiva, en dos puntos: manifiesto de fuente y captura de referencias de recuperación. Los demás relojes y plazos mantienen su valor. Ambos negativos terminaron con DID NOT RAISE ValidationError; no hubo rechazo de la prueba caducada. Son intercalaciones controladas de reloj, no callbacks de proveedor o esperas concurrentes de caducidad observadas.

La corrección exige la misma prueba vigente vinculada al inventario después de esas lecturas y antes de crear RightsAction o aplicar efectos. Las dos variantes verifican que se conservan favoritos, versiones de expediente/privacidad/sesión/MFA y que no existen ejecución, acción de supresión o outbox nuevos. El replay válido de una ejecución ya completada conserva su recorrido. El consumidor de excepciones mantiene además su validación final propia, porque realiza trabajo adicional después del punto común.

| Ejecución | Resultado comprobado | Alcance |
| --- | --- | --- |
| `20261024-005741-2d9f96b6` | Dos FAIL esperados, cero errores/omisiones; runner ERROR | Código sin corregir, PostgreSQL17/Redis7.4 propios, dos workers pytest |
| `20261024-010117-d4160478` | 35PASS, cero fallos/errores/omisiones | Siete archivos, tres workers pytest; cuenta/perfil, HTTP/móvil, replay, revocaciones y excepciones |

[Auditoría de corrección](evidencias/b00-330-erasure-proof-freshness-20261024.json): JUnit y selección, hashes congelados iguales a los planes, resultado de cada gate y recibos terminales. La ausencia de los cuatro contenedores exactos y temporales se comprobó de forma independiente. Se conserva el negativo y la versión previa completa; la modificación propia añade import y guardia, preservando cambios anteriores. Sin migraciones, nueva carga, proveedor real o aceptación beta global.

## Lectura y procedencia

Seis lectores nativos de sólo lectura cubrieron645.204caracteres en seis partes y54emisiones literales contiguas de hasta12.000caracteres; máximo tres lectores simultáneos. Sin truncamientos o reparaciones delegadas declaradas. Los informes persistidos son extractos seleccionados marcados, no transcripciones completas. Cero nuevas invocaciones ClaudeV1; ocho históricas y consumo anterior conservados, sin estimación nativa.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Pruebas7/11 | `source:apxy4dmbaiiwrbw0nptv` | 321463 | [0,107154), [107154,214308), [214308,321463) |
| Pruebas8/11 | `source:wycwsasrapepcev5farj` | 323741 | [0,107913), [107913,215827), [215827,323741) |

SHA completos: `2114032a3d6c3caab66e809003059d897b75a9db422448ab362bb73b1e100bdb` y `b3865634ea827d6e2968385cdc689a4a01e95ff0d93159afe92aaafdf74c4304`. Snapshot11/10/base7e04016, representación transformada con daños de formato; no son bytes ejecutables actuales ni lectura de imports o artefactos únicamente referidos.

El principal cotejó seis huellas de parte y doce citas declaradas, inspeccionó fronteras y contextos. El verificador efectuó catorce cotejos sobre esos doce intervalos, verificó uniones completas y revalidó integridad de las295capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de266a268disposiciones y de29a27pendientes, con base266fijada, reemplazo atómico y permisos conservados. La aceptación de disposición exige además auditoría2FAIL/35PASS. Artefactos: `artifacts/beta-promotion-fix-20261020/b00-330-*`.

El primer verificador generado cambió por error la constante del corpus de295a275 al sustituir el prefijo numérico de pendientes29→27. Falló antes de modificar el ledger, cuya huella se comprobó intacta. Se restauró el invariante explícito de295 y el verificador corregido pasó. Se conserva el recibo EXIT1 y la corrección; ninguna prueba de producto se repitió por ese error auxiliar.

## Contenido conciliado y límites

La captura7 reúne revisión/ejecución de rectificación y receptores, cargas de reemplazo, orígenes Redis y sus proyecciones, reflow/contraste, denuncias y restricciones, recursos retenidos/RDB, conservación, revisiones y contabilidad de acceso. La captura8 cubre cobertura de acceso, evidencia y campos, proyección de destinatario, respuesta, ámbitos de cuenta, autoridad/asignación, comunicaciones, copias por páginas, información/política, empaquetado y reconstrucción.

Las pruebas preservan separación entre propuesta/revisión/notificación/recepción y ejecución, historial inmutable y borrador corregido sin publicación automática. Capturar un dispatch no acredita broker o worker; identidad y entrega simuladas conservan ese carácter. Una autorización de cuenta no concede acceso editorial a perfiles gestionados. La validación de evidencia histórica tampoco otorga autoridad actual para leerla o aprobarla.

Los orígenes retenidos y censos mantienen procedencia, cutoff y digests. Un parser que consume bytes completos o un censo sintético sin pendientes no prueba asociación semántica del sujeto o cobertura del servidor real. Metadatos AUX/físicos y declaraciones de operador tienen revisión y límites propios. Los tests de Redis y logs seleccionan ámbitos y excluyen datos privados; no convierten cobertura parcial en exhaustiva.

Los tests de reflow miden anchos CSS seleccionados, no zoom del navegador. Los cálculos de contraste conservan selectores no medidos y fondos/composiciones no soportados. Ninguna definición de Chromium/viewport constituye por sí sola ejecución o accesibilidad completa. El diagnóstico de recursos puede terminar con observaciones utilizables sin aceptar p95 o capacidad; sus límites de host compartido, instrumentación y eager siguen explícitos.

La contabilidad de acceso vincula campos, límites y referencias sin inventar approved/complete. Los paquetes de copia requieren decisiones vigentes, revisiones independientes y proyección minimizada. Acuse o estado reviewed_partial no equivalen a comunicación integral. Los ZIPs, fragmentos Unicode y reconstrucción privada tienen límites de tamaño/hash/orden propios; una prueba con umbral reducido o fuente sintética no acredita el escenario contractual combinado.

## Contraste actual y grafo

Once archivos actuales y veinticinco literales: diez módulos de pruebas y los bloques de autoridad del actor/comprobación final de `erasure_execution.py`. Se seleccionaron la nueva caducidad, revocación tras bloqueos, referencias de evidencia, privacidad de Redis, reconstrucción exclusiva0600, consulta privada de denuncias, caducidad de cargas, contabilidad sin aprobación, seguimiento de conservación y equivalencia de rutas pequeñas. Su presencia es evidencia estática; la nueva regresión35PASS es evidencia ejecutada separada y acotada. Las correctivas anteriores mantienen sus resultados propios sin crédito duplicado.

Grafo383 revalidado antes del análisis. AST dirigido del nuevo test antes del negativo y del módulo de ejecución corregido antes de la regresión, con sello previo a cada congelación. Integración semántica dirigida384; sin AST global, semántica exhaustiva o HTML global. Sin nueva capacidad o aceptación de la versión actual desde B07 por lectura de su acta.

Quedan27fuentes de arquitectura,20.979.887caracteres: pruebas9–11, interfaz, herramientas, referencias y grandes grafos. Conteos no son porcentaje de esfuerzo; continuar lectura y contraste vigente. B00 abierto, nueve de18puntos beta cerrados y B15 opcional. Se conservan límites legales y de producción; sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación288](288-conciliacion-excepciones-recuperacion-b00-20261024.md).
