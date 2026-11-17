---
title: Revisar un paquete de idioma
description: Cómo revisar el paquete de tu idioma mediante una pull request y qué ocurre después.
sidebar:
  badge:
    text: revisión
    variant: caution
---

Todo paquete de idioma empieza como experimental: una máquina propuso las palabras, y solo quienes
hablan el idioma pueden mejorarlas. Revisar un paquete es la forma de dar forma a las palabras con
las que se programa en tu idioma.

Las revisiones llegan como pull requests en [legesher/language-packs](https://github.com/legesher/language-packs). Necesitas una cuenta de
GitHub y sentirte cómodo editando un archivo y abriendo una pull request. No necesitas saber Python
para revisar un paquete de Python.

## Revisar en cuatro pasos

1. Copia la plantilla de tu idioma en tu propio archivo de revisión. La etiqueta es el código de
   tu idioma (`reference/es.md` es el español) y username es tu nombre de usuario de GitHub.

   ```text
   reference/<tag>.md
   → reviews/<tag>/<tag>-<username>.md
   ```
2. Revisa los términos. Pon `✓` en Comments para respaldar la palabra actual, escribe `Keep` con una
   nota para respaldarla con una limitación, o pon otra palabra en Suggested con tu razonamiento en
   Comments. Deja una fila sin tocar si no tienes opinión.
3. Completa "About you", marca las casillas Required en "Before you submit" y deja una sola opción
   en la línea "Credit me as".
4. Abre una pull request con tu archivo. Firma cada commit:

   ```sh
   git commit -s
   ```

## Conviene saber

- **Una sugerencia añade una opción.** Nunca reemplaza la palabra actual. Otras personas revisoras
  pueden respaldarla, y un paquete solo cambia cuando la evidencia lo indica.
- **Las casillas Required las marcas tú.** La comprobación de la revisión falla sin ellas, y nadie
  puede marcarlas por ti, porque registran tu propio consentimiento.
- **Tu archivo es público una vez fusionado, comentarios incluidos.** Nunca pongas en él una
  dirección de correo ni datos de contacto privados.

## Qué pasa después

1. Una persona mantenedora ejecuta la comprobación, lee cada línea y responde en tu pull request en
   un plazo de 7 días: o está lista para fusionarse, o la respuesta indica exactamente qué corregir.
2. Sube las correcciones a la misma rama, con cada commit firmado.
3. Tras la fusión, tus respaldos y sugerencias se suman al corpus lingüístico público. Una palabra
   nueva que sugieras queda en espera hasta que una persona mantenedora la apruebe.
4. Los respaldos se acumulan. Cuando un idioma supera un umbral de revisión, se publica una nueva
   versión del paquete, que puede pasar de experimental a revisado y, mediante una sesión de
   ratificación, a oficial.

## Más información

- [Empieza aquí](https://github.com/legesher/language-packs#start-here) en el repositorio language-packs (en inglés)
- [La guía de revisión](https://github.com/legesher/language-packs/blob/main/REVIEWING.md) (en inglés): cómo elegir una palabra, quién puede revisar y cómo un
  paquete llega a ser oficial
- ¿Tu idioma aún no tiene paquete? [Solicita un idioma nuevo](https://github.com/legesher/legesher/issues/new?template=add_language.yml).

Pronto habrá más formas de contribuir.
