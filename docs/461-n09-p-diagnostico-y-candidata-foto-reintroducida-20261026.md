# N09P — diagnóstico confirmado y candidata de autoridad fotográfica

Estado: diagnóstico confirmado, corrección candidata pendiente de verificación.
N09abierto y8/13obligatorios aceptados; alpha/noindex. [Prerregistro460](460-n09-p-prerregistro-autoridad-foto-reintroducida-20261026.md).

Original: run20261026-174845-5e27b1a6,1PASS/1FAILsinERROR/SKIP,66,001sJUnitQA;
runnerERRORpreservado,1.783huellas intactas. Ambos casos acreditan esperaPGBlob,
PIDs distintos, permiso de petición cacheado, cuerpos yrespuesta cerrada, SQL
ymedios invariantes. La retirada efectiva se comprueba con Userrecién consultado;
commitea con la liberación del holder, no antes en otra conexión independiente.
El control devuelve200ybytesexactos; el revocado también200ybytesexactos frente
al403exigido. Auditoría confirma el defecto finito yno lo reclasifica comoPASS.
Recursos ytemporal propios ausentes; recibosTelegramERRORydeauditoría comprobados.

Causa: permiso/MFA sobreUsercacheado antes de locks, sin revalidación del operador
tras el último Blob; el refresco de prueba/recursos no cubre permisos actuales.
La misma guarda locked se usa en inspect/decide eimagen; queue/review son las otras
superficies de lectura del módulo. La búsqueda acotada de variantes mantuvo estos
llamadores; no convierte otros permission()homónimos en defectos confirmados.

Candidata: permission()consulta Useractual yrechaza cuenta inactiva/borrada,
MFAapagado, versiones de sesión/MFA distintas de las de la instancia original
ypermiso efectivo retirado. No reutiliza cachés has_perm. Tras todos los locks de
alcance/candidate/Revision/Blob vuelve a comprobar operador ypermitted(current,case).
Las vistas revalidan antes del render de review/queue yantes de abrir la imagen.
Sin nuevos locks o writes, sin cambios de claves/replays/versiones de negocio,
reglas de foto/prueba, independencia, formatos oprocesado. Consultas adicionales
son coste de seguridad, no optimización ni promesa de serialización universal.

Revisión: root Django/seguridad yrevisor nativo independiente, sin bloqueantes
en el diff de dos archivos. El diagnóstico se reforzó antes del baseline con
asserts de cierre yUserfresh sin permiso efectivo. Ninguna propuesta de agente
se acepta como prueba de ejecución. Consumo nativo desconocido,V1nuevo0.

Selección candidata: quince casos esperados. Instrumento propio con2HTTPde espera
originales,6inspecciones con actororiginalcacheado tras retirada de permiso,
versión sesión,versiónMFA,cuentainactiva,MFAapagado oborrado; y1replay exacto de
una decisión legítima tras retirar permiso. Más3originales de photo_reuse_races
(medios borrados,decisiones concurrentes,prueba cambiada) y3de photo_reuse_inventory
(drift de versión/motivo/consulta invalida borrado). Las nuevas siete variantes
son servicios nativos sin nueva espera acreditada; no se presentan como siete
defectos adicionales del original. Repetir los dos controles es pertinente al
cambio compartido, sin repetir generación/descarga/outbox/workerQA ya válidos.

Criterio:15PASSsinERROR/FAIL/SKIP, negativosdenegadossinbytes/deltas, controles
legítimos yoráculos originales íntegros. Replays siguen condicionados aautoridad
actual. Comprobar fuentes congeladas, oráculos, observadores reenviados, cierres,
recursos ausentes yTelegram. Un ERROR de fixture se conserva ycorrige como tal,
no se acepta la candidata por mera inspección de código oRuff.

Medidas: para los dos HTTPcomparar estados/bytes antes/después ytiempos de cuerpoQA
incluida preparación/espera/snapshots; no inferir latencia normal ni aceleración.
Las otras siete variantes no tienen una pareja baseline yno acreditan nueva
esperaPG. Los seis originales conservan sus escenarios yrelojes respectivos.

Antes de ejecutar: Ruff acotado, AST de dos fuentes ydel instrumento mássemántica
460/461, manifiesto ycongelación mediante check=True; runnerfocusedserial con
PostgreSQL/Redispropios yparsernativo fijado. Después auditar15casos ysnapshots,
recursos yrecibos. No cambiar fuentes durante el runner ni pausar/reiniciar por
la instalación de herramientas. No proveedor,migración,CI,servicios normales o
nueva capacidad comercial. N02diferido; N10/N11/N15pendientes,N12–N14condicionados;
limpieza finalN15artifactsobligatoria aún pendiente.
