import * as vscode from 'vscode';

/**
 * Translate a Python document to the target language.
 *
 * For MVP, this is a placeholder that returns a simulated translation.
 * In production, this will integrate with the LSP server to perform actual translation.
 *
 * @param document The document to translate
 * @param targetLanguage The target language code (e.g., 'es', 'ar', 'zh')
 * @returns The translated code as a string
 */
export async function translateDocument(
    document: vscode.TextDocument,
    targetLanguage: string
): Promise<string> {
    // Validate document is Python
    if (document.languageId !== 'python') {
        throw new Error('Translation only supports Python files');
    }

    const originalCode = document.getText();

    // Check if document is empty
    if (!originalCode.trim()) {
        return originalCode;
    }

    try {
        // TODO: Integrate with LSP server for actual translation
        // For now, return a simulated translation for demo purposes
        const translated = await simulateTranslation(originalCode, targetLanguage);
        return translated;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw new Error(`Translation failed: ${errorMessage}`);
    }
}

/**
 * Translation mapping for Python keywords and built-in functions
 * Organized by language and keyword category for maintainability
 */
const KEYWORD_TRANSLATIONS: { [lang: string]: { [keyword: string]: string } } = {
    es: {
        // Control flow keywords
        if: 'si',
        else: 'sino',
        elif: 'sinosi',
        for: 'para',
        while: 'mientras',
        break: 'romper',
        continue: 'continuar',
        pass: 'pasar',
        // Function/class definition
        def: 'definir',
        class: 'clase',
        return: 'retornar',
        yield: 'ceder',
        lambda: 'lambda',
        // Import statements
        import: 'importar',
        from: 'de',
        as: 'como',
        // Exception handling
        try: 'intentar',
        except: 'excepto',
        finally: 'finalmente',
        raise: 'elevar',
        assert: 'afirmar',
        // Context managers
        with: 'con',
        // Boolean values
        True: 'Verdadero',
        False: 'Falso',
        None: 'Ninguno',
        // Logical operators
        and: 'y',
        or: 'o',
        not: 'no',
        // Membership/identity
        in: 'en',
        is: 'es',
        // Async/await
        async: 'asíncrono',
        await: 'esperar',
        // Scope keywords
        global: 'global',
        nonlocal: 'nolocal',
        del: 'eliminar',
        // Built-in functions
        print: 'imprimir',
        len: 'longitud',
        range: 'rango',
        str: 'cadena',
        int: 'entero',
        float: 'flotante',
        bool: 'booleano',
        list: 'lista',
        dict: 'diccionario',
        set: 'conjunto',
        tuple: 'tupla',
        open: 'abrir',
        input: 'entrada',
        type: 'tipo',
        sum: 'suma',
        max: 'máximo',
        min: 'mínimo',
        abs: 'absoluto',
        round: 'redondear',
        zip: 'cremallera',
        map: 'mapear',
        filter: 'filtrar',
        enumerate: 'enumerar',
        sorted: 'ordenado',
        reversed: 'invertido',
        all: 'todos',
        any: 'alguno'
    },
    ar: {
        // Control flow keywords
        if: 'إذا',
        else: 'وإلا',
        elif: 'أوإذا',
        for: 'لكل',
        while: 'بينما',
        break: 'كسر',
        continue: 'استمرار',
        pass: 'تمرير',
        // Function/class definition
        def: 'تعريف',
        class: 'صنف',
        return: 'إرجاع',
        yield: 'ناتج',
        lambda: 'لامدا',
        // Import statements
        import: 'استيراد',
        from: 'من',
        as: 'كـ',
        // Exception handling
        try: 'محاولة',
        except: 'استثناء',
        finally: 'أخيرا',
        raise: 'رفع',
        assert: 'تأكيد',
        // Context managers
        with: 'مع',
        // Boolean values
        True: 'صحيح',
        False: 'خطأ',
        None: 'لاشيء',
        // Logical operators
        and: 'و',
        or: 'أو',
        not: 'ليس',
        // Membership/identity
        in: 'في',
        is: 'هو',
        // Async/await
        async: 'غيرمتزامن',
        await: 'انتظار',
        // Scope keywords
        global: 'عام',
        nonlocal: 'غيرمحلي',
        del: 'حذف',
        // Built-in functions
        print: 'طباعة',
        len: 'طول',
        range: 'نطاق',
        str: 'نص',
        int: 'صحيح',
        float: 'عشري',
        bool: 'منطقي',
        list: 'قائمة',
        dict: 'قاموس',
        set: 'مجموعة',
        tuple: 'صف',
        open: 'فتح',
        input: 'إدخال',
        type: 'نوع',
        sum: 'مجموع',
        max: 'أقصى',
        min: 'أدنى',
        abs: 'مطلق',
        round: 'تقريب',
        zip: 'دمج',
        map: 'تطبيق',
        filter: 'تصفية',
        enumerate: 'تعداد',
        sorted: 'مرتب',
        reversed: 'معكوس',
        all: 'الكل',
        any: 'أي'
    },
    zh: {
        // Control flow keywords
        if: '如果',
        else: '否则',
        elif: '或如果',
        for: '对于',
        while: '当',
        break: '中断',
        continue: '继续',
        pass: '通过',
        // Function/class definition
        def: '定义',
        class: '类',
        return: '返回',
        yield: '产出',
        lambda: '匿名',
        // Import statements
        import: '导入',
        from: '从',
        as: '作为',
        // Exception handling
        try: '尝试',
        except: '捕获',
        finally: '最后',
        raise: '抛出',
        assert: '断言',
        // Context managers
        with: '与',
        // Boolean values
        True: '真',
        False: '假',
        None: '空',
        // Logical operators
        and: '与',
        or: '或',
        not: '非',
        // Membership/identity
        in: '在',
        is: '是',
        // Async/await
        async: '异步',
        await: '等待',
        // Scope keywords
        global: '全局',
        nonlocal: '非局部',
        del: '删除',
        // Built-in functions
        print: '打印',
        len: '长度',
        range: '范围',
        str: '字符串',
        int: '整数',
        float: '浮点',
        bool: '布尔',
        list: '列表',
        dict: '字典',
        set: '集合',
        tuple: '元组',
        open: '打开',
        input: '输入',
        type: '类型',
        sum: '求和',
        max: '最大',
        min: '最小',
        abs: '绝对值',
        round: '四舍五入',
        zip: '压缩',
        map: '映射',
        filter: '过滤',
        enumerate: '枚举',
        sorted: '排序',
        reversed: '反转',
        all: '全部',
        any: '任意'
    }
};

/**
 * Simulate translation for demo purposes.
 * This will be replaced with actual LSP server integration.
 *
 * @param code The original Python code
 * @param targetLanguage The target language code
 * @returns Simulated translated code
 */
async function simulateTranslation(code: string, targetLanguage: string): Promise<string> {
    // Get translations for the target language
    const translations = KEYWORD_TRANSLATIONS[targetLanguage];

    if (!translations) {
        // Default: return original code (English or unsupported language)
        return code;
    }

    // Apply translations using word boundary regex to avoid partial matches
    let translatedCode = code;
    for (const [keyword, translation] of Object.entries(translations)) {
        const regex = new RegExp(`\\b${keyword}\\b`, 'g');
        translatedCode = translatedCode.replace(regex, translation);
    }

    return translatedCode;
}

/**
 * Format a translation error for display.
 *
 * @param error The error that occurred
 * @returns A user-friendly error message
 */
export function formatTranslationError(error: unknown): string {
    if (error instanceof Error) {
        return error.message;
    }
    return 'An unknown error occurred during translation';
}
