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
            rtlLanguages
        } = data;

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
            originalCodeBlock.textContent = originalCode;
            translatedCodeBlock.textContent = translatedCode;

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

            // Apply syntax highlighting
            if (window.Prism) {
                Prism.highlightElement(originalCodeBlock);
                Prism.highlightElement(translatedCodeBlock);
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
