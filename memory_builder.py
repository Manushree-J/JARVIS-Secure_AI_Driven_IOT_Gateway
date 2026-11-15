import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

VAULT = os.getenv("JARVIS_OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis Brain"))

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(
    path="jarvis_memory"
)

collection = client.get_or_create_collection(
    "brain"
)

for file in Path(VAULT).rglob("*.md"):

    try:

        content = file.read_text(
            encoding="utf-8"
        )

        collection.add(
            documents=[content],
            ids=[str(file)]
        )

        print("Added:", file)

    except Exception as e:

        print(e)

print("Brain indexed.")