# N09P — autoridad de reintroducción fotográfica verificada

Estado: corrección finita aceptada localmente; N09 sigue abierto con139IDs y8/13
bloques obligatorios aceptados. Alpha/noindex. Base5735b72; [protocolo460](460-n09-p-prerregistro-autoridad-foto-reintroducida-20261026.md)
y[diagnóstico/candidata461](461-n09-p-diagnostico-y-candidata-foto-reintroducida-20261026.md).

Original:20261026-174845-5e27b1a6,1PASS/1FAIL,66,001sJUnit; ERRORdel runner
preservado,1.783huellas intactas. Retirar permiso efectivo durante la espera real
PGBlob dejabaHTTP200con10.516bytes de imagen privada. El control legítimo era200.
Revocación commiteada al liberar holder, no transición independiente anterior.
Auditoría confirma el defecto finito, sin convertir elFAILoriginal enPASS.

Candidata:20261026-175634-8cf2e07b,17PASS/0FAIL/ERROR/SKIP,249,003sJUnitQA;
1.783huellas estables. Auditoría independiente propiaPASS: dos esperasPGreales,
seis actores cacheados, un replay de decisión yocho originales. PostgreSQL17 y
Redis7.4propios, parsernativo fijado yrunnerfocusedserial. Contenedores exactos y
temporal ausentes; Telegram terminalPASS/deauditoría con delivery=sent. No quedan
pruebas activas de este lote. No nueva ejecución deworker,Beat oproveedor.

Cambio: dos archivos de aplicación. permission()lee Useractual sin reutilizar
has_permcacheado, exige activa/no borrada/MFAhabilitado, versiones de sesión/MFA
vigentes ypermiso efectivo. Tras los locks de alcance/candidate/Revision/Blob,
locked()revalida operador ypermitted(current,case). Las vistas revalidan antes de
renderizar review/queue yabrir el derivado. Sin nuevos locks,writes,claves de
idempotencia,estados oreglas de foto/prueba/independencia. Se acepta el coste de
consultas frescas por seguridad; no se presenta como optimización de latencia.

## Antes y después

| Escenario | HTTP / bytes de imagen antes | HTTP / bytes de imagen después | Tiempo cuerpo QA antes → después |
|---|---:|---:|---:|
| Control legítimo | 200 / 10516 | 200 / 10516 | 13.489 → 12.312 s |
| Permiso retirado durante espera | 200 / 10516 | 403 / 0 | 11.355 → 10.843 s |

Los tiempos incluyen preparación, espera inducida ysnapshots; N1porcaso, no
latencia de aplicación ni mejora causal. No calcular aceleración entre2casos/
66,001sy17casos/249,003s. La métrica de bytes corresponde a imagen privada
entregada conHTTP200: el403contiene una página de error genérica, no cero bytes
HTTPtotales. Su cuerpo no coincide con la imagen; respuesta cerrada. No hay
trazado exhaustivo de toda lectura interna ni serialización universal después
de la última comprobación de autoridad.

Cobertura: los2HTTPcon permiso cacheado mantienen snapshot completo de modelos
instalados/through/sesiones ymedios, con PIDs distintos, bloqueo observado,
respuestas/conexiones/hilos cerrados. Los6servicios inspect deniegan permiso
retirado, sesiónMFAversiones cambiadas, cuenta inactiva,MFAapagado yborrado; son
variantes sin nueva espera oHTTPacreditados. El replay exacto de decide tras una
decisión legítima se deniega al retirar permiso, sin devolver datos privados ni
mutar SQL/medios. No son siete defectos baseline adicionales.

Originales:3photo_reuse_races conservan medios retirados, decisiones concurrentes
yprueba cambiada;3photo_reuse_inventory conservan drift invalidando borrado.
Dos casos ES/EN de test_review_requires_independence_current_audit_and_invalidates_changed_resources
comprueban HTTPqueue/review/inspect/imágenes/decisión yChromiumreal. Estos dos
se añadieron expresamente antes de congelar mediante candidate-ui-addendum.json,
15casos base+2afectados=17; no ampliación silenciosa después del resultado.
Se mantienen sus oráculos originales, sin nuevas baterías ajenas a la corrección.

Revisión: root aplica Django/seguridad/revisión de accesos ybúsqueda de variantes
acotada; revisor nativo independiente sin ejecutar pruebas. Sus propuestas fueron
insumos; root añadió guardas de permiso efectivo ycierre antes del baseline.
RuffPASS yAST de3fuentes mássemántica461/17 antes de la candidata;2.107fuentes/
20.647nodos/85.421relaciones, SHA6540e08363a1fc0754c2800ae38410e3c12060723d58347eb7a6846eadb5ef04.
Refresco terminal462/17sin repetir runtime, no reconstrucciónN15 ni semántica
exhaustiva.111preservado;consumo nativo desconocido,V1nuevo0/historial retenido.

Conciliación: se conservan52IDs de derechos/15grupos y48declaraciones asíncronas
con hashes yreferencias actuales en matrices de trabajo. La propuesta nativa49
con referencias limitadas y3con hueco compartido no equivale a52aceptaciones
finales; esta corrección aporta evidencia aqueue/review/image fotográficos.
Se contrastaron identidades/JUnit/archivos de correccionesB/C/E/F/G/H, sin repetir
sus pruebas válidas. AliasBeat ycallbacks anidados no suman ejecuciones.

Pendientes: el mismo triage acotado localizó dos hipótesis estáticas distintas
en escrituras de appeals.review yphoto_appeals.review: permiso cacheado antes
de locks ysin recarga antes de resolver. No se declaran defectos runtime por
inspección; requieren reproducción focal posterior. UrgentalertsPOSTya revalida
tras su lock ylas confirmaciones bearer no comparten ese operador. No se alteró
la candidata congelada para añadir casos de apelación ni se reabre N07completo.
N09conserva esas comprobaciones ylas139disposiciones; N10/N11/N15pendientes.

Custodia: [paquete saneado](evidencias/n09-p-autoridad-foto-reintroducida-20261026.tar.gz),
SHA256 `f58195b7e4f9e7b79e36bffce67c92270fff1664a94d9faf221535c9238a6d43`,23miembros con manifiesto comprobado.
Incluye originales/candidata/acotación previa/auditorías estructuradas,revisiones
yrecibos, sin logscrudos,settings,entorno,credenciales,cuerpos privados,grafo
completo ocontenido lateral. Auditoría local enartifacts/recorridos-n09-p-20261026/.
N15mantiene resumen duradero fuera deartifactsyvaciado final obligatorio; aún no
ejecutado. N02restante diferido al final,N12–N14condicionados,sin apertura.
