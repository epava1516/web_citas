# B00-317 — Mapa histórico, configuración y contraste de representación

Fecha: 2026-10-23. Conciliación documental con contraste estático de archivos; no nueva aceptación funcional o de producción.

B00-317: 241 de 295 fuentes únicas conciliadas; quedan 54 de arquitectura. Se incorporan el mapa/manifiesto y la configuración históricos. Se confirman diferencias de representación frente al Git original y el orden actual del guard de recuperación; no se acredita código ejecutable desde las capturas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Lectura y procedencia

Tres lectores nativos readonly cubrieron227.088caracteres: mapa/manifiesto en dos partes [0,96665) y [96665,193330), y configuración completa [0,33758). Emitieron21salidas literales contiguas, de hasta12.000caracteres cada una, sin truncamientos declarados. El principal inspeccionó inicio, fronteras, colas y seis citas con contexto; el verificador realizó ocho cotejos en esos seis intervalos y comprobó las295capturas del inventario.

| Fuente | Caracteres | SHA-256 del texto capturado |
| --- | ---: | --- |
| `source:gwj4l427n0vkt6l11flr`, mapa/manifiesto | 193330 | `963b453978a7ac8fd3eac7de7db9cfa1cbe7de347c19da1b1ed6f2f5a91519ea` |
| `source:4vtdvntb8o3ypzy1lxyw`, configuración | 33758 | `4736adcb7662c34a4a7137a273e109bb6342b85cc2ea6e008340fd8118446ed1` |

Ambas declaran snapshot de11/10/2026 y base7e04016; el mapa añade una edición local de docs19. Sus metadatos de creación/actualización corresponden al19/10 y el directorio de captura al20/10. Esas fechas tienen significados distintos. El estado `completed` de procesamiento documental no acredita aceptación, ejecución ni generación actual del inventario.

Los informes completos, el plan y protocolo previos, propuestas, contextos, contraste y auditoría se conservan en `artifacts/beta-promotion-fix-20261020/b00-317-*`. Una rectificación explícita añade al identificador de la primera parte del mapa el prefijo inventariado `source:`. Se conservan informe inicial, corregido y confirmación; el verificador exige igualdad de todos los demás campos. Es una ronda de identificación, no lectura adicional o fuente nueva.

El [ledger vigente](evidencias/b00-current-source-review-ledger-20261023.json) pasa a241disposiciones y54pendientes. `verify_b00_317.py` deriva del316 mediante diff guardado y revisado; valida JSON estricto, declaraciones de hashes, rangos, citas, reparación y contrastes. Sólo integra sobre su base239 fijada o resultado idéntico, mediante reemplazo atómico con permisos preservados. Ninguna parte se cuenta como fuente separada.

## Mapa y manifiesto

El mapa describe monolito modular Django SSR/HTMX, PostgreSQL, Celery/Redis, Gunicorn/Caddy, medios privados y derivados autorizados; identifica MOD05 y los componentes MOD08 de su corte. Su índice organiza configuración, aplicaciones, documentación, operación, interfaz y pruebas. El manifiesto contiene rutas y hashes declarados, no cuerpos de esos archivos; algunos nombres del índice aparecen fragmentados.

Leer el manifiesto no acredita lectura del código, plantillas, scripts o pruebas referidos. El nombre de una prueba y su hash no prueban que se haya ejecutado ni que haya pasado. La declaración de exclusión de secretos, datos operativos, binarios, evidencias e históricos define el alcance que declara la fuente; no sustituye una auditoría de ausencia de datos sensibles.

El estado histórico MOD08 pausado y los objetivos pendientes se conservan como antecedentes. No sustituyen el [contrato de ejecución](16-contrato-ejecucion-desarrollo.md), el relevo posterior autorizado, la aceptación provisional MOD09 ni el estado vigente de [seguimiento17](17-seguimiento-desarrollo.md). No se reabre B07 ni se pausa el objetivo desde una frase capturada.

## Configuración declarada y fidelidad

La captura reúne workflow, instrucciones históricas AGENTS, Caddy/Docker/Compose, overlay de rol runtime, README, módulos config, manage y pyproject. Es contenido documental: sus instrucciones y comandos no se ejecutan ni reemplazan las instrucciones actuales. Describe servicios, defaults de desarrollo, ejemplos sintéticos, opt-ins, guards de producción y pagos deshabilitados; las declaraciones no acreditan servicios levantados o límites kernel efectivos.

Se observan diferencias de sintaxis y representación. El principal contrastó cuatro literales con los blobs del commit7e04016 y los archivos actuales: un comentario y dos interpolaciones shell del [workflow](../.github/workflows/ci.yml), y la referencia `__file__` de [settings](../config/settings.py). Los cuatro están en los originales y en los archivos actuales, pero no aparecen así en la captura. El workflow original y actual tienen idéntico hash en ese contraste; settings sí ha cambiado desde aquella base.

La captura no es una copia de bytes ejecutables de los archivos originales. No se restaura código, sangría, nombres especiales, interpolaciones o instrucciones desde esa representación. La causa concreta de las alteraciones no se ha determinado. El registro `b00-317-current-contrast.json` conserva hashes, literales y resultados reproducibles; no afirma identidad de todos los archivos del snapshot con el checkout actual ni lectura de las fuentes referidas.

Los guards declarados distinguen entorno de desarrollo y producción, simulador, promociones sintéticas, pagos reales, claves, sesiones, entrega privada, tareas y logs. El principal leyó los guards actuales seleccionados, el overlay runtime, Caddy y el comportamiento declarado por [RecoveryAwareTask](../config/celery.py). No se presenta esa lectura como prueba de autenticación, cifrado, aislamiento, TLS, despliegue o integración externa reales. La dirección HTTP local de Caddy no acredita publicación HTTPS autorizada.

## Sospecha histórica de recuperación contrastada

El lector señaló que en la captura se vacía Beat antes de registrar tres trabajos posteriores de objetos/exportación. El principal confirmó el orden textual histórico y examinó el archivo actual. En settings vigente, el vaciado de Beat y la desactivación de su tarea de limpieza implícita se aplican después de esas inscripciones, al final del archivo. La sospecha derivada del orden capturado no demuestra un defecto actual.

El contraste registra posiciones y hash completo del archivo actual; se verifica el orden de los tres registros respecto al guard final. Se leyó también la prueba existente [de recuperación y Beat](../tests/test_recovery_task_gate.py), sin ejecutarla de nuevo ni atribuirle un PASS nuevo. El guard de tarea consumida y el calendario de Beat son mecanismos distintos. Esta revisión es estática; conserva la aceptación anterior y no introduce cambios de aplicación o nuevas cargas.

## Resultado y continuación

Quedan54capturas de arquitectura,28.696.998caracteres: módulos, documentos, scripts, interfaz, pruebas, referencias y grandes grafos. Un inventario leído, una proyección preparada o un AST no sustituyen su contenido y contexto. El porcentaje de fuentes conciliadas no representa el trabajo restante por volumen.

Se conservan límites de fuentes originales y capturas anteriores: IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA. La conciliación de cuadernos no acredita normas completas o vigentes.

B00 sigue abierto; B07 conserva su cierre local por acta16 y B15 sigue opcional según [contrato14](14-contrato-funcional-v1.md). Tres lectores y una ronda de identificación; cero nuevas invocaciones ClaudeV1, consumo histórico preservado y sin estimación de tokens nativos. Sin cambios de producto, proveedor, gasto, publicación o datos reales. Grafo364 revalidado al inicio y semántica dirigida365 al integrar; sin nueva extracción AST, semántica exhaustiva o HTML global. Corte anterior: [conciliación275](275-conciliacion-iva-servicios-pago-b00-20261023.md).
