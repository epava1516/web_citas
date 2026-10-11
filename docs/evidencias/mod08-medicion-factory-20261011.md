# Diagnóstico terminal de preparación de clientes

Solo un caso sintético completo. Fuentes608dfd0,1151hashes por ejecución y retirada propia comprobados independientemente. No aceptación dos casos/N3.

| Métrica | Muestras | Anterior | Actual | Variación | Objetivo |
| --- | ---: | ---: | ---: | ---: | ---: |
| whole | 383 | 3.885480 s | 3.865976 s | -0.50% | 2 s |
| matched123 | 123 | 3.376274 s | 3.203978 s | -5.10% | 2 s |
| generation | 1 | 45.953214 s | 44.090730 s | -4.05% | 120 s |
| final_preparation | 1 | 14.613018 s | 15.200386 s | +4.02% | 30 s |
| final_inspection | 1 | 4.183466 s | 3.664138 s | -12.41% | 30 s |
| final_approval | 1 | 4.024230 s | 4.225175 s | +4.99% | 5 s |
| closure | 1 | 15.602488 s | 16.213333 s | +3.92% | 30 s |
| json_download | 3 | 6.908405 s | 7.313810 s | +5.87% | 5 s |
| binary_download | 8 | 7.705974 s | 7.418959 s | -3.72% | 5 s |

n1 no p95; n3/n8 nearest-rank coincide con máximo y no cumple mínimo20porcaso/variante. El listado mide lotes completos de4páginas. Diferencias entre ejecuciones de cambio diagnóstico no demuestran mejora productiva.

| Request perfilado | Worker | Constructor wall | Constructor CPU | Factory wall total |
| --- | ---: | ---: | ---: | ---: |
| capacity-profile-binary_download_proxy-99.txt | 1 | 0.655834 s | 0.351230 s | 0.663358 s |
| capacity-profile-binary_download_proxy-99.txt | 2 | 0.497666 s | 0.269670 s | 0.504777 s |
| capacity-profile-binary_download-100.txt | 1 | 0.504033 s | 0.258077 s | 0.513257 s |
| capacity-profile-binary_download-100.txt | 2 | 0.574923 s | 0.330977 s | 0.582333 s |
| capacity-profile-json_download_proxy-100.txt | 1 | 0.521710 s | 0.262827 s | 0.529969 s |
| capacity-profile-json_download_proxy-100.txt | 2 | 0.369109 s | 0.241323 s | 0.376943 s |
| capacity-profile-json_download-99.txt | 1 | 0.707936 s | 0.349131 s | 0.716387 s |
| capacity-profile-json_download-99.txt | 2 | 0.513026 s | 0.301197 s | 0.521898 s |

Fases inclusivas y solapadas; no sumar trabajadores ni atribuir estos tiempos al p95. Cada trabajador construye1cliente;27repositorios frescos por request en total. No se cachea ring/crypto/autoridad. Próximo análisis: reducir construcción conservando protocolos, hooks y configuración fresca.
