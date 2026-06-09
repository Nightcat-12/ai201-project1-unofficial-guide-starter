# California Travel Guide — Project 1

A retrieval-augmented generation (RAG) system that answers questions about California coastal travel and Bay Area events using only loaded document chunks. Built for AI201 Project 1: *The Unofficial Guide*.

## Quick start

```bash
cp .env.example .env          # add your GROQ_API_KEY
pip install -r requirements.txt
python app.py                 # opens Gradio chat UI
```

CLI testing without the web UI:

```bash
python main.py "What is Sensorio in Paso Robles?"
```

Delete `./chroma_db` and restart to re-ingest after changing chunking or documents.

---

## Domain

California coastal travel and regional event listings. This knowledge is useful because recommendations are scattered across Visit California guides, local tourism boards, and Funcheap event calendars. A grounded Q&A system lets travelers ask natural questions ("What can I do in Morro Bay?", "What free events are in the East Bay?") and get answers tied to specific source documents rather than generic LLM knowledge.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Central Coast Wine Tour | Travel guide (PDF) | `documents/Central Coast Wine Tour _ Visit California.pdf` |
| 2 | East Bay Events | Events listing (PDF) | `documents/East Bay Events-Funcheap.pdf` |
| 3 | Events in Carmel-by-the-Sea | Events listing (PDF) | `documents/Events in Carmel-by-the-Sea _ Carmel-by-the-Sea, California.pdf` |
| 4 | How to See Sensorio in Paso Robles | Travel guide (PDF) | `documents/How to See Sensorio in Paso Robles _ Visit California.pdf` |
| 5 | Monterey Travel Guide | Travel guide (PDF) | `documents/Monterey Travel Guide_ Aquarium, Cannery Row & More _ Visit California.pdf` |
| 6 | Morro Bay | Travel guide (PDF) | `documents/Morro Bay _ Visit California.pdf` |
| 7 | North Bay Events | Events listing (PDF) | `documents/North Bay Events - Funcheap.pdf` |
| 8 | NorthCoast events | Events listing (PDF) | `documents/NorthCoast.pdf` |
| 9 | South Bay Events | Events listing (PDF) | `documents/South Bay Events - Funcheap.pdf` |
| 10 | *Add one more* | — | Add another PDF to `documents/` to meet the 10-source requirement |

### Document ingestion pipeline

1. **Load** — `pdfplumber` extracts text from each PDF in `documents/`.
2. **Clean** — `clean_text()` in `ingest.py` removes navigation lines (Funcheap menus, Visit California headers, page numbers, map attributions, Carmel page footers), fixes hyphenated line breaks, and normalizes whitespace.
3. **Structure** — Each document becomes a dict with `source`, `filename`, `doc_type` (`travel_guide` or `events_listing`), and cleaned `text` ready for chunking.

---

## Chunking Strategy

**Chunk size:**
- Travel guides: 800 characters
- Event listings: 500 characters

**Overlap:**
- Travel guides: 100 characters
- Event listings: 80 characters

**Why these choices fit your documents:**
Visit California guides contain multi-sentence paragraphs about destinations; 800-character chunks keep a full recommendation intact (e.g., Monterey Bay Aquarium + Cannery Row context). Funcheap event PDFs are short listings with date, venue, and cost on separate lines; 500-character chunks keep individual events together and reduce cross-event noise. Both types split on paragraph boundaries first, using a sliding window only when a single paragraph exceeds the chunk size.

**Preprocessing before chunking:** PDF text cleaning via `clean_text()` (see ingestion pipeline above).

**Final chunk count:** 163 chunks across 9 documents (10 once you add another PDF).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` (sentence-transformers, embedded locally through ChromaDB)

**Production tradeoff reflection:**
- **Cost:** MiniLM is free and runs locally; API models (OpenAI `text-embedding-3-small`, Cohere) add per-token cost but remove local compute requirements.
- **Context length:** MiniLM handles short-to-medium chunks well; very long guide sections might need a model with a larger token window.
- **Multilingual support:** Current corpus is English-only; adding Spanish tourism content would warrant `multilingual-e5` or similar.
- **Domain accuracy:** Place names like "Sensorio" and "Carmel-by-the-Sea" can be confused with generic travel text; larger or domain-fine-tuned embeddings would improve retrieval precision.
- **Local vs API:** Local embeddings keep documents private and avoid rate limits; API embeddings simplify deployment and model updates for frequently changing event calendars.

---

## Grounded Generation

**System prompt grounding instruction:**

```
Answer ONLY using the retrieved context below. Do not use outside knowledge.
If the context does not contain enough information, say you don't have it.
Cite source document names inline. Do not invent events, prices, dates, or locations.
```

**Mechanism:**
- Retrieved chunks are formatted as numbered context blocks with source names.
- Chunks with cosine distance above 0.65 are filtered out before calling the LLM.
- Temperature is set to 0.1 to reduce hallucination.
- The LLM is Groq's `llama-3.3-70b-versatile`.

**How source attribution is surfaced in the response:**
- The system prompt requires inline citations by document name.
- Every response ends with `**Sources:** Document A, Document B`.
- The Gradio UI also appends retrieved chunk previews with source names and similarity scores for demo transparency.

---

## Evaluation Report

Run these 5 questions through `python main.py "<question>"` or the Gradio UI, then update the table with your live results.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is Sensorio in Paso Robles? | Outdoor "Field of Light" art installation in Paso Robles wine country | *Run system and record* | *Relevant if Sensorio PDF ranks top* | *Accurate if answer matches installation description* |
| 2 | What is notable about the Monterey Bay Aquarium? | Housed in a former sardine cannery on Cannery Row; acclaimed marine aquarium | *Run system and record* | *Relevant if Monterey guide ranks top* | *Accurate if Cannery Row / cannery detail included* |
| 3 | What landmark defines Morro Bay? | Morro Rock, 576-foot volcanic plug off the shore | *Run system and record* | *Relevant if Morro Bay PDF ranks top* | *Accurate if Morro Rock mentioned* |
| 4 | Where does the Central Coast Wine Tour start and end? | Santa Barbara → Paso Robles, 8 stops, ~155 miles | *Run system and record* | *Relevant if Wine Tour PDF ranks top* | *Accurate if both cities named* |
| 5 | What annual events happen in Carmel-by-the-Sea? | Carmel Culinary Week, Bach Festival, Art Walk, Car Week, Film Festival, etc. | *Run system and record* | *Relevant if Carmel events PDF ranks top* | *Accurate if named events match PDF* |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** *Example — fill after running live evals*

"What time does Sensorio close on weekdays?"

**What the system returned:** May return a vague answer or "I don't have that information" if hours are not in a single retrieved chunk.

**Root cause (tied to a specific pipeline stage):** **Chunking / retrieval.** Opening hours may sit in a separate paragraph from the Sensorio description. If the hours paragraph lands in a low-similarity chunk, retrieval returns the descriptive chunk without schedule details, so generation cannot answer even though the PDF contains the information.

**What you would change to fix it:** Increase top-k to 6, add section-header-aware chunking for Visit California guides, or attach structured metadata (e.g., `topic: hours`) during ingestion.

---

## Spec Reflection

**One way the spec helped you during implementation:**

Defining doc-type-specific chunk sizes in `planning.md` before coding led directly to separate 800/500 character strategies in `ingest.py`, rather than a single arbitrary split.

**One way your implementation diverged from the spec, and why:**

The spec assumed 10 documents at planning time; the repo currently has 9 PDFs. Ingestion still runs, but one more source should be added to fully meet the assignment requirement.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* Chunking Strategy and document samples from `planning.md`, plus the starter `ingest.py` template.
- *What it produced:* `load_documents()`, `clean_text()`, and paragraph-aware `chunk_document()` with travel vs events sizing.
- *What I changed or overrode:* Added extra noise patterns for Carmel PDF footers (`1 of 4`, date stamps) after inspecting raw extraction output.

**Instance 2**

- *What I gave the AI:* Retrieval and generation TODOs from starter files, grounding requirements from the assignment.
- *What it produced:* `retrieve()` flattening ChromaDB results, `generate_response()` with distance filtering and source footer.
- *What I changed or overrode:* Set `MAX_DISTANCE = 0.65` and appended retrieved-chunk previews in the Gradio UI for demo visibility.
