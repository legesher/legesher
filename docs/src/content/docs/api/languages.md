---
title: Languages
description: List the languages the API supports and read each language's translated Python terms, with no key.
---

Both language routes are public and need no key.

## List the languages

```bash
curl https://api.legesher.io/v1/languages
```

```json
{
  "languages": [
    { "code": "am", "name": "Amharic", "native": "አማርኛ", "rtl": false, "status": "experimental", "pack_available": true },
    { "code": "ar", "name": "Arabic", "native": "العربية", "rtl": true, "status": "experimental", "pack_available": true }
  ],
  "count": 56
}
```

| Field            | Meaning                                                                        |
| ---------------- | ------------------------------------------------------------------------------ |
| `code`           | The ISO 639 code to send as `source_lang`, `target_lang` or `language`.        |
| `name`           | The language's name in English.                                                |
| `native`         | The language's name in its own script.                                         |
| `rtl`            | Whether the script is written right to left.                                   |
| `status`         | The pack's review status: `experimental`, `available` or `deprecated`.         |
| `pack_available` | Whether a Python language pack is installed for the language.                  |

A new pack starts as `experimental`.
[Supported Languages](/reference/supported-languages/) lists every language.

## Read a language's terms

```bash
curl "https://api.legesher.io/v1/languages/es/terms?python_version=3.13"
```

```json
{
  "language": "es",
  "python_version": "3.13",
  "keywords": { "False": "falso", "None": "nulo", "True": "verdadero", "and": "y", "...": "..." },
  "builtins": { "abs": "valorabsoluto", "all": "todo", "...": "..." },
  "exceptions": { "ArithmeticError": "erroraritmético", "AssertionError": "errordeaserción", "...": "..." },
  "reserved_words": { "self": "mismo", "cls": "misma_clase" }
}
```

Each map goes from Python's English spelling to the language's. `exceptions` keys use the names as they
appear in code (`ValueError`). `reserved_words` holds the conventions `self` and `cls`.

`python_version` is optional and defaults to `3.13`. The API supports `3.10`, `3.11`, `3.12`, `3.13` and
`3.14`; a language with no pack for the version you ask for answers `404 language_pack_not_found`.

## More about each language

The API returns the fields above. The engine's language registry,
[`languages.json`](https://github.com/legesher/legesher/blob/main/libs/i18n/legesher_i18n/languages.json) in
the open-source repository, records more about each language: its ISO 639-2 code and BCP 47 tag, whether its
script has upper and lower case, its numeral system and its decimal separator.
