"""
Model configuration for Academic Copilot.

- Locally:     uses Ollama (llama3.1:8b) — no API keys needed
- On GCP:      uses Gemini (primary) with Anthropic Claude (fallback)

Set USE_CLOUD_MODELS=true in your environment to force cloud models locally.
"""
from __future__ import annotations
import os
import logging

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel

logger = logging.getLogger(__name__)

# ── Detect environment ─────────────────────────────────────
# Cloud Run always sets K_SERVICE. We also allow manual override.
_IS_CLOUD = bool(os.getenv("K_SERVICE") or os.getenv("USE_CLOUD_MODELS"))

# ── Model names ────────────────────────────────────────────
OLLAMA_MODEL     = "ollama:llama3.1:8b"
GEMINI_MODEL     = "google-gla:gemini-2.0-flash"
ANTHROPIC_MODEL  = "anthropic:claude-3-5-haiku-latest"


def get_model() -> str | Model:
    """
    Return the right model for the current environment.

    Local  → ollama:llama3.1:8b
    Cloud  → Gemini 2.0 Flash with Anthropic Claude as fallback
    """
    if not _IS_CLOUD:
        logger.info("Running locally — using Ollama (%s)", OLLAMA_MODEL)
        return OLLAMA_MODEL

    gemini_key    = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_key and not anthropic_key:
        raise RuntimeError(
            "Running in cloud mode but neither GEMINI_API_KEY nor "
            "ANTHROPIC_API_KEY is set. Add at least one API key."
        )

    if gemini_key and anthropic_key:
        logger.info(
            "Cloud mode — primary: %s, fallback: %s",
            GEMINI_MODEL, ANTHROPIC_MODEL,
        )
        from pydantic_ai.models.gemini import GeminiModel
        from pydantic_ai.models.anthropic import AnthropicModel
        return FallbackModel(
            GeminiModel("gemini-2.0-flash", api_key=gemini_key),
            AnthropicModel("claude-3-5-haiku-latest", api_key=anthropic_key),
        )

    if gemini_key:
        logger.info("Cloud mode — using Gemini only (no Anthropic key found)")
        return GEMINI_MODEL

    logger.info("Cloud mode — using Anthropic only (no Gemini key found)")
    return ANTHROPIC_MODEL


def make_agent(system_prompt: str, **kwargs) -> Agent:
    """
    Convenience wrapper — creates an Agent with the right model
    and sensible shared defaults.
    """
    return Agent(
        get_model(),
        output_type=str,
        system_prompt=system_prompt,
        retries=2,
        output_retries=3,
        defer_model_check=True,
        **kwargs,
    )
