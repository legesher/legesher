#!/usr/bin/env python3
"""CORE-1644: select the Ukrainian (uk) Python vocabulary, DB-first.

Ukrainian had a ``languages`` row and 109 candidate rows but no pack: 103
community candidates from the 2025-11-11 bulk import (35 keywords, 53 builtin
functions, 15 builtin types, one per term) and six showcase seeds (CORE-1299),
with no exception, special-constant or implicit-parameter rows at all. This
script decides all 184 terms of the shipped inventory.

Design:
  * DB-first: every value goes through ``add_translation`` (a provenanced
    candidate, so no selection is orphaned from the pool) and then
    ``set_selected`` (publish gate, collision guard, and the uk forbidden-letter
    guard). The exporter regenerates the pack from the selections.
  * A community candidate is kept wherever it is the right Ukrainian word; it
    is replaced only where it is wrong in sense or form, and each replacement
    says why in its rationale. The replaced candidate stays in the pool.
  * Generated values are written as a linguist would choose them (part of
    speech, aspect, case, register, native CS usage), following
    ``style-guides/uk.yml``. Prompts were rendered through the pipeline's own
    PromptBuilder; the selections are ``source='claude'`` at the experimental
    rung, pending native review.
  * Four calls are open decisions and are flags, both sides prepared. Every
    run writes the candidate rows for every side, so flipping a decision is a
    re-run with a different flag, then the usual regen ritual:

      --apostrophe drop|u02bc     ім'я-class words: omit the apostrophe, or
                                  spell it with U+02BC (the script audit reads
                                  U+02BC as Unknown today, so this side also
                                  needs a script_policy table entry)
      --def визначити|оголосити   define vs declare
      --none ніщо|нічого          nominative pronoun vs genitive/adverbial
      --verbs infinitive|imperative

  * Idempotent: a re-run with the same flags changes nothing. The whole target
    state is checked before any selection is touched, so a run either sets
    everything or changes nothing.

Usage:
    uv run python libs/i18n/scripts/translate/backfill_core1644.py [--dry-run]
        [--db PATH] [--apostrophe drop] [--def визначити] [--none ніщо]
        [--verbs infinitive]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
I18N_ROOT = HERE.parents[2]  # libs/i18n
sys.path.insert(0, str(I18N_ROOT))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.selection import is_valid_pack_value  # noqa: E402

DB_PATH = I18N_ROOT / "legesher_i18n" / "db" / "translations.db"

LANG = "uk"
SELECTED_BY = "CORE-1644"
GEN_SOURCE = "claude"
GEN_MODEL = "claude-opus-5-5"
GEN_CREATED_BY = "CORE-1644"

KEEP = "Community candidate retained"

# (category, term, value, word_type, confidence, rationale)
# Values here are the recommended branch: apostrophe dropped, def визначити,
# None ніщо, infinitive verbs. The alternates below override them per flag.
SELECTIONS: list[tuple[str, str, str, str, str, str]] = [
    # --- keywords -----------------------------------------------------------
    (
        "keyword",
        "False",
        "хибність",
        "noun",
        "high",
        f"{KEEP}: істина / хибність is the logic pair Ukrainian uses for truth values.",
    ),
    ("keyword", "True", "істина", "noun", "high", f"{KEEP}: pairs with хибність."),
    (
        "keyword",
        "None",
        "ніщо",
        "pronoun",
        "medium",
        "Showcase seed retained (CORE-1299). Nominative ніщо names the absence as a value (повернути ніщо, x є ніщо); the community нічого is genitive and adverbial in feel. Decision flag --none.",
    ),
    ("keyword", "and", "і", "conjunction", "high", f"{KEEP}: the plain conjunction."),
    (
        "keyword",
        "as",
        "як",
        "conjunction",
        "high",
        f"{KEEP}: імпортувати x як y reads naturally.",
    ),
    (
        "keyword",
        "assert",
        "перевірити",
        "verb",
        "medium",
        f"{KEEP}: assert checks a condition; перевірити (verify) names what it does, which стверджувати (claim) does not. Pairs with ПомилкаПеревірки.",
    ),
    (
        "keyword",
        "async",
        "асинхронно",
        "adverb",
        "high",
        f"{KEEP}: the adverb modifies the verb it precedes (асинхронно визначити).",
    ),
    (
        "keyword",
        "await",
        "очікувати",
        "verb",
        "high",
        f"{KEEP}: imperfective infinitive; awaiting is an ongoing action.",
    ),
    (
        "keyword",
        "break",
        "перервати",
        "verb",
        "high",
        f"{KEEP}: perfective infinitive, interrupt the loop.",
    ),
    (
        "keyword",
        "case",
        "випадок",
        "noun",
        "high",
        "New. The noun for one alternative of a match (випадок 1:), as in Ukrainian prose on case analysis.",
    ),
    ("keyword", "class", "клас", "noun", "high", f"{KEEP}: the established term."),
    (
        "keyword",
        "continue",
        "продовжити",
        "verb",
        "high",
        f"{KEEP}: perfective infinitive.",
    ),
    (
        "keyword",
        "def",
        "визначити",
        "verb",
        "medium",
        "Showcase seed retained (CORE-1299). def defines a function body, which is визначити (define); the community оголосити (declare) names a declaration without a body. Decision flag --def.",
    ),
    (
        "keyword",
        "del",
        "видалити",
        "verb",
        "high",
        f"{KEEP}: perfective infinitive, delete.",
    ),
    (
        "keyword",
        "elif",
        "інакше_якщо",
        "conjunction",
        "high",
        f"{KEEP}: else + if, joined with the underscore joiner.",
    ),
    ("keyword", "else", "інакше", "adverb", "high", f"{KEEP}: otherwise."),
    (
        "keyword",
        "except",
        "перехопити",
        "verb",
        "high",
        f"{KEEP}: catch (intercept) the exception, the sense Ukrainian programmers use.",
    ),
    (
        "keyword",
        "except*",
        "перехопити*",
        "verb",
        "high",
        "New. Mirrors except with the trailing * the soft keyword requires (CORE-1839).",
    ),
    (
        "keyword",
        "finally",
        "наостанок",
        "adverb",
        "medium",
        "Replaces the community зрештою, which means after all / eventually and carries a discourse sense. наостанок (at the very end, lastly) names a block that always runs last.",
    ),
    (
        "keyword",
        "for",
        "для_кожного",
        "preposition",
        "high",
        f"{KEEP}: for each; для_кожного x у список reads as Ukrainian.",
    ),
    ("keyword", "from", "з", "preposition", "high", f"{KEEP}: з модуль імпортувати x."),
    (
        "keyword",
        "global",
        "глобальна",
        "adjective",
        "medium",
        f"{KEEP}: feminine, agreeing with the implied змінна (variable); pairs with нелокальна.",
    ),
    (
        "keyword",
        "if",
        "якщо",
        "conjunction",
        "high",
        "Showcase seed retained (CORE-1299); matches the community candidate.",
    ),
    (
        "keyword",
        "import",
        "імпортувати",
        "verb",
        "high",
        f"{KEEP}: the established term.",
    ),
    (
        "keyword",
        "in",
        "у",
        "preposition",
        "high",
        f"{KEEP}: у / в alternate by euphony; a pack needs one form and у is the safer default.",
    ),
    ("keyword", "is", "є", "verb", "high", f"{KEEP}: the copula."),
    (
        "keyword",
        "lambda",
        "лямбда",
        "noun",
        "high",
        f"{KEEP}: the Greek letter's Ukrainian name.",
    ),
    (
        "keyword",
        "match",
        "зіставити",
        "verb",
        "medium",
        "New. Pattern matching is зіставлення зі зразком; the perfective infinitive keeps one verb form across the pack.",
    ),
    (
        "keyword",
        "nonlocal",
        "нелокальна",
        "adjective",
        "medium",
        f"{KEEP}: feminine, agreeing with the implied змінна; pairs with глобальна.",
    ),
    ("keyword", "not", "не", "particle", "high", f"{KEEP}: the negation particle."),
    ("keyword", "or", "або", "conjunction", "high", f"{KEEP}: the plain disjunction."),
    ("keyword", "pass", "пропустити", "verb", "high", f"{KEEP}: skip."),
    (
        "keyword",
        "raise",
        "викинути",
        "verb",
        "medium",
        "Replaces the community підняти, a calque of English raise (physically lift). Ukrainian technical usage is викинути виняток (throw an exception).",
    ),
    (
        "keyword",
        "return",
        "повернути",
        "verb",
        "high",
        "Showcase seed retained (CORE-1299); matches the community candidate.",
    ),
    (
        "keyword",
        "try",
        "спробувати",
        "verb",
        "high",
        f"{KEEP}: perfective infinitive, attempt.",
    ),
    (
        "keyword",
        "type",
        "тип",
        "noun",
        "high",
        "New for the 3.12 soft keyword; the same surface as the builtin type, which is the sanctioned same-name pair.",
    ),
    ("keyword", "while", "поки", "conjunction", "high", f"{KEEP}: while, as long as."),
    (
        "keyword",
        "with",
        "використовуючи",
        "adverbial participle",
        "medium",
        "Replaces the community з_допомогою (with the help of). The context manager reads as using: використовуючи відкрити(шлях) як файл.",
    ),
    (
        "keyword",
        "yield",
        "видати",
        "verb",
        "medium",
        f"{KEEP}: give out, hand over a value.",
    ),
    # --- builtin functions --------------------------------------------------
    (
        "builtin_func",
        "__import__",
        "__імпортувати__",
        "verb",
        "high",
        f"{KEEP}: import inside the dunder boundaries.",
    ),
    (
        "builtin_func",
        "abs",
        "абсолютне_значення",
        "noun phrase",
        "medium",
        f"{KEEP}: absolute value. School maths says модуль числа, but модуль also names a Python module, so the longer form avoids the clash.",
    ),
    (
        "builtin_func",
        "aiter",
        "асинхронний_ітератор",
        "noun phrase",
        "medium",
        "New. Asynchronous counterpart of iter (ітератор).",
    ),
    ("builtin_func", "all", "всі", "pronoun", "high", f"{KEEP}: all (of them)."),
    (
        "builtin_func",
        "anext",
        "асинхронне_наступне",
        "noun phrase",
        "medium",
        "New. Asynchronous counterpart of next (наступне), with neuter agreement kept.",
    ),
    (
        "builtin_func",
        "any",
        "хоч_один",
        "pronoun phrase",
        "medium",
        "Replaces the community будь_які (any ones, whichever). any() asks whether at least one element is true, which is хоч_один; якщо хоч_один(...) reads as a sentence.",
    ),
    (
        "builtin_func",
        "ascii",
        "екрановане_подання",
        "noun phrase",
        "low",
        "Replaces the community ascii, which is Latin script and fails the uk script policy. Ukrainian writes the acronym in Latin, and a Cyrillic transliteration is not a translation, so this is a native coinage for what the function returns: the repr with non-ASCII characters escaped (екрановане). Flagged for native review.",
    ),
    (
        "builtin_func",
        "bin",
        "двійкове",
        "adjective",
        "medium",
        "Replaces the community бінарне with the native term двійкове (двійкова система), consistent with шістнадцяткове and вісімкове.",
    ),
    (
        "builtin_func",
        "breakpoint",
        "точка_зупинки",
        "noun phrase",
        "medium",
        "Replaces the community точка_переривання (interruption point) with точка зупинки, the usual Ukrainian debugger term.",
    ),
    (
        "builtin_func",
        "callable",
        "можна_викликати",
        "predicate",
        "medium",
        f"{KEEP}: can be called; якщо можна_викликати(f) reads naturally.",
    ),
    ("builtin_func", "chr", "символ", "noun", "high", f"{KEEP}: character."),
    (
        "builtin_func",
        "classmethod",
        "метод_класу",
        "noun phrase",
        "high",
        f"{KEEP}: method of the class.",
    ),
    (
        "builtin_func",
        "compile",
        "компілювати",
        "verb",
        "high",
        f"{KEEP}: the established term.",
    ),
    (
        "builtin_func",
        "delattr",
        "видалити_атрибут",
        "verb phrase",
        "high",
        f"{KEEP}: delete attribute.",
    ),
    (
        "builtin_func",
        "dir",
        "перелік_атрибутів",
        "noun phrase",
        "medium",
        "Replaces the community директорія, a different concept (a filesystem directory). dir() lists the names an object carries.",
    ),
    (
        "builtin_func",
        "divmod",
        "частка_й_остача",
        "noun phrase",
        "medium",
        "Replaces the community ділення_націло (integer division), which drops half the result. divmod returns the quotient and the remainder; й is the euphonic form after a vowel.",
    ),
    (
        "builtin_func",
        "enumerate",
        "перерахувати",
        "verb",
        "medium",
        f"{KEEP}: list one by one.",
    ),
    (
        "builtin_func",
        "eval",
        "обчислити",
        "verb",
        "high",
        f"{KEEP}: evaluate, compute.",
    ),
    ("builtin_func", "exec", "виконати", "verb", "high", f"{KEEP}: execute."),
    ("builtin_func", "filter", "фільтрувати", "verb", "high", f"{KEEP}: filter."),
    ("builtin_func", "format", "форматувати", "verb", "high", f"{KEEP}: format."),
    (
        "builtin_func",
        "getattr",
        "отримати_атрибут",
        "verb phrase",
        "high",
        f"{KEEP}: get attribute.",
    ),
    (
        "builtin_func",
        "globals",
        "глобальні",
        "adjective",
        "medium",
        f"{KEEP}: the global (variables), plural; distinct from the keyword глобальна.",
    ),
    (
        "builtin_func",
        "hasattr",
        "має_атрибут",
        "predicate",
        "high",
        f"{KEEP}: has attribute.",
    ),
    (
        "builtin_func",
        "hash",
        "хеш",
        "noun",
        "high",
        "Replaces the community закодувати (to encode), a different operation. хеш is the loanword Ukrainian computing uses (хеш-функція).",
    ),
    ("builtin_func", "help", "допомога", "noun", "high", f"{KEEP}: help."),
    (
        "builtin_func",
        "hex",
        "шістнадцяткове",
        "adjective",
        "high",
        f"{KEEP}: hexadecimal, the native term.",
    ),
    (
        "builtin_func",
        "id",
        "ідентифікатор",
        "noun",
        "high",
        "Replaces the community ід, an abbreviation Ukrainian does not use; ідентифікатор is the term.",
    ),
    (
        "builtin_func",
        "input",
        "введення",
        "noun",
        "medium",
        f"{KEEP}: input, as a noun like довжина and сума.",
    ),
    (
        "builtin_func",
        "isinstance",
        "є_екземпляром",
        "predicate",
        "high",
        f"{KEEP}: is an instance (instrumental case).",
    ),
    (
        "builtin_func",
        "issubclass",
        "є_підкласом",
        "predicate",
        "high",
        f"{KEEP}: is a subclass.",
    ),
    ("builtin_func", "iter", "ітератор", "noun", "high", f"{KEEP}: iterator."),
    ("builtin_func", "len", "довжина", "noun", "high", f"{KEEP}: length."),
    (
        "builtin_func",
        "locals",
        "локальні",
        "adjective",
        "medium",
        f"{KEEP}: the local (variables), plural.",
    ),
    (
        "builtin_func",
        "map",
        "застосувати",
        "verb",
        "medium",
        "Replaces the community мапувати, a slang calque. map applies a function to each element; застосувати(f, список) reads as apply f to the list.",
    ),
    (
        "builtin_func",
        "max",
        "максимум",
        "noun",
        "high",
        "Replaces the community максимальне, an adjective with no noun to agree with; the noun matches сума and довжина.",
    ),
    (
        "builtin_func",
        "min",
        "мінімум",
        "noun",
        "high",
        "Replaces the community мінімальне, for the same reason as максимум.",
    ),
    (
        "builtin_func",
        "next",
        "наступне",
        "adjective",
        "medium",
        f"{KEEP}: the next (element), neuter.",
    ),
    (
        "builtin_func",
        "oct",
        "вісімкове",
        "adjective",
        "high",
        f"{KEEP}: octal, the native term.",
    ),
    ("builtin_func", "open", "відкрити", "verb", "high", f"{KEEP}: open."),
    (
        "builtin_func",
        "ord",
        "код_символу",
        "noun phrase",
        "high",
        "Corrects the community код_символа: the Ukrainian genitive of символ is символу; символа is the Russian pattern.",
    ),
    (
        "builtin_func",
        "pow",
        "степінь",
        "noun",
        "high",
        "Replaces the community ступінь (degree, level) with степінь, the mathematical power (піднести до степеня).",
    ),
    (
        "builtin_func",
        "print",
        "друкувати",
        "verb",
        "medium",
        "Showcase seed retained (CORE-1299); matches the community candidate.",
    ),
    ("builtin_func", "property", "властивість", "noun", "high", f"{KEEP}: property."),
    ("builtin_func", "range", "діапазон", "noun", "high", f"{KEEP}: range."),
    (
        "builtin_func",
        "repr",
        "подання",
        "noun",
        "medium",
        "Replaces the community представити (to introduce, present). repr returns a representation, which Ukrainian computing calls подання (подання даних).",
    ),
    (
        "builtin_func",
        "reversed",
        "обернений",
        "participle",
        "medium",
        "Replaces the community зворотній, a nonstandard spelling of зворотний. обернений (reversed) is a past participle parallel to відсортований.",
    ),
    ("builtin_func", "round", "округлити", "verb", "high", f"{KEEP}: round."),
    (
        "builtin_func",
        "setattr",
        "присвоїти_атрибут",
        "verb phrase",
        "high",
        f"{KEEP}: assign attribute (присвоїти значення is the usual phrase).",
    ),
    (
        "builtin_func",
        "slice",
        "зріз",
        "noun",
        "high",
        "Replaces the community відрізок (a line segment) with зріз, the Ukrainian term for a sequence slice.",
    ),
    (
        "builtin_func",
        "sorted",
        "відсортований",
        "participle",
        "high",
        f"{KEEP}: sorted.",
    ),
    (
        "builtin_func",
        "staticmethod",
        "статичний_метод",
        "noun phrase",
        "high",
        f"{KEEP}: static method.",
    ),
    ("builtin_func", "sum", "сума", "noun", "high", f"{KEEP}: sum."),
    (
        "builtin_func",
        "super",
        "надклас",
        "noun",
        "medium",
        "New. super() reaches the class above; надклас (superclass) is the native compound.",
    ),
    ("builtin_func", "vars", "змінні", "noun", "high", f"{KEEP}: variables."),
    (
        "builtin_func",
        "zip",
        "поєднати_в_кортеж",
        "verb phrase",
        "medium",
        f"{KEEP}: combine into tuples. The zipper metaphor does not carry (a zipper is блискавка), so the descriptive phrase stays.",
    ),
    # --- builtin types ------------------------------------------------------
    (
        "builtin_type",
        "bool",
        "булеве",
        "adjective",
        "medium",
        f"{KEEP}: Boolean (value), neuter.",
    ),
    (
        "builtin_type",
        "bytearray",
        "масив_байтів",
        "noun phrase",
        "high",
        f"{KEEP}: array of bytes.",
    ),
    ("builtin_type", "bytes", "байти", "noun", "high", f"{KEEP}: bytes."),
    (
        "builtin_type",
        "complex",
        "комплексне",
        "adjective",
        "high",
        f"{KEEP}: complex (number), neuter.",
    ),
    ("builtin_type", "dict", "словник", "noun", "high", f"{KEEP}: dictionary."),
    (
        "builtin_type",
        "float",
        "дійсне_число",
        "noun phrase",
        "medium",
        f"{KEEP}: real number, short and familiar from school maths.",
    ),
    (
        "builtin_type",
        "frozenset",
        "заморожена_множина",
        "noun phrase",
        "high",
        f"{KEEP}: frozen set.",
    ),
    ("builtin_type", "int", "ціле_число", "noun phrase", "high", f"{KEEP}: integer."),
    ("builtin_type", "list", "список", "noun", "high", f"{KEEP}: list."),
    (
        "builtin_type",
        "memoryview",
        "огляд_памяті",
        "noun phrase",
        "medium",
        f"{KEEP}: a view of memory. Spelled without the apostrophe of пам'ять (style guide); flag --apostrophe.",
    ),
    (
        "builtin_type",
        "object",
        "обєкт",
        "noun",
        "high",
        f"{KEEP}: object. Spelled without the apostrophe of об'єкт (style guide); flag --apostrophe.",
    ),
    (
        "builtin_type",
        "set",
        "множина",
        "noun",
        "high",
        f"{KEEP}: set (the mathematical term).",
    ),
    (
        "builtin_type",
        "str",
        "рядок",
        "noun",
        "high",
        "Showcase seed retained (CORE-1299); matches the community candidate.",
    ),
    ("builtin_type", "tuple", "кортеж", "noun", "high", f"{KEEP}: tuple."),
    ("builtin_type", "type", "тип", "noun", "high", f"{KEEP}: type."),
    # --- special constants --------------------------------------------------
    (
        "special_constant",
        "ellipsis",
        "трикрапка",
        "noun",
        "high",
        "New. The Ukrainian name of the ... mark.",
    ),
    (
        "special_constant",
        "notimplemented",
        "не_реалізовано",
        "predicate",
        "medium",
        "New. Not implemented, the impersonal -но form; distinct from ПомилкаВідсутньоїРеалізації.",
    ),
    # --- implicit parameters (reflexive, per reserved_words_prompt.md) ------
    (
        "implicit_param",
        "self",
        "себе",
        "reflexive pronoun",
        "high",
        "New. The Ukrainian reflexive pronoun (oneself); not a demonstrative (цей) and not first person (я).",
    ),
    (
        "implicit_param",
        "cls",
        "свій_клас",
        "noun phrase",
        "medium",
        "New. The reflexive possessive свій (one's own) applied to the class: the class referring to itself, not клас in general.",
    ),
    # --- exceptions ---------------------------------------------------------
    (
        "exception",
        "baseexception",
        "БазовийВиняток",
        "noun phrase",
        "high",
        "New. Base exception; Виняток is the exception root (style guide).",
    ),
    (
        "exception",
        "exception",
        "Виняток",
        "noun",
        "high",
        "New. Виняток, not the Russian-calque виключення.",
    ),
    (
        "exception",
        "generatorexit",
        "ВихідГенератора",
        "noun phrase",
        "high",
        "New. Exit of the generator.",
    ),
    (
        "exception",
        "systemexit",
        "СистемнийВихід",
        "noun phrase",
        "medium",
        "New. System exit; вихід із системи would mean log out.",
    ),
    (
        "exception",
        "keyboardinterrupt",
        "ПерериванняЗКлавіатури",
        "noun phrase",
        "high",
        "New. Interruption from the keyboard.",
    ),
    (
        "exception",
        "arithmeticerror",
        "АрифметичнаПомилка",
        "noun phrase",
        "high",
        "New. A true adjective keeps its place before the noun.",
    ),
    (
        "exception",
        "floatingpointerror",
        "ПомилкаРухомоїКоми",
        "noun phrase",
        "high",
        "New. Floating point is число з рухомою комою.",
    ),
    (
        "exception",
        "overflowerror",
        "ПомилкаПереповнення",
        "noun phrase",
        "high",
        "New. Overflow.",
    ),
    (
        "exception",
        "zerodivisionerror",
        "ПомилкаДіленняНаНуль",
        "noun phrase",
        "high",
        "New. Division by zero.",
    ),
    (
        "exception",
        "lookuperror",
        "ПомилкаПошуку",
        "noun phrase",
        "high",
        "New. Lookup, search.",
    ),
    (
        "exception",
        "indexerror",
        "ПомилкаІндексу",
        "noun phrase",
        "high",
        "New. Index, genitive -у.",
    ),
    (
        "exception",
        "keyerror",
        "ПомилкаКлюча",
        "noun phrase",
        "high",
        "New. Key; ключ takes genitive -а.",
    ),
    (
        "exception",
        "attributeerror",
        "ПомилкаАтрибута",
        "noun phrase",
        "high",
        "New. Attribute; the term takes genitive -а.",
    ),
    (
        "exception",
        "nameerror",
        "ПомилкаІмені",
        "noun phrase",
        "high",
        "New. The genitive of ім'я is імені, which needs no apostrophe.",
    ),
    (
        "exception",
        "unboundlocalerror",
        "ПомилкаНеприсвоєноїЗмінної",
        "noun phrase",
        "medium",
        "New. A local variable read before it was assigned; неприсвоєна змінна names that directly and avoids незв'язана, which would need an apostrophe.",
    ),
    (
        "exception",
        "oserror",
        "ПомилкаОС",
        "noun phrase",
        "high",
        "New. ОС is the Ukrainian abbreviation for операційна система.",
    ),
    (
        "exception",
        "blockingioerror",
        "ПомилкаБлокувальногоВведенняВиведення",
        "noun phrase",
        "medium",
        "New. Blocking input/output: введення-виведення, with the adjective in -увальний (style guide).",
    ),
    (
        "exception",
        "childprocesserror",
        "ПомилкаДочірньогоПроцесу",
        "noun phrase",
        "high",
        "New. Child process (дочірній процес).",
    ),
    (
        "exception",
        "connectionerror",
        "ПомилкаЗєднання",
        "noun phrase",
        "high",
        "New. Connection (з'єднання), spelled without the apostrophe; flag --apostrophe.",
    ),
    (
        "exception",
        "brokenpipeerror",
        "ПомилкаРозірваногоКаналу",
        "noun phrase",
        "medium",
        "New. A pipe is канал in Ukrainian OS terms; broken is розірваний.",
    ),
    (
        "exception",
        "connectionabortederror",
        "ПомилкаПерерваногоЗєднання",
        "noun phrase",
        "high",
        "New. Aborted (interrupted) connection; flag --apostrophe.",
    ),
    (
        "exception",
        "connectionrefusederror",
        "ПомилкаВідхиленогоЗєднання",
        "noun phrase",
        "high",
        "New. Refused connection; flag --apostrophe.",
    ),
    (
        "exception",
        "connectionreseterror",
        "ПомилкаСкинутогоЗєднання",
        "noun phrase",
        "high",
        "New. Reset connection; flag --apostrophe.",
    ),
    (
        "exception",
        "fileexistserror",
        "ПомилкаНаявногоФайлу",
        "noun phrase",
        "medium",
        "New. The file is already present (наявний), not the participle існуючий (style guide).",
    ),
    (
        "exception",
        "filenotfounderror",
        "ПомилкаВідсутньогоФайлу",
        "noun phrase",
        "high",
        "New. Missing (absent) file; parallel to ПомилкаНаявногоФайлу.",
    ),
    (
        "exception",
        "interruptederror",
        "ПомилкаПерерваногоВиклику",
        "noun phrase",
        "medium",
        "New. A system call interrupted by a signal.",
    ),
    (
        "exception",
        "isadirectoryerror",
        "ПомилкаЄКаталогом",
        "noun phrase",
        "medium",
        "New. Is a directory (каталог), mirroring English IsADirectory; pairs with ПомилкаНеКаталог.",
    ),
    (
        "exception",
        "notadirectoryerror",
        "ПомилкаНеКаталог",
        "noun phrase",
        "medium",
        "New. Not a directory; pairs with ПомилкаЄКаталогом.",
    ),
    (
        "exception",
        "permissionerror",
        "ПомилкаДоступу",
        "noun phrase",
        "high",
        "New. Access, as in відмовлено в доступі (permission denied).",
    ),
    (
        "exception",
        "processlookuperror",
        "ПомилкаПошукуПроцесу",
        "noun phrase",
        "high",
        "New. Process lookup.",
    ),
    (
        "exception",
        "timeouterror",
        "ПомилкаЧасуОчікування",
        "noun phrase",
        "high",
        "New. Timeout is час очікування.",
    ),
    (
        "exception",
        "importerror",
        "ПомилкаІмпорту",
        "noun phrase",
        "high",
        "New. Import.",
    ),
    (
        "exception",
        "modulenotfounderror",
        "ПомилкаВідсутньогоМодуля",
        "noun phrase",
        "high",
        "New. Missing module; parallel to ПомилкаВідсутньогоФайлу.",
    ),
    (
        "exception",
        "stopiteration",
        "ЗупинкаІтерації",
        "noun phrase",
        "high",
        "New. Not an error, so no Помилка root: the stop of an iteration.",
    ),
    (
        "exception",
        "stopasynciteration",
        "ЗупинкаАсинхронноїІтерації",
        "noun phrase",
        "high",
        "New. Asynchronous counterpart of ЗупинкаІтерації.",
    ),
    (
        "exception",
        "typeerror",
        "ПомилкаТипу",
        "noun phrase",
        "high",
        "New. Type, genitive -у.",
    ),
    (
        "exception",
        "valueerror",
        "ПомилкаЗначення",
        "noun phrase",
        "high",
        "New. Value; the example in the style guide.",
    ),
    (
        "exception",
        "unicodeerror",
        "ПомилкаЮнікоду",
        "noun phrase",
        "high",
        "New. Юнікод is the Ukrainian spelling of Unicode.",
    ),
    (
        "exception",
        "unicodedecodeerror",
        "ПомилкаДекодуванняЮнікоду",
        "noun phrase",
        "high",
        "New. Decoding.",
    ),
    (
        "exception",
        "unicodeencodeerror",
        "ПомилкаКодуванняЮнікоду",
        "noun phrase",
        "high",
        "New. Encoding.",
    ),
    (
        "exception",
        "unicodetranslateerror",
        "ПомилкаПеретворенняЮнікоду",
        "noun phrase",
        "medium",
        "New. str.translate maps characters, so перетворення (conversion), not переклад (translation between languages).",
    ),
    (
        "exception",
        "runtimeerror",
        "ПомилкаВиконання",
        "noun phrase",
        "high",
        "New. Runtime is час виконання.",
    ),
    (
        "exception",
        "notimplementederror",
        "ПомилкаВідсутньоїРеалізації",
        "noun phrase",
        "medium",
        "New. Missing implementation; distinct from the constant не_реалізовано.",
    ),
    (
        "exception",
        "recursionerror",
        "ПомилкаРекурсії",
        "noun phrase",
        "high",
        "New. Recursion.",
    ),
    (
        "exception",
        "systemerror",
        "СистемнаПомилка",
        "noun phrase",
        "high",
        "New. A true adjective keeps its place before the noun.",
    ),
    (
        "exception",
        "referenceerror",
        "ПомилкаПосилання",
        "noun phrase",
        "high",
        "New. A weak reference is слабке посилання.",
    ),
    (
        "exception",
        "assertionerror",
        "ПомилкаПеревірки",
        "noun phrase",
        "high",
        "New. Pairs with the keyword assert (перевірити).",
    ),
    (
        "exception",
        "memoryerror",
        "ПомилкаПамяті",
        "noun phrase",
        "high",
        "New. Memory (пам'ять), spelled without the apostrophe; flag --apostrophe.",
    ),
    (
        "exception",
        "buffererror",
        "ПомилкаБуфера",
        "noun phrase",
        "high",
        "New. Buffer, genitive -а.",
    ),
    (
        "exception",
        "eoferror",
        "ПомилкаКінцяФайлу",
        "noun phrase",
        "high",
        "New. EOF is end of file.",
    ),
    (
        "exception",
        "syntaxerror",
        "СинтаксичнаПомилка",
        "noun phrase",
        "high",
        "New. The established phrase синтаксична помилка.",
    ),
    (
        "exception",
        "indentationerror",
        "ПомилкаВідступу",
        "noun phrase",
        "high",
        "New. Indentation is відступ.",
    ),
    (
        "exception",
        "taberror",
        "ПомилкаТабуляції",
        "noun phrase",
        "high",
        "New. Tabulation.",
    ),
    (
        "exception",
        "environmenterror",
        "ПомилкаСередовища",
        "noun phrase",
        "high",
        "New. Environment.",
    ),
    (
        "exception",
        "ioerror",
        "ПомилкаВведенняВиведення",
        "noun phrase",
        "high",
        "New. Input/output is введення-виведення.",
    ),
    (
        "exception",
        "warning",
        "Попередження",
        "noun",
        "high",
        "New. The warning root (style guide).",
    ),
    (
        "exception",
        "userwarning",
        "ПопередженняКористувача",
        "noun phrase",
        "high",
        "New. User's warning.",
    ),
    (
        "exception",
        "deprecationwarning",
        "ПопередженняЗастарілості",
        "noun phrase",
        "high",
        "New. Deprecation is застарілість; the example in the style guide.",
    ),
    (
        "exception",
        "pendingdeprecationwarning",
        "ПопередженняМайбутньоїЗастарілості",
        "noun phrase",
        "medium",
        "New. Deprecation still to come.",
    ),
    (
        "exception",
        "syntaxwarning",
        "СинтаксичнеПопередження",
        "noun phrase",
        "high",
        "New. Pairs with СинтаксичнаПомилка.",
    ),
    (
        "exception",
        "runtimewarning",
        "ПопередженняВиконання",
        "noun phrase",
        "high",
        "New. Pairs with ПомилкаВиконання.",
    ),
    (
        "exception",
        "futurewarning",
        "ПопередженняПроМайбутнє",
        "noun phrase",
        "medium",
        "New. A warning about future behaviour.",
    ),
    (
        "exception",
        "importwarning",
        "ПопередженняІмпорту",
        "noun phrase",
        "high",
        "New. Pairs with ПомилкаІмпорту.",
    ),
    (
        "exception",
        "unicodewarning",
        "ПопередженняЮнікоду",
        "noun phrase",
        "high",
        "New. Pairs with ПомилкаЮнікоду.",
    ),
    (
        "exception",
        "byteswarning",
        "ПопередженняБайтів",
        "noun phrase",
        "high",
        "New. Bytes.",
    ),
    (
        "exception",
        "encodingwarning",
        "ПопередженняКодування",
        "noun phrase",
        "high",
        "New. Encoding.",
    ),
    (
        "exception",
        "resourcewarning",
        "ПопередженняРесурсів",
        "noun phrase",
        "high",
        "New. Resources.",
    ),
    (
        "exception",
        "exceptiongroup",
        "ГрупаВинятків",
        "noun phrase",
        "high",
        "New. Group of exceptions.",
    ),
    (
        "exception",
        "baseexceptiongroup",
        "БазоваГрупаВинятків",
        "noun phrase",
        "high",
        "New. Base group of exceptions.",
    ),
    (
        "exception",
        "pythonfinalizationerror",
        "ПомилкаЗавершенняІнтерпретатора",
        "noun phrase",
        "medium",
        "New. Raised while the interpreter shuts down; names the interpreter rather than transliterating Python.",
    ),
]

# --- decision branches --------------------------------------------------------

MODIFIER_APOSTROPHE = "ʼ"  # MODIFIER LETTER APOSTROPHE, category Lm

#: --apostrophe u02bc: the dropped spellings, restored with U+02BC.
APOSTROPHE_U02BC: dict[tuple[str, str], str] = {
    ("builtin_type", "object"): f"об{MODIFIER_APOSTROPHE}єкт",
    ("builtin_type", "memoryview"): f"огляд_пам{MODIFIER_APOSTROPHE}яті",
    ("exception", "memoryerror"): f"ПомилкаПам{MODIFIER_APOSTROPHE}яті",
    ("exception", "connectionerror"): f"ПомилкаЗ{MODIFIER_APOSTROPHE}єднання",
    (
        "exception",
        "connectionabortederror",
    ): f"ПомилкаПерерваногоЗ{MODIFIER_APOSTROPHE}єднання",
    (
        "exception",
        "connectionrefusederror",
    ): f"ПомилкаВідхиленогоЗ{MODIFIER_APOSTROPHE}єднання",
    (
        "exception",
        "connectionreseterror",
    ): f"ПомилкаСкинутогоЗ{MODIFIER_APOSTROPHE}єднання",
}

#: --verbs imperative: the second-person singular imperative of every verb value.
IMPERATIVE: dict[tuple[str, str], str] = {
    ("keyword", "assert"): "перевір",
    ("keyword", "await"): "очікуй",
    ("keyword", "break"): "перерви",
    ("keyword", "continue"): "продовж",
    ("keyword", "def"): "визнач",
    ("keyword", "del"): "видали",
    ("keyword", "except"): "перехопи",
    ("keyword", "except*"): "перехопи*",
    ("keyword", "import"): "імпортуй",
    ("keyword", "match"): "зістав",
    ("keyword", "pass"): "пропусти",
    ("keyword", "raise"): "викинь",
    ("keyword", "return"): "поверни",
    ("keyword", "try"): "спробуй",
    ("keyword", "yield"): "видай",
    ("builtin_func", "__import__"): "__імпортуй__",
    ("builtin_func", "compile"): "компілюй",
    ("builtin_func", "delattr"): "видали_атрибут",
    ("builtin_func", "enumerate"): "перерахуй",
    ("builtin_func", "eval"): "обчисли",
    ("builtin_func", "exec"): "виконай",
    ("builtin_func", "filter"): "фільтруй",
    ("builtin_func", "format"): "форматуй",
    ("builtin_func", "getattr"): "отримай_атрибут",
    ("builtin_func", "map"): "застосуй",
    ("builtin_func", "open"): "відкрий",
    ("builtin_func", "print"): "друкуй",
    ("builtin_func", "round"): "округли",
    ("builtin_func", "setattr"): "присвой_атрибут",
    ("builtin_func", "zip"): "поєднай_у_кортеж",
}

#: --def оголосити, imperative form for the combined branch.
DEF_DECLARE = {"infinitive": "оголосити", "imperative": "оголоси"}

#: --none нічого.
NONE_GENITIVE = "нічого"


def resolve(args: argparse.Namespace) -> list[tuple[str, str, str, str, str, str]]:
    """Apply the decision flags to SELECTIONS and return the chosen rows."""
    rows = []
    for category, name, value, word_type, confidence, rationale in SELECTIONS:
        key = (category, name)
        if args.apostrophe == "u02bc" and key in APOSTROPHE_U02BC:
            value = APOSTROPHE_U02BC[key]
            rationale += " Branch --apostrophe u02bc."
        if args.verbs == "imperative" and key in IMPERATIVE:
            value = IMPERATIVE[key]
            rationale += " Branch --verbs imperative."
        if key == ("keyword", "def") and args.def_ == "оголосити":
            value = DEF_DECLARE[args.verbs]
            rationale += " Branch --def оголосити."
        if key == ("keyword", "None") and args.none == "нічого":
            value = NONE_GENITIVE
            rationale += " Branch --none нічого."
        rows.append((category, name, value, word_type, confidence, rationale))
    return rows


def branch_candidates() -> list[tuple[str, str, str, str]]:
    """Every alternate value, so each branch's candidate rows always exist."""
    out = [
        (c, n, v, "Branch --apostrophe u02bc.")
        for (c, n), v in APOSTROPHE_U02BC.items()
    ]
    out += [(c, n, v, "Branch --verbs imperative.") for (c, n), v in IMPERATIVE.items()]
    out += [
        ("keyword", "def", v, f"Branch --def оголосити ({form}).")
        for form, v in DEF_DECLARE.items()
    ]
    out += [("keyword", "None", NONE_GENITIVE, "Branch --none нічого.")]
    return out


def check_target_state(wanted: dict[tuple[str, str], str]) -> list[str]:
    """Every reason the chosen values could not all be selected together.

    Mirrors the two refusals ``set_selected`` can raise (the publish gate,
    including the uk forbidden letters, and the cross-term collision guard,
    under which same-name terms such as ``type`` may share a value), so a
    run either sets everything or touches nothing.
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


def has_candidate(db: TranslationDatabase, term_id: int, value: str) -> bool:
    """True if the uk candidate pool already holds ``value`` for the term."""
    return any(
        row["translation"] == value for row in db.get_translations(term_id, LANG)
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Select the Ukrainian Python vocabulary, DB-first."
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    ap.add_argument("--apostrophe", choices=["drop", "u02bc"], default="drop")
    ap.add_argument(
        "--def", dest="def_", choices=["визначити", "оголосити"], default="визначити"
    )
    ap.add_argument("--none", choices=["ніщо", "нічого"], default="ніщо")
    ap.add_argument(
        "--verbs", choices=["infinitive", "imperative"], default="infinitive"
    )
    args = ap.parse_args()

    if not args.db.exists():
        print(
            f"no database at {args.db}; copy it in from the data home first",
            file=sys.stderr,
        )
        return 2
    db = TranslationDatabase(db_path=str(args.db))

    rows = resolve(args)
    term_ids = {}
    for category, name, *_ in rows:
        term = db.get_term_by_name(name, "python", category=category)
        if term is None or term["category"] != category:
            print(f"missing term row: {category} {name}", file=sys.stderr)
            return 1
        term_ids[(category, name)] = term["id"]

    # set_selected commits per call, so check the whole target state before
    # writing anything: a refusal mid-pass would otherwise leave terms with no
    # selection at all, or a refused value in the candidate pool.
    problems = check_target_state({(c, n): v for c, n, v, *_ in rows})
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    added = selected = unchanged = 0
    candidates = [(c, n, v, None, "medium", r) for c, n, v, r in branch_candidates()]
    for category, name, value, word_type, confidence, rationale in rows + candidates:
        term_id = term_ids[(category, name)]
        if not has_candidate(db, term_id, value):
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
    selected = len(changed)

    mode = "dry run, nothing written" if args.dry_run else "written"
    print(
        f"uk: {len(wanted)} terms; {added} candidate rows added, "
        f"{selected} selections set, {unchanged} already selected ({mode})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
