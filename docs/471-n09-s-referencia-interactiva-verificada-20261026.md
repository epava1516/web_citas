# N09S — referencia normal de servicios interactivos verificada

Estado: referencia finita aceptada localmente. No hay candidata ni cambio de producto en este lote. Base `bdb74d9`; [prerregistro470](470-n09-s-prerregistro-referencia-interactiva-20261026.md). La suficiencia y disposición completa de N09 se decide por separado en [472](472-n09-aceptacion-local-derechos-avisos-limpieza-20261026.md).

Run `20261026-194756-e6af8904`: **3 PASS, cero FAIL/ERROR/SKIP, 85,223 s JUnit de QA**. Tres recorridos nativos, 66 observaciones y 16 grupos de etapa exactamente; 1.787 huellas estables. Runner oficial focused serial, PostgreSQL/Redis desechables propios y parser nativo local limpio. No se repitieron las campañas A–R. Auditoría posterior independiente de selección, métricas, oráculos, fuente/documentos/grafo, recursos retirados y Telegram PASS entregado.

## Referencia de máquina y comparación

La primera observación es independiente de las cinco siguientes. Sólo GET y replay tienen cinco seguimientos con trabajo/estado homogéneo; una operación nueva con efectos tiene una observación. Estos valores no son el tiempo de preparación, revisión humana o QA.

| Etapa | Primera pared, ms | Mediana siguientes 5, ms | Rango siguientes 5, ms | SQL primera / siguientes | Después, otra candidata |
| --- | ---: | ---: | --- | --- | --- |
| rights_queue_es | 155.940 | 21.264 | 18.855–33.687 | 7 / 7 | Sin candidata |
| rights_queue_en | 22.520 | 22.107 | 19.228–26.356 | 7 / 7 | Sin candidata |
| processing_inspect_new | 328.939 | — | N=1 | 122 / — | Sin candidata |
| processing_inspect_replay | 261.627 | 332.336 | 274.144–478.900 | 113 / 113 | Sin candidata |
| processing_review_new | 435.734 | — | N=1 | 124 / — | Sin candidata |
| processing_review_replay | 310.970 | 391.356 | 298.513–446.836 | 112 / 112 | Sin candidata |
| rectification_source_preview | 319.279 | — | N=1 | 123 / — | Sin candidata |
| rectification_proposal_inspect | 461.220 | — | N=1 | 163 / — | Sin candidata |
| rectification_review_new | 655.886 | — | N=1 | 222 / — | Sin candidata |
| rectification_review_replay | 98.232 | 97.955 | 63.403–102.280 | 24 / 24 | Sin candidata |
| complaint_queue_open_es | 44.018 | 45.707 | 40.227–50.526 | 12 / 12 | Sin candidata |
| complaint_queue_open_en | 34.908 | 29.269 | 26.099–34.074 | 12 / 12 | Sin candidata |
| complaint_resolve_new | 86.576 | — | N=1 | 26 / — | Sin candidata |
| complaint_resolve_replay | 45.994 | 40.816 | 32.914–50.587 | 15 / 15 | Sin candidata |
| complaint_queue_resolved_es | 32.969 | 22.303 | 21.884–30.587 | 7 / 7 | Sin candidata |
| complaint_queue_resolved_en | 25.780 | 24.621 | 23.684–26.496 | 7 / 7 | Sin candidata |

Antes del lote no había una base normal equivalente inspeccionada para estas etapas; ahora existe esta referencia del producto vigente. No hay segundo producto medido ni porcentaje de mejora. Creación y replay son operaciones distintas: sus tiempos no se comparan como una optimización. Tampoco se suman CPU, SQL y pared como componentes disjuntos, porque se solapan. Los contadores de consultas permanecen visibles —hasta 222 en la aprobación nueva de rectificación—; no se ha demostrado aquí un incumplimiento que justifique modificar las guardas y transacciones. Se conserva la aplicación y no se abre una campaña marginal.

El archivo de evidencia conserva por observación pared, CPU del proceso y SQL observado, estado/bytes donde se midió Client, cinco seguimientos y recursos. La CPU Python no es la de PostgreSQL. El driver puede no exponer BEGIN/COMMIT en execute_wrapper. Los primeros tiempos ya tienen componentes calentados por fixtures; no son caché fría. Host observado x86_64, 8 CPU lógicas, MemTotal 23.760.928 KiB; sin aislamiento de carga ni cuotas cgroup identificadas por las rutas disponibles. Sobrecoste del observador no cuantificado, sin p95/p99 o SLA.

## Oráculos e integridad

Cada caso comparó filas de **173 modelos instalados**, incluidas relaciones automáticas, permisos y sesiones. Sólo se aceptaron PK nuevas exactas y los campos concretos del único padre que debe cambiar; ninguna tabla completa se excluyó. Los ocho archivos de la cohorte conservaron contenido, tamaño, mtime y modo. Los snapshots completos se procesaron localmente; sólo salen métricas y hashes.

- Procesamiento: un nuevo Action+Read y un nuevo Action+Review, firmas/FK/prueba/digests/fechas exactos, mismo cuerpo autorizado en inspección y replay; aprobación independiente. Repeticiones misma PK y cero escrituras; padres y datos de cuenta intactos.
- Rectificación: un SourceRead y un ProposalRead con la propuesta de alias exacta; aprobación añade Action+Review y sólo cambia version+1/scope_status unverified del expediente. No ejecuta la corrección ni modifica el perfil/publicación. Replay con clave y versión originales devuelve la misma revisión sin efectos.
- Reclamación: upheld añade Action+Resolution+Notice queued con cero intentos, sin enviar nada; sólo status resolved/version+1 del expediente. Cuerpo y destinatario sintéticos verificados localmente, fuente y publicación intactas. Replay sin segundo efecto; la cola ES/EN deja de mostrar el expediente resuelto.

Los GET ES/EN comprobaron idioma efectivo de la petición y Content-Language, encabezado real, estado 200, private/no-store y noindex/nofollow, IDs/orden esperados y cero cambios duraderos por grupo. Son handlers Client, no transporte por proxy o navegador. Los servicios se llamaron realmente sin sustituir callables; creación/validación/materialización/cifrado de la aplicación están dentro de la ventana medida. Preparación nativa, inspección previa necesaria, serialización de oráculos y snapshots quedan fuera.

## Custodia y límites

[Archivo compacto](evidencias/n09-s-referencia-interactiva-20261026.tar.gz): 13 entradas, 22082 bytes, SHA-256 `b31027ddb37cedc73e965a2d69c880ebb048c69662cd1d02cf2c09904225fdc1`. Incluye instrumento, protocolo, auditoría y métricas, revisión propia/propuesta nativa, identidades seleccionadas y resultado saneado. Excluye logs crudos, SQL/parámetros, valores privados, credenciales, cambios laterales y grafo completo.

Limitación de identidad: reference-freeze conserva fuentes/documentos/grafo antes del lanzamiento, pero no incluía los IDs inmutables de las imágenes. La raíz los observó en los contenedores propios mientras estaban vivos: PostgreSQL `sha256:ab20e934b27ba3ff927c1b4c9ff8cf6c32f315f743efe68dd3441182a87fb085`, Redis `sha256:f84b0c4678011602b9b98c227a4dcd5468bf8b088b02fdd4165cb7758bad8058`. El runner usó --pull=never; no atribuir esa observación al fichero de congelación previo ni afirmar un prerregistro perfecto o comparación A/B de imágenes. Se acepta esta referencia actual acotada con identidades reales observadas; no se repite QA válida por esa aclaración.

Corte anterior al run: 2.120 fuentes, 20.851 nodos, 85.815 relaciones, 1.022 comunidades; SHA-256 `781fa84d02edf6a9f9b508f3ec6f524c0a5416e88f4e7c9b7287c9efe7426523`. Un AST de instrumento y semántica selectiva470/17, no reconstrucción N15 ni semántica exhaustiva. Tokens nativos desconocidos; V1nuevo0/histórico8 preservado. Revisión root de 502 líneas y servicios/modelos nativos, Ruff PASS; el escritor no ejecutó pruebas ni modificó producto.

Un expediente por cohorte no mide crecimiento del histórico. Derechos materializa elegibles antes de Paginator50 y reclamaciones toma 100 candidatos antes de permitted; no se acredita coste global acotado, equidad de un histórico mayor o rendimiento de cada ruta del censo. No worker/Beat, entrega externa, juicio humano, apertura o preparación de producción. Los presupuestos públicos y FAIL/objetivos2s/5s de MOD09 conservan su ámbito; no se aplican a estas muestras privadas.
