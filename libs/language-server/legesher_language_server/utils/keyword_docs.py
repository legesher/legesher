"""Python keyword documentation in multiple languages.

This module provides documentation for Python keywords with translations
for hover tooltips in the Language Server.
"""

import logging
import threading

from legesher_i18n import LanguagePackLoader

# TODO: Consider validating keys against legesher_i18n.scripts.translate.term_classifier
#       to ensure all Python keywords are documented and no deprecated keywords remain.
#       Currently missing Python 3.11+ (except*) and 3.12+ (type) keywords.

logger = logging.getLogger(__name__)

# Shared language pack loader with LRU cache (CORE-446)
# Uses lazy initialization to avoid import-time failures
_pack_loader: LanguagePackLoader | None = None

# Shared ParameterTranslation instance (lazy singleton)
# Loaded once and reused to avoid repeated translation loading on every hover
_param_translator: "ParameterTranslation | None" = None
_param_translator_lock = threading.Lock()


def _get_pack_loader() -> LanguagePackLoader:
    """Get or create the shared language pack loader with error handling.

    Uses lazy initialization to avoid module import failures if language
    pack directory is missing or permissions are incorrect (CORE-446 security).

    Returns:
        LanguagePackLoader instance

    Note:
        On initialization failure, returns a loader with empty pack root
        to allow graceful degradation rather than crashing.
    """
    global _pack_loader
    if _pack_loader is None:
        _pack_loader = LanguagePackLoader()
    return _pack_loader


def get_param_translator() -> "ParameterTranslation":
    """Get or create the shared ParameterTranslation instance.

    Uses lazy initialization to load translations once and reuse across all
    hover requests. This avoids repeated loading of 174+ translations.

    Returns:
        Shared ParameterTranslation instance

    Note:
        Thread-safe with double-check locking pattern to prevent race conditions
        during concurrent async task execution.
    """
    global _param_translator
    # Fast path - already initialized
    if _param_translator is not None:
        return _param_translator

    # Slow path - need to initialize with lock
    with _param_translator_lock:
        # Double-check: another thread might have initialized while we waited
        if _param_translator is None:
            _param_translator = ParameterTranslation()

    return _param_translator


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

# Python builtin function documentation (English, Spanish, Arabic)
# These provide translated descriptions for hover tooltips on builtin functions
PYTHON_BUILTIN_DOCS = {
    "print": {
        "en": "Print objects to the text stream file, separated by sep and followed by end",
        "es": "Imprimir objetos en el flujo de texto, separados por sep y seguidos por end",
        "ar": "طباعة الكائنات إلى تيار النص، مفصولة بـ sep ومتبوعة بـ end",
    },
    "input": {
        "en": "Read a string from standard input",
        "es": "Leer una cadena desde la entrada estándar",
        "ar": "قراءة سلسلة من الإدخال القياسي",
    },
    "len": {
        "en": "Return the number of items in a container",
        "es": "Devolver el número de elementos en un contenedor",
        "ar": "إرجاع عدد العناصر في حاوية",
    },
    "range": {
        "en": "Return a sequence of numbers",
        "es": "Devolver una secuencia de números",
        "ar": "إرجاع تسلسل من الأرقام",
    },
    "type": {
        "en": "Return the type of an object",
        "es": "Devolver el tipo de un objeto",
        "ar": "إرجاع نوع الكائن",
    },
    "int": {
        "en": "Convert to integer",
        "es": "Convertir a entero",
        "ar": "تحويل إلى عدد صحيح",
    },
    "float": {
        "en": "Convert to floating point number",
        "es": "Convertir a número de punto flotante",
        "ar": "تحويل إلى رقم عشري",
    },
    "str": {
        "en": "Convert to string",
        "es": "Convertir a cadena de texto",
        "ar": "تحويل إلى سلسلة نصية",
    },
    "bool": {
        "en": "Convert to boolean",
        "es": "Convertir a booleano",
        "ar": "تحويل إلى قيمة منطقية",
    },
    "list": {
        "en": "Create a list or convert to list",
        "es": "Crear una lista o convertir a lista",
        "ar": "إنشاء قائمة أو تحويل إلى قائمة",
    },
    "dict": {
        "en": "Create a dictionary or convert to dictionary",
        "es": "Crear un diccionario o convertir a diccionario",
        "ar": "إنشاء قاموس أو تحويل إلى قاموس",
    },
    "set": {
        "en": "Create a set or convert to set",
        "es": "Crear un conjunto o convertir a conjunto",
        "ar": "إنشاء مجموعة أو تحويل إلى مجموعة",
    },
    "tuple": {
        "en": "Create a tuple or convert to tuple",
        "es": "Crear una tupla o convertir a tupla",
        "ar": "إنشاء صف أو تحويل إلى صف",
    },
    "open": {
        "en": "Open a file and return a file object",
        "es": "Abrir un archivo y devolver un objeto de archivo",
        "ar": "فتح ملف وإرجاع كائن ملف",
    },
    "abs": {
        "en": "Return the absolute value of a number",
        "es": "Devolver el valor absoluto de un número",
        "ar": "إرجاع القيمة المطلقة لرقم",
    },
    "sum": {
        "en": "Return the sum of all items in an iterable",
        "es": "Devolver la suma de todos los elementos en un iterable",
        "ar": "إرجاع مجموع كل العناصر في قابل للتكرار",
    },
    "min": {
        "en": "Return the smallest item",
        "es": "Devolver el elemento más pequeño",
        "ar": "إرجاع أصغر عنصر",
    },
    "max": {
        "en": "Return the largest item",
        "es": "Devolver el elemento más grande",
        "ar": "إرجاع أكبر عنصر",
    },
    "sorted": {
        "en": "Return a new sorted list",
        "es": "Devolver una nueva lista ordenada",
        "ar": "إرجاع قائمة جديدة مرتبة",
    },
    "reversed": {
        "en": "Return a reverse iterator",
        "es": "Devolver un iterador inverso",
        "ar": "إرجاع مكرر معكوس",
    },
    "enumerate": {
        "en": "Return an enumerate object with index and value pairs",
        "es": "Devolver un objeto enumerate con pares de índice y valor",
        "ar": "إرجاع كائن enumerate مع أزواج الفهرس والقيمة",
    },
    "zip": {
        "en": "Return an iterator of tuples from multiple iterables",
        "es": "Devolver un iterador de tuplas de múltiples iterables",
        "ar": "إرجاع مكرر من الصفوف من عدة قوابل للتكرار",
    },
    "map": {
        "en": "Apply function to every item in iterable",
        "es": "Aplicar función a cada elemento en el iterable",
        "ar": "تطبيق دالة على كل عنصر في القابل للتكرار",
    },
    "filter": {
        "en": "Filter items from iterable using a function",
        "es": "Filtrar elementos del iterable usando una función",
        "ar": "تصفية العناصر من القابل للتكرار باستخدام دالة",
    },
    "any": {
        "en": "Return True if any element is true",
        "es": "Devolver True si algún elemento es verdadero",
        "ar": "إرجاع True إذا كان أي عنصر صحيحاً",
    },
    "all": {
        "en": "Return True if all elements are true",
        "es": "Devolver True si todos los elementos son verdaderos",
        "ar": "إرجاع True إذا كانت كل العناصر صحيحة",
    },
    "isinstance": {
        "en": "Check if object is an instance of a class",
        "es": "Verificar si el objeto es una instancia de una clase",
        "ar": "التحقق مما إذا كان الكائن مثيلاً لفئة",
    },
    "hasattr": {
        "en": "Check if object has an attribute",
        "es": "Verificar si el objeto tiene un atributo",
        "ar": "التحقق مما إذا كان للكائن سمة",
    },
    "getattr": {
        "en": "Get attribute value from object",
        "es": "Obtener valor de atributo de un objeto",
        "ar": "الحصول على قيمة سمة من كائن",
    },
    "setattr": {
        "en": "Set attribute value on object",
        "es": "Establecer valor de atributo en un objeto",
        "ar": "تعيين قيمة سمة على كائن",
    },
    "round": {
        "en": "Round a number to given precision",
        "es": "Redondear un número a la precisión dada",
        "ar": "تقريب رقم إلى الدقة المحددة",
    },
    "ord": {
        "en": "Return Unicode code point for character",
        "es": "Devolver punto de código Unicode del carácter",
        "ar": "إرجاع نقطة رمز يونيكود للحرف",
    },
    "chr": {
        "en": "Return character from Unicode code point",
        "es": "Devolver carácter del punto de código Unicode",
        "ar": "إرجاع حرف من نقطة رمز يونيكود",
    },
    "hex": {
        "en": "Convert integer to hexadecimal string",
        "es": "Convertir entero a cadena hexadecimal",
        "ar": "تحويل عدد صحيح إلى سلسلة سداسية عشرية",
    },
    "bin": {
        "en": "Convert integer to binary string",
        "es": "Convertir entero a cadena binaria",
        "ar": "تحويل عدد صحيح إلى سلسلة ثنائية",
    },
    "oct": {
        "en": "Convert integer to octal string",
        "es": "Convertir entero a cadena octal",
        "ar": "تحويل عدد صحيح إلى سلسلة ثمانية",
    },
    "format": {
        "en": "Format value using format specification",
        "es": "Formatear valor usando especificación de formato",
        "ar": "تنسيق القيمة باستخدام مواصفات التنسيق",
    },
    "repr": {
        "en": "Return printable representation of object",
        "es": "Devolver representación imprimible del objeto",
        "ar": "إرجاع تمثيل قابل للطباعة للكائن",
    },
    "id": {
        "en": "Return identity (memory address) of object",
        "es": "Devolver identidad (dirección de memoria) del objeto",
        "ar": "إرجاع هوية (عنوان الذاكرة) للكائن",
    },
    "help": {
        "en": "Invoke the built-in help system",
        "es": "Invocar el sistema de ayuda integrado",
        "ar": "استدعاء نظام المساعدة المدمج",
    },
    "dir": {
        "en": "List valid attributes of object",
        "es": "Listar atributos válidos del objeto",
        "ar": "إدراج السمات الصالحة للكائن",
    },
    "vars": {
        "en": "Return __dict__ attribute of object",
        "es": "Devolver atributo __dict__ del objeto",
        "ar": "إرجاع سمة __dict__ للكائن",
    },
    "globals": {
        "en": "Return dictionary of global symbol table",
        "es": "Devolver diccionario de tabla de símbolos globales",
        "ar": "إرجاع قاموس جدول الرموز العامة",
    },
    "locals": {
        "en": "Return dictionary of local symbol table",
        "es": "Devolver diccionario de tabla de símbolos locales",
        "ar": "إرجاع قاموس جدول الرموز المحلية",
    },
    "eval": {
        "en": "Evaluate Python expression",
        "es": "Evaluar expresión de Python",
        "ar": "تقييم تعبير بايثون",
    },
    "exec": {
        "en": "Execute Python code dynamically",
        "es": "Ejecutar código Python dinámicamente",
        "ar": "تنفيذ كود بايثون ديناميكياً",
    },
    "compile": {
        "en": "Compile source into code object",
        "es": "Compilar fuente en objeto de código",
        "ar": "ترجمة المصدر إلى كائن رمز",
    },
    "callable": {
        "en": "Check if object is callable",
        "es": "Verificar si el objeto es invocable",
        "ar": "التحقق مما إذا كان الكائن قابلاً للاستدعاء",
    },
    "iter": {
        "en": "Return iterator object",
        "es": "Devolver objeto iterador",
        "ar": "إرجاع كائن مكرر",
    },
    "next": {
        "en": "Get next item from iterator",
        "es": "Obtener siguiente elemento del iterador",
        "ar": "الحصول على العنصر التالي من المكرر",
    },
    "slice": {
        "en": "Create a slice object",
        "es": "Crear un objeto slice",
        "ar": "إنشاء كائن شريحة",
    },
    "property": {
        "en": "Return property attribute",
        "es": "Devolver atributo de propiedad",
        "ar": "إرجاع سمة خاصية",
    },
    "staticmethod": {
        "en": "Transform method into static method",
        "es": "Transformar método en método estático",
        "ar": "تحويل طريقة إلى طريقة ثابتة",
    },
    "classmethod": {
        "en": "Transform method into class method",
        "es": "Transformar método en método de clase",
        "ar": "تحويل طريقة إلى طريقة فئة",
    },
    "super": {
        "en": "Return proxy object for parent class",
        "es": "Devolver objeto proxy para clase padre",
        "ar": "إرجاع كائن وكيل للفئة الأم",
    },
    "object": {
        "en": "Base class for all classes",
        "es": "Clase base para todas las clases",
        "ar": "الفئة الأساسية لجميع الفئات",
    },
    "bytes": {
        "en": "Create immutable bytes object",
        "es": "Crear objeto bytes inmutable",
        "ar": "إنشاء كائن بايتات غير قابل للتغيير",
    },
    "bytearray": {
        "en": "Create mutable bytes object",
        "es": "Crear objeto bytes mutable",
        "ar": "إنشاء كائن بايتات قابل للتغيير",
    },
    "memoryview": {
        "en": "Create memory view object",
        "es": "Crear objeto de vista de memoria",
        "ar": "إنشاء كائن عرض الذاكرة",
    },
    "frozenset": {
        "en": "Create immutable set",
        "es": "Crear conjunto inmutable",
        "ar": "إنشاء مجموعة غير قابلة للتغيير",
    },
    "complex": {
        "en": "Create complex number",
        "es": "Crear número complejo",
        "ar": "إنشاء رقم مركب",
    },
    "pow": {
        "en": "Return base raised to power",
        "es": "Devolver base elevada a potencia",
        "ar": "إرجاع الأساس مرفوعاً للقوة",
    },
    "divmod": {
        "en": "Return quotient and remainder",
        "es": "Devolver cociente y resto",
        "ar": "إرجاع الحاصل والباقي",
    },
    "hash": {
        "en": "Return hash value of object",
        "es": "Devolver valor hash del objeto",
        "ar": "إرجاع قيمة التجزئة للكائن",
    },
    "ascii": {
        "en": "Return ASCII representation",
        "es": "Devolver representación ASCII",
        "ar": "إرجاع تمثيل ASCII",
    },
    "delattr": {
        "en": "Delete attribute from object",
        "es": "Eliminar atributo del objeto",
        "ar": "حذف سمة من الكائن",
    },
    "issubclass": {
        "en": "Check if class is subclass of another",
        "es": "Verificar si la clase es subclase de otra",
        "ar": "التحقق مما إذا كانت الفئة فئة فرعية من أخرى",
    },
    "breakpoint": {
        "en": "Drop into debugger at call site",
        "es": "Entrar al depurador en el sitio de llamada",
        "ar": "الدخول إلى مصحح الأخطاء في موقع الاستدعاء",
    },
    "Exception": {
        "en": "Base class for all exceptions",
        "es": "Clase base para todas las excepciones",
        "ar": "الفئة الأساسية لجميع الاستثناءات",
    },
    "ValueError": {
        "en": "Raised when argument has wrong value",
        "es": "Se lanza cuando el argumento tiene un valor incorrecto",
        "ar": "يُرفع عندما يكون للوسيط قيمة خاطئة",
    },
    "TypeError": {
        "en": "Raised when argument has wrong type",
        "es": "Se lanza cuando el argumento tiene un tipo incorrecto",
        "ar": "يُرفع عندما يكون للوسيط نوع خاطئ",
    },
    "KeyError": {
        "en": "Raised when key is not found in dictionary",
        "es": "Se lanza cuando la clave no se encuentra en el diccionario",
        "ar": "يُرفع عندما لا يُعثر على المفتاح في القاموس",
    },
    "IndexError": {
        "en": "Raised when index is out of range",
        "es": "Se lanza cuando el índice está fuera de rango",
        "ar": "يُرفع عندما يكون الفهرس خارج النطاق",
    },
    "AttributeError": {
        "en": "Raised when attribute reference fails",
        "es": "Se lanza cuando falla la referencia de atributo",
        "ar": "يُرفع عندما يفشل مرجع السمة",
    },
    "NameError": {
        "en": "Raised when name is not found",
        "es": "Se lanza cuando no se encuentra el nombre",
        "ar": "يُرفع عندما لا يُعثر على الاسم",
    },
    "FileNotFoundError": {
        "en": "Raised when file is not found",
        "es": "Se lanza cuando no se encuentra el archivo",
        "ar": "يُرفع عندما لا يُعثر على الملف",
    },
    "ZeroDivisionError": {
        "en": "Raised when dividing by zero",
        "es": "Se lanza cuando se divide por cero",
        "ar": "يُرفع عند القسمة على صفر",
    },
    "ImportError": {
        "en": "Raised when import fails",
        "es": "Se lanza cuando falla la importación",
        "ar": "يُرفع عندما يفشل الاستيراد",
    },
    "RuntimeError": {
        "en": "Raised when error doesn't fall into other categories",
        "es": "Se lanza cuando el error no cae en otras categorías",
        "ar": "يُرفع عندما لا يقع الخطأ في فئات أخرى",
    },
    "StopIteration": {
        "en": "Raised to signal end of iteration",
        "es": "Se lanza para señalar el fin de la iteración",
        "ar": "يُرفع للإشارة إلى نهاية التكرار",
    },
}

# Python function parameter translations (English -> target language)
# These are used to translate function signatures in hover tooltips
PYTHON_PARAMETER_TRANSLATIONS = {
    # Common parameters across many functions
    "args": {
        "es": "argumentos",
        "ar": "الوسائط",
    },
    "kwargs": {
        "es": "argumentos_clave",
        "ar": "وسائط_مفتاحية",
    },
    "kwds": {
        "es": "palabras_clave",
        "ar": "كلمات_مفتاحية",
    },
    "kws": {
        "es": "claves",
        "ar": "مفاتيح",
    },
    # print() parameters
    "sep": {
        "es": "separador",
        "ar": "فاصل",
    },
    "end": {
        "es": "fin",
        "ar": "نهاية",
    },
    "file": {
        "es": "archivo",
        "ar": "ملف",
    },
    "flush": {
        "es": "vaciar",
        "ar": "تفريغ",
    },
    # open() parameters
    "mode": {
        "es": "modo",
        "ar": "وضع",
    },
    "buffering": {
        "es": "almacenamiento",
        "ar": "تخزين_مؤقت",
    },
    "encoding": {
        "es": "codificación",
        "ar": "ترميز",
    },
    "errors": {
        "es": "errores",
        "ar": "أخطاء",
    },
    "newline": {
        "es": "nueva_línea",
        "ar": "سطر_جديد",
    },
    "closefd": {
        "es": "cerrar_fd",
        "ar": "إغلاق_fd",
    },
    "opener": {
        "es": "abridor",
        "ar": "فاتح",
    },
    # sorted(), min(), max() parameters
    "key": {
        "es": "clave",
        "ar": "مفتاح",
    },
    "reverse": {
        "es": "invertir",
        "ar": "عكس",
    },
    "default": {
        "es": "predeterminado",
        "ar": "افتراضي",
    },
    # Iterable-related parameters
    "iterable": {
        "es": "iterable",
        "ar": "قابل_للتكرار",
    },
    "iterables": {
        "es": "iterables",
        "ar": "قوابل_للتكرار",
    },
    "sequence": {
        "es": "secuencia",
        "ar": "تسلسل",
    },
    "start": {
        "es": "inicio",
        "ar": "بداية",
    },
    "stop": {
        "es": "fin",
        "ar": "نهاية",
    },
    "step": {
        "es": "paso",
        "ar": "خطوة",
    },
    # Function-related parameters
    "function": {
        "es": "función",
        "ar": "دالة",
    },
    "func": {
        "es": "func",
        "ar": "دالة",
    },
    "callable": {
        "es": "invocable",
        "ar": "قابل_للاستدعاء",
    },
    # Object-related parameters
    "obj": {
        "es": "objeto",
        "ar": "كائن",
    },
    "object": {
        "es": "objeto",
        "ar": "كائن",
    },
    "cls": {
        "es": "clase",
        "ar": "فئة",
    },
    "class_or_tuple": {
        "es": "clase_o_tupla",
        "ar": "فئة_أو_صف",
    },
    # Attribute-related parameters
    "name": {
        "es": "nombre",
        "ar": "اسم",
    },
    "value": {
        "es": "valor",
        "ar": "قيمة",
    },
    # Numeric parameters
    "x": {
        "es": "x",
        "ar": "س",
    },
    "y": {
        "es": "y",
        "ar": "ص",
    },
    "number": {
        "es": "número",
        "ar": "رقم",
    },
    "ndigits": {
        "es": "n_dígitos",
        "ar": "عدد_الأرقام",
    },
    "base": {
        "es": "base",
        "ar": "أساس",
    },
    "exp": {
        "es": "exponente",
        "ar": "أُس",
    },
    "mod": {
        "es": "módulo",
        "ar": "معامل",
    },
    # complex() parameters
    "real": {
        "es": "real",
        "ar": "حقيقي",
    },
    "imag": {
        "es": "imaginario",
        "ar": "تخيلي",
    },
    # String-related parameters
    "chars": {
        "es": "caracteres",
        "ar": "أحرف",
    },
    "width": {
        "es": "ancho",
        "ar": "عرض",
    },
    "fillchar": {
        "es": "carácter_relleno",
        "ar": "حرف_ملء",
    },
    "old": {
        "es": "antiguo",
        "ar": "قديم",
    },
    "new": {
        "es": "nuevo",
        "ar": "جديد",
    },
    "count": {
        "es": "conteo",
        "ar": "عدد",
    },
    "maxsplit": {
        "es": "máx_divisiones",
        "ar": "أقصى_تقسيم",
    },
    # input() parameters
    "prompt": {
        "es": "mensaje",
        "ar": "رسالة",
    },
    # format() parameters
    "format_spec": {
        "es": "especificación_formato",
        "ar": "مواصفات_التنسيق",
    },
    # compile() parameters
    "source": {
        "es": "fuente",
        "ar": "مصدر",
    },
    "filename": {
        "es": "nombre_archivo",
        "ar": "اسم_الملف",
    },
    "flags": {
        "es": "banderas",
        "ar": "أعلام",
    },
    "dont_inherit": {
        "es": "no_heredar",
        "ar": "لا_ترث",
    },
    "optimize": {
        "es": "optimizar",
        "ar": "تحسين",
    },
    # eval/exec parameters
    "globals": {
        "es": "globales",
        "ar": "عامة",
    },
    "locals": {
        "es": "locales",
        "ar": "محلية",
    },
    "closure": {
        "es": "clausura",
        "ar": "إغلاق",
    },
    # property() parameters
    "fget": {
        "es": "f_obtener",
        "ar": "د_الحصول",
    },
    "fset": {
        "es": "f_establecer",
        "ar": "د_التعيين",
    },
    "fdel": {
        "es": "f_eliminar",
        "ar": "د_الحذف",
    },
    "doc": {
        "es": "documentación",
        "ar": "توثيق",
    },
    # zip() parameters
    "strict": {
        "es": "estricto",
        "ar": "صارم",
    },
    # enumerate() - already have start
    # chr/ord parameters
    "i": {
        "es": "i",
        "ar": "ع",
    },
    "character": {
        "es": "carácter",
        "ar": "حرف",
    },
    # set operations
    "other": {
        "es": "otro",
        "ar": "آخر",
    },
    "others": {
        "es": "otros",
        "ar": "آخرون",
    },
    # list operations
    "index": {
        "es": "índice",
        "ar": "فهرس",
    },
}


class ParameterTranslation:
    """Provides comprehensive translations for Python function signatures.

    This class translates all components in function signatures for hover tooltips:
    - Parameter names (sep, end, file, etc.)
    - Keyword constants (None, True, False, lambda)
    - Builtin types (str, int, dict, list, etc.)
    - Exception types (ValueError, TypeError, etc.)
    - Functions (print, len, range, etc.)

    Translations are lazily loaded per language on first use to minimize memory
    footprint and startup time.
    """

    def __init__(self) -> None:
        """Initialize parameter translation with lazy loading."""
        self._translations = PYTHON_PARAMETER_TRANSLATIONS
        # Lazy cache: translations loaded on-demand per language
        self._keyword_constants_cache: dict[str, dict[str, str]] = {}
        self._cache_lock = threading.Lock()

    def _load_language_pack(self, language: str) -> dict[str, str]:
        """Load keyword/builtin/exception translations for a specific language.

        Lazily loads translations only when needed for a specific language.
        Results are cached to avoid repeated loading.

        Args:
            language: Target language code ('es', 'ar', 'zh', etc.)

        Returns:
            Dictionary mapping English terms to translated terms for this language.
            Example: {"None": "nulo", "str": "cadena", "ValueError": "error de valor"}

        Raises:
            ImportError: If language pack cannot be loaded
            AttributeError: If pack structure is invalid
        """
        # Check cache first
        if language in self._keyword_constants_cache:
            return self._keyword_constants_cache[language]

        # Load with lock to prevent concurrent loads of same language
        with self._cache_lock:
            # Double-check after acquiring lock
            if language in self._keyword_constants_cache:
                return self._keyword_constants_cache[language]

            translations = {}
            loader = _get_pack_loader()

            try:
                pack = loader.load(language=language, target="python", version="3.10")

                if not pack:
                    logger.warning(f"No language pack found for {language}")
                    self._keyword_constants_cache[language] = {}
                    return {}

                # Load keywords section: None, True, False, lambda, and, or, etc.
                if pack.keywords:
                    translations.update(pack.keywords)

                # Load builtins section: str, int, dict, print, len, etc.
                if pack.builtins:
                    translations.update(pack.builtins)

                # Load exceptions section: ValueError, TypeError, etc.
                if hasattr(pack, "exceptions") and pack.exceptions:
                    translations.update(pack.exceptions)

                logger.debug(f"Loaded {len(translations)} translations for {language}")

            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to load language pack for {language}: {e}")
                translations = {}
            except Exception as e:
                logger.error(f"Unexpected error loading {language} pack: {e}", exc_info=True)
                translations = {}

            # Cache even if empty to avoid repeated failed loads
            self._keyword_constants_cache[language] = translations
            return translations

    def translate(self, param: str, language: str) -> str:
        """Translate a parameter name to target language.

        Args:
            param: Parameter name in English (e.g., 'sep', 'end')
            language: Target language code ('es', 'ar')

        Returns:
            Translated parameter name, or original if no translation exists

        Example:
            >>> trans = ParameterTranslation()
            >>> trans.translate("sep", "es")
            'separador'
            >>> trans.translate("flush", "ar")
            'تفريغ'
        """
        if param not in self._translations:
            return param

        return self._translations[param].get(language, param)

    def translate_signature(self, signature_str: str, language: str) -> str:
        """Translate all components of a function signature to the target language.

        Performs comprehensive translation in two phases:
        1. Parameter names: sep → separador, end → fin, file → archivo
        2. Default values: None → nulo, dict → diccionario, ValueError → error de valor

        Supports translation of:
        - Parameter names (sep, end, file, flush, etc.)
        - Keyword constants (None, True, False, lambda)
        - Builtin types (str, int, dict, list, bool, etc.)
        - Exception types (ValueError, TypeError, ConnectionError, etc.)
        - Any item defined in language pack's keywords, builtins, or exceptions

        Args:
            signature_str: Function signature to translate
                (e.g., "(sep=' ', end='\\n', file=None, factory=dict)")
            language: Target language code ('es', 'ar', 'zh', etc.)

        Returns:
            Fully translated signature with all parameters and values localized

        Examples:
            >>> trans = ParameterTranslation()
            >>> trans.translate_signature("(sep=' ', end='\\n', file=None)", "es")
            "(separador=' ', fin='\\n', archivo=nulo)"
            >>> trans.translate_signature("(factory=dict, default=False)", "es")
            "(fábrica=diccionario, predeterminado=falso)"
            >>> trans.translate_signature("(exc_type=ValueError, retries=3)", "es")
            "(tipo_exc=error de valor, reintentos=3)"

        Note:
            Uses case-insensitive matching for default values to handle both
            Python's CamelCase (ValueError) and language pack lowercase (valueerror).
        """
        import re

        result = signature_str

        # Phase 1: Translate parameter names (sep, end, file, etc.)
        # Sort by length (longest first) to avoid partial replacements (e.g., 'sep' before 's')
        sorted_params = sorted(self._translations.keys(), key=len, reverse=True)

        for param in sorted_params:
            translation = self._translations[param].get(language)
            if translation:
                # Match parameter as a complete word with optional * or **
                # Handles: param=value, param, *param, **param
                # Captures: (\*{0,2})  - optional * or **
                #          (param)     - the parameter name
                #          (\s*[=,)])  - followed by =, comma, or closing paren
                pattern = rf"(\*{{0,2}})({re.escape(param)})(\s*[=,\)])"
                replacement = rf"\1{translation}\3"
                result = re.sub(pattern, replacement, result)

        # Phase 2: Translate default values (None, dict, ValueError, etc.)
        # Lazy-load translations for the target language only
        keyword_translations = self._load_language_pack(language)

        # Uses case-insensitive matching to handle Python's CamelCase vs pack lowercase
        # Example: "ValueError" in code matches "valueerror" in language pack
        for const, translation in keyword_translations.items():
            if translation:
                # Match default value after '=' sign
                # Captures: (=\s*)      - equals sign with optional whitespace
                #          (const)      - the constant/type name
                #          (\s*[,)])    - followed by comma or closing paren
                pattern = rf"(=\s*)({re.escape(const)})(\s*[,\)])"
                replacement = rf"\1{translation}\3"
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def get_all_parameters(self) -> list[str]:
        """Get list of all translatable parameters.

        Returns:
            List of parameter names with translations
        """
        return list(self._translations.keys())

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language codes ('es', 'ar')
        """
        return ["es", "ar"]


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

    def get_keyword_translation(self, keyword: str, target_lang: str) -> str | None:
        """Get keyword translation from English to target language.

        Uses cached LanguagePackLoader for performance (CORE-446).
        All language packs are loaded once and cached in memory.

        Args:
            keyword: English keyword (e.g., 'def', 'class')
            target_lang: Target language code ('es', 'ar', 'zh')

        Returns:
            Translated keyword or None if not available

        Error Handling:
            All errors are caught and logged, never raises exceptions.
            Falls back to None (English keyword) on any error.

        Example:
            >>> docs = KeywordDocumentation()
            >>> docs.get_keyword_translation("def", "es")
            'definir'
            >>> docs.get_keyword_translation("class", "ar")
            'صنف'
            >>> docs.get_keyword_translation("def", "nonexistent")  # Missing pack
            None  # Logs warning
        """
        try:
            # Load language pack using cached loader (CORE-446)
            pack = _get_pack_loader().load(language=target_lang, target="python", version="3.10")
            translation = pack.keywords.get(keyword)

            if translation:
                logger.debug(f"Found translation for '{keyword}' in {target_lang}: '{translation}'")

            return translation

        except Exception as e:
            # Log warning and fall back to None (English keywords)
            logger.warning(
                f"Failed to load keyword translation for '{keyword}' in '{target_lang}': {e}"
            )
            return None


class BuiltinDocumentation:
    """Provides documentation for Python builtins in multiple languages.

    This class provides quick access to builtin documentation for hover
    tooltips, with support for English, Spanish, and Arabic.
    """

    def __init__(self) -> None:
        """Initialize builtin documentation."""
        self._docs = PYTHON_BUILTIN_DOCS

    def get(self, builtin: str, language: str = "en") -> str | None:
        """Get documentation for a builtin in specified language.

        Args:
            builtin: Python builtin name (e.g., 'print', 'len', 'list')
            language: Target language code ('en', 'es', 'ar')

        Returns:
            Documentation string or None if builtin/language not found

        Example:
            >>> docs = BuiltinDocumentation()
            >>> docs.get("print", "es")
            'Imprimir objetos en el flujo de texto, separados por sep y seguidos por end'
            >>> docs.get("len", "ar")
            'إرجاع عدد العناصر في حاوية'
        """
        if builtin not in self._docs:
            return None

        builtin_doc = self._docs[builtin]
        return builtin_doc.get(language)

    def has_builtin(self, builtin: str) -> bool:
        """Check if builtin has documentation.

        Args:
            builtin: Python builtin name to check

        Returns:
            True if builtin has documentation
        """
        return builtin in self._docs

    def get_all_builtins(self) -> list[str]:
        """Get list of all documented builtins.

        Returns:
            List of Python builtins with documentation
        """
        return list(self._docs.keys())

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language codes ('en', 'es', 'ar')
        """
        return ["en", "es", "ar"]
