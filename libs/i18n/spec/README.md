# Pack spec — per-target profiles

The per-programming-language half of the pack contract (CORE-1503). Each
target owns a directory under `targets/`:

| File | Role |
| -- | -- |
| `profile.json` | Machine-readable target facts: version-token grammar, partitions, identifier grammar, contextual keywords, and the prompt-consumed rule strings (`prompt_rules`). |
| `GUIDE.md` | The prose the machine rules can't carry; rendered verbatim (minus its leading provenance/lint comments) into generation prompts as the "Target Guide" section. |

Loaded by `legesher_i18n.target_profiles.TargetProfileLoader`; consumed by the
`PromptBuilder` via its `target=` parameter. Per-target **data**, never
per-target code paths — if a difference can't be expressed as profile data,
extend the profile, don't branch the engine (CORE-1503's hard rule).

Shipped today: `javascript` only (the CORE-1608 trial slice). `python` has no
profile yet — the PromptBuilder's historical Python wording is the implicit
python profile, and migrating it here stays with CORE-1503, along with
`pack.schema.json`, generated engine types, and the conformance corpus.
