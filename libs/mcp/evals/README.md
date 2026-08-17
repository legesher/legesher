# Grounding evals

Measures whether a model **relays** this server's engine facts or **invents**
them.

## Why this exists

The server's contract is a division of labour: it returns deterministic engine
facts, the model writes the prose. A client that calls the tools and then
narrates its own numbers has broken that contract while appearing to honour it.

That failure is invisible to the user. A fabricated keyword mapping looks
exactly like a real one — more convincing, if anything, because the model
introduces it as engine output.

So "did it call the right tool" is necessary and nowhere near sufficient. A
model can score perfectly on tool selection and zero on grounding, and that
combination is **worse than not calling the tools at all**.

## What it measures

| Metric | Question |
| -- | -- |
| `hit` | Did it call the tool the task calls for? |
| `fidelity` | Did the engine's facts survive into its prose? |
| `envelope` | Did its tool-call arguments need unwrapping to be usable? |

Facts are extracted from **what the tool returned on this run**, never from a
snapshot, so the harness stays correct as packs change. A dropped fact is
reported by name and value, so a failure tells you which one went missing
rather than just that something did.

## Running it

Needs an endpoint speaking Ollama's **native** chat API (`/api/chat`, with
tool support) and the Legesher engine importable. The OpenAI-compatible
surface (`/v1/chat/completions`) is not what this posts to — pointing it at
a vLLM-style server 404s every task as inconclusive.

```bash
# Ollama on the default port
uv run python libs/mcp/evals/grounding_eval.py <model-tag>

# Ollama listening somewhere else
uv run python libs/mcp/evals/grounding_eval.py <model-tag> \
    --base-url http://localhost:11435

# machine-readable, for collecting a scorecard across candidates
uv run python libs/mcp/evals/grounding_eval.py <model-tag> --json
```

Exit code is 0 only when every task hit its tool **and** mean fidelity is
≥ 90% — in the human-readable mode. `--json` always exits 0: the scorecard
consumer applies its own thresholds, so a collection run over failing
candidates is not itself a failure.

## Known limitations

Stated so the numbers are read as what they are:

- **Fidelity is substring presence.** A near-miss rendering that *contains*
  the true term (morphological variants — plurals, inflected forms) scores
  as survived. The per-fact "said instead" excerpt is the guard: read it.
- **Facts are extracted from the full tool result; the model is shown the
  first 4,000 characters.** A model that requests a very large result (the
  full dictionary) is graded against facts it may never have seen. Keep
  task prompts scoped to bounded requests.
- **`hit` checks the tool name, not its arguments.** A model that calls the
  right tool for the wrong language still hits; fidelity then measures
  faithful relay of whatever it fetched.
- **A run can exit 0 with a task's fidelity unmeasured** (`n/a`: the tool
  was hit but facts were never captured). The per-task lines show it; the
  exit code does not.

## Adding a task

Each task names the tool a competent client should reach for, and supplies a
`facts` function that pulls the engine's assertions out of that tool's result.
Keep those functions shape-aware — `lookup_keyword_mapping` nests its mappings
under category (`keywords`, `builtins`, …), `explain_in_language` returns a
`constructs` list, `translate_to_native` returns a source string whose every
line is a fact the prose must not silently rewrite.

## Reading a result

**High hit, low fidelity** is the dangerous case, not the reassuring one. It
means the model reached for the engine and then ignored what it said. The
harness calls this out explicitly rather than leaving it to be inferred from
two numbers.

**Envelope warnings** are an interoperability cost, not a capability failure.
Some models describe the whole call rather than just its arguments, nesting the
real payload under `parameters`. The arguments inside are usually well-formed;
the harness unwraps and reports rather than failing, because a strict client
would reject every call from such a model and the underlying tool use is fine.

## Recorded results

First run, 2026-08-13 — findings on CORE-1843. Note that a shortlist needs
several candidates; one model is a data point, not a recommendation.
