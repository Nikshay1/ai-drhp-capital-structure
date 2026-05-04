"""Thin LLM client wrapper.

Centralises all LLM calls behind a single interface so that:
  - We can swap providers (Anthropic ↔ OpenAI) in one place.
  - We enforce structured JSON output via tool-use / response_format.
  - Token usage is logged for cost tracking.

Currently backed by Anthropic Claude (Sonnet for extraction, Haiku for
classification).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLASSIFICATION_MODEL = os.getenv("DRHP_CLASSIFICATION_MODEL", "claude-sonnet-4-20250514")
EXTRACTION_MODEL = os.getenv("DRHP_EXTRACTION_MODEL", "claude-sonnet-4-20250514")

_total_input_tokens = 0
_total_output_tokens = 0


def _get_client():
    """Lazy-init Anthropic client."""
    import anthropic
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_llm_structured(
    prompt: str,
    response_model: Type[T],
    *,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> T:
    """Call the LLM and parse the response into a Pydantic model.
    
    Uses a system prompt that instructs the model to return valid JSON
    matching the schema. Falls back to extracting JSON from the response
    text if the model wraps it in markdown fences.
    """
    global _total_input_tokens, _total_output_tokens

    model = model or EXTRACTION_MODEL
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)

    full_system = (
        f"{system}\n\n" if system else ""
    ) + (
        f"You MUST respond with valid JSON matching this schema:\n"
        f"```json\n{schema_json}\n```\n"
        f"Do NOT include any text outside the JSON object. "
        f"Do NOT wrap the JSON in markdown fences."
    )

    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=full_system,
        messages=[{"role": "user", "content": prompt}],
    )

    _total_input_tokens += response.usage.input_tokens
    _total_output_tokens += response.usage.output_tokens
    log.debug(
        "LLM call: model=%s, input_tokens=%d, output_tokens=%d",
        model, response.usage.input_tokens, response.usage.output_tokens,
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    return response_model.model_validate_json(raw)


def call_llm_text(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Call the LLM and return raw text."""
    global _total_input_tokens, _total_output_tokens

    model = model or EXTRACTION_MODEL
    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system or "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
    )

    _total_input_tokens += response.usage.input_tokens
    _total_output_tokens += response.usage.output_tokens

    return response.content[0].text.strip()


def get_token_usage() -> dict[str, int]:
    """Return cumulative token usage."""
    return {
        "total_input_tokens": _total_input_tokens,
        "total_output_tokens": _total_output_tokens,
    }
