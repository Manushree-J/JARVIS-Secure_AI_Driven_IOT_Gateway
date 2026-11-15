import customtkinter as ctk
import tkinter as tk
import threading
import queue
import time
import math
import os
from datetime import datetime

# ============================================================
# JARVIS UI + BACKGROUND ENGINE
# ============================================================

from memory_writer import (
    start_conversation,
    save_message,
    end_conversation,
    save_memory,
)

from jarvis_ai import ask_ai

# Wake-word import guard
try:
    from wake_word import wait_for_wake_word
except Exception:
    def wait_for_wake_word(): pass

# Speech import guard (listen/speak for background loop)
try:
    from speech import speak, listen
except Exception:
    def speak(text): pass
    def listen(): return ""

# Background jarvis_ai engine (no destruction of jarvis_ui)
try:
    import jarvis_ai, threading
    def _start_jarvis_ai_bg():
        try:
            jarvis_ai.start_mqtt_listener()  # ESP32 preserved
        except Exception: pass
            # Voice loop runs when jarvis_ai.__main__ active; here we just keep MQTT/AI ready
    _bg = threading.Thread(target=lambda: _start_jarvis_ai_bg(), daemon=True, name="jarvis_ai_bg")
    _bg.start()
    print("[BG] jarvis_ai background started inside jarvis_ui")
except Exception as e: print("[BG] jarvis_ai bg skipped:", e)


APP_TITLE = "JARVIS"
WIDTH = 1400
HEIGHT = 850
INACTIVITY_TIMEOUT = 300

BG = "#03060B"
ANIM_BG = "#02040A"
PANEL = "#080E16"
PANEL2 = "#0A1220"
BORDER = "#0F2B3D"
CYAN = "#00D4FF"
BLUE = "#1677FF"
GREEN = "#00FF9C"
ORANGE = "#FFB020"
RED = "#FF4D6D"
WHITE = "#EAF7FF"
TEXT = "#A9C4D6"
MUTED = "#587080"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("JARVIS — AI Core")
app.geometry(f"{WIDTH}x{HEIGHT}")
app.minsize(1100, 700)

ui_queue = queue.Queue()
shutdown_event = threading.Event()

current_state = "STANDBY"
conversation_active = False
conversation_started = False
last_activity = time.time()
animation_time = 0.0


try:
    from gui_event_manager import emit_status, emit_message, emit_ai_provider, emit_skill, emit_memory, emit_timer
except Exception:
    def emit_status(s): pass
    def emit_message(r, t): pass
    def emit_ai_provider(p, m=""): pass
    def emit_skill(n): pass
    def emit_memory(t, s): pass
    def emit_timer(sec): pass

# ============================================================
# SAFE UI QUEUE
# ============================================================

def post_ui(function, *args):
    ui_queue.put((function, args))


def process_ui_queue():
    try:
        while True:
            function, args = ui_queue.get_nowait()
            try:
                function(*args)
            except Exception as e:
                print("UI update error:", e)
    except queue.Empty:
        pass

    if not shutdown_event.is_set():
        app.after(30, process_ui_queue)


# Faster update loop — start after definition
app.after(16, process_ui_queue)


# ============================================================
# HEADER
# ============================================================

header = ctk.CTkFrame(app, fg_color=BG, corner_radius=0)
header.pack(fill="x", padx=28, pady=(20, 0))
header.grid_columnconfigure(1, weight=1)

brand = ctk.CTkLabel(
    header, text="JARVIS",
    font=("Orbitron", 36, "bold"),
    text_color="#EAF7FF"
)
brand.grid(row=0, column=0, sticky="w")

subtitle = ctk.CTkLabel(
    header,
    text="AI CORE  •  VISUAL PROCESSING  •  VOICE INTERFACE",
    font=("Orbitron", 10, "bold"),
    text_color="#00D4FF"
)
subtitle.grid(row=1, column=0, sticky="w")

system_status = ctk.CTkLabel(
    header,
    text="● ONLINE",
    font=("Orbitron", 12, "bold"),
    text_color="#00FF9C"
)
system_status.grid(row=0, column=2, sticky="e", padx=20)

clock_label = ctk.CTkLabel(
    header,
    text="",
    font=("Share Tech Mono", 13),
    text_color=MUTED
)
clock_label.grid(row=1, column=2, sticky="e", padx=20)


# ============================================================
# MAIN
# ============================================================

main = ctk.CTkFrame(app, fg_color=BG, corner_radius=0)
main.pack(fill="both", expand=True, padx=28, pady=20)

main.grid_columnconfigure(0, weight=0, minsize=430)
main.grid_columnconfigure(1, weight=1)
main.grid_rowconfigure(0, weight=1)


# ============================================================
# LEFT / CORE
# ============================================================

left = ctk.CTkFrame(
    main,
    fg_color=PANEL,
    border_width=1,
    border_color=BORDER,
    corner_radius=18
)
left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

ctk.CTkLabel(
    left,
    text="JARVIS CORE",
    font=("Orbitron", 13, "bold"),
    text_color="#00D4FF"
).pack(pady=(24, 5))


core_canvas = tk.Canvas(
    left,
    width=390,
    height=390,
    bg=PANEL,
    highlightthickness=0,
    bd=0
)
core_canvas.pack(pady=8)

CX, CY = 195, 195

orbit1 = core_canvas.create_oval(
    42, 42, 348, 348, outline="#102C3D"
)
orbit2 = core_canvas.create_oval(
    65, 65, 325, 325, outline="#12364A"
)
orbit3 = core_canvas.create_oval(
    92, 92, 298, 298, outline="#15465C"
)

outer = core_canvas.create_oval(
    55, 55, 335, 335,
    outline=CYAN, width=3
)
middle = core_canvas.create_oval(
    92, 92, 298, 298,
    outline=CYAN, width=2
)
inner = core_canvas.create_oval(
    130, 130, 260, 260,
    outline=CYAN, width=3
)
center = core_canvas.create_oval(
    165, 165, 225, 225,
    fill=CYAN, outline=CYAN
)

# Light scan line that rotates
scan_line = core_canvas.create_oval(
    55, 55, 335, 335,
    outline="", width=0
)

# Particles stay atomic
particles = []
for i in range(16):
    item = core_canvas.create_oval(0, 0, 0, 0, fill=CYAN, outline="")
    particles.append({
        "id": item,
        "angle": math.pi * 2 * i / 16,
        "radius": 150 + (i % 4) * 7,
        "speed": 0.006 + (i % 4) * 0.002,
        "size": 2 + i % 3
    })


# ============================================================
# STATE
# ============================================================

state_label = ctk.CTkLabel(
    left,
    text="STANDBY",
    font=("Share Tech Mono", 25, "bold"),
    text_color=CYAN
)
state_label.pack(pady=(0, 2))

state_detail = ctk.CTkLabel(
    left,
    text='Awaiting wake word — say "Hey Jarvis"',
    font=("Orbitron", 12),
    text_color=MUTED
)
state_detail.pack(pady=(0, 18))

indicator_frame = ctk.CTkFrame(
    left, fg_color=PANEL2, corner_radius=12
)
indicator_frame.pack(fill="x", padx=25, pady=(0, 20))


def indicator(row, name):
    dot = ctk.CTkLabel(
        indicator_frame, text="●",
        font=("Orbitron", 13), text_color=GREEN
    )
    dot.grid(row=row, column=0, padx=(15, 7), pady=7)

    text = ctk.CTkLabel(
        indicator_frame, text=name,
        font=("Share Tech Mono", 11), text_color=TEXT
    )
    text.grid(row=row, column=1, sticky="w", pady=7)
    indicator_frame.grid_columnconfigure(1, weight=1)
    return dot


wake_dot = indicator(0, "WAKE WORD")
ai_dot = indicator(1, "AI / LOCAL QWEN")
memory_dot = indicator(2, "MEMORY / CHROMADB")
voice_dot = indicator(3, "VOICE / TTS")

floating_dots = []

# Create floating dots on core canvas
for i in range(20):
    x = CX + math.cos(i * 0.5) * (100 + (i % 5) * 20)
    y = CY + math.sin(i * 0.7) * (100 + (i % 4) * 15)
    d = core_canvas.create_oval(
        x-3, y-3, x+3, y+3,
        fill="#587080", outline="#587080"
    )
    floating_dots.append({"id": d, "x": x, "y": y, "speed": 0.003 + 0.002*(i%3), "angle": i*0.3})


# ============================================================
# CORE ANIMATION
# ============================================================

def animate_core():
    global animation_time
    animation_time += 0.03

    # Cinematic color by state
    colors = {
        "STANDBY": "#00D4FF",
        "LISTENING": "#00D4FF",
        "THINKING": "#FFB020",
        "SPEAKING": "#00FF9C",
        "OPENING": "#1677FF",
        "ERROR": "#FF4D6D",
        "OFFLINE": "#FF4D6D",
    }
    color = colors.get(current_state, "#00D4FF")

    # Pulse base
    if current_state == "LISTENING":
        base = 150 + math.sin(animation_time * 3) * 22
    elif current_state == "THINKING":
        base = 150 + math.sin(animation_time * 5) * 16
    elif current_state == "SPEAKING":
        base = 155 + math.sin(animation_time * 4) * 24
    else:
        base = 140 + math.sin(animation_time) * 6

    # Orbitals
    core_canvas.coords(outer, CX-base, CY-base, CX+base, CY+base)
    core_canvas.coords(middle, CX-base*0.73, CY-base*0.73, CX+base*0.73, CY+base*0.73)
    core_canvas.coords(inner, CX-base*0.40, CY-base*0.40, CX+base*0.40, CY+base*0.40)
    core_canvas.itemconfig(outer, outline=color, width=3)
    core_canvas.itemconfig(middle, outline=color, width=2)
    core_canvas.itemconfig(inner, outline=color, width=3)

    # Glowing center
    center_size = 28 + (math.sin(animation_time * 4) + 1) * 10
    core_canvas.coords(
        center, CX-center_size, CY-center_size,
        CX+center_size, CY+center_size
    )
    core_canvas.itemconfig(center, fill=color, outline=color)

    # Rotating light scan line (Tony Stark-style arc)
    scan_angle = animation_time * 2.5
    scan_r = 120 + math.sin(animation_time * 3) * 10
    scan_x1 = CX + math.cos(scan_angle) * (scan_r - 30)
    scan_y1 = CY + math.sin(scan_angle) * (scan_r - 30)
    scan_x2 = CX + math.cos(scan_angle + 0.3) * scan_r
    scan_y2 = CY + math.sin(scan_angle + 0.3) * scan_r
    # Draw as temporary arc by moving an oval (simplified)
    core_canvas.coords(scan_line, scan_x1, scan_y1, scan_x2, scan_y2)
    core_canvas.itemconfig(scan_line, outline=color, width=3)

    # Particles orbit
    for p in particles:
        p["angle"] += p["speed"]
        x = CX + math.cos(p["angle"]) * p["radius"]
        y = CY + math.sin(p["angle"]) * p["radius"]
        s = p["size"]
        core_canvas.coords(p["id"], x-s, y-s, x+s, y+s)
        core_canvas.itemconfig(p["id"], fill=color, outline="")

    # Floating dots
    for d in floating_dots:
        d["angle"] += d["speed"] * 0.4
        d["x"] = CX + math.cos(d["angle"]) * 120
        d["y"] = CY + math.sin(d["angle"] * 1.3) * 100
        core_canvas.coords(d["id"], d["x"]-3, d["y"]-3, d["x"]+3, d["y"]+3)
        dot_color = dot_colors.get(current_state, "#587080")
        core_canvas.itemconfig(d["id"], fill=dot_color, outline=dot_color)

    app.after(35, animate_core)


# ============================================================
# RIGHT / CONVERSATION
# ============================================================

right = ctk.CTkFrame(
    main,
    fg_color=PANEL,
    border_width=1,
    border_color=BORDER,
    corner_radius=18
)
right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
right.grid_rowconfigure(1, weight=1)
right.grid_columnconfigure(0, weight=1)

conversation_header = ctk.CTkFrame(
    right, fg_color="transparent"
)
conversation_header.grid(
    row=0, column=0, sticky="ew",
    padx=25, pady=(20, 10)
)
conversation_header.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(
    conversation_header,
    text="CONVERSATION",
    font=("Orbitron", 14, "bold"),
    text_color=WHITE
).grid(row=0, column=0, sticky="w")

session_label = ctk.CTkLabel(
    conversation_header,
    text="SESSION: STANDBY",
    font=("Share Tech Mono", 10),
    text_color=MUTED
)
session_label.grid(row=0, column=1, sticky="e")


chatbox = ctk.CTkTextbox(
    right,
    font=("Share Tech Mono", 13),
    text_color=TEXT,
    fg_color="#070C12",
    border_width=1,
    border_color=BORDER,
    corner_radius=12,
    wrap="word"
)
chatbox.grid(
    row=1, column=0, sticky="nsew",
    padx=25, pady=(0, 15)
)
chatbox.configure(state="disabled")


def add_message(sender, text):
    def update():
        chatbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")

        chatbox.insert(
            "end",
            f"\n[{timestamp}] {sender.upper()}\n",
        )
        chatbox.insert("end", f"{text}\n")
        chatbox.configure(state="disabled")
        chatbox.see("end")

    post_ui(update)


# ============================================================
# MANUAL COMMAND INPUT
# ============================================================

input_frame = ctk.CTkFrame(
    right, fg_color=PANEL2, corner_radius=12
)
input_frame.grid(
    row=2, column=0, sticky="ew",
    padx=25, pady=(0, 20)
)
input_frame.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(
    input_frame,
    placeholder_text='Type a command or say "Hey Jarvis"...',
    height=48,
    font=("Orbitron", 13),
    fg_color="#070C12",
    border_color=BORDER,
    text_color=WHITE
)
entry.grid(
    row=0, column=0, sticky="ew",
    padx=(12, 8), pady=12
)


def send_typed_command():
    command = entry.get().strip()
    if not command:
        return

    entry.delete(0, "end")

    threading.Thread(
        target=process_command,
        args=(command,),
        daemon=True
    ).start()


send_button = ctk.CTkButton(
    input_frame,
    text="SEND",
    width=100,
    height=42,
    font=("Orbitron", 12, "bold"),
    fg_color="#12364A",
    hover_color="#16516A",
    command=send_typed_command
)
send_button.grid(
    row=0, column=1,
    padx=(0, 12), pady=12
)

entry.bind(
    "<Return>",
    lambda event: send_typed_command()
)


# ============================================================
# FOOTER
# ============================================================

footer = ctk.CTkFrame(
    app, fg_color=BG, corner_radius=0
)
footer.pack(fill="x", padx=28, pady=(0, 15))

ctk.CTkLabel(
    footer,
    text="VISION  •  SPEECH  •  MEMORY  •  SKILLS  •  HYBRID AI",
    font=("Share Tech Mono", 9),
    text_color="#587080"
).pack(side="left")

ctk.CTkLabel(
    footer,
    text="JARVIS CORE  •  ACTIVE",
    font=("Share Tech Mono", 9, "bold"),
    text_color="#00D4FF"
).pack(side="right")


# ============================================================
# STATE MANAGEMENT
# ============================================================

def set_state(state):
    global current_state
    current_state = state
    # Update floating dots color based on state (if defined)
    try:
        dot_colors = {
            "STANDBY": "#587080",
            "LISTENING": "#00FF9C",
            "THINKING": "#1677FF",
            "SPEAKING": "#FFB020",
            "OFFLINE": "#FF4D6D",
            "ERROR": "#FF4D6D"
        }
        dot_color = dot_colors.get(state, "#00D9FF")
        for d in floating_dots:
            if isinstance(d, dict) and "id" in d:
                core_canvas.itemconfig(d["id"], fill=dot_color, outline=dot_color)
    except NameError:
        pass

    descriptions = {
        "STANDBY": 'Awaiting wake word — say "Hey Jarvis"',
        "LISTENING": "Listening for Master",
        "THINKING": "Processing your command",
        "SPEAKING": "JARVIS is responding",
        "OPENING": "Executing local system command",
        "ERROR": "System encountered an error",
        "OFFLINE": "JARVIS is shutting down",
    }

    colors = {
        "STANDBY": CYAN,
        "LISTENING": CYAN,
        "THINKING": ORANGE,
        "SPEAKING": GREEN,
        "OPENING": BLUE,
        "ERROR": RED,
        "OFFLINE": RED,
    }

    color = colors.get(state, CYAN)

    emit_status(state)

    state_label.configure(
        text=state,
        text_color=color
    )
    state_detail.configure(
        text=descriptions.get(state, "JARVIS active")
    )
    session_label.configure(
        text=f"SESSION: {state}"
    )

    if state == "STANDBY":
        system_status.configure(
            text="● SYSTEM ONLINE",
            text_color=GREEN
        )
    elif state == "ERROR":
        system_status.configure(
            text="● SYSTEM ERROR",
            text_color=RED
        )
    else:
        system_status.configure(
            text="● JARVIS ACTIVE",
            text_color=color
        )


# ============================================================
# MEMORY
# ============================================================

def memory_message(role, text):
    if save_message:
        try:
            save_message(role, text)
        except Exception as e:
            print("Memory save error:", e)


def start_memory():
    global conversation_started

    if start_conversation:
        try:
            start_conversation()
            conversation_started = True
        except Exception as e:
            print("Conversation start error:", e)


def finish_memory():
    global conversation_started

    if conversation_started and end_conversation:
        try:
            end_conversation()
        except Exception as e:
            print("Conversation end error:", e)

    conversation_started = False


# ============================================================
# COMMAND PROCESSING
# ============================================================

def process_command(command):
    global last_activity
    global conversation_active

    command = command.lower().strip()

    if not command:
        return

    last_activity = time.time()
    conversation_active = True

    add_message("You", command)
    memory_message("user", command)

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if command in [
        "exit",
        "stop",
        "goodbye",
        "go offline",
        "shutdown jarvis",
    ]:
        reply = "Understood, Master. Going offline."

        memory_message("assistant", reply)
        add_message("Jarvis", reply)

        post_ui(set_state, "SPEAKING")
        # (UI only — jarvis_ai handles voice)
        conversation_active = False
        finish_memory()
        post_ui(set_state, "STANDBY")
        return

    # --------------------------------------------------------
    # EXPLICIT MEMORY
    # --------------------------------------------------------

    if command.startswith("remember that"):
        memory_text = command[len("remember that"):].strip()

        if memory_text and save_memory:
            try:
                save_memory(memory_text)
                reply = "Understood, Master. I will remember that."
            except Exception as e:
                print("Memory error:", e)
                reply = "Master, I couldn't save that memory."
        else:
            reply = "What would you like me to remember, Master?"

        memory_message("assistant", reply)
        add_message("Jarvis", reply)

        post_ui(set_state, "SPEAKING")
        post_ui(set_state, "LISTENING")
        return

    # --------------------------------------------------------
    # LOCAL SKILLS FIRST
    # --------------------------------------------------------

    post_ui(set_state, "THINKING")

    result = None

    try:
        result = run_skill(command)
    except Exception as e:
        print("Skill manager error:", e)

    # --------------------------------------------------------
    # SKILL RESULT / AI FALLBACK
    # --------------------------------------------------------

    if isinstance(result, dict):
        if result.get("type") == "vision_followup":
            prompt = (
                "Use this previous vision result as context:\n\n"
                + str(result.get("context", ""))
                + "\n\nQuestion: "
                + str(result.get("question", command))
            )
            reply = ask_ai(prompt)
        else:
            reply = str(result)

    elif result:
        reply = str(result)

    else:
        try:
            reply = ask_ai(command)
        except Exception as e:
            print("AI error:", e)
            reply = "Master, I encountered an AI processing error."

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    memory_message("assistant", reply)
    add_message("Jarvis", reply)
    emit_message("jarvis", reply)

    post_ui(set_state, "SPEAKING")
    # UI: visual only — jarvis_ai handles ALL voice
    post_ui(set_state, "LISTENING")


# ============================================================
# BACKGROUND JARVIS ENGINE
# ============================================================

def background_engine():
    global conversation_active
    global last_activity
    global conversation_started

    while not shutdown_event.is_set():

        try:
            # ================================================
            # STANDBY / WAKE WORD
            # ================================================

            conversation_active = False
            post_ui(set_state, "STANDBY")

            wait_for_wake_word()

            if shutdown_event.is_set():
                break

            # ================================================
            # NEW CONVERSATION
            # ================================================

            conversation_active = True
            last_activity = time.time()

            start_memory()
            start_conversation()

            # Greet precisely once, immediately after wake-word detection
            if not conversation_started:
                # UI: visual greeting only — jarvis_ai handles voice
                conversation_started = True
                # Small delay to let TTS finish before listening resumes
                time.sleep(0.3)
            post_ui(set_state, "LISTENING")

            # ================================================
            # ACTIVE SESSION
            # ================================================

            while conversation_active and not shutdown_event.is_set():

                # 60-second inactivity
                if time.time() - last_activity >= INACTIVITY_TIMEOUT:

                    reply = (
                        "No command received. "
                        "Returning to standby."
                    )

                    memory_message("assistant", reply)
                    add_message("Jarvis", reply)

                    conversation_active = False
                    finish_memory()
                    end_conversation()

                    post_ui(set_state, "STANDBY")
                    break

                # Listen
                post_ui(set_state, "LISTENING")

                try:
                    command = listen()
                except Exception as e:
                    print("Listening error:", e)
                    time.sleep(0.5)
                    continue

                if not command:
                    continue

                last_activity = time.time()

                # Process in worker thread so UI remains responsive.
                # Only one command should normally be spoken at a time.
                worker = threading.Thread(
                    target=process_command,
                    args=(command,),
                    daemon=True
                )
                worker.start()

                # Wait for response/TTS before opening microphone
                # again. This prevents overlapping listening and speech.
                worker.join(timeout=120)

        except Exception as e:
            print("Background JARVIS error:", e)
            add_message("Error", str(e))
            post_ui(set_state, "ERROR")
            time.sleep(2)


# ============================================================
# CLOCK
# ============================================================

def update_clock():
    clock_label.configure(
        text=datetime.now().strftime(
            "%A  •  %d %B %Y  •  %H:%M:%S"
        )
    )

    if not shutdown_event.is_set():
        app.after(1000, update_clock)


# ============================================================
# CLOSE
# ============================================================

def close_jarvis():
    global conversation_active

    shutdown_event.set()
    conversation_active = False
    finish_memory()

    set_state("OFFLINE")

    app.after(300, app.destroy)


app.protocol("WM_DELETE_WINDOW", close_jarvis)


# ============================================================
# STARTUP
# ============================================================

add_message("Jarvis", "System initialized.")
add_message("Jarvis", "Core systems online.")
add_message("Jarvis", 'Say "Hey Jarvis" to begin.')

update_clock()  # pulse disabled - UI finalized
process_ui_queue()

threading.Thread(
    target=background_engine,
    daemon=True
).start()

app.mainloop()
