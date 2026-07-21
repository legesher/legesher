---
title: Política de privacidad — Extensión de VS Code y documentación
description: Prácticas de privacidad específicas de producto para la extensión de VS Code de Legesher y el sitio de documentación
sidebar:
  badge:
    text: revisión
    variant: caution
---

**Última actualización:** 20 de abril de 2026

> **¿Buscas la política general de la empresa?** Los términos generales — incluidos tus derechos, cómo contactarnos,
> los periodos de retención, las divulgaciones de GDPR/CCPA/CPRA y quiénes somos — están en la
> [política de privacidad general en www.legesher.io/privacy](https://www.legesher.io/privacy).
> Esta página cubre los detalles específicos de producto para la **extensión de VS Code** de Legesher y este
> **sitio de documentación** (`docs.legesher.io`).

## Alcance de esta página

Esta página complementa la [política de privacidad general](https://www.legesher.io/privacy) con detalles
específicos de:

- La **extensión de VS Code de Legesher**, publicada en el VS Code Marketplace
- El **sitio de documentación de Legesher** en `docs.legesher.io`

## Extensión de VS Code

### Procesamiento local

Tu código fuente se procesa por completo **localmente en tu equipo**. Nunca enviamos tu código a nuestros
servidores ni a servicios de terceros. Toda la traducción, los filtros de git y las funciones de IntelliSense
funcionan 100 % sin conexión.

### Telemetría básica (opcional)

Cuando está activada, recopilamos estadísticas de uso anónimas para ayudarnos a mejorar el producto:

- Eventos de activación de la extensión
- Frecuencia de uso de funcionalidades (qué comandos usas)
- Uso de paquetes de idioma (a qué idiomas traduces y desde cuáles)
- Métricas de rendimiento de la extensión (tiempo de arranque, capacidad de respuesta)
- Reportes de errores (informes de fallos, mensajes de error — sin contenido de código)

**Lo que NO recopilamos:**

- ❌ Tu código fuente ni el contenido de tus archivos
- ❌ Información de identificación personal (nombre, correo, dirección IP)
- ❌ Nombres de proyectos ni rutas de archivos
- ❌ Nombres de variables o funciones definidos por el usuario
- ❌ Valores literales de tu código
- ❌ Datos sensibles de ningún tipo

**Control:** puedes desactivar la telemetría en cualquier momento en la configuración de VS Code:

```json
{
  "legesher.telemetry.enabled": false
}
```

### Datos de entrenamiento de ML (solo con consentimiento explícito)

Si quieres, puedes ayudar a mejorar los modelos de traducción de Legesher compartiendo comentarios anónimos cuando
cambies nuestras sugerencias de traducción.

#### Qué recopilamos

- **Correcciones de traducción**: cuando cambias una sugerencia de Legesher (p. ej., "media" → "promedio")
- **Contexto del código**: estructura de alto nivel (función, variable, clase)
- **Tipo de operación**: categorización básica (aritmética, manipulación de cadenas, etc.)

#### Cómo se usa

Estos datos nos ayudan a:

1. Mejorar la precisión de la traducción para tu idioma
2. Entender cómo abordan los problemas de programación las personas hablantes nativas
3. Identificar patrones culturales y lingüísticos en la programación

#### Control

- **Configuración:** `legesher.telemetry.contributeToMLTraining`
- **Valor predeterminado:** `false` (debes dar tu consentimiento de forma explícita)
- **Cámbialo cuando quieras:** Configuración de VS Code → busca "Legesher ML Training"

### Almacenamiento de la telemetría

- **Ubicación:** Azure Application Insights (región de EE. UU.)
- **Retención:** 90 días para la telemetría; los datos anonimizados de entrenamiento de ML se conservan indefinidamente
- **Seguridad:** cifrado estándar de la industria (TLS 1.3 en tránsito, AES-256 en reposo)

### La telemetría propia de VS Code

VS Code recopila telemetría por su cuenta, independientemente de Legesher. Consulta la
[declaración de privacidad de VS Code](https://code.visualstudio.com/docs/supporting/faq#_microsoft-privacy-statement)
y la configuración de telemetría de VS Code.

## Sitio de documentación (docs.legesher.io)

### Alojamiento

Este sitio de documentación está alojado en [Vercel](https://vercel.com). Vercel procesa registros estándar de
acceso al servidor (direcciones IP, marcas de tiempo de las solicitudes, URL) como parte del funcionamiento normal
del alojamiento. Consulta la [política de privacidad de Vercel](https://vercel.com/legal/privacy-policy) para más
detalles.

### Analítica

Este sitio usa [Vercel Web Analytics](https://vercel.com/docs/analytics/privacy-policy), que está diseñado para
respetar la privacidad:

- **Sin cookies:** Vercel Web Analytics no usa cookies ni ningún almacenamiento del lado del cliente
- **Sin identificadores personales:** las visitas se identifican mediante un hash anónimo que no puede usarse para
  rastrear a personas entre sitios
- **Sin rastreo entre sitios:** los datos no permiten reconstruir sesiones de navegación ni identificar a usuarios
  individuales
- **Solo datos agregados:** vemos recuentos de vistas de página, referentes, geolocalización (a nivel de
  país/región), tipo de dispositivo y navegador, todo de forma agregada

Datos recopilados por vista de página: URL, referente, geolocalización (país/región), sistema operativo del
dispositivo, navegador, tipo de dispositivo y marca de tiempo. No se almacenan direcciones IP, agentes de usuario ni
información personal.

Como Vercel Web Analytics no recopila datos personales y no usa cookies, no se requiere ningún aviso de
consentimiento según el GDPR ni las normativas de ePrivacy.

### Fuentes

Todas las fuentes (Noto Sans) están autoalojadas y se sirven directamente desde `docs.legesher.io`. No se usan
servicios de fuentes de terceros, por lo que no se comparte ningún dato con proveedores externos al cargar las
páginas.

## Cumplimiento de GDPR y CCPA

Tus derechos bajo el GDPR, el GDPR del Reino Unido, la CCPA/CPRA y otras leyes regionales de privacidad aplican
tanto a la telemetría anónima como a los datos de entrenamiento de ML con consentimiento explícito descritos
arriba. En particular, puedes:

- **Desactivar toda la telemetría** en cualquier momento desde la configuración de VS Code (consulta las notas de
  _Control_ en cada sección anterior) — la forma más rápida de detener por completo la recopilación de datos
- **Solicitar acceso, corrección o eliminación** de cualquier dato que hayamos recopilado, escribiendo a
  [privacy@legesher.com](mailto:privacy@legesher.com)
- **Retirar el consentimiento de entrenamiento de ML** desactivando `legesher.telemetry.contributeToMLTraining`;
  la recopilación futura se detiene de inmediato, y puedes solicitar la eliminación de las contribuciones anónimas
  históricas escribiéndonos
- **Presentar una reclamación** ante tu autoridad local de protección de datos (EEE) o ante la
  [Information Commissioner's Office](https://ico.org.uk/make-a-complaint/) (Reino Unido) si consideras que hemos
  tratado tus datos de forma indebida

La enumeración completa de tus derechos — incluidos los artículos 15–22 del GDPR, las categorías de la CCPA/CPRA,
las leyes estatales de privacidad (Virginia, Colorado, Connecticut, Utah, Nevada), la base de las transferencias
internacionales, los periodos de retención y quiénes somos (Legesher Inc y Legesher Global Tech Limited) — está en
la [política de privacidad general](https://www.legesher.io/privacy).

Para preguntas de privacidad específicas sobre la extensión o este sitio de documentación, escribe a
[privacy@legesher.com](mailto:privacy@legesher.com).
