# Pack messages: localized error-message templates

> **Audience:** Contributors, who change the code, tests and docs, or offer and review the words in a language pack.

A pack version file may carry a `messages` section: the localized wording of
the traceback structure ("Traceback (most recent call last):") and of the
interpreter's error messages ("name 'x' is not defined"). The section was
added in CORE-2630. The Spanish and Arabic packs carry it; the others do not yet.

```yaml
messages:
  cpython:
    traceback.frame:
      text: "Archivo \"{file}\", línea {line}, en {name}"
      src: "fcb6c6422b34"
    NameError.not_defined:
      text: "el nombre '{name}' no está definido"
      src: "998720c0a4af"
```

## What is in the pack and what is not

The split is the one keywords use: the term belongs to the target, the
rendering belongs to the pack.

- **In `legesher-i18n`:** the message key, the English template, the matcher
  that recognizes the message, its placeholders, and the Python versions the
  wording applies to.
- **In the pack:** for each key, the localized template (`text`) and a
  fingerprint of the English template it translates (`src`).

## Shape

- The section is nested by **implementation** (`cpython`), lowercase letters
  and digits. The catalog is already per implementation, so a pack can carry
  another implementation's wording later without a format change.
- Under an implementation, entries are keyed by the **catalog key**
  (`traceback.frame`, `NameError.not_defined`). Keys are never localized.
- An entry is a mapping with two required fields:
  - `text`: the localized template. Placeholders are written `{name}`.
  - `src`: twelve lowercase hex digits. Always write it quoted. Unquoted,
    some values read as numbers (`123456789012`, `0b0101010101`, or `1234567890e1`
    to a YAML 1.2 reader such as the editor extension's).
- An entry may also carry `status`, the review rung of the translation:
  `machine`, `experimental`, `reviewed` or `official`. An entry with no
  `status` is `machine`.
- An entry may carry other fields, under any field name. A pack load does
  not examine any field beyond `text` and `src`.

`src` is the first twelve hex digits of the SHA-256 of the English template,
NFC-normalized and encoded as UTF-8 (`legesher_i18n.pack_messages.message_fingerprint`).
The matcher is not part of it, so a fix to how a message is recognized keeps
every translation of its wording valid.

## What a pack load checks

Loading a pack checks the **shape** of the section, with
`legesher_i18n.pack_messages.messages_structure_errors`:

- the nesting above, and the name patterns for implementations and keys;
- `text` is a string and carries no bidi control characters (isolating an
  interpolated value is a render-time concern, so stored templates stay
  clean);
- `src` is a string of twelve lowercase hex digits.

A violation fails the load and names the path of the offending value, as any
other malformed section does.

A load does **not** decide whether an entry is usable. That is decided where
the catalog is read, and an entry that fails there is skipped. The message
then prints as the interpreter printed it, and the pack still loads. One
unusable message must not take a pack's keywords and exception names down
with it.

## When an entry is used

`legesher_i18n.messages.load_catalog` pairs each entry with the English
template that applies to the running interpreter for the entry's key, and
uses the entry only when `legesher_i18n.pack_messages.entry_problem` finds
nothing wrong:

1. The entry carries only `text`, `src` and `status`, and `status`, when
   present, is one of the four rungs. An entry with any other field is not
   used: a field a later release adds may change what the text means, and a
   reader that does not know it must not guess. The text carries no control
   character (NUL, or the ESC that starts a terminal escape sequence), no line
   or paragraph separator and no lone surrogate: it is written to a
   terminal. Joiners such as ZWJ are
   allowed.
2. `src` is the fingerprint of that English template. This is what keeps a
   translation off a wording it was not written for. Python 3.11 reworded
   "local variable 'x' referenced before assignment" under the same key and
   with the same placeholder, so nothing else tells a translation of the old
   sentence from a translation of the new one. The same holds when an
   English template is corrected.
3. The placeholders in `text` are exactly the ones the English template
   declares. A brace that is not a `{name}` placeholder is plain text.
4. `text` is empty only when the English template is empty.

An entry whose key has no English template at this interpreter version is
ignored. A pack may be newer than the catalog it is read with.

A skipped entry is logged at debug level with its key and the reason.
`legesher_i18n.messages.pack_message_problems` returns the same reasons for
one pack and version, and reports an unknown key too. A test runs it over
every shipped pack at every version, and at one version past the newest
tier, so an entry the join would skip fails the suite instead of leaving a
message in English without notice.

Two unused entries are expected and not reported, because a later pack file
can add or override an entry but never remove one: the translation of an
earlier wording of a message, inherited by the files after the one where
Python reworded it, and the translation of a message Python stopped printing.
So a pack may translate a message's earlier wording without its rewording.
Such an entry is exempt only when the pack carried it unchanged at a version
where that wording applied. An entry that names an earlier wording but first
appears, or is rewritten, after that wording stopped applying is a stale
fingerprint and is reported.

## Where the catalog comes from

In order:

1. An explicit `db_path` is read alone.
2. The default translations database, when it holds the catalog, is the
   whole catalog: English and translations. Normally only a maintainer
   checkout has one.
3. Otherwise the English side comes from the seed that ships in the package,
   and the translations from the pack for the locale, at the tier the pack
   loader picks for the running Python version, by the rule that picks the
   tier for words. On a Python newer than every tier the pack has, that
   is its newest tier: every entry is joined by fingerprint, so a message
   the newer Python reworded stays in English and every other message stays
   translated. The pack is the only source of translations: a message it
   does not translate prints in English, and so does every message when
   there is no pack for the locale, the loader serves no tier for that
   Python version (below the pack's oldest tier, a tier missing from the
   middle, the next major version), the pack does not load, or it carries
   no messages for the implementation. The seed carries no translations.

The pack's minimum interpreter version is not enforced for this read. That
guard protects translated identifiers that would not parse on an older
interpreter, and rendering a message runs none.

## Placeholder kinds

On the English side, a placeholder may declare a `kind`: `line` for a line
number, `count` for a count. A placeholder with no kind is copied verbatim,
which includes numbers that are neither, such as an errno. The kind reaches
a renderer as `MessageRule.slot_kinds` and `MessageRule.kind_of(name)`, so
which values a renderer may reformat is data on the English side and a pack
carries nothing for it. A database seeded before kinds existed takes them
from the seed's row with the same key and wording.

## Version tiering

The section rides the pack's `extends` chain, merged per implementation and
per key, the child file winning. An entry is replaced whole: `text` and `src`
describe one English wording together, so a reworded entry never inherits a
field from the entry it replaces.

A translation of a message that Python reworded in a later version is written
into that version's file. A section can therefore appear only in an overlay
file (`3.12.yml`) and not in the base (`3.10.yml`).

## Where the entries come from

The section is exported from the translations database, like every other
section, and never edited by hand. `scripts/translate/yaml_exporter.py` reads
`message_templates` joined to `message_translations` for the locale and:

- writes each translation into the file of the Python version its English
  wording entered at (`version_added`; none means `3.10.yml`), so a reworded
  message's translation overrides the earlier one through `extends`;
- writes `src` as the fingerprint of that wording, always double-quoted;
- writes `status` only when it is not `machine`;
- writes the entries in catalog order, so a regeneration is reproducible;
- exports a partial set as it is: an untranslated message prints in English;
- refuses a stored translation that fails a join rule or carries a bidi
  control (the database is damaged), and a wording that entered at a Python
  version with no pack file.

`scripts/verify_pack_regen.py` compares the section entry by entry, so a
changed message is reported as `messages.cpython.<key>`.

`scripts/translate/import_yaml_to_db.py` reads the section back into the
database: each entry goes to the English template with its key and
fingerprint. An entry for a wording the database does not have, or one that
fails a join rule, is skipped. A translation the database already stores is
never overwritten. Inserted rows record `source = 'pack-import'`.

A message that a later Python version stops printing, with no rewording to
replace it, cannot be retracted from the files after the one that carries it:
`extends` only adds and overrides. The entry is ignored at run time, and
`pack_message_problems` treats it as inherited, like an earlier wording's
translation.

The published dataset does not carry pack messages: `scripts/export_packs.py`
reads only the term and vocabulary sections from packs, and a test holds that
until message endorsements have content-addressed keys.

## Compatibility: a pack with messages needs a loader that knows them

- A `legesher-i18n` release **from before this section** refuses a base file
  that carries `messages`: the pack schema forbids unknown keys. In an
  overlay file the same release ignores the section without an error.
- A pack **without** the section loads identically on every release.

Language packs ship inside the `legesher-i18n` distribution, so the loader
that reads the section and the packs that carry it are released together. A
language pack installed as its own distribution takes precedence over the
bundled copy; one that carries `messages` must require a `legesher-i18n`
release that knows the section.
