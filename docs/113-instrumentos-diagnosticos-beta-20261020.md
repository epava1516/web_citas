# Instrumentos diagnósticos y colección de regresión

Fecha:2026-10-20. Estado: separación y conservación verificadas; sin cambios de producto ni aceptación beta. No son3760pruebas ejecutadas.

Los seis módulos de medición añadidos durante B07/B08 tenían nombre test_*.py y entraban en la colección ordinaria, incluida la vía funcional paralela del runner. Sus experimentos exigen ejecución secuencial y algunos fijan el SHA original del producto: no deben convertirse accidentalmente en pruebas funcionales ordinarias ni repetirse contra otra versión para acreditar mejoras.

Se trasladan dentro de tests/ a nombres beta_*_diagnostic.py. La configuración existente sólo descubre test_*.py por defecto; una selección explícita de pytest conserva sus escenarios. No se añaden skips, se relajan criterios ni se eliminan funciones. Los originales exactos quedan como texto en evidencias/beta-diagnosticos-20261020/*.py.txt, fuera de la colección, con hashes y correspondencias en la auditoría. Sólo cambian ruta, nombres de imports entre diagnósticos y orden de esos imports; funciones/decoradores y demás AST permanecen idénticos.

| Ruta histórica ejecutada | Ruta actual explícita |
| --- | --- |
| tests/test_beta_read_baseline.py | tests/beta_read_baseline_diagnostic.py |
| tests/test_beta_promotion_profile.py | tests/beta_promotion_profile_diagnostic.py |
| tests/test_beta_promotion_plans.py | tests/beta_promotion_plans_diagnostic.py |
| tests/test_beta_post_tcp_profile.py | tests/beta_post_tcp_profile_diagnostic.py |
| tests/test_beta_rights_materialization_roi.py | tests/beta_rights_materialization_roi_diagnostic.py |
| tests/test_beta_rights_materialization_uuid_roi.py | tests/beta_rights_materialization_uuid_roi_diagnostic.py |

[Auditoría](evidencias/beta-diagnosticos-coleccion-audit-20261020.json): colección anterior3769, ordinaria posterior3760, nueve escenarios conservados mediante selección explícita; todos los demás nodeids idénticos. Archivos originales y funciones verificados;622fuentes de producto iguales al contraste130958 y al corte QA17. Recibos Telegram de colección y auditoría comprobados. Ruff normaliza cuatro grupos de imports; colección explícita posterior conserva los mismos nueve escenarios. Esta prueba comprueba descubrimiento e imports, no ejecuta las3760pruebas ni nueve cargas.

Los comandos históricos de las evidencias conservan su ruta original. Para nuevas mediciones usar run_local_ci --profile focused --test con la ruta actual y el selector concreto; un worker, PostgreSQL/Redis propios, broker aislado, fuente nativa fijada y notificación terminal. Los ROI rechazados111/112 sólo pueden reproducirse con el SHA original exigido y su protocolo; no son autorización para repetirlos hasta cruzar umbral. El baseline conserva exactamente su función y muestreo, aunque su módulo se haya trasladado.

Un diagnóstico nuevo, como [114](114-diagnostico-estados-pendientes-beta-20261020.md), se declara por separado con su protocolo, escenarios y límites. No convierte automáticamente el inventario histórico de nueve en cobertura de nuevas mediciones. B07/B08 siguen abiertos; corto TCP FAIL y900s bloqueado.


## Diagnósticos posteriores de orden y etiquetas

El inventario anterior de nueve escenarios pertenece a su corte histórico. Se añaden explícitamente, fuera de colección ordinaria por nombre:

| Módulo explícito | Alcance | Estado propio |
| --- | --- | --- |
| tests/beta_global_rights_parity_diagnostic.py | nueve testigos, incluido selectivo | [127](127-diagnostico-orden-global-derechos-beta-20261020.md):8PASS+1PASS conciliados, no una sola ejecución9PASS; candidata no adoptada |
| tests/beta_promotion_label_projection_diagnostic.py | diez casos de formaSQL/paridad | [128](128-diagnostico-proyeccion-etiquetas-beta-20261020.md):10PASS de paridad;129rechaza adopción |
| tests/beta_label_projection_roi_diagnostic.py | un experimento152lecturas, no152tests | [129](129-contraste-proyeccion-etiquetas-beta-20261020.md):1PASS de integridad, candidata rechazada por criterios; sin adopción |

Son escenarios adicionales declarados, no una recuenta global actual de la colección ni aceptación beta. Las referencias de import entre diagnósticos se conservan; los SHA fijados impiden atribuir resultados a otro producto.
