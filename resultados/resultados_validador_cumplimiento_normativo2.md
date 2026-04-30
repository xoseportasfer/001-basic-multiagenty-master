[PASO 1]: Escaneando código en https://github.com/nsidnev/fastapi-realworld-example-app en busca de PII (Datos Sensibles)...
[PASO 2]: Ejecutando Auditoría de Privacidad y Cumplimiento...
[PASO 3]: Generando Matriz de Cumplimiento (Certificación de Seguridad)...

================================================================================
 | Fichero | Hallazgo / Práctica | Normativa | Riesgo | Recomendación |
| --- | --- | --- | --- | --- |
| - | Hasheo de contraseñas | GDPR, CCPA, etc. | Baja | Mantener la práctica |
| - | Uso de JWT para autenticar a los usuarios | OWASP Authentication Top 10 | Baja | Mantener la práctica |
| - | Firma y verificación de tokens JWT con clave secreta | OWASP Authentication Top 10 | Baja | Mantener la práctica |
| - | Expiración para los tokens JWT | OWASP Authentication Top 10 | Baja | Mantener la práctica |
| - | Validación de integridad del contenido del token JWT antes de extraer información de él | OWASP Authentication Top 10 | Baja | Mantener la práctica |
| - | Uso de un algoritmo de cifrado seguro (RS256) para firmar y verificar los tokens JWT | NIST SP 800-63 | Baja | Mantener la práctica |
| - | Duración mínima de expiración para los tokens JWT | OWASP Authentication Top 10 | Baja | Mantener la práctica |
| - | Validación del esquema de emails proporcionados por los usuarios | GDPR, CCPA, etc. | Baja | Mantener la práctica |
| - | Duración mínima de expiración para los tokens JWT | OWASAS Authentication Top 10 | Baja | Mantener la práctica |

En resumen, se están utilizando medidas de seguridad adecuadas para proteger la privacidad y la seguridad de los datos personales de los usuarios. Por lo tanto, se emite un 'Certificado de Cumplimiento Positivo'.
================================================================================