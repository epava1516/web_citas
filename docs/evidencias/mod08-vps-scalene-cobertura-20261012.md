# MOD-08: diagnóstico Scalene de cobertura en VPS

SHA `8af315a04475485a1bcf8c97f664cca3321d3f1a`; ejecución
`20261012-095117-11c3b82a`, Python 3.12.15, Scalene 2.3.0,
8 CPU con límites existentes, PostgreSQL y datos sintéticos propios.

| Evidencia | Diagnose anterior 568ff53 | Diagnose actual 8af315a |
| --- | --- | --- |
| Resultado runner | ERROR | PROFILE_DIAGNOSTIC_NOT_CAPACITY |
| Duración JUnit | 1583.477s | 1566.464s |
| Fallos / errores JUnit | 0 / 0 | 0 / 0 |
| Capturas coverage completas | 2 | 2 |
| JSON combinado | Ausente | Presente y validado |
| Nueva medida p95 sin perfilador | Ninguna | Ninguna |

La duración diagnóstica no compara rendimiento: cambió el cierre del
instrumento. Auditoría independiente: 1414 fuentes idénticas durante la prueba,
memoria propia conservadora 2920894464 bytes bajo 6 GiB, archivo sin problemas,
contenedores/red/volumen propios ausentes tras limpieza. Launcher exit 0.

La salida combina las ventanas temprana y tardía; no separa sus porcentajes.
Las mayores atribuciones por archivo son rights_copy_revision_batches (14.07%),
crypto (11.24%), evidence_chain (8.89%), rights_portability_review (8.14%) y
rights_exports (7.12%). Incluyen categorías Python, nativa y sistema;
no equivalen a porcentajes exclusivos de CPU ni del tiempo total del ensayo.
No identifican por sí solas una causa única. La lectura de originales y las
consultas/materialización deben contrastarse con los perfiles previos y el
código, preservando comprobaciones frescas y autorización.

[Evidencia compacta](mod08-vps-scalene-cobertura-20261012.json).
Los registros privados completos permanecen en artifacts/ sin versionar.
Siguiente: analizar puntos concretos y comprobar una corrección justificada;
medir HTTP sin perfiladores después. No hay aceptación global/N3.
