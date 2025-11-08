"""Python keyword documentation in multiple languages.

This module provides documentation for Python keywords with translations
for hover tooltips in the Language Server.
"""

# Python keyword documentation (English, Spanish, Arabic)
PYTHON_KEYWORD_DOCS = {
    "def": {
        "en": "Define a function",
        "es": "Definir una función",
        "ar": "تعريف دالة",
    },
    "class": {
        "en": "Define a class",
        "es": "Definir una clase",
        "ar": "تعريف فئة",
    },
    "if": {
        "en": "Conditional statement",
        "es": "Declaración condicional",
        "ar": "جملة شرطية",
    },
    "elif": {
        "en": "Else if condition",
        "es": "Si no, si condición",
        "ar": "وإلا إذا كان الشرط",
    },
    "else": {
        "en": "Alternative condition",
        "es": "Condición alternativa",
        "ar": "شرط بديل",
    },
    "for": {
        "en": "For loop iteration",
        "es": "Bucle for de iteración",
        "ar": "حلقة التكرار for",
    },
    "while": {
        "en": "While loop",
        "es": "Bucle while",
        "ar": "حلقة while",
    },
    "return": {
        "en": "Return value from function",
        "es": "Devolver valor de función",
        "ar": "إرجاع قيمة من دالة",
    },
    "import": {
        "en": "Import module",
        "es": "Importar módulo",
        "ar": "استيراد وحدة",
    },
    "from": {
        "en": "Import from module",
        "es": "Importar desde módulo",
        "ar": "استيراد من وحدة",
    },
    "as": {
        "en": "Alias for import",
        "es": "Alias para importación",
        "ar": "اسم مستعار للاستيراد",
    },
    "try": {
        "en": "Try exception handling",
        "es": "Intentar manejo de excepciones",
        "ar": "محاولة معالجة الاستثناءات",
    },
    "except": {
        "en": "Catch exception",
        "es": "Capturar excepción",
        "ar": "التقاط استثناء",
    },
    "finally": {
        "en": "Execute regardless of exception",
        "es": "Ejecutar independientemente de excepción",
        "ar": "تنفيذ بغض النظر عن الاستثناء",
    },
    "raise": {
        "en": "Raise an exception",
        "es": "Lanzar una excepción",
        "ar": "إطلاق استثناء",
    },
    "with": {
        "en": "Context manager",
        "es": "Gestor de contexto",
        "ar": "مدير السياق",
    },
    "pass": {
        "en": "Empty statement",
        "es": "Declaración vacía",
        "ar": "جملة فارغة",
    },
    "break": {
        "en": "Exit loop",
        "es": "Salir del bucle",
        "ar": "الخروج من الحلقة",
    },
    "continue": {
        "en": "Continue to next iteration",
        "es": "Continuar a siguiente iteración",
        "ar": "المتابعة إلى التكرار التالي",
    },
    "yield": {
        "en": "Generate value (generator)",
        "es": "Generar valor (generador)",
        "ar": "إنتاج قيمة (مولد)",
    },
    "lambda": {
        "en": "Anonymous function",
        "es": "Función anónima",
        "ar": "دالة مجهولة",
    },
    "global": {
        "en": "Declare global variable",
        "es": "Declarar variable global",
        "ar": "الإعلان عن متغير عام",
    },
    "nonlocal": {
        "en": "Declare nonlocal variable",
        "es": "Declarar variable no local",
        "ar": "الإعلان عن متغير غير محلي",
    },
    "assert": {
        "en": "Assert condition is true",
        "es": "Afirmar que condición es verdadera",
        "ar": "التأكيد على صحة الشرط",
    },
    "del": {
        "en": "Delete object",
        "es": "Eliminar objeto",
        "ar": "حذف كائن",
    },
    "await": {
        "en": "Await coroutine",
        "es": "Esperar corrutina",
        "ar": "انتظار coroutine",
    },
    "async": {
        "en": "Define async function/context",
        "es": "Definir función/contexto asíncrono",
        "ar": "تعريف دالة/سياق غير متزامن",
    },
    "match": {
        "en": "Pattern matching (Python 3.10+)",
        "es": "Coincidencia de patrones (Python 3.10+)",
        "ar": "مطابقة الأنماط (Python 3.10+)",
    },
    "case": {
        "en": "Match case pattern (Python 3.10+)",
        "es": "Caso de coincidencia (Python 3.10+)",
        "ar": "حالة المطابقة (Python 3.10+)",
    },
    "and": {
        "en": "Logical AND operator",
        "es": "Operador AND lógico",
        "ar": "عامل AND المنطقي",
    },
    "or": {
        "en": "Logical OR operator",
        "es": "Operador OR lógico",
        "ar": "عامل OR المنطقي",
    },
    "not": {
        "en": "Logical NOT operator",
        "es": "Operador NOT lógico",
        "ar": "عامل NOT المنطقي",
    },
    "in": {
        "en": "Membership test operator",
        "es": "Operador de prueba de pertenencia",
        "ar": "عامل اختبار العضوية",
    },
    "is": {
        "en": "Identity test operator",
        "es": "Operador de prueba de identidad",
        "ar": "عامل اختبار الهوية",
    },
    "True": {
        "en": "Boolean true value",
        "es": "Valor booleano verdadero",
        "ar": "القيمة المنطقية صحيح",
    },
    "False": {
        "en": "Boolean false value",
        "es": "Valor booleano falso",
        "ar": "القيمة المنطقية خطأ",
    },
    "None": {
        "en": "Null value",
        "es": "Valor nulo",
        "ar": "قيمة فارغة",
    },
}


class KeywordDocumentation:
    """Provides documentation for Python keywords in multiple languages.

    This class provides quick access to keyword documentation for hover
    tooltips, with support for English, Spanish, and Arabic.
    """

    def __init__(self) -> None:
        """Initialize keyword documentation."""
        self._docs = PYTHON_KEYWORD_DOCS

    def get(self, keyword: str, language: str = "en") -> str | None:
        """Get documentation for a keyword in specified language.

        Args:
            keyword: Python keyword (e.g., 'def', 'class', 'if')
            language: Target language code ('en', 'es', 'ar')

        Returns:
            Documentation string or None if keyword/language not found

        Example:
            >>> docs = KeywordDocumentation()
            >>> docs.get("def", "es")
            'Definir una función'
            >>> docs.get("class", "ar")
            'تعريف فئة'
        """
        if keyword not in self._docs:
            return None

        keyword_doc = self._docs[keyword]
        return keyword_doc.get(language)

    def has_keyword(self, keyword: str) -> bool:
        """Check if keyword has documentation.

        Args:
            keyword: Python keyword to check

        Returns:
            True if keyword has documentation
        """
        return keyword in self._docs

    def get_all_keywords(self) -> list[str]:
        """Get list of all documented keywords.

        Returns:
            List of Python keywords with documentation
        """
        return list(self._docs.keys())

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language codes ('en', 'es', 'ar')
        """
        return ["en", "es", "ar"]

    def _find_language_pack(self, target_lang: str):
        """Find language pack directory using multiple strategies.

        Checks:
        1. Development location: libs/i18n-python-{lang}/ (relative to this file)
        2. Installed package: try importing legesher_i18n_python_{lang}
        3. Site-packages: check importlib metadata

        Args:
            target_lang: Target language code

        Returns:
            Path to language pack directory or None if not found
        """
        from pathlib import Path

        # Strategy 1: Development monorepo structure (libs/ directory)
        dev_pack_dir = Path(__file__).parent.parent.parent.parent / f"i18n-python-{target_lang}"
        if dev_pack_dir.exists():
            return dev_pack_dir

        # Strategy 2: Try importing the package (works if installed)
        try:
            import importlib.util

            pack_module_name = f"legesher_i18n_python_{target_lang}"
            spec = importlib.util.find_spec(pack_module_name)
            if spec and spec.origin:
                # Return parent directory of the package
                return Path(spec.origin).parent.parent
        except (ImportError, AttributeError):
            pass

        # Strategy 3: Check site-packages using importlib.metadata
        try:
            import importlib.metadata

            pack_dist_name = f"legesher-i18n-python-{target_lang}"
            dist = importlib.metadata.distribution(pack_dist_name)
            # Get files from distribution
            if dist.files:
                # Find the packs directory
                for file in dist.files:
                    if "packs" in str(file):
                        return Path(dist.locate_file(file)).parent.parent
        except (ImportError, importlib.metadata.PackageNotFoundError):
            pass

        return None

    def get_keyword_translation(self, keyword: str, target_lang: str) -> str | None:
        """Get keyword translation from English to target language.

        This method loads translations from i18n language packs dynamically.
        Uses robust package discovery that works in development and installed environments.

        Args:
            keyword: English keyword (e.g., 'def', 'class')
            target_lang: Target language code ('es', 'ar', 'zh')

        Returns:
            Translated keyword or None if not available

        Example:
            >>> docs = KeywordDocumentation()
            >>> docs.get_keyword_translation("def", "es")
            'definir'
            >>> docs.get_keyword_translation("class", "ar")
            'صنف'
        """
        # For MVP, load from i18n packages if available
        try:
            import yaml

            # Find language pack using robust discovery
            pack_dir = self._find_language_pack(target_lang)
            if not pack_dir:
                return None

            # Load the base pack (3.10 has all keywords)
            pack_file = pack_dir / f"legesher_i18n_python_{target_lang}" / "packs" / "3.10.yml"

            if pack_file.exists():
                with open(pack_file, encoding="utf-8") as f:
                    pack_data = yaml.safe_load(f)

                # Get keyword translation
                keywords = pack_data.get("keywords", {})
                return keywords.get(keyword)

        except Exception:
            # Fallback: If loading fails, return None
            pass

        return None
