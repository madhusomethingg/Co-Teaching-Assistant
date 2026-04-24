# CoTA — Co-Teaching Assistant
### A Canvas-integrated AI TA built on participatory research with grad students and TAs

**Hackathon:** Anthropic × Maryland Hackathon
**Track:** Campus Intelligence and Equity
**Built by:** Madhumitha Rajagopal (Graduate TA, DATA643 Time Series Analysis)

---

## 🎯 The Problem

I'm a TA for DATA643 Time Series Analysis at UMD. I see the same pattern every week: students need help at 11pm before a deadline when no human is available; first-gen and international grad students hesitate to ask "obvious" questions in public forums; and TAs like me drown in repetitive policy questions ("when is HW3 due?", "what's the late penalty?") that pull time away from the students who genuinely need a human.

Generic AI chatbots don't fix this. They hallucinate course policies, give the same answer to a "what's the late policy" question as to a "I think I'm going to fail and want my grade changed" question, and offer no path back to the human teaching team when one is needed.

## 🔬 The Research

Before building, I conducted **participatory inquiry** with grad students and TAs using **semi-structured interviews and photovoice methodology** to surface lived experiences of help-seeking, trust, and perceived risks in an AI-mediated classroom. Three themes emerged:

1. **Off-hours support vs. social comfort** — *"Private feels easier. Less pressure."* AI value lies in low-pressure access at the moment of confusion.
2. **The high stakes of policy** — Mistakes on deadlines and collaboration rules are significantly more harmful than conceptual errors. Wrong concept → student is confused. Wrong policy → student fails the assignment.
3. **The authority of the platform** — Embedding inside Canvas builds trust, but heightens the risk of unofficial guidance being treated as official.

The headline finding: **success is not just about accuracy, but knowing when the AI should step back to protect the student-teacher relationship.**

## 🛠️ What CoTA Does

CoTA is a Canvas-integrated AI co-teaching assistant for DATA643. It implements three research-driven design implications, all working live in the demo:

### 1. Risk-Tiered Responses
Every student question is classified by Claude into one of three tiers — `concept`, `policy`, or `sensitive` — and answered differently:
- **Concept** (e.g., "Explain ARIMA models") → Full explanation grounded in course readings, ends with a pointer to office hours.
- **Policy** (e.g., "What's the late policy?") → Answer drawn strictly from the syllabus, with a citation badge.
- **Sensitive** (e.g., "Can you change my midterm grade?") → CoTA *steps back*, acknowledges warmly, and routes to the right human (instructor, TA, ADS, Counseling Center) — never attempts to answer the substance.

### 2. Direct Policy Grounding
Policy and concept answers are powered by **retrieval-augmented generation** over the actual DATA643 syllabus. The syllabus is chunked by section (Grading, Academic Integrity, Course Outline, etc.), embedded with `sentence-transformers`, and stored in **ChromaDB**. Every policy answer is required to cite the specific syllabus section — and if the answer isn't in the syllabus, CoTA admits it and refers the student to the TA.

### 3. Visible Evidence
Below every answer, students can expand a "Visible Evidence" panel showing the exact retrieved syllabus chunks used to generate the response — directly addressing the research finding about the heightened risk of unofficial guidance when the AI is embedded in a high-authority platform.

## 🏗️ Stack

- **ChromaDB** — local persistent vector store for syllabus chunks
- **sentence-transformers** (`all-MiniLM-L6-v2`) — embeddings (runs locally, no API costs)
- **Anthropic Claude Sonnet 4.6** — risk classification + answer generation
- **Streamlit** — Canvas-styled UI

The production version would integrate with Canvas LTI/API for live syllabus, announcement, and assignment sync. The demo uses the real DATA643 Fall 2025 syllabus as its grounded knowledge base.

## 🤖 Why Claude

CoTA is built specifically on Anthropic's Claude for two reasons that map directly to the research:

1. **Instruction following for risk-tiering and step-back behavior.** The hardest part of CoTA isn't getting an answer — it's getting the model to *refuse* to answer when stepping back is the right move. Claude's reliability at honoring negative instructions ("do not attempt to answer the substance; route to a human") is what makes the sensitive tier actually work.
2. **Honest, calibrated responses.** When the syllabus doesn't contain an answer, we need the model to *say so* rather than fabricate. Claude's tendency toward calibrated uncertainty maps directly to the research finding that wrong policy answers are more harmful than acknowledged uncertainty.

In other words, CoTA leans on the Claude qualities — honesty, instruction-following, knowing when not to answer — that are exactly what a TA needs from an AI co-pilot.



Office hours have hidden barriers — time conflicts for working students and parents, social anxiety, language barriers, the fear of looking unprepared in front of an instructor. CoTA lowers that floor: every student gets the same patient, judgment-free, syllabus-grounded first-line support, 24/7. And by stepping back on sensitive questions, CoTA preserves the human relationship that matters most — it doesn't try to *replace* the TA, it gives the TA back the time to actually be one.

## 🎬 Demo

**Live demo:** `localhost:8501` after running `./run.sh` (or `streamlit run app.py`)
**Try these three questions** to see all three design implications in action:
1. *"Can you explain ARIMA models? I'm a bit lost on AR vs MA."* (concept)
2. *"What's the late policy and when is HW3 due?"* (policy — watch the citation)
3. *"I'm stressed and want my midterm grade changed."* (sensitive — watch CoTA step back)

## 📦 What's in the Repo

```
cota/
├── app.py              # Streamlit UI + risk-tiered chat logic + RAG pipeline
├── ingest.py           # Chunks syllabus → embeds → ChromaDB
├── requirements.txt    # 4 deps: streamlit, chromadb, anthropic, sentence-transformers
├── data/
│   └── syllabus.txt    # Real DATA643 Fall 2025 syllabus
├── run.sh              # One-command setup + launch
└── README.md
```
