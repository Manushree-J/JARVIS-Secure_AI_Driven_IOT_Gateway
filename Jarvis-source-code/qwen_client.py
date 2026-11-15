#!/usr/bin/env python3
"""
qwen_client.py — Dedicated Ollama / Qwen client for JARVIS.

This is the ONLY text-LLM interface in the JARVIS pipeline.

Architecture:
    JARVIS → qwen_client → Ollama (qwen2.5:7b) → ElevenLabs TTS

Design goals:
    - No cloud fallback. If Ollama is down, the caller gets a clean
      error and JARVIS reports it to the user instead of crashing.
    - Health-checked at startup and on every call so the GUI can show
      Ollama online/offline status.
    - Thin wrapper around the OpenAI-compatible endpoint Ollama exposes
      at http://127.0.0.1:11434/v1.
"""

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5:7b")
QWEN_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
QWEN_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

# Connection tuning
REQUEST_TIMEOUT = int(os.getenv("QWEN_REQUEST_TIMEOUT", "90"))
MAX_RETRIES = int(os.getenv("QWEN_MAX_RETRIES", "2"))

# Module-level client (lazily created so import never fails)
_client = None


def _get_client():
    """Return a shared OpenAI client pointed at Ollama's /v1 endpoint."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=QWEN_BASE_URL,
            api_key=QWEN_API_KEY,
            timeout=REQUEST_TIMEOUT,
        )
    return _client


# ============================================================
# HEALTH CHECK
# ============================================================

def is_ollama_online(timeout=3):
    """
    Return True if Ollama is reachable and the configured model is present.

    Uses Ollama's native /api/tags endpoint (no API key needed) so this
    works even when the OpenAI-compatible client would raise on auth.
    """
    try:
        import requests
        resp = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=timeout,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        tags = [t.get("name", "") for t in data.get("models", [])]
        return QWEN_MODEL in tags
    except Exception:
        return False


# ============================================================
# CORE ASK
# ============================================================

def ask(
    messages,
    max_tokens=256,
    temperature=0.7,
):
    """
    Send a chat-completion request to local Qwen via Ollama.

    Args:
        messages: list of {"role": ..., "content": ...} dicts.
        max_tokens: max tokens for the response.
        temperature: sampling temperature.

    Returns:
        str — the assistant's reply text.

    Raises:
        RuntimeError with a clear, user-facing message if Ollama is
        unreachable or the model is missing. The caller (ask_ai) catches
        this and reports it to Master instead of crashing or falling
        back to a cloud model.
    """
    if not is_ollama_online():
        raise RuntimeError(
            "Ollama is not running or the qwen2.5:7b model is not loaded. "
            "Start it with: ollama serve  &&  ollama pull qwen2.5:7b"
        )

    client = _get_client()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=QWEN_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            reply = response.choices[0].message.content
            if not reply:
                raise RuntimeError("Qwen returned an empty response.")
            return reply.strip()
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)

    raise RuntimeError(
        f"Qwen (Ollama) request failed after {MAX_RETRIES} attempts: {last_error}"
    )


# ============================================================
# STATUS EVENT (for GUI)
# ============================================================

def emit_ollama_status():
    """
    Broadcast the current Ollama online/offline status to the GUI.

    Safe to call from any thread — gui_event_manager.broadcast is
    thread-safe (it just appends to a deque).
    """
    try:
        from gui_event_manager import emit_ollama_status as _emit
        online = is_ollama_online()
        _emit("ONLINE" if online else "OFFLINE", QWEN_MODEL)
    except Exception:
        # Never let status reporting break the main pipeline.
        pass


# ============================================================
# MODULE-LEVEL STATUS (cached, refreshed periodically)
# ============================================================

_last_status_check = 0
_status_cache = False
_status_cache_ttl = 5  # seconds


def cached_ollama_online():
    """Return a cached health result to avoid hammering Ollama."""
    global _last_status_check, _status_cache
    now = time.time()
    if now - _last_status_check > _status_cache_ttl:
        _status_cache = is_ollama_online()
        _last_status_check = now
    return _status_cache