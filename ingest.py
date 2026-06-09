import os
import re

import pdfplumber

from config import DOCS_PATH

# Lines matching these patterns are dropped during cleaning (nav, ads, footers).
_NOISE_LINE_PATTERNS = [
    re.compile(r"^Menu\b"),
    re.compile(r"^All Events\b"),
    re.compile(r"^Search Funcheap"),
    re.compile(r"^Home »"),
    re.compile(r"visitcalifornia\.com"),
    re.compile(r"^© Mapbox"),
    re.compile(r"^© OpenStreetMap"),
    re.compile(r"^Add Event\b"),
    re.compile(r"^Advertise\b"),
    re.compile(r"^Newsletter\b"),
    re.compile(r"Free Museum Days"),
    re.compile(r"Top Picks of the Week"),
    re.compile(r"San Francisco Calendar"),
    re.compile(r"East Bay Calendar"),
    re.compile(r"Bay Area Calendar"),
    re.compile(r"Peninsula Events"),
    re.compile(r"Free Today"),
    re.compile(r"^Weekend\b"),
    re.compile(r"Win Tix"),
    re.compile(r"^Summary\b"),
    re.compile(r"^Things To Do\b"),
    re.compile(r"^Videos\b"),
    re.compile(r"^Podcasts\b"),
    re.compile(r"^Map View\b"),
    re.compile(r"^Created by California Travel Experts\b"),
    re.compile(r"^\d+$"),
    re.compile(r"^\d+ of \d+"),
    re.compile(r"^MENU$"),
    re.compile(r"^Best Kept Carmel Travel Updates\b"),
    re.compile(r"^Visitor Center\b"),
    re.compile(r"^Destination Stewardship\b"),
    re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}"),
]

_CHUNK_CONFIG = {
    "travel_guide": {"chunk_size": 800, "overlap": 100, "min_length": 80},
    "events_listing": {"chunk_size": 500, "overlap": 80, "min_length": 60},
}


def source_name_from_filename(filename: str) -> str:
    name = filename.replace(".pdf", "")
    name = re.sub(r" _ Visit California$", "", name)
    name = re.sub(r" _ Carmel-by-the-Sea, California$", "", name)
    return name


def _classify_doc_type(filename: str) -> str:
    lower = filename.lower()
    if "visitcalifornia" in lower or "visit california" in lower:
        return "travel_guide"
    if "funcheap" in lower or "northcoast" in lower or "events" in lower:
        return "events_listing"
    return "travel_guide"


def _extract_pdf_text(filepath: str) -> str:
    with pdfplumber.open(filepath) as pdf:
        pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
    return "\n\n".join(pages)


def clean_text(text: str) -> str:
    """Remove navigation, ads, and PDF artifacts; normalize whitespace."""
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 3:
            continue
        if any(pattern.search(line) for pattern in _NOISE_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _sliding_window_chunks(
    text: str,
    source: str,
    filename: str,
    doc_type: str,
    chunk_size: int,
    overlap: int,
    min_length: int,
    prefix: str,
    start_counter: int,
) -> list[dict]:
    chunks = []
    counter = start_counter
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()

        if len(chunk_text) >= min_length:
            chunks.append({
                "text": chunk_text,
                "source": source,
                "filename": filename,
                "doc_type": doc_type,
                "chunk_id": f"{prefix}_{counter}",
            })
            counter += 1

        if end >= len(text):
            break
        start += chunk_size - overlap

    return chunks


def chunk_document(text: str, source: str, filename: str, doc_type: str) -> list[dict]:
    """
    Split a document into chunks using a doc-type-aware strategy.

    Travel guides use larger paragraph-grouped chunks to preserve narrative context.
    Event listings use smaller chunks so individual events stay intact.
    """
    cfg = _CHUNK_CONFIG[doc_type]
    chunk_size = cfg["chunk_size"]
    overlap = cfg["overlap"]
    min_length = cfg["min_length"]

    prefix = re.sub(r"[^\w]+", "_", filename.lower()).strip("_")[:40]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    buffer = ""
    counter = 0

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if buffer and len(buffer) >= min_length:
                chunks.append({
                    "text": buffer,
                    "source": source,
                    "filename": filename,
                    "doc_type": doc_type,
                    "chunk_id": f"{prefix}_{counter}",
                })
                counter += 1
                buffer = ""

            window_chunks = _sliding_window_chunks(
                paragraph,
                source,
                filename,
                doc_type,
                chunk_size,
                overlap,
                min_length,
                prefix,
                counter,
            )
            chunks.extend(window_chunks)
            counter += len(window_chunks)
            continue

        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue

        if len(buffer) >= min_length:
            chunks.append({
                "text": buffer,
                "source": source,
                "filename": filename,
                "doc_type": doc_type,
                "chunk_id": f"{prefix}_{counter}",
            })
            counter += 1
        buffer = paragraph

    if buffer and len(buffer) >= min_length:
        chunks.append({
            "text": buffer,
            "source": source,
            "filename": filename,
            "doc_type": doc_type,
            "chunk_id": f"{prefix}_{counter}",
        })

    return chunks


def load_documents() -> list[dict]:
    """Load and preprocess all PDF documents from the documents folder."""
    documents = []

    for filename in sorted(os.listdir(DOCS_PATH)):
        if not filename.endswith(".pdf"):
            continue

        filepath = os.path.join(DOCS_PATH, filename)
        raw_text = _extract_pdf_text(filepath)
        if not raw_text:
            print(f"Skipping empty PDF: {filename}")
            continue

        cleaned = clean_text(raw_text)
        if not cleaned:
            print(f"Skipping PDF with no usable text after cleaning: {filename}")
            continue

        source = source_name_from_filename(filename)
        doc_type = _classify_doc_type(filename)
        documents.append({
            "source": source,
            "filename": filename,
            "doc_type": doc_type,
            "text": cleaned,
        })

    print(
        f"Loaded {len(documents)} document(s): "
        f"{[d['source'] for d in documents]}"
    )
    return documents
