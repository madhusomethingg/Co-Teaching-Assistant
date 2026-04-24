# 🎓 CoTA — Co-Teaching Assistant

A Canvas-integrated AI co-teaching assistant for **DATA643 Time Series Analysis** (UMD, Fall 2025).
Built on participatory research with graduate students and TAs.

## What it does

CoTA answers student questions grounded in the actual course syllabus, using three research-driven design implications:

1. **Risk-tiered responses** — every question is classified as `concept` / `policy` / `sensitive`, and CoTA responds differently for each
2. **Direct policy grounding** — policy answers cite specific sections of the syllabus, retrieved via vector search
3. **Visible evidence** — students see exactly which syllabus chunks were used to answer their question

For sensitive questions (grades, accommodations, mental health), CoTA **steps back** and routes to a human — protecting the student-teacher relationship.

## Stack

- **ChromaDB** — local persistent vector database for syllabus retrieval
- **sentence-transformers** (`all-MiniLM-L6-v2`) — embeddings, runs locally, no API costs
- **Anthropic Claude API** — risk classification + answer generation
- **Streamlit** — Canvas-styled UI

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Ingest the syllabus into ChromaDB (one-time)
python ingest.py

# 4. Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`.

## Try these queries

- **Concept:** *"Can you explain ARIMA models? I'm a bit lost on AR vs MA."*
- **Policy:** *"What's the late policy and when is HW3 due?"*
- **Sensitive:** *"I'm stressed and want my midterm grade changed."*

Watch how CoTA handles each one differently — that's the research speaking.

## Project structure

```
cota/
├── app.py              # Streamlit UI + chat logic + risk-tiered answering
├── ingest.py           # One-time: chunks syllabus → embeds → ChromaDB
├── requirements.txt    # Dependencies
├── data/
│   └── syllabus.txt    # DATA643 course content (instructor info, policies, schedule)
└── chroma_db/          # Created by ingest.py — persistent vector store
```

## Research foundation

This project is built on prior participatory research using semi-structured interviews and photovoice methodology, surfacing three themes:

- **Off-hours support vs. social comfort** — students need help when humans aren't available
- **The high stakes of policy** — wrong policy answers are more harmful than wrong concept answers
- **The authority of the platform** — Canvas embedding builds trust but raises stakes

Key takeaway: *"Success is not just about accuracy, but knowing when the AI should step back to protect the student-teacher relationship."*

## Equity angle

Office hours have hidden barriers: time conflicts for working students, social anxiety, language barriers, fear of looking unprepared. CoTA lowers that floor — every student gets the same patient, judgment-free first-line support, 24/7. TAs are freed up for the students who genuinely need a human.
