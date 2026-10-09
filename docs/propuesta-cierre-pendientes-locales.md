# Propuesta para cerrar los pendientes locales

Fecha: 2026-10-09. Solicitada por el usuario tras el saneamiento técnico y confirmada para preparar objetivos de capacidad. **Criterios técnicos locales fijados por Codex bajo delegación expresa; capacidad todavía sin medir.** No cambia porcentajes ni acredita gates o capacidad productiva. Estado y cola: [seguimiento17](17-seguimiento-desarrollo.md); requisitos: [matriz83](83-auditoria-pendientes-cr09.md).

Decisión posterior del usuario2026-10-09: «Delegar los objetivos técnicos». Codex elegirá y registrará los criterios definitivos del ensayo ajustados a recursos locales disponibles antes de medir; esta propuesta es referencia de diseño, sin exigir otra aprobación rutinaria. La delegación permite definir objetivos y continuar la verificación local pertinente; no aprueba capacidad desde cifras propuestas ni autoriza gasto, infraestructura ajena o publicación.

## Objetivos técnicos locales de expedientes grandes — fijados2026-10-09

Se fija una referencia local desechable con presupuesto conjunto máximo de4CPU,8GiB de RAM y20GiB de almacenamiento, PostgreSQL17 y Redis7.4 reales, Chromium y datos sintéticos. Inventario previo: host compartido de8CPU y23.204MiB de RAM,11.075MiB disponibles,98GB de disco libre; swap casi ocupada (4.072/4.095MiB). Hay margen nominal para el ensayo, pero se comprobará de nuevo antes de reservar recursos. Los límites deben abarcar aplicación, base, broker, navegador y generador mediante cgroups o límites equivalentes comprobables; nombres distintos de bases no son aislamiento de rendimiento. No modificar servicios normales ni contratar infraestructura. Si no hay margen, aplazar el ensayo y continuar tareas independientes; no reducir la población o elevar recursos para obtener PASS.

| Escenario fijado | Revisiones por expediente | JSON revisado | Imágenes revisadas | Concurrencia |
| --- | --- | --- | --- | --- |
| Control pequeño | 30 | Hasta 1 MiB | Hasta 8 MiB | 1 |
| Volumen histórico existente | 1.500 | Aproximadamente 10 MiB; registrar tamaño real | Hasta 64 MiB | 1 |
| Capacidad objetivo | 1.500 por expediente | Hasta 16 MiB por expediente | Hasta 64 MiB por expediente | 2 expedientes independientes |

En el escenario objetivo se alcanzan los límites de16MiB JSON y64MiB de imágenes por expediente (tolerancia de tamaño ±1% declarada antes del ensayo), con1.500 revisiones y dos cuentas/expedientes independientes activos a la vez; un fixture menor no acredita ese máximo. El JSON se mide como bytes UTF-8 del contenido exigible previo al empaquetado, imágenes como bytes originales retenidos, sin contar duplicados artificiales ni relleno ajeno al dominio. Registrar también tamaños de la copia entregable y paquetes. No rellenar límites truncando la fuente. Variar relaciones, longitudes, Unicode, decisiones por campo, imágenes y registros ajenos excluidos. Mantener asociaciones, autorización, revocación, revisión independiente sintética, hashes y cobertura completa de los datos exigibles. Identidades/proveedores simulados siguen identificados.

| Etapa | Límite fijado | Qué se mide |
| --- | --- | --- |
| Preparar selección y cobertura | 60 s por operación | Tiempo servidor completo; registrar consultas y cardinalidad |
| Abrir una página de revisión de hasta 50 filas | p95 ≤2 s | HTTP completo, al menos 20 aperturas tras preparación; primera apertura separada |
| Guardar o aprobar una página de revisión | p95 ≤5 s | HTTP completo; excluir tiempo humano y conservar comprobaciones globales necesarias |
| Generar la entrega revisada | 120 s | Tiempo servidor completo; registrar JSON, imágenes y paquetes producidos |
| Emitir respuesta final y cerrar | 30 s por operación | Tiempo servidor completo con revalidación y auditoría |
| Descargar un paquete de hasta 8 MiB | p95 ≤5 s | TCP local, al menos 20 descargas autorizadas con cliente que consume todo el cuerpo |
| Memoria de cada proceso de aplicación participante | RSS máximo ≤1 GiB | Muestreo de RSS durante todas las etapas; registrar también pico Python por separado |
| Memoria del entorno desechable completo | Máximo ≤6 GiB | Agregado de contenedores y procesos propios, sin contar servicios ajenos |

Estos límites son objetivos técnicos locales elegidos por Codex para un proyecto nuevo, no una obligación jurídica, previsión comercial o promesa de mejora. TCP local no acredita Internet. Preparación/generación completas pueden requerir operaciones asíncronas o revisión paginada si las mediciones demuestran incumplimiento; no adoptar esas soluciones antes del diagnóstico.

Secuencia fijada: comprobar recursos disponibles y aplicar límites → reproducir primero la etapa costosa con fixture pequeño → medir una pasada de referencia grande → corregir el mecanismo demostrado → comparar equivalencia y coste en las mismas condiciones → ejecutar el recorrido completo con dos expedientes. Para cada variante y cada expediente deben cumplirse los límites; no mezclar muestras del control pequeño con las del escenario objetivo. Usar p95 por rango más próximo y al menos20 operaciones por etapa que exige percentil; primera apertura separada. Los paquetes mayores de8MiB requieren partición íntegra o un ensayo adicional explícito, nunca truncamiento. Medir el agregado de memoria mediante cgroups disjuntos (incluye caché), evitando sumar de nuevo procesos ya contenidos; RSS de aplicación también se registra individualmente. Prefijar comandos, huellas, selección, tiempos máximos de ejecución y limpieza en seguimiento17 antes de lanzar cargas. Estos criterios ya están definidos por delegación; no requieren otra aprobación rutinaria. Una cifra incumplida produce FAIL de su escenario; un instrumento o fixture inválido produce INVALID. No sumarlos como aceptación integral.

La prueba existente de 1.500 revisiones conserva su resultado histórico, cercano a 89 minutos para el recorrido. No volver a ejecutarla por rutina ni confundir generación instrumentada con tiempo total. Los límites nuevos requieren medición propia; el SLO de 800 ms del directorio público no se aplica a estos expedientes.

## Insumos operativos para revisar

Conforme al contrato 16 v1.6, Codex puede definir fixtures y configuraciones ordinarias de ensayo, contrastarlas con código e implementar diferencias técnicas. La tabla siguiente enumera decisiones productivas reales del titular/revisores; no son prerrequisitos de verificar sus mecanismos locales con casos sintéticos. No se inventan ni se dan por aprobadas para completar un gate productivo.

| Entrada | Entregable que debe quedar decidido |
| --- | --- |
| Censo e identidad | Inventario por origen y corte, asociación al sujeto, huella, formato, período, decisiones de divulgación y revisor; procedimiento de identidad/representación y fallos admitidos |
| Conservación | Política por finalidad y artefacto, fundamento, inicio/duración, excepciones, backups y autoridad de destrucción |
| Restauración | Entorno real, inventario/custodio y acta; comprobar allí objetivos de diseño RPO 1 h/RTO 8 h de docs14 §10 o registrar su cambio autorizado |
| Comunicaciones | Destinatario/rol/canal por derecho, contenido mínimo, acuse, fallos/reintentos y efecto sobre cierre |
| Urgencias | Responsable/suplente, cobertura, prioridad, canal, plazo operativo, autoridad de resolución y simulacro |
| Seguridad independiente | Revisor, alcance, criterios, informe y remediaciones verificadas |

Los procedimientos y cuentas de prueba sintéticos deben ser explícitos, con roles de autor/revisor separados cuando lo exige la aplicación. Esa verificación acredita sus mecanismos en el alcance técnico probado; no acredita operación real o aprobación jurídica independiente. La matriz83 separa los requisitos exactos de ambos cierres.

## CI y regresión común

**Decisión posterior del usuario:** gestionar CI nosotros, sin presupuesto para alojamiento. El [gate local reproducible](ci-local.md) sustituye el requisito de un entorno CI alojado; GitHub queda solo manual. El bloqueo de cuenta descrito abajo es histórico. N3 conserva sus criterios técnicos locales; revisión independiente externa sigue exigida antes de producción.

Diagnóstico histórico: acceso de lectura verificado; [ejecución37874402205](https://github.com/epava1516/web_citas/actions/runs/37874402205), sobre `2e4f6b64e15b68f70a5298ec401fb9b94a658642`, falló antes de asignar runner/pasos. La anotación señala pagos fallidos o límite de gasto, sin distinguir causa exacta. CI propio elimina esa dependencia; no se modificaron pagos/límites/plan/runners ni se exige resolverlos ahora.

La [anotación original de GitHub](evidencias/ci-bloqueo-cuenta-20261009.json) conserva la causa y el aviso separado sobre la futura imagen del runner. El workflow local incorpora PostgreSQL/Redis, herramientas nativas fijadas por commit, Chromium y conservación de JUnit/manifest nativo incluso ante fallo. Esta configuración no está publicada ni ejecutada externamente. El informe de pytest incluye propiedades de medición con formato xunit1; los artefactos se conservan 14 días propuestos.

La suite de 2.085 casos incluye carga contractual 900 s, recorrido grande histórico y experimentos optativos con variables explícitas. Su colección no acredita ejecución ni experimentos omitidos. Antes de regresión completa registrar cargas autorizadas, exclusiones/skips y recursos/condición de salida. N3 sigue pendiente de sus requisitos locales; CI propio es el entorno autorizado y una ejecución reducida no acredita batería integral.

Si en el futuro se eligiera CI externo, haría falta resolver su bloqueo y autorizar la publicación. La opción vigente es CI propio local, sin esas dependencias. Codex asume ejecución, diagnóstico y trazabilidad dentro del alcance autorizado.
