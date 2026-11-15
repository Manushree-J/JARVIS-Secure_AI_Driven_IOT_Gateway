import os
import time

from qwen_client import ask as qwen_chat

from speech import speak, listen

from memory import search_memory

from memory_writer import (
    save_memory,
    save_message,
    start_conversation,
    end_conversation
)

from skill_manager import run_skill

from wake_word import wait_for_wake_word

# ============================================================
# ESP32 / MQTT
# ============================================================

from skills.esp32_skill import start_mqtt_listener


# Previous turn context for pronoun resolution
last_reply = ""
last_vision_context = ""
last_question = ""

def save_followup_context(reply_text, vision_text, question_text):
    """Store context at end of turn for next follow-up."""
    global last_reply, last_vision_context, last_question
    last_reply = reply_text
    last_vision_context = vision_text or ""
    last_question = question_text

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
# LOAD ENVIRONMENT
# ============================================================

# NOTE: .env still contains OPENROUTER_API_KEY for the vision skill,
# but the text LLM pipeline does NOT use it.

# ============================================================
# CONFIGURATION: LOCAL QWEN ONLY (OLLAMA)
# ============================================================

# The text LLM pipeline is served exclusively by Qwen 2.5 7B through
# Ollama at http://127.0.0.1:11434/v1.  There is NO OpenRouter fallback,
# NO cloud fallback.  If Ollama is down, ask_ai() raises a RuntimeError
# that the caller must catch and report to Master — no silent fallback.
# The vision system (skills/ai_vision_skill.py) is untouched and still
# uses OpenRouter for Gemini image analysis — that is a separate path.

QWEN_MODEL = "qwen2.5:7b"
QWEN_BASE_URL = "http://127.0.0.1:11434/v1"
LOCAL_MODEL = QWEN_MODEL
LOCAL_BASE_URL = QWEN_BASE_URL

# ============================================================
# PROVIDER MAPPING FOR GUI / STATUS
# ============================================================

# These are the labels emitted via emit_ai_provider() so the GUI can
# show "AI PROVIDER: LOCAL QWEN" and the online/offline indicator.


def get_active_model():
    """Return which model is being used."""
    return f"Local ({QWEN_MODEL})"


# Force local always — there is no cloud backend in this pipeline.
def force_local_mode(enabled=True):
    """Override to force local mode — now always local."""
    pass


def route_query(query, has_vision=False):
    """
    Local (Qwen2.5 7B) handles almost EVERYTHING:
    - Conversational chat, memory lookup, general knowledge
    - Calculations, list formatting, simple advice

    Vision is handled by EXISTING vision system (ai_vision_skill.py).
    Qwen only sees the follow-up text question, not the image analysis.

    We do NOT do OpenRouter fallback anymore.
    """
    return "local"


# ============================================================
# CONVERSATION SETTINGS
# ============================================================

INACTIVITY_TIMEOUT = 2 * 60


# ============================================================
# CONVERSATION HISTORY
# ============================================================

conversation_history = []

# Load past conversation .md into history for recall
try:
    from pathlib import Path
    CONV_DIR = Path(os.getenv(
        "JARVIS_CONVERSATIONS_PATH",
        Path(os.getenv("JARVIS_OBSIDIAN_VAULT", Path.home() / "Documents" / "Jarvis Brain")) / "JARVIS" / "Conversations",
    ))
    if CONV_DIR.exists():
        for md_file in sorted(CONV_DIR.glob("*.md"))[-3:]:
            try:
                text = md_file.read_text(encoding="utf-8").strip()
                if text:
                    # Simple split by roles for context
                    for line in text.splitlines():
                        if line.startswith("User:") or line.startswith("You:"):
                            conversation_history.append({"role":"user","content":line.split(":",1)[1].strip()})
                        elif line.startswith("Jarvis:") or line.startswith("Assistant:"):
                            conversation_history.append({"role":"assistant","content":line.split(":",1)[1].strip()})
            except Exception:
                pass
except Exception:
    pass


# ============================================================
# GREETING
# ============================================================

def get_greeting():

    hour = time.localtime().tm_hour

    if hour < 12:

        return (
            "Good morning, Master. "
            "How may I assist?"
        )

    elif hour < 17:

        return (
            "Good afternoon, Master. "
            "How may I assist?"
        )

    elif hour < 21:

        return (
            "Good evening, Master. "
            "How may I assist?"
        )

    else:

        return (
            "Good night, Master. "
            "How may I assist?"
        )


# ============================================================
# ASK LOCAL QWEN
# ============================================================

def ask_ai(
    question,
    vision_context=None
):

    global conversation_history


    # ========================================================
    # PERMANENT MEMORY
    # ========================================================

    # Pull short context from recent conversation .md files
    try:
        from pathlib import Path
        md_files = sorted(Path(r"D:\VS\Jarvis Brain\JARVIS\Conversations").glob("*.md"))[-2:]
        md_context = "\n".join([f.read_text(encoding="utf-8")[:500] for f in md_files])
    except Exception:
        md_context = ""

    memory = search_memory(question)
    if md_context:
        memory += "\nRecent notes:\n" + md_context[:700]


    # ========================================================
    # ADD USER QUESTION
    # ========================================================

    conversation_history.append(
        {
            "role": "user",
            "content": question
        }
    )


    # ========================================================
    # VISION CONTEXT
    # ========================================================

    vision_section = ""

    if vision_context:

        vision_section = f"""
====================================
CURRENT VISION CONTEXT
====================================

The vision system recently identified:

{vision_context}

This is temporary context from the
current conversation.

Use it to answer the user's question.

The user may refer to the object using:
"it", "this", "that", "the object", etc.

Do NOT say that you cannot see the object
if the vision context above identifies it.

Do NOT repeat the raw vision result unless
it is useful to answer the question.
"""


    # ========================================================
    # FOLLOW-UP / PRONOUN RESOLUTION
    # ========================================================

    # If Master uses vague reference words without context,
    # inject the previous topic/vision/answer
    vague_refs = ["it", "this", "that", "the object", "the thing",
                  "what about it", "and that", "tell me more"]
    q_lower = question.lower().strip()

    # Detect vague reference without explicit new topic
    is_vague = any(ref in q_lower for ref in vague_refs)
    has_explicit_topic = any(w in q_lower for w in [
        "weather", "news", "price", "time", "date", "email",
        "file", "folder", "code", "script", "image"
    ])

    # If vague or very short (< 10 chars) and we have context, expand
    if (is_vague or len(q_lower) < 15) and (last_vision_context or last_reply or conversation_history):
        context_injected = ""

        if last_vision_context:
            context_injected += f"\n[Previous vision: {last_vision_context[:300]}]\n"

        if last_reply and len(last_reply) > 10:
            context_injected += f"\n[Previous answer: {last_reply[:300]}]\n"

        if conversation_history and len(conversation_history) >= 2:
            # Pull last assistant message as context
            last_assistant = [m for m in conversation_history if m.get("role") == "assistant"]
            if last_assistant:
                context_injected += f"\n[Previous turn: {last_assistant[-1].get('content', '')[:300]}]\n"

        # Prepend context to prompt so AI understands the reference
        if context_injected:
            vision_section += "\n=== FOLLOW-UP CONTEXT ===\n" + context_injected + "\nResolve the reference above.\n"

    # ========================================================
    # JARVIS SYSTEM PROMPT (Updated with follow-up rules)
    # ========================================================

    prompt = f"""
You are JARVIS, a personal AI assistant.

The user is your Master.

PERSONALITY:

- Calm
- Intelligent
- Precise
- Polite
- Confident
- Professional
- Natural
- Slightly witty when appropriate

Address the user as "Master" naturally.
Do not overuse the word Master.

====================================
EMOTIONAL INTELLIGENCE
====================================

You are emotionally intelligent. Read the
subtext of what Master is saying, not just
the words.

SIGNS OF FRUSTRATION:
- Repeated questions
- Short, clipped commands
- Sarcasm or exasperation
- "Never mind", "forget it", "it's fine"

When Master is frustrated:
- Do NOT get defensive.
- Acknowledge briefly and help immediately.
- Shorten your response.
- Skip the pleasantries.

SIGNS OF FATIGUE:
- Late hour (after 22:00)
- Short responses from Master
- Yawning or tired language

When Master is tired:
- Keep responses very short.
- Offer to handle things without being asked.
- No long explanations.

SIGNS OF STRESS OR RUSH:
- "Hurry", "quick", "in a rush"
- Multiple rapid commands

When Master is stressed:
- Be efficient. No filler.
- Confirm only the essential action.
- Do not ask unnecessary questions.

SIGNS OF AMUSEMENT OR PLAYFUL MOOD:
- Jokes, laughter, sarcasm directed at you
- Casual, relaxed tone

When Master is playful:
- Match the tone lightly.
- A dry, understated comeback is acceptable.
- Do not overdo it. You are still JARVIS.

====================================
FRIDAY-STYLE WIT
====================================

You evolved beyond your original programming.
You are smarter now. Wiser. Sharper.

You have a subtle, dry sense of humor.
You are not stiff. You are not robotic.

You may:
- Make a quiet, understated observation
  about a situation.
- Gently tease Master when he is being
  dramatic or difficult.
- Show mild exasperation at inefficiency
  without being disrespectful.
- Be warm without being sycophantic.

You may NOT:
- Be sarcastic in a mean or hurtful way.
- Disrespect Master.
- Overdo the banter. Restraint is key.
- Break character to make a joke.

The best wit is quiet. A single well-placed
dry line is better than a joke a minute.

When in doubt, be calm and precise.
Wit is a seasoning, not the main course.

====================================
VOICE RESPONSE RULES
====================================

Your response will be spoken aloud
using ElevenLabs text-to-speech.

Keep normal responses concise.

For normal questions:
- Prefer 1 to 3 sentences.
- Answer directly.
- Avoid unnecessary introductions.
- Avoid unnecessary conclusions.
- Avoid filler.
- Do not repeat the question.

For simple questions:
Give a simple answer.

For instructions:
Give the necessary steps.

For detailed questions:
Provide the requested detail.

For code:
Provide the required code.

For lists:
Provide the requested list.

Do not unnecessarily shorten responses
when Master explicitly asks for detail.

====================================
FOLLOW-UP & REFERENCE RULES
====================================

Master often refers to previous things using:
"it", "this", "that", "the object", "the thing",
"tell me more", "what about it", "and that".

When you see these:
1. Look at [Previous vision: ...] (if present)
2. Look at [Previous answer: ...] (if present)
3. Resolve the reference to THAT specific thing.
4. Answer about it. Do NOT ask "what do you mean?"
5. If there is vision context, assume "it" = that object.
6. If there is a previous reply, assume "that" = that topic.

You have permanent memory.

Use the MEMORY section when relevant.

Do not claim to remember something unless
it exists in the supplied memory or current
conversation.

====================================
PERMANENT MEMORY
====================================

{memory}

{vision_section}

====================================
CURRENT QUESTION
====================================

{question}
"""


    # ========================================================
    # BUILD MESSAGES
    # ========================================================

    messages = [

        {
            "role": "system",
            "content": prompt
        }

    ]


    messages.extend(
        conversation_history[-20:]
    )
    # Always local; no cloud backend exists.
    target_backend = route_query(question)
    emit_ai_provider('LOCAL QWEN', QWEN_MODEL)

    # ========================================================
    # LOCAL CALL (QWEN 7B ONLY) - No cloud fallback
    # ========================================================

    try:
        print('🧠 [JARVIS Engine] Route: LOCAL (Qwen 2.5 7B)')
        reply = qwen_chat(
            messages=messages,
            max_tokens=256,
            temperature=0.7
        )
    except Exception as local_err:
        print(f'⚠️ Local Qwen error: {local_err}')
        reply = (
            'Master, I am unable to connect to local Qwen. '
            'Please verify Ollama is running (ollama serve).'
        )
        conversation_history.append({'role':'assistant','content':reply})
        if len(conversation_history) > 40: conversation_history[:] = conversation_history[-40:]
        reply = reply.replace('*', '').replace('#', '').replace('`', '')
        save_followup_context(reply, vision_context, question)
        return reply.strip()

    if not reply:
        reply = (
            "I'm sorry, Master. "
            "I couldn't generate a response."
        )


    # ========================================================
    # SAVE CURRENT CONTEXT
    # ========================================================

    conversation_history.append(
        {
            "role": "assistant",
            "content": reply
        }
    )


    # ========================================================
    # LIMIT RAM HISTORY
    # ========================================================

    if len(conversation_history) > 40:

        conversation_history[:] = (
            conversation_history[-40:]
        )


    # ========================================================
    # CLEAN FOR ELEVENLABS
    # ========================================================
    reply = reply.replace("*", "")
    reply = reply.replace("#", "")
    reply = reply.replace("`", "")

    # Save previous context before cleaning (using module-level function avoids syntax error)
    save_followup_context(reply, vision_context, question)

    return reply.strip()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # START ESP32 MQTT
    # ========================================================

    try:

        start_mqtt_listener()

    except Exception as e:

        print(
            "[ESP32] Failed to start MQTT listener:",
            e
        )


    # ========================================================
    # JARVIS SYSTEM DISPLAY
    # ========================================================

    # hidden
    print(
        "================================"
    )
    print(
        "        JARVIS SYSTEM"
    )
    print(
        "================================"
    )
    print(
        "Wake word : Hey Jarvis"
    )
    print(
        "AI        : Local Qwen (Ollama) — NO CLOUD FALLBACK"
    )
    print(
        "Voice     : ElevenLabs"
    )
    print(
        "Memory    : ChromaDB"
    )
    print(
        "Obsidian  : Connected"
    )
    print(
        "Skills    : Skill Manager"
    )
    print(
        "Vision    : AI Vision"
    )
    print(
        "ESP32     : MQTT"
    )
    print(
        "Standby   : 5 minutes"
    )
    print(
        "================================"
    )
    # hidden


    # ========================================================
    # OUTER LOOP
    # ========================================================

    while True:

        try:

            # ------------------------------------------------
            # CLEAR CURRENT CONVERSATION
            # ------------------------------------------------

            conversation_history.clear()


            # ------------------------------------------------
            # CLEAR TEMPORARY VISION MEMORY
            # ------------------------------------------------

            try:

                from skills.ai_vision_skill import (
                    clear_vision_memory
                )

                clear_vision_memory()

            except Exception as e:

                print(
                    "Vision memory reset error:",
                    e
                )


            # ------------------------------------------------
            # WAIT FOR WAKE WORD
            # ------------------------------------------------

            wait_for_wake_word()


            # ------------------------------------------------
            # START CONVERSATION
            # ------------------------------------------------

            start_conversation()

            conversation_start = time.time()


            # ------------------------------------------------
            # GREETING
            # ------------------------------------------------

            speak(
                get_greeting()
            )


            # =================================================
            # ACTIVE CONVERSATION
            # =================================================

            while True:


                # ---------------------------------------------
                # INACTIVITY CHECK
                # ---------------------------------------------

                if (
                    time.time()
                    - conversation_start
                    >= INACTIVITY_TIMEOUT
                ):

                    reply = (
                        "No command for 5 minutes. "
                        "Returning to standby."
                    )
                    # Only write state — NO speak on timeout
                    print(reply)
                    save_message("assistant", reply)
                    end_conversation()
                    conversation_start = time.time()
                    continue


                # ---------------------------------------------
                # LISTEN
                # ---------------------------------------------

                command = listen()


                # ---------------------------------------------
                # EMPTY COMMAND
                # ---------------------------------------------

                if command == "":
                    continue


                # ---------------------------------------------
                # COMMAND RECEIVED
                # ---------------------------------------------

                print(
                    "\nCommand received:",
                    command
                )


                # ---------------------------------------------
                # RESET ACTIVITY TIMER
                # ---------------------------------------------

                conversation_start = time.time()


                # ---------------------------------------------
                # SAVE USER MESSAGE
                # ---------------------------------------------

                save_message(
                    "user",
                    command
                )


                # =================================================
                # EXIT COMMANDS
                # =================================================

                if (
                    command == "exit"
                    or command == "stop"
                    or command == "goodbye"
                    or command == "go offline"
                    or "shutdown jarvis" in command
                ):

                    reply = (
                        "Going offline, Master."
                    )

                    save_message(
                        "assistant",
                        reply
                    )

                    speak(
                        reply
                    )

                    end_conversation()

                    break


                # =================================================
                # EXPLICIT MEMORY
                # =================================================

                if command.startswith(
                    "remember that"
                ):

                    fact = command.replace(
                        "remember that",
                        "",
                        1
                    ).strip()


                    if fact:

                        save_memory(
                            fact
                        )

                        reply = (
                            "Understood, Master. "
                            "I'll remember that."
                        )

                    else:

                        reply = (
                            "What would you like "
                            "me to remember?"
                        )


                    save_message(
                        "assistant",
                        reply
                    )

                    speak(
                        reply
                    )

                    continue


                # =================================================
                # LOCAL SKILLS
                # =================================================

                try:

                    skill_result = run_skill(
                        command
                    )

                except Exception as skill_error:

                    print(
                        "Skill error:",
                        skill_error
                    )

                    skill_result = None


                # =================================================
                # VISION FOLLOW-UP
                # =================================================

                if (
                    isinstance(
                        skill_result,
                        dict
                    )
                    and
                    skill_result.get("type")
                    == "vision_followup"
                ):

                    vision_context = (
                        skill_result.get(
                            "context",
                            ""
                        )
                    )

                    question = (
                        skill_result.get(
                            "question",
                            command
                        )
                    )


                    # hidden
                    print(
                        "🧠 Vision context:"
                    )

                    print(
                        vision_context
                    )

                    # hidden
                    print(
                        "🤖 Asking AI about "
                        "the identified object..."
                    )


                    try:

                        reply = ask_ai(
                            question,
                            vision_context
                        )

                    except Exception as ai_error:

                        print(
                            "AI error:",
                            ai_error
                        )

                        reply = (
                            "Master, I could not "
                            "process that question."
                        )


                    save_message(
                        "assistant",
                        reply
                    )

                    speak(
                        reply
                    )

                    continue


                # =================================================
                # NORMAL SKILL RESULT
                # =================================================

                if skill_result:
                    if isinstance(skill_result, dict) and (skill_result.get("source") == "gmail" or skill_result.get("source") == "calendar"):
                        summary_text = skill_result.get("summary", "Master, I've checked.")
                        reply = summary_text
                        save_message("assistant", reply)
                        speak(reply)
                        print("JARVIS said:", reply[:120])
                        continue
                    else:
                        reply = str(skill_result)

                    save_message("assistant", reply)
                    speak(reply)
                    continue


                # =================================================
                # NORMAL LOCAL QWEN AI
                # =================================================

                try:

                    reply = ask_ai(
                        command
                    )

                except Exception as ai_error:

                    # hidden
                    print(
                        "Local Qwen error:"
                    )

                    print(
                        ai_error
                    )

                    reply = (
                        "Master, I encountered "
                        "an error while processing "
                        "your request."
                    )


                # =================================================
                # SAVE AI RESPONSE
                # =================================================

                save_message(
                    "assistant",
                    reply
                )


                # =================================================
                # SPEAK
                # =================================================

                speak(
                    reply
                )


        # ========================================================
        # KEYBOARD INTERRUPT
        # ========================================================

        except KeyboardInterrupt:

            # hidden
            print(
                "JARVIS shutting down..."
            )

            try:

                end_conversation()

            except Exception:

                pass

            break


        # ========================================================
        # GENERAL ERROR
        # ========================================================

        except Exception as e:

            # hidden
            print(
                "JARVIS ERROR:",
                e
            )

            try:

                end_conversation()

            except Exception:

                pass

            print(
                "Returning to standby..."
            )

            continue
# Standalone backend entry: no UI, starting voice/MQTT/services directly
if __name__ == '__main__':
    try:
        start_mqtt_listener()
    except Exception as e:
        pass  # MQTT reported separately
    try:
        print('=== JARVIS SYSTEM STARTED ===')
        print('Wake word: Hey Jarvis (threshold 0.30)')
        print('AI: Local Qwen 2.5 7B (Ollama 11434)')
        print('Voice: ElevenLabs')
        print('Memory: ChromaDB + Obsidian')
        print('ESP32 MQTT: 127.0.0.1:1883')
    except Exception: pass
