[PASO 1]: Escaneando código en https://github.com/digininja/DVWA en busca de PII (Datos Sensibles)...
[PASO 2]: Ejecutando Auditoría de Privacidad y Cumplimiento...
[PASO 3]: Generando Matriz de Cumplimiento (Certificación de Seguridad)...

================================================================================
 | Fichero | Hallazgo / Práctica | Normativa | Riesgo | Recomendación |
| --- | --- | --- | --- | --- |
| Código en cuestión | Utilización de una lista de archivos PHP para buscar URLs | GDPR, PCI, HIPAA | Alta | Realizar una evaluación exhaustiva de la seguridad de datos y aplicar medidas de seguridad apropiadas para proteger contra ataques de inyección SQL, ataques de fuerza bruta, ataques de tipo "cross-site scripting" (XSS), ataques de tipo "cross-site request forgery" (CSRF), ataques de tipo "inyección de código malicioso", y ataques de tipo "man-in-the-middle" (MITM). |
| Código en cuestión | Uso de una lista de URLs a las que no se le permite acceder | GDPR, PCI, HIPAA | Alta | Asegurarse de que estas URLs no contengan información sensible y que no sean accesibles desde el exterior. |
| Código en cuestión | Uso de un User-Agent específico en las solicitudes HTTP | GDPR, PCI, HIPAA | Alta | Evitar el uso de User-Agents específicos y utilizar medidas de seguridad apropiadas para proteger contra ataques de tipo "fingerprinting" o "profiling". |
| Código en cuestión | Uso de una lista de URLs a las que se les permite acceder | GDPR, PCI, HIPAA | Alta | Asegurarse de que solo sean accesibles desde lugares seguros y que se utilicen medidas de seguridad apropiadas para proteger la información. |
| Código en cuestión | Falta de verificación de la integridad o confidencialidad de las solicitudes HTTP | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques que modifiquen la información en tránsito o accedan a información sensible sin autorización. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de inyección SQL | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de inyección SQL. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de fuerza bruta | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de fuerza bruta. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de tipo "cross-site scripting" (XSS) | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de tipo XSS. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de tipo "cross-site request forgery" (CSRF) | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de tipo CSRF. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de tipo "inyección de código malicioso" | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de tipo inyección de código malicioso. |
| Código en cuestión | Falta de medidas de seguridad contra ataques de tipo "man-in-the-middle" (MITM) | GDPR, PCI, HIPAA | Alta | Aplicar medidas de seguridad apropiadas para proteger contra ataques de tipo MITM. |
================================================================================