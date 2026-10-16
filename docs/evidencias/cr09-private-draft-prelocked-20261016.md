# Escritores prebloqueados: regresión de 0021

Run `20261016-051054-7133ceaf`, HEAD `f17b060539399a68f9852afd210a1ab277147a55` más instrumento nuevo registrado en source-hashes. Resultado: **1 PASS, 1 FAIL en 56,02 s**. Fuentes congeladas, ausencia de runner/child, temporal y contenedores propios verificadas independientemente; unidad terminada con fallo y cgroup vacío. Originales del instrumento y migración conservados dentro del artefacto ignorado.

| Control | Resultado |
|---|---|
| Funciones originales 0020, restauradas exactamente al salir | Ambos escritores completan; Dirty drena y estado coincide con nativo |
| Migración 0021 actual | Un escritor aborta con `OperationalError: deadlock detected`; el otro completa |

Dos anuncios sintéticos publicados unidos por Match. Dos transacciones bloquean primero su propio Listing con SELECT FOR UPDATE, sincronizan barrera y modifican removed_at de su propia Photo. El nuevo helper intenta bloquear ambos Listings: cada transacción espera al dueño del otro anuncio. PostgreSQL detectó el ciclo entre procesos 99/100, transacciones 1313/1312, dentro de listings_publication_lock llamado por lpd_mediafiles_photo. Lock timeout 5 s y futuros 15 s. No carga ni perfilador, sólo PG propio y límites existentes.

El orden previo es relevante: rights_scope.locked_case(lock_listing=True) bloquea Listing, y erasure_execution modifica Photo posteriormente. Esta prueba reproduce el orden de locks, **no ejecuta dos borrados de derechos completos**. El control previo de fotos opuestas sin Listing prebloqueado no cubría esta condición.

La optimización 0021 no es aceptable con este defecto. Los 24 PASS N2a y 55 PASS N2b no lo excluyen; el ROI secuencial de 13,9–26,5 % tampoco compensa una regresión de concurrencia. No hay nuevo p95. Mantener FAIL, analizar protocolo de exclusión antes de corregir o descartar candidato; no lanzar carga ni declarar CR09/N3. Versión local experimental, sin despliegue.
