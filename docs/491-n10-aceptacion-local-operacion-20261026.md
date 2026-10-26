# N10 — acta de aceptación técnica local

N10 queda aceptado en el alcance operativo local del contrato340/roadmap341. **10 de 13 bloques obligatorios aceptados**; el objetivo completo continúa activo. El producto sigue alpha/noindex, sin proveedores elegidos ni autorización de apertura.

## Requisitos y evidencias

La [matriz canónica77](evidencias/n10-e-matriz77-disposiciones-20261026.json) conserva exactamente los IDs y variantes N00: 15 comandos propios, 31 del framework, 11 runbooks, 16 patrones Admin, una acción global, una ruta health y dos IDs dispatch. Son disposiciones acotadas, no77 pruebas ni funcionalidades completas declaradas PASS. Cada fila identifica fuente, modos, autoridad, efectos, reversibilidad/replay, evidencia, coste y límites.

| Requisito | Evidencia contrastada | Resultado y límite |
|---|---|---|
| Censo original y trazabilidad | Matriz77 contra N00 y variantes originales | 77 disposiciones verificadas; no sustitución del censo |
| CLI y acciones seleccionadas | 46 comandos,83 fuentes,133 testigos originales, revalidación E | Ejecución directa, servicio equivalente, metadata y no selección diferenciados |
| Operación y recuperación | 11 runbooks,120 PASS y2 SKIP originales; restauraciones reales | Alcances locales y puentes de fuente explícitos; no SLA del destino |
| Admin y autoridad tras esperas | A16 casos; GroupAdmin y helpers preservados | Nueve esperas PostgreSQL, tres válidas y seis denegaciones; CRUD/autorevocación |
| Login/MFA y cuenta nativos | D10 únicos entre dos cortes; E2 ES/EN | Ceremonias reales y efectos exactos; no suma ficticia de ejecuciones |
| Retorno de la fuente actual | F1, tres fases, doce workers, seis HTTP200 | Continuidad de lectura/sesión admitida; no despliegue ni nueva admisión anterior |
| Medición | B/C/E/F y cuatro restores | Relojes de app separados de QA, sin speedup causal inventado |
| Integridad y custodia | Congelaciones, cleanup, Telegram, negativos y archivos compactos | Fuentes y evidencias contrastadas por root; no aceptación por registro |

Framework31: check/makemigrations/migrate tienen modos seleccionados reales; los otros28 quedan no seleccionados con motivo o condicionados a proveedor. No se ejecutaron comandos destructivos, shell o correo para aparentar cobertura. configure_rights_evidence_role conserva evidencia del servicio/initializer y wrapper de tres líneas; su CLI standalone no fue ejecutada. operational_snapshot sí tiene seis invocaciones positivas nativas B, aparte del collector y negativo anterior.

Runbooks: al corte C eran94 identidades; ahora93 son byteidénticas y apps/core/admin.py tiene puente explícito por el receptor D. GroupAdmin/helpers son AST equivalentes; F cargó las dos fuentes reales. No se afirma identidad de94 archivos. El retorno histórico de tres imágenes y726 archivos queda histórico. Dos IDs dispatch corresponden a un productor on_commit real: 21 fuentes iguales más puente del argumento default recipient_review=False; once testigos F75 originales. Eager no acredita broker/worker nuevo.

## Antes y después, con relojes separados

| Acción | Antes | Después verificado | Interpretación |
|---|---|---|---|
| GroupAdmin tras revocación durante espera | 1 PASS/1 FAIL,55,892 s QA | 16 PASS,159,971 s QA | Corrección funcional; no mejora de latencia |
| Login Admin epoch1 | 1 PASS/1 FAIL,59,198 s QA | 10 casos únicos entre primera candidata y focal | Primera candidata7 PASS/3 FAIL por oráculo RateWindow; focal4 PASS,76,644 s; seis reutilizados por identidad |
| Arranque Gunicorn propio | Sin comparador equivalente | 4 workers listos en1,690 s | Sondeo50ms, no SLA |
| Health | Sin comparador equivalente | Primera62,325 ms; mediana cinco3,164 ms | TCP local, cohorte fija |
| operational_snapshot nativo | Sin positivo CLI comparable | Primera129,319 ms; mediana cinco127,491 ms,50 SQL | In-process; no coste de spawn Python |
| Group changelist ES / EN | Sin comparador equivalente | Primera49,497 /39,126 ms; mediana cinco29,618 /40,819 ms,9 SQL | Cohorte de un target, no crecimiento |
| Password Admin ES / EN | Sin comparador equivalente | 230,965 /256,933 ms,12 SQL | Una muestra por idioma |
| Sesión peer tras cambio ES / EN | Sin comparador equivalente | 10,036 /15,265 ms,4 SQL | Hash antiguo invalida sesión; no revocación universal de tokens |
| Logout Admin ES / EN | Sin comparador equivalente | 16,658 /18,222 ms,6 SQL | POST/CSRF nativos y efecto exacto |
| Retorno actual→anterior→actual | Sin comparador equivalente actual | F:1 PASS,57,716 s QA; tiempos de proceso/HTTP en490 | QA y latencia separados; no image switch |

| Restore propio real | Backup | Restore y reconciliación | Bytes |
|---|---:|---:|---:|
| Plain, misma clave | 0,876 s | 6,537 s | 1.060.546 |
| Plain, lectura clave retenida | 0,777 s | 6,297 s | 1.060.560 |
| Cifrado, misma clave | 0,770 s | 5,659 s | 1.060.611 |
| Cifrado, lectura clave retenida | 0,811 s | 5,925 s | 1.060.578 |

Estos relojes comprenden etapas de backup/restore locales; no PITR, offsite, retención completa o SLA. La comprobación incluyó PostgreSQL real, medios, autoridad independiente, peer intacto, sesiones/grants invalidados, triggers y limpieza; publication_authorized=False.

## Conciliación y límites

A16, B2, C2, E2 y F1 son ejecuciones distintas. D conserva original negativo, primera candidata7 PASS/3 FAIL y focal4 PASS; diez escenarios únicos aceptados entre dos cortes, no una batería10 PASS ni once casos por repetición. Los tres FAIL fueron errores del oráculo sobre escrituras legítimas RateWindow, corregidos sin tocar la app. El whole histórico sigue ERROR:3697 PASS,129 SKIP y3 FAIL,3829 casos reales; diferencia frente a3833 metadata preservada. No se convierte en regresión global PASS.

Producto `0dcf89f`; SHA admin actual `d7087491e7924216d09401b2505e739b5fb71bc445e8bec44db88f824bc2beea`. Desde ese commit no hay cambio de aplicación. La matriz provisional E queda conservada en su archivo histórico. La actualización F cambia sólo la disposición de retorno y cabeceras de aceptación, manteniendo otras76 filas. SHA matriz actual `c6f504c524f4b155a46bc6bbc1ee89a49e46cbae2cb7060a3f1de8b58c88cdde`.

Referencias: [A477](477-n10-a-groupadmin-autoridad-verificada-20261026.md), [B479](479-n10-b-referencias-operativas-verificadas-20261026.md), resultado C481, D486 y E488 conservados en docs; [F490](490-n10-f-retorno-procesos-actuales-verificado-20261026.md) y su archivo compacto contienen el gate de aceptación de ocho requisitos. Las referencias históricas se verifican por sus archivos/manifiestos, no por una propuesta o etiqueta verde.

## Pendientes del contrato

Sigue N11: candidata integrada y matriz requisito→acción→candidata→prueba→resultado→límite, conciliando negativos, exclusiones, fuentes y recursos. N15 requiere grafo completo nuevo antes del inventario diferencial, relevo frontend y acta, terminando con vaciado efectivo de artifacts según contrato. N02 residual queda pospuesto por el usuario al final del desarrollo con sus FAIL temporales visibles. N12–N14 continúan condicionados, no PASS.

No despliegue, migraciones persistentes, cambios de servicios/proveedores/CI ni repetición de QA válido por instalación de capacidades. Los quince cambios laterales permanecen fuera de esta entrega.
