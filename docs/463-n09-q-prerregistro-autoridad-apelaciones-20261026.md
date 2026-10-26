# N09Q — prerregistro de autoridad al resolver apelaciones

Estado: dos hipótesis estáticas pendientes de reproducción; sin cambios de
aplicación. Base812b2b7,N09abierto139y8/13obligatorios aceptados. [Última corrección462](462-n09-p-autoridad-foto-reintroducida-verificada-20261026.md).

Corte: grafo2108fuentes/20661nodos/85436relaciones,SHA256
55d93f815ed8b134af060b324096e1ebf4dfb22ba8e9ed4270aebbc947828bc3;
manifiesto completo sin diferencias antes del análisis. Refrescar AST del nuevo
instrumento ysemántica de este documento antes de congelar/ejecutar; noN15fullrebuild.

Hipótesis: appeals.review yphoto_appeals.review comprueban reviewer_allowed sobre
request.userantes de locks. Tras el último Appeal/PhotoAppeal, comprueban
independencia/estado, pero no recargan permiso del operador antes de resolver.
La protecciónCOIno equivale a permiso/MFA/sesión actual. N07conserva sus escenarios
aceptados; este diagnóstico pertenece a los IDs compartidos actualesN09y no
reabre N07completo. No afirmar defecto runtime antes de medir.

Selección: cuatro casos, publicación/fotografía por control/permiso revocado.
Seeds nativos de fixtures rejected/photo_case ysubmit real cuando corresponde;
usuario independiente con listings.review_listing,sesiónMFA/accountversion válida.
POST upheld con motivo sintético, sin reabrir Match/Revision opublicar perfiles.
Holder retiene la última fila Appeal/PhotoAppeal; workerPIDdistinto debe estar
realmente bloqueado con permiso de request cacheado. Sólo entonces retirar permiso
efectivo ycomprobarlo con Userfresh. Revocación commitea con liberación del holder,
no antes mediante una tercera conexión. Sin stub de permisos oSQL.

Oráculos: control302yúnica fila objetivo con exactamente status/result/reason/
reviewer_id/resolved_at, resultado upheld,actor/motivo exactos ymarca dentro del
intervalo. Revocado403ycero cambios de filas, incluyendo objetivo. Snapshots de
todos los modelos instalados/through/sesiones, antes tras la retirada propia y
después; snapshot adicional de todos los restantes incluso si falla el original.
Medios bytes/mtime/modo/digests invariantes. Emitir hashes,campos cambiados ybanderas
no privadas de resultado/actor/motivo; no UUID,SQL,payloads,archivos oidentidades.

Limpieza: consumir/cerrar respuesta en worker, statement_timeout10s,future15s,
cancelar únicamente conexión propia si timeout ycerrar hilo/conexión/holder en
finally con asserts. Guard explícito serial/DBpropia/noPRODUCTION/RECOVERY.
Una excepción de fixture no confirma la hipótesis. Resultado original inseguro
previsto2PASS2FAIL; preservar cada estado yrunnerERROR, sin xfail ni aceptación
por un porcentaje de casos. Auditoría inspeccionará resultados ymutaciones
reales para separar resolución indebida de fallos de preparación.

Después: si se reproduce, prerregistrar una corrección compartida de autoridad
actual tras locks, sin cambiar independencia,estados,cuotas,idempotencia oclaves.
Seleccionar regresión afectada de publicación/fotos yvariantes concretas de
sesión/MFA antes del candidato; no repetir baterías ajenas ni añadir exigencia de
proveedor/producción. Tiempo de los casos incluye preparación/espera/oráculos:
no es latencia normal de app,tiempo humano ni aceleración. Tabla posterior
comparará estados/deltas yQAcon ese límite.

Gates: escritor nativo aislado sparse propietario sólo del instrumento/reporte;
root revisa fixtures,modelos,lecturas/efectos,privacidad ycleanup con Django/
seguridad/revisión de accesos. Root reforzó hashes de otras tablas yresultado
seguro para que elFAILoriginal conserve causa trazable. Ruff yAST/semántica,
fuentes congeladas por secuencia estricta,runnerfocusedserial/parsernativo y
PostgreSQL/Redispropios. Telegram para toda prueba/auditoría con recibo. No editar
fuentes durante la ejecución ni declarar el modeloMCPdummy como esquema real.

Límites: estos dos handlers,un resultado upheld yuna revocación durante espera
final; sin cobertura exhaustiva de otros moderadores,broker,proveedor oapertura.
Alpha/noindex,N02restante al final,N10/N11/N15pendientes,N12–N14condicionados.
Limpieza completa deartifactscomo última acciónN15obligatoria aún pendiente;
preservar fuentes/evidencias y15cambios laterales fuera de commits propios.
