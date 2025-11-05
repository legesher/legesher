"""Error message templates for Python diagnostics.

Provides translated error messages for common Python errors with variable preservation.
This module enables translating Python error messages while preserving variable names,
line numbers, and other dynamic content.
"""

import re
from typing import Any


class ErrorMessageTemplates:
    """Manages error message templates and translations.

    This class provides translation templates for common Python error messages,
    supporting variable substitution to preserve dynamic content like variable
    names, line numbers, types, and other context-specific information.

    Example:
        >>> templates = ErrorMessageTemplates()
        >>> templates.get_translation(
        ...     "NameError",
        ...     "not_defined",
        ...     "es",
        ...     var="foo"
        ... )
        "el nombre 'foo' no está definido"
    """

    def __init__(self) -> None:
        """Initialize error message templates."""
        self._templates = self._load_templates()

    def get_translation(
        self,
        error_type: str,
        template_key: str,
        target_lang: str,
        **variables: Any,
    ) -> str | None:
        """Get translated error message with variable substitution.

        Args:
            error_type: Type of error (e.g., "SyntaxError", "NameError")
            template_key: Specific error template key (e.g., "not_defined")
            target_lang: Target language code (e.g., "es", "ar")
            **variables: Variable values to substitute in template

        Returns:
            Translated error message with substituted variables,
            or None if template not found

        Example:
            >>> templates = ErrorMessageTemplates()
            >>> templates.get_translation(
            ...     "TypeError",
            ...     "not_callable",
            ...     "es",
            ...     var="int"
            ... )
            "el objeto 'int' no es invocable"
        """
        if error_type not in self._templates:
            return None

        error_templates = self._templates[error_type]
        if template_key not in error_templates:
            return None

        template = error_templates[template_key].get(target_lang)
        if template is None:
            # Fallback to English
            template = error_templates[template_key].get("en")

        if template is None:
            return None

        # Substitute variables in template
        try:
            return template.format(**variables)
        except (KeyError, ValueError):
            # Return template without substitution if variables don't match
            return template

    def match_error_message(
        self, error_type: str, message: str
    ) -> tuple[str | None, dict[str, str]]:
        """Match error message to template key and extract variables.

        Args:
            error_type: Type of error (e.g., "SyntaxError", "NameError")
            message: Actual error message to match

        Returns:
            Tuple of (template_key, variables) or (None, {}) if no match

        Example:
            >>> templates = ErrorMessageTemplates()
            >>> templates.match_error_message(
            ...     "NameError",
            ...     "name 'foo' is not defined"
            ... )
            ('not_defined', {'var': 'foo'})
        """
        if error_type not in self._templates:
            return None, {}

        error_templates = self._templates[error_type]

        # Try to match each template pattern
        for template_key, translations in error_templates.items():
            # Use English template as pattern
            en_template = translations.get("en", "")
            if not en_template:
                continue

            # Convert template to regex pattern
            # Replace {var} with named capture group
            pattern = re.escape(en_template)
            # Replace escaped placeholders with regex groups
            pattern = re.sub(r"\\{(\w+)\\}", r"(?P<\1>.+?)", pattern)

            # Try to match the message
            match = re.match(pattern, message)
            if match:
                return template_key, match.groupdict()

        return None, {}

    def has_error_type(self, error_type: str) -> bool:
        """Check if error type has templates.

        Args:
            error_type: Error type to check

        Returns:
            True if error type has templates
        """
        return error_type in self._templates

    def get_error_types(self) -> list[str]:
        """Get list of all error types with templates.

        Returns:
            List of error type names
        """
        return list(self._templates.keys())

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language codes ('en', 'es', 'ar')
        """
        return ["en", "es", "ar"]

    def _load_templates(self) -> dict[str, dict[str, dict[str, str]]]:
        """Load error message templates.

        Returns:
            Dictionary of error templates organized by:
            {error_type: {template_key: {language: template}}}
        """
        return {
            "SyntaxError": {
                "invalid_syntax": {
                    "en": "invalid syntax",
                    "es": "sintaxis inválida",
                    "ar": "بناء جملة غير صالح",
                },
                "expected_colon": {
                    "en": "expected ':'",
                    "es": "se esperaba ':'",
                    "ar": "متوقع ':'",
                },
                "eol_while_scanning": {
                    "en": "EOL while scanning string literal",
                    "es": "fin de línea al escanear literal de cadena",
                    "ar": "نهاية السطر أثناء فحص حرف السلسلة",
                },
                "eof_while_scanning": {
                    "en": "EOF while scanning triple-quoted string literal",
                    "es": "fin de archivo al escanear literal de cadena con comillas triples",
                    "ar": "نهاية الملف أثناء فحص حرف سلسلة ثلاثي الاقتباس",
                },
                "unmatched_parenthesis": {
                    "en": "unmatched ')'",
                    "es": "')' sin correspondencia",
                    "ar": "')' غير متطابق",
                },
                "invalid_character": {
                    "en": "invalid character in identifier",
                    "es": "carácter inválido en identificador",
                    "ar": "حرف غير صالح في المعرف",
                },
                "unexpected_eof": {
                    "en": "unexpected EOF while parsing",
                    "es": "fin de archivo inesperado durante el análisis",
                    "ar": "نهاية ملف غير متوقعة أثناء التحليل",
                },
                "invalid_decimal_literal": {
                    "en": "invalid decimal literal",
                    "es": "literal decimal inválido",
                    "ar": "حرف عشري غير صالح",
                },
            },
            "IndentationError": {
                "unexpected_indent": {
                    "en": "unexpected indent",
                    "es": "indentación inesperada",
                    "ar": "مسافة بادئة غير متوقعة",
                },
                "expected_indent": {
                    "en": "expected an indented block",
                    "es": "se esperaba un bloque indentado",
                    "ar": "متوقع كتلة ذات مسافة بادئة",
                },
                "unindent_does_not_match": {
                    "en": "unindent does not match any outer indentation level",
                    "es": "la desindentación no coincide con ningún nivel de indentación exterior",
                    "ar": "إلغاء المسافة البادئة لا يطابق أي مستوى مسافة بادئة خارجية",
                },
            },
            "NameError": {
                "not_defined": {
                    "en": "name '{var}' is not defined",
                    "es": "el nombre '{var}' no está definido",
                    "ar": "الاسم '{var}' غير معرف",
                },
                "free_variable": {
                    "en": "free variable '{var}' referenced before assignment in enclosing scope",
                    "es": "variable libre '{var}' referenciada antes de asignación en ámbito circundante",
                    "ar": "متغير حر '{var}' مشار إليه قبل الإسناد في النطاق المحيط",
                },
            },
            "TypeError": {
                "not_callable": {
                    "en": "'{var}' object is not callable",
                    "es": "el objeto '{var}' no es invocable",
                    "ar": "الكائن '{var}' غير قابل للاستدعاء",
                },
                "wrong_arg_count": {
                    "en": "takes {expected} positional argument but {actual} were given",
                    "es": "toma {expected} argumento posicional pero se dieron {actual}",
                    "ar": "يتطلب {expected} وسيطة موضعية ولكن تم إعطاء {actual}",
                },
                "wrong_arg_count_plural": {
                    "en": "takes {expected} positional arguments but {actual} were given",
                    "es": "toma {expected} argumentos posicionales pero se dieron {actual}",
                    "ar": "يتطلب {expected} وسائط موضعية ولكن تم إعطاء {actual}",
                },
                "unsupported_operand": {
                    "en": "unsupported operand type(s) for {op}: '{type1}' and '{type2}'",
                    "es": "tipo(s) de operando no soportado(s) para {op}: '{type1}' y '{type2}'",
                    "ar": "نوع (أنواع) معامل غير مدعوم لـ {op}: '{type1}' و '{type2}'",
                },
                "not_subscriptable": {
                    "en": "'{type}' object is not subscriptable",
                    "es": "el objeto '{type}' no es susceptible de subíndice",
                    "ar": "الكائن '{type}' غير قابل للفهرسة",
                },
                "unhashable_type": {
                    "en": "unhashable type: '{type}'",
                    "es": "tipo no hashable: '{type}'",
                    "ar": "نوع غير قابل للتجزئة: '{type}'",
                },
            },
            "AttributeError": {
                "no_attribute": {
                    "en": "'{obj}' object has no attribute '{attr}'",
                    "es": "el objeto '{obj}' no tiene el atributo '{attr}'",
                    "ar": "الكائن '{obj}' ليس له سمة '{attr}'",
                },
                "module_no_attribute": {
                    "en": "module '{module}' has no attribute '{attr}'",
                    "es": "el módulo '{module}' no tiene el atributo '{attr}'",
                    "ar": "الوحدة '{module}' ليس لها سمة '{attr}'",
                },
            },
            "ImportError": {
                "no_module": {
                    "en": "No module named '{module}'",
                    "es": "No hay módulo llamado '{module}'",
                    "ar": "لا توجد وحدة تسمى '{module}'",
                },
                "cannot_import_name": {
                    "en": "cannot import name '{name}' from '{module}'",
                    "es": "no se puede importar el nombre '{name}' desde '{module}'",
                    "ar": "لا يمكن استيراد الاسم '{name}' من '{module}'",
                },
            },
            "ModuleNotFoundError": {
                "no_module": {
                    "en": "No module named '{module}'",
                    "es": "No hay módulo llamado '{module}'",
                    "ar": "لا توجد وحدة تسمى '{module}'",
                },
            },
            "ValueError": {
                "invalid_literal": {
                    "en": "invalid literal for {type}() with base {base}: '{value}'",
                    "es": "literal inválido para {type}() con base {base}: '{value}'",
                    "ar": "حرفي غير صالح لـ {type}() مع القاعدة {base}: '{value}'",
                },
                "not_enough_values": {
                    "en": "not enough values to unpack (expected {expected}, got {actual})",
                    "es": "no hay suficientes valores para desempaquetar (se esperaban {expected}, se obtuvieron {actual})",
                    "ar": "قيم غير كافية لفك الحزمة (متوقع {expected}، حصل على {actual})",
                },
                "too_many_values": {
                    "en": "too many values to unpack (expected {expected})",
                    "es": "demasiados valores para desempaquetar (se esperaban {expected})",
                    "ar": "قيم كثيرة جدًا لفك الحزمة (متوقع {expected})",
                },
            },
            "KeyError": {
                "missing_key": {
                    "en": "'{key}'",
                    "es": "'{key}'",
                    "ar": "'{key}'",
                },
            },
            "IndexError": {
                "list_index": {
                    "en": "list index out of range",
                    "es": "índice de lista fuera de rango",
                    "ar": "فهرس القائمة خارج النطاق",
                },
                "tuple_index": {
                    "en": "tuple index out of range",
                    "es": "índice de tupla fuera de rango",
                    "ar": "فهرس المجموعة خارج النطاق",
                },
                "string_index": {
                    "en": "string index out of range",
                    "es": "índice de cadena fuera de rango",
                    "ar": "فهرس السلسلة خارج النطاق",
                },
            },
            "ZeroDivisionError": {
                "division_by_zero": {
                    "en": "division by zero",
                    "es": "división por cero",
                    "ar": "القسمة على صفر",
                },
                "modulo_by_zero": {
                    "en": "integer division or modulo by zero",
                    "es": "división entera o módulo por cero",
                    "ar": "قسمة الأعداد الصحيحة أو الباقي على صفر",
                },
            },
            "FileNotFoundError": {
                "no_file": {
                    "en": "No such file or directory: '{path}'",
                    "es": "No existe el archivo o directorio: '{path}'",
                    "ar": "لا يوجد ملف أو دليل: '{path}'",
                },
            },
            "KeyboardInterrupt": {
                "interrupted": {
                    "en": "interrupted by user",
                    "es": "interrumpido por el usuario",
                    "ar": "مقاطع من قبل المستخدم",
                },
            },
            "RecursionError": {
                "max_depth": {
                    "en": "maximum recursion depth exceeded",
                    "es": "profundidad máxima de recursión excedida",
                    "ar": "تجاوز الحد الأقصى لعمق التكرار",
                },
            },
            "RuntimeError": {
                "generator_already_executing": {
                    "en": "generator already executing",
                    "es": "generador ya en ejecución",
                    "ar": "المولد قيد التنفيذ بالفعل",
                },
                "dictionary_changed": {
                    "en": "dictionary changed size during iteration",
                    "es": "el diccionario cambió de tamaño durante la iteración",
                    "ar": "تغير حجم القاموس أثناء التكرار",
                },
            },
            "StopIteration": {
                "iteration_stopped": {
                    "en": "iteration stopped",
                    "es": "iteración detenida",
                    "ar": "توقف التكرار",
                },
            },
            "AssertionError": {
                "assertion_failed": {
                    "en": "assertion failed",
                    "es": "aserción falló",
                    "ar": "فشل التأكيد",
                },
                "assertion_failed_with_message": {
                    "en": "{message}",
                    "es": "{message}",
                    "ar": "{message}",
                },
            },
        }
