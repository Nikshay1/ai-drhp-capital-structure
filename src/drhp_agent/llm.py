"""Thin LLM client wrapper.

Centralises all LLM calls behind a single interface so that:
  - We can swap providers in one place.
  - We enforce structured JSON output via response_format / system prompts.
  - Token usage is logged for cost tracking.

Backed by OpenAI (GPT-4o for extraction, GPT-4o-mini for classification).
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLASSIFICATION_MODEL = os.getenv("DRHP_CLASSIFICATION_MODEL", "gpt-4o-mini")
EXTRACTION_MODEL = os.getenv("DRHP_EXTRACTION_MODEL", "gpt-4o")

_total_input_tokens = 0
_total_output_tokens = 0


def _get_client():
    """Lazy-init OpenAI client."""
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


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
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ],
    )

    usage = response.usage
    if usage:
        _total_input_tokens += usage.prompt_tokens
        _total_output_tokens += usage.completion_tokens
        log.debug(
            "LLM call: model=%s, input_tokens=%d, output_tokens=%d",
            model, usage.prompt_tokens, usage.completion_tokens,
        )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
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
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system or "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    usage = response.usage
    if usage:
        _total_input_tokens += usage.prompt_tokens
        _total_output_tokens += usage.completion_tokens

    return response.choices[0].message.content.strip()


def get_token_usage() -> dict[str, int]:
    """Return cumulative token usage."""
    return {
        "total_input_tokens": _total_input_tokens,
        "total_output_tokens": _total_output_tokens,
    }
