---
title: Supported Languages
description: All 26 languages supported by Legesher for coding in your native language
---

Legesher currently supports **26 languages** for Python development. Each language pack consists of
Python's 37 keywords, 72 builtins, and 66 exceptions in the target language, enabling you to write fully functional Python
code in your native language.

<!-- VISUAL: [Demo 4] Grid showing the same code snippet in 6+ visually distinct languages (Arabic, Japanese, Chinese, Spanish, French, Hindi) -->

## Language Packs

All language packs currently have **experimental** status. Language packs are initially generated via Cohere's Aya models and then await community validation before being promoted to **accepted** status.

| Code | Language   | Native Name      | RTL | Status       |
|------|------------|------------------|-----|--------------|
| ar   | Arabic     | العربية          | Yes | Experimental |
| da   | Danish     | Dansk            | No  | Experimental |
| de   | German     | Deutsch          | No  | Experimental |
| el   | Greek      | Ελληνικά         | No  | Experimental |
| en   | English    | English          | No  | Experimental |
| es   | Spanish    | Español          | No  | Experimental |
| fi   | Finnish    | Suomi            | No  | Experimental |
| fr   | French     | Français         | No  | Experimental |
| he   | Hebrew     | עברית            | Yes | Experimental |
| hi   | Hindi      | हिन्दी           | No  | Experimental |
| hu   | Hungarian  | Magyar           | No  | Experimental |
| id   | Indonesian | Bahasa Indonesia | No  | Experimental |
| it   | Italian    | Italiano         | No  | Experimental |
| ja   | Japanese   | 日本語           | No  | Experimental |
| ko   | Korean     | 한국어           | No  | Experimental |
| ms   | Malay      | Bahasa Melayu    | No  | Experimental |
| nl   | Dutch      | Nederlands       | No  | Experimental |
| no   | Norwegian  | Norsk            | No  | Experimental |
| pl   | Polish     | Polski           | No  | Experimental |
| pt   | Portuguese | Português        | No  | Experimental |
| ru   | Russian    | Русский          | No  | Experimental |
| sv   | Swedish    | Svenska          | No  | Experimental |
| th   | Thai       | ไทย              | No  | Experimental |
| tr   | Turkish    | Türkçe           | No  | Experimental |
| vi   | Vietnamese | Tiếng Việt       | No  | Experimental |
| zh   | Chinese    | 中文             | No  | Experimental |

## Python Version Support

All language packs support Python **3.10 through 3.14** using a version inheritance system. The base translations live in the 3.10 pack, and each subsequent Python version inherits those translations while adding any new keywords introduced in that version.

## Right-to-Left (RTL) Support

Arabic and Hebrew are right-to-left languages. Legesher translates RTL keywords the same as any other
language, and the VS Code extension's translation panel applies RTL text direction and alignment when
an RTL language is active.

<!-- VISUAL: [Demo 5] Screenshot of VS Code showing Arabic or Hebrew RTL code -->

## Translation Status

- **Experimental**: Translations are functional but have not yet been validated by native-speaking
  community members. This is the current status for all 26 packs.
- **Available**: Translations have been reviewed and approved by native speakers. This status will be
  assigned after community validation (planned for v1.0.0).
- **Deprecated**: Language pack is no longer actively maintained and is excluded from active language
  lists.

## Adding Your Language

If your language isn't listed above, you can contribute a new language pack. Each pack requires translating Python's keywords, builtins, and exceptions into your language. See the [contributing guide on GitHub](https://github.com/legesher/legesher/blob/main/CONTRIBUTING.md) for instructions.
