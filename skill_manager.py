import importlib


# ============================================================
# SKILL MODULES
# ============================================================

SKILL_MODULES = [
    "skills.windows_skill",
    "skills.ai_vision_skill",
    "skills.esp32_skill",
    "skills.browser_skill",
    "skills.coding_skill",
    "skills.file_skill",
    "skills.obsidian_skill",
    "skills.system_skill",
    "skills.vision_skill",
    "skills.gmail_skill",
    "skills.calendar_skill",
]


# ============================================================
# LOAD SKILLS
# ============================================================

def load_skills():
    loaded_skills = []

    for module_name in SKILL_MODULES:
        try:
            module = importlib.import_module(module_name)
            loaded_skills.append(module)

            # hidden

        except Exception as e:
            print(
                f"[WARN] Could not load {module_name}: {e}"
            )

    return loaded_skills


SKILLS = load_skills()


# ============================================================
# VISION COMMANDS
# ============================================================

VISION_COMMANDS = [
    "what do you see",
    "what am i looking at",

    "identify this",
    "identify that",
    "identify the object",

    "analyze this",
    "analyze that",
    "analyze the object",

    "what is this",
    "what is that",

    "look at this",
    "look at that",
    "look at this object",

    "describe this",
    "describe that",
]


# ============================================================
# VISION FOLLOW-UP COMMANDS
# ============================================================

VISION_FOLLOW_UPS = [
    "what can i use that for",
    "what can i use this for",

    "what is that used for",
    "what is this used for",

    "what can i do with it",
    "what can i do with this",

    "what does it do",
    "what does this do",
    "what does that do",

    "how does it work",

    "how can i use it",
    "how can i use this",
    "how can i use that",

    "what are its applications",

    "tell me more about it",
    "tell me more about this",
    "tell me more about that",

    "is it useful",
    "why is it useful",

    "what is the purpose of it",
    "what is its purpose",
]


# ============================================================
# ESP32 COMMANDS
# ============================================================

ESP32_COMMANDS = [

    # --------------------------------------------------------
    # ESP32
    # --------------------------------------------------------

    "esp32",
    "esp 32",

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    "esp32 status",
    "esp 32 status",

    "is the esp32 online",
    "is esp32 online",
    "is the esp 32 online",

    "check esp32",
    "check the esp32",

    # --------------------------------------------------------
    # SENSOR
    # --------------------------------------------------------

    "sensor",
    "sensor reading",
    "sensor readings",
    "sensor data",
    "sensor value",
    "sensor values",

    "read sensor",
    "read the sensor",
    "read sensors",
    "read the sensors",

    "esp32 readings",
    "esp32 sensor",

    "analog reading",
    "analog value",
    "analog data",

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    "temperature",
    "temperature reading",
    "temperature readings",
    "current temperature",

    "what is the temperature",
    "what's the temperature",

    "how hot is it",

    "read temperature",
    "read the temperature",

    # --------------------------------------------------------
    # HUMIDITY
    # --------------------------------------------------------

    "humidity",
    "humidity reading",
    "humidity readings",
    "current humidity",

    "what is the humidity",
    "what's the humidity",

    "how humid is it",

    "read humidity",
    "read the humidity",

    # --------------------------------------------------------
    # DHT11
    # --------------------------------------------------------

    "dht",
    "dht11",
    "dht 11",
    "dht sensor",

    "read dht",
    "read the dht",

    "read dht11",
    "read the dht11",

    # --------------------------------------------------------
    # LED
    # --------------------------------------------------------

    "turn on led",
    "turn on the led",

    "turn off led",
    "turn off the led",

    "turn on the esp32 led",
    "turn off the esp32 led",

    "turn on esp32 led",
    "turn off esp32 led",

    "led on",
    "led off",

    "switch on led",
    "switch off led",

    "switch on the led",
    "switch off the led",

    # --------------------------------------------------------
    # BUZZER
    # --------------------------------------------------------

    "turn on buzzer",
    "turn on the buzzer",

    "turn off buzzer",
    "turn off the buzzer",

    "buzzer on",
    "buzzer off",

    "switch on buzzer",
    "switch off buzzer",

    "switch on the buzzer",
    "switch off the buzzer",

    "start buzzer",
    "start the buzzer",

    "stop buzzer",
    "stop the buzzer",

    "activate buzzer",
    "activate the buzzer",

    "deactivate buzzer",
    "deactivate the buzzer",
    "light",
    "lux",
    "brightness",
    "light intensity",
    "how bright",
    "illumination",
    "mq3",
    "air quality",
    "gas",
    "mq-3",
    "motion",
    "pir",
    "movement",
    "moving",
    "vibration",
    "accelerometer",
    "magnitude",
    "shake",
    "is esp32 online",
    "is the esp32 connected",
    "esp32 connected",
    "connection status",
    # Actuator commands (relay control)
    "turn on fan", "turn on the fan", "start fan", "start the fan",
    "turn off fan", "turn off the fan", "stop fan", "stop the fan",
    "turn on lights", "turn on the lights", "turn on light", "switch on lights",
    "turn off lights", "turn off the lights", "turn off light", "switch off lights",
    "turn on heater", "turn on the heater", "start heater",
    "turn off heater", "turn off the heater", "stop heater",
    "turn on tv", "turn on the tv", "start tv", "turn on television",
    "turn off tv", "turn off the tv", "stop tv", "turn off television",
    "turn everything off", "turn all off", "switch everything off", "all off",
    "relay status", "status of my relays",
]


# ============================================================
# COMMAND DETECTION
# ============================================================

def is_vision_command(command):
    command = command.lower().strip()

    for phrase in VISION_COMMANDS:
        if phrase in command:
            return True

    return False


def is_vision_follow_up(command):
    command = command.lower().strip()

    for phrase in VISION_FOLLOW_UPS:
        if phrase in command:
            return True

    return False


def is_esp32_command(command):
    command = command.lower().strip()

    for phrase in ESP32_COMMANDS:
        if phrase in command:
            return True

    return False


# ============================================================
# GMAIL COMMANDS
# ============================================================

GMAIL_COMMANDS = [
    # --------------------------------------------------------
    # Basic Gmail
    # --------------------------------------------------------

    "gmail",
    "email",
    "emails",
    "e-mail",
    "e-mails",

    # --------------------------------------------------------
    # Unread
    # --------------------------------------------------------

    "unread email",
    "unread emails",
    "unread message",
    "unread messages",
    "any unread email",
    "any unread emails",
    "how many unread email",
    "how many unread emails",
    "how many unread message",
    "how many unread messages",
    "do i have unread email",
    "do i have unread emails",
    "do i have unread message",
    "do i have unread messages",
    "any new email",
    "any new emails",

    # --------------------------------------------------------
    # Latest / Recent
    # --------------------------------------------------------

    "latest email",
    "latest emails",
    "recent email",
    "recent emails",
    "read my latest email",
    "read my latest emails",
    "read my recent email",
    "read my recent emails",
    "show me latest email",
    "show me latest emails",
    "show me recent email",
    "show me recent emails",

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    "find email",
    "find emails",
    "search email",
    "search emails",
    "find message",
    "find messages",
    "search message",
    "search messages",
    "find email containing",
    "find emails containing",
    "find message containing",
    "find messages containing",
    "search email containing",
    "search emails containing",
    "search message containing",
    "search messages containing",
    "find email with word",
    "find emails with word",
    "find message with word",
    "find messages with word",
    "search email with word",
    "search emails with word",
    "search message with word",
    "search messages with word",

    # --------------------------------------------------------
    # From Sender
    # --------------------------------------------------------

    "email from",
    "emails from",
    "message from",
    "messages from",
    "show me email from",
    "show me emails from",
    "show me message from",
    "show me messages from",
    "find email from",
    "find emails from",
    "find message from",
    "find messages from",
    "latest email from",
    "latest emails from",
    "recent email from",
    "recent emails from",

    # --------------------------------------------------------
    # Summarize
    # --------------------------------------------------------

    "summarize email",
    "summarize emails",
    "summarize message",
    "summarize messages",
    "summarize my email",
    "summarize my emails",
    "summarize my message",
    "summarize my messages",
    "summarize important email",
    "summarize important emails",
    "summarize important message",
    "summarize important messages",
    "summarize today email",
    "summarize today emails",
    "summarize today message",
    "summarize today messages",
    "summarize today's email",
    "summarize today's emails",
    "summarize today's message",
    "summarize today's messages",

    # --------------------------------------------------------
    # Specific Senders
    # --------------------------------------------------------

    "email from john",
    "email from professor",
    "email from boss",
    "email from mom",
    "email from dad",
    "email from family",
    "email from work",
    "email from school",
    "email from university",
    "email from colleague",
    "email from friend",
    "email from friends",
]


# ============================================================
# CALENDAR COMMANDS
# ============================================================

CALENDAR_COMMANDS = [
    # --------------------------------------------------------
    # Basic Calendar
    # --------------------------------------------------------

    "calendar",
    "schedule",
    "agenda",
    "events",
    "event",
    "meeting",
    "meetings",
    "appointment",
    "appointments",

    # --------------------------------------------------------
    # Today
    # --------------------------------------------------------

    "what's on my calendar today",
    "what is on my calendar today",
    "what do i have today",
    "what do i have on my calendar today",
    "calendar today",
    "schedule today",
    "events today",
    "agenda today",
    "meetings today",
    "appointments today",
    "today's calendar",
    "today's schedule",
    "today's events",
    "today's agenda",
    "today's meetings",
    "today's appointments",

    # --------------------------------------------------------
    # Next Event / Meeting
    # --------------------------------------------------------

    "next meeting",
    "next event",
    "next appointment",
    "what's my next meeting",
    "what is my next meeting",
    "what's my next event",
    "what is my next event",
    "what's my next appointment",
    "what is my next appointment",
    "when is my next event",
    "when is my next meeting",
    "when is my next appointment",
    "when is my next event",
    "when is my next meeting",
    "when is my next appointment",
    "next meeting time",
    "next event time",
    "next appointment time",

    # --------------------------------------------------------
    # Tomorrow
    # --------------------------------------------------------

    "calendar tomorrow",
    "schedule tomorrow",
    "events tomorrow",
    "agenda tomorrow",
    "meetings tomorrow",
    "appointments tomorrow",
    "tomorrow's calendar",
    "tomorrow's schedule",
    "tomorrow's events",
    "tomorrow's agenda",
    "tomorrow's meetings",
    "tomorrow's appointments",
    "do i have anything tomorrow",
    "do i have anything tomorrow?",
    "what do i have tomorrow",
    "what do i have tomorrow?",

    # --------------------------------------------------------
    # This Week
    # --------------------------------------------------------

    "calendar this week",
    "schedule this week",
    "events this week",
    "agenda this week",
    "meetings this week",
    "appointments this week",
    "this week's calendar",
    "this week's schedule",
    "this week's events",
    "this week's agenda",
    "this week's meetings",
    "this week's appointments",
    "show my schedule this week",
    "show me my schedule this week",
    "show my calendar this week",
    "show me my calendar this week",
    "my schedule this week",
    "my calendar this week",

    # --------------------------------------------------------
    # Specific Date
    # --------------------------------------------------------

    "calendar on",
    "schedule on",
    "events on",
    "agenda on",
    "meetings on",
    "appointments on",
    "show events on",
    "show calendar on",
    "show schedule on",
    "what's on calendar on",
    "what is on calendar on",
]


# ============================================================
# COMMAND DETECTION
# ============================================================

def is_gmail_command(command):
    command = command.lower().strip()

    for phrase in GMAIL_COMMANDS:
        if phrase in command:
            return True

    return False


def is_calendar_command(command):
    command = command.lower().strip()

    for phrase in CALENDAR_COMMANDS:
        if phrase in command:
            return True

    return False


# ============================================================
# EXECUTE GENERIC SKILL
# ============================================================

def execute_skill(module, command):

    function_names = [
        "execute",
        "handle",
        "run",
    ]

    for function_name in function_names:

        function = getattr(
            module,
            function_name,
            None
        )

        if not callable(function):
            continue

        try:

            result = function(command)

            if result:
                return result

        except TypeError:

            try:

                result = function()

                if result:
                    return result

            except Exception as e:

                print(
                    f"⚠️ Skill execution error "
                    f"in {module.__name__}: {e}"
                )

        except Exception as e:

            print(
                f"⚠️ Skill execution error "
                f"in {module.__name__}: {e}"
            )

    return None


# ============================================================
# MAIN SKILL ROUTER
# ============================================================

def run_skill(command):

    command = command.lower().strip()

    print()
    print(
        f"🧠 Skill Manager received: {command}"
    )


    # ========================================================
    # GMAIL COMMAND
    # ========================================================

    if is_gmail_command(command):

        print(
            "📧 Gmail command detected."
        )

        try:

            from skills.gmail_skill import process_gmail_command

            print(
                "📧 Sending command to Gmail skill..."
            )

            result = process_gmail_command(command)

            if result:

                return result

            print(
                "ℹ️ Gmail skill did not "
                "handle the command."
            )

        except Exception as e:

            print(
                f"❌ Gmail skill error: {e}"
            )

            return (
                "Master, the Gmail system "
                "encountered an error."
            )


    # ========================================================
    # CALENDAR COMMAND
    # ========================================================

    if is_calendar_command(command):

        print(
            "📅 Calendar command detected."
        )

        try:

            from skills.calendar_skill import process_calendar_command

            print(
                "📅 Sending command to Calendar skill..."
            )

            result = process_calendar_command(command)

            if result:

                return result

            print(
                "ℹ️ Calendar skill did not "
                "handle the command."
            )

        except Exception as e:

            print(
                f"❌ Calendar skill error: {e}"
            )

            return (
                "Master, the Calendar system "
                "encountered an error."
            )


    # ========================================================
    # VISION COMMAND
    # ========================================================

    if is_vision_command(command):

        print(
            "👁️ Vision command detected."
        )

        try:

            from skills.ai_vision_skill import ask_vision

            print(
                "👁️ Starting AI Vision..."
            )

            return ask_vision()

        except Exception as e:

            print(
                f"❌ Vision skill error: {e}"
            )

            return (
                "Master, the vision system "
                "encountered an error."
            )


    # ========================================================
    # VISION FOLLOW-UP
    # ========================================================

    if is_vision_follow_up(command):

        print(
            "👁️ Vision follow-up detected."
        )

        try:

            from skills.ai_vision_skill import (
                get_last_vision_result
            )

            vision_context = (
                get_last_vision_result()
            )

            if vision_context:

                return {
                    "type": "vision_followup",
                    "context": vision_context,
                    "question": command,
                }

        except Exception as e:

            print(
                f"❌ Vision follow-up error: {e}"
            )

        return None


    # ========================================================
    # ESP32 / MQTT
    # ========================================================

    if is_esp32_command(command):

        print(
            "📡 ESP32 command detected."
        )

        try:

            from skills.esp32_skill import execute

            print(
                "📡 Sending command to ESP32 skill..."
            )

            result = execute(command)

            if result:

                return result

            print(
                "ℹ️ ESP32 skill did not "
                "handle the command."
            )

        except Exception as e:

            print(
                f"❌ ESP32 skill error: {e}"
            )

            return (
                "Master, the ESP32 system "
                "encountered an error."
            )


    # ========================================================
    # OTHER SKILLS
    # ========================================================

    for skill in SKILLS:

        # Vision already handled above
        if skill.__name__ == "skills.ai_vision_skill":
            continue

        # ESP32 already handled above
        if skill.__name__ == "skills.esp32_skill":
            continue

        result = execute_skill(
            skill,
            command
        )

        if result:

            print(
                f"✅ Skill handled by: "
                f"{skill.__name__}"
            )

            return result


    # ========================================================
    # NO SKILL MATCHED
    # ========================================================

    print(
        "ℹ️ No local skill matched."
    )

    return None