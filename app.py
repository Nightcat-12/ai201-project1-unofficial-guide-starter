import os

import gradio as gr

from config import DOCS_PATH
from generator import generate_response
from ingest import chunk_document, load_documents, source_name_from_filename
from retriever import embed_and_store, get_collection, retrieve


def _document_names():
    return [
        source_name_from_filename(filename)
        for filename in sorted(os.listdir(DOCS_PATH))
        if filename.endswith(".pdf")
    ]


def run_ingestion():
    """Load travel documents, chunk them, and store in ChromaDB."""
    collection = get_collection()

    if collection.count() > 0:
        print(
            f"Vector store already populated ({collection.count()} chunks). "
            "Skipping ingestion."
        )
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return collection.count()

    print("Ingesting California travel documents...")
    documents = load_documents()
    all_chunks = []

    for doc in documents:
        chunks = chunk_document(
            doc["text"],
            doc["source"],
            doc["filename"],
            doc["doc_type"],
        )
        all_chunks.extend(chunks)

    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
        return len(all_chunks)

    print(
        "\nNo chunks produced. Check that PDFs exist in ./documents and "
        "contain extractable text.\n"
    )
    return 0


def chat(message, history):
    if not message.strip():
        return ""

    retrieved = retrieve(message)
    response = generate_response(message, retrieved)

    if retrieved:
        chunk_lines = []
        for index, chunk in enumerate(retrieved, start=1):
            preview = chunk["text"][:180].replace("\n", " ")
            chunk_lines.append(
                f"{index}. {chunk['source']} "
                f"(distance: {chunk['distance']:.3f}) — {preview}..."
            )
        response += "\n\n**Retrieved chunks:**\n" + "\n".join(chunk_lines)

    return response


def document_sidebar_html():
    items = "\n".join(f"<li>📄 {name}</li>" for name in _document_names())
    return f"""
        <div style="background:#eff6ff; border:1px solid #bfdbfe;
                    border-radius:10px; padding:1rem; margin-top:0.5rem;">
            <p style="font-size:0.8rem; font-weight:700; color:#1e3a8a;
                       margin:0 0 0.5rem; letter-spacing:0.05em;">
                LOADED DOCUMENTS
            </p>
            <ul style="font-size:0.85rem; color:#1d4ed8; list-style:none;
                        padding:0; margin:0; line-height:1.8;">
                {items}
            </ul>
            <hr style="border:none; border-top:1px solid #bfdbfe; margin:0.75rem 0;">
            <p style="font-size:0.75rem; color:#2563eb; margin:0; line-height:1.5;">
                Answers are grounded in retrieved document chunks only.
                Source names appear in every response.
            </p>
        </div>
    """


with gr.Blocks() as demo:
    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#1e3a8a; margin:0;">
                California Travel Guide
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask about Central Coast trips, Monterey, Morro Bay, Sensorio, and Bay Area events.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chat,
                chatbot=gr.Chatbot(
                    height=440,
                    placeholder=(
                        "<div style='text-align:center; color:#9ca3af; margin-top:3rem;'>"
                        "Ask a travel or events question to get started."
                        "</div>"
                    ),
                ),
                textbox=gr.Textbox(
                    placeholder='e.g. "What can you do in Morro Bay?"',
                    container=False,
                    scale=7,
                ),
                examples=[
                    "What is Sensorio in Paso Robles?",
                    "What can you do at the Monterey Bay Aquarium?",
                    "What are the stops on the Central Coast Wine Tour?",
                    "What free events are happening in the East Bay?",
                    "What annual events happen in Carmel-by-the-Sea?",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=180):
            gr.HTML(document_sidebar_html())


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  California Travel Guide — starting up")
    print("=" * 50 + "\n")
    run_ingestion()
    demo.launch(theme=gr.themes.Soft(primary_hue="blue"))
