# B00-301 — Almacenamiento de contraseñas

Fecha: 2026-10-23. Conciliación documental de una captura; sin cambios de producto ni aceptación beta.

B00-301: 165 de 295 fuentes únicas conciliadas; quedan 130. Revisada la captura de almacenamiento de contraseñas y contrastada con la configuración declarada. B00 sigue abierto; nueve de los 18 puntos de beta están cerrados.

## Fuente y lectura

Fuente `source:ked12x8kuysogk5bu48l`, «Password Storage - OWASP Cheat Sheet Series». Se leyó íntegramente el texto capturado de 46.218 caracteres en cuatro intervalos contiguos: [0,12000), [12000,24000), [24000,36000) y [36000,46218). Su huella SHA-256 es `97e51b4e72ef599b2aefa09cb31fbf701ce775e8f90f62f67767a269a2b8ac18`. Se conserva el original y su procedencia en el [registro de fuentes](evidencias/b00-current-source-review-ledger-20261023.json). La lectura no incluye las referencias enlazadas ni una comprobación de la versión remota actual.

## Conciliación

La captura recomienda hash adaptativo con sal para contraseñas, coste ajustado al servidor y una estrategia de actualización. Examina Argon2id, scrypt, bcrypt y PBKDF2, límites de entrada, prehash, pepper y compatibilidad Unicode. Los ejemplos de migración y las afirmaciones generales de resistencia no prueban la seguridad del proyecto.

`config/settings.py` declara Argon2 como primera opción y PBKDF2 como alternativa. Esta inspección estática acredita sólo esa selección: no verifica los parámetros efectivos, costes bajo concurrencia, migración de credenciales, resistencia a abuso ni certificación FIPS. No se ha cambiado el algoritmo ni ejecutado una batería de autenticación para esta conciliación.

Las preferencias recuperables de B15 requieren una decisión de almacenamiento distinta del hash de contraseñas. Se mantienen cookies propias para visitantes, evaluación de almacenamiento privado cifrado para cuentas y decisiones pendientes sobre claves, retención y persistencia. No se incorpora pepper, infraestructura de secretos ni un proveedor por la lectura de esta referencia. Véase el [contrato funcional](14-contrato-funcional-v1.md).

## Estado

Incremento: una fuente nueva sobre las 164 anteriores, sin duplicidad. Quedan 130 fuentes pendientes. B00 y la aceptación global de beta siguen abiertos; B15 sigue siendo opcional. El corte previo se conserva en la [conciliación259](259-conciliacion-seo-seguridad-comercial-b00-20261023.md).
