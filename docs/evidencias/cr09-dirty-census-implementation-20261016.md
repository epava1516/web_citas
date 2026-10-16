# Censo dirty limitado al snapshot repetible propio

Implementación `6daa170`: all_state_current se reutiliza para acotar unknown al conjunto dirty sólo en trusted_snapshot=True. complete continúa falso con dirty, por lo que no se habilita la proyección de población. Si cobertura/versiones son incompletas se conserva el anti-join global; en transacción heredada dirty se conserva el algoritmo original sin consulta extra de censo. Misma población, orden, guardia final y límites dirty1000/unknown48. No caché de resultados o autoridad.

Motivación y ahorro aislado en [contraste](cr09-dirty-census-contrast-20261016.md), con antecedentes y límites conservados. Revisión independiente nativa detectó y evitó el contraejemplo READCOMMITTED antes de implementación.

[Paridad](cr09-dirty-census-parity-terminal-20261016.json):run003139-54108bb5,16PASS224,83s,0omisiones. Cuatro variantes nuevas actual/faltante/antigua/heredada comparan cuerpos nativos ESEN; pertenencia con filtros/páginas y elegibilidad/revocación; coberturaFK/censo y concurrencia de aprobación propias/heredadas. [Límites](cr09-dirty-census-limits-terminal-20261016.json):run003644-93458c9a,2PASS51,67s;48 permite página/49 fallback. Selecciones distintas, no una N3 común. Fuentes congeladas ycleanupindependientes comprobados antes de mutar/commitear.

La evidencia HTTP ahora registra identidad canónica. Adaptador propio exige native-sealed antes de recursos y conserva entorno. Ensayo limpio iniciado enunidadcr09-dirty-census-clean-20261016, SHA6daa170:4sync, afinidad0–3/controller3584MiBswap0pids512;PG1CPUafinidad4/1536MiBsinSwap/pids128;Redis0,2CPUafinidad5/128MiBsinSwap/pids64.10ksintéticos/20rps60s/1subida/Celery2+Beat,normalrefresh/generatorfreeze, reglas yprobes existentes sin cambios, sinperfiladores niobservadores deworkers. Resultado pendiente.

SiPASS repetiruna vez sin cambios; siFAIL conservar ydiagnosticar aparte,noencadenar15min. No aceptación globalCR09/N3. RuntimeDocker2workers permanece pendiente de coherencia con topología finalmente aceptada.


Resultado posterior: ensayo003849-cc3fd173FAIL,p95mezcla0,904873942s,1200completas0errores,generadorválido. No se repite. Detalle ycomparación en[mediciónlimpia](cr09-dirty-census-clean-20261016.md).
