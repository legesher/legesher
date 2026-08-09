// Pyodide runner for the docs playground (CORE-1551).
//
// A MODULE web worker that lazy-loads Pyodide v314.0.2 (CPython 3.14) from the
// pinned CDN, installs the vendored Legesher wheels via micropip, translates the
// editor's localized Python into English with TokenTranslator, and execs it —
// streaming stdout/stderr back to the main thread.
//
// Lives in public/ (not src/) so its top-level CDN `import` is served verbatim
// and never rewritten by the bundler. It is loaded on FIRST Run only.
//
// Protocol
//   main → worker:  { id, type: 'run', source, lang }
//                   { id, type: 'translate', source, lang, direction }  // to-en | from-en
//   worker → main:  { type: 'status', phase, message }        // lifecycle
//                   { id, type: 'stdout' | 'stderr', line }    // streamed output
//                   { id, type: 'result' }                     // finished OK
//                   { id, type: 'translated', code }           // translate finished OK
//                   { id, type: 'error', phase, message }      // translate|run|boot
//
// The recipe below (index deps via callKwargs, wheels with deps=false, the
// `.reverse()` before translate_code) was proven end-to-end in Task 0. Two
// non-obvious musts: callKwargs — a plain object is passed positionally by
// Pyodide, so `{deps:false}` would silently become `keep_going`; and `.reverse()`
// — from_language_pack(lang) yields en→lang, its reverse is the lang→en we need.
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.2/full/pyodide.mjs";

const PYODIDE_INDEX = "https://cdn.jsdelivr.net/pyodide/v314.0.2/full/";
const WHEELS = `${self.location.origin}/wheels/`;

const post = (msg) => self.postMessage(msg);

let pyodide = null;
let micropip = null;
let manifest = null;
let bootPromise = null;
const installedPacks = new Set();
let currentId = null; // tags streamed stdout/stderr with the active run

// One-time Python helpers. `_run_user` strips its own frame from tracebacks so
// the user sees a traceback rooted at "<playground>", not our exec wrapper.
const PY_SETUP = `
from legesher_core import TokenTranslator

_pg_translators = {}

def _pg_translate(src, lang):
    t = _pg_translators.get(lang)
    if t is None:
        # from_language_pack(lang) maps en→lang; reverse() gives lang→en.
        t = TokenTranslator.from_language_pack(lang).reverse()
        _pg_translators[lang] = t
    return t.translate_code(src)

_pg_forward_translators = {}

def _pg_translate_forward(src, lang):
    t = _pg_forward_translators.get(lang)
    if t is None:
        # from_language_pack(lang) is already the en→lang direction.
        t = TokenTranslator.from_language_pack(lang)
        _pg_forward_translators[lang] = t
    return t.translate_code(src)

def _pg_run_user(code):
    import sys, traceback
    try:
        compiled = compile(code, "<playground>", "exec")
    except SyntaxError:
        return traceback.format_exc()
    try:
        exec(compiled, {"__name__": "__main__"})
    except SystemExit:
        pass
    except BaseException:
        etype, evalue, tb = sys.exc_info()
        # tb.tb_next drops the _pg_run_user frame from the report.
        return "".join(traceback.format_exception(etype, evalue, tb.tb_next))
    return None
`;

async function boot() {
  post({ type: "status", phase: "booting", message: "Loading Python runtime…" });
  pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX });

  post({ type: "status", phase: "installing", message: "Installing the translation engine…" });
  manifest = await (await fetch(`${WHEELS}wheels-manifest.json`)).json();

  await pyodide.loadPackage("micropip");
  micropip = pyodide.pyimport("micropip");
  // Index deps (pydantic pulls pydantic_core wasm + typing-extensions etc.).
  await micropip.install.callKwargs(manifest.indexDeps, { keep_going: true });
  // Our pure wheels — deps:false keeps i18n's server-only deps (anthropic,
  // jinja2, click, rich…) out of the browser. MUST go through callKwargs.
  await micropip.install.callKwargs([`${WHEELS}${manifest.i18n}`, `${WHEELS}${manifest.core}`], {
    deps: false,
  });

  pyodide.runPython(PY_SETUP);

  pyodide.setStdout({
    batched: (line) => currentId != null && post({ id: currentId, type: "stdout", line }),
  });
  pyodide.setStderr({
    batched: (line) => currentId != null && post({ id: currentId, type: "stderr", line }),
  });

  post({ type: "status", phase: "ready", message: "Ready" });
}

function ensureBooted() {
  if (!bootPromise) bootPromise = boot();
  return bootPromise;
}

async function ensurePack(lang) {
  if (lang === "en" || installedPacks.has(lang)) return;
  const file = manifest.packs[lang];
  if (!file) throw new Error(`No language pack is vendored for '${lang}'.`);
  await micropip.install.callKwargs([`${WHEELS}${file}`], { deps: false });
  installedPacks.add(lang);
}

async function handleRun(id, source, lang) {
  try {
    await ensureBooted();
  } catch (e) {
    post({ id, type: "error", phase: "boot", message: `Failed to start the Python runtime: ${e && e.message ? e.message : e}` });
    return;
  }

  currentId = id;
  try {
    // 1) Translate localized → English (English needs no translation).
    let english = source;
    if (lang !== "en") {
      try {
        await ensurePack(lang);
        pyodide.globals.set("_pg_src", source);
        pyodide.globals.set("_pg_lang", lang);
        english = pyodide.runPython("_pg_translate(_pg_src, _pg_lang)");
      } catch (e) {
        post({ id, type: "error", phase: "translate", message: `Could not translate the code: ${e && e.message ? e.message : e}` });
        return;
      } finally {
        pyodide.globals.set("_pg_src", "");
      }
    }

    // 2) Execute; _pg_run_user returns a clean traceback string or None.
    post({ type: "status", phase: "running", message: "Running" });
    pyodide.globals.set("_pg_code", english);
    const traceback = await pyodide.runPythonAsync("_pg_run_user(_pg_code)");
    if (traceback) {
      post({ id, type: "error", phase: "run", message: String(traceback) });
    } else {
      post({ id, type: "result" });
    }
  } catch (e) {
    // Unexpected host-side failure (e.g. worker about to be terminated).
    post({ id, type: "error", phase: "run", message: String(e && e.message ? e.message : e) });
  } finally {
    currentId = null;
  }
}

// Translate without executing (CORE-1696 source ↔ canonical toggle). Both
// directions ride the same packs: 'to-en' is the runner's lang→en path,
// 'from-en' the forward en→lang one.
async function handleTranslate(id, source, lang, direction) {
  try {
    await ensureBooted();
  } catch (e) {
    post({ id, type: "error", phase: "boot", message: `Failed to start the Python runtime: ${e && e.message ? e.message : e}` });
    return;
  }

  if (lang === "en") {
    post({ id, type: "translated", code: source });
    return;
  }
  try {
    await ensurePack(lang);
    pyodide.globals.set("_pg_src", source);
    pyodide.globals.set("_pg_lang", lang);
    const fn = direction === "from-en" ? "_pg_translate_forward" : "_pg_translate";
    const code = pyodide.runPython(`${fn}(_pg_src, _pg_lang)`);
    post({ id, type: "translated", code });
  } catch (e) {
    post({ id, type: "error", phase: "translate", message: `Could not translate the code: ${e && e.message ? e.message : e}` });
  } finally {
    pyodide.globals.set("_pg_src", "");
  }
}

self.onmessage = (ev) => {
  const data = ev.data || {};
  if (data.type === "run") {
    handleRun(data.id, data.source, data.lang);
  } else if (data.type === "translate") {
    handleTranslate(data.id, data.source, data.lang, data.direction);
  } else if (data.type === "boot") {
    ensureBooted().catch(() => {});
  }
};
