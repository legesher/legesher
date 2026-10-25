// @ts-check

(function () {
    // Get VS Code API
    const vscode = acquireVsCodeApi();

    // DOM elements
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const contentEl = document.getElementById('content');
    const errorMessageEl = document.getElementById('error-message');
    const retryButton = document.getElementById('retry-button');
    const copyButton = document.getElementById('copy-button');
    const sourceLangLabel = document.getElementById('source-lang-label');
    const targetLangLabel = document.getElementById('target-lang-label');
    const fileNameEl = document.getElementById('file-name');
    const originalCodeEl = document.getElementById('original-code');
    const translatedCodeEl = document.getElementById('translated-code');
    const leftPane = document.querySelector('.left-pane');
    const rightPane = document.querySelector('.right-pane');

    // State
    let isSyncing = false;
    let translatedCode = '';
    let copyTimeout = null;

    // Python keywords and builtins - loaded from extension (source of truth: language packs)
    // These are populated when the extension sends data via postMessage
    let PYTHON_KEYWORDS = new Set();
    let PYTHON_BUILTINS = new Set();

    /**
     * Apply custom syntax highlighting for translated code
     * Since Prism.js only knows English Python keywords, we need to highlight
     * translated keywords manually using the same CSS classes.
     */
    function highlightTranslatedCode(code, translations) {
        // Build keyword/builtin sets from translations
        const translatedKeywords = new Set();
        const translatedBuiltins = new Set();

        if (translations && Object.keys(translations).length > 0) {
            for (const [english, translated] of Object.entries(translations)) {
                if (PYTHON_KEYWORDS.has(english)) {
                    translatedKeywords.add(translated);
                } else if (PYTHON_BUILTINS.has(english)) {
                    translatedBuiltins.add(translated);
                }
            }
        }

        // Tokenize the code and apply highlighting
        const tokens = tokenizePython(code, translatedKeywords, translatedBuiltins);
        return tokens.map(token => {
            const escaped = escapeHtml(token.value);
            if (token.type === 'plain') {
                return escaped;
            }
            return `<span class="token ${token.type}">${escaped}</span>`;
        }).join('');
    }

    /**
     * Simple Python tokenizer for syntax highlighting
     */
    function tokenizePython(code, translatedKeywords, translatedBuiltins) {
        const tokens = [];
        let i = 0;

        while (i < code.length) {
            // Triple-quoted strings (docstrings)
            // [Copilot Review Fix] Fixed end index calculation - was setting end to code.length-3
            // which could be negative for short strings. Now properly consumes rest of string.
            if (code.slice(i, i + 3) === '"""' || code.slice(i, i + 3) === "'''") {
                const quote = code.slice(i, i + 3);
                let end = code.indexOf(quote, i + 3);
                if (end === -1) end = code.length; // Consume rest if no closing quote
                else end = end + 3; // Include the closing quote
                tokens.push({ type: 'string', value: code.slice(i, end) });
                i = end;
                continue;
            }

            // Prefixed triple-quoted strings (r"""...""", f'''...''', etc.)
            // Must check BEFORE prefixed single-quoted strings to avoid partial matches
            if (/^[rRfFbBuU]{1,2}("""|''')/.test(code.slice(i, i + 5))) {
                let prefixLen = 1;
                if (/^[rRfFbBuU]{2}("""|''')/.test(code.slice(i, i + 5))) prefixLen = 2;
                const quote = code.slice(i + prefixLen, i + prefixLen + 3); // """ or '''
                let end = code.indexOf(quote, i + prefixLen + 3);
                if (end === -1) end = code.length;
                else end = end + 3; // Include closing quote
                tokens.push({ type: 'string', value: code.slice(i, end) });
                i = end;
                continue;
            }

            // Prefixed single/double quoted strings (r"...", f'...', etc.)
            if (/^[rRfFbBuU]{1,2}["']/.test(code.slice(i, i + 3))) {
                let prefixLen = 1;
                if (/^[rRfFbBuU]{2}["']/.test(code.slice(i, i + 3))) prefixLen = 2;
                const quoteChar = code[i + prefixLen];
                let j = i + prefixLen + 1;
                while (j < code.length && code[j] !== quoteChar) {
                    if (code[j] === '\\' && j + 1 < code.length) j++; // Skip escaped char
                    j++;
                }
                const hasClosingQuote = j < code.length && code[j] === quoteChar;
                const endIndex = hasClosingQuote ? j + 1 : j;
                tokens.push({ type: 'string', value: code.slice(i, endIndex) });
                i = endIndex;
                continue;
            }

            // Single/double quoted strings
            // [Copilot Review Fix] Fixed handling when closing quote is not found.
            // Previously would slice beyond string end. Now checks bounds properly.
            if (code[i] === '"' || code[i] === "'") {
                const quote = code[i];
                let j = i + 1;
                while (j < code.length && code[j] !== quote) {
                    if (code[j] === '\\' && j + 1 < code.length) j++; // Skip escaped char
                    j++;
                }
                const hasClosingQuote = j < code.length && code[j] === quote;
                const endIndex = hasClosingQuote ? j + 1 : j;
                tokens.push({ type: 'string', value: code.slice(i, endIndex) });
                i = endIndex;
                continue;
            }

            // Comments
            if (code[i] === '#') {
                let end = code.indexOf('\n', i);
                if (end === -1) end = code.length;
                tokens.push({ type: 'comment', value: code.slice(i, end) });
                i = end;
                continue;
            }

            // Numbers (including floats)
            // [Copilot Review Fix] Added explicit bounds checks (i + 1 < code.length, j + 1 < code.length)
            // throughout number parsing to prevent accessing undefined array indices.
            if (/[0-9]/.test(code[i]) || (code[i] === '.' && i + 1 < code.length && /[0-9]/.test(code[i + 1]))) {
                let j = i;
                // Handle hex, octal, binary
                if (code[i] === '0' && i + 1 < code.length && /[xXoObB]/.test(code[i + 1])) {
                    j += 2;
                    while (j < code.length && /[0-9a-fA-F_]/.test(code[j])) j++;
                } else {
                    while (j < code.length && /[0-9_]/.test(code[j])) j++;
                    if (j < code.length && code[j] === '.' && j + 1 < code.length && /[0-9]/.test(code[j + 1])) {
                        j++;
                        while (j < code.length && /[0-9_]/.test(code[j])) j++;
                    }
                    // Scientific notation
                    if (j < code.length && /[eE]/.test(code[j])) {
                        j++;
                        if (j < code.length && /[+-]/.test(code[j])) j++;
                        while (j < code.length && /[0-9_]/.test(code[j])) j++;
                    }
                }
                tokens.push({ type: 'number', value: code.slice(i, j) });
                i = j;
                continue;
            }

            // Identifiers (keywords, builtins, function names, variables)
            // [Copilot Review Fix] Added Greek (\u0370-\u03FF) and Japanese Hiragana/Katakana (\u3040-\u30FF)
            //
            // UNICODE RANGES FOR SUPPORTED LANGUAGE PACKS:
            // When adding new language packs, ensure their script's Unicode range is included here.
            //
            // Range           | Script              | Languages Supported
            // ----------------|---------------------|--------------------
            // a-zA-Z          | Basic Latin         | en, da, de, es, fi, fr, hu, id, it, ms, nl, no, pl, pt, sv, sw, tl, tr, vi, xh
            // \u00C0-\u024F   | Latin Extended      | da, de, es, fi, fr, hu, id, it, nl, no, pl, pt, sv, tl, tr, vi (accents)
            // \u0370-\u03FF   | Greek               | el (Greek)
            // \u0400-\u04FF   | Cyrillic            | mk, mn, ru, sr, uk
            // \u0590-\u05FF   | Hebrew              | he (Hebrew) [RTL]
            // \u0600-\u06FF   | Arabic              | ar (Arabic) [RTL]
            // \u0900-\u097F   | Devanagari          | hi, ne
            // \u0E00-\u0E7F   | Thai                | th (Thai)
            // \u3040-\u30FF   | Hiragana + Katakana | ja (Japanese)
            // \u4E00-\u9FFF   | CJK Unified         | zh (Chinese), ja (Japanese kanji)
            // \uAC00-\uD7AF   | Hangul Syllables    | ko (Korean)
            //
            // NOTE: Some languages (fi=Finnish, ms=Malay) use Latin script with minimal extensions.
            if (/[a-zA-Z_\u00C0-\u024F\u0370-\u03FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u0900-\u097F\u0E00-\u0E7F\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]/.test(code[i])) {
                let j = i;
                while (j < code.length && /[a-zA-Z0-9_\u00C0-\u024F\u0370-\u03FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u0900-\u097F\u0E00-\u0E7F\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]/.test(code[j])) j++;
                const word = code.slice(i, j);

                // Check if it's a function definition or call
                // [Copilot Review Fix] Added bounds check (afterWord < code.length) before
                // checking if code[afterWord] === '(' to handle end-of-string case.
                let afterWord = j;
                while (afterWord < code.length && /\s/.test(code[afterWord])) afterWord++;

                if (translatedKeywords.has(word) || PYTHON_KEYWORDS.has(word)) {
                    tokens.push({ type: 'keyword', value: word });
                } else if (translatedBuiltins.has(word) || PYTHON_BUILTINS.has(word)) {
                    tokens.push({ type: 'builtin', value: word });
                } else if (afterWord < code.length && code[afterWord] === '(') {
                    tokens.push({ type: 'function', value: word });
                } else {
                    tokens.push({ type: 'plain', value: word });
                }
                i = j;
                continue;
            }

            // Operators - explicitly match valid Python multi-character operators
            // [Copilot Review Fix] Changed from greedy approach (consuming all consecutive operator chars)
            // to explicit matching of valid Python operators. The greedy approach incorrectly parsed
            // "a**-b" as "**-" instead of "**" followed by "-".
            if (/[+\-*/%=<>!&|^~]/.test(code[i])) {
                const multiCharOperators = [
                    '**=', '>>=', '<<=', '//=',
                    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=',
                    '==', '!=', '<=', '>=', '**', '//', '<<', '>>'
                ];

                let matchedOp = null;
                for (const op of multiCharOperators) {
                    if (code.startsWith(op, i)) {
                        matchedOp = op;
                        break;
                    }
                }

                if (matchedOp !== null) {
                    tokens.push({ type: 'operator', value: matchedOp });
                    i += matchedOp.length;
                } else {
                    tokens.push({ type: 'operator', value: code[i] });
                    i++;
                }
                continue;
            }

            // Punctuation
            if (/[()[\]{},.:;@]/.test(code[i])) {
                tokens.push({ type: 'punctuation', value: code[i] });
                i++;
                continue;
            }

            // Whitespace and other characters
            tokens.push({ type: 'plain', value: code[i] });
            i++;
        }

        return tokens;
    }

    /**
     * Escape HTML special characters
     * [Copilot Review Fix] Changed from DOM-based approach (creating div element for each token)
     * to static map replacement, which is significantly faster for large code blocks.
     */
    function escapeHtml(text) {
        if (text === null || text === undefined) {
            return '';
        }

        const replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };

        return String(text).replace(/[&<>"']/g, function (ch) {
            return replacements[ch];
        });
    }

    /**
     * Show a specific view state
     */
    function showView(view) {
        loadingEl.classList.add('hidden');
        errorEl.classList.add('hidden');
        contentEl.classList.add('hidden');

        if (view === 'loading') {
            loadingEl.classList.remove('hidden');
        } else if (view === 'error') {
            errorEl.classList.remove('hidden');
        } else if (view === 'content') {
            contentEl.classList.remove('hidden');
        }
    }

    /**
     * Display an error message
     */
    function showError(message) {
        errorMessageEl.textContent = message;
        showView('error');
    }

    /**
     * Update the translation view with new content
     */
    function updateContent(data) {
        const {
            originalCode,
            translatedCode: translated,
            sourceLanguage,
            targetLanguage,
            sourceLanguageName,
            targetLanguageName,
            fileName,
            rtlLanguages,
            translations,
            pythonKeywords,
            pythonBuiltins
        } = data;

        // Update keyword/builtin sets from source of truth (language packs)
        if (pythonKeywords && Array.isArray(pythonKeywords)) {
            PYTHON_KEYWORDS = new Set(pythonKeywords);
        }
        if (pythonBuiltins && Array.isArray(pythonBuiltins)) {
            PYTHON_BUILTINS = new Set(pythonBuiltins);
        }

        // Store translated code for copy function
        translatedCode = translated;

        // Update language labels using names from extension
        sourceLangLabel.textContent = `Original (${sourceLanguageName || sourceLanguage.toUpperCase()})`;
        targetLangLabel.textContent = `Translation (${targetLanguageName || targetLanguage.toUpperCase()})`;

        // Update file name
        const baseName = fileName ? fileName.split('/').pop() : 'Untitled';
        fileNameEl.textContent = baseName;

        // Update code content
        const originalCodeBlock = originalCodeEl.querySelector('code');
        const translatedCodeBlock = translatedCodeEl.querySelector('code');

        if (originalCodeBlock && translatedCodeBlock) {
            // Original code uses Prism.js (English keywords)
            originalCodeBlock.textContent = originalCode;

            // Translated code uses custom highlighting (translated keywords)
            // Use innerHTML with custom highlighting instead of textContent + Prism
            translatedCodeBlock.innerHTML = highlightTranslatedCode(translatedCode, translations);

            // Add RTL class for Arabic and other RTL languages
            if (rtlLanguages.includes(targetLanguage)) {
                rightPane.classList.add('rtl');
                // Apply RTL direction for natural right-to-left code flow
                translatedCodeEl.style.direction = 'rtl';
                translatedCodeEl.style.textAlign = 'right';
                translatedCodeBlock.style.direction = 'rtl';
                translatedCodeBlock.style.textAlign = 'right';
            } else {
                rightPane.classList.remove('rtl');
                translatedCodeEl.style.direction = '';
                translatedCodeEl.style.textAlign = '';
                translatedCodeBlock.style.direction = '';
                translatedCodeBlock.style.textAlign = '';
            }

            if (rtlLanguages.includes(sourceLanguage)) {
                leftPane.classList.add('rtl');
                originalCodeEl.style.direction = 'rtl';
                originalCodeEl.style.textAlign = 'right';
                originalCodeBlock.style.direction = 'rtl';
                originalCodeBlock.style.textAlign = 'right';
            } else {
                leftPane.classList.remove('rtl');
                originalCodeEl.style.direction = '';
                originalCodeEl.style.textAlign = '';
                originalCodeBlock.style.direction = '';
                originalCodeBlock.style.textAlign = '';
            }

            // Apply Prism syntax highlighting for original (English) code only
            // Translated code is already highlighted by highlightTranslatedCode()
            if (window.Prism) {
                Prism.highlightElement(originalCodeBlock);
            }
        }

        // Reset scroll positions
        leftPane.scrollTop = 0;
        rightPane.scrollTop = 0;

        // Show content
        showView('content');
    }

    /**
     * Copy translated code to clipboard
     */
    function copyTranslation() {
        if (!translatedCode) {
            return;
        }

        // Send message to extension to copy
        vscode.postMessage({
            type: 'copy',
            data: { text: translatedCode }
        });

        // Update button text temporarily
        const originalText = copyButton.textContent;
        copyButton.textContent = '✓ Copied!';
        copyButton.classList.add('copied');

        // Clear existing timeout to prevent race condition
        if (copyTimeout) {
            clearTimeout(copyTimeout);
        }

        copyTimeout = setTimeout(() => {
            copyButton.textContent = originalText;
            copyButton.classList.remove('copied');
            copyTimeout = null;
        }, 2000);
    }

    /**
     * Request a refresh of the translation
     */
    function refreshTranslation() {
        vscode.postMessage({
            type: 'refresh'
        });
        showView('loading');
    }

    /**
     * Synchronize scrolling between left and right panes
     */
    function setupScrollSync() {
        leftPane.addEventListener('scroll', () => {
            if (!isSyncing) {
                isSyncing = true;
                rightPane.scrollTop = leftPane.scrollTop;
                // Use requestAnimationFrame for smooth sync
                requestAnimationFrame(() => {
                    isSyncing = false;
                });
            }
        });

        rightPane.addEventListener('scroll', () => {
            if (!isSyncing) {
                isSyncing = true;
                leftPane.scrollTop = rightPane.scrollTop;
                // Use requestAnimationFrame for smooth sync
                requestAnimationFrame(() => {
                    isSyncing = false;
                });
            }
        });
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Copy button
        copyButton.addEventListener('click', copyTranslation);

        // Retry button
        retryButton.addEventListener('click', refreshTranslation);

        // Set up scroll synchronization
        setupScrollSync();

        // Listen for messages from extension
        window.addEventListener('message', event => {
            const message = event.data;

            switch (message.type) {
                case 'loading':
                    if (message.data.isLoading) {
                        showView('loading');
                    }
                    break;

                case 'update':
                    updateContent(message.data);
                    break;

                case 'error':
                    showError(message.data.message);
                    break;
            }
        });
    }

    /**
     * Initialize the webview
     */
    function init() {
        setupEventListeners();
        showView('loading');
    }

    // Start the application
    init();
})();
