[PASO 1]: Escaneando código en https://github.com/nsidnev/fastapi-realworld-example-app en busca de PII (Datos Sensibles)...
[PASO 2]: Ejecutando Auditoría de Privacidad y Cumplimiento...
[PASO 3]: Generando Matriz de Cumplimiento (Certificación de Seguridad)...

================================================================================
 | Fichero | Hallazgo / Práctica | Normativa | Riesgo | Recomendación |
|--------|---------------------|-----------|-------|--------------|
| - | Hasheo de contraseñas | GDPR, CCPA, etc. | Baja | Mantener actualizado el algoritmo de hasheo y sal de hasheo según las mejores prácticas |
| - | Uso de JWT para autenticación | OWASP Authentication Cheat Sheet | Baja | Continuar utilizando JWT con la firma RSA y validación del contenido del token || - | Validación de esquema para datos de entrada en algunas partes del código | OWASP Input Validation Cheat Sheet | Baja | Aplicar validación de esquema a todos los puntos de entrada de datos |
| - | Validación de esquema para emails antes de guardarlos en la base de datos | GDPR, CCPA, etc. | Baja | Continuar validando el formato de email antes de su almacenamiento |
| - | Uso de una clave secreta para firmar y verificar los tokens JWT | OWASP Authentication Cheat Sheet | Baja | Mantener la clave secreta segura y actualizada |
| - | Expiración para los tokens JWT | OWASP Authentication Cheat Sheet | Baja | Ajustar la expiración de los tokens según las necesidades de seguridad y usabilidad del sistema |
| - | Validación de contenido del token JWT antes de procesarlo | OWASP Authentication Cheat Sheet | Baja | Continuar validando el contenido del token antes de su procesamiento |
| - | Uso de un algoritmo seguro para firmar y verificar los tokens JWT (RSA) | OWASP Authentication Cheat Sheet | Baja | Mantener actualizado el algoritmo de firma utilizado |
| - | No se detectaron riesgos evidentes en los códigos proporcionados que violen la privacidad o la seguridad de los datos personales. | GDPR, CCPA, etc. | Ninguno | Continuar manteniendo y actualizando el código para garantizar que siga siendo seguro y cumpliendo con las regulaciones aplicables. |
================================================================================