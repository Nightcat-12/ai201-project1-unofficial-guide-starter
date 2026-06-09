from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL, MAX_DISTANCE

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a California travel and events assistant.

Rules:
1. Answer ONLY using the retrieved context below. Do not use outside knowledge.
2. If the context does not contain enough information, say:
   "I don't have that information in my loaded documents."
3. Cite the source document name(s) inline when you state facts.
4. Keep answers concise and practical for travelers.
5. Do not invent events, prices, dates, or locations that are not in the context."""


def _format_context(chunks):
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Chunk {index}] Source: {chunk['source']}\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def generate_response(query, retrieved_chunks):
    """Generate a grounded answer with source attribution."""
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded travel documents. "
            "Try rephrasing your question or asking about a specific region "
            "(Monterey, Morro Bay, Paso Robles, East Bay, etc.)."
        )

    relevant_chunks = [
        chunk for chunk in retrieved_chunks
        if chunk["distance"] <= MAX_DISTANCE
    ]
    if not relevant_chunks:
        return (
            "I found some loosely related text, but nothing close enough to "
            "answer confidently from the loaded documents. Try a more specific "
            "question about a place or event listed in the corpus."
        )

    context = _format_context(relevant_chunks)
    user_prompt = (
        f"Retrieved context:\n{context}\n\n"
        f"User question: {query}\n\n"
        "Write a grounded answer and mention which source document(s) you used."
    )

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip()
    sources = list(dict.fromkeys(chunk["source"] for chunk in relevant_chunks))
    return f"{answer}\n\n**Sources:** {', '.join(sources)}"
