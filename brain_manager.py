import os
from memory_writer import save_memory

BRAIN_PATH = os.getenv("JARVIS_OBSIDIAN_VAULT", os.path.join(os.path.expanduser("~"), "Documents", "Jarvis Brain"))


def learn(fact):

    # Save to ChromaDB
    save_memory(fact)

    # Save to Obsidian
    memory_file = os.path.join(
        BRAIN_PATH,
        "Conversations",
        "Auto Memory.md"
    )

    os.makedirs(
        os.path.dirname(memory_file),
        exist_ok=True
    )

    with open(
        memory_file,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(f"- {fact}\n")