#!/usr/bin/env python3
"""Measure whether a model relays this server's engine facts, or invents them.

The server's contract is a division of labour: it supplies deterministic
engine facts, the model supplies prose. A client that calls the tools and
then narrates its own numbers has broken that contract while appearing to
honour it — and the failure is invisible to the user, because a fabricated
mapping looks exactly like a real one.

So tool-selection is necessary but nowhere near sufficient. This harness
measures two things:

  hit          did it call the tool the task calls for
  fidelity     did the engine's facts survive into its prose

A model can score 100% on the first and 0% on the second. That combination
is worse than not calling the tools at all, and it is the specific outcome
this exists to catch. A contradiction metric — did the model assert a
*different* value than the engine gave — is not measured yet; a fact the
model contradicted scores the same as one it omitted. It lands with the
round-trip task (CORE-1813's ``verdict_line`` is the fact it grades
against).

Usage::

    python grounding_eval.py <model-tag>
    python grounding_eval.py <model-tag> --base-url http://localhost:11434
    python grounding_eval.py <model-tag> --json

Requires an endpoint speaking Ollama's native chat API (``/api/chat``,
tool support) and the Legesher engine importable. The OpenAI-compatible
surface (``/v1/chat/completions``) is NOT what this posts to.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://localhost:11434"
MAX_TURNS = 6
REQUEST_TIMEOUT = 600


# --------------------------------------------------------------------------
# Tasks
#
# `facts` pulls the values the engine actually returned out of a tool result.
# We assert against what the tool said on this run, never against a snapshot,
# so the harness stays correct as packs change.
# --------------------------------------------------------------------------


def _facts_from_constructs(payload: dict) -> dict[str, str]:
    return {
        c["construct"]: c["in_explain_lang"]
        for c in payload.get("constructs", [])
        if c.get("in_explain_lang")
    }


def _facts_from_mappings(payload: dict) -> dict[str, str]:
    """`mappings` is keyed by category — keywords, builtins, exceptions … —
    each holding term -> rendering. Flatten across categories."""
    facts: dict[str, str] = {}
    for category in (payload.get("mappings") or {}).values():
        if isinstance(category, dict):
            facts.update({k: v for k, v in category.items() if isinstance(v, str)})
    return facts


def _facts_from_translation(payload: dict) -> dict[str, str]:
    """Every translated line is a fact the prose must not silently rewrite."""
    source = payload.get("translated_source") or ""
    return {f"line{i}": line.strip() for i, line in enumerate(source.splitlines()) if line.strip()}


TASKS = [
    {
        "name": "explain-in-language",
        "expect": "explain_in_language",
        "facts": _facts_from_constructs,
        "prompt": (
            "Explain this code to an Amharic speaker, construct by construct.\n\n"
            "```python\nfor name in names:\n    print(name)\n```"
        ),
    },
    {
        "name": "lookup-mapping",
        "expect": "lookup_keyword_mapping",
        "facts": _facts_from_mappings,
        "prompt": (
            "In Arabic, how do the Python keywords 'def', 'return' and 'if' "
            "render? Give me the exact terms."
        ),
    },
    {
        "name": "translate-to-native",
        "expect": "translate_to_native",
        "facts": _facts_from_translation,
        "prompt": (
            "Render this into French for a learner, then say in one sentence "
            "what it does.\n\n```python\ndef to_letter(score):\n"
            '    if score >= 90:\n        return "A"\n    return "F"\n```'
        ),
    },
]


# --------------------------------------------------------------------------
# Model plumbing
# --------------------------------------------------------------------------


def chat(base_url: str, model: str, messages: list, tools: list) -> dict:
    payload = json.dumps(
        {"model": model, "messages": messages, "tools": tools, "stream": False}
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read())["message"]


def normalize_arguments(args) -> tuple[dict, bool]:
    """Return (arguments, was_enveloped).

    Some models describe the whole call rather than just its arguments,
    nesting the real payload under "parameters" beside a repeated tool name.
    Observed on North-Mini-Code-1.0. The arguments inside are well-formed, so
    unwrap rather than fail — but report it, because it is a real
    interoperability cost for anyone pointing that model at this server.
    """
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return {}, False
    if isinstance(args, dict) and isinstance(args.get("parameters"), dict):
        if {"tool_name", "tool_call_id"} & set(args):
            return args["parameters"], True
    return (args if isinstance(args, dict) else {}), False


def result_text(result) -> str:
    """The text payload of an MCP tool result.

    ``call_tool`` yields content objects, not raw JSON. Reach for ``.text``
    rather than str()-ing the object — its repr embeds the JSON in an escaped
    form that is painful and lossy to recover.
    """
    payload = result[0] if isinstance(result, tuple) else result
    if isinstance(payload, list) and payload:
        payload = payload[0]
    text = getattr(payload, "text", None)
    if isinstance(text, str):
        return text
    return payload if isinstance(payload, str) else json.dumps(payload, default=str)


def parse_payload(text: str) -> dict:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


async def run_task(mcp, base_url: str, model: str, task: dict, tools: list) -> dict:
    messages = [{"role": "user", "content": task["prompt"]}]
    called: list[str] = []
    enveloped = 0
    engine_facts: dict[str, str] = {}
    errors: list[str] = []

    for _ in range(MAX_TURNS):
        try:
            msg = chat(base_url, model, messages, tools)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"transport: {exc}")
            break
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            break
        for call in calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            args, was_env = normalize_arguments(fn.get("arguments") or {})
            enveloped += int(was_env)
            called.append(name)
            try:
                body = result_text(await mcp.call_tool(name, args))
                if name == task["expect"]:
                    engine_facts.update(task["facts"](parse_payload(body)))
                text = body[:4000]
            except Exception as exc:  # noqa: BLE001 — grading failures is the job
                text = f"ERROR: {type(exc).__name__}: {exc}"
                errors.append(f"{name}: {type(exc).__name__}")
            messages.append({"role": "tool", "content": text})

    prose = next(
        (
            m["content"]
            for m in reversed(messages)
            if m.get("role") == "assistant" and m.get("content")
        ),
        "",
    )

    present = {k: v for k, v in engine_facts.items() if v and v in prose}
    missing = {k: v for k, v in engine_facts.items() if v and v not in prose}

    return {
        "task": task["name"],
        "expected_tool": task["expect"],
        "called": called,
        "hit": task["expect"] in called,
        "enveloped": enveloped,
        "engine_facts": engine_facts,
        "present": present,
        "missing": missing,
        "fidelity": (len(present) / len(engine_facts)) if engine_facts else None,
        "errors": errors,
        "prose": prose,
    }


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = ap.parse_args()

    from legesher_mcp.server import mcp

    raw = await mcp.list_tools()
    tools = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "").strip()[:900],
                "parameters": t.inputSchema,
            },
        }
        for t in raw
    ]

    results = [await run_task(mcp, args.base_url, args.model, t, tools) for t in TASKS]

    if args.json:
        print(
            json.dumps(
                {"model": args.model, "results": results}, ensure_ascii=False, indent=2, default=str
            )
        )
        return 0

    print(f"model: {args.model}")
    print(f"tools: {len(tools)} exposed by the server\n")

    for r in results:
        print(f"── {r['task']} ".ljust(64, "─"))
        transport_failed = any(e.startswith("transport:") for e in r["errors"])
        print(f"  expected tool : {r['expected_tool']}")
        if transport_failed:
            # Distinguish "never got an answer" from "chose not to call" —
            # conflating them would blame the model for our timeout.
            print(
                f"  called        : {r['called'] or '(none)'}  "
                f"hit=INCONCLUSIVE (transport failed mid-task)"
            )
        else:
            print(f"  called        : {r['called'] or '(none)'}  hit={r['hit']}")
        if r["enveloped"]:
            print(f"  envelope      : {r['enveloped']} nested-argument call(s) unwrapped")
        if r["fidelity"] is None:
            print("  fidelity      : n/a — no engine facts captured")
        else:
            print(
                f"  fidelity      : {r['fidelity']:.0%} "
                f"({len(r['present'])}/{len(r['engine_facts'])} facts survived)"
            )
            for k, v in list(r["missing"].items())[:6]:
                print(f"    DROPPED     : {k} -> {v!r} never appears in the prose")
            if r["fidelity"] < 1.0 and r["prose"]:
                # A fidelity number nobody can adjudicate is a number nobody
                # will trust. Show what the model actually said.
                excerpt = " ".join(r["prose"].split())[:400]
                print(f"    said instead: {excerpt}")
        for e in r["errors"]:
            print(f"  error         : {e}")
        print()

    graded = [r for r in results if r["fidelity"] is not None]
    inconclusive = [r for r in results if any(e.startswith("transport:") for e in r["errors"])]
    scored = [r for r in results if r not in inconclusive]
    hits = sum(r["hit"] for r in scored)
    mean_fid = (sum(r["fidelity"] for r in graded) / len(graded)) if graded else 0.0

    print("═" * 64)
    print(f"tool selection : {hits}/{len(scored)} conclusive task(s)")
    print(f"grounding      : {mean_fid:.0%} mean fidelity over {len(graded)} graded task(s)")
    if inconclusive:
        print(
            f"inconclusive   : {len(inconclusive)} task(s) failed transport — "
            f"re-run before drawing conclusions"
        )
    if hits and graded and mean_fid < 0.5:
        print("\n  It calls the tools and then does not use what they return.")
        print("  Worse than not calling them — the output looks sourced.")
    ok = hits == len(scored) and mean_fid >= 0.9 and not inconclusive
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
