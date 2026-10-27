# N11C — candidata de autorización de moderación e imágenes

Candidata aplicada, todavía no verificada ni aceptada. Base1d2703d,10/13 bloques, N11 abierto. Se conservan492/493 y sus negativos. [Registro de deuda](deuda-pendiente-viva.md) leído tras nueva anotación lateral; no se incorpora ni modifica con esta entrega.

## Evidencia original y separación de fallos

N11A20261026-234256-cf0028d1:1PASS3FAIL,66,291sQA,1798 fuentes estables. ControlListing válido, dos POSTrevocados302 con cambios, y controlMatch cuyo efecto no estaba completamente enumerado. Snapshots173modelos/archivos, esperasPGreales, cleanup y TelegramERRORsent. Diagnóstico fuente→espera→permiso fresco falso→efecto persistido contrastado, no propuesta.

N11B20261026-235019-b9ec9ed8: runner **INVALID**, JUnit observó3PASS3FAIL78,737s. Tres controles de imagen200 y tres revocados200 con derivado exacto, filas/archivos intactos. AGENTS.md cambió desde conversación lateral durante el run; app/instrumentos estables y limpieza/TelegramINVALIDsent. No se acepta como QA ni se reetiqueta. El nuevo freeze incorpora la instrucción vigente y conserva sus archivos fuera del commit de desarrollo. Ruff había requerido sólo reformatear un import; AST idéntico y posiciones del grafo conciliadas antes de ese run.

## Corrección y revisión previa

Cuatro archivos: moderation.py, match_review.py, moderation_views.py y match_views.py. Las vistas usan la guarda fresca de apelaciones ya existente para cuenta/MFA/sesión. Servicios recargan User/permiso efectivo y comparan versiones/activo/noerased con el actor admitido después de los locks. La aprobación bloquea revisiones pending que también pueden esperar y revalida antes del primer write; los demás checks de contenido/COI/historial, firmas, transacciones, auditoría y publicación siguen vigentes. Imágenes revalidan después del último lock antes de FileResponse/open. No lockUser nuevo ni cambio de esquema/dependencias/servicios.

Revisión Django y diferencial de riesgo alto con historia2955509c/3e4710a1/710c856f, flujos y radio estático registrados en DIFFERENTIAL_REVIEW.md compacto posterior. Variante exacta extendida sólo a los lectores con locks del mismo dominio; apelaciones ya protegidas y colas sin este wait se separan. No escaneo activo ni garantía universal posterior a la última lectura de autoridad.

El instrumentoPOST original se conserva aparte; sólo se completa el oráculo positivoMatch para PublicationState elegible→False/checksFalse y computed_at acotado. Ninguna tabla excluida ni relajación de los negativos403/ceroefectos. Si no concuerda se conservaFAIL y se estudia, sin atribuirlo automáticamente a producto. Instrumento de imágenes permanece idéntico al observado.

## Selección y aceptación de la candidata

Treinta casos seriales por archivo/nodo explícito:4POSToriginales,6lecturasoriginales en freezeestable,13variantes nuevas,5originales de aprobación/prerrequisitos y2 de resolución/COI/bytes. Las trece variantes cubren cada servicio con permiso sólo de grupo, epochcuenta, epochMFA, inactivo, erased, permiso retirado durante waitfinalRevision/Match; más wait de revisiónpendinghermana en aprobación. Todas usan POSTnativo, actor sintético ya admitido, holderspropios y pg_blocking_pids. No nueva ceremonia login/TOTP o benchmark.

Esperado30PASS0FAIL/ERROR/SKIP, fuentes/instrumentos/migraciones/deps estables, imágenespre/runtime exactas, snapshots completos, todos los waits demostrados, cleanup y reciboTelegram. Runneroficialfocused1,PG17/Redis7.4propios/parsernativo; timeout1200s como cota por paso, no ETA ni medición. Sin servicios normales o migraciones persistentes. Los tiempos de QA no acreditan rendimiento app.

Actualizar AST de6fuentes y semántica literal494/seguimiento antes de freeze; grafo selectivo, no reconstrucciónN15. No editar fuentes durante ensayo. Resultados originales y elINVALID se mantienen para archivo compacto saneado. La candidata no cierraN11: falta matriz de integración443acciones/28familias, puentes de fuente, conciliación de pruebas, omisiones, deuda y regresión común pertinente.

Trabajo activoN11/N15; deudaN02/MOD09 al final del desarrollo, N12/B14,N13/B15,N14/B17 condicionados; contrato generalQA pospuesto hasta versión estable/productiva. Mantener alpha/noindex y preparar relevo/frontend/grafo completo/inventario y purga final conforme N15, sin abrir beta o producción.
