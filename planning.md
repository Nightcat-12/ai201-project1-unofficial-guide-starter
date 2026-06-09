# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

The choosen domain will be popular events in the area. This knowledge is difficult to find on the major page because it is seasonal and changes every year.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 |funcheap|South Bay    |https://sf.funcheap.com/region/south-bay/|
| 2 |funcheap|North Bay    |https://sf.funcheap.com/region/north-bay/|
| 3 |funcheap|East Bay     |https://sf.funcheap.com/region/east-bay/|
| 4 |Visit California|North Coast| https://www.visitcalifornia.com/experience/north-coast-festivals/|
| 5 |Visit California|Central Coast|https://www.visitcalifornia.com/region/central-coast/|
| 6 |Visit California|Central Coast|https://www.visitcalifornia.com/experience/central-coast-wine-country/|
| 7 |Visit California|Peso Robles|https://www.visitcalifornia.com/experience/sensorio-paso-robles/
| 8 |Visit California|Camel-By-The-Sea|https://www.carmelcalifornia.com/events-in-carmel/|
| 9 |Visit California|Monterey|https://www.visitcalifornia.com/places-to-visit/monterey/|
| 10 |Visit California|Morro Bay|https://www.visitcalifornia.com/places-to-visit/morro-bay/|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
Documents will be splited into chunks of 50-150 characters. 

**Overlap:**
There will be slight overlap in the content of each website. For example, a guide to Camel-by-the-sea will have similar parts to that of Morro Bay, such as restaurants, events, hiking spots. However, individual locations will be different.

**Reasoning:**
Each link is in a long-formatted document, which means that information will be spread across multiple paragraphs.  Each sentence will be 6-20 word long. This chunking size will ensure correct syntax because it connects to one idea. For example, fun and cheap events in northbay will include locations, time, and cost. Each paragraph in the Camel-by-the-sea guide will have different content such as restaurants, hiking spots, free events.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
The current embedding model will be all-MiniLM-L6-v2 via sentence-transformers

**Top-k:**
The number of chunks per querry would be 5 to 9, which is relatively small compared to chunks per querry of smaller chunks. The reason is because this is a text-dense document, which result in larger chunks. 

**Production tradeoff reflection:**
This choice will ensure comprehensive information but might dilute the answer.
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Chunks that split key information across boundaries.

2. Inconsistent documents.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
this is a RAG (Retrieval-Augmented Generation) pipeline with four components:

User query
    │
    ▼
[1] INGEST          ──► Rule book text is chunked and stored once at startup
    ingest.py
    │
    ▼
[2] RETRIEVE        ──► Query is embedded and matched against stored chunks
    retriever.py         via semantic similarity search
    │
    ▼
[3] GENERATE        ──► Retrieved chunks are passed as context to an LLM,
    generator.py         which produces a grounded, cited answer
    │
    ▼
[4] UI              ──► Gradio chat interface serves the response to the user
    app.py
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

1. AI tools: Claud Code
2. Input: Architecture and Evaluation Plan
3. Expected Results: 
4. Evalutation method: Answers that are close to the documents.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
