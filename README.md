# CoTA — Co-Teaching Assistant

A risk-tiered AI teaching assistant that answers student questions grounded in actual course materials — the syllabus and the assigned textbook. Built for DATA643 Time Series Analysis at the University of Maryland.

**Live demo:** [cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app](https://cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app)

---

## Overview

CoTA is not a general-purpose chatbot. Every response is grounded in one of two sources — the course textbook or the course syllabus — and every question is classified before answering to determine how much can go wrong if the answer is wrong.

The core insight comes from participatory research with graduate students and teaching assistants: **the harm from a wrong policy answer (missed deadline, failed assignment) is far greater than the harm from a wrong concept answer**. That asymmetry demands a different handling pipeline for different question types, not just different prompts.

### How it works

| Question type | Source | Behavior |
|--------------|--------|----------|
| **Concept** — course topics, methods, theory | Textbook (Shumway & Stoffer Ch. 1–6) | Retrieves relevant passages, generates grounded explanation |
| **Policy** — deadlines, grading, rules | Syllabus | Retrieves relevant section, cites it explicitly, admits gaps |
| **Sensitive** — grades, mental health, accommodations | — | Steps back entirely, routes to the right human contact |
| **Beyond scope** | Textbook (best effort) | Attempts answer; if nothing relevant, redirects to instructor |

Every answer includes a collapsible panel showing the exact retrieved passages used, so students can verify the grounding themselves.

---

## Research Foundation

CoTA's design is grounded in prior participatory research conducted with graduate students and TAs using semi-structured interviews and photovoice methodology. Three findings shaped the architecture:

1. **Off-hours access without social cost.** Students described AI value as private, low-pressure, and available at the moment of confusion — not as a replacement for human expertise.
2. **Asymmetric stakes of policy errors.** Wrong policy answers cause concrete harm (failed assignments, missed accommodations). Wrong concept answers cause confusion. The system treats these differently by design.
3. **Platform authority amplifies both value and risk.** A tool embedded in Canvas carries institutional weight. Showing retrieved sources directly addresses the heightened risk of unofficial guidance being mistaken for official policy.

The key design principle: *success is not just about accuracy — it is about knowing when the AI should step back to protect the student-teacher relationship.*

---

## Architecture

```
Student query
    │
    ▼
Claude (risk classifier)
    │
    ├── concept ──► BM25 → textbook chunks ──► Claude (answer with citations)
    ├── policy ───► BM25 → syllabus chunks ──► Claude (answer citing section)
    ├── sensitive ─────────────────────────► Claude (step-back, human routing)
    └── beyond ───► BM25 → textbook ────────► Claude (best effort or redirect)
                                                        │
                                              Visible evidence panel
```

**Retrieval** uses BM25 (Okapi BM25) over two pre-built indexes:
- **Textbook index** — 446 chunks extracted from Chapters 1–6 of *Shumway & Stoffer, Time Series Analysis and Its Applications (4th ed.)*, split using the PDF's embedded table of contents to find exact section boundaries
- **Syllabus index** — 21 chunks split by section markers covering grading, policies, schedule, and assignments

BM25 was chosen over neural embeddings deliberately: it is pure Python, has no compiled dependencies, is robust across Python versions, and performs well for this domain because students use course-specific terminology (ARIMA, eigendecomposition, spectral density) that keyword matching captures precisely.

**Risk classification and answer generation** use Claude Sonnet 4.6 via the Anthropic API. Claude runs twice per query: once to classify risk tier, once to generate the grounded answer.

---

## Stack

| Component | Technology |
|-----------|-----------|
| LLM | Claude Sonnet 4.6 (Anthropic) |
| Retrieval | BM25 via `rank-bm25` |
| PDF parsing | PyMuPDF |
| UI | Streamlit |
| Deployment | Streamlit Community Cloud |

No vector database. No neural embedding model. No GPU dependency. The pre-built BM25 indexes are stored as pickle files and committed to the repository — cold starts are instant.

---

## Setup

```bash
git clone https://github.com/madhusomethingg/cota-data643
cd cota-data643

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=your_key_here

# Build the retrieval indexes (one-time)
python ingest.py

# Run
streamlit run app.py
```

App runs at `http://localhost:8501`.

For Streamlit Cloud deployment, add `ANTHROPIC_API_KEY` under **App Settings → Secrets**.

---

## Repository Structure

```
cota-data643/
├── app.py              # Streamlit UI, risk-tiered chat logic, RAG pipeline
├── ingest.py           # Builds BM25 indexes from syllabus and textbook
├── vector_store.py     # BM25 vector store — add, query, save, load
├── requirements.txt
├── data/
│   ├── syllabus.txt    # DATA643 Fall 2025 course syllabus
│   └── textbook.pdf    # Shumway & Stoffer 4th ed. (Chapters 1–6 ingested)
└── vector_store/
    ├── syllabus.pkl    # Pre-built BM25 index — syllabus
    └── textbook.pkl    # Pre-built BM25 index — textbook
```

---

## Extending to Other Courses

The ingestion pipeline is course-agnostic. To adapt CoTA for a different course:

1. Replace `data/syllabus.txt` with the new syllabus, using `### SECTION NAME ###` markers for chunking
2. Replace `data/textbook.pdf` with the course textbook; update `ASSIGNED_SECTIONS` in `ingest.py` to reflect the course reading list
3. Run `python ingest.py` to rebuild the indexes
4. Update the sidebar and banner content in `app.py`

---

## Limitations

- **Static knowledge base.** The textbook and syllabus are ingested once. Live Canvas integration (assignment updates, announcements) would require a Canvas LTI connection.
- **Keyword retrieval.** BM25 retrieves by term overlap, not semantic similarity. Questions phrased very differently from the textbook's language may retrieve less relevant passages.
- **Single course.** Currently configured for DATA643. Multi-course support requires parameterising the ingestion and configuration.

---

## Authors

Madhumitha Rajagopal 
