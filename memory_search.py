import chromadb

client = chromadb.PersistentClient(
    path="jarvis_memory"
)

collection = client.get_collection(
    "brain"
)

while True:

    q = input("\nQuestion: ")

    if q == "exit":
        break

    results = collection.query(

        query_texts=[q],

        n_results=3
    )

    print("\nRESULTS:\n")

    for doc in results["documents"][0]:

        print(doc[:500])
        print("-" * 50)