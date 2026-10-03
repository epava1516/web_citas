# CR-02 — Agencias, asignación y MFA, interfaz v1

Todas las rutas bajo /es o /en; sesión confirmada, documentos vigentes y MFA para agencias, miembros activos y staff. Los visitantes pueden activar MFA voluntario. La autorización se comprueba servidor en cada operación y consulta, también tras revocación.

| Ruta | Método | Permiso/resultado |
| --- | --- | --- |
| /account/mfa/enroll/ | GET/POST | sesión; contraseña actual antes de generar clave; confirmación TOTP habilita y muestra diez códigos una sola vez |
| /account/mfa/ | GET/POST | sesión; TOTP o recuperación, 302 panel si válido |
| /agency/create/ | GET/POST | sesión+MFA; propietario único, cambio de role servidor; particular con persona propia requiere transferencia |
| /agency/{id}/ | GET | propietario ve todas sus personas/equipo; editor solo asignadas; ajeno 403 |
| /agency/{id}/invite/ | GET/POST | propietario; email, invitación de dos días; envío simulado/pruebas |
| /agency/invitation/{id}/{secret}/ | GET/POST | cuenta con email destino y MFA; GET no consume, POST de un solo uso |
| /agency/{id}/people/add/ | GET/POST | propietario; alias; cuota inicial diez personas, afinada a pendientes en CR-03/06 |
| /agency/{id}/people/{person}/assign/ | GET/POST | propietario; editor debe ser miembro activo de esa agencia; ninguno retira asignación |
| /agency/{id}/members/{member}/revoke/ | POST | propietario; revoca miembro, asignaciones e invitaciones pendientes al email |

Person tiene exactamente un gestor: individual XOR agencia mediante CHECK PostgreSQL. Alias no prueba unicidad física; verificación y antiduplicados se completan CR-03/05. Editor no puede añadir personas, invitar equipo ni asignarse perfiles. Propietario es responsable de todas las publicaciones sin conceder acceso global a otros modelos.

TOTP: secreto cifrado Fernet; clave independiente MFA_ENCRYPTION_KEY exigida en producción. Derivación del secreto Django solo en desarrollo, documentada como local. Ventana ±1 intervalo, contador consumido guardado bajo bloqueo PostgreSQL para impedir replay. Códigos de recuperación aleatorios de 128 bits, HMAC almacenado, consumo atómico, nunca texto persistido. Sesión guarda versión de MFA; nuevo login exige factor. Rate limit enrol/challenge diez por quince minutos.

Wireframes: panel cuenta → contraseña actual → clave manual para autenticador → código → códigos de recuperación → agencia → personas y equipo. Agencia no publica modelos automáticamente: pantalla señala verificaciones pendientes. Sin QR externo, tracking ni envío de secretos a terceros.

Pendiente operativo B-B: rotación de clave, recuperación asistida segura, política final y alertas; no soporte que omita MFA. Integraciones reales siguen pendientes.
