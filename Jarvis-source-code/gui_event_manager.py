#!/usr/bin/env python3
"""
GUI Event Manager — bridges JARVIS core to the web frontend.
Reuses existing jarvis_ui.py commands; does NOT replace brain logic.
"""
import threading
from collections import deque

# Internal in-memory subscribers (no external API keys exposed)
_subscribers = []

# Thread-safe event queue (last 50 events for reconnect)
_event_log = deque(maxlen=50)


def subscribe(ws_handler):
    """Register a WebSocket handler to receive broadcast events."""
    if ws_handler not in _subscribers:
        _subscribers.append(ws_handler)


def unsubscribe(ws_handler):
    if ws_handler in _subscribers:
        _subscribers.remove(ws_handler)


def broadcast(event: dict):
    """Broadcast event to all connected WebSocket clients and log locally."""
    import json
    _event_log.append(event)
    payload = json.dumps(event)
    dead = []
    for handler in list(_subscribers):
        try:
            # FastAPI websocket handler expects json() or send_json()
            if hasattr(handler, "send_json"):
                # This won't work synchronously in all contexts; handled via loop
                pass
            # Instead we rely on the server loop to poll event_log
            # (see gui_server.py)
        except Exception:
            dead.append(handler)
    for d in dead:
        unsubscribe(d)

# Convenience helpers called from jarvis_ui / jarvis_ai

def emit_status(status: str):
    broadcast({"type": "status", "status": status})


def emit_message(role: str, text: str):
    broadcast({"type": "message", "role": role, "text": text})


def emit_ai_provider(provider: str, model: str = ""):
    broadcast({"type": "ai_provider", "provider": provider, "model": model})


def emit_ollama_status(status: str, model: str = ""):
    """Broadcast Ollama online/offline status to the web frontend."""
    broadcast({"type": "ollama_status", "status": status, "model": model})


def emit_skill(name: str):
    broadcast({"type": "skill", "name": name})


def emit_memory(memory_type: str, status_text: str):
    broadcast({"type": "memory", "memory_type": memory_type, "status": status_text})


def emit_system(metric: str, value: float):
    broadcast({"type": "system", "metric": metric, "value": value})


def emit_timer(seconds_remaining: int):
    broadcast({"type": "timer", "seconds_remaining": seconds_remaining})


# ============================================================
# GOOGLE INTEGRATION EVENTS
# ============================================================

def emit_google_authenticating(service: str):
    """Emit event when Google authentication is starting."""
    broadcast({
        "type": "integration",
        "service": service,
        "status": "AUTHENTICATING"
    })


def emit_google_searching(service: str):
    """Emit event when Google API search is in progress."""
    broadcast({
        "type": "integration",
        "service": service,
        "status": "SEARCHING"
    })


def emit_google_result(service: str, result: dict):
    """Emit event when Google API search completes."""
    broadcast({
        "type": "integration",
        "service": service,
        "status": "RESULT",
        "data": result
    })


def emit_google_error(service: str, error: str):
    """Emit event when Google API operation fails."""
    broadcast({
        "type": "integration",
        "service": service,
        "status": "ERROR",
        "error": error
    })
