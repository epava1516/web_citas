# B13 — Estrategia de rollback de aplicación y esquema

Estado: análisis de fuentes y estrategia local, no ensayo de compatibilidad de imágenes. B13 abierto; siete de18puntos cerrados. Complementa [144](144-restauracion-retirada-beta-b13-20261021.md) y [roadmap103](103-roadmap-beta-clasificados-20261020.md).

## Qué permiten concluir las fuentes

| Fuente | Hecho comprobado por lectura | Límite |
|---|---|---|
| listings/migrations/0023_romantic_profile_contract.py | Añade content_contract; filas existentes reciben legacy-professional-v1 y el estado nuevo usa romantic-v1. Su descenso elimina la columna. La reversa del catálogo es noop. | El descenso no conserva la distinción de contratos ni revierte una decisión editorial. Reaplicar clasificaría como históricas las filas que sobrevivieran sin esa columna. |
| listings/migrations/0024_optional_profile_type.py | Cambia el tipo a opcional y el valor por defecto a vacío. | Revertir el valor por defecto no demuestra compatibilidad semántica del código alfa con perfiles beta existentes. |
| listings/migrations/0025_optional_trans_label.py | La reversa rechaza etiquetas seleccionadas mediante IrreversibleError antes de eliminar el campo. | Ausencia de etiquetas seleccionadas no autoriza borrar content_contract ni desplegar código alfa. |
| tests/test_beta_profile_contract.py | Contiene upgrade real y descenso que preservan registros/tarifas y catálogo inactivo. | Preservar filas no prueba conservación del contrato de cada revisión ni compatibilidad HTTP de una imagen anterior. |
| tests/test_declared_profile_label.py | Contiene rechazo de descenso con etiqueta seleccionada. | No es una prueba universal de todos los descensos. |
| docs/12-operacion-seguridad.md | El ensayo de estáticos exige collectstatic --clear y comprueba hashes/404. | No acredita rollback de aplicación, esquema ni datos beta. |

Estas conclusiones son análisis del código vigente, no nuevas ejecuciones PostgreSQL. No se reutilizan los resultados alfa como aceptación beta.

## Procedimiento adoptado para preparar y ensayar el rollback

1. Identificar la imagen candidata y la anterior mediante digest inmutable, las migraciones aplicadas y la configuración esperada, sin copiar secretos al informe. Sólo una versión que entienda el contrato romántico puede ser candidata al retorno. Una imagen alfa no es una candidata compatible por defecto.
2. Preparar DB y medios sintéticos aislados al esquema beta actual, incluyendo revisiones históricas y románticas, tipo vacío, etiqueta seleccionada, restricciones, derechos y evidencia comercial. Capturar inventario y huellas privadas de control.
3. Mantener el esquema beta al volver al código anterior compatible. No ejecutar migrate listings 0022 ni eliminar columnas para hacer arrancar una imagen. Los cambios aditivos futuros deben mantener compatibilidad de lectores/escritores durante la ventana de retorno; cambios destructivos requieren una fase distinta y evidencia previa.
4. En el ensayo aislado, iniciar el código candidato anterior con el mismo esquema y lectores criptográficos necesarios. Verificar arranque, rutas ES/EN, edición y moderación, filtros de derechos, historial, contactos, medios y tareas; revisar que no reintroduce anuncios profesionales, estados públicos ni tareas revocadas. Comparar registros y archivos con controles pares.
5. Volver al código actual y repetir los controles de integridad y las rutas afectadas. Estáticos se regeneran con clear dentro de STATIC_ROOT propio; salud HTTP por sí sola no basta. No declarar éxito si sólo se ha renderizado Compose o usado el código actual bajo otro nombre.
6. Si falla compatibilidad, mantener aislamiento y aplicar una corrección hacia delante. No manipular django_migrations ni vaciar datos. Restaurar una copia anterior es una operación de recuperación distinta: exige DB y medios coherentes, autoridad independiente de derechos, invalidación de sesiones/grants y generación nueva de cola antes de exposición, como en144.
7. Conservar resultado terminal, fuentes exactas, pruebas, diferencias de datos, limpieza y recibo Telegram. La apertura externa continúa sujeta a B17 y los permisos ya establecidos.

## Pendiente para aceptar este requisito

Falta seleccionar y construir una pareja real de versiones beta compatibles y ejecutar el ciclo de aplicación sobre el mismo esquema. El árbol actual con cambios sin integrar no identifica por sí mismo una imagen anterior beta aceptada. No se inventa esa pareja ni se declara impedimento externo: puede prepararse localmente preservando los cambios del usuario. También falta verificar el procedimiento futuro de migraciones con escritura durante la ventana de compatibilidad. Este documento no cierra B13 y no cambia migraciones históricas ni el alcance de B07.

## Pareja de imágenes preparada y verificada

[Manifiesto de preparación](evidencias/b13-rollback-images-prepared-20261021.json): imagen actual6c8abf2e1d3b y anteriora699565c12bf, identificadas por SHA256 completo en la evidencia. Base beta vigente construida desde725archivos congelados; límites por RUN1536MiB/sin swap/cuota2CPU/cpuset0–3. Capas de variantes sin red,724archivos runtime/scripts comprobados por SHA dentro de cada imagen; kernel native-sealed y UID10001. Contenedores de comprobación eliminados y avisos terminales confirmados. No servicios normales modificados ni publicación.

El corte anterior reproduce exactamente las fuentes de producto040020; difiere del actual041741 sólo en apply_recovery_ledger. Conserva la omisión conocida de invalidación de grants: no es candidato para reconciliar restauraciones. Ambas imágenes mantienen las migraciones beta y las dependencias vigentes. Esta pareja permite ensayar retorno de aplicación limitado a ese cambio; no acredita compatibilidad con alfa ni con futuros cambios destructivos.

Dos preparaciones negativas se conservan: la imagen worker normal fue rechazada por pyproject anterior; un FROM con ID desnudo se interpretó como referencia de registro y falló antes de construir. Se corrigió a base local nominal identificada por ID. El ensayo de código sobre PostgreSQL/medios y rutas sigue pendiente. Las imágenes preparadas se conservan intencionalmente para ese ensayo; no se afirma limpieza de esos artefactos.

## Ciclo real de lectura verificado

[Auditoría terminal](evidencias/b13-rollback-cycle-terminal-audit-20261021.json): actual80d66b10e1f4 → anterior980bcc133069 → actual80d66b10e1f4, misma DB PostgreSQL17 y mismo volumen de medios, sin descenso de esquema. Nueve tablas completas de negocio/migraciones comparadas por huella y ocho archivos de medios conservados en los tres controles. Tipo vacío y etiqueta seleccionada preservados; perfiles de consentimiento revocado y contrato histórico permanecen ocultos. Dieciocho comprobaciones TCP de fichas ES/EN y seis fotos200 con bytes, servidas por Gunicorn real desde otra sonda en la red interna, sin puertos publicados. Sesión sintética autenticada alcanza panel por Client WSGI en cada imagen; no se presenta ese control como navegación TCP autenticada.

Las imágenes anteriores preparadas ya no estaban disponibles en Docker al iniciar el ciclo. Se reconstruyeron desde los contextos congelados; los nuevos IDs completos figuran en la auditoría y los724archivos/kernel/UID se verificaron de nuevo dentro de cada imagen. Los IDs de la sección previa describen el corte previo de preparación, no las instancias de este ciclo. No se atribuye una causa a la desaparición.

Cinco intentos negativos propios conservados: imágenes ausentes, permisos de lectura de la sonda, generación de cola con guiones rechazada, puerto no publicado y Host interno rechazado con400. Se corrigió el montaje propio, el valor sintético de cola y la sonda TCP usando Host localhost ya autorizado; no se cambiaron guardias, producto ni ALLOWED_HOSTS. La primera auditoría de ausencia de red esperaba el texto no such; Docker devuelve network not found y se corrigió el reconocimiento exacto del recurso ausente. Todos estos negativos son del arnés, no evidencia de incompatibilidad de producto.

Resultado PASS local acotado. Fuentes runtime frescas724, contenedores/red/volumen ausentes por inspección fresca, recibo terminal Telegram confirmado. No hay escrituras de negocio concurrentes, cambio de worker ni reconciliación con la imagen anterior. Falta ampliar el ciclo a edición/moderación y tareas durante la ventana de retorno; B13 sigue abierto y el total permanece7/18.

La ampliación posterior a escrituras y consumo real entre versiones está verificada en [146](146-rollback-escrituras-workers-beta-b13-20261021.md). Sustituye la ausencia de ese ensayo por evidencia local del relevo secuencial; no acredita tráfico concurrente ni una imagen alfa compatible. B13 conserva los demás pendientes.
