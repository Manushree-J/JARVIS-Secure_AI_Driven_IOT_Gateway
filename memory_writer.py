from pathlib import Path
from datetime import datetime
import os
import re

import chromadb


# =====================================
# OBSIDIAN VAULT
# =====================================

VAULT = Path(os.getenv("JARVIS_OBSIDIAN_VAULT", Path.home() / "Documents" / "Jarvis Brain"))

JARVIS_FOLDER = VAULT / "JARVIS"

CONVERSATIONS_FOLDER = (
    JARVIS_FOLDER / "Conversations"
)

PERSONAL_FOLDER = (
    JARVIS_FOLDER / "Personal"
)

MEMORY_FILE = (
    PERSONAL_FOLDER / "Memory.md"
)


# =====================================
# CREATE FOLDERS
# =====================================

CONVERSATIONS_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

PERSONAL_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# =====================================
# CHROMADB
# =====================================

client = chromadb.PersistentClient(
    path="jarvis_memory"
)

collection = client.get_or_create_collection(
    name="brain"
)


# =====================================
# CONVERSATION STATE
# =====================================

conversation_id = None

conversation_file = None

conversation_topics = set()


# =====================================
# TOPIC DATABASE
# =====================================

TOPICS = [
    "ESP32",
    "Arduino",
    "Embedded Systems",
    "PCB",
    "FreeRouting",
    "MQTT",
    "IoT",
    "Python",
    "C",
    "C++",
    "Qwen",
    "JARVIS",
    "ElevenLabs",
    "GitHub",
    "Linux",
    "GATE",
    "ECE",
    "AI",
    "Machine Learning",
    "Computer Vision",
    "RTOS",
    "Microcontroller",
    "Raspberry Pi",
    "Sensors",
    "Networking",
    "TCP/IP",
    "OSI",
    "Java",
    "VirtualBox",
]


# =====================================
# DETECT TOPICS
# =====================================

def detect_topics(text):

    found = set()

    text_lower = text.lower()


    for topic in TOPICS:

        if topic.lower() in text_lower:

            found.add(topic)


    return found


# =====================================
# CREATE OBSIDIAN TOPIC LINKS
# =====================================

def make_topic_links(topics):

    if not topics:

        return "None"


    sorted_topics = sorted(
        topics,
        key=str.lower
    )


    return "\n".join(
        f"[[{topic}]]"
        for topic in sorted_topics
    )


# =====================================
# START CONVERSATION
# =====================================

def start_conversation():

    global conversation_id
    global conversation_file
    global conversation_topics


    now = datetime.now()


    conversation_id = (
        now.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )


    conversation_file = (
        CONVERSATIONS_FOLDER
        / f"{conversation_id}.md"
    )


    conversation_topics = set()


    conversation_file.write_text(

        f"""# JARVIS Conversation

Date: {now.strftime("%Y-%m-%d")}
Time: {now.strftime("%H:%M:%S")}

---

## Topics

None

---

## Conversation

""",

        encoding="utf-8"
    )


    return conversation_file


# =====================================
# UPDATE TOPICS SECTION
# =====================================

def update_topics():

    if conversation_file is None:

        return


    content = conversation_file.read_text(
        encoding="utf-8"
    )


    topic_links = make_topic_links(
        conversation_topics
    )


    pattern = (
        r"## Topics\n\n.*?\n\n---"
    )


    replacement = (
        "## Topics\n\n"
        + topic_links
        + "\n\n---"
    )


    updated = re.sub(
        pattern,
        replacement,
        content,
        count=1,
        flags=re.DOTALL
    )


    conversation_file.write_text(
        updated,
        encoding="utf-8"
    )


# =====================================
# SAVE MESSAGE
# =====================================

def save_message(role, text):

    global conversation_file
    global conversation_topics


    if not text:

        return False


    # ---------------------------------
    # Start conversation automatically
    # ---------------------------------

    if conversation_file is None:

        start_conversation()


    # ---------------------------------
    # Detect topics
    # ---------------------------------

    new_topics = detect_topics(
        text
    )


    conversation_topics.update(
        new_topics
    )


    # ---------------------------------
    # Timestamp
    # ---------------------------------

    timestamp = datetime.now().strftime(
        "%H:%M:%S"
    )


    # ---------------------------------
    # Speaker
    # ---------------------------------

    if role.lower() == "user":

        speaker = "Master"

    else:

        speaker = "JARVIS"


    # ---------------------------------
    # Save to Obsidian
    # ---------------------------------

    with open(
        conversation_file,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"\n### {speaker} — "
            f"{timestamp}\n\n"
        )

        f.write(
            f"{text}\n\n"
        )


    # ---------------------------------
    # Update Graph topics
    # ---------------------------------

    update_topics()


    # ---------------------------------
    # Save to ChromaDB
    # ---------------------------------

    document_id = (
        f"{conversation_id}_"
        f"{datetime.now().strftime('%H%M%S%f')}"
    )


    collection.add(

        documents=[
            f"{speaker}: {text}"
        ],

        ids=[
            document_id
        ],

        metadatas=[
            {
                "conversation_id":
                    conversation_id,

                "role":
                    role,

                "timestamp":
                    timestamp,

                "source":
                    "conversation"
            }
        ]
    )


    return True


# =====================================
# SAVE EXPLICIT MEMORY
# =====================================

def save_memory(text):

    if not text:

        return False


    # ---------------------------------
    # Create Memory.md
    # ---------------------------------

    if not MEMORY_FILE.exists():

        MEMORY_FILE.write_text(
            "# JARVIS Long-Term Memory\n\n",
            encoding="utf-8"
        )


    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    with open(
        MEMORY_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"- [{timestamp}] {text}\n"
        )


    # ---------------------------------
    # Detect topics
    # ---------------------------------

    topics = detect_topics(
        text
    )


    # ---------------------------------
    # Add topic links to memory
    # ---------------------------------

    if topics:

        with open(
            MEMORY_FILE,
            "a",
            encoding="utf-8"
        ) as f:

            f.write("\nTopics:\n")

            for topic in sorted(
                topics,
                key=str.lower
            ):

                f.write(
                    f"[[{topic}]] "
                )

            f.write("\n")


    # ---------------------------------
    # ChromaDB
    # ---------------------------------

    document_id = (
        "memory_"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )


    collection.add(

        documents=[
            text
        ],

        ids=[
            document_id
        ],

        metadatas=[
            {
                "source":
                    "explicit_memory"
            }
        ]
    )


    return True


# =====================================
# END CONVERSATION
# =====================================

def end_conversation():

    global conversation_id
    global conversation_file
    global conversation_topics


    conversation_id = None

    conversation_file = None

    conversation_topics = set()