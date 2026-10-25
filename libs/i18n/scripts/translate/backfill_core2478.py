#!/usr/bin/env python3
"""CORE-2478: select the Swahili (sw) Python vocabulary, DB-first.

Swahili had a ``languages`` row and 104 candidate rows but no pack: community
candidates from the 2025-11-11 bulk import (35 keywords, 54 builtin functions,
15 builtin types, one per term), with no selection and no exception,
special-constant or implicit-parameter rows at all. This script decides all
184 terms of the shipped inventory.

Design (the backfill_core1644.py pattern):
  * DB-first: every value goes through ``add_translation`` (a provenanced
    candidate, so no selection is orphaned from the pool) and then
    ``set_selected`` (publish gate, collision guard, and the sw forbidden
    letters q and x). The exporter regenerates the pack from the selections.
  * A community candidate is kept wherever it is the right Swahili word; it
    is replaced only where it is wrong in sense or form, and each replacement
    says why in its rationale. The replaced candidate stays in the pool.
    Fifteen candidates are hyphenated, which no identifier can be; where
    the word itself is right the replacement keeps it and only drops the
    hyphens (seven values), as ``style-guides/sw.yml`` specifies.
  * Generated values are written as a linguist would choose them (part of
    speech, noun class and agreement, register, native CS usage), following
    ``style-guides/sw.yml``. Prompts were rendered through the pipeline's own
    PromptBuilder; the selections are ``source='claude'`` at the experimental
    rung, pending native review.
  * Five calls are flags, both sides prepared. --verbs imperative,
    --joiner none and --exceptions lower are decided; --compounds and
    --loans are open. Every run writes the candidate rows for every side, so
    flipping a decision is a re-run with a different flag, then the usual
    regen ritual. A flip of --verbs, --compounds or --joiner also means
    editing the matching rule in sw.yml by hand: the guide states the
    recommended side, and nothing here writes it.

      --verbs imperative|infinitive    bare stem (fungua) or ku- infinitive
                                       (kufungua) for action words
      --compounds associative|juxtaposed
                                       hitilafu_ya_thamani, with the particle
                                       that agrees with the head's noun
                                       class, or hitilafu_thamani without it
      --loans native|adapted           a native word (sambamba, mantiki,
                                       maandishi, umbiza) or the respelled
                                       English loan (asinkroni, buliani,
                                       stringi, fomati) where both exist
      --joiner none|underscore         words run together like Python's own
                                       reserved words (hitilafuyathamani), or
                                       joined with underscores
      --exceptions lower|capwords      exception names in lowercase like every
                                       other value, or CapWords
                                       (HitilafuYaThamani)

  * The seed data writes every multi-word value with its word boundaries
    (hitilafu_ya_thamani). The shipped surface is derived from it, and the
    database keeps the separation twice: the underscore form is a candidate
    row, and every rationale records "Separated form: ...".

  * Every combination of the flags is checked before anything is written, so
    no future flip can trip the publish gate or the collision guard.
  * Idempotent: a re-run with the same flags changes nothing. The whole target
    state is checked against both of set_selected's refusals before anything
    is written, so neither can stop a run halfway. The writes commit one at a
    time, so a run interrupted for any other reason is finished by running it
    again.

Usage:
    uv run python libs/i18n/scripts/translate/backfill_core2478.py [--dry-run]
        [--db PATH] [--verbs imperative] [--compounds associative]
        [--loans native] [--joiner none] [--exceptions lower]
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
I18N_ROOT = HERE.parents[2]  # libs/i18n
sys.path.insert(0, str(I18N_ROOT))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.selection import is_valid_pack_value  # noqa: E402

DB_PATH = I18N_ROOT / "legesher_i18n" / "db" / "translations.db"

LANG = "sw"
SELECTED_BY = "CORE-2478"
GEN_SOURCE = "claude"
GEN_MODEL = "claude-opus-5-5"
GEN_CREATED_BY = "CORE-2478"

KEEP = "Community candidate retained"
JOIN = (
    "Community word kept, its hyphens removed (hyphens are not identifier characters)"
)

# (category, term, value, word_type, confidence, rationale)
# Values here are the recommended branch: bare verb stems, the associative
# particle in compounds, native words over loans. The alternates below
# override them per flag.
SELECTIONS: list[tuple[str, str, str, str, str, str]] = [
    # --- keywords -----------------------------------------------------------
    (
        "keyword",
        "False",
        "uongo",
        "noun",
        "medium",
        "Replaces the community uwongo with the standard spelling uongo (falsehood), the pair of ukweli in truth values.",
    ),
    (
        "keyword",
        "None",
        "hakuna",
        "existential",
        "medium",
        f"{KEEP}: hakuna (there is none) is the everyday way to say a thing is absent; rudisha hakuna, x ni hakuna both read naturally.",
    ),
    (
        "keyword",
        "True",
        "ukweli",
        "noun",
        "high",
        f"{KEEP}: ukweli (truth) / uongo (falsehood) is the noun pair for truth values.",
    ),
    ("keyword", "and", "na", "conjunction", "high", f"{KEEP}: the plain conjunction."),
    (
        "keyword",
        "as",
        "kama",
        "conjunction",
        "high",
        f"{KEEP}: agiza x kama y, isipokuwa E kama e. The community pool also offered kama for if; as keeps it because as has no other Swahili word, and if takes ikiwa.",
    ),
    (
        "keyword",
        "assert",
        "hakikisha",
        "verb",
        "medium",
        "Replaces sisitiza (emphasise, insist), which states rather than checks. hakikisha (make sure, verify) names what assert does; pairs with hitilafu_ya_uhakikisho.",
    ),
    (
        "keyword",
        "async",
        "sambamba",
        "adverb",
        "low",
        "Replaces the untranslated async. sambamba (alongside, concurrently) is the native adverb for work that runs beside other work; it carries no noun-class agreement, so it can stand before fasili. Decision flag --loans (asinkroni).",
    ),
    (
        "keyword",
        "await",
        "ngoja",
        "verb",
        "high",
        f"{KEEP}: bare stem of kungoja (wait).",
    ),
    (
        "keyword",
        "break",
        "vunja",
        "verb",
        "high",
        f"{KEEP}: bare stem of kuvunja (break), break out of the loop.",
    ),
    (
        "keyword",
        "case",
        "endapo",
        "conjunction",
        "medium",
        "New. endapo (in the event that) introduces one alternative of a match (endapo 1:), with no noun-class agreement to guess.",
    ),
    (
        "keyword",
        "class",
        "darasa",
        "noun",
        "medium",
        f"{KEEP}: darasa (class, as of pupils) is the calque in use for a class of objects; pairs with darasa_tanzu (subclass) and darasa_kuu (superclass).",
    ),
    (
        "keyword",
        "continue",
        "endelea",
        "verb",
        "high",
        f"{KEEP}: bare stem of kuendelea (go on).",
    ),
    (
        "keyword",
        "def",
        "fasili",
        "verb",
        "medium",
        "Replaces fafanua (explain in detail, elaborate). fasili is the dictionary verb for giving a definition, and def defines a body.",
    ),
    (
        "keyword",
        "del",
        "futa",
        "verb",
        "high",
        "Replaces duta, which is not a Swahili word. futa (erase, delete) is the delete command in Swahili software.",
    ),
    (
        "keyword",
        "elif",
        "vinginevyo_ikiwa",
        "conjunction",
        "medium",
        "Replaces vinginevyo, which means otherwise and belongs to else. vinginevyo_ikiwa (otherwise if) mirrors the else + if structure.",
    ),
    (
        "keyword",
        "else",
        "vinginevyo",
        "adverb",
        "high",
        "Replaces ikiwa-si-ivyo (hyphenated, and ivyo for hivyo). vinginevyo (otherwise) is the standard single word, offered in the pool under elif.",
    ),
    (
        "keyword",
        "except",
        "isipokuwa",
        "conjunction",
        "high",
        f"{KEEP}: isipokuwa (except, unless it is); jaribu: ... isipokuwa hitilafu_ya_thamani: reads as a sentence.",
    ),
    (
        "keyword",
        "except*",
        "isipokuwa*",
        "conjunction",
        "high",
        "New. except* mirrors except with the trailing star.",
    ),
    (
        "keyword",
        "finally",
        "mwishowe",
        "adverb",
        "high",
        f"{KEEP}: mwishowe (in the end), the block that runs at the end.",
    ),
    (
        "keyword",
        "for",
        "kwa",
        "preposition",
        "medium",
        f"{KEEP}: kwa i katika orodha: reads as for i in list.",
    ),
    ("keyword", "from", "kutoka", "preposition", "high", f"{KEEP}: from."),
    (
        "keyword",
        "global",
        "kote",
        "adverb",
        "medium",
        "Replaces kimataifa, which means international. kote (everywhere) names module scope and, as an adverb, needs no agreement with the name it declares; pairs with vigeu_vya_kote.",
    ),
    (
        "keyword",
        "if",
        "ikiwa",
        "conjunction",
        "high",
        "Replaces kama, which as also needs. ikiwa (if, in case it is) is equally standard for a condition, and as has no other word.",
    ),
    (
        "keyword",
        "import",
        "agiza",
        "verb",
        "high",
        f"{KEEP}: kuagiza is to import (goods); bare stem.",
    ),
    (
        "keyword",
        "in",
        "katika",
        "preposition",
        "high",
        "Replaces ndani (inside), an adverb that needs ya before a noun. katika (in) is the invariable preposition: kwa i katika orodha, x katika y.",
    ),
    (
        "keyword",
        "is",
        "ni",
        "copula",
        "high",
        f"{KEEP}: the copula; x ni hakuna.",
    ),
    (
        "keyword",
        "lambda",
        "lambda",
        "noun",
        "high",
        f"{KEEP}: the Greek letter's name, which Swahili uses unchanged; an accepted English-identical value named in style-guides/sw.yml, as for cs, cy, ga, hr and lv.",
    ),
    (
        "keyword",
        "match",
        "linganisha",
        "verb",
        "medium",
        "New. linganisha (compare, match against) introduces the subject the cases are compared with.",
    ),
    (
        "keyword",
        "nonlocal",
        "nje",
        "adverb",
        "low",
        "Replaces isiyo-ya-kawaida (hyphenated, and it means unusual). nje (outside) names the enclosing scope outside the current function, an adverb with no agreement, beside kote for global.",
    ),
    (
        "keyword",
        "not",
        "si",
        "particle",
        "high",
        f"{KEEP}: the negative copula and particle.",
    ),
    ("keyword", "or", "au", "conjunction", "high", f"{KEEP}: the plain conjunction."),
    (
        "keyword",
        "pass",
        "pita",
        "verb",
        "medium",
        f"{KEEP}: pita (pass on, go by): move on without doing anything.",
    ),
    (
        "keyword",
        "raise",
        "ibua",
        "verb",
        "medium",
        "Replaces inua, which is physical lifting. ibua is to raise an issue or bring a matter up (kuibua suala), the sense of raising an error.",
    ),
    (
        "keyword",
        "return",
        "rudisha",
        "verb",
        "high",
        f"{KEEP}: bare stem of kurudisha (give back).",
    ),
    (
        "keyword",
        "try",
        "jaribu",
        "verb",
        "high",
        f"{KEEP}: bare stem of kujaribu (try).",
    ),
    (
        "keyword",
        "type",
        "aina",
        "noun",
        "high",
        "New. The 3.12 type statement shares the builtin's word, aina (kind, type); same-name slots may share.",
    ),
    (
        "keyword",
        "while",
        "wakati",
        "conjunction",
        "medium",
        f"{KEEP}: wakati (while, at the time that); wakati x < 10: reads as a condition.",
    ),
    (
        "keyword",
        "with",
        "kwa_kutumia",
        "prepositional phrase",
        "medium",
        "Replaces na, which and already holds. kwa_kutumia (by using) names the context manager: kwa_kutumia fungua(f) kama faili.",
    ),
    (
        "keyword",
        "yield",
        "toa",
        "verb",
        "medium",
        "Replaces mavuno, a noun for a crop harvest. toa (give out, produce) is the act of handing a value out.",
    ),
    # --- special constants --------------------------------------------------
    (
        "special_constant",
        "ellipsis",
        "nukta_tatu",
        "noun phrase",
        "high",
        "New. nukta tatu (three dots), the Swahili name of the mark.",
    ),
    (
        "special_constant",
        "notimplemented",
        "haijatekelezwa",
        "verb",
        "medium",
        "New. haijatekelezwa (it has not been implemented), from tekeleza as in exec.",
    ),
    # --- implicit parameters -------------------------------------------------
    (
        "implicit_param",
        "cls",
        "darasa_lake",
        "noun phrase",
        "medium",
        "New. darasa lake (its class), the class the method belongs to; lake agrees with darasa, class 5.",
    ),
    (
        "implicit_param",
        "self",
        "nafsi",
        "noun",
        "medium",
        "New. nafsi (self) is the noun for the self; it refers to the instance without any personal pronoun (mimi, wewe) and needs no agreement.",
    ),
    # --- builtin functions --------------------------------------------------
    (
        "builtin_func",
        "__import__",
        "__agiza__",
        "verb",
        "high",
        "Replaces _agiza_, which has single underscores. The dunder form of agiza.",
    ),
    (
        "builtin_func",
        "abs",
        "thamani_kamili",
        "noun phrase",
        "low",
        "Replaces the untranslated abs. thamani kamili, the absolute value of school mathematics.",
    ),
    (
        "builtin_func",
        "aiter",
        "kirudiaji_sambamba",
        "noun phrase",
        "low",
        "New. The concurrent form of kirudiaji, as sambamba is for async. Decision flag --loans.",
    ),
    (
        "builtin_func",
        "all",
        "yote",
        "quantifier",
        "high",
        f"{KEEP}: yote (all).",
    ),
    (
        "builtin_func",
        "anext",
        "ifuatayo_sambamba",
        "noun phrase",
        "low",
        "New. The concurrent form of ifuatayo. Decision flag --loans.",
    ),
    (
        "builtin_func",
        "any",
        "yoyote",
        "quantifier",
        "medium",
        f"{KEEP}: yoyote (any at all).",
    ),
    (
        "builtin_func",
        "ascii",
        "ascii",
        "noun",
        "medium",
        f"{KEEP}: an acronym with no Swahili expansion; an accepted English-identical value named in style-guides/sw.yml, as for cs.",
    ),
    (
        "builtin_func",
        "bin",
        "msingi_wa_mbili",
        "noun phrase",
        "medium",
        "Replaces the untranslated bin. msingi wa mbili (base two), the school term, and the pattern of oct and hex.",
    ),
    (
        "builtin_func",
        "breakpoint",
        "mahali_pa_kusimama",
        "noun phrase",
        "medium",
        "Replaces mahali-pa-kuvunja (hyphenated; the place of breaking). mahali pa kusimama (the place to stop) is what a debugger breakpoint is; pa agrees with mahali, class 16.",
    ),
    (
        "builtin_func",
        "callable",
        "inaweza_kuitwa",
        "verb phrase",
        "medium",
        "Replaces inayoitwa, which reads as which is named. inaweza kuitwa (it can be called).",
    ),
    (
        "builtin_func",
        "chr",
        "herufi",
        "noun",
        "high",
        "Replaces tabia, which is a person's character. herufi (letter, character of text).",
    ),
    (
        "builtin_func",
        "classmethod",
        "njia_ya_darasa",
        "noun phrase",
        "medium",
        "Replaces njia-ya-darase (hyphenated, darase for darasa). njia ya darasa (method of the class), the community word with the joiner and spelling fixed.",
    ),
    (
        "builtin_func",
        "compile",
        "kusanya",
        "verb",
        "medium",
        f"{KEEP}: kusanya (collect, compile, as a book is compiled); the stem itself begins with ku.",
    ),
    (
        "builtin_func",
        "delattr",
        "futa_sifa",
        "verb phrase",
        "high",
        f"{JOIN}: futa sifa (delete attribute), as del is futa.",
    ),
    (
        "builtin_func",
        "dir",
        "orodha_ya_sifa",
        "noun phrase",
        "medium",
        "Replaces saraka, a filesystem directory, which is a different concept. orodha ya sifa (list of attributes) is what dir returns.",
    ),
    (
        "builtin_func",
        "divmod",
        "gawanya_na_baki",
        "verb phrase",
        "medium",
        "Replaces the untranslated divmod. gawanya na baki (divide with remainder): it returns the quotient and the remainder.",
    ),
    (
        "builtin_func",
        "enumerate",
        "hesabu",
        "verb",
        "medium",
        "Replaces kuhesabu, the ku- infinitive, with its bare stem hesabu (count, number off), the pack's verb form. The community word is the --verbs infinitive branch.",
    ),
    (
        "builtin_func",
        "eval",
        "tathmini",
        "verb",
        "high",
        f"{KEEP}: tathmini (evaluate).",
    ),
    (
        "builtin_func",
        "exec",
        "tekeleza",
        "verb",
        "high",
        f"{KEEP}: tekeleza (execute, carry out).",
    ),
    (
        "builtin_func",
        "filter",
        "chuja",
        "verb",
        "high",
        f"{KEEP}: chuja (filter, sieve).",
    ),
    (
        "builtin_func",
        "format",
        "umbiza",
        "verb",
        "low",
        "Replaces muundo, a noun (structure). umbiza (format) is the verb Swahili software uses for formatting. Decision flag --loans (fomati).",
    ),
    (
        "builtin_func",
        "getattr",
        "pata_sifa",
        "verb phrase",
        "high",
        f"{JOIN}: pata sifa (get attribute).",
    ),
    (
        "builtin_func",
        "globals",
        "vigeu_vya_kote",
        "noun phrase",
        "medium",
        "Replaces ulimwengu (the world). vigeu vya kote (the variables of everywhere), beside kote for global; vya agrees with vigeu, class 8.",
    ),
    (
        "builtin_func",
        "hasattr",
        "ina_sifa",
        "verb phrase",
        "high",
        f"{JOIN}: ina sifa (it has the attribute).",
    ),
    (
        "builtin_func",
        "hash",
        "hashi",
        "noun",
        "low",
        "Replaces the untranslated hash with the loan respelled to Swahili orthography; there is no native term.",
    ),
    (
        "builtin_func",
        "help",
        "saidia",
        "verb",
        "high",
        f"{KEEP}: bare stem of kusaidia (help).",
    ),
    (
        "builtin_func",
        "hex",
        "msingi_wa_kumi_na_sita",
        "noun phrase",
        "medium",
        "Replaces the untranslated hex. msingi wa kumi na sita (base sixteen), the pattern of bin and oct.",
    ),
    (
        "builtin_func",
        "id",
        "kitambulisho",
        "noun",
        "high",
        f"{KEEP}: kitambulisho (identifier, identity card).",
    ),
    (
        "builtin_func",
        "input",
        "ingiza",
        "verb",
        "medium",
        "Replaces pembejeo, which means farm inputs (seed, fertiliser). ingiza (enter) is what an input prompt asks: jina = ingiza('Jina lako: ').",
    ),
    (
        "builtin_func",
        "isinstance",
        "ni_mfano_wa",
        "verb phrase",
        "medium",
        "Replaces mfano (example) with the predicate ni mfano wa (is an instance of), as issubclass is.",
    ),
    (
        "builtin_func",
        "issubclass",
        "ni_darasa_tanzu_la",
        "verb phrase",
        "medium",
        "Replaces darasa-ndogo (hyphenated; a small class). ni darasa tanzu la (is a subclass of), tanzu as in kampuni tanzu (subsidiary company); la agrees with darasa, class 5.",
    ),
    (
        "builtin_func",
        "iter",
        "kirudiaji",
        "noun",
        "low",
        "Replaces mara-kwa-mara (hyphenated; an adverb, repeatedly). kirudiaji (iterator) is a ki- instrument noun from rudia (repeat), the pattern of kichapishi (printer) and kivinjari (browser).",
    ),
    (
        "builtin_func",
        "len",
        "urefu",
        "noun",
        "high",
        f"{KEEP}: urefu (length).",
    ),
    (
        "builtin_func",
        "locals",
        "vigeu_vya_hapa",
        "noun phrase",
        "medium",
        "Replaces wenyeji, which means local people. vigeu vya hapa (the variables of here), the pair of vigeu_vya_kote.",
    ),
    (
        "builtin_func",
        "map",
        "tumia_kwa_kila",
        "verb phrase",
        "medium",
        "Replaces ramani, a geographic map. tumia kwa kila (apply to each) is what map does.",
    ),
    (
        "builtin_func",
        "max",
        "kiwango_cha_juu",
        "noun phrase",
        "medium",
        "Replaces upeo (limit, horizon) with kiwango cha juu (the highest level), the pair of the community kiwango_cha_chini for min.",
    ),
    (
        "builtin_func",
        "min",
        "kiwango_cha_chini",
        "noun phrase",
        "high",
        f"{JOIN}: kiwango cha chini (the lowest level); cha agrees with kiwango, class 7.",
    ),
    (
        "builtin_func",
        "next",
        "ifuatayo",
        "relative",
        "medium",
        "Replaces ijayo, which is next in time (wiki ijayo, next week). ifuatayo (the following one) is next in a sequence.",
    ),
    (
        "builtin_func",
        "oct",
        "msingi_wa_nane",
        "noun phrase",
        "medium",
        "Replaces the untranslated oct. msingi wa nane (base eight).",
    ),
    (
        "builtin_func",
        "open",
        "fungua",
        "verb",
        "high",
        f"{KEEP}: fungua (open), the command in Swahili software.",
    ),
    (
        "builtin_func",
        "ord",
        "msimbo_wa_herufi",
        "noun phrase",
        "medium",
        "Replaces utaratibu, which means procedure or order of events. msimbo wa herufi (the code of a character) is what ord returns, the inverse of herufi; wa agrees with msimbo, class 3.",
    ),
    (
        "builtin_func",
        "pow",
        "kipeo",
        "noun",
        "medium",
        "Replaces nguvu, which is physical strength. kipeo is the mathematical power (exponent).",
    ),
    (
        "builtin_func",
        "print",
        "chapisha",
        "verb",
        "high",
        f"{KEEP}: chapisha (print), the command in Swahili software.",
    ),
    (
        "builtin_func",
        "property",
        "sifa",
        "noun",
        "medium",
        "Replaces mali, which means possessions or wealth. sifa (property, characteristic), the root of the attribute builtins.",
    ),
    (
        "builtin_func",
        "range",
        "masafa",
        "noun",
        "medium",
        f"{KEEP}: masafa (range, span).",
    ),
    (
        "builtin_func",
        "repr",
        "uwakilishi",
        "noun",
        "medium",
        "Replaces the untranslated repr. uwakilishi (representation).",
    ),
    (
        "builtin_func",
        "reversed",
        "kinyume",
        "adverb",
        "medium",
        "Replaces geuza-nyuma (hyphenated). kinyume (in reverse, the opposite way): kwa x katika kinyume(orodha).",
    ),
    (
        "builtin_func",
        "round",
        "kadiria",
        "verb",
        "medium",
        "Replaces raundi, a loan for a round of a contest. kadiria (round off, approximate) is the school term for rounding.",
    ),
    (
        "builtin_func",
        "setattr",
        "weka_sifa",
        "verb phrase",
        "high",
        f"{JOIN}: weka sifa (set attribute).",
    ),
    (
        "builtin_func",
        "slice",
        "kipande",
        "noun",
        "high",
        f"{KEEP}: kipande (piece, slice).",
    ),
    (
        "builtin_func",
        "sorted",
        "iliyopangwa",
        "relative",
        "medium",
        "Replaces pangwa (be arranged) with the relative iliyopangwa (which has been arranged), agreeing with orodha, class 9, the list sorted returns.",
    ),
    (
        "builtin_func",
        "staticmethod",
        "njia_tuli",
        "noun phrase",
        "medium",
        f"{JOIN}: njia tuli (static method).",
    ),
    (
        "builtin_func",
        "sum",
        "jumla",
        "noun",
        "high",
        f"{KEEP}: jumla (total), a noun like urefu.",
    ),
    (
        "builtin_func",
        "super",
        "darasa_kuu",
        "noun phrase",
        "medium",
        "Replaces the untranslated super. darasa kuu (the principal class), the pair of darasa tanzu, as kampuni kuu and kampuni tanzu are parent and subsidiary.",
    ),
    (
        "builtin_func",
        "vars",
        "vigeu",
        "noun",
        "medium",
        "Replaces the untranslated vars. vigeu (variables, plural of kigeu, the school term).",
    ),
    (
        "builtin_func",
        "zip",
        "oanisha",
        "verb",
        "medium",
        "Replaces bana (squeeze, compress), the wrong sense of zip. oanisha (pair up, match together) is what zip does to its arguments.",
    ),
    # --- builtin types ------------------------------------------------------
    (
        "builtin_type",
        "bool",
        "mantiki",
        "noun",
        "low",
        "Replaces the untranslated bool. mantiki (logic): mantiki(x) gives the logical value. Decision flag --loans (buliani).",
    ),
    (
        "builtin_type",
        "bytearray",
        "safu_ya_baiti",
        "noun phrase",
        "medium",
        "Replaces baiti-safu (hyphenated, and in English order). safu ya baiti (array of bytes), head noun first.",
    ),
    (
        "builtin_type",
        "bytes",
        "baiti",
        "noun",
        "high",
        f"{KEEP}: baiti, the established loan for byte.",
    ),
    (
        "builtin_type",
        "complex",
        "namba_changamano",
        "noun phrase",
        "medium",
        "Replaces tata, which means complicated. namba changamano (complex number), in the namba family with namba_kamili and namba_desimali.",
    ),
    (
        "builtin_type",
        "dict",
        "kamusi",
        "noun",
        "high",
        f"{KEEP}: kamusi (dictionary).",
    ),
    (
        "builtin_type",
        "float",
        "namba_desimali",
        "noun phrase",
        "medium",
        "Replaces elea, the verb to float on water. namba desimali (decimal number), with desimali the established loan.",
    ),
    (
        "builtin_type",
        "frozenset",
        "seti_iliyoganda",
        "noun phrase",
        "medium",
        "Replaces waliohifadhiwa, which agrees with people (class 2: those who were preserved). seti iliyoganda (a set that has frozen) agrees with seti, class 9.",
    ),
    (
        "builtin_type",
        "int",
        "namba_kamili",
        "noun phrase",
        "medium",
        "Replaces nambari (number) with namba kamili (integer, whole number), the school term.",
    ),
    (
        "builtin_type",
        "list",
        "orodha",
        "noun",
        "high",
        f"{KEEP}: orodha (list).",
    ),
    (
        "builtin_type",
        "memoryview",
        "mtazamo_wa_kumbukumbu",
        "noun phrase",
        "medium",
        f"{JOIN}: mtazamo wa kumbukumbu (view of memory); wa agrees with mtazamo, class 3.",
    ),
    (
        "builtin_type",
        "object",
        "kitu",
        "noun",
        "high",
        f"{KEEP}: kitu (thing, object).",
    ),
    (
        "builtin_type",
        "set",
        "seti",
        "noun",
        "high",
        f"{KEEP}: seti, the loan school mathematics uses for a set.",
    ),
    (
        "builtin_type",
        "str",
        "maandishi",
        "noun",
        "medium",
        "Replaces the untranslated str. maandishi (text, writing): maandishi(5) gives the text '5'. Decision flag --loans (stringi).",
    ),
    (
        "builtin_type",
        "tuple",
        "orodha_tuli",
        "noun phrase",
        "low",
        "Replaces the untranslated tuple. orodha tuli (a fixed list), tuli as in njia_tuli: an ordered sequence that does not change.",
    ),
    (
        "builtin_type",
        "type",
        "aina",
        "noun",
        "high",
        f"{KEEP}: aina (kind, type).",
    ),
    # --- exceptions ---------------------------------------------------------
    # Three roots (style-guides/sw.yml): Hitilafu (error, class 9, takes ya),
    # hali_ya_kipekee (exception, an exceptional condition), onyo (warning,
    # class 5, takes la). Head noun first, then the associative particle that
    # agrees with it.
    (
        "exception",
        "arithmeticerror",
        "hitilafu_ya_hesabu",
        "noun phrase",
        "medium",
        "New. Error of arithmetic (hesabu).",
    ),
    (
        "exception",
        "assertionerror",
        "hitilafu_ya_uhakikisho",
        "noun phrase",
        "medium",
        "New. Error of verification (uhakikisho), the noun of hakikisha (assert).",
    ),
    (
        "exception",
        "attributeerror",
        "hitilafu_ya_sifa",
        "noun phrase",
        "high",
        "New. Error of an attribute (sifa), as in pata_sifa.",
    ),
    (
        "exception",
        "baseexception",
        "hali_ya_kipekee_ya_msingi",
        "noun phrase",
        "low",
        "New. The base (ya msingi) exceptional condition.",
    ),
    (
        "exception",
        "baseexceptiongroup",
        "kundi_la_msingi_la_hali_za_kipekee",
        "noun phrase",
        "low",
        "New. The base group (kundi la msingi) of exceptional conditions; za agrees with hali, plural class 10.",
    ),
    (
        "exception",
        "blockingioerror",
        "hitilafu_ya_kuzuia_uingizaji_na_utoaji",
        "noun phrase",
        "low",
        "New. Error of blocking (kuzuia) input and output; uingizaji and utoaji are the nouns of ingiza (input) and toa.",
    ),
    (
        "exception",
        "brokenpipeerror",
        "hitilafu_ya_bomba_lililovunjika",
        "noun phrase",
        "medium",
        "New. Error of a pipe (bomba, class 5) that has broken; the relative lililo- agrees with bomba.",
    ),
    (
        "exception",
        "buffererror",
        "hitilafu_ya_hifadhi_ya_muda",
        "noun phrase",
        "low",
        "New. Error of temporary storage (hifadhi ya muda), what a buffer is.",
    ),
    (
        "exception",
        "byteswarning",
        "onyo_la_baiti",
        "noun phrase",
        "high",
        "New. Warning about bytes (baiti).",
    ),
    (
        "exception",
        "childprocesserror",
        "hitilafu_ya_mchakato_mtoto",
        "noun phrase",
        "medium",
        "New. Error of a child process: mchakato (process) with mtoto (child) in apposition.",
    ),
    (
        "exception",
        "connectionabortederror",
        "hitilafu_ya_muunganisho_uliokatizwa",
        "noun phrase",
        "medium",
        "New. Error of a connection (muunganisho, class 3) that was cut off.",
    ),
    (
        "exception",
        "connectionerror",
        "hitilafu_ya_muunganisho",
        "noun phrase",
        "high",
        "New. Error of a connection (muunganisho).",
    ),
    (
        "exception",
        "connectionrefusederror",
        "hitilafu_ya_muunganisho_uliokataliwa",
        "noun phrase",
        "medium",
        "New. Error of a connection that was refused.",
    ),
    (
        "exception",
        "connectionreseterror",
        "hitilafu_ya_muunganisho_uliowekwa_upya",
        "noun phrase",
        "medium",
        "New. Error of a connection that was reset (set anew, wekwa upya).",
    ),
    (
        "exception",
        "deprecationwarning",
        "onyo_la_kupitwa_na_wakati",
        "noun phrase",
        "high",
        "New. kupitwa na wakati (to be overtaken by time) is the Swahili idiom for obsolete.",
    ),
    (
        "exception",
        "encodingwarning",
        "onyo_la_usimbaji",
        "noun phrase",
        "medium",
        "New. Warning about encoding (usimbaji).",
    ),
    (
        "exception",
        "environmenterror",
        "hitilafu_ya_mazingira",
        "noun phrase",
        "high",
        "New. Error of the environment (mazingira).",
    ),
    (
        "exception",
        "eoferror",
        "hitilafu_ya_mwisho_wa_faili",
        "noun phrase",
        "high",
        "New. Error of the end of a file (mwisho wa faili).",
    ),
    (
        "exception",
        "exception",
        "hali_ya_kipekee",
        "noun phrase",
        "low",
        "New. An exceptional condition (hali ya kipekee), Python's own definition, and a root distinct from Hitilafu (error) and onyo (warning).",
    ),
    (
        "exception",
        "exceptiongroup",
        "kundi_la_hali_za_kipekee",
        "noun phrase",
        "low",
        "New. A group (kundi, class 5) of exceptional conditions.",
    ),
    (
        "exception",
        "fileexistserror",
        "hitilafu_ya_faili_iliyopo",
        "noun phrase",
        "high",
        "New. Error of a file that exists; the relative iliyopo agrees with faili, class 9.",
    ),
    (
        "exception",
        "filenotfounderror",
        "hitilafu_ya_faili_isiyopatikana",
        "noun phrase",
        "high",
        "New. Error of a file that is not found.",
    ),
    (
        "exception",
        "floatingpointerror",
        "hitilafu_ya_namba_desimali",
        "noun phrase",
        "medium",
        "New. Error of a decimal number, after namba_desimali for float.",
    ),
    (
        "exception",
        "futurewarning",
        "onyo_la_baadaye",
        "noun phrase",
        "medium",
        "New. A warning about later (baadaye): behaviour that will change.",
    ),
    (
        "exception",
        "generatorexit",
        "kutoka_kwa_kizalishi",
        "noun phrase",
        "low",
        "New. The exit (kutoka, class 15) of a generator; kizalishi is a ki- instrument noun from zalisha (produce).",
    ),
    (
        "exception",
        "importerror",
        "hitilafu_ya_uagizaji",
        "noun phrase",
        "high",
        "New. Error of importing (uagizaji), the noun of agiza.",
    ),
    (
        "exception",
        "importwarning",
        "onyo_la_uagizaji",
        "noun phrase",
        "high",
        "New. Warning about importing.",
    ),
    (
        "exception",
        "indentationerror",
        "hitilafu_ya_ujongezaji",
        "noun phrase",
        "low",
        "New. Error of indentation (ujongezaji), the term of Swahili word processors.",
    ),
    (
        "exception",
        "indexerror",
        "hitilafu_ya_faharasa",
        "noun phrase",
        "medium",
        "New. Error of an index (faharasa).",
    ),
    (
        "exception",
        "interruptederror",
        "hitilafu_ya_kukatizwa",
        "noun phrase",
        "medium",
        "New. Error of being interrupted (kukatizwa).",
    ),
    (
        "exception",
        "ioerror",
        "hitilafu_ya_uingizaji_na_utoaji",
        "noun phrase",
        "medium",
        "New. Error of input and output.",
    ),
    (
        "exception",
        "isadirectoryerror",
        "hitilafu_ya_kuwa_saraka",
        "noun phrase",
        "medium",
        "New. Error of being a directory (saraka).",
    ),
    (
        "exception",
        "keyboardinterrupt",
        "ukatizaji_kwa_kibodi",
        "noun phrase",
        "medium",
        "New. Interruption (ukatizaji) by the keyboard; kwa is instrumental here, not a concord.",
    ),
    (
        "exception",
        "keyerror",
        "hitilafu_ya_ufunguo",
        "noun phrase",
        "high",
        "New. Error of a key (ufunguo).",
    ),
    (
        "exception",
        "lookuperror",
        "hitilafu_ya_utafutaji",
        "noun phrase",
        "medium",
        "New. Error of looking up (utafutaji, searching).",
    ),
    (
        "exception",
        "memoryerror",
        "hitilafu_ya_kumbukumbu",
        "noun phrase",
        "high",
        "New. Error of memory (kumbukumbu).",
    ),
    (
        "exception",
        "modulenotfounderror",
        "hitilafu_ya_moduli_isiyopatikana",
        "noun phrase",
        "high",
        "New. Error of a module (moduli) that is not found.",
    ),
    (
        "exception",
        "nameerror",
        "hitilafu_ya_jina",
        "noun phrase",
        "high",
        "New. Error of a name (jina).",
    ),
    (
        "exception",
        "notadirectoryerror",
        "hitilafu_ya_kutokuwa_saraka",
        "noun phrase",
        "medium",
        "New. Error of not being a directory, the negative of hitilafu_ya_kuwa_saraka.",
    ),
    (
        "exception",
        "notimplementederror",
        "hitilafu_ya_kutotekelezwa",
        "noun phrase",
        "medium",
        "New. Error of not being implemented, beside haijatekelezwa.",
    ),
    (
        "exception",
        "oserror",
        "hitilafu_ya_mfumo_endeshi",
        "noun phrase",
        "high",
        "New. mfumo endeshi is the Swahili term for an operating system.",
    ),
    (
        "exception",
        "overflowerror",
        "hitilafu_ya_kufurika",
        "noun phrase",
        "high",
        "New. Error of overflowing (kufurika).",
    ),
    (
        "exception",
        "pendingdeprecationwarning",
        "onyo_la_kupitwa_na_wakati_baadaye",
        "noun phrase",
        "medium",
        "New. Warning of becoming obsolete later, after onyo_la_kupitwa_na_wakati.",
    ),
    (
        "exception",
        "permissionerror",
        "hitilafu_ya_ruhusa",
        "noun phrase",
        "high",
        "New. Error of permission (ruhusa).",
    ),
    (
        "exception",
        "processlookuperror",
        "hitilafu_ya_utafutaji_wa_mchakato",
        "noun phrase",
        "medium",
        "New. Error of looking up a process (mchakato).",
    ),
    (
        "exception",
        "pythonfinalizationerror",
        "hitilafu_ya_kuhitimisha_python",
        "noun phrase",
        "medium",
        "New. Error of finalising (kuhitimisha) Python; the proper name stays as written.",
    ),
    (
        "exception",
        "recursionerror",
        "hitilafu_ya_ujirudiaji",
        "noun phrase",
        "low",
        "New. ujirudiaji, the noun of jirudia (repeat itself, with the reflexive -ji-), is recursion.",
    ),
    (
        "exception",
        "referenceerror",
        "hitilafu_ya_rejeleo",
        "noun phrase",
        "medium",
        "New. Error of a reference (rejeleo).",
    ),
    (
        "exception",
        "resourcewarning",
        "onyo_la_rasilimali",
        "noun phrase",
        "high",
        "New. Warning about resources (rasilimali).",
    ),
    (
        "exception",
        "runtimeerror",
        "hitilafu_ya_wakati_wa_utekelezaji",
        "noun phrase",
        "medium",
        "New. Error of the time of execution (wakati wa utekelezaji), utekelezaji being the noun of tekeleza.",
    ),
    (
        "exception",
        "runtimewarning",
        "onyo_la_wakati_wa_utekelezaji",
        "noun phrase",
        "medium",
        "New. Warning at the time of execution.",
    ),
    (
        "exception",
        "stopasynciteration",
        "mwisho_wa_marudio_sambamba",
        "noun phrase",
        "low",
        "New. The end of concurrent iteration. Decision flag --loans.",
    ),
    (
        "exception",
        "stopiteration",
        "mwisho_wa_marudio",
        "noun phrase",
        "medium",
        "New. The end of iteration (mwisho wa marudio): the signal that a kirudiaji has nothing left.",
    ),
    (
        "exception",
        "syntaxerror",
        "hitilafu_ya_sintaksia",
        "noun phrase",
        "high",
        "New. Error of syntax (sintaksia, the term of Swahili grammar).",
    ),
    (
        "exception",
        "syntaxwarning",
        "onyo_la_sintaksia",
        "noun phrase",
        "high",
        "New. Warning about syntax.",
    ),
    (
        "exception",
        "systemerror",
        "hitilafu_ya_mfumo",
        "noun phrase",
        "high",
        "New. Error of the system (mfumo).",
    ),
    (
        "exception",
        "systemexit",
        "kutoka_kwa_mfumo",
        "noun phrase",
        "medium",
        "New. The exit of the system, after kutoka_kwa_kizalishi.",
    ),
    (
        "exception",
        "taberror",
        "hitilafu_ya_kichupo",
        "noun phrase",
        "low",
        "New. Error of a tab (kichupo).",
    ),
    (
        "exception",
        "timeouterror",
        "hitilafu_ya_kuisha_kwa_muda",
        "noun phrase",
        "medium",
        "New. Error of time running out (kuisha kwa muda).",
    ),
    (
        "exception",
        "typeerror",
        "hitilafu_ya_aina",
        "noun phrase",
        "high",
        "New. Error of type (aina).",
    ),
    (
        "exception",
        "unboundlocalerror",
        "hitilafu_ya_kigeu_kisichopewa_thamani",
        "noun phrase",
        "medium",
        "New. Error of a variable (kigeu, class 7) that has not been given a value; kisicho- agrees with kigeu.",
    ),
    (
        "exception",
        "unicodedecodeerror",
        "hitilafu_ya_usimbuaji_wa_yunikodi",
        "noun phrase",
        "medium",
        "New. Error of decoding (usimbuaji) Unicode (Yunikodi, the respelled loan).",
    ),
    (
        "exception",
        "unicodeencodeerror",
        "hitilafu_ya_usimbaji_wa_yunikodi",
        "noun phrase",
        "medium",
        "New. Error of encoding (usimbaji) Unicode.",
    ),
    (
        "exception",
        "unicodeerror",
        "hitilafu_ya_yunikodi",
        "noun phrase",
        "high",
        "New. Error of Unicode.",
    ),
    (
        "exception",
        "unicodetranslateerror",
        "hitilafu_ya_tafsiri_ya_yunikodi",
        "noun phrase",
        "medium",
        "New. Error of translating (tafsiri) Unicode.",
    ),
    (
        "exception",
        "unicodewarning",
        "onyo_la_yunikodi",
        "noun phrase",
        "high",
        "New. Warning about Unicode.",
    ),
    (
        "exception",
        "userwarning",
        "onyo_la_mtumiaji",
        "noun phrase",
        "high",
        "New. A warning of the user (mtumiaji).",
    ),
    (
        "exception",
        "valueerror",
        "hitilafu_ya_thamani",
        "noun phrase",
        "high",
        "New. Error of a value (thamani).",
    ),
    (
        "exception",
        "warning",
        "onyo",
        "noun",
        "high",
        "New. onyo (warning), the Warning root.",
    ),
    (
        "exception",
        "zerodivisionerror",
        "hitilafu_ya_kugawanya_kwa_sifuri",
        "noun phrase",
        "high",
        "New. Error of dividing by zero (kugawanya kwa sifuri); kwa is instrumental here.",
    ),
]

# --- decision branches --------------------------------------------------------

#: --verbs infinitive: the ku- infinitive of every action value.
INFINITIVE: dict[tuple[str, str], str] = {
    ("keyword", "assert"): "kuhakikisha",
    ("keyword", "await"): "kungoja",
    ("keyword", "break"): "kuvunja",
    ("keyword", "continue"): "kuendelea",
    ("keyword", "def"): "kufasili",
    ("keyword", "del"): "kufuta",
    ("keyword", "import"): "kuagiza",
    ("keyword", "match"): "kulinganisha",
    ("keyword", "pass"): "kupita",
    ("keyword", "raise"): "kuibua",
    ("keyword", "return"): "kurudisha",
    ("keyword", "try"): "kujaribu",
    ("keyword", "yield"): "kutoa",
    ("builtin_func", "__import__"): "__kuagiza__",
    ("builtin_func", "compile"): "kukusanya",
    ("builtin_func", "delattr"): "kufuta_sifa",
    ("builtin_func", "divmod"): "kugawanya_na_baki",
    ("builtin_func", "enumerate"): "kuhesabu",
    ("builtin_func", "eval"): "kutathmini",
    ("builtin_func", "exec"): "kutekeleza",
    ("builtin_func", "filter"): "kuchuja",
    ("builtin_func", "format"): "kuumbiza",
    ("builtin_func", "getattr"): "kupata_sifa",
    ("builtin_func", "help"): "kusaidia",
    ("builtin_func", "input"): "kuingiza",
    ("builtin_func", "map"): "kutumia_kwa_kila",
    ("builtin_func", "open"): "kufungua",
    ("builtin_func", "print"): "kuchapisha",
    ("builtin_func", "round"): "kukadiria",
    ("builtin_func", "setattr"): "kuweka_sifa",
    ("builtin_func", "zip"): "kuoanisha",
}

#: --compounds juxtaposed: every value with an associative particle, without it.
#: Instrumental kwa (ukatizaji_kwa_kibodi, KwaSifuri), na (and), possessives
#: (darasa_lake) and relatives are not concords and stay.
JUXTAPOSED: dict[tuple[str, str], str] = {
    ("builtin_func", "bin"): "msingi_mbili",
    ("builtin_func", "breakpoint"): "mahali_kusimama",
    ("builtin_func", "classmethod"): "njia_darasa",
    ("builtin_func", "dir"): "orodha_sifa",
    ("builtin_func", "globals"): "vigeu_kote",
    ("builtin_func", "hex"): "msingi_kumi_na_sita",
    ("builtin_func", "isinstance"): "ni_mfano",
    ("builtin_func", "issubclass"): "ni_darasa_tanzu",
    ("builtin_func", "locals"): "vigeu_hapa",
    ("builtin_func", "max"): "kiwango_juu",
    ("builtin_func", "min"): "kiwango_chini",
    ("builtin_func", "oct"): "msingi_nane",
    ("builtin_func", "ord"): "msimbo_herufi",
    ("builtin_type", "bytearray"): "safu_baiti",
    ("builtin_type", "memoryview"): "mtazamo_kumbukumbu",
    ("exception", "arithmeticerror"): "hitilafu_hesabu",
    ("exception", "assertionerror"): "hitilafu_uhakikisho",
    ("exception", "attributeerror"): "hitilafu_sifa",
    ("exception", "baseexception"): "hali_kipekee_msingi",
    ("exception", "baseexceptiongroup"): "kundi_msingi_hali_kipekee",
    ("exception", "blockingioerror"): "hitilafu_kuzuia_uingizaji_na_utoaji",
    ("exception", "brokenpipeerror"): "hitilafu_bomba_lililovunjika",
    ("exception", "buffererror"): "hitilafu_hifadhi_muda",
    ("exception", "byteswarning"): "onyo_baiti",
    ("exception", "childprocesserror"): "hitilafu_mchakato_mtoto",
    ("exception", "connectionabortederror"): "hitilafu_muunganisho_uliokatizwa",
    ("exception", "connectionerror"): "hitilafu_muunganisho",
    ("exception", "connectionrefusederror"): "hitilafu_muunganisho_uliokataliwa",
    ("exception", "connectionreseterror"): "hitilafu_muunganisho_uliowekwa_upya",
    ("exception", "deprecationwarning"): "onyo_kupitwa_na_wakati",
    ("exception", "encodingwarning"): "onyo_usimbaji",
    ("exception", "environmenterror"): "hitilafu_mazingira",
    ("exception", "eoferror"): "hitilafu_mwisho_faili",
    ("exception", "exception"): "hali_kipekee",
    ("exception", "exceptiongroup"): "kundi_hali_kipekee",
    ("exception", "fileexistserror"): "hitilafu_faili_iliyopo",
    ("exception", "filenotfounderror"): "hitilafu_faili_isiyopatikana",
    ("exception", "floatingpointerror"): "hitilafu_namba_desimali",
    ("exception", "futurewarning"): "onyo_baadaye",
    ("exception", "generatorexit"): "kutoka_kizalishi",
    ("exception", "importerror"): "hitilafu_uagizaji",
    ("exception", "importwarning"): "onyo_uagizaji",
    ("exception", "indentationerror"): "hitilafu_ujongezaji",
    ("exception", "indexerror"): "hitilafu_faharasa",
    ("exception", "interruptederror"): "hitilafu_kukatizwa",
    ("exception", "ioerror"): "hitilafu_uingizaji_na_utoaji",
    ("exception", "isadirectoryerror"): "hitilafu_kuwa_saraka",
    ("exception", "keyerror"): "hitilafu_ufunguo",
    ("exception", "lookuperror"): "hitilafu_utafutaji",
    ("exception", "memoryerror"): "hitilafu_kumbukumbu",
    ("exception", "modulenotfounderror"): "hitilafu_moduli_isiyopatikana",
    ("exception", "nameerror"): "hitilafu_jina",
    ("exception", "notadirectoryerror"): "hitilafu_kutokuwa_saraka",
    ("exception", "notimplementederror"): "hitilafu_kutotekelezwa",
    ("exception", "oserror"): "hitilafu_mfumo_endeshi",
    ("exception", "overflowerror"): "hitilafu_kufurika",
    ("exception", "pendingdeprecationwarning"): "onyo_kupitwa_na_wakati_baadaye",
    ("exception", "permissionerror"): "hitilafu_ruhusa",
    ("exception", "processlookuperror"): "hitilafu_utafutaji_mchakato",
    ("exception", "pythonfinalizationerror"): "hitilafu_kuhitimisha_python",
    ("exception", "recursionerror"): "hitilafu_ujirudiaji",
    ("exception", "referenceerror"): "hitilafu_rejeleo",
    ("exception", "resourcewarning"): "onyo_rasilimali",
    ("exception", "runtimeerror"): "hitilafu_wakati_utekelezaji",
    ("exception", "runtimewarning"): "onyo_wakati_utekelezaji",
    ("exception", "stopasynciteration"): "mwisho_marudio_sambamba",
    ("exception", "stopiteration"): "mwisho_marudio",
    ("exception", "syntaxerror"): "hitilafu_sintaksia",
    ("exception", "syntaxwarning"): "onyo_sintaksia",
    ("exception", "systemerror"): "hitilafu_mfumo",
    ("exception", "systemexit"): "kutoka_mfumo",
    ("exception", "taberror"): "hitilafu_kichupo",
    ("exception", "timeouterror"): "hitilafu_kuisha_muda",
    ("exception", "typeerror"): "hitilafu_aina",
    ("exception", "unboundlocalerror"): "hitilafu_kigeu_kisichopewa_thamani",
    ("exception", "unicodedecodeerror"): "hitilafu_usimbuaji_yunikodi",
    ("exception", "unicodeencodeerror"): "hitilafu_usimbaji_yunikodi",
    ("exception", "unicodeerror"): "hitilafu_yunikodi",
    ("exception", "unicodetranslateerror"): "hitilafu_tafsiri_yunikodi",
    ("exception", "unicodewarning"): "onyo_yunikodi",
    ("exception", "userwarning"): "onyo_mtumiaji",
    ("exception", "valueerror"): "hitilafu_thamani",
    ("exception", "zerodivisionerror"): "hitilafu_kugawanya_kwa_sifuri",
}

#: --loans adapted: the respelled English loan where a native word was chosen.
#: The async family swaps sambamba for asinkroni inside whatever the other
#: flags produced; format follows --verbs.
LOANS: dict[tuple[str, str], str] = {
    ("builtin_type", "bool"): "buliani",
    ("builtin_type", "str"): "stringi",
}
LOAN_FORMAT = {"imperative": "fomati", "infinitive": "kufomati"}
ASYNC_FAMILY = {
    ("keyword", "async"),
    ("builtin_func", "aiter"),
    ("builtin_func", "anext"),
    ("exception", "stopasynciteration"),
}

FLAG_CHOICES = {
    "verbs": ("imperative", "infinitive"),
    "compounds": ("associative", "juxtaposed"),
    "loans": ("native", "adapted"),
    "joiner": ("none", "underscore"),
    "exceptions": ("lower", "capwords"),
}
DEFAULTS = tuple(choices[0] for choices in FLAG_CHOICES.values())


def separated(
    category: str, name: str, seed: str, verbs: str, compounds: str, loans: str
) -> str:
    """The value with its word boundaries, as written in the seed data.

    Multi-word values are written with underscores between the words
    (hitilafu_ya_thamani). This is the form the database keeps as the
    record of the separation, whatever surface ships.
    """
    key = (category, name)
    value = seed
    if compounds == "juxtaposed" and key in JUXTAPOSED:
        value = JUXTAPOSED[key]
    if verbs == "infinitive" and key in INFINITIVE:
        value = INFINITIVE[key]
    if loans == "adapted":
        if key in LOANS:
            value = LOANS[key]
        elif key in ASYNC_FAMILY:
            value = value.replace("sambamba", "asinkroni")
        elif key == ("builtin_func", "format"):
            value = LOAN_FORMAT[verbs]
    return value


def surface(category: str, words: str, joiner: str, exceptions: str) -> str:
    """The shipped identifier for a separated value.

    The default mirrors how Python spells its own reserved words: lowercase,
    words run together (getattr, isinstance, and the en pack's valueerror).
    Underscores and capitals are left to the programmer's own code. A dunder
    keeps its own underscores (__agiza__).
    """
    if category == "exception" and exceptions == "capwords":
        return "".join(word.capitalize() for word in words.split("_"))
    if joiner == "underscore":
        return words
    if words.startswith("__") and words.endswith("__"):
        return "__" + words[2:-2].replace("_", "") + "__"
    return words.replace("_", "")


def resolve(
    verbs: str, compounds: str, loans: str, joiner: str, exceptions: str
) -> list[tuple[str, str, str, str, str, str]]:
    """Apply the decision flags to SELECTIONS and return the chosen rows.

    Every multi-word row's rationale records its separated form, so the word
    boundaries stay in the database when the shipped value runs them
    together. A value the flags change from the recommended one gets its own
    rationale naming the branch and the value it stands in for.
    """
    rows = []
    for category, name, seed, word_type, confidence, rationale in SELECTIONS:
        key = (category, name)
        words = separated(category, name, seed, verbs, compounds, loans)
        value = surface(category, words, joiner, exceptions)
        default_words = separated(category, name, seed, *DEFAULTS[:3])
        recommended = surface(category, default_words, *DEFAULTS[3:])
        if "_" in default_words.strip("_"):
            rationale += f" Separated form: {default_words}."
        if value != recommended:
            applies = {
                "verbs": key in INFINITIVE,
                "compounds": key in JUXTAPOSED,
                "loans": key in LOANS
                or key in ASYNC_FAMILY
                or key == ("builtin_func", "format"),
                "joiner": "_" in words.strip("_"),
                "exceptions": category == "exception",
            }
            run = dict(zip(FLAG_CHOICES, (verbs, compounds, loans, joiner, exceptions)))
            flags = ", ".join(
                f"--{flag} {choice}"
                for (flag, choice), default in zip(run.items(), DEFAULTS)
                if choice != default and applies[flag]
            )
            note = f" Separated form: {words}." if "_" in words.strip("_") else ""
            rationale = (
                f"Branch {flags}: in place of the recommended {recommended!r}.{note} "
                f"The recommended value's reasoning: {rationale}"
            )
        rows.append((category, name, value, word_type, confidence, rationale))
    return rows


def all_branches() -> list[tuple[str, ...]]:
    """Every combination of the decision flags."""
    return list(itertools.product(*FLAG_CHOICES.values()))


def candidate_rows() -> list[tuple[str, str, str, str, str, str]]:
    """Every value any branch selects, so each side's candidate row exists
    whichever flags a run is given (the recommended values included)."""
    seen: set[tuple[str, str, str]] = set()
    out = []
    for branch in all_branches():
        for row in resolve(*branch):
            if row[:3] not in seen:
                seen.add(row[:3])
                out.append(row)
    return out


def check_target_state(wanted: dict[tuple[str, str], str]) -> list[str]:
    """Every reason the chosen values could not all be selected together.

    Mirrors the two refusals ``set_selected`` can raise (the publish gate,
    including the sw forbidden letters, and the cross-term collision guard,
    under which same-name terms such as ``type`` may share a value), so
    neither can stop a run halfway.
    """
    problems = [
        f"refused by the publish gate: {category} {name} -> {value!r}"
        for (category, name), value in wanted.items()
        if not is_valid_pack_value(name, value, LANG)
    ]
    owners: dict[str, set[str]] = {}
    for (_, name), value in wanted.items():
        owners.setdefault(value, set()).add(name)
    problems += [
        f"collision: {value!r} would be selected for {sorted(names)}"
        for value, names in owners.items()
        if len(names) > 1
    ]
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Select the Swahili Python vocabulary, DB-first."
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    for flag, choices in FLAG_CHOICES.items():
        ap.add_argument(f"--{flag}", choices=choices, default=choices[0])
    args = ap.parse_args()

    if not args.db.exists():
        print(
            f"no database at {args.db}; copy it in from the data home first",
            file=sys.stderr,
        )
        return 2
    db = TranslationDatabase(db_path=str(args.db))

    rows = resolve(*(getattr(args, flag) for flag in FLAG_CHOICES))
    term_ids = {}
    for category, name, *_ in rows:
        term = db.get_term_by_name(name, "python", category=category)
        if term is None or term["category"] != category:
            print(f"missing term row: {category} {name}", file=sys.stderr)
            return 1
        term_ids[(category, name)] = term["id"]

    # set_selected commits per call, so check the whole target state before
    # writing anything: a refusal mid-pass would otherwise leave terms with no
    # selection at all, or a refused value in the candidate pool. Every other
    # branch is checked too, so a later flip cannot fail halfway either.
    problems = []
    for branch in all_branches():
        found = check_target_state({(c, n): v for c, n, v, *_ in resolve(*branch)})
        problems += [f"[{' '.join(branch)}] {p}" for p in found]
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    # One read of the sw pool per term, not one per candidate value.
    pool = {
        term_id: {r["translation"] for r in db.get_translations(term_id, LANG)}
        for term_id in term_ids.values()
    }
    added = 0
    for category, name, value, word_type, confidence, rationale in candidate_rows():
        term_id = term_ids[(category, name)]
        if value not in pool[term_id]:
            added += 1
            if not args.dry_run:
                db.add_translation(
                    term_id=term_id,
                    language_code=LANG,
                    translation=value,
                    source=GEN_SOURCE,
                    model_version=GEN_MODEL,
                    word_type=word_type,
                    confidence=confidence,
                    model_rationale=rationale,
                    created_by=GEN_CREATED_BY,
                )

    # Selections in two passes: clear this language's selections for the
    # terms below, then set them, so a branch flip that swaps two values can
    # never trip the collision guard against its own previous state.
    current = {
        (r["term_category"], r["term_name"]): r["translation"]
        for r in db.get_all_selected(language_code=LANG)
        if r["programming_language"] == "python"
    }
    wanted = {(c, n): (v, r) for c, n, v, _, _, r in rows}
    changed = {k for k, (v, _) in wanted.items() if current.get(k) != v}
    unchanged = len(wanted) - len(changed)
    if not args.dry_run:
        for key in changed:
            if key in current:
                db.remove_selected(term_ids[key], LANG)
        for key in sorted(changed):
            value, rationale = wanted[key]
            db.set_selected(
                term_id=term_ids[key],
                language_code=LANG,
                translation=value,
                selected_by=SELECTED_BY,
                selection_reason=rationale,
            )

    mode = "dry run, nothing written" if args.dry_run else "written"
    print(
        f"sw: {len(wanted)} terms; {added} candidate rows added, "
        f"{len(changed)} selections set, {unchanged} already selected ({mode})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
