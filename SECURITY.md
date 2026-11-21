# Política de seguridad

Gracias por ayudar a mantener ChronoCode y a sus usuarios seguros.

## Versiones soportadas

Solo la última versión publicada recibe correcciones de seguridad.

| Versión | Soportada |
|---------|-----------|
| 1.0.x   | Sí        |
| < 1.0   | No        |

## Reportar una vulnerabilidad

**No abras un Issue público para reportar vulnerabilidades.** Un reporte público puede poner en riesgo a los usuarios antes de que exista una corrección.

Envía tu reporte por correo electrónico a:

**jesusmoralesrodriguez925@gmail.com**

Usa como asunto: `[SEGURIDAD] ChronoCode: descripción breve`.

Incluye, en la medida de lo posible:

- Descripción del problema y componente afectado (archivo, función o comando).
- Pasos para reproducirlo, con la versión y el sistema operativo (Termux, Windows, macOS o Linux).
- Impacto potencial y, si lo tienes, una prueba de concepto.
- Si lo has compartido con alguien más.

## Qué puedes esperar

| Etapa | Plazo objetivo |
|-------|----------------|
| Acuse de recibo | 48 horas |
| Confirmación o descarte del problema | 7 días |
| Corrección y publicación de una versión | Según la gravedad y la complejidad |

Trabajaremos contigo para validar el problema y coordinar la publicación. Te pedimos que no hagas público el detalle hasta que exista una corrección o acordemos un plazo.

Si el reporte es válido, lo reconoceremos en las notas de la versión, salvo que prefieras permanecer anónimo.

## Alcance

Son de interés los problemas que afecten a:

- La ejecución de comandos: evasión de la denylist, de la revisión por IA o de la confirmación del usuario.
- La escritura de archivos fuera del directorio de trabajo o en rutas sensibles.
- La exposición de API Keys, del archivo `.env` o de otros secretos del usuario.
- La inyección de instrucciones a través de respuestas del modelo o de archivos procesados.
- La instalación (`install.sh`) y la configuración del alias global.

No son de interés, salvo que tengan impacto de seguridad demostrable:

- Limitaciones conocidas de la denylist o de la revisión por IA, que son capas heurísticas y no un aislamiento completo.
- Fallos de los proveedores de IA de terceros.
- Problemas de interfaz sin impacto de seguridad.

## Recomendaciones para usuarios

- Lee cada comando antes de confirmarlo. Las protecciones reducen el riesgo, pero no lo eliminan.
- No compartas tu archivo `.env` ni lo subas a repositorios.
- Usa claves de API con los permisos mínimos y revócalas si sospechas que se han expuesto.
- Mantén ChronoCode actualizado a la última versión.

## Reconocimientos

Las personas que reporten vulnerabilidades válidas y lo deseen aparecerán aquí, en orden cronológico.
