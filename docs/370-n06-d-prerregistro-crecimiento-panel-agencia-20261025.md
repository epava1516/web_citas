# N06D — crecimiento del panel de agencia

25 de octubre de 2026. N06abierto; [referencia369](369-n06-c-resultado-representacion-autoridad-20261025.md). Grafo previo focal verificado1966fuentes/18471nodos/80987relaciones/876comunidades; SHA8a87554b5f54fb9de2eb8e40d6a102077e1494e92da67522d2d7b38e4e2a8b27. Preserva AST anterior y base completa; semántica focal, no exhaustiva. MOD09restante diferido por usuario367. Ningún candidato de aplicación aún.

## Hipótesis, trabajo útil y decisión previa

apps/core/agencies.py::panel entrega agency.memberships.filter(active=True) al propietario. templates/core/agency.html itera members y accede member.user.email. Hipótesis: una consulta adicional por editor activo. El editor ve sólo personas asignadas, sin lista de miembros; no se amplía su acceso ni se elimina filtro active.

Primero medir la referencia actual. Sólo si confirma coste creciente por editor, candidato acotado previsto: select_related("user") sobre el queryset de miembros activos entregado al propietario. No cambiar esquema, orden, cardinalidad, contenido, permisos, retirada ni llamadas de servicios. Comparación conforme354: coste objetivo consultas SQL de la petición, candidato≤referencia en cada modalidad; reducción estricta para cohortes10/100si se afirma mejora. Comprobar respuesta de tamaño equivalente y oráculos funcionales en ambos; conservar posibles costes/regresiones CPU/pared. Cinco observaciones posteriores por variante y primera aparte; mediana/rango sin p95. Si el tiempo no permite concluir mejora, registrar inconclusión sin repetir adaptativamente por rutina.

## Datos y escenarios

Instrumento tests/test_agency_panel_growth_reference.py. Seis casos: cohortes1/10/100por ES/EN. Cada agencia tiene ese número de personas y miembros activos; un editor asignado únicamente a la primera persona, los demás usuarios sintéticos sólo como filas de miembros. Miembro inactivo y agencia/persona ajenos adicionales. Propietario/editor/externo creados con el helper original de cuenta y aceptación/MFA de prueba; ningún proveedor real ni datos reales. Creación ORM/bulk de fixtures fuera del reloj, no sustitución del trabajo de una petición. Estado de verificación de agencia pendiente declarado, sin revisión ni publicación simuladas como éxito real.

Por caso: seis GET200del propietario y seis GET200del editor (primera y cinco posteriores), luego externo403/anónimo302/revocación de membresía→editor403/propietario200. Total72peticiones medidas y24negativas/comprobación posteriores. Una baja y una lectura por caso; no modificar derechos durante las muestras de la misma variante. Mantener conjuntos exactos de personas/miembros, email de cada miembro activo para propietario, exclusión del inactivo/ajenos y ocultación de miembros para editor. Fuente/semántica del protocolo y AST del instrumento incorporados al grafo antes de congelar/medir.

## Relojes, recursos y comandos

Pared de client.get y CPU del proceso, y execute_wrapper de la conexión PostgreSQL con conteo/tiempo SQL. Aserciones y fixtures fuera del reloj; render/middleware/consultas de la petición dentro. Guardar sólo escenario/actor/ordinal/tamaño/idioma/números, nunca SQL/params/cuerpos/credenciales/UUID. Se puede calcular variación de bytes, sin publicar contenido privado sintético. No medir navegador/TCP/carga/colas reales ni reclamar SLO de producción. No sumar CPU/SQL/pared como etapas disjuntas.

Comando para ambas fuentes: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_agency_panel_growth_reference.py`. PostgreSQL17/Redis7.4propios, herramientas nativas fijadas, dependencias bloqueadas, sin cuotas dedicadas/carga paralela. Mismo instrumento/orden/datos/recursos; fuentes completas/grafo/imágenes congeladas antes de cada ejecución. Seis casos cada pasada, sin repeticiones adaptativas ni recorte de población. El tiempo entre ejecuciones/calor no permite atribución causal universal: sólo escenario local explícito.

## Auditoría y salida

Auditar6casos/72muestras y oráculos en cada fuente, primera separada/medianas cinco/rangos, consultas/CPU/SQL/bytes, errores/muestras no finitas, integridad de fuentes, ausencia independiente de recursos/temp y Telegram terminal. Tabla anterior/posterior por actor/cohorte/idioma con delta y porcentaje sólo comparable; QA separado. No hay cierreN06por una corrección del panel: cuenta/variantes restantes se concilian posteriormente. Si la hipótesis se descarta, documentar sin candidato y pasar a coste probado.
