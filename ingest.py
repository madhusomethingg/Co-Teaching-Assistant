"""
ingest.py — Loads syllabus + textbook (Ch.1-6) into a lightweight numpy vector store.
Run ONCE: python ingest.py
"""
import os
import re
import fitz  # pymupdf
from vector_store import VectorStore

SYLLABUS_PATH = "data/syllabus.txt"
TEXTBOOK_PATH = "data/textbook.pdf"

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


# ── Syllabus ───────────────────────────────────────────────────────────────────

def chunk_syllabus(text: str):
    parts = re.split(r"### ([^#]+) ###", text)
    chunks, metas = [], []
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        for para in [p.strip() for p in content.split("\n\n") if p.strip()]:
            chunks.append(f"[{header}]\n{para}")
            metas.append({"section": header, "source": "syllabus"})
    return chunks, metas


# ── Textbook ───────────────────────────────────────────────────────────────────

def _chapter_title(toc, chapter_num):
    count = 0
    skip = {"Preface to the Fourth Edition", "Preface to the Third Edition",
            "Statistical Methods in the Frequency Domain",
            "Appendix Large Sample Theory ", "Appendix Time Domain Theory",
            "Appendix Spectral Domain Theory", "Appendix R Supplement",
            "References", "Index"}
    for level, title, _ in toc:
        if level == 1 and title not in skip and not title.startswith("Appendix"):
            count += 1
            if count == chapter_num:
                return title
    return f"Chapter {chapter_num}"


def _clean(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def extract_textbook_chunks(pdf_path: str):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    skip_titles = {"Preface to the Fourth Edition", "Preface to the Third Edition",
                   "Statistical Methods in the Frequency Domain",
                   "Appendix Large Sample Theory ", "Appendix Time Domain Theory",
                   "Appendix Spectral Domain Theory", "Appendix R Supplement",
                   "References", "Index"}

    chapter_num = 0
    current_chapter = None
    sections = []

    for level, title, page in toc:
        if level == 1:
            if title in skip_titles or title.startswith("Appendix"):
                current_chapter = None
            else:
                chapter_num += 1
                current_chapter = chapter_num
        elif level == 2 and current_chapter is not None:
            if 1 <= current_chapter <= 6 and title.strip() != "Problems":
                assigned = title.strip() in ASSIGNED_SECTIONS.get(str(current_chapter), [])
                sections.append({
                    "chapter": current_chapter,
                    "chapter_title": _chapter_title(toc, current_chapter),
                    "section_title": title.strip(),
                    "start_page": page - 1,
                    "assigned": assigned,
                })

    for i in range(len(sections) - 1):
        sections[i]["end_page"] = sections[i + 1]["start_page"]
    if sections:
        sections[-1]["end_page"] = min(sections[-1]["start_page"] + 15, len(doc) - 1)

    chunks, metas = [], []
    for sec in sections:
        raw = "".join(doc[p].get_text() for p in range(sec["start_page"], sec["end_page"]))
        text = _clean(raw)
        if len(text) < 50:
            continue
        words = text.split()
        for j in range(0, len(words), 350):
            chunk_words = words[j: j + 400]
            if len(chunk_words) < 30:
                continue
            chunks.append(
                f"[Chapter {sec['chapter']}: {sec['chapter_title']} — {sec['section_title']}]\n"
                + " ".join(chunk_words)
            )
            metas.append({
                "chapter": str(sec["chapter"]),
                "chapter_title": sec["chapter_title"],
                "section": sec["section_title"],
                "assigned": str(sec["assigned"]),
                "source": "textbook",
            })

    doc.close()
    return chunks, metas


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("CoTA Ingestion — syllabus + Shumway & Stoffer Ch.1-6\n")

    print("Loading syllabus...")
    with open(SYLLABUS_PATH) as f:
        syllabus_text = f.read()
    s_docs, s_metas = chunk_syllabus(syllabus_text)
    print(f"  {len(s_docs)} chunks")

    syllabus_store = VectorStore("syllabus")
    syllabus_store.add(s_docs, s_metas)
    syllabus_store.save()

    print("\nLoading textbook (Ch.1-6)...")
    t_docs, t_metas = extract_textbook_chunks(TEXTBOOK_PATH)
    print(f"  {len(t_docs)} chunks")

    textbook_store = VectorStore("textbook")
    textbook_store.add(t_docs, t_metas)
    textbook_store.save()

    print("\nDone. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
