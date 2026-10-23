---
title: Idiomas compatibles
description: Los 52 idiomas compatibles con Legesher para programar en tu idioma nativo
sidebar:
  badge:
    text: revisión
    variant: caution
---

Legesher es actualmente compatible con **52 idiomas** para el desarrollo en Python. Cada paquete de idioma incluye
las 37 palabras clave, las 72 funciones integradas y las 66 excepciones de Python en el idioma de destino, lo que te
permite escribir código Python plenamente funcional en tu idioma nativo.

<!-- VISUAL: [Demo 4] Grid showing the same code snippet in 6+ visually distinct languages (Arabic, Japanese, Chinese, Spanish, French, Hindi) -->

## Paquetes de idioma

Todos los paquetes de idioma tienen actualmente el estado **experimental**. Los paquetes se generan inicialmente con los modelos Aya de Cohere y después esperan la validación de la comunidad antes de pasar al estado **aceptado**.

| Código | Idioma            | Nombre nativo    | RTL | Estado       |
|--------|-------------------|------------------|-----|--------------|
| am     | Amárico           | አማርኛ             | No  | Experimental |
| ar     | Árabe             | العربية          | Sí  | Experimental |
| bn     | Bengalí           | বাংলা            | No  | Experimental |
| bs     | Bosnio            | Bosanski         | No  | Experimental |
| ca     | Catalán           | Català           | No  | Experimental |
| cs     | Checo             | Čeština          | No  | Experimental |
| cy     | Galés             | Cymraeg          | No  | Experimental |
| da     | Danés             | Dansk            | No  | Experimental |
| de     | Alemán            | Deutsch          | No  | Experimental |
| el     | Griego            | Ελληνικά         | No  | Experimental |
| en     | Inglés            | English          | No  | Experimental |
| es     | Español           | Español          | No  | Experimental |
| fa     | Persa             | فارسی            | Sí  | Experimental |
| fi     | Finés             | Suomi            | No  | Experimental |
| fr     | Francés           | Français         | No  | Experimental |
| ga     | Irlandés          | Gaeilge          | No  | Experimental |
| gd     | Gaélico escocés   | Gàidhlig         | No  | Experimental |
| gl     | Gallego           | Galego           | No  | Experimental |
| gu     | Guyaratí          | ગુજરાતી         | No  | Experimental |
| he     | Hebreo            | עברית            | Sí  | Experimental |
| hi     | Hindi             | हिन्दी           | No  | Experimental |
| hr     | Croata            | Hrvatski         | No  | Experimental |
| hu     | Húngaro           | Magyar           | No  | Experimental |
| id     | Indonesio         | Bahasa Indonesia | No  | Experimental |
| it     | Italiano          | Italiano         | No  | Experimental |
| ja     | Japonés           | 日本語           | No  | Experimental |
| kn     | Canarés           | ಕನ್ನಡ            | No  | Experimental |
| ko     | Coreano           | 한국어           | No  | Experimental |
| lv     | Letón             | Latviešu         | No  | Experimental |
| mk     | Macedonio         | Македонски       | No  | Experimental |
| ml     | Malayalam         | മലയാളം           | No  | Experimental |
| mn     | Mongol            | Монгол           | No  | Experimental |
| ms     | Malayo            | Bahasa Melayu    | No  | Experimental |
| my     | Birmano           | မြန်မာ           | No  | Experimental |
| nl     | Neerlandés        | Nederlands       | No  | Experimental |
| no     | Noruego           | Norsk            | No  | Experimental |
| pl     | Polaco            | Polski           | No  | Experimental |
| pt     | Portugués         | Português        | No  | Experimental |
| ro     | Rumano            | Română           | No  | Experimental |
| ru     | Ruso              | Русский          | No  | Experimental |
| si     | Cingalés          | සිංහල            | No  | Experimental |
| sr     | Serbio            | Српски           | No  | Experimental |
| su     | Sundanés          | Basa Sunda       | No  | Experimental |
| sv     | Sueco             | Svenska          | No  | Experimental |
| te     | Telugu            | తెలుగు           | No  | Experimental |
| th     | Tailandés         | ไทย              | No  | Experimental |
| tr     | Turco             | Türkçe           | No  | Experimental |
| uk     | Ucraniano         | Українська       | No  | Experimental |
| ur     | Urdu              | اردو             | Sí  | Experimental |
| uz     | Uzbeko            | O'zbek           | No  | Experimental |
| vi     | Vietnamita        | Tiếng Việt       | No  | Experimental |
| zh     | Chino             | 中文             | No  | Experimental |

## Compatibilidad con versiones de Python

Todos los paquetes de idioma son compatibles con Python **3.10 a 3.14** mediante un sistema de herencia de versiones. Las traducciones base viven en el paquete 3.10, y cada versión posterior de Python hereda esas traducciones e incorpora las palabras clave nuevas introducidas en esa versión.

## Compatibilidad con escritura de derecha a izquierda (RTL)

El árabe, el hebreo, el persa y el urdu son idiomas que se escriben de derecha a izquierda. Legesher traduce las palabras clave RTL igual que las de cualquier otro idioma, y el panel de traducción de la extensión de VS Code aplica la dirección y la alineación del texto RTL cuando hay un idioma RTL activo.

<!-- VISUAL: [Demo 5] Screenshot of VS Code showing Arabic or Hebrew RTL code -->

## Estado de las traducciones

- **Experimental**: las traducciones funcionan, pero aún no han sido validadas por miembros de la comunidad
  hablantes nativos. Es el estado actual de los 52 paquetes.
- **Disponible**: las traducciones han sido revisadas y aprobadas por hablantes nativos. Este estado se asignará
  tras la validación comunitaria (prevista para la v1.0.0).
- **Obsoleto**: el paquete de idioma ya no se mantiene activamente y queda excluido de las listas de idiomas
  activos.

## Añade tu idioma

Si tu idioma no aparece en la lista anterior, puedes contribuir con un nuevo paquete de idioma. Cada paquete requiere traducir las palabras clave, las funciones integradas y las excepciones de Python a tu idioma. Consulta la [guía de contribución en GitHub](https://github.com/legesher/legesher/blob/main/CONTRIBUTING.md) para ver las instrucciones.
