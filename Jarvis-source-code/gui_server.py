#!/usr/bin/env python3
"""
FastAPI + WebSocket GUI server for JARVIS.
Local only (127.0.0.1:8000). No .env exposure. No API keys sent.
"""
import asyncio
import json
import os
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
import threading, queue

from gui_event_manager import (
    _event_log,
    subscribe,
    unsubscribe,
    emit_status,
    emit_message,
    emit_ai_provider,
)

app = FastAPI(title="JARVIS GUI Gateway")

# Active WebSocket connections
clients = set()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    subscribe(websocket)  # tracked but actual send uses clients loop
    # Send recent history for reconnect
    for ev in list(_event_log)[-10:]:
        try:
            await websocket.send_json(ev)
        except Exception:
            pass
    try:
        while True:
            # Keep alive; events pushed by gui_event_manager + server loop
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(websocket)
        unsubscribe(websocket)


# Background broadcaster: pushes events from _event_log to all clients
async def broadcaster():
    sent_ids = set()
    while True:
        await asyncio.sleep(0.5)
        # Send only newest events not yet broadcast (dedup by content hash)
        for ev in list(_event_log)[-3:]:
            ev_id = json.dumps(ev, sort_keys=True)
            if ev_id not in sent_ids:
                sent_ids.add(ev_id)
                for c in list(clients):
                    try:
                        await c.send_json(ev)
                    except Exception:
                        clients.discard(c)
        # Trim dedup set so memory stays bounded
        if len(sent_ids) > 200:
            sent_ids.clear()


@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcaster())
    # Initialize with standby
    emit_status("STANDBY")
    emit_ai_provider("Ollama", "qwen2.5:7b")
    emit_message("jarvis", "GUI connected. JARVIS core online.")


# Queue to feed browser commands into JARVIS brain (from jarvis_ui process_command)
command_queue = queue.Queue()

# Import bridge to activate brain loop
try:
    import gui_bridge
except Exception as e:
    print("[Server] bridge import error:", e)

# Direct endpoint — puts command into shared queue; bridge feeds brain
@app.post("/command")
async def command_endpoint(req: dict):
    cmd_text = req.get("text", "").strip()
    if cmd_text:
        command_queue.put(cmd_text)
        emit_message("master", cmd_text)
        emit_status("THINKING")
    return {"status": "received", "command": cmd_text}

# Service static frontend at root
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")
