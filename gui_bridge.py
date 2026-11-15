#!/usr/bin/env python3
"""Bridge between browser /command input and existing jarvis_ui brain."""
import threading, queue, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from gui_event_manager import emit_status, emit_message, emit_skill, emit_timer
# Queue shared with server
from gui_server import command_queue

def bridge_loop():
    # Import process_command from jarvis_ui safely
    try:
        from jarvis_ui import process_command, post_ui, set_state
    except Exception as e:
        print("[Bridge] import error:", e)
        # Fallback: log command only
        while True:
            try:
                cmd = command_queue.get(timeout=2)
                print("[GUI CMD]", cmd)
            except Exception:
                pass
            time.sleep(0.5)
            continue

    print("[Bridge] Running process_command loop...")
    while True:
        try:
            cmd = command_queue.get(timeout=2)
            # Call brain directly in this thread
            process_command(cmd)
        except Exception as e:
            print("[Bridge] process_command error:", e)
            time.sleep(0.5)

# Auto-start when module loaded
threading.Thread(target=bridge_loop, daemon=True).start()
