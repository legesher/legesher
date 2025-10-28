#!/usr/bin/env python3
"""
Test Translation Prompts

Purpose: Test the three model-specific prompts (Claude, GPT-4, Aya) on sample terms
         to verify output format and quality before running full batch translations.

Usage:
    # Test all 3 models on all 5 sample terms (requires API keys)
    python test-prompts.py --all

    # Test specific model
    python test-prompts.py --model claude
    python test-prompts.py --model gpt4
    python test-prompts.py --model aya

    # Test specific term
    python test-prompts.py --term def --model claude

    # Dry run (just show prompts without calling APIs)
    python test-prompts.py --dry-run

Version: 1.0
Created: 2025-10-28
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Sample terms for testing (different patterns and difficulty levels)
SAMPLE_TERMS = [
    {
        "term": "def",
        "type": "keyword",
        "pattern": "ACTION_KEYWORD",
        "difficulty": "EASY",
        "description": "Defines a function"
    },
    {
        "term": "return",
        "type": "keyword",
        "pattern": "ACTION_KEYWORD",
        "difficulty": "EASY",
        "description": "Returns a value from function"
    },
    {
        "term": "True",
        "type": "keyword",
        "pattern": "VALUE_CONSTANT",
        "difficulty": "EASY",
        "description": "Boolean true constant"
    },
    {
        "term": "isinstance",
        "type": "builtin",
        "pattern": "TYPE_CONSTRUCTOR",
        "difficulty": "MEDIUM",
        "description": "Check if object is instance of class"
    },
    {
        "term": "lambda",
        "type": "keyword",
        "pattern": "ACTION_KEYWORD",
        "difficulty": "HARD",
        "description": "Anonymous function"
    }
]

# Test languages (one from each tier)
TEST_LANGUAGES = [
    {"code": "es", "name": "Spanish", "family": "Romance", "tier": 1},
    {"code": "ar", "name": "Arabic", "family": "Semitic", "tier": 1},
    {"code": "zh", "name": "Chinese (Simplified)", "family": "Sino-Tibetan", "tier": 2},
    {"code": "hi", "name": "Hindi", "family": "Indo-Aryan", "tier": 2}
]


def load_prompt_template(model: str) -> str:
    """Load the prompt template for specified model."""
    prompts_dir = Path(__file__).parent / "prompts"

    if model == "claude":
        prompt_file = prompts_dir / "claude-translation-prompt.md"
    elif model == "gpt4":
        prompt_file = prompts_dir / "gpt4-translation-prompt.json"
    elif model == "aya":
        prompt_file = prompts_dir / "aya-translation-prompt.md"
    else:
        raise ValueError(f"Unknown model: {model}")

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        if model == "gpt4":
            return json.load(f)
        else:
            return f.read()


def load_tier1_context(term: str) -> str:
    """
    Load Tier 1 context document for a term.

    NOTE: This is a placeholder. In the full implementation, this would:
    1. Check if context already exists for this term
    2. If not, generate it using the Tier 1 template
    3. Return the complete context document

    For now, returns a minimal context for testing prompt structure.
    """
    return f"""# Python Keyword: `{term}` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 3.10+
**Difficulty:** EASY

## Quick Summary

[Context would be here for term '{term}']

## Code Examples FIRST

### Example 1: Minimal Usage
```python
# Example code showing {term}
```

[... rest of Tier 1 context template ...]
"""


def load_linguistic_standards() -> str:
    """Load linguistic standards document."""
    standards_file = Path(__file__).parent.parent.parent / "libs" / "i18n" / "docs" / "linguistic-standards.md"

    if not standards_file.exists():
        # Return excerpt for testing
        return """
Key Linguistic Standards:
- Register: Technical/formal (CS education vocabulary)
- ACTION keywords: Use infinitive verb forms
- VALUE constants: Use appropriate case conventions
- RTL languages: No diacritics, max 10 characters
- Consistency: Related terms must use same form
"""

    with open(standards_file, 'r', encoding='utf-8') as f:
        return f.read()


def prepare_claude_prompt(term: Dict, language: Dict, tier1_context: str, standards: str) -> str:
    """Prepare prompt for Claude model."""
    template = load_prompt_template("claude")

    # Fill in template variables
    prompt = template.replace("{TERM}", term["term"])
    prompt = prompt.replace("{keyword|builtin}", term["type"])
    prompt = prompt.replace("{TARGET_LANGUAGE}", language["name"])
    prompt = prompt.replace("{TIER_1_CONTEXT_DOCUMENT}", tier1_context)
    prompt = prompt.replace("{LINGUISTIC_STANDARDS_EXCERPT}", standards)

    # Add pattern-specific guidance
    if term["pattern"] == "ACTION_KEYWORD":
        prompt = prompt.replace("{infinitive|noun|adjective|masdar}", "infinitive")
        prompt = prompt.replace("{language_family}", language["family"])
        prompt = prompt.replace("{ACTION|STATE|VALUE|TYPE}", "ACTION")

    return prompt


def prepare_gpt4_prompt(term: Dict, language: Dict, tier1_context: str, standards: str) -> Dict:
    """Prepare prompt for GPT-4 model (returns dict for API call)."""
    config = load_prompt_template("gpt4")

    # Fill in user message template
    user_message = config["user_message_template"].format(
        term=term["term"],
        term_type=term["type"],
        target_language=language["name"],
        tier1_context=tier1_context,
        recommended_form="infinitive" if term["pattern"] == "ACTION_KEYWORD" else "noun",
        language_family=language["family"],
        pattern_type=term["pattern"],
        related_terms="return, break, continue",
        existing_translations_table="| return | retornar | infinitive |"
    )

    return {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "response_format": config["response_format"],
        "messages": [
            {"role": "system", "content": config["system_message"]},
            {"role": "user", "content": user_message}
        ]
    }


def prepare_aya_prompt(term: Dict, language: Dict, tier1_context: str, standards: str) -> str:
    """Prepare prompt for Aya model."""
    template = load_prompt_template("aya")

    # Fill in template variables
    prompt = template.replace("{TERM}", term["term"])
    prompt = prompt.replace("{keyword|builtin}", term["type"])
    prompt = prompt.replace("{TARGET_LANGUAGE}", language["name"])
    prompt = prompt.replace("{TIER_1_CONTEXT_SUMMARY}", tier1_context[:500] + "...")  # Shorter for Aya
    prompt = prompt.replace("{EXISTING_TRANSLATIONS}", "return → retornar (infinitive)")
    prompt = prompt.replace("{recommended_form}", "infinitive" if term["pattern"] == "ACTION_KEYWORD" else "noun")
    prompt = prompt.replace("{language_family}", language["family"])
    prompt = prompt.replace("{ACTION|STATE|VALUE}", term["pattern"].replace("_KEYWORD", ""))
    prompt = prompt.replace("{related_terms}", "return, break, continue")

    return prompt


def call_claude_api(prompt: str, dry_run: bool = False) -> Optional[str]:
    """Call Claude API with prepared prompt."""
    if dry_run:
        print("\n=== CLAUDE PROMPT (DRY RUN) ===")
        print(prompt[:1000] + "\n...\n" + prompt[-500:])
        return None

    # TODO: Implement actual API call
    # import anthropic
    # client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # response = client.messages.create(...)
    # return response.content[0].text

    print("⚠️  Claude API call not implemented yet (set --dry-run to test prompts)")
    return None


def call_gpt4_api(prompt_config: Dict, dry_run: bool = False) -> Optional[str]:
    """Call GPT-4 API with prepared prompt."""
    if dry_run:
        print("\n=== GPT-4 PROMPT (DRY RUN) ===")
        print(json.dumps(prompt_config, indent=2)[:1000] + "\n...")
        return None

    # TODO: Implement actual API call
    # from openai import OpenAI
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # response = client.chat.completions.create(**prompt_config)
    # return response.choices[0].message.content

    print("⚠️  GPT-4 API call not implemented yet (set --dry-run to test prompts)")
    return None


def call_aya_api(prompt: str, dry_run: bool = False) -> Optional[str]:
    """Call Aya API with prepared prompt."""
    if dry_run:
        print("\n=== AYA PROMPT (DRY RUN) ===")
        print(prompt[:1000] + "\n...\n" + prompt[-500:])
        return None

    # TODO: Implement actual API call
    # import cohere
    # client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
    # response = client.chat(model="aya-expanse-32b", message=prompt, temperature=0.5)
    # return response.text

    print("⚠️  Aya API call not implemented yet (set --dry-run to test prompts)")
    return None


def test_model_on_term(model: str, term: Dict, language: Dict, dry_run: bool = False):
    """Test a specific model on a specific term."""
    print(f"\n{'='*70}")
    print(f"Testing {model.upper()} on '{term['term']}' → {language['name']}")
    print(f"{'='*70}")

    # Load context and standards
    tier1_context = load_tier1_context(term["term"])
    standards = load_linguistic_standards()

    # Prepare model-specific prompt
    if model == "claude":
        prompt = prepare_claude_prompt(term, language, tier1_context, standards)
        response = call_claude_api(prompt, dry_run)
    elif model == "gpt4":
        prompt_config = prepare_gpt4_prompt(term, language, tier1_context, standards)
        response = call_gpt4_api(prompt_config, dry_run)
    elif model == "aya":
        prompt = prepare_aya_prompt(term, language, tier1_context, standards)
        response = call_aya_api(prompt, dry_run)
    else:
        raise ValueError(f"Unknown model: {model}")

    if response:
        print(f"\n{model.upper()} Response:")
        print(response)

    return response


def main():
    parser = argparse.ArgumentParser(description="Test translation prompts on sample terms")
    parser.add_argument("--model", choices=["claude", "gpt4", "aya", "all"], default="all",
                       help="Which model to test")
    parser.add_argument("--term", choices=[t["term"] for t in SAMPLE_TERMS] + ["all"], default="all",
                       help="Which term to test")
    parser.add_argument("--language", choices=[l["code"] for l in TEST_LANGUAGES] + ["all"], default="es",
                       help="Which language to test (default: Spanish)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show prompts without calling APIs")

    args = parser.parse_args()

    # Determine which models to test
    models = ["claude", "gpt4", "aya"] if args.model == "all" else [args.model]

    # Determine which terms to test
    terms = SAMPLE_TERMS if args.term == "all" else [t for t in SAMPLE_TERMS if t["term"] == args.term]

    # Determine which language to test
    languages = TEST_LANGUAGES if args.language == "all" else [l for l in TEST_LANGUAGES if l["code"] == args.language]

    print(f"\nTesting Configuration:")
    print(f"  Models: {', '.join(models)}")
    print(f"  Terms: {', '.join(t['term'] for t in terms)}")
    print(f"  Languages: {', '.join(l['name'] for l in languages)}")
    print(f"  Dry run: {args.dry_run}")

    # Run tests
    results = []
    for model in models:
        for term in terms:
            for language in languages:
                try:
                    response = test_model_on_term(model, term, language, args.dry_run)
                    results.append({
                        "model": model,
                        "term": term["term"],
                        "language": language["name"],
                        "success": response is not None,
                        "response": response
                    })
                except Exception as e:
                    print(f"❌ Error testing {model} on {term['term']}: {e}")
                    results.append({
                        "model": model,
                        "term": term["term"],
                        "language": language["name"],
                        "success": False,
                        "error": str(e)
                    })

    # Print summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    total = len(results)
    success = sum(1 for r in results if r.get("success", False))
    print(f"Total tests: {total}")
    print(f"Successful: {success}")
    print(f"Failed: {total - success}")

    if args.dry_run:
        print("\n✅ Dry run complete. Prompts are ready for testing with actual API calls.")
        print("\nNext steps:")
        print("  1. Set API keys: ANTHROPIC_API_KEY, OPENAI_API_KEY, COHERE_API_KEY")
        print("  2. Run without --dry-run to test actual API calls")
        print("  3. Review output format and quality")
        print("  4. Adjust prompts if needed")


if __name__ == "__main__":
    main()
