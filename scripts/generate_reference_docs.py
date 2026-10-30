"""Generate REFERENCE.md, the review template, for every registry language.

Each ``libs/i18n/language-packs/python/<code>/REFERENCE.md`` is both the
readable reference for a pack and the markdown review template for it: a
reviewer copies the file into the language-packs repository as
``reviews/<bcp47>/<bcp47>-<github-username>.md``, fills the Suggested
and Comments columns, and opens a pull request. The same bytes are mirrored to
the preview repository (``languages/<code>/REFERENCE.md``) and language-packs
(``reference/<bcp47>.md``).

By default the files are written in place, next to each pack. ``--out DIR``
writes ``DIR/<code>/REFERENCE.md`` instead, which is how
``make check-generated-reference`` regenerates into a temporary tree and diffs
against the committed files (CORE-2415). ``--languages si,ja`` restricts the
run; ``--python-version 3.11`` renders the view at that Python version instead
of the newest one.

The consistency contract (scripts/tests/test_review_template_contract.py
enforces every line):

Versions
  * Every version string in a template comes from one source: the pack version
    from that pack's ``pyproject.toml``, the Python versions from the pack's
    version files, the version a term arrives in from ``version-index.yml``.
    No literal anywhere.
  * The hidden first line, the heading and the language column header agree.
    A version bump without regeneration fails ``make check-generated``.
  * The template shows the newest Python view of the pack (its highest version
    file, merged along the ``extends:`` chain). Every row states the versions
    its word applies to, and where an earlier Python version uses a different
    word (Sinhala ZWJ forms on 3.13+), the row shows that word and its range.
    ``--python-version`` renders any other view the same way.
  * The review pin a file carries is checked by
    ``legesher_i18n.intake.review_template.check_review_pin``.

Languages
  * Every row carries a stable key, ``<yaml section>.<yaml key>``
    (``keywords.True``, ``exceptions.valueerror``), never the English display
    text; a row means the same term in every language.
  * Every language has the same sections and the same key set as English for
    the same Python view. A term a pack lacks is listed with an empty word and
    recorded in ``PackView.lacking``; it is never filled with English.
  * Templates exist for exactly the registry's languages.
  * Values are written byte-identical to the pack (NFC as stored, joiners
    kept). RTL terms are single right-to-left runs, so they render in the
    same order in a table cell as on a source line.

The example program
  * Its keywords, builtins and exceptions are the pack's words for the same
    view, so they change with the pack. Its identifiers come from
    ``EXAMPLE_TEXT``, are NFKC-normalised, and are never a word of that
    pack, compared after NFKC normalisation as Python compares names: with
    the pack words reversed to English the program compiles, and no variable
    shadows a keyword, builtin or exception. The contract test checks both.

Dialects and locale identity
  * The review folder and file name follow the registry's BCP 47 tag; the
    hidden line carries both ``code`` and ``bcp47``, so a parser never guesses.
  * A dialect pack (``es-MX`` beside ``es``) marks every row it inherits from
    its base language (``TermRow.inherited_from``); its own rows are unmarked.

Regeneration is per pack: a template's bytes depend only on its own pack's
inputs and ``FORMAT_VERSION``. Nothing repo-wide (no commit SHA, no date, no
language count) goes in, so changing one pack rewrites one template.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

from legesher_i18n.intake.review_template import (
    FORMAT_VERSION,
    TemplateMetadata,
    render_metadata_line,
    review_file_name,
    review_folder,
)

# Paths
ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "libs" / "i18n"
PACKS_DIR = I18N_DIR / "language-packs" / "python"
LANGUAGES_JSON = I18N_DIR / "legesher_i18n" / "languages.json"
VERSION_INDEX = PACKS_DIR / "version-index.yml"
SECTIONS = ("keywords", "builtins", "exceptions", "implicit_params")
INDEX_LISTS = {
    "keywords": "added_keywords",
    "builtins": "added_builtins",
    "exceptions": "added_exceptions",
}
LANGUAGE_PACKS_URL = "https://github.com/legesher/language-packs"
# Script (writing system) for each language
# Based on Aya/Cohere documentation and Unicode CLDR
LANGUAGE_SCRIPTS = {
    "am": "Ge'ez",
    "ar": "Arabic",
    "bn": "Bengali",
    "bs": "Latin",
    "ca": "Latin",
    "cs": "Latin",
    "cy": "Latin",
    "da": "Latin",
    "de": "Latin",
    "el": "Greek",
    "en": "Latin",
    "es": "Latin",
    "fa": "Arabic",
    "fi": "Latin",
    "fr": "Latin",
    "ga": "Latin",
    "gd": "Latin",
    "gl": "Latin",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Devanagari",
    "hr": "Latin",
    "hu": "Latin",
    "id": "Latin",
    "it": "Latin",
    "ja": "Japanese (Kanji, Hiragana, Katakana)",
    "kn": "Kannada",
    "ko": "Hangul",
    "lv": "Latin",
    "mk": "Cyrillic",
    "ml": "Malayalam",
    "mn": "Cyrillic",
    "ms": "Latin",
    "my": "Myanmar",
    "ne": "Devanagari",
    "nl": "Latin",
    "no": "Latin",
    "pl": "Latin",
    "pt": "Latin",
    "ro": "Latin",
    "ru": "Cyrillic",
    "si": "Sinhala",
    "sr": "Cyrillic",
    "su": "Latin",
    "sv": "Latin",
    "sw": "Latin",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Latin",
    "tr": "Latin",
    "uk": "Cyrillic",
    "ur": "Arabic",
    "uz": "Latin",
    "vi": "Latin",
    "xh": "Latin",
    "zh": "Simplified Chinese (Han)",
}

# Localized example text for each language
# Keys: factorial, main, numbers, num, result, count, error_var,
#       docstring, comment_example, comment_while, comment_try,
#       msg_negative, msg_count, msg_error, msg_done
# The first seven are identifiers in the example program. An identifier must
# not be a word of that language's pack (a keyword there breaks the program,
# a builtin or exception name shadows it); the contract test refuses one.
EXAMPLE_TEXT = {
    "am": {
        "factorial": "ፋክቶሪያል",
        "main": "ዋና",
        "numbers": "ቁጥሮች",
        "num": "ቁጥር",
        "result": "ውጤት",
        "count": "ቆጠራ",
        "error_var": "ስህተት",
        "docstring": "የን ፋክቶሪያል ያስላል።",
        "comment_example": "ምሳሌ፡ ከስህተት አያያዝ ጋር ፋክቶሪያል ተግባር",
        "comment_while": "የእስከ ዙር ማሳያ",
        "comment_try": "የሞክር/ከቀረ ማሳያ",
        "msg_negative": "አሉታዊ ቁጥሮች አይፈቀዱም",
        "msg_count": "ቆጠራ:",
        "msg_error": "ስህተት:",
        "msg_done": "ተጠናቋል!",
    },
    "ar": {
        "factorial": "المضروب",
        "main": "الرئيسية",
        "numbers": "الأرقام",
        "num": "رقم",
        "result": "النتيجة",
        "count": "العداد",
        "error_var": "الخطأ",
        "docstring": "حساب مضروب العدد ن.",
        "comment_example": "مثال: دالة المضروب مع معالجة الأخطاء",
        "comment_while": "توضيح حلقة while",
        "comment_try": "توضيح try/except",
        "msg_negative": "الأرقام السالبة غير مسموحة",
        "msg_count": "العداد:",
        "msg_error": "خطأ:",
        "msg_done": "انتهى!",
    },
    "bn": {
        "factorial": "গুণনফল",
        "main": "প্রধান",
        "numbers": "সংখ্যাসমূহ",
        "num": "সংখ্যা",
        "result": "ফলাফল",
        "count": "গণক",
        "error_var": "ত্রুটি",
        "docstring": "n এর গুণনফল গণনা করুন।",
        "comment_example": "উদাহরণ: ত্রুটি পরিচালনাসহ গুণনফল ফাংশন",
        "comment_while": "while লুপ প্রদর্শন",
        "comment_try": "try/except প্রদর্শন",
        "msg_negative": "ঋণাত্মক সংখ্যা অনুমোদিত নয়",
        "msg_count": "গণনা:",
        "msg_error": "ত্রুটি:",
        "msg_done": "সম্পন্ন!",
    },
    "bs": {
        "factorial": "faktorijel",
        "main": "glavni",
        "numbers": "brojevi",
        "num": "broj",
        "result": "rezultat",
        "count": "brojac",
        "error_var": "greska",
        "docstring": "Izračunaj faktorijel broja n.",
        "comment_example": "Primjer: Funkcija faktorijela s obradom grešaka",
        "comment_while": "Demonstracija while petlje",
        "comment_try": "Demonstracija try/except",
        "msg_negative": "Negativni brojevi nisu dozvoljeni",
        "msg_count": "Brojač:",
        "msg_error": "Greška:",
        "msg_done": "Gotovo!",
    },
    "ca": {
        "factorial": "factorial",
        "main": "principal",
        "numbers": "nombres",
        "num": "nombre",
        "result": "resultat",
        "count": "comptador",
        "error_var": "error",
        "docstring": "Calcula el factorial de n.",
        "comment_example": "Exemple: Funció factorial amb gestió d'errors",
        "comment_while": "Demostració del bucle while",
        "comment_try": "Demostració de try/except",
        "msg_negative": "Els nombres negatius no estan permesos",
        "msg_count": "Comptador:",
        "msg_error": "Error:",
        "msg_done": "Fet!",
    },
    "cs": {
        "factorial": "faktorial",
        "main": "hlavni",
        "numbers": "cisla",
        "num": "cislo",
        "result": "vysledek",
        "count": "pocitadlo",
        "error_var": "chyba",
        "docstring": "Vypočítá faktoriál čísla n.",
        "comment_example": "Příklad: Funkce faktoriálu s ošetřením chyb",
        "comment_while": "Ukázka cyklu while",
        "comment_try": "Ukázka try/except",
        "msg_negative": "Záporná čísla nejsou povolena",
        "msg_count": "Počítadlo:",
        "msg_error": "Chyba:",
        "msg_done": "Hotovo!",
    },
    "cy": {
        "factorial": "ffactorial",
        "main": "prif",
        "numbers": "rhifau",
        "num": "rhif",
        "result": "canlyniad",
        "count": "cyfrif",
        "error_var": "gwall",
        "docstring": "Cyfrifo ffactorial n.",
        "comment_example": "Enghraifft: Ffwythiant ffactorial gyda thrin gwallau",
        "comment_while": "Arddangos dolen while",
        "comment_try": "Arddangos try/except",
        "msg_negative": "Ni chaniateir rhifau negatif",
        "msg_count": "Cyfrif:",
        "msg_error": "Gwall:",
        "msg_done": "Gorffen!",
    },
    "da": {
        "factorial": "fakultet",
        "main": "hoved",
        "numbers": "tal",
        "num": "nummer",
        "result": "resultat",
        "count": "tæller",
        "error_var": "fejl",
        "docstring": "Beregn fakultet af n.",
        "comment_example": "Eksempel: Fakultetsfunktion med fejlhåndtering",
        "comment_while": "Demonstrer while-løkke",
        "comment_try": "Demonstrer try/except",
        "msg_negative": "Negative tal er ikke tilladt",
        "msg_count": "Tæller:",
        "msg_error": "Fejl:",
        "msg_done": "Færdig!",
    },
    "de": {
        "factorial": "fakultaet",
        "main": "haupt",
        "numbers": "zahlen",
        "num": "zahl",
        "result": "ergebnis",
        "count": "zaehler",
        "error_var": "fehler",
        "docstring": "Berechne die Fakultät von n.",
        "comment_example": "Beispiel: Fakultätsfunktion mit Fehlerbehandlung",
        "comment_while": "Demonstriere While-Schleife",
        "comment_try": "Demonstriere Try/Except",
        "msg_negative": "Negative Zahlen sind nicht erlaubt",
        "msg_count": "Zähler:",
        "msg_error": "Fehler:",
        "msg_done": "Fertig!",
    },
    "el": {
        "factorial": "παραγοντικό",
        "main": "κύριο",
        "numbers": "αριθμοί",
        "num": "αριθμός",
        "result": "τιμή",
        "count": "μετρητής",
        "error_var": "σφάλμα",
        "docstring": "Υπολογισμός παραγοντικού του n.",
        "comment_example": "Παράδειγμα: Συνάρτηση παραγοντικού με χειρισμό σφαλμάτων",
        "comment_while": "Επίδειξη βρόχου while",
        "comment_try": "Επίδειξη try/except",
        "msg_negative": "Οι αρνητικοί αριθμοί δεν επιτρέπονται",
        "msg_count": "Μετρητής:",
        "msg_error": "Σφάλμα:",
        "msg_done": "Ολοκληρώθηκε!",
    },
    "en": {
        "factorial": "factorial",
        "main": "main",
        "numbers": "numbers",
        "num": "num",
        "result": "result",
        "count": "count",
        "error_var": "error",
        "docstring": "Calculate the factorial of n.",
        "comment_example": "Example: factorial function with error handling",
        "comment_while": "Demonstrate a while loop",
        "comment_try": "Demonstrate try/except",
        "msg_negative": "Negative numbers are not allowed",
        "msg_count": "Count:",
        "msg_error": "Error:",
        "msg_done": "Done!",
    },
    "es": {
        "factorial": "factorial",
        "main": "principal",
        "numbers": "numeros",
        "num": "numero",
        "result": "resultado",
        "count": "contador",
        "error_var": "error",
        "docstring": "Calcular el factorial de n.",
        "comment_example": "Ejemplo: Función factorial con manejo de errores",
        "comment_while": "Demostrar bucle while",
        "comment_try": "Demostrar try/except",
        "msg_negative": "Los números negativos no están permitidos",
        "msg_count": "Contador:",
        "msg_error": "Error:",
        "msg_done": "¡Listo!",
    },
    "fa": {
        "factorial": "فاکتوریل",
        "main": "اصلی",
        "numbers": "اعداد",
        "num": "عدد",
        "result": "نتیجه",
        "count": "شمارنده",
        "error_var": "خطا",
        "docstring": "محاسبه فاکتوریل n.",
        "comment_example": "مثال: تابع فاکتوریل با مدیریت خطا",
        "comment_while": "نمایش حلقه while",
        "comment_try": "نمایش try/except",
        "msg_negative": "اعداد منفی مجاز نیستند",
        "msg_count": "شمارنده:",
        "msg_error": "خطا:",
        "msg_done": "تمام!",
    },
    "fi": {
        "factorial": "kertoma",
        "main": "paa",
        "numbers": "numerot",
        "num": "numero",
        "result": "tulos",
        "count": "laskuri",
        "error_var": "virhe",
        "docstring": "Laske n:n kertoma.",
        "comment_example": "Esimerkki: Kertomafunktio virheenkäsittelyllä",
        "comment_while": "Esittele while-silmukka",
        "comment_try": "Esittele try/except",
        "msg_negative": "Negatiiviset luvut eivät ole sallittuja",
        "msg_count": "Laskuri:",
        "msg_error": "Virhe:",
        "msg_done": "Valmis!",
    },
    "fr": {
        "factorial": "factorielle",
        "main": "principal",
        "numbers": "nombres",
        "num": "nombre",
        "result": "resultat",
        "count": "compteur",
        "error_var": "erreur",
        "docstring": "Calculer la factorielle de n.",
        "comment_example": "Exemple: Fonction factorielle avec gestion des erreurs",
        "comment_while": "Démontrer la boucle while",
        "comment_try": "Démontrer try/except",
        "msg_negative": "Les nombres négatifs ne sont pas autorisés",
        "msg_count": "Compteur:",
        "msg_error": "Erreur:",
        "msg_done": "Terminé!",
    },
    "ga": {
        "factorial": "fachtóireach",
        "main": "príomh",
        "numbers": "uimhreacha",
        "num": "uimhir",
        "result": "toradh",
        "count": "áireamh",
        "error_var": "earráid",
        "docstring": "Ríomh fachtóireach n.",
        "comment_example": "Sampla: Feidhm fachtóirigh le láimhseáil earráidí",
        "comment_while": "Léiriú lúb while",
        "comment_try": "Léiriú try/except",
        "msg_negative": "Ní cheadaítear uimhreacha diúltacha",
        "msg_count": "Áireamh:",
        "msg_error": "Earráid:",
        "msg_done": "Críochnaithe!",
    },
    "gd": {
        "factorial": "factarail",
        "main": "priomh",
        "numbers": "aireamhan",
        "num": "aireamh",
        "result": "toradh",
        "count": "cunntair",
        "error_var": "mearachd",
        "docstring": "Obraich a-mach factarail n.",
        "comment_example": "Eisimpleir: Gnìomh factarail le làimhseachadh mhearachdan",
        "comment_while": "Taisbeanadh lùb while",
        "comment_try": "Taisbeanadh try/except",
        "msg_negative": "Chan eil àireamhan àicheil ceadaichte",
        "msg_count": "Cunntair:",
        "msg_error": "Mearachd:",
        "msg_done": "Deiseil!",
    },
    "gl": {
        "factorial": "factorial",
        "main": "principal",
        "numbers": "numeros",
        "num": "numero",
        "result": "resultado",
        "count": "contador",
        "error_var": "erro",
        "docstring": "Calcular o factorial de n.",
        "comment_example": "Exemplo: Función factorial con xestión de erros",
        "comment_while": "Demostración do bucle while",
        "comment_try": "Demostración de try/except",
        "msg_negative": "Os números negativos non están permitidos",
        "msg_count": "Contador:",
        "msg_error": "Erro:",
        "msg_done": "Feito!",
    },
    "gu": {
        "factorial": "ક્રમગુણિત",
        "main": "મુખ્ય",
        "numbers": "સંખ્યાઓ",
        "num": "સંખ્યા",
        "result": "પરિણામ",
        "count": "ગણતરી",
        "error_var": "ભૂલ",
        "docstring": "n નું ક્રમગુણિત ગણો.",
        "comment_example": "ઉદાહરણ: ભૂલ વ્યવસ્થાપન સાથે ક્રમગુણિત ફંક્શન",
        "comment_while": "while લૂપ દર્શાવો",
        "comment_try": "try/except દર્શાવો",
        "msg_negative": "ઋણ સંખ્યાઓ મંજૂર નથી",
        "msg_count": "ગણતરી:",
        "msg_error": "ભૂલ:",
        "msg_done": "પૂર્ણ!",
    },
    "he": {
        "factorial": "עצרת",
        "main": "ראשי",
        "numbers": "מספרים",
        "num": "מספר",
        "result": "תוצאה",
        "count": "מונה",
        "error_var": "שגיאה",
        "docstring": "חישוב עצרת של n.",
        "comment_example": "דוגמה: פונקציית עצרת עם טיפול בשגיאות",
        "comment_while": "הדגמת לולאת while",
        "comment_try": "הדגמת try/except",
        "msg_negative": "מספרים שליליים אינם מותרים",
        "msg_count": "מונה:",
        "msg_error": "שגיאה:",
        "msg_done": "סיום!",
    },
    "hi": {
        "factorial": "क्रमगुणित",
        "main": "मुख्य",
        "numbers": "संख्याएं",
        "num": "संख्या",
        "result": "परिणाम",
        "count": "गिनती",
        "error_var": "ग़लती",
        "docstring": "n का क्रमगुणित गणना करें।",
        "comment_example": "उदाहरण: त्रुटि प्रबंधन के साथ क्रमगुणित फ़ंक्शन",
        "comment_while": "while लूप प्रदर्शन",
        "comment_try": "try/except प्रदर्शन",
        "msg_negative": "ऋणात्मक संख्याएं अनुमत नहीं हैं",
        "msg_count": "गिनती:",
        "msg_error": "त्रुटि:",
        "msg_done": "पूर्ण!",
    },
    "hr": {
        "factorial": "faktorijel",
        "main": "glavni",
        "numbers": "brojevi",
        "num": "broj",
        "result": "rezultat",
        "count": "brojac",
        "error_var": "greska",
        "docstring": "Izračunaj faktorijel broja n.",
        "comment_example": "Primjer: Funkcija faktorijela s obradom pogrešaka",
        "comment_while": "Demonstracija while petlje",
        "comment_try": "Demonstracija try/except",
        "msg_negative": "Negativni brojevi nisu dopušteni",
        "msg_count": "Brojač:",
        "msg_error": "Pogreška:",
        "msg_done": "Gotovo!",
    },
    "hu": {
        "factorial": "faktorialis",
        "main": "fo",
        "numbers": "szamok",
        "num": "szam",
        "result": "eredmeny",
        "count": "szamlalo",
        "error_var": "hibauzenet",
        "docstring": "Számítsd ki n faktoriálisát.",
        "comment_example": "Példa: Faktoriális függvény hibakezeléssel",
        "comment_while": "While ciklus bemutatása",
        "comment_try": "Try/except bemutatása",
        "msg_negative": "Negatív számok nem engedélyezettek",
        "msg_count": "Számláló:",
        "msg_error": "Hiba:",
        "msg_done": "Kész!",
    },
    "id": {
        "factorial": "faktorial",
        "main": "utama",
        "numbers": "angka",
        "num": "nomor",
        "result": "hasil",
        "count": "hitungan",
        "error_var": "kesalahan",
        "docstring": "Hitung faktorial dari n.",
        "comment_example": "Contoh: Fungsi faktorial dengan penanganan kesalahan",
        "comment_while": "Demonstrasi perulangan while",
        "comment_try": "Demonstrasi try/except",
        "msg_negative": "Angka negatif tidak diperbolehkan",
        "msg_count": "Hitungan:",
        "msg_error": "Kesalahan:",
        "msg_done": "Selesai!",
    },
    "it": {
        "factorial": "fattoriale",
        "main": "principale",
        "numbers": "numeri",
        "num": "numero",
        "result": "risultato",
        "count": "contatore",
        "error_var": "errore",
        "docstring": "Calcola il fattoriale di n.",
        "comment_example": "Esempio: Funzione fattoriale con gestione degli errori",
        "comment_while": "Dimostra il ciclo while",
        "comment_try": "Dimostra try/except",
        "msg_negative": "I numeri negativi non sono consentiti",
        "msg_count": "Contatore:",
        "msg_error": "Errore:",
        "msg_done": "Fatto!",
    },
    "ja": {
        "factorial": "階乗",
        "main": "メイン",
        "numbers": "数値リスト",
        "num": "数値",
        "result": "結果",
        "count": "カウント",
        "error_var": "エラー",
        "docstring": "nの階乗を計算する。",
        "comment_example": "例: エラー処理付き階乗関数",
        "comment_while": "whileループのデモ",
        "comment_try": "try/exceptのデモ",
        "msg_negative": "負の数は許可されていません",
        "msg_count": "カウント:",
        "msg_error": "エラー:",
        "msg_done": "完了!",
    },
    "kn": {
        "factorial": "ಕ್ರಮಗುಣಿತ",
        "main": "ಮುಖ್ಯ",
        "numbers": "ಸಂಖ್ಯೆಗಳು",
        "num": "ಸಂಖ್ಯೆ",
        "result": "ಫಲಿತಾಂಶ",
        "count": "ಎಣಿಕೆ",
        "error_var": "ದೋಷ",
        "docstring": "n ನ ಕ್ರಮಗುಣಿತವನ್ನು ಲೆಕ್ಕಹಾಕಿ.",
        "comment_example": "ಉದಾಹರಣೆ: ದೋಷ ನಿರ್ವಹಣೆಯೊಂದಿಗೆ ಕ್ರಮಗುಣಿತ ಕಾರ್ಯ",
        "comment_while": "while ಲೂಪ್ ಪ್ರದರ್ಶನ",
        "comment_try": "try/except ಪ್ರದರ್ಶನ",
        "msg_negative": "ಋಣ ಸಂಖ್ಯೆಗಳು ಅನುಮತಿಸಲಾಗಿಲ್ಲ",
        "msg_count": "ಎಣಿಕೆ:",
        "msg_error": "ದೋಷ:",
        "msg_done": "ಮುಗಿಯಿತು!",
    },
    "ko": {
        "factorial": "팩토리얼",
        "main": "메인",
        "numbers": "숫자들",
        "num": "숫자",
        "result": "결과",
        "count": "카운트",
        "error_var": "오류_내용",
        "docstring": "n의 팩토리얼을 계산합니다.",
        "comment_example": "예제: 오류 처리가 있는 팩토리얼 함수",
        "comment_while": "while 루프 시연",
        "comment_try": "try/except 시연",
        "msg_negative": "음수는 허용되지 않습니다",
        "msg_count": "카운트:",
        "msg_error": "오류:",
        "msg_done": "완료!",
    },
    "lv": {
        "factorial": "faktorials",
        "main": "galvenais",
        "numbers": "skaitli",
        "num": "skaitlis",
        "result": "rezultats",
        "count": "skaititajs",
        "error_var": "kluda",
        "docstring": "Aprēķināt n faktoriālu.",
        "comment_example": "Piemērs: Faktoriāla funkcija ar kļūdu apstrādi",
        "comment_while": "while cilpas demonstrācija",
        "comment_try": "try/except demonstrācija",
        "msg_negative": "Negatīvi skaitļi nav atļauti",
        "msg_count": "Skaitītājs:",
        "msg_error": "Kļūda:",
        "msg_done": "Gatavs!",
    },
    "mk": {
        "factorial": "факторијал",
        "main": "главна",
        "numbers": "броеви",
        "num": "број",
        "result": "резултат",
        "count": "бројач",
        "error_var": "грешка",
        "docstring": "Пресметај факторијал на n.",
        "comment_example": "Пример: Функција за факторијал со обработка на грешки",
        "comment_while": "Демонстрација на while циклус",
        "comment_try": "Демонстрација на try/except",
        "msg_negative": "Негативни броеви не се дозволени",
        "msg_count": "Бројач:",
        "msg_error": "Грешка:",
        "msg_done": "Готово!",
    },
    "ml": {
        "factorial": "ഫാക്ടോറിയൽ",
        "main": "പ്രധാന",
        "numbers": "സംഖ്യകൾ",
        "num": "സംഖ്യ",
        "result": "ഫലം",
        "count": "എണ്ണം",
        "error_var": "പിശക്",
        "docstring": "n ന്റെ ഫാക്ടോറിയൽ കണക്കാക്കുക.",
        "comment_example": "ഉദാഹരണം: പിശക് കൈകാര്യം ചെയ്യലോടെ ഫാക്ടോറിയൽ ഫങ്ഷൻ",
        "comment_while": "while ലൂപ്പ് പ്രദർശനം",
        "comment_try": "try/except പ്രദർശനം",
        "msg_negative": "ഋണ സംഖ്യകൾ അനുവദനീയമല്ല",
        "msg_count": "എണ്ണം:",
        "msg_error": "പിശക്:",
        "msg_done": "പൂർത്തിയായി!",
    },
    "mn": {
        "factorial": "факториал",
        "main": "гол",
        "numbers": "тоонууд",
        "num": "тоо",
        "result": "үр_дүн",
        "count": "тоолуур",
        "error_var": "алдаа",
        "docstring": "n-ийн факториалыг тооцоол.",
        "comment_example": "Жишээ: Алдааг зохицуулсан факториал функц",
        "comment_while": "while давталтын жишээ",
        "comment_try": "try/except жишээ",
        "msg_negative": "Сөрөг тоо зөвшөөрөгдөхгүй",
        "msg_count": "Тоолуур:",
        "msg_error": "Алдаа:",
        "msg_done": "Дууссан!",
    },
    "ms": {
        "factorial": "faktorial",
        "main": "utama",
        "numbers": "nombor",
        "num": "nom",
        "result": "hasil",
        "count": "kiraan",
        "error_var": "ralat",
        "docstring": "Kira faktorial n.",
        "comment_example": "Contoh: Fungsi faktorial dengan pengendalian ralat",
        "comment_while": "Tunjukkan gelung while",
        "comment_try": "Tunjukkan try/except",
        "msg_negative": "Nombor negatif tidak dibenarkan",
        "msg_count": "Kiraan:",
        "msg_error": "Ralat:",
        "msg_done": "Selesai!",
    },
    "my": {
        "factorial": "အချက်အလက်",
        "main": "အဓိက",
        "numbers": "ဂဏန်းများ",
        "num": "ဂဏန်း",
        "result": "ရလဒ်",
        "count": "အရေအတွက်",
        "error_var": "အမှား",
        "docstring": "n ၏ ဖက်တိုရီယယ်ကို တွက်ချက်ပါ။",
        "comment_example": "ဥပမာ: အမှားကိုင်တွယ်မှုပါ ဖက်တိုရီယယ် လုပ်ဆောင်ချက်",
        "comment_while": "while ကွင်းဆက် သရုပ်ပြ",
        "comment_try": "try/except သရုပ်ပြ",
        "msg_negative": "အနှုတ်ဂဏန်းများ ခွင့်မပြုပါ",
        "msg_count": "ရေတွက်:",
        "msg_error": "အမှား:",
        "msg_done": "ပြီးပါပြီ!",
    },
    "ne": {
        "factorial": "क्रमगुणन",
        "main": "मुख्य",
        "numbers": "संख्याहरू",
        "num": "संख्या",
        "result": "नतिजा",
        "count": "गणना",
        "error_var": "त्रुटि",
        "docstring": "n को क्रमगुणन गणना गर्नुहोस्।",
        "comment_example": "उदाहरण: त्रुटि व्यवस्थापनसहित क्रमगुणन",
        "comment_while": "while लुपको प्रदर्शन",
        "comment_try": "try/except को प्रदर्शन",
        "msg_negative": "ऋणात्मक संख्याहरूको अनुमति छैन",
        "msg_count": "गणना:",
        "msg_error": "त्रुटि:",
        "msg_done": "सम्पन्न!",
    },
    "nl": {
        "factorial": "faculteit",
        "main": "hoofd",
        "numbers": "getallen",
        "num": "getal",
        "result": "resultaat",
        "count": "teller",
        "error_var": "foutmelding",
        "docstring": "Bereken de faculteit van n.",
        "comment_example": "Voorbeeld: Faculteitsfunctie met foutafhandeling",
        "comment_while": "Demonstreer while-lus",
        "comment_try": "Demonstreer try/except",
        "msg_negative": "Negatieve getallen zijn niet toegestaan",
        "msg_count": "Teller:",
        "msg_error": "Fout:",
        "msg_done": "Klaar!",
    },
    "no": {
        "factorial": "fakultet",
        "main": "hoved",
        "numbers": "tall",
        "num": "nummer",
        "result": "resultat",
        "count": "teller",
        "error_var": "feilmelding",
        "docstring": "Beregn fakultet av n.",
        "comment_example": "Eksempel: Fakultetsfunksjon med feilhåndtering",
        "comment_while": "Demonstrer while-løkke",
        "comment_try": "Demonstrer try/except",
        "msg_negative": "Negative tall er ikke tillatt",
        "msg_count": "Teller:",
        "msg_error": "Feil:",
        "msg_done": "Ferdig!",
    },
    "pl": {
        "factorial": "silnia",
        "main": "glowna",
        "numbers": "liczby",
        "num": "liczba",
        "result": "wynik",
        "count": "licznik",
        "error_var": "blad",
        "docstring": "Oblicz silnię liczby n.",
        "comment_example": "Przykład: Funkcja silni z obsługą błędów",
        "comment_while": "Demonstracja pętli while",
        "comment_try": "Demonstracja try/except",
        "msg_negative": "Liczby ujemne nie są dozwolone",
        "msg_count": "Licznik:",
        "msg_error": "Błąd:",
        "msg_done": "Gotowe!",
    },
    "pt": {
        "factorial": "fatorial",
        "main": "principal",
        "numbers": "numeros",
        "num": "numero",
        "result": "resultado",
        "count": "contador",
        "error_var": "erro",
        "docstring": "Calcular o fatorial de n.",
        "comment_example": "Exemplo: Função fatorial com tratamento de erros",
        "comment_while": "Demonstrar laço while",
        "comment_try": "Demonstrar try/except",
        "msg_negative": "Números negativos não são permitidos",
        "msg_count": "Contador:",
        "msg_error": "Erro:",
        "msg_done": "Pronto!",
    },
    "ro": {
        "factorial": "factorial",
        "main": "principal",
        "numbers": "numere",
        "num": "numar",
        "result": "rezultat",
        "count": "contor",
        "error_var": "eroare",
        "docstring": "Calculează factorialul lui n.",
        "comment_example": "Exemplu: Funcție factorial cu tratarea erorilor",
        "comment_while": "Demonstrare buclă while",
        "comment_try": "Demonstrare try/except",
        "msg_negative": "Numerele negative nu sunt permise",
        "msg_count": "Contor:",
        "msg_error": "Eroare:",
        "msg_done": "Gata!",
    },
    "ru": {
        "factorial": "факториал",
        "main": "главная",
        "numbers": "числа",
        "num": "число",
        "result": "результат",
        "count": "счетчик",
        "error_var": "ошибка",
        "docstring": "Вычислить факториал числа n.",
        "comment_example": "Пример: Функция факториала с обработкой ошибок",
        "comment_while": "Демонстрация цикла while",
        "comment_try": "Демонстрация try/except",
        "msg_negative": "Отрицательные числа не допускаются",
        "msg_count": "Счетчик:",
        "msg_error": "Ошибка:",
        "msg_done": "Готово!",
    },
    "si": {
        "factorial": "සාධක",
        "main": "ප්‍රධාන",
        "numbers": "සංඛ්‍යා",
        "num": "අංකය",
        "result": "ප්‍රතිඵලය",
        "count": "ගණනය",
        "error_var": "දෝෂය",
        "docstring": "අංකයක සාධකය ගණනය කරන්න.",
        "comment_example": "උදාහරණය: දෝෂ හැසිරවීම සමඟ සාධක ශ්‍රිතය",
        "comment_while": "අතරතුර ලූපය නිරූපණය",
        "comment_try": "උත්සාහ/හැර නිරූපණය",
        "msg_negative": "සෘණ සංඛ්‍යා අනුමත නැත",
        "msg_count": "ගණනය:",
        "msg_error": "දෝෂය:",
        "msg_done": "අවසන්!",
    },
    "sr": {
        "factorial": "факторијел",
        "main": "главна",
        "numbers": "бројеви",
        "num": "број",
        "result": "резултат",
        "count": "бројач",
        "error_var": "грешка",
        "docstring": "Израчунај факторијел броја n.",
        "comment_example": "Пример: Функција факторијела са обрадом грешака",
        "comment_while": "Демонстрација while петље",
        "comment_try": "Демонстрација try/except",
        "msg_negative": "Негативни бројеви нису дозвољени",
        "msg_count": "Бројач:",
        "msg_error": "Грешка:",
        "msg_done": "Готово!",
    },
    "su": {
        "factorial": "faktorial",
        "main": "utama",
        "numbers": "angka",
        "num": "wilangan",
        "result": "hasil",
        "count": "cacah",
        "error_var": "kasalahan",
        "docstring": "Itung faktorial tina n.",
        "comment_example": "Conto: Fungsi faktorial kalawan penanganan kasalahan",
        "comment_while": "Demonstrasi loop while",
        "comment_try": "Demonstrasi try/except",
        "msg_negative": "Wilangan negatif teu diwenangkeun",
        "msg_count": "Cacah:",
        "msg_error": "Kasalahan:",
        "msg_done": "Rengse!",
    },
    "sv": {
        "factorial": "fakultet",
        "main": "huvud",
        "numbers": "tal",
        "num": "nummer",
        "result": "resultat",
        "count": "rakna",
        "error_var": "felmeddelande",
        "docstring": "Beräkna fakulteten av n.",
        "comment_example": "Exempel: Fakultetsfunktion med felhantering",
        "comment_while": "Demonstrera while-loop",
        "comment_try": "Demonstrera try/except",
        "msg_negative": "Negativa tal är inte tillåtna",
        "msg_count": "Räknare:",
        "msg_error": "Fel:",
        "msg_done": "Klart!",
    },
    "sw": {
        "factorial": "faktoria",
        "main": "kuu",
        "numbers": "namba_zote",
        "num": "namba",
        "result": "matokeo",
        "count": "kihesabu",
        "error_var": "hitilafu",
        "docstring": "Kokotoa faktoria ya namba n.",
        "comment_example": "Mfano: faktoria pamoja na kushughulikia hitilafu",
        "comment_while": "Onyesho la kitanzi cha while",
        "comment_try": "Onyesho la try/except",
        "msg_negative": "Namba hasi haziruhusiwi",
        "msg_count": "Hesabu:",
        "msg_error": "Hitilafu:",
        "msg_done": "Imekamilika!",
    },
    "te": {
        "factorial": "కారణాంకం",
        "main": "ప్రధాన",
        "numbers": "సంఖ్యలు",
        "num": "సంఖ్య",
        "result": "ఫలితం",
        "count": "లెక్కింపు",
        "error_var": "లోపం",
        "docstring": "n యొక్క కారణాంకాన్ని లెక్కించండి.",
        "comment_example": "ఉదాహరణ: లోపం నిర్వహణతో కారణాంకం ఫంక్షన్",
        "comment_while": "while లూప్ ప్రదర్శన",
        "comment_try": "try/except ప్రదర్శన",
        "msg_negative": "ప్రతికూల సంఖ్యలు అనుమతించబడవు",
        "msg_count": "లెక్కింపు:",
        "msg_error": "లోపం:",
        "msg_done": "పూర్తయింది!",
    },
    "th": {
        "factorial": "แฟกทอเรียล",
        "main": "หลัก",
        "numbers": "ตัวเลข",
        "num": "จำนวน",
        "result": "ผลลัพธ์",
        "count": "นับ",
        "error_var": "ข้อผิดพลาด",
        "docstring": "คำนวณแฟกทอเรียลของ n",
        "comment_example": "ตัวอย่าง: ฟังก์ชันแฟกทอเรียลพร้อมการจัดการข้อผิดพลาด",
        "comment_while": "สาธิตลูป while",
        "comment_try": "สาธิต try/except",
        "msg_negative": "ไม่อนุญาตให้ใช้ตัวเลขติดลบ",
        "msg_count": "นับ:",
        "msg_error": "ข้อผิดพลาด:",
        "msg_done": "เสร็จสิ้น!",
    },
    "tl": {
        "factorial": "paktoryal",
        "main": "pangunahin",
        "numbers": "mga_numero",
        "num": "numero",
        "result": "resulta",
        "count": "panbilang",
        "error_var": "pagkakamali",
        "docstring": "Kalkulahin ang paktoryal ng n.",
        "comment_example": "Halimbawa: paktoryal na may paghawak ng pagkakamali",
        "comment_while": "Pagpapakita ng while loop",
        "comment_try": "Pagpapakita ng try/except",
        "msg_negative": "Hindi pinapayagan ang mga negatibong numero",
        "msg_count": "Bilang:",
        "msg_error": "Pagkakamali:",
        "msg_done": "Tapos na!",
    },
    "tr": {
        "factorial": "faktoriyel",
        "main": "ana",
        "numbers": "sayilar",
        "num": "sayi",
        "result": "sonuc",
        "count": "sayac",
        "error_var": "hata_mesaji",
        "docstring": "n'nin faktöriyelini hesapla.",
        "comment_example": "Örnek: Hata işlemeli faktöriyel fonksiyonu",
        "comment_while": "while döngüsü gösterimi",
        "comment_try": "try/except gösterimi",
        "msg_negative": "Negatif sayılara izin verilmiyor",
        "msg_count": "Sayaç:",
        "msg_error": "Hata:",
        "msg_done": "Bitti!",
    },
    "uk": {
        "factorial": "факторіал",
        "main": "головна",
        "numbers": "числа",
        "num": "число",
        "result": "результат",
        "count": "лічильник",
        "error_var": "помилка",
        "docstring": "Обчислити факторіал числа n.",
        "comment_example": "Приклад: функція факторіала з обробкою помилок",
        "comment_while": "Демонстрація циклу while",
        "comment_try": "Демонстрація try/except",
        "msg_negative": "Від'ємні числа не допускаються",
        "msg_count": "Лічильник:",
        "msg_error": "Помилка:",
        "msg_done": "Готово!",
    },
    "ur": {
        "factorial": "فیکٹوریل",
        "main": "مرکزی",
        "numbers": "اعداد",
        "num": "عدد",
        "result": "نتیجہ",
        "count": "گنتی",
        "error_var": "غلطی",
        "docstring": "عدد ن کا فیکٹوریل حساب کریں۔",
        "comment_example": "مثال: غلطی کی ہینڈلنگ کے ساتھ فیکٹوریل فنکشن",
        "comment_while": "جبتک لوپ کا مظاہرہ",
        "comment_try": "کوشش/سوائے کا مظاہرہ",
        "msg_negative": "منفی اعداد کی اجازت نہیں",
        "msg_count": "گنتی:",
        "msg_error": "غلطی:",
        "msg_done": "مکمل!",
    },
    "uz": {
        "factorial": "faktorial",
        "main": "asosiy",
        "numbers": "raqamlar",
        "num": "raqam",
        "result": "natija",
        "count": "hisoblagich",
        "error_var": "xatolik",
        "docstring": "n ning faktorialini hisoblang.",
        "comment_example": "Misol: Xatolarni qayta ishlash bilan faktorial funksiyasi",
        "comment_while": "while sikli namoyishi",
        "comment_try": "try/except namoyishi",
        "msg_negative": "Manfiy sonlar ruxsat etilmaydi",
        "msg_count": "Hisoblagich:",
        "msg_error": "Xatolik:",
        "msg_done": "Tayyor!",
    },
    "vi": {
        "factorial": "giaithua",
        "main": "chinh",
        "numbers": "cacso",
        "num": "so",
        "result": "ketqua",
        "count": "dem",
        "error_var": "loi",
        "docstring": "Tính giai thừa của n.",
        "comment_example": "Ví dụ: Hàm giai thừa với xử lý lỗi",
        "comment_while": "Minh họa vòng lặp while",
        "comment_try": "Minh họa try/except",
        "msg_negative": "Không cho phép số âm",
        "msg_count": "Đếm:",
        "msg_error": "Lỗi:",
        "msg_done": "Hoàn thành!",
    },
    "xh": {
        "factorial": "ifaktoriyali",
        "main": "eyona",
        "numbers": "amanani",
        "num": "inani",
        "result": "isiphumo",
        "count": "isibali",
        "error_var": "impazamo",
        "docstring": "Bala ifaktoriyali ka-n.",
        "comment_example": "Umzekelo: ifaktoriyali kunye nokulawula iimpazamo",
        "comment_while": "Umboniso we-while",
        "comment_try": "Umboniso we-try/except",
        "msg_negative": "Amanani angaphantsi kweqanda awavumelekanga",
        "msg_count": "Isibali:",
        "msg_error": "Impazamo:",
        "msg_done": "Kugqityiwe!",
    },
    "zh": {
        "factorial": "阶乘",
        "main": "主函数",
        "numbers": "数字列表",
        "num": "数字",
        "result": "结果",
        "count": "计数",
        "error_var": "错误信息",
        "docstring": "计算n的阶乘。",
        "comment_example": "示例：带错误处理的阶乘函数",
        "comment_while": "演示while循环",
        "comment_try": "演示try/except",
        "msg_negative": "不允许负数",
        "msg_count": "计数：",
        "msg_error": "错误：",
        "msg_done": "完成！",
    },
}


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_languages() -> dict:
    """Load language metadata from languages.json."""
    with open(LANGUAGES_JSON, encoding="utf-8") as f:
        return json.load(f)["languages"]


def get_packs_dir(lang_code: str) -> Path:
    """Get path to language pack's packs directory."""
    return PACKS_DIR / lang_code / f"legesher_i18n_python_{lang_code}" / "packs"


def find_packs_dir(code: str, packs_root: Path = PACKS_DIR) -> Path:
    """The ``packs`` directory of a pack under *packs_root*.

    The package directory is ``legesher_i18n_python_<code>`` for every shipped
    pack; a dialect pack whose code is not a Python identifier (``es-MX``)
    normalises it, so a single ``legesher_i18n_python_*`` match is accepted.
    """
    exact = packs_root / code / f"legesher_i18n_python_{code}" / "packs"
    if exact.is_dir():
        return exact
    matches = sorted((packs_root / code).glob("legesher_i18n_python_*/packs"))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"Packs directory not found: {exact}")


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def version_layers(packs_dir: Path) -> list[tuple[str, dict]]:
    """``(python version, raw YAML)`` per version file, oldest first."""
    files = sorted(packs_dir.glob("3.*.yml"), key=lambda p: _version_key(p.stem))
    if not files:
        raise FileNotFoundError(f"No version files found in {packs_dir}")
    return [(path.stem, load_yaml(path) or {}) for path in files]


def load_merged_pack(lang_code: str) -> dict:
    """Load and merge all YAML files for a language pack.

    This merges all version files (3.10.yml, 3.11.yml, etc.) to get
    the complete set of keywords, builtins, and exceptions; a later file
    overrides an earlier word, which is the newest Python view.
    """
    merged: dict[str, dict] = {section: {} for section in SECTIONS}
    for _version, data in version_layers(find_packs_dir(lang_code)):
        for section in SECTIONS:
            if data.get(section):
                merged[section].update(data[section])
    return merged


def pack_digest(packs_dir: Path) -> str:
    """First 12 hex digits of a SHA-256 over this pack's version files, by name."""
    digest = hashlib.sha256()
    for path in sorted(packs_dir.glob("3.*.yml"), key=lambda p: _version_key(p.stem)):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _pyproject_project(pack_root: Path) -> dict:
    with (pack_root / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]


def pack_version_from_pyproject(pack_root: Path) -> str:
    """The pack's version, from its own ``pyproject.toml`` and nowhere else."""
    return str(_pyproject_project(pack_root)["version"])


def pack_distribution_name(pack_root: Path) -> str:
    """The pack's distribution name (``legesher-i18n-python-si``) from ``pyproject.toml``."""
    return str(_pyproject_project(pack_root)["name"])


def _term_arrivals(index_path: Path = VERSION_INDEX) -> tuple[str, dict[str, str]]:
    """The base Python version and ``key -> version`` for every term the index adds later."""
    index = load_yaml(index_path)["python_versions"]
    versions = sorted(index, key=_version_key)
    arrivals: dict[str, str] = {}
    for version in versions:
        for section, list_name in INDEX_LISTS.items():
            for term in index[version].get(list_name) or []:
                arrivals[f"{section}.{term}"] = version
    return versions[0], arrivals


@dataclass(frozen=True)
class TermRow:
    """One term of one pack in one Python view."""

    key: str
    section: str
    term: str
    english: str
    word: str | None
    applies_from: str
    earlier: tuple[tuple[str, str, str], ...]
    inherited_from: str | None


@dataclass(frozen=True)
class PackView:
    """A pack's words at one Python version, with every version string it needs."""

    code: str
    bcp47: str
    name: str
    native: str
    rtl: bool
    iso639_2: str
    status: str
    pack_name: str
    pack_version: str
    python: str
    python_versions: tuple[str, ...]
    digest: str
    rows: tuple[TermRow, ...]
    lacking: tuple[str, ...]
    base: str | None

    @property
    def rows_by_key(self) -> dict[str, TermRow]:
        return {row.key: row for row in self.rows}

    @property
    def metadata(self) -> TemplateMetadata:
        return TemplateMetadata(
            format=FORMAT_VERSION,
            pack=self.pack_name,
            pack_version=self.pack_version,
            python=self.python,
            code=self.code,
            bcp47=self.bcp47,
            digest=self.digest,
        )

    def section_rows(self, section: str) -> list[TermRow]:
        return [row for row in self.rows if row.section == section]


def _word_histories(
    layers: list[tuple[str, dict]], upto: str
) -> dict[str, list[tuple[str, str]]]:
    """``key -> [(version, word), ...]`` for every distinct word along the chain up to *upto*."""
    histories: dict[str, list[tuple[str, str]]] = {}
    for version, data in layers:
        if _version_key(version) > _version_key(upto):
            continue
        for section in SECTIONS:
            for term, word in (data.get(section) or {}).items():
                key = f"{section}.{term}"
                history = histories.setdefault(key, [])
                if not history or history[-1][1] != str(word):
                    history.append((version, str(word)))
    return histories


def _row_from_history(
    key: str,
    english: str,
    history: list[tuple[str, str]],
    versions: list[str],
    base_version: str,
    arrivals: dict[str, str],
    inherited_from: str | None,
) -> TermRow:
    section, term = key.split(".", 1)
    term_from = arrivals.get(key, base_version)
    first_version = history[0][0]
    if _version_key(first_version) < _version_key(term_from):
        raise ValueError(
            f"{key} is set in {first_version}.yml but the term arrives in Python {term_from}"
            " (version-index.yml); a word cannot predate its term"
        )
    word_from, word = history[-1]
    earlier: list[tuple[str, str, str]] = []
    for index, (version, old_word) in enumerate(history[:-1]):
        next_version = history[index + 1][0]
        before = versions[versions.index(next_version) - 1]
        earlier.append((version, before, old_word))
    applies_from = word_from
    return TermRow(
        key=key,
        section=section,
        term=term,
        english=english,
        word=word,
        applies_from=applies_from,
        earlier=tuple(earlier),
        inherited_from=inherited_from,
    )


_TAG_RE = re.compile(
    r"^(?P<language>[a-z]{2,3})(?:-(?P<script>[A-Z][a-z]{3}))?(?:-(?P<region>[A-Z]{2}|\d{3}))?$"
)


def _base_code(bcp47: str, registry: dict) -> str | None:
    """The registry language a region dialect inherits from, if the registry has one.

    Only a region subtag makes a dialect (``es-MX`` from ``es``, ``zh-Hans-TW``
    from ``zh-Hans``). A script subtag never does: ``pa-Arab`` must not inherit
    Gurmukhi words from ``pa``.
    """
    match = _TAG_RE.match(bcp47)
    if match is None or match.group("region") is None:
        return None
    base_tag = match.group("language")
    if match.group("script"):
        base_tag += "-" + match.group("script")
    by_tag = {entry["bcp47"]: code for code, entry in registry.items()}
    return by_tag.get(base_tag)


def load_pack_view(
    code: str,
    *,
    packs_root: Path = PACKS_DIR,
    registry: dict | None = None,
    python_version: str | None = None,
) -> PackView:
    """Build the view of one pack at one Python version.

    *python_version* defaults to the pack's newest version file. The key set is
    English's at the same version; a key the pack lacks becomes a row with no
    word and an entry in ``lacking``. A dialect pack takes the rows it does not
    define from its base language, marked ``inherited_from``.
    """
    languages = registry if registry is not None else load_languages()
    info = languages[code]
    pack_root = packs_root / code
    packs_dir = find_packs_dir(code, packs_root)
    layers = version_layers(packs_dir)
    versions = [version for version, _ in layers]
    python = python_version if python_version is not None else versions[-1]
    if python not in versions:
        raise ValueError(
            f"{code} has no {python}.yml version file (has {', '.join(versions)})"
        )
    index_path = packs_root / "version-index.yml"
    base_version, arrivals = _term_arrivals(
        index_path if index_path.is_file() else VERSION_INDEX
    )

    canonical = json.loads(LANGUAGES_JSON.read_text(encoding="utf-8"))[
        "canonical_language"
    ]
    english_layers = version_layers(find_packs_dir(canonical, packs_root))
    english = _word_histories(english_layers, python)
    own = _word_histories(layers, python)

    base = _base_code(info["bcp47"], languages)
    base_histories: dict[str, list[tuple[str, str]]] = {}
    base_versions: list[str] = []
    if base is not None:
        base_layers = version_layers(find_packs_dir(base, packs_root))
        base_versions = [version for version, _ in base_layers]
        base_histories = _word_histories(base_layers, python)

    rows: list[TermRow] = []
    lacking: list[str] = []
    for section in SECTIONS:
        keys = sorted(
            (key for key in english if key.startswith(section + ".")),
            key=lambda k: k.split(".", 1)[1].lower(),
        )
        for key in keys:
            english_word = english[key][-1][1]
            if key in own:
                rows.append(
                    _row_from_history(
                        key,
                        english_word,
                        own[key],
                        versions,
                        base_version,
                        arrivals,
                        None,
                    )
                )
            elif key in base_histories:
                rows.append(
                    _row_from_history(
                        key,
                        english_word,
                        base_histories[key],
                        base_versions,
                        base_version,
                        arrivals,
                        base,
                    )
                )
            else:
                lacking.append(key)
                rows.append(
                    TermRow(
                        key=key,
                        section=section,
                        term=key.split(".", 1)[1],
                        english=english_word,
                        word=None,
                        applies_from=max(
                            arrivals.get(key, base_version),
                            versions[0],
                            key=_version_key,
                        ),
                        earlier=(),
                        inherited_from=None,
                    )
                )

    return PackView(
        code=code,
        bcp47=info["bcp47"],
        name=info["name"],
        native=info["native"],
        rtl=bool(info.get("rtl", False)),
        iso639_2=str(info.get("iso639_2", "")),
        status=str(info.get("status", "experimental")),
        pack_name=pack_distribution_name(pack_root),
        pack_version=pack_version_from_pyproject(pack_root),
        python=python,
        python_versions=tuple(versions),
        digest=pack_digest(packs_dir),
        rows=tuple(rows),
        lacking=tuple(lacking),
        base=base,
    )


def generate_example_code(
    lang_code: str, keywords: dict, builtins: dict, exceptions: dict
) -> str:
    """Generate example code using as many keywords as possible."""
    kw = keywords
    bl = builtins
    ex = exceptions
    txt = EXAMPLE_TEXT.get(lang_code, EXAMPLE_TEXT["es"])  # Fallback to Spanish

    # Get translated ValueError (stored lowercase in exceptions dict).
    # Use the pack value verbatim: the identifier is case-sensitive, so
    # "class name style" capitalization would document a name the pack
    # never maps (the table above and the example must agree).
    value_error = ex.get("valueerror", "ValueError")

    # Build example that uses many keywords with localized names
    example = f'''```python
# {txt["comment_example"]}

{kw.get("from", "from")} typing {kw.get("import", "import")} Optional

{kw.get("def", "def")} {txt["factorial"]}(n):
    """{txt["docstring"]}"""
    {kw.get("if", "if")} n < 0:
        {kw.get("raise", "raise")} {value_error}("{txt["msg_negative"]}")
    {kw.get("elif", "elif")} n == 0 {kw.get("or", "or")} n == 1:
        {kw.get("return", "return")} 1
    {kw.get("else", "else")}:
        {kw.get("return", "return")} n * {txt["factorial"]}(n - 1)

{kw.get("def", "def")} {txt["main"]}():
    {txt["numbers"]} = [{bl.get("int", "int")}(x) {kw.get("for", "for")} x {kw.get("in", "in")} {bl.get("range", "range")}(6)]

    {kw.get("for", "for")} {txt["num"]} {kw.get("in", "in")} {txt["numbers"]}:
        {txt["result"]} = {txt["factorial"]}({txt["num"]})
        {bl.get("print", "print")}(f"{{{txt["num"]}}}! = {{{txt["result"]}}}")

    # {txt["comment_while"]}
    {txt["count"]} = 0
    {kw.get("while", "while")} {txt["count"]} < 3:
        {bl.get("print", "print")}(f"{txt["msg_count"]} {{{txt["count"]}}}")
        {txt["count"]} += 1

    # {txt["comment_try"]}
    {kw.get("try", "try")}:
        {txt["factorial"]}(-1)
    {kw.get("except", "except")} {value_error} {kw.get("as", "as")} {txt["error_var"]}:
        {bl.get("print", "print")}(f"{txt["msg_error"]} {{{txt["error_var"]}}}")
    {kw.get("finally", "finally")}:
        {bl.get("print", "print")}("{txt["msg_done"]}")

{kw.get("if", "if")} __name__ == "__main__":
    {txt["main"]}()
```'''
    return example


def _applies_to(row: TermRow) -> str:
    cell = f"{row.applies_from}+"
    for start, end, old_word in row.earlier:
        cell += f" ({start} to {end}: `{old_word}`)"
    if row.inherited_from is not None:
        cell += f" · inherited from {row.inherited_from}"
    return cell


def _term_table(view: PackView, section: str) -> str:
    column = f"{view.name} · {view.pack_version} · Python {view.python}"
    lines = [
        f"| Key | English | {column} | Applies to | Suggested | Comments |",
        f"| --- | ------- | {'-' * len(column)} | ---------- | --------- | -------- |",
    ]
    for row in view.section_rows(section):
        word = f"`{row.word}`" if row.word is not None else "(no word in this pack)"
        lines.append(
            f"| `{row.key}` | `{row.english}` | {word} | {_applies_to(row)} | | |"
        )
    return "\n".join(lines)


SECTION_TITLES = {
    "keywords": "Keywords",
    "builtins": "Built-in Functions",
    "exceptions": "Exceptions",
    "implicit_params": "Reserved Words",
}


def render_template(view: PackView, english_view: PackView) -> str:
    """The REFERENCE.md of *view*, also its review template.

    *english_view* is the English view at the same Python version; rendering
    refuses a pair whose key sets differ, so a template can never show a key
    set that is not English's.
    """
    own_keys = [row.key for row in view.rows]
    english_keys = [row.key for row in english_view.rows]
    if own_keys != english_keys:
        raise ValueError(
            f"{view.code} rows do not match the English view at Python {view.python}: "
            f"{sorted(set(own_keys) ^ set(english_keys))}"
        )

    name, native, code = view.name, view.native, view.code
    folder = review_folder(code, view.bcp47)
    first_file = review_file_name(folder, "<your-github-username>")
    bumped_file = review_file_name(folder, "<your-github-username>", "<pack-version>")

    words = {
        section: {
            row.term: row.word
            for row in view.section_rows(section)
            if row.word is not None
        }
        for section in SECTIONS
    }
    example = generate_example_code(
        code, words["keywords"], words["builtins"], words["exceptions"]
    )

    iso639_2 = view.iso639_2
    status = view.status
    script = LANGUAGE_SCRIPTS.get(code, "Unknown")
    status_color = "yellow" if status == "experimental" else "brightgreen"
    badges = (
        f"![Legesher](https://img.shields.io/badge/Legesher-{code}-blue?"
        f"style=for-the-badge&logo=python&logoColor=white)\n"
        f"![Script](https://img.shields.io/badge/Script-"
        f"{script.replace(' ', '%20').replace('(', '%28').replace(')', '%29').replace(',', '%2C')}"
        f"-green?style=for-the-badge)\n"
        f"![Status](https://img.shields.io/badge/Status-{status.capitalize()}-"
        f"{status_color}?style=for-the-badge)"
    )
    if view.rtl:
        badges += "\n![RTL](https://img.shields.io/badge/Direction-RTL-orange?style=for-the-badge)"

    rtl_note = ""
    if view.rtl:
        rtl_note = (
            "\n>\n> **Note:** This is a right-to-left (RTL) language. RTL support is a work in\n"
            "> progress; the words below render in the same order a Python source line shows\n"
            "> them."
        )

    older = [v for v in view.python_versions if v != view.python]
    if older:
        coverage = (
            f"The pack also covers Python {older[0]}"
            + (f" to {older[-1]}" if len(older) > 1 else "")
            + ". Where an earlier Python version uses a different word, the\n"
            '"Applies to" column shows that word and its versions.'
        )
    else:
        coverage = f"Python {view.python} is the only version this pack covers so far."

    base_note = ""
    if view.base is not None:
        base_note = (
            f"\n\nThis is a dialect pack. Rows marked `inherited from {view.base}` carry the"
            f" `{view.base}` word unchanged; a review of this file is a review of"
            f" `{view.pack_name}`, not of `{view.base}`."
        )

    lacking_note = ""
    if view.lacking:
        lacking_note = (
            "\n\nTerms this pack has no word for yet (listed so the row still exists): "
            + ", ".join(f"`{key}`" for key in view.lacking)
            + "."
        )

    sections = "\n\n".join(
        f"## {SECTION_TITLES[section]}\n\n{_section_intro(section, name, view)}\n\n{_term_table(view, section)}"
        for section in SECTIONS
    )

    return f"""{render_metadata_line(view.metadata)}
# {name} ({native}) · {view.pack_name} {view.pack_version} · Python {view.python}

{badges}

> Write Python code in {name}. This guide shows the {name} words Legesher
> understands for Python's keywords, built-in functions, exceptions and
> reserved words, as shipped in `{view.pack_name}` {view.pack_version}.{rtl_note}

This file is also the review template for this pack. To review it, copy this file to
`reviews/{folder}/{first_file}` in the
[language-packs repository]({LANGUAGE_PACKS_URL}), fill in the Suggested and
Comments columns for the terms you want to review, and open a pull request. Untouched rows
mean "no opinion". The full guide is
[REVIEWING.md]({LANGUAGE_PACKS_URL}/blob/main/REVIEWING.md).

The words shown are the Python {view.python} view of this pack, its newest version file.
{coverage}{base_note}{lacking_note}

## About you

- GitHub username: `<your-github-username>` (must be the account that opens the pull request)
- Your relationship to {name} (keep one): native speaker · fluent · professional · learning

## Before you submit

Required:

- [ ] These suggestions and comments are my own work. AI help with formatting is fine; the
      linguistic judgment is mine.
- [ ] I sign off under the Developer Certificate of Origin.
- [ ] I license my suggestions and comments under Apache-2.0.
- [ ] I agree to the Code of Conduct.
- [ ] I have read "Your contributions and your data" (CONTRIBUTOR_PRIVACY.md, version 1.0) and agree.

Optional:

- [ ] My contribution data may appear in research datasets and publications (never my identity).

Credit me as (keep one): anonymous · my GitHub handle · this name: `<name>`

Do not put an email address in this file. It is public. To reach us privately, write to
<contribute@legesher.com>.

## Language Details

| Attribute | Value |
| --------- | ----- |
| **Language** | {name} |
| **Native Name** | {native} |
| **Script** | {script} |
| **Pack** | `{view.pack_name}` {view.pack_version} |
| **Python view** | {view.python} (version files: {", ".join(view.python_versions)}) |
| **ISO 639-2** | `{iso639_2}` |
| **BCP 47 Tag** | `{view.bcp47}` |
| **Text Direction** | {"Right-to-Left (RTL)" if view.rtl else "Left-to-Right (LTR)"} |
| **Status** | {status.capitalize()} |

{sections}

## Example Code

Here's an example showing {name} Python code with Legesher:

{example}

## Usage

```python
from legesher_i18n import LanguagePackLoader

# Load the {name} pack for Python {view.python}
loader = LanguagePackLoader()
pack = loader.load("{code}", "python", "{view.python}")

# Translate code
from legesher import translate
english_code = translate(your_{code.replace("-", "_")}_code, from_lang="{code}", to_lang="en")
```

## Notes for Future Updates

Language-wide observations: word order, register, how compounds join. Write them here when you
review; they often matter more than any single word.

## How to submit this review

1. Copy this file to `reviews/{folder}/{first_file}` in
   [language-packs]({LANGUAGE_PACKS_URL}). The username in the name must be the account that
   opens the pull request.
2. For each term you have an opinion on: `✓` in Comments endorses the current word; `Keep` plus a
   note endorses it with a recorded limitation; a word in Suggested plus your reasoning in Comments
   proposes a replacement. Leave the other rows untouched, and leave the first line of the file and
   the Key, English, current-word and Applies to columns as they are: the importer reads them.
3. Fill in "About you", tick the boxes under "Before you submit", and open a pull request with one
   language per pull request. Sign your commits off (`git commit -s`).
4. A second review of the same pack version updates your existing file. After a pack version bump,
   start a new file named `{bumped_file}` from the regenerated template.

The guide is [REVIEWING.md]({LANGUAGE_PACKS_URL}/blob/main/REVIEWING.md); the folder rules are in
[reviews/README.md]({LANGUAGE_PACKS_URL}/blob/main/reviews/README.md).
"""


def _section_intro(section: str, name: str, view: PackView) -> str:
    count = sum(1 for row in view.section_rows(section) if row.word is not None)
    if section == "keywords":
        return (
            f"These are Python's reserved words translated to {name} ({count} terms)."
        )
    if section == "builtins":
        return f"Python's built-in functions and types in {name} ({count} terms)."
    if section == "exceptions":
        return f"Exception classes for error handling ({count} terms)."
    return (
        f"Python conventions like `self` and `cls` translated deterministically by the\n"
        f"language pack rather than the LLM ({count} terms). Distinct from keywords because they\n"
        "aren't actual keywords in the Python language."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line; with no arguments the files are written in place."""
    parser = argparse.ArgumentParser(
        description="Generate REFERENCE.md, the review template, for every registry language."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "write DIR/<code>/REFERENCE.md instead of the in-tree files; "
            "make check-generated-reference uses this to diff a fresh "
            "regeneration against the committed files"
        ),
    )
    parser.add_argument(
        "--languages",
        default=None,
        metavar="CODES",
        help="comma-separated registry codes to generate (default: every registry language)",
    )
    parser.add_argument(
        "--python-version",
        default=None,
        metavar="X.Y",
        help="render the view at this Python version instead of each pack's newest version file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Generate REFERENCE.md for every registry language (or ``--languages``)."""
    args = parse_args(argv)
    out_root = args.out if args.out is not None else PACKS_DIR
    languages = load_languages()
    codes = sorted(languages)
    if args.languages:
        codes = [code.strip() for code in args.languages.split(",") if code.strip()]
        unknown = [code for code in codes if code not in languages]
        if unknown:
            raise SystemExit(f"not in the language registry: {', '.join(unknown)}")

    generated = []
    errors = []
    english_views: dict[str, PackView] = {}

    for lang_code in codes:
        output_path = out_root / lang_code / "REFERENCE.md"
        try:
            view = load_pack_view(lang_code, python_version=args.python_version)
            if view.python not in english_views:
                english_views[view.python] = load_pack_view(
                    "en", python_version=view.python
                )
            content = render_template(view, english_views[view.python])
            if args.out is not None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            counts = {section: len(view.section_rows(section)) for section in SECTIONS}
            generated.append(
                f"  {lang_code}: {view.name} {view.pack_version} "
                f"({counts['keywords']} kw, {counts['builtins']} builtins, "
                f"{counts['exceptions']} exceptions)"
            )
        except Exception as e:  # noqa: BLE001 - every language is reported, then the run fails
            errors.append(f"  {lang_code}: Error - {e}")

    print(f"Generated {len(generated)} REFERENCE.md files:")
    for g in generated:
        print(g)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
