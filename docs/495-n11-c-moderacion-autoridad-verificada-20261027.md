# N11C — autoridad de moderación e imágenes verificada

Candidata494 aceptada **sólo en sus escenarios funcionales locales**. Run `20261026-235930-b380126e`: **30 PASS,0 FAIL,0 ERROR,0 SKIP**,205,811sJUnit de QA,1800 fuentes estables. No se acepta N11 completo:10/13 bloques se mantienen, falta conciliación y regresión común pertinente. Producto alpha/noindex.

## Antes y después

| Recorrido | Original observado | Candidata actual | Alcance |
|---|---|---|---|
| Listing POST durante Personwait | Control302 y efecto exacto; revocado302 y efecto exacto | Control302 con efecto exacto; revocado403/ceroefectos | Mismo negativo, User/permiso efectivo fresco después de locks |
| Match POST durante Personwait | Ambos302/escrituras; oráculo positivo incompleto | Control302/efecto completo; revocado403/ceroefectos | Incluye proyección nativa exacta; no exclusión de tablas |
| Tres lecturas de imagen | INVALIDB: tres controles200 y tres revocados200/bytes; observación no aceptada como QA | Tres controles200/derivado exacto y tres revocados403/sin stream/bytes | Instrumento idéntico bajo freeze estable |
| Trece variantes nuevas | Sin testigo equivalente | 13PASS,403 y todos los modelos/archivos sin efectos | Permiso de grupo, epochs cuenta/MFA, inactive/erased, targetRevision/Match y pendingSibling de aprobación |
| Publicación y resolución ordinarias | Se conservan testigos previos con sus versiones | 7PASS originales de aprobación/prerrequisitos/resolución/COI/bytes | No debilitar los controles de dominio |
| Tiempo de QA | A66,291s; B78,737sINVALID | C205,811s para30casos | Poblaciones distintas; no speedup o latencia app |

Veintitrés esperas PostgreSQL reales:cinco controles válidos y dieciocho denegaciones después de intervención comprometida. PID distinto, pg_blocking_pids recursivo y future pendiente acreditados. Snapshots173modelos/through y archivos/hash/metadata; retirada de permisos y cambios deliberados del actor incluidos en baseline. Los controlesPOST enumeran exactamente auditoría/revisión/matches/restricciones/listing y proyección esperados; los negativos no escriben. Las imágenes válidas concuerdan con el derivado privado; las denegadas no lo entregan.

## Cambios y límites

Cuatro fuentes de aplicación. Guarda fresca de sesión/MFA ya usada por apelaciones; servicios recargan User/permiso y comparan estados/epochs después de locks. Aprobación toma también locks de pendingsiblings antes del primer write y revalida después; las imágenes revalidan antes de FileResponse/open. Sin nuevas migraciones, settings, firmas de servicio, dependencias o servicios. No garantía de revocación posterior a la última lectura de autoridad ni interrupción de un stream ya admitido. Sesiones sintéticas force_login con epochs explícitos, no nuevas ceremonias login/TOTP.

El oráculo positivoMatch omitía PublicationState: al quedar el listing no elegible, el refresco nativo cambia eligible/checksFalse y computed_at. Se completó esa expectativa estricta manteniendo todos los demás campos/modelos exactos y conservando originalA. Los negativos403/ceroefectos no cambiaron. Se comprobaron los campos cambiados sin almacenar valores privados. La aprobación ordinaria y las cuatro condiciones inválidas, resolución de personas distintas y límites de COI/bytes exactos siguen pasando.

La revisión diferencial de riesgo alto y variantes conserva historia2955509c/3e4710a1/710c856f, flujos, falsos positivos y sitios de llamada. No auditoría universal. Los cuerpos AST de publicly_visible/conflict_of_interest/unresolved_matches, páginas públicas y locked_pair permanecen iguales; sus módulos no son byteidénticos y la autoridad compartida sí cambia. RULE_SOURCES incorpora la nueva huella de moderation; no atribuir automáticamente antiguas latencias de guarda privada al producto actual.

## Verificación y custodia

Runnerfocusedserial, PG17/Redis7.4propios, parsernativo. Fuentes/instrumentos/docs/vendor congelados, IDs imágenes pre/runtime contrastados, contenedores/temporal y conexiones propios retirados; TelegramPASSsent. SHA JUnit `eaf98898d973ccc1e727ac5fecff6642df103fce4724ab6c4340f19ed01745dd`.

La auditoría root conserva A1PASS3FAIL, BINVALID y C30PASS separados. Se corrigieron dos errores del verificador local posterior (sintaxis y referencia textual al observador); no se repitió pytest ni se cambió producto por ellos. No se convierte INVALID en PASS ni se suman los tres runs como batería única.

Archivo compacto [N11ABC](evidencias/n11-abc-moderacion-autoridad-20261027.tar.gz), 48 miembros con manifiestoSHA256; SHA del archivo `40ede83066cb3ce34c0665b20ad63008258241d240195a6e6959f0e473012e63`. Contiene originales/instrumentos, fuentes antes/después, congelaciones, propiedades auditadas, resúmenes terminales, intentos de aviso y revisión. No logs, cookies, configuración privada o datos reales. Los dieciséis archivos laterales, incluida deuda-pendiente-viva, quedan preservados fuera de esta entrega.

## Continuación

Trabajo activo: N11 matriz requisito→acción→candidata→prueba→resultado→límite de443acciones/28familias, puentes de fuente y selección de regresión común. No repetir la batería histórica de4horas por el mensaje CLI ya corregido en315: su ERROR se conserva y su correctiva23PASS es otro testigo. Omisiones129 y sus disposiciones no son PASS. N15 grafo completo nuevo antes de diferencial de inventario, relevo frontend y purga final de artifacts.

Deuda separada conforme [registro vivo](deuda-pendiente-viva.md): N02/MOD09 residual al final del desarrollo, N12/B14,N13/B15,N14/B17 condicionados; contrato generalQA aplazado hasta primera versión estable/productiva. Nada activa UI/UX/Front, proveedores, indexación, beta o producción.
