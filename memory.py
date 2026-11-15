import os
import hashlib
import chromadb


# =====================================
# PATHS
# =====================================

CONVERSATIONS_PATH = os.getenv(
    "JARVIS_CONVERSATIONS_PATH",
    os.path.join(os.getenv("JARVIS_OBSIDIAN_VAULT", os.path.join(os.path.expanduser("~"), "Documents", "Jarvis Brain")), "JARVIS", "Conversations"),
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
# INDEX MARKDOWN FILES
# =====================================

def load_markdown_files():

    if not os.path.exists(CONVERSATIONS_PATH):

        print(
            "⚠️ Conversations folder not found:"
        )

        print(
            CONVERSATIONS_PATH
        )

        return


    documents = []
    metadatas = []
    ids = []


    for root, dirs, files in os.walk(
        CONVERSATIONS_PATH
    ):

        for filename in files:

            if not filename.lower().endswith(".md"):
                continue


            filepath = os.path.join(
                root,
                filename
            )


            try:

                with open(
                    filepath,
                    "r",
                    encoding="utf-8"
                ) as file:

                    content = file.read().strip()


                if not content:
                    continue


                # Stable ID for this file
                file_hash = hashlib.sha256(
                    filepath.encode("utf-8")
                ).hexdigest()


                documents.append(
                    content
                )


                metadatas.append(
                    {
                        "source": "obsidian",
                        "file": filename,
                        "path": filepath
                    }
                )


                ids.append(
                    "md_" + file_hash
                )


            except Exception as e:

                print(
                    f"Memory file error: "
                    f"{filepath} -> {e}"
                )


    if not documents:

        print(
            "🧠 No Markdown files found."
        )

        return


    try:

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )


        print(
            f"🧠 Indexed "
            f"{len(documents)} Markdown file(s)."
        )


    except Exception as e:

        print(
            "❌ Markdown indexing error:",
            e
        )


# =====================================
# SEARCH MEMORY
# =====================================

def search_memory(query):

    if not query:

        return ""


    try:

        # Index Markdown files before searching
        load_markdown_files()


        results = collection.query(
            query_texts=[query],
            n_results=5
        )


        documents = results.get(
            "documents",
            [[]]
        )


        if not documents:

            return ""


        if not documents[0]:

            return ""


        context = "\n\n".join(
            documents[0]
        )


        return context


    except Exception as e:

        print(
            "Memory search error:",
            e
        )


        return ""