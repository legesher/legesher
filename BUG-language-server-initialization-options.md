# BUG: Language Server Not Reading Initialization Options Correctly

## Issue Description

The VS Code extension correctly sends the target language in `initialization_options`,
but the language server ignores it and loads the wrong language pack.

## Reproduction Steps

1. Set language to Arabic via "Legesher: Select Language" command
2. Extension correctly updates global settings to `"legesher.targetLanguage": "ar"`
3. Extension sends `initialization_options={'targetLanguage': 'ar', 'sourceLanguage': 'en'}` to language server
4. Language server logs show: `Initializing Legesher Language Server (source: en, target: es)` ❌
5. Language server loads Spanish language pack instead of Arabic

## Evidence from Logs

### Extension Side (CORRECT ✅)

```log
[2025-11-24T18:46:32.477Z] [INFO] Starting language server with configuration
initialization_options={'targetLanguage': 'ar', 'sourceLanguage': 'en', 'trace': 'off'}
```

### Language Server Side (WRONG ❌)

```log
2025-11-24 22:46:32,767 [INFO] legesher_language_server.server: Initializing (source: en, target: es)
2025-11-24 22:46:32,779 [INFO] legesher_language_server.pylance_proxy: Loaded 37 for es from 3.10.yml
```

## Root Cause Analysis

**FOUND**: The `on_initialize()` method exists in `server.py` but is **never registered with pygls**.

### The Problem

1. `server.py` has an `on_initialize()` method (line 215) that processes `initialization_options`
2. However, in `_register_handlers()` (line 164), there is NO wrapper or registration for initialize
3. Line 200 comment says: "don't override initialize - let pygls handle it"
4. pygls registers its builtin initialize handler that doesn't call our `on_initialize()`
5. Result: Our custom `on_initialize()` method is dead code - never executed

### Evidence

From logs, we see pygls's builtin handler:

```log
2025-11-24 23:12:55,598 [INFO] pygls.feature_manager: Registered builtin feature initialize
```

But we NEVER see the DEBUG logs from our `on_initialize()` method:

- "Client initializing from: ..." ❌
- "DEBUG: initialization_options = ..." ❌
- "Updated target language from init options: ar" ❌

### The Flow

```text
1. pygls registers builtin initialize handler (automatic)
2. Server.__init__() calls _register_handlers()
3. _register_handlers() registers initialized, shutdown, etc. BUT NOT initialize
4. LSP client sends InitializeParams with initialization_options={'targetLanguage': 'ar'}
5. pygls builtin handler processes it WITHOUT calling our on_initialize()
6. Config stays at default: target='es'
7. PylanceProxy loads Spanish language pack
```

## Expected Behavior

Language server should:

1. Read `initialization_options` from the LSP client
2. Use the `targetLanguage` value to load the correct language pack
3. Log: `Initializing Legesher Language Server (source: en, target: ar)`
4. Load Arabic translations: `Loaded 37 keyword translations for ar from 3.10.yml`

## Solution

### Approach 1: Register initialize handler (ATTEMPTED)

Added in `_register_handlers()`:

```python
async def initialize_wrapper(params: InitializeParams) -> InitializeResult:
    return await self.on_initialize(params)

self.feature(INITIALIZE)(initialize_wrapper)
```

**Status**: Testing needed - pygls may still use builtin handler instead of ours

### Approach 2: Process initialization_options in on_initialized() (ALTERNATIVE)

Since `on_initialized()` IS being called correctly, we can access initialization_options there:

```python
async def on_initialized(self, params: InitializedParams) -> None:
    # Access initialization_options from server's stored InitializeParams
    # Update config before creating PylanceProxy
    if hasattr(self, 'workspace') and hasattr(self.workspace, 'initialization_options'):
        init_opts = self.workspace.initialization_options
        if 'targetLanguage' in init_opts:
            self.config.target_language = validate_language_code(init_opts['targetLanguage'])
```

### Recommendation

Try Approach 1 first (already implemented). If pygls builtin still takes precedence, fall back to Approach 2.

## Files Modified

- `libs/language-server/legesher_language_server/server.py`:
  - Added `INITIALIZE` import from lsprotocol.types
  - Added `initialize_wrapper()` in `_register_handlers()`
  - Registered wrapper with `self.feature(INITIALIZE)(initialize_wrapper)`
  - Added DEBUG logging in `on_initialize()` to track execution
  - Added DEBUG logging in `on_initialized()` for troubleshooting

## Impact

- Language switching doesn't work
- Users cannot use non-Spanish languages in the extension
- Telemetry will track incorrect language usage
- All language tests fail for non-Spanish languages

## Testing

After fix:

1. Restart extension with Arabic selected
2. Should see in logs: "DEBUG: initialization_options = {'targetLanguage': 'ar', ...}"
3. Should see: "Updated target language from init options: ar"
4. Should see: "Loaded 37 keyword translations for ar from 3.10.yml"
5. Arabic keywords should work in test_arabic.py

## Priority

High - blocks language switching feature (CORE-473)
