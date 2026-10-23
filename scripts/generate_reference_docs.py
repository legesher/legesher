#!/usr/bin/env python3
"""Generate REFERENCE.md files for all language packs.

This script creates side-by-side comparison guides for developers
who want to code in their native language using Legesher.

By default the files are written in place, next to each pack. ``--out DIR``
writes ``DIR/<lang>/REFERENCE.md`` instead, which is how
``make check-generated-reference`` regenerates into a temporary tree and diffs
against the committed files (CORE-2415).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

# Paths
ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "libs" / "i18n"
PACKS_DIR = I18N_DIR / "language-packs" / "python"
LANGUAGES_JSON = I18N_DIR / "legesher_i18n" / "languages.json"

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
    "te": "Telugu",
    "th": "Thai",
    "tr": "Latin",
    "uk": "Cyrillic",
    "ur": "Arabic",
    "uz": "Latin",
    "vi": "Latin",
    "zh": "Simplified Chinese (Han)",
}

# Localized example text for each language
# Keys: factorial, main, numbers, num, result, count, error_var,
#       docstring, comment_example, comment_while, comment_try,
#       msg_negative, msg_count, msg_error, msg_done
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
        "error_var": "خطأ",
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
        "count": "গণনা",
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
        "result": "αποτέλεσμα",
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
        "error_var": "त्रुटि",
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
        "error_var": "hiba",
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
        "error_var": "오류",
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
        "count": "ရေတွက်",
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
    "nl": {
        "factorial": "faculteit",
        "main": "hoofd",
        "numbers": "getallen",
        "num": "getal",
        "result": "resultaat",
        "count": "teller",
        "error_var": "fout",
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
        "error_var": "feil",
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
        "error_var": "fel",
        "docstring": "Beräkna fakulteten av n.",
        "comment_example": "Exempel: Fakultetsfunktion med felhantering",
        "comment_while": "Demonstrera while-loop",
        "comment_try": "Demonstrera try/except",
        "msg_negative": "Negativa tal är inte tillåtna",
        "msg_count": "Räknare:",
        "msg_error": "Fel:",
        "msg_done": "Klart!",
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
    "tr": {
        "factorial": "faktoriyel",
        "main": "ana",
        "numbers": "sayilar",
        "num": "sayi",
        "result": "sonuc",
        "count": "sayac",
        "error_var": "hata",
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
    "zh": {
        "factorial": "阶乘",
        "main": "主函数",
        "numbers": "数字列表",
        "num": "数字",
        "result": "结果",
        "count": "计数",
        "error_var": "错误",
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


def load_merged_pack(lang_code: str) -> dict:
    """Load and merge all YAML files for a language pack.

    This merges all version files (3.10.yml, 3.11.yml, etc.) to get
    the complete set of keywords, builtins, and exceptions.
    """
    packs_dir = get_packs_dir(lang_code)

    if not packs_dir.exists():
        raise FileNotFoundError(f"Packs directory not found: {packs_dir}")

    # Find all version YAML files
    version_files = sorted(packs_dir.glob("3.*.yml"))

    if not version_files:
        raise FileNotFoundError(f"No version files found in {packs_dir}")

    # Merge all versions (base + additions from each version)
    merged = {
        "keywords": {},
        "builtins": {},
        "exceptions": {},
        "implicit_params": {},
    }

    for version_file in version_files:
        data = load_yaml(version_file)

        # Merge keywords
        if "keywords" in data and data["keywords"]:
            merged["keywords"].update(data["keywords"])

        # Merge builtins
        if "builtins" in data and data["builtins"]:
            merged["builtins"].update(data["builtins"])

        # Merge exceptions
        if "exceptions" in data and data["exceptions"]:
            merged["exceptions"].update(data["exceptions"])

        # Merge implicit_params (CORE-710: self, cls)
        if "implicit_params" in data and data["implicit_params"]:
            merged["implicit_params"].update(data["implicit_params"])

    return merged


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

{kw.get('from', 'from')} typing {kw.get('import', 'import')} Optional

{kw.get('def', 'def')} {txt["factorial"]}(n):
    """{txt["docstring"]}"""
    {kw.get('if', 'if')} n < 0:
        {kw.get('raise', 'raise')} {value_error}("{txt["msg_negative"]}")
    {kw.get('elif', 'elif')} n == 0 {kw.get('or', 'or')} n == 1:
        {kw.get('return', 'return')} 1
    {kw.get('else', 'else')}:
        {kw.get('return', 'return')} n * {txt["factorial"]}(n - 1)

{kw.get('def', 'def')} {txt["main"]}():
    {txt["numbers"]} = [{bl.get('int', 'int')}(x) {kw.get('for', 'for')} x {kw.get('in', 'in')} {bl.get('range', 'range')}(6)]

    {kw.get('for', 'for')} {txt["num"]} {kw.get('in', 'in')} {txt["numbers"]}:
        {txt["result"]} = {txt["factorial"]}({txt["num"]})
        {bl.get('print', 'print')}(f"{{{txt["num"]}}}! = {{{txt["result"]}}}")

    # {txt["comment_while"]}
    {txt["count"]} = 0
    {kw.get('while', 'while')} {txt["count"]} < 3:
        {bl.get('print', 'print')}(f"{txt["msg_count"]} {{{txt["count"]}}}")
        {txt["count"]} += 1

    # {txt["comment_try"]}
    {kw.get('try', 'try')}:
        {txt["factorial"]}(-1)
    {kw.get('except', 'except')} {value_error} {kw.get('as', 'as')} {txt["error_var"]}:
        {bl.get('print', 'print')}(f"{txt["msg_error"]} {{{txt["error_var"]}}}")
    {kw.get('finally', 'finally')}:
        {bl.get('print', 'print')}("{txt["msg_done"]}")

{kw.get('if', 'if')} __name__ == "__main__":
    {txt["main"]}()
```'''
    return example


def generate_reference_md(
    lang_code: str, lang_info: dict, pack_data: dict, english_data: dict
) -> str:
    """Generate REFERENCE.md content for a language pack."""
    name = lang_info["name"]
    native = lang_info["native"]
    rtl = lang_info.get("rtl", False)

    keywords = pack_data.get("keywords", {})
    builtins = pack_data.get("builtins", {})
    exceptions = pack_data.get("exceptions", {})
    implicit_params = pack_data.get("implicit_params", {})

    en_keywords = english_data.get("keywords", {})
    en_builtins = english_data.get("builtins", {})
    en_exceptions = english_data.get("exceptions", {})
    en_implicit_params = english_data.get("implicit_params", {})

    # Build keyword table (sorted alphabetically by English)
    keyword_rows = []
    for eng_kw in sorted(en_keywords.keys(), key=str.lower):
        trans = keywords.get(eng_kw, eng_kw)
        keyword_rows.append(f"| `{eng_kw}` | `{trans}` |")

    # Build builtin table (sorted alphabetically)
    builtin_rows = []
    for eng_bl in sorted(en_builtins.keys(), key=str.lower):
        trans = builtins.get(eng_bl, eng_bl)
        builtin_rows.append(f"| `{eng_bl}` | `{trans}` |")

    # Build exception table (sorted alphabetically)
    exception_rows = []
    for eng_ex in sorted(en_exceptions.keys(), key=str.lower):
        trans = exceptions.get(eng_ex, eng_ex)
        exception_rows.append(f"| `{eng_ex}` | `{trans}` |")

    # Build implicit-param table (CORE-710: self, cls). Sorted alphabetically.
    implicit_param_rows = []
    for eng_rw in sorted(en_implicit_params.keys(), key=str.lower):
        trans = implicit_params.get(eng_rw, eng_rw)
        implicit_param_rows.append(f"| `{eng_rw}` | `{trans}` |")

    # Generate example code
    example = generate_example_code(lang_code, keywords, builtins, exceptions)

    # Language metadata
    iso639_2 = lang_info.get("iso639_2", "")
    bcp47 = lang_info.get("bcp47", lang_code)
    status = lang_info.get("status", "experimental")
    script = LANGUAGE_SCRIPTS.get(lang_code, "Unknown")

    # Status badge color
    status_color = "yellow" if status == "experimental" else "brightgreen"

    # Build badge line
    badges = (
        f"![Legesher](https://img.shields.io/badge/Legesher-{lang_code}-blue?"
        f"style=for-the-badge&logo=python&logoColor=white)\n"
        f"![Script](https://img.shields.io/badge/Script-"
        f"{script.replace(' ', '%20').replace('(', '%28').replace(')', '%29').replace(',', '%2C')}"
        f"-green?style=for-the-badge)\n"
        f"![Status](https://img.shields.io/badge/Status-{status.capitalize()}-"
        f"{status_color}?style=for-the-badge)"
    )
    if rtl:
        badges += (
            "\n![RTL](https://img.shields.io/badge/Direction-RTL-orange?"
            "style=for-the-badge)"
        )

    # Build blockquote section
    blockquote = (
        f"> Write Python code in {name}. This guide shows the {name} keywords\n"
        f"> to use for Legesher to understand your code."
    )
    if rtl:
        blockquote += (
            "\n>\n> **Note:** This is a right-to-left (RTL) language. "
            "RTL support is currently a work in progress — we welcome your feedback!"
        )

    content = f"""# {name} ({native}) - Python Quick Reference

{badges}

{blockquote}

## Language Details

| Attribute | Value |
| --------- | ----- |
| **Language** | {name} |
| **Native Name** | {native} |
| **Script** | {script} |
| **ISO 639-1** | `{lang_code}` |
| **ISO 639-2** | `{iso639_2}` |
| **BCP 47 Tag** | `{bcp47}` |
| **Text Direction** | {"Right-to-Left (RTL)" if rtl else "Left-to-Right (LTR)"} |
| **Status** | {status.capitalize()} |

## Keywords ({len(keywords)} terms)

These are Python's reserved words translated to {name}.

| English | {name} |
| ------- | ------ |
{chr(10).join(keyword_rows)}

## Built-in Functions ({len(builtins)} terms)

Python's built-in functions and types in {name}.

| English | {name} |
| ------- | ------ |
{chr(10).join(builtin_rows)}

## Exceptions ({len(exceptions)} terms)

Exception classes for error handling.

| English | {name} |
| ------- | ------ |
{chr(10).join(exception_rows)}

## Reserved Words ({len(implicit_param_rows)} terms)

Python conventions like `self` and `cls` translated deterministically by the
language pack rather than the LLM. Distinct from keywords because they aren't
actual keywords in the Python language. (CORE-710)

| English | {name} |
| ------- | ------ |
{chr(10).join(implicit_param_rows)}

## Example Code

Here's an example showing {name} Python code with Legesher:

{example}

## Usage

```python
from legesher_i18n import LanguagePackLoader

# Load {name} pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("{lang_code}", "python", "3.12")

# Translate code
from legesher import translate
english_code = translate(your_{lang_code}_code, from_lang="{lang_code}", to_lang="en")
```

## Contributing

Found a better translation? We welcome contributions from native speakers!

1. Edit `legesher_i18n_python_{lang_code}/packs/<version>.yml` for the Python version where the term was introduced:
   - `3.10.yml` - Base translations (most terms)
   - `3.11.yml` - Terms added in Python 3.11 (e.g., `except*`)
   - `3.12.yml` - Terms added in Python 3.12 (e.g., `type`)
   - `3.13.yml` / `3.14.yml` - Future additions
2. Submit a pull request with your reasoning
3. Translations should be natural, commonly used in CS education, and easy to type
"""
    return content


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line; with no arguments the files are written in place."""
    parser = argparse.ArgumentParser(
        description="Generate REFERENCE.md for all language packs."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "write DIR/<lang>/REFERENCE.md instead of the in-tree files; "
            "make check-generated-reference uses this to diff a fresh "
            "regeneration against the committed files"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Generate REFERENCE.md for all non-English language packs."""
    args = parse_args(argv)
    out_root = args.out if args.out is not None else PACKS_DIR
    languages = load_languages()

    # Load merged English pack (all versions combined)
    try:
        english_data = load_merged_pack("en")
    except FileNotFoundError as e:
        print(f"Error loading English pack: {e}")
        return

    generated = []
    errors = []

    for lang_code in sorted(languages.keys()):
        if lang_code == "en":
            continue  # Skip English (it's the reference)

        packs_dir = get_packs_dir(lang_code)
        output_path = out_root / lang_code / "REFERENCE.md"

        if not packs_dir.exists():
            errors.append(f"  {lang_code}: Packs directory not found at {packs_dir}")
            continue

        try:
            # Load merged pack data (all versions combined)
            pack_data = load_merged_pack(lang_code)
            content = generate_reference_md(
                lang_code, languages[lang_code], pack_data, english_data
            )

            if args.out is not None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Count totals from merged data
            kw_count = len(pack_data.get("keywords", {}))
            bl_count = len(pack_data.get("builtins", {}))
            ex_count = len(pack_data.get("exceptions", {}))

            generated.append(
                f"  {lang_code}: {languages[lang_code]['name']} "
                f"({kw_count} kw, {bl_count} builtins, {ex_count} exceptions)"
            )
        except Exception as e:
            errors.append(f"  {lang_code}: Error - {e}")

    print(f"Generated {len(generated)} REFERENCE.md files:")
    for g in generated:
        print(g)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(e)


if __name__ == "__main__":
    main()
