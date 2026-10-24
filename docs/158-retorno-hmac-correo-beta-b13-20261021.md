# B13 — Retorno de aplicación con HMAC activo y correo explícito

Estado: ciclo integrado de retorno con HMAC activo verificado localmente. B13 aceptado técnicamente en local por acta15, ocho puntos de18cerrados. Continúa [matriz155](155-matriz-vigente-b13-beta-20261021.md) y [corrección157](157-preparacion-adaptadores-beta-b14-20261021.md). No se usa la histórica80d66b10 incompatible con HMAC.

## Versiones y condición de retorno

Candidata5a0751c1 y retorno66c6d381:726fuentes de runtime por imagen verificadas dentro del contenedor, UID10001 y kernel nativo sellado. Dependencias iguales. Diferencia funcional real: guardia de arranque de correo en config/settings.py, verificada por35casos en080733. El retorno no contiene esa guardia; mantener EMAIL_BACKEND explícito permitido es condición obligatoria. Ambos aceptan SMTP configurado en un arranque production aislado sin red y HMAC independiente activo; no se abrió conexión SMTP ni se verificó proveedor.

No son dos builds de la misma aplicación. No se revierte SECRET_KEY a una clave anterior para lograr compatibilidad. No se hace downgrade de esquema, borrado de filas ni modificación de django_migrations. La prueba de configuración production se separa de los recorridos sintéticos de aplicación, que usan development/simuladores y no acreditan apertura.

## Protocolo previo al ciclo

Recursos propios: PostgreSQL17 en tmpfs, Redis7.4 y volumen de medios nuevos, red Docker interna sin puertos publicados. Prefijo aleatorio y etiqueta propia. App y workers de estas dos imágenes sólo se conectan a esos servicios. No servicios normales, proveedores, pagos o datos reales.

Ciclo candidata→retorno→candidata, con checks antes y después de escrituras. Dataset romántico, perfil sin tipo y etiqueta trans opcional, par revocado y anuncio legacy que deben permanecer ocultos. Once tablas de contenido/migración/denuncias/derechos y archivos de medios se comparan; se permiten únicamente las escrituras declaradas y las acciones/sesiones/cachés correspondientes.

Recibos: crear una denuncia y una solicitud de derechos por formularios reales locales usando el binding heredado en un proceso de semilla aislado; pasar a SECRET_KEY de Django nueva y pin del valor anterior sólo como HMAC de dominio. Todas las fases de servidor/worker conservan esa clave nueva y el pin; no se reactiva la anterior como firma Django del runtime. En cada check, los recibos originales ES/EN devuelven200 privado/no-store/noindex y el replay exacto vuelve al mismo expediente; filas completas/ciphertext/huellas/plazos y plaintext descifrado conservan sus hashes. Secretos/URLs de recibo sólo en el volumen privado efímero, sin salir al resumen/Telegram. TCP comprueba los mismos recibos en cada versión.

Escrituras: editar el mismo borrador en tres etapas; pausa/reanudación/disponibilidad con tres acciones nuevas y seis replays idempotentes. Procesar tareas reales con worker de retorno para productor candidata, worker candidata para productor retorno y worker candidata para productor candidata. Exigir tarea identificada terminada, cola vacía, sin PublicationDirty y todas las columnas derivadas iguales a la regla nativa; conservar pares, revisión aprobada y medios. No Beat ni proveedor real acreditados en este ciclo.

HTTP interno: por etapa, seis fichas públicas/denegadas ES/EN, dos fotografías y cuatro recibos privados; readiness añade lecturas fuera de ese conteo. Total prefijado18fichas/6fotos/12recibos TCP, además de controles Client y POST. El recurso pausado devuelve404 y vuelve a200 al reanudar; revocado/legacy siempre404. No es prueba de carga ni Internet.

## Auditoría y límites

Congelar fuentes completas y copias de sondas antes del ciclo. Guardar cada intento en directorio nuevo; conservar cualquier fallo. Resultado sólo tras limpieza de contenedores, red y volumen y ausencia verificada, PIDs terminales, fuentes frescas iguales y Telegram terminal confirmado. Auditar fuera del escenario antes de editar documentación. Las imágenes permanecen como artefactos locales de retorno.

PASS del ciclo no cierra B13 automáticamente: conciliar literalmente runbooks/rotaciones/restauraciones/retirada/migraciones sobre la candidata vigente y separar custodia/personas/infraestructura real B17. B07 conserva cortoFAIL y900s bloqueados. Ningún simulador pasa a integración real por esta prueba.

## Negativo de preparación conservado

Intento4bc1e19b6c49 termina antes de ejecutar la aplicación: el directorio de sondas0750 y archivos0640 del host no son legibles por UID10001 del contenedor. Python no abre check.py, sin crédito de semilla, migraciones, recibos, worker o rollback. [Auditoría negativa](evidencias/b13-hmac-mail-permission-negative-20261021.json): fuentes iguales, contenedores/red/volumen propios ausentes y Telegram EXIT1 confirmado. Se conservan el intento y sus logs privados.

Corrección limitada a la fixture: cada directorio de intento nuevo tiene0755 y sus seis archivos de código0644, montados readonly; logs, claves/recibos y datos privados no reciben esos permisos. Aplicación e imágenes intactas. Repetir en recursos nuevos y directorio distinto; no sobrescribir el negativo.

## Segundo negativo del arnés y ajuste acotado

Intento697a69d40ddb: después de la semilla, la guarda del ensayo detecta que setup_test_environment de Django sustituye EMAIL_BACKEND por locmem. No se crean los recibos ni se ejercita el retorno. [Auditoría negativa](evidencias/b13-hmac-mail-setup-negative-20261021.json): fuentes/limpieza/Telegram EXIT1 confirmados; no defecto nuevo de aplicación.

Se instrumenta únicamente Template._render para capturar contexto de formulario; se elimina setup_test_environment y se conserva la configuración efectiva de Django. Preflight reforzado dentro de ambas imágenes verifica lectura de las sondas por UID10001,726fuentes/kernel nativo/arranqueproduction y EMAIL_BACKEND efectivo SMTP tras importar la sonda, con red deshabilitada. No es un envío de correo. Ambos negativos se conservan y la tercera ejecución usa otro directorio y recursos nuevos.

## Resultado integrado auditado

Intentof47e2f8fbb3a: PASS_LOCAL_ACTIVE_HMAC_APPLICATION_ROLLBACK, [auditoría terminal](evidencias/b13-hmac-mail-rollback-terminal-audit-20261021.json). Una ejecución de escenario con tres etapas reales5a0751c1→66c6d381→5a0751c1; tres workers, incluyendo consumo cruzado entre versiones. No son tres casos pytest ni una regresión completa. Se conservan los dos negativos previos y sus recibos terminales.

Once tablas por check; filas completas/ciphertext/huellas/plazos de denuncia y derechos y hashes de plaintext inalterados. Recibos originales ES/EN y replays exactos conservan los mismos expedientes. El runtime siempre usa SECRET_KEY nueva y pinHMAC del binding heredado; sólo la semilla recrea su estado anterior. Tres ediciones de borrador, tres acciones de ciclo y seis replays, sin cambios de pares/revisión aprobada/medios. Tres tareas identificadas terminadas, cola vacía, sin PublicationDirty y estado igual a la regla nativa. HTTP interno:18fichas/6fotografías/12recibos privados TCP, además de Client.

Fuentes completas y seis sondas congeladas/fresh,726fuentes por imagen verificadas, red interna sin puertos de app publicados, contenedores/red/volumen y PID del controlador ausentes; recibo Telegram PASS confirmado. No downgrade de esquema. Las imágenes permanecen locales; el retorno exige correo explícito permitido porque carece de la nueva guardia. No acredita SMTP, proveedor, HTTP de producción o infraestructura real.

Este resultado satisface el contraste local de retorno de la candidata actual en la configuración ensayada. B13 no se cierra automáticamente: siguiente acción, conciliación literal final de su matriz y alcance de reutilización, manteniendo límites de apertura B17. B07 sigueFAIL; no900s ni aceptación beta global.

Conciliación final posterior: [acta15](actas/15-beta-b13-aceptacion-local-20261021.md) acepta B13 en su alcance local; sustituye el siguiente paso de revisión señalado antes, conservando los límites de este ensayo.
