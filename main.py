"""CLI helper for testing ingestion and retrieval without the web UI."""

import argparse

from generator import generate_response
from ingest import chunk_document, load_documents
from retriever import embed_and_store, get_collection, retrieve


def ingest():
    collection = get_collection()
    if collection.count() > 0:
        print(f"Vector store already has {collection.count()} chunks.")
        return collection.count()

    documents = load_documents()
    all_chunks = []
    for doc in documents:
        all_chunks.extend(
            chunk_document(
                doc["text"],
                doc["source"],
                doc["filename"],
                doc["doc_type"],
            )
        )

    embed_and_store(all_chunks)
    print(f"Ingested {len(all_chunks)} chunks from {len(documents)} documents.")
    return len(all_chunks)


def ask(question: str):
    ingest()
    retrieved = retrieve(question)
    print("\nRetrieved chunks:")
    for index, chunk in enumerate(retrieved, start=1):
        preview = chunk["text"][:160].replace("\n", " ")
        print(
            f"  {index}. {chunk['source']} "
            f"(distance={chunk['distance']:.3f}) — {preview}..."
        )

    print("\nAnswer:")
    print(generate_response(question, retrieved))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the travel RAG pipeline.")
    parser.add_argument("question", nargs="?", help="Question to ask the system.")
    args = parser.parse_args()

    if args.question:
        ask(args.question)
    else:
        chunk_count = ingest()
        print(f"Ready. Stored {chunk_count} chunks.")
