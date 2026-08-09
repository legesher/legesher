// Main-thread client for the Pyodide playground worker (CORE-1551).
//
// Spawns the module worker on FIRST run (lazy — the ~6 MB Pyodide runtime is
// never fetched on page load), correlates messages by id, and guards user code
// with a 5 s execution watchdog that terminates + respawns a runaway worker.

const WORKER_URL = "/playground/pyodide-worker.mjs";
const EXEC_TIMEOUT_MS = 5000;

type WorkerStatus = "booting" | "installing" | "ready" | "running";

type WorkerMessage =
  | { type: "status"; phase: WorkerStatus; message: string }
  | { id: number; type: "stdout" | "stderr"; line: string }
  | { id: number; type: "result" }
  | { id: number; type: "translated"; code: string }
  | { id: number; type: "error"; phase: string; message: string };

/** 'to-en' = localized → canonical (what Run uses); 'from-en' = the reverse. */
export type TranslateDirection = "to-en" | "from-en";

export interface RunnerCallbacks {
  /** Lifecycle hints for the loading modal / status line. */
  onStatus?: (phase: WorkerStatus, message: string) => void;
  /** A line of program output. */
  onOutput?: (stream: "stdout" | "stderr", line: string) => void;
  /** Translation or runtime failure. `phase` ∈ translate|run|boot|timeout. */
  onError?: (phase: string, message: string) => void;
  /** Program finished without error. */
  onResult?: () => void;
}

export interface Runner {
  run(source: string, lang: string, callbacks: RunnerCallbacks): void;
  /** Translate without executing; resolves to the translated source. */
  translate(
    source: string,
    lang: string,
    direction: TranslateDirection,
    onStatus?: (phase: WorkerStatus, message: string) => void,
  ): Promise<string>;
  dispose(): void;
}

interface PendingTranslation {
  resolve: (code: string) => void;
  reject: (err: Error) => void;
  onStatus?: (phase: WorkerStatus, message: string) => void;
}

export function createRunner(): Runner {
  let worker: Worker | null = null;
  let nextId = 1;
  let activeId: number | null = null;
  let activeCbs: RunnerCallbacks | null = null;
  let watchdog: ReturnType<typeof setTimeout> | null = null;
  const pendingTranslations = new Map<number, PendingTranslation>();

  const rejectTranslations = (message: string) => {
    for (const pending of pendingTranslations.values()) pending.reject(new Error(message));
    pendingTranslations.clear();
  };

  const clearWatchdog = () => {
    if (watchdog) {
      clearTimeout(watchdog);
      watchdog = null;
    }
  };

  const finish = (): RunnerCallbacks | null => {
    clearWatchdog();
    const cbs = activeCbs;
    activeId = null;
    activeCbs = null;
    return cbs;
  };

  const startWatchdog = () => {
    clearWatchdog();
    watchdog = setTimeout(() => {
      // Runaway user code blocks the worker thread, so it can't self-report —
      // kill it from here and respawn a clean one for the next run.
      if (worker) {
        worker.terminate();
        worker = null;
      }
      rejectTranslations("The Python runtime was stopped by a timed-out run.");
      const cbs = finish();
      cbs?.onError?.(
        "timeout",
        `Your code ran longer than ${EXEC_TIMEOUT_MS / 1000}s and was stopped. Check for an infinite loop.`,
      );
    }, EXEC_TIMEOUT_MS);
  };

  const onMessage = (msg: WorkerMessage) => {
    if (msg.type === "status") {
      activeCbs?.onStatus?.(msg.phase, msg.message);
      for (const pending of pendingTranslations.values()) pending.onStatus?.(msg.phase, msg.message);
      // Only user-code execution is guarded; boot/install/translate are not.
      if (msg.phase === "running") startWatchdog();
      return;
    }
    const pending = pendingTranslations.get(msg.id);
    if (pending) {
      pendingTranslations.delete(msg.id);
      if (msg.type === "translated") pending.resolve(msg.code);
      else if (msg.type === "error") pending.reject(new Error(msg.message));
      return;
    }
    if (msg.id !== activeId) return; // stale message from a superseded run
    if (msg.type === "stdout" || msg.type === "stderr") {
      activeCbs?.onOutput?.(msg.type, msg.line);
    } else if (msg.type === "result") {
      finish()?.onResult?.();
    } else if (msg.type === "error") {
      finish()?.onError?.(msg.phase, msg.message);
    }
  };

  const spawn = (): Worker => {
    const w = new Worker(WORKER_URL, { type: "module" });
    w.onmessage = (ev: MessageEvent<WorkerMessage>) => onMessage(ev.data);
    w.onerror = (ev) => {
      rejectTranslations(ev.message || "The Python runtime failed to start.");
      const cbs = finish();
      cbs?.onError?.("boot", ev.message || "The Python runtime failed to start.");
    };
    return w;
  };

  return {
    run(source: string, lang: string, callbacks: RunnerCallbacks) {
      // One run at a time; the page disables Run while busy. Supersede anyway.
      clearWatchdog();
      if (!worker) worker = spawn();
      const id = nextId++;
      activeId = id;
      activeCbs = callbacks;
      worker.postMessage({ id, type: "run", source, lang });
    },
    translate(source, lang, direction, onStatus) {
      if (!worker) worker = spawn();
      const id = nextId++;
      return new Promise<string>((resolve, reject) => {
        pendingTranslations.set(id, { resolve, reject, onStatus });
        worker!.postMessage({ id, type: "translate", source, lang, direction });
      });
    },
    dispose() {
      clearWatchdog();
      if (worker) {
        worker.terminate();
        worker = null;
      }
      rejectTranslations("The playground was disposed.");
      activeId = null;
      activeCbs = null;
    },
  };
}
