"""
ingest.py — Loads the course syllabus AND textbook (chapters 1-6) into ChromaDB.
Run ONCE before starting the app: python ingest.py
"""
import os
import re
import fitz  # pymupdf
import chromadb
from chromadb.utils import embedding_functions

# --- Config ---
SYLLABUS_PATH = "data/syllabus.txt"
TEXTBOOK_PATH = "data/textbook.pdf"
DB_PATH = "./chroma_db"
SYLLABUS_COLLECTION = "data643_syllabus"
TEXTBOOK_COLLECTION = "data643_textbook"

EMBED_MODEL = "all-MiniLM-L6-v2"

# Chapters covered in this course (from syllabus course outline)
# Ch 7+ is NOT part of the course
COURSE_CHAPTER_RANGE = (1, 6)  # inclusive

# Which sections are directly assigned as readings (for metadata tagging)
ASSIGNED_SECTIONS = {
    "1": ["The Nature of Time Series Data", "Time Series Statistical Models",
          "Measures of Dependence", "Stationary Time Series", "Estimation of Correlation"],
    "2": ["Classical Regression in the Time Series Context",
          "Exploratory Data Analysis", "Smoothing in the Time Series Context"],
    "3": ["Autoregressive Moving Average Models", "Difference Equations",
          "Autocorrelation and Partial Autocorrelation", "Integrated Models for Nonstationary Data",
          "Building ARIMA Models", "Multiplicative Seasonal ARIMA Models"],
    "4": ["Cyclical Behavior and Periodicity", "The Spectral Density",
          "Periodogram and Discrete Fourier Transform", "Nonparametric Spectral Estimation",
          "Parametric Spectral Estimation", "Linear Filters"],
    "5": ["Unit Root Testing", "GARCH Models", "Multivariate ARMAX Models"],
    "6": ["Linear Gaussian Model", "Filtering, Smoothing, and Forecasting"],
}


# ── Syllabus ingestion ─────────────────────────────────────────────────────────

def chunk_syllabus(text: str):
    pattern = r"### ([^#]+) ###"
    parts = re.split(pattern, text)
    chunks = []
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if not content:
            continue
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for j, para in enumerate(paragraphs):
            chunks.append({
                "id": f"syllabus_{header.replace(' ', '_').lower()}_{j}",
                "text": f"[{header}]\n{para}",
                "section": header,
                "source": "syllabus",
            })
    return chunks


# ── Textbook ingestion ─────────────────────────────────────────────────────────

def extract_textbook_chunks(pdf_path: str):
    """
    Extract text from textbook chapters 1-6 using the PDF table of contents.
    Each section becomes one or more retrievable chunks.
    """
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()  # [level, title, page_number]

    # Identify chapter and section boundaries within chapters 1-6
    chapter_num = 0
    sections = []  # list of dicts: {chapter, section_title, start_page, assigned}

    for i, (level, title, page) in enumerate(toc):
        if level == 1:
            # Detect chapter number by counting top-level content entries
            # Skip prefaces; chapters start with "Characteristics of Time Series"
            if title.startswith("Preface") or title.startswith("Appendix") or \
               title == "References" or title == "Index" or \
               title == "Statistical Methods in the Frequency Domain":
                chapter_num_tmp = None
            else:
                chapter_num += 1
                chapter_num_tmp = chapter_num
            current_chapter = chapter_num_tmp
        elif level == 2 and current_chapter is not None:
            if COURSE_CHAPTER_RANGE[0] <= current_chapter <= COURSE_CHAPTER_RANGE[1]:
                if title.strip() != "Problems":  # skip problem sets
                    assigned = title.strip() in ASSIGNED_SECTIONS.get(str(current_chapter), [])
                    sections.append({
                        "chapter": current_chapter,
                        "chapter_title": _chapter_title(toc, current_chapter),
                        "section_title": title.strip(),
                        "start_page": page - 1,  # convert to 0-indexed
                        "assigned": assigned,
                    })

    # Add end pages by looking at next section's start
    for i in range(len(sections) - 1):
        sections[i]["end_page"] = sections[i + 1]["start_page"]
    # Last section in Ch 6 ends before Ch 7
    if sections:
        sections[-1]["end_page"] = sections[-1]["start_page"] + 15  # safe buffer

    # Extract and chunk text per section
    chunks = []
    for sec in sections:
        text = ""
        start = sec["start_page"]
        end = min(sec["end_page"], len(doc) - 1)
        for p in range(start, end):
            text += doc[p].get_text()

        text = _clean_text(text)
        if len(text) < 50:
            continue

        # Split into ~400-word chunks for tight retrieval
        words = text.split()
        chunk_size = 400
        overlap = 50
        for j in range(0, len(words), chunk_size - overlap):
            chunk_words = words[j: j + chunk_size]
            if len(chunk_words) < 30:
                continue
            chunk_text = " ".join(chunk_words)
            chunk_id = f"book_ch{sec['chapter']}_{sec['section_title'].replace(' ', '_').lower()[:40]}_{j}"
            chunks.append({
                "id": chunk_id,
                "text": f"[Chapter {sec['chapter']}: {sec['chapter_title']} — {sec['section_title']}]\n{chunk_text}",
                "chapter": str(sec["chapter"]),
                "chapter_title": sec["chapter_title"],
                "section": sec["section_title"],
                "assigned": str(sec["assigned"]),
                "source": "textbook",
            })

    doc.close()
    return chunks


def _chapter_title(toc, chapter_num):
    """Return the title of the nth chapter-level entry (skipping prefaces/appendices)."""
    count = 0
    for level, title, page in toc:
        if level == 1 and not title.startswith("Preface") and \
           not title.startswith("Appendix") and title not in ("References", "Index",
           "Statistical Methods in the Frequency Domain"):
            count += 1
            if count == chapter_num:
                return title
    return f"Chapter {chapter_num}"


def _clean_text(text: str) -> str:
    """Clean up extracted PDF text."""
    # Remove excessive whitespace and page artifacts
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # Remove lines that are just numbers (page numbers)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("🎓 CoTA Ingestion — DATA643 syllabus + textbook (Chapters 1-6)")
    print()

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    client = chromadb.PersistentClient(path=DB_PATH)

    # ── Syllabus ──
    print("📄 Loading syllabus...")
    with open(SYLLABUS_PATH, "r") as f:
        syllabus_text = f.read()
    syllabus_chunks = chunk_syllabus(syllabus_text)
    print(f"  ✓ {len(syllabus_chunks)} chunks from syllabus")

    try:
        client.delete_collection(SYLLABUS_COLLECTION)
    except Exception:
        pass
    syllabus_col = client.create_collection(
        name=SYLLABUS_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"description": "DATA643 syllabus — policies, schedule, grading"},
    )
    syllabus_col.add(
        ids=[c["id"] for c in syllabus_chunks],
        documents=[c["text"] for c in syllabus_chunks],
        metadatas=[{"section": c["section"], "source": "syllabus"} for c in syllabus_chunks],
    )
    print(f"  ✓ Stored in ChromaDB collection: {SYLLABUS_COLLECTION}")
    print()

    # ── Textbook ──
    print("📚 Loading textbook (Chapters 1-6 of Shumway & Stoffer)...")
    book_chunks = extract_textbook_chunks(TEXTBOOK_PATH)
    print(f"  ✓ {len(book_chunks)} chunks from textbook chapters 1-6")

    try:
        client.delete_collection(TEXTBOOK_COLLECTION)
    except Exception:
        pass
    book_col = client.create_collection(
        name=TEXTBOOK_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"description": "Shumway & Stoffer Time Series Analysis 4e — Chapters 1-6"},
    )

    # Add in batches of 100 to avoid memory issues
    batch_size = 100
    for i in range(0, len(book_chunks), batch_size):
        batch = book_chunks[i: i + batch_size]
        book_col.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "chapter": c["chapter"],
                "chapter_title": c["chapter_title"],
                "section": c["section"],
                "assigned": c["assigned"],
                "source": "textbook",
            } for c in batch],
        )
        print(f"  ... stored chunks {i+1}–{min(i+batch_size, len(book_chunks))}", end="\r")

    print(f"\n  ✓ Stored in ChromaDB collection: {TEXTBOOK_COLLECTION}")
    print()
    print("✅ All done. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
