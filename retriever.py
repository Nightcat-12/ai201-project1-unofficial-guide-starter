import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks):
    """Embed chunks and store them in ChromaDB with source metadata."""
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source": c["source"],
                "filename": c["filename"],
                "doc_type": c["doc_type"],
            }
            for c in chunks
        ],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")


def retrieve(query, n_results=N_RESULTS):
    """Return the top semantic matches for a user query."""
    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=min(n_results, _collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "text": doc,
            "source": metadata.get("source", "Unknown"),
            "filename": metadata.get("filename", ""),
            "doc_type": metadata.get("doc_type", ""),
            "distance": distance,
        })

    return retrieved
