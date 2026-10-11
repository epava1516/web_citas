# MOD-08: memoria del ciclo pipeline/HMAC

| Fase | Cota global anterior (GiB) | Cota global nueva (GiB) | Pico cgroup app anterior (GiB) | Pico cgroup app nuevo (GiB) |
|---|---:|---:|---:|---:|
| capture | 1.817 | 1.917 | 1.196 | 1.193 |
| use | 2.657 | 2.714 | 1.709 | 1.730 |

Todos los registros comparados sin swap ni OOM. Cotas globales bajo 6GiB. Suma conservadora de picos cgroup disjuntos, incluye cache/tmpfs y techo completo del controlador: no pico simultáneo ni RSS de aplicación. Un caso diagnóstico; aceptación completa pendiente.
