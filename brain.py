import os
from pathlib import Path

VAULT = os.getenv("JARVIS_OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis Brain"))

def get_notes():

    all_notes = ""

    for file in Path(VAULT).rglob("*.md"):

        try:

            all_notes += f"\n\n=== {file.name} ===\n"

            all_notes += file.read_text(
                encoding="utf-8"
            )

        except Exception as e:

            print(e)

    return all_notes


if __name__ == "__main__":

    print(get_notes())