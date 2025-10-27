"""Arabic translation maps for Python keywords and builtins.

This module provides hardcoded translation maps for translating Python
keywords and builtin functions to Arabic. These are used for testing
the token-based transformer and RTL language support.

Language: Arabic (العربية)
ISO Code: ar
Python Version: 3.13
Writing Direction: Right-to-left (RTL)
Encoding: UTF-8
"""

# Python 3.13 Keywords - Arabic Translations
# Based on common Arabic programming terminology
ARABIC_KEYWORDS = {
    # Control flow
    "if": "إذا",
    "elif": "وإلا_إذا",
    "else": "وإلا",
    "for": "لكل",
    "while": "بينما",
    "break": "كسر",
    "continue": "استمر",
    "pass": "تمرير",
    # Function/class definition
    "def": "تعريف",
    "class": "صنف",
    "return": "إرجاع",
    "yield": "إنتاج",
    "lambda": "لامدا",
    # Exception handling
    "try": "حاول",
    "except": "إلا",
    "finally": "أخيرا",
    "raise": "رفع",
    "assert": "تأكيد",
    # Imports
    "import": "استيراد",
    "from": "من",
    "as": "كـ",
    # Context managers
    "with": "مع",
    # Async keywords
    "async": "غير_متزامن",
    "await": "انتظر",
    # Boolean/None
    "True": "صحيح",
    "False": "خطأ",
    "None": "لاشيء",
    # Operators
    "and": "و",
    "or": "أو",
    "not": "ليس",
    "in": "في",
    "is": "هو",
    # Other
    "del": "حذف",
    "global": "عام",
    "nonlocal": "غير_محلي",
}

# Common Python Builtins - Arabic Translations
ARABIC_BUILTINS = {
    # I/O functions
    "print": "طباعة",
    "input": "إدخال",
    "open": "فتح",
    # Type conversions
    "int": "صحيح",
    "float": "عشري",
    "str": "نص",
    "bool": "منطقي",
    "list": "قائمة",
    "dict": "قاموس",
    "set": "مجموعة",
    "tuple": "صف",
    # Sequence operations
    "len": "طول",
    "range": "نطاق",
    "sum": "مجموع",
    "max": "أقصى",
    "min": "أدنى",
    "sorted": "مرتب",
    "reversed": "معكوس",
    "enumerate": "تعداد",
    "zip": "ضغط",
    # Functional programming
    "map": "خريطة",
    "filter": "تصفية",
    "any": "أي",
    "all": "الكل",
    # Object introspection
    "type": "نوع",
    "isinstance": "هو_مثيل",
    "hasattr": "له_خاصية",
    "getattr": "احصل_على_خاصية",
    "setattr": "اضبط_خاصية",
    "dir": "دليل",
    "help": "مساعدة",
    # Math functions
    "abs": "مطلق",
    "round": "تقريب",
    "pow": "قوة",
}

# Reverse maps for translating from Arabic back to English
ENGLISH_KEYWORDS = {v: k for k, v in ARABIC_KEYWORDS.items()}
ENGLISH_BUILTINS = {v: k for k, v in ARABIC_BUILTINS.items()}

# Validation: Ensure all Python 3.13 keywords are covered
PYTHON_313_KEYWORDS = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}

# Check coverage (should be 100%)
_missing_keywords = PYTHON_313_KEYWORDS - set(ARABIC_KEYWORDS.keys())
if _missing_keywords:
    raise ValueError(f"Missing Arabic translations for keywords: {_missing_keywords}")
