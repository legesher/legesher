# Pack messages: localized error-message templates

> **Maintainer notes, not newcomer documentation.** Written for someone already
> working in this code. It may cite work-tracker ids (`CORE-####`) an outside
> reader cannot resolve.

A pack version file may carry a `messages` section: the localized wording of
the traceback structure ("Traceback (most recent call last):") and of the
interpreter's error messages ("name 'x' is not defined"). The section was
added in CORE-2630. No shipped pack carries it yet.

```yaml
messages:
  cpython:
    traceback.frame:
      text: "Archivo \"{file}\", línea {line}, en {name}"
      src: fcb6c6422b34
    NameError.not_defined:
      text: "el nombre '{name}' no está definido"
      src: 998720c0a4af
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
  - `src`: twelve lowercase hex digits. Quote a value made only of digits,
    or YAML reads it as a number.
- An entry may carry other fields. A pack load does not examine them.

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

A load does **not** decide whether an entry is usable: whether its key is a
known message, whether `src` matches the English template, whether its
placeholders agree. Those are decided where the catalog is read, and an entry
that fails there is skipped. The message then prints as the interpreter
printed it, and the pack still loads. One unusable message must not take a
pack's keywords and exception names down with it.

## Version tiering

The section rides the pack's `extends` chain, merged per implementation and
per key, the child file winning. An entry is replaced whole: `text` and `src`
describe one English wording together, so a reworded entry never inherits a
field from the entry it replaces.

A translation of a message that Python reworded in a later version is written
into that version's file. A section can therefore appear only in an overlay
file (`3.12.yml`) and not in the base (`3.10.yml`).

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
