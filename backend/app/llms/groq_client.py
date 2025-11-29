import os
import json
import logging
import requests
from typing import Optional

# Simple Groq client wrapper. Uses environment variables:
# - GROQ_API_KEY (required)
# - GROQ_API_URL (optional, defaults to a common Groq endpoint)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.ai/v1/llm")

# Preferred and fallback model names
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
FALLBACK_MODEL = "llama3-8b-8192"

logger = logging.getLogger(__name__)


def _parse_response(resp_json: dict) -> str:
    """Try several common response shapes and return text output."""
    # Common shapes: {"output": "..."}, {"choices": [{"text": "..."}]}
    if not isinstance(resp_json, dict):
        return str(resp_json)

    if "output" in resp_json and isinstance(resp_json["output"], str):
        return resp_json["output"]

    choices = resp_json.get("choices") or resp_json.get("outputs")
    if isinstance(choices, list) and len(choices) > 0:
        first = choices[0]
        if isinstance(first, dict):
            # typical places
            for key in ("text", "content", "message", "output"):
                if key in first and isinstance(first[key], str):
                    return first[key]
            # nested message
            msg = first.get("message") or first.get("content")
            if isinstance(msg, dict):
                if "text" in msg:
                    return msg["text"]
                if "content" in msg and isinstance(msg["content"], str):
                    return msg["content"]
        elif isinstance(first, str):
            return first

    # Best-effort fallback: pretty-print JSON
    return json.dumps(resp_json)


def call_groq(prompt: str, model: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.1) -> str:
    """Call the Groq LLM API and return the text output.

    This is a generic wrapper: adjust `GROQ_API_URL` and body to match the exact
    Groq API you are using.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Determine models to try: provided model first, then primary, then fallback
    initial_model = model or PRIMARY_MODEL
    models_to_try = [initial_model]
    if PRIMARY_MODEL not in models_to_try:
        models_to_try.append(PRIMARY_MODEL)
    if FALLBACK_MODEL not in models_to_try:
        models_to_try.append(FALLBACK_MODEL)

    last_exc = None
    for m in models_to_try:
        payload = {
            # many providers use `model` and `prompt` keys; if your Groq API differs,
            # set GROQ_API_URL appropriately or edit this payload.
            "model": m,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            logger.debug("Calling Groq model=%s url=%s", m, GROQ_API_URL)
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()

            try:
                data = resp.json()
            except ValueError:
                return resp.text

            return _parse_response(data)

        except requests.exceptions.RequestException as e:
            # Save exception and try next model
            logger.warning("Groq request failed for model=%s: %s", m, e)
            last_exc = e
            # try next model
            continue

    # If we reach here, all attempts failed
    err_msg = f"All Groq model attempts failed (tried: {models_to_try}). Last error: {last_exc}"
    logger.error(err_msg)
    raise RuntimeError(err_msg)
