"""Tests for the env-overridable model configuration (CORE-1804)."""

from __future__ import annotations

from legesher_i18n.model_config import (
    ANTHROPIC_MODEL_ENV,
    DEFAULT_ANTHROPIC_MODEL,
    anthropic_model,
)


def test_default_model_without_env(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_MODEL_ENV, raising=False)
    assert anthropic_model() == DEFAULT_ANTHROPIC_MODEL


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv(ANTHROPIC_MODEL_ENV, "claude-test-override")
    assert anthropic_model() == "claude-test-override"


def test_blank_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv(ANTHROPIC_MODEL_ENV, "   ")
    assert anthropic_model() == DEFAULT_ANTHROPIC_MODEL


def test_provider_and_generation_model_share_the_config(monkeypatch):
    """Both constructors resolve the model from the one config source."""
    monkeypatch.setenv(ANTHROPIC_MODEL_ENV, "claude-config-test")

    from legesher_i18n.api.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider(api_key="sk-ant-test")
    assert provider.model == "claude-config-test"

    import sys
    from pathlib import Path

    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from translate.models.claude_model import ClaudeModel

    model = ClaudeModel(dry_run=True)
    assert model.model == "claude-config-test"
    assert model.get_model_version() == "claude-config-test"
