# CoTA — Co-Teaching Assistant

### A Canvas-integrated AI TA built on participatory research with graduate students

**Hackathon:** Anthropic × Maryland Hackathon  
**Track:** Campus Intelligence and Equity  
**Built by:** Madhumitha Rajagopal — Graduate Teaching Assistant, DATA643 Time Series Analysis, University of Maryland  
**Live demo:** [cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app](https://cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app)

---

## Inspiration

I am the TA for DATA643 — a graduate-level Time Series Analysis course at UMD. Every week, without fail, I watch the same thing happen.

A student spends two hours confused about why their ARIMA model isn't converging. It's 11:47 PM on a Wednesday. Office hours ended at 7:45 PM. The homework is due at midnight. They post on the ELMS discussion board, hesitate, and delete it. They don't want to look unprepared in front of the instructor. They don't want to bother the TA at midnight. So they guess, submit something wrong, and lose points on work they actually understood — they just needed one clarifying sentence.

I've seen this over and over. And I've felt it too — as a graduate student myself, I know how much courage it takes to raise your hand and say *I don't understand*. The courage required scales up with the stakes of the course, the anxiety of the student, and the visibility of the forum.

That's why I built CoTA.

But I didn't build it on intuition. I built it on research.

---

## The Research Foundation

Before writing a single line of code, I conducted **participatory research** with graduate students and TAs using **semi-structured interviews and photovoice methodology** — a technique where participants photograph moments that represent their lived experiences, then discuss them. The goal was to understand not just *what* students struggle with, but *why* they hesitate to ask for help, and what they actually need from an AI presence in the classroom.

Three themes emerged that directly shaped every design decision in CoTA:

**Theme 1: Off-hours support vs. social comfort**

> *"Private feels easier. Less pressure."*

Students consistently described AI as valuable not because it's smarter than a human — it isn't — but because it's available at the exact moment of confusion with zero social cost. No waiting, no judgment, no performance anxiety. The value proposition isn't intelligence. It's access.

**Theme 2: The high stakes of policy**

Policy errors are asymmetrically harmful. If I give a student a wrong explanation of ARIMA's AR component, they're confused and might re-read. But if CoTA tells a student the wrong late-submission deadline and they miss it trusting that answer, they fail the assignment. The research confirmed what I suspected intuitively:

$$\text{harm}(\text{wrong policy}) \gg \text{harm}(\text{wrong concept})$$

This asymmetry demanded a different handling pipeline for policy questions — not just a better answer, but a fundamentally different approach: direct syllabus retrieval, explicit citation, and a standing instruction to admit uncertainty rather than guess.

**Theme 3: The authority of the platform**

Canvas is not just a website. For students, Canvas *is* the course. Something that lives inside Canvas carries institutional authority. That authority amplifies both the value and the risk of an embedded AI. Students said they would trust a Canvas-embedded AI *more* than a generic chatbot — which means a wrong answer carries more weight, not less.

The headline finding from the research:

> **Success is not just about accuracy. It is about knowing when the AI should step back to protect the student-teacher relationship.**

This single sentence is CoTA's north star. It is why the system has a *sensitive* tier that refuses to answer and routes to a human. That refusal is not a failure — it is the feature.

---

## What I Built

CoTA is a Canvas-integrated AI co-teaching assistant for DATA643. It implements three research-driven design implications:

### 1. Risk-Tiered Responses

Every question a student asks is first **classified by Claude** into one of four tiers before any retrieval or answering occurs:

| Tier | Example | What CoTA does |
|------|---------|----------------|
| `concept` | "Explain ARIMA models" | Answers from the course textbook (Shumway & Stoffer, Ch.1-6) |
| `policy` | "When is HW3 due?" | Answers strictly from the syllabus, with explicit section citation |
| `sensitive` | "Can you change my grade?" | Steps back entirely — warm acknowledgment + routes to the right human |
| `beyond_scope` | "Explain blockchain" | Tries the textbook; if nothing relevant, redirects to Prof. Forgy |

The classifier prompt is carefully designed to be conservative in both directions — leaning toward `concept` when ambiguous, and erring toward `sensitive` when there's any emotional weight. This is because false negatives in the sensitive tier (treating a distressed student's message as a concept question) are far more harmful than false positives.

### 2. Retrieval-Augmented Generation — Grounded in the Actual Course Materials

CoTA does not answer from general AI knowledge. It answers from *this course's* materials.

**For concept questions**, I ingested the course textbook — *Time Series Analysis and Its Applications* by Shumway & Stoffer (4th ed.) — specifically Chapters 1–6, which correspond exactly to the course reading schedule:

| Week | Topic | Textbook Sections |
|------|-------|-------------------|
| 1–2 | Time series characteristics, statistical models | Ch. 1.1–1.5 |
| 3 | Regression in time series context | Ch. 2.1–2.3 |
| 4–5 | ARIMA models | Ch. 3.1–3.9 |
| 6 | Exponential smoothing, STL decomposition | FPP 3.4–3.6, 8.1–8.7 |
| 8–9 | Spectral analysis, Fourier | Ch. 4.1–4.7 |
| 10–11 | Unit roots, ARCH/GARCH | Ch. 5.2–5.3 |
| 12 | VAR, state-space models | Ch. 5.6, 6.1–6.2 |
| 13 | LSTM, Transformers for time series | Research papers |

The textbook is chunked by section using the PDF table of contents, producing **446 retrievable chunks** from 385 pages of content. When a student asks "what is spectral density?", CoTA retrieves the actual passage from Chapter 4.2 of Shumway & Stoffer — the same book they are assigned to read — and answers from that.

**For policy questions**, the DATA643 syllabus is chunked by `### SECTION ###` markers into 21 semantically-distinct chunks covering grading structure, attendance, academic integrity, assignment due dates, and course policies. Every policy answer is required to name the specific section it drew from.

**The retrieval system** uses BM25 (Okapi BM25) — a probabilistic keyword-based ranking algorithm that is fast, dependency-free, and robust:

$$\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

where $f(q_i, D)$ is the term frequency of query term $q_i$ in document $D$, $|D|$ is the document length, $\text{avgdl}$ is the average document length across the corpus, and $k_1 = 1.5$, $b = 0.75$ are tuning parameters. The top $k=4$ chunks are retrieved and passed to Claude as grounding context.

### 3. Visible Evidence

Below every answer, students can expand a **"View evidence"** panel that shows the exact textbook or syllabus passages retrieved to generate the response. This addresses the research finding that the authority of the Canvas platform raises the stakes of unofficial guidance — by making the source transparent, students can judge the grounding themselves rather than taking the answer on faith.

---

## How I Built It

### Architecture

```
Student query
    │
    ▼
Claude (risk classifier)
    │
    ├── concept ──► BM25 search → textbook chunks → Claude (answer)
    ├── policy ───► BM25 search → syllabus chunks → Claude (answer, citing section)
    ├── sensitive ─► Claude (step-back response, routes to human)
    └── beyond ───► BM25 search → textbook → Claude (or redirect to Prof. Forgy)
                                                        │
                                              Visible evidence panel
```

### Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Claude Sonnet 4.6 (Anthropic) | Instruction following, calibrated uncertainty, step-back behavior |
| Retrieval | BM25 via `rank_bm25` | Pure Python, zero dependencies, works on any platform |
| PDF parsing | PyMuPDF (`fitz`) | Extracts textbook chapters using the embedded table of contents |
| UI | Streamlit | Rapid prototyping with Canvas-accurate styling |
| Deployment | Streamlit Community Cloud | Free, public URL, auto-deploys from GitHub |

### The Ingestion Pipeline

`ingest.py` runs once and builds two BM25 indexes:

1. **Syllabus index** — 21 chunks split by section headers
2. **Textbook index** — 446 chunks from Ch. 1–6 of Shumway & Stoffer, split using the PDF's table of contents to find exact section boundaries, then windowed into ~400-word overlapping passages

The pre-built indexes are committed to the repository as pickle files (~2MB total), so the deployed app loads instantly with no cold-start ingestion.

### Canvas-Accurate UI

The UI is deliberately designed to look like a Canvas LTI tool — the same interface students and instructors use every day for the course. This is not cosmetic. The research showed that platform authority matters: students engage differently with a tool that feels like it belongs in their course environment versus a generic chatbot. The sidebar mirrors the exact Canvas course navigation (Home, Announcements, Syllabus, Modules, Assignments, Discussions, Grades, Zoom) with CoTA highlighted as the active tool.

---

## Challenges

**1. The step-back problem is harder than it looks.**

Getting an LLM to *not* answer is genuinely harder than getting it to answer. The first versions of CoTA would, when faced with a sensitive question, provide a thoughtful and empathetic response that still tried to engage with the substance. That's exactly wrong. The prompt engineering for the sensitive tier went through many iterations to get Claude to consistently acknowledge the student, explain *why* it's routing them to a human (not because the question is wrong, but because they deserve proper support), and then stop — without being cold or bureaucratic.

**2. Dependency hell on cloud deployment.**

The original architecture used ChromaDB for vector storage and `sentence-transformers` for embeddings. ChromaDB 1.x introduced a heavy gRPC telemetry stack that fails on Python 3.14 (which Streamlit Cloud now defaults to) due to a protobuf binary incompatibility. Switching to `sentence-transformers` directly caused a `RuntimeError: can't register atexit after shutdown` error from PyTorch's multiprocessing module on the same Python version. The solution was to remove both entirely — replacing the neural embedding approach with BM25, which is pure Python, has no C extensions, and is robust to any Python version. The retrieval quality is excellent for this use case because students use course-specific terminology (ARIMA, spectral density, eigendecomposition) that keyword matching handles well.

**3. Knowing what not to ingest.**

The textbook has 568 pages and 7 chapters plus appendices. The course covers specific sections across Chapters 1–6. Rather than ingesting everything or arbitrarily cutting at a page count, I used the PDF's embedded table of contents to programmatically identify section boundaries and extract only the course-assigned sections — producing 446 targeted, retrievable chunks rather than a noisy full-book dump. Questions about topics in Chapter 7 (statistical methods in the frequency domain, which isn't in the course schedule) are handled by the `beyond_scope` tier rather than hallucinated answers from out-of-scope material.

**4. Balancing the equity angle without performing it.**

The course has working students, students with dependents, international students navigating a second language, and students with disabilities who may face additional barriers to in-person office hours. CoTA needs to lower the floor of access for all of them — not with hollow "inclusivity" language, but structurally: by being available at 2 AM, by removing the social performance of asking a question in a public forum, and by routing disability accommodation questions directly to UMD's Accessibility & Disability Service rather than guessing at eligibility. The equity dimension isn't a feature — it's the point.

---

## What I Learned

- **Research first, code second.** The three-tier risk architecture came entirely from the participatory research findings. Without that, I would have built a generic RAG chatbot that answers every question the same way. The research gave me the insight that sensitive and policy questions need fundamentally different handling — not just different prompts.

- **Refusal is a feature.** The most important thing Claude does in CoTA is sometimes refuse to answer. That took real prompt work to get right, and it's the thing I'm most proud of.

- **Infrastructure matters as much as the model.** I spent more time on deployment, dependency resolution, and ingestion pipeline design than on prompt engineering. A brilliant RAG system that crashes in production helps nobody.

- **The retrieval problem is a design problem.** Choosing *what* to retrieve from — and structuring those documents — is as important as the retrieval algorithm. Having the textbook chunked by section means that "explain ARIMA models" returns Chapter 3 content, not a random passage that happens to mention ARIMA in passing.

---

## What's Next

If CoTA were taken to production for real course use:

- **Canvas LTI integration** — connect to the Canvas API to sync the live syllabus, assignment deadlines, and announcements automatically so the knowledge base stays current without manual re-ingestion
- **TA dashboard** — aggregate anonymised question logs so I can see which concepts students struggle with most before class, letting me target my office hours and lecture emphasis
- **Multi-course extension** — parameterise the ingestion pipeline so any instructor can drop in their syllabus and textbook and get a CoTA instance for their course in minutes
- **Evaluation harness** — build a test set of question/answer pairs (verified by the instructor) to measure retrieval precision and answer accuracy over time, and alert on drift

---

## Why Claude

CoTA is built on Anthropic's Claude for two reasons that map directly to the research:

**Instruction following for negative behaviors.** The hardest requirement in CoTA is getting the model to *step back* on sensitive questions — not just flag them, but genuinely decline to engage with the substance while still being warm and helpful about the redirect. Claude's reliability on this — consistently honoring "do not attempt to answer; route to a human" — is what makes the sensitive tier actually work.

**Calibrated uncertainty on policy.** When the syllabus doesn't contain an answer, the model must say so rather than confabulate. Given that wrong policy answers are disproportionately harmful, a model that confidently makes up a deadline is worse than useless. Claude's tendency toward epistemic honesty — acknowledging what it doesn't know — maps directly onto what the research said students and instructors need from a course-embedded AI.

---

## The Bigger Picture

Office hours have hidden barriers. Time conflicts for students who work or have families. Social anxiety about asking in front of peers. Language barriers. The fear of looking unprepared. These barriers are not equally distributed — they fall harder on students who are already navigating the most.

CoTA lowers that floor. Every student gets the same patient, judgment-free, syllabus-grounded support at any hour. And by stepping back on sensitive questions, CoTA doesn't try to replace the human teaching relationship — it protects it. It gives the TA back the time to be a TA, for the students who genuinely need a human in the room.

That's the goal. Not a smarter chatbot. A better classroom.

---

*Built at the Anthropic × Maryland Hackathon by Madhumitha Rajagopal, Graduate TA, DATA643 Time Series Analysis, University of Maryland.*  
*Live: [cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app](https://cota-data643-iss5zmonhuiwrw7h2yxdhg.streamlit.app)*
