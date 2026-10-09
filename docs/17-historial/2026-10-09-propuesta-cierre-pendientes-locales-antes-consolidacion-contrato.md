# Propuesta para cerrar los pendientes locales

Fecha: 2026-10-09. Solicitada por el usuario tras el saneamiento técnico y confirmada para preparar objetivos de capacidad. **Propuesta para revisión; sus cifras no son objetivos aceptados ni resultados medidos.** No cambia contratos, porcentajes o gates. Estado y cola: [seguimiento17](17-seguimiento-desarrollo.md); requisitos: [matriz83](83-auditoria-pendientes-cr09.md).

## Capacidad de expedientes grandes

Proponer una referencia local desechable de 4 CPU, 8 GiB de RAM y 20 GiB de almacenamiento, con PostgreSQL17 y Redis7.4 reales, navegador Chromium y datos exclusivamente sintéticos. Son recursos propuestos para el entorno completo; comprobar disponibilidad antes de reservarlos. No aumentar recursos de servicios normales ni contratar infraestructura.

| Escenario propuesto | Revisiones por expediente | JSON revisado | Imágenes revisadas | Concurrencia |
| --- | --- | --- | --- | --- |
| Control pequeño | 30 | Hasta 1 MiB | Hasta 8 MiB | 1 |
| Volumen histórico existente | 1.500 | Aproximadamente 10 MiB; registrar tamaño real | Hasta 64 MiB | 1 |
| Capacidad objetivo | 1.500 por expediente | Hasta 16 MiB por expediente | Hasta 64 MiB por expediente | 2 expedientes independientes |

No rellenar límites truncando la fuente. Variar relaciones, longitudes, Unicode, decisiones por campo, imágenes y registros ajenos excluidos. Mantener asociaciones, autorización, revocación, revisión independiente sintética, hashes y cobertura completa de los datos exigibles. Identidades/proveedores simulados siguen identificados.

| Etapa | Límite propuesto | Qué se mide |
| --- | --- | --- |
| Preparar selección y cobertura | 60 s por operación | Tiempo servidor completo; registrar consultas y cardinalidad |
| Abrir una página de revisión de hasta 50 filas | p95 ≤2 s | HTTP completo, al menos 20 aperturas tras preparación; primera apertura separada |
| Guardar o aprobar una página de revisión | p95 ≤5 s | HTTP completo; excluir tiempo humano y conservar comprobaciones globales necesarias |
| Generar la entrega revisada | 120 s | Tiempo servidor completo; registrar JSON, imágenes y paquetes producidos |
| Emitir respuesta final y cerrar | 30 s por operación | Tiempo servidor completo con revalidación y auditoría |
| Descargar un paquete de hasta 8 MiB | p95 ≤5 s | TCP local, al menos 20 descargas autorizadas con cliente que consume todo el cuerpo |
| Memoria de cada proceso de aplicación participante | RSS máximo ≤1 GiB | Muestreo de RSS durante todas las etapas; registrar también pico Python por separado |
| Memoria del entorno desechable completo | Máximo ≤6 GiB | Agregado de contenedores y procesos propios, sin contar servicios ajenos |

Estos límites son una hipótesis operativa para un proyecto nuevo, no una obligación jurídica, previsión comercial o promesa de mejora. TCP local no acredita Internet. Preparación/generación completas pueden requerir operaciones asíncronas o revisión paginada si las mediciones demuestran incumplimiento; no adoptar esas soluciones antes del diagnóstico.

Secuencia propuesta: aprobar alcance y cifras → inventariar recursos disponibles → reproducir primero la etapa costosa con fixture pequeño → medir una pasada de referencia grande → corregir el mecanismo demostrado → comparar equivalencia y coste en las mismas condiciones → ejecutar el recorrido completo con dos expedientes. Prefijar comandos, huellas, selección, tiempos máximos de ejecución y limpieza en seguimiento17 antes de lanzar cargas. Una cifra incumplida produce FAIL de su escenario; un instrumento o fixture inválido produce INVALID. No sumarlos como aceptación integral.

La prueba existente de 1.500 revisiones conserva su resultado histórico, cercano a 89 minutos para el recorrido. No volver a ejecutarla por rutina ni confundir generación instrumentada con tiempo total. Los límites nuevos requieren medición propia; el SLO de 800 ms del directorio público no se aplica a estos expedientes.

## Insumos operativos para revisar

Codex puede preparar formularios, contrastar decisiones con el código e implementar diferencias. Las decisiones de autoridad corresponden al titular y a los revisores pertinentes; no se inventan para completar un gate.

| Entrada | Entregable que debe quedar decidido |
| --- | --- |
| Censo e identidad | Inventario por origen y corte, asociación al sujeto, huella, formato, período, decisiones de divulgación y revisor; procedimiento de identidad/representación y fallos admitidos |
| Conservación | Política por finalidad y artefacto, fundamento, inicio/duración, excepciones, backups y autoridad de destrucción |
| Restauración | Entorno, inventario/custodio de backups, RPO/RTO numéricos y acta requerida |
| Comunicaciones | Destinatario/rol/canal por derecho, contenido mínimo, acuse, fallos/reintentos y efecto sobre cierre |
| Urgencias | Responsable/suplente, cobertura, prioridad, canal, plazo operativo, autoridad de resolución y simulacro |
| Seguridad independiente | Revisor, alcance, criterios, informe y remediaciones verificadas |

En esta fase pueden acordarse procedimientos y personas de prueba sintéticos para verificar la entrega local. Esa verificación no acredita operación real ni aprobación jurídica independiente. La matriz83 conserva los requisitos exactos de cierre.

## CI y regresión común

**Decisión posterior del usuario:** gestionar CI nosotros, sin presupuesto para alojamiento. El [gate local reproducible](ci-local.md) sustituye el requisito de un entorno CI alojado; GitHub queda solo manual. El bloqueo de cuenta descrito abajo se conserva como diagnóstico histórico, sin exigir resolver facturación ni publicar para verificar localmente. N3 y seguridad independiente conservan los demás prerrequisitos.

Acceso de lectura a GitHub verificado. La ejecución [37874402205](https://github.com/epava1516/web_citas/actions/runs/37874402205), sobre `2e4f6b64e15b68f70a5298ec401fb9b94a658642`, falló antes de asignar runner o iniciar pasos. GitHub informa de pagos recientes fallidos o necesidad de aumentar el límite de gasto; no permite distinguir esas dos causas desde la anotación. El titular debe revisar facturación. No se modificaron pagos, límites, plan o runners.

La [anotación original de GitHub](evidencias/ci-bloqueo-cuenta-20261009.json) conserva la causa y el aviso separado sobre la futura imagen del runner. El workflow local incorpora PostgreSQL/Redis, herramientas nativas fijadas por commit, Chromium y conservación de JUnit/manifest nativo incluso ante fallo. Esta configuración no está publicada ni ejecutada externamente. El informe de pytest incluye propiedades de medición con formato xunit1; los artefactos se conservan 14 días propuestos.

La suite de 2.085 casos incluye carga contractual de 900 s, el recorrido grande histórico y experimentos optativos sujetos a variables explícitas. Su mera colección no es una ejecución ni acredita experimentos omitidos. Antes de lanzar la regresión completa, registrar qué cargas quedan autorizadas, cada exclusión/skip y recursos/condición de salida. N3 sigue pendiente hasta sus requisitos contractuales; un resultado local no sustituye CI externo.

Si en el futuro se eligiera CI externo, haría falta resolver su bloqueo y autorizar la publicación. La opción vigente es CI propio local, sin esas dependencias. Codex asume ejecución, diagnóstico y trazabilidad dentro del alcance autorizado.
