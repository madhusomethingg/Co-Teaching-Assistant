"""
CoTA — Co-Teaching Assistant for DATA643 Time Series Analysis
Canvas-integrated AI TA built on participatory research.

Risk tiers:  concept → textbook  |  policy → syllabus  |  sensitive → human
Run: streamlit run app.py
"""
import os
import json
import streamlit as st
from anthropic import Anthropic
from vector_store import VectorStore

# ── Config ─────────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"
TOP_K = 4

st.set_page_config(
    page_title="CoTA — DATA643",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,300;0,400;0,700;0,900;1,400&display=swap');

  /* ── Reset & base ── */
  html, body, [class*="css"], p, div, span, li, a {
    font-family: 'Lato', system-ui, sans-serif !important;
  }
  .stApp { background: #EFEFEF; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; max-width: 100% !important; }
  p { font-size: 15px !important; line-height: 1.65 !important; }

  /* ── Sidebar — Canvas left nav ── */
  [data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #C7CDD1 !important;
    min-width: 220px !important;
  }
  [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

  .nav-course-block {
    padding: 16px 18px 14px;
    border-bottom: 1px solid #E3E8ED;
  }
  .nav-course-tag {
    font-size: 10px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: #8C9BA5; margin: 0 0 4px 0;
  }
  .nav-course-name {
    font-size: 15px; font-weight: 700; color: #1A2833;
    margin: 0 0 2px 0; line-height: 1.3;
  }
  .nav-course-meta {
    font-size: 12px; color: #6B7780; margin: 0; line-height: 1.4;
  }

  .nav-item {
    display: block; padding: 10px 18px;
    font-size: 14px; font-weight: 400; color: #0770A2;
    text-decoration: none; border-left: 3px solid transparent;
    cursor: default; transition: background 0.12s;
    line-height: 1.3;
  }
  .nav-item:hover { background: #F5F8FA; }
  .nav-item.active {
    background: #555F65; color: #fff !important;
    font-weight: 700; border-left-color: transparent;
  }
  .nav-divider { border: none; border-top: 1px solid #E3E8ED; margin: 4px 0; }

  .team-block { padding: 12px 18px; }
  .team-role {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: #8C9BA5; margin: 0 0 1px 0;
  }
  .team-name { font-size: 14px; font-weight: 700; color: #1A2833; margin: 0 0 1px 0; }
  .team-email { font-size: 12px; color: #0770A2; margin: 0 0 12px 0; }

  /* ── Top breadcrumb ── */
  .breadcrumb {
    background: #fff; border-bottom: 1px solid #C7CDD1;
    padding: 10px 24px; font-size: 13px; color: #556572;
    display: flex; align-items: center; gap: 6px;
  }
  .breadcrumb a { color: #0770A2; text-decoration: none; font-weight: 600; }
  .breadcrumb .crumb-sep { color: #C7CDD1; font-size: 16px; }
  .breadcrumb .crumb-current { color: #1A2833; font-weight: 400; }

  /* ── Course banner ── */
  .course-banner {
    background: #7B1113;
    background-image:
      linear-gradient(160deg, #8D1416 0%, #6B0F11 50%, #4E0B0D 100%);
    color: #fff;
    padding: 28px 32px 24px;
    position: relative; overflow: hidden;
  }
  .course-banner::after {
    content: '';
    position: absolute; top: 0; right: 0; bottom: 0;
    width: 45%;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Ccircle cx='150' cy='50' r='80' fill='rgba(255,255,255,0.03)'/%3E%3Ccircle cx='180' cy='150' r='60' fill='rgba(255,255,255,0.03)'/%3E%3Ccircle cx='80' cy='160' r='40' fill='rgba(255,255,255,0.03)'/%3E%3C/svg%3E") center/cover;
    pointer-events: none;
  }
  .banner-label {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: rgba(255,255,255,0.6);
    margin: 0 0 6px 0;
  }
  .banner-title {
    font-size: 28px; font-weight: 900; color: #fff;
    margin: 0 0 4px 0; letter-spacing: -0.5px; line-height: 1.15;
  }
  .banner-subtitle {
    font-size: 14px; color: rgba(255,255,255,0.78);
    margin: 0 0 16px 0; font-weight: 400;
  }
  .banner-tags { display: flex; gap: 8px; flex-wrap: wrap; }
  .banner-tag {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    color: rgba(255,255,255,0.9);
    border-radius: 3px; padding: 3px 10px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.3px;
  }

  /* ── Info banner ── */
  .info-banner {
    background: #EBF5FB; border-left: 4px solid #0770A2;
    padding: 12px 18px; margin: 16px 0 4px 0;
    border-radius: 0 4px 4px 0; font-size: 14px; color: #1A3A4F;
    line-height: 1.55;
  }

  /* ── Risk labels ── */
  .risk-label {
    display: inline-block; padding: 4px 14px;
    border-radius: 3px; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin-bottom: 12px;
  }
  .risk-concept  { background: #E5F3EC; color: #1B6B3A; }
  .risk-policy   { background: #FEF9EC; color: #7A5500; border: 1px solid #E8C84D; }
  .risk-sensitive{ background: #FEF0EF; color: #9B1C1C; }
  .risk-beyond   { background: #F3F0FF; color: #5B21B6; }

  /* ── Citation boxes ── */
  .citation-block {
    background: #F8FAFC; border: 1px solid #DDE3E9;
    border-left: 3px solid #0770A2;
    border-radius: 0 4px 4px 0; padding: 12px 16px;
    margin: 8px 0; font-size: 13.5px;
  }
  .citation-source {
    font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; color: #0770A2; margin-bottom: 6px;
  }
  .citation-text { color: #3D4D57; line-height: 1.55; }

  /* ── Suggested prompt buttons ── */
  .stButton > button {
    background: #fff !important;
    border: 1px solid #C7CDD1 !important;
    color: #2D3B45 !important;
    font-size: 14px !important;
    font-family: 'Lato', sans-serif !important;
    border-radius: 4px !important;
    text-align: left !important;
    padding: 11px 16px !important;
    font-weight: 400 !important;
    transition: all 0.12s !important;
    line-height: 1.4 !important;
  }
  .stButton > button:hover {
    border-color: #0770A2 !important;
    color: #0770A2 !important;
    background: #EBF5FB !important;
  }
  .prompt-section-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: #8C9BA5; margin: 20px 0 10px 0;
  }

  /* ── Footer ── */
  .page-footer {
    font-size: 12px; color: #8C9BA5; text-align: center;
    padding: 16px; border-top: 1px solid #E3E8ED;
    margin-top: 16px; line-height: 1.6;
  }

  /* ── Clear btn override in sidebar ── */
  [data-testid="stSidebar"] .stButton > button {
    font-size: 13px !important;
    color: #556572 !important;
    border-color: #DDE3E9 !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    color: #C0392B !important;
    border-color: #C0392B !important;
    background: #FEF0EF !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Cached resources ────────────────────────────────────────────────────────────
def _api_key():
    """Read key from Streamlit secrets (cloud) or environment variable (local)."""
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")


@st.cache_resource(show_spinner=False)
def get_collections():
    """Load (or build) vector stores. Auto-ingests if stores are missing."""
    import sys
    if not VectorStore.exists("syllabus") or not VectorStore.exists("textbook"):
        with st.spinner("First-time setup: building course knowledge base (~2 min)..."):
            if "ingest" in sys.modules:
                del sys.modules["ingest"]
            import ingest as ing
            ing.main()
    syllabus = VectorStore.load("syllabus")
    textbook = VectorStore.load("textbook")
    return syllabus, textbook


@st.cache_resource(show_spinner=False)
def get_claude():
    api_key = _api_key()
    if not api_key:
        st.error("ANTHROPIC_API_KEY is not set. Add it in Streamlit Cloud → Settings → Secrets.")
        st.stop()
    return Anthropic(api_key=api_key)


syllabus_col, textbook_col = get_collections()
claude = get_claude()


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="nav-course-block">
      <p class="nav-course-tag">Fall 2025</p>
      <p class="nav-course-name">DATA643 · Time Series Analysis</p>
      <p class="nav-course-meta">Thu 4:00–6:45 PM &nbsp;·&nbsp; SQH 1120</p>
    </div>

    <a class="nav-item" href="#">Home</a>
    <a class="nav-item" href="#">Announcements</a>
    <a class="nav-item" href="#">Syllabus</a>
    <a class="nav-item" href="#">Modules</a>
    <a class="nav-item" href="#">Assignments</a>
    <a class="nav-item" href="#">Discussions</a>
    <a class="nav-item" href="#">Grades</a>
    <a class="nav-item" href="#">Zoom</a>
    <a class="nav-item" href="#">Lucid (Whiteboard)</a>
    <a class="nav-item" href="#">Course Reserves</a>
    <a class="nav-item" href="#">People</a>
    <a class="nav-item" href="#">Course Analytics</a>
    <hr class="nav-divider"/>
    <a class="nav-item active" href="#">CoTA &mdash; AI Assistant</a>
    <hr class="nav-divider"/>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="team-block">
      <p class="team-role">Instructor</p>
      <p class="team-name">Charles C. Forgy, PhD</p>
      <p class="team-email">ccforgy@umd.edu</p>
      <p class="team-role">Teaching Assistant</p>
      <p class="team-name">Madhumitha Rajagopal</p>
      <p class="team-email">rmadhu@umd.edu</p>
      <p class="team-meta" style="font-size:12px;color:#556572;margin:0 0 12px 0;">Mon 2–3 PM &nbsp;·&nbsp; Wed 4–5 PM</p>
    </div>
    <hr class="nav-divider"/>
    """, unsafe_allow_html=True)

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Page layout ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="breadcrumb">
  <a href="#">DATA643</a>
  <span class="crumb-sep">›</span>
  <span class="crumb-current">CoTA — AI Teaching Assistant</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="course-banner">
  <p class="banner-label">Co-Teaching Assistant</p>
  <h1 class="banner-title">CoTA</h1>
  <p class="banner-subtitle">
    DATA643 · Time Series Analysis &nbsp;·&nbsp; Fall 2025 &nbsp;·&nbsp;
    Prof. Charles C. Forgy, PhD
  </p>
  <div class="banner-tags">
    <span class="banner-tag">Textbook-grounded</span>
    <span class="banner-tag">Syllabus-aware</span>
    <span class="banner-tag">Risk-tiered responses</span>
    <span class="banner-tag">Available 24 / 7</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-banner">
  CoTA is designed for graduate students who need support outside office hours.
  Concept questions are answered from <em>Shumway &amp; Stoffer (4th ed.)</em>,
  the course textbook. Policy questions cite the syllabus directly.
  Anything requiring human judgment is routed to Prof. Forgy or TA Madhumitha.
</div>
""", unsafe_allow_html=True)


# ── Risk classification ─────────────────────────────────────────────────────────
def classify_risk(query: str):
    prompt = f"""You are classifying a student question for DATA643 Time Series Analysis (UMD grad course).

Course topics: random walks, ARIMA, exponential smoothing, spectral analysis, Fourier transforms,
ARCH/GARCH, VAR models, state-space models, LSTM and transformer-based forecasting,
time series regression, stationarity, autocorrelation, periodograms.
Textbook: Shumway & Stoffer "Time Series Analysis and Its Applications" 4th ed., Chapters 1–6.

Classify into exactly one category:
- "concept"      — student wants to understand a topic, method, or theory (e.g. "explain ARIMA", "what is spectral density", "how does Kalman filtering work")
- "policy"       — course logistics: deadlines, grading breakdown, late policy, attendance, collaboration rules, office hours, exam format, HW due dates
- "sensitive"    — grade disputes, accommodation requests, mental health, academic integrity, requests to change grades, emotionally heavy topics
- "homework"     — student is asking CoTA to DO their work: solve a specific textbook problem, complete an assignment, write code for a homework task, or do any part of graded work for them. Signals: "do it for me", "solve this", "give me the answer", "do part (a)", "write the code for problem X.X", "complete this", pasting assignment text and asking for a solution
- "beyond_scope" — clearly unrelated to time series or statistics entirely (e.g. history essay, blockchain, weather)

When in doubt between concept and homework: if the student is asking to understand → concept. If they are asking CoTA to produce the answer/solution/code they will submit → homework.

Student question: "{query}"

Respond ONLY with JSON: {{"risk": "concept|policy|sensitive|homework|beyond_scope", "reason": "one short sentence"}}"""

    response = claude.messages.create(
        model=CLAUDE_MODEL, max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(text)
        if result.get("risk") in ("concept", "policy", "sensitive", "homework", "beyond_scope"):
            return result["risk"], result.get("reason", "")
    except Exception:
        pass
    return "concept", "Defaulted to concept"


# ── Retrieval ───────────────────────────────────────────────────────────────────
def retrieve_textbook(query: str, k: int = TOP_K):
    results = textbook_col.query(query, k=k)
    return [
        {
            "text": r["text"],
            "section": f"Ch {r['meta'].get('chapter','?')} · {r['meta'].get('section','?')}",
            "chapter": r["meta"].get("chapter", "?"),
            "distance": 1 - r["score"],   # convert cosine similarity to distance
            "source": "textbook",
        }
        for r in results
    ]


def retrieve_syllabus(query: str, k: int = TOP_K):
    results = syllabus_col.query(query, k=k)
    return [
        {
            "text": r["text"],
            "section": r["meta"].get("section", "Syllabus"),
            "distance": 1 - r["score"],
            "source": "syllabus",
        }
        for r in results
    ]


# ── Answer generation ───────────────────────────────────────────────────────────
def answer_homework(query: str, sources):
    context = "\n\n---\n".join(
        f"[{s['section']}]\n{s['text']}" for s in sources
    )
    prompt = f"""You are CoTA, the AI co-teaching assistant for DATA643 Time Series Analysis at UMD.
Instructor: Prof. Charles C. Forgy, PhD. Teaching Assistant: Madhumitha Rajagopal (office hours: Mon 2–3 PM, Wed 4–5 PM).

A student is asking you to solve, complete, or write code for a specific assignment problem. You must NOT do that.

Your response must do these things in order, in clean prose (no bullet lists, no emoji):

1. Briefly explain what the problem is asking — what question is it posing, what does it want the student to do or produce. Keep this to 2–3 sentences. If the problem number is mentioned and you can identify it from the textbook excerpts, describe it specifically.

2. Explain what concepts or skills the problem is testing — what the student needs to understand to approach it (e.g. "this problem is testing your understanding of autocovariance and stationarity").

3. Say clearly, in plain language: this assignment is for you to work through — CoTA is here to help you understand concepts, not to solve problems for you.

4. Offer genuinely: if they are unsure about any specific concept the problem involves, CoTA is happy to explain it. Name the concept(s) so they know exactly what to ask.

Do NOT give any part of the solution. Do NOT write any code they could submit. Do NOT work through the math.

TEXTBOOK EXCERPTS (for context on what the problem covers):
{context}

STUDENT MESSAGE: {query}

Response:"""

    return claude.messages.create(
        model=CLAUDE_MODEL, max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    ).content[0].text


def answer_concept(query: str, sources):
    context = "\n\n---\n".join(
        f"[{s['section']}]\n{s['text']}" for s in sources
    )
    prompt = f"""You are CoTA, the AI co-teaching assistant for DATA643 Time Series Analysis at UMD.
Instructor: Prof. Charles C. Forgy, PhD. Teaching Assistant: Madhumitha Rajagopal (office hours: Mon 2–3 PM, Wed 4–5 PM).

Answer the concept question below using the textbook excerpts as your primary source.

Formatting rules — follow these exactly:
- Write in clear, flowing prose. No bullet points unless listing genuinely parallel items.
- When referencing the textbook, write naturally: "In Chapter 3..." or "Shumway & Stoffer describe..." — never use bracket citations like [Chapter 3].
- Do not use warning symbols, flags, asterisks, or emoji anywhere in the response.
- Do not add a numbered list of "key points" at the end — just answer the question directly.
- Close with one sentence: "Madhumitha (Mon 2–3 PM, Wed 4–5 PM) or Prof. Forgy (Thu 6:45–7:45 PM) are happy to go deeper during office hours."

TEXTBOOK EXCERPTS (Shumway & Stoffer, 4th ed.):
{context}

STUDENT QUESTION: {query}

Answer:"""

    return claude.messages.create(
        model=CLAUDE_MODEL, max_tokens=900,
        messages=[{"role": "user", "content": prompt}],
    ).content[0].text


def answer_policy(query: str, sources):
    context = "\n\n---\n".join(
        f"[{s['section']}]\n{s['text']}" for s in sources
    )
    prompt = f"""You are CoTA, the AI co-teaching assistant for DATA643 Time Series Analysis at UMD.

Answer the policy question below using ONLY the syllabus excerpts provided.

Formatting rules — follow these exactly:
- Write in clean, direct prose. One or two short paragraphs at most.
- Cite the syllabus section naturally in the sentence: "The syllabus states..." or "According to the grading section..." — never use bracket notation like [GRADING STRUCTURE].
- Be precise with dates, percentages, and deadlines — quote them exactly as they appear.
- Do not use warning symbols, flags, emoji, or phrases like "Ambiguity flag:" anywhere.
- If the answer is not clearly in the excerpts, say so in one sentence and direct the student to Madhumitha (rmadhu@umd.edu) or Prof. Forgy (ccforgy@umd.edu).
- If there is genuine ambiguity, mention it briefly and naturally — do not format it as a separate callout box or warning.

SYLLABUS EXCERPTS:
{context}

STUDENT QUESTION: {query}

Answer:"""

    return claude.messages.create(
        model=CLAUDE_MODEL, max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    ).content[0].text


def answer_sensitive(query: str):
    prompt = f"""You are CoTA, the AI co-teaching assistant for DATA643 at UMD.

This question needs to go to a human. Write a warm, brief response — two short paragraphs maximum.

First paragraph: acknowledge the student without judgment. One or two sentences.
Second paragraph: explain who they should contact and how. Use this information:
- Grades, grading concerns → Prof. Charles C. Forgy (ccforgy@umd.edu)
- Assignment questions, logistics → TA Madhumitha Rajagopal (rmadhu@umd.edu) — office hours Mon 2–3 PM, Wed 4–5 PM
- Disability accommodations → Accessibility & Disability Service: adsfrontdesk@umd.edu / 301-314-7682
- Mental health → UMD Counseling Center: 301-314-7651
- Sexual assault / harassment (confidential) → CARE to Stop Violence: 301-741-3442

Optionally add one sentence offering to help draft an email if useful.

Rules: no bullet lists, no emoji, no headers, no lecturing. Just two short human paragraphs.

STUDENT MESSAGE: {query}

Response:"""

    return claude.messages.create(
        model=CLAUDE_MODEL, max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    ).content[0].text


def answer_beyond(query: str, sources):
    relevant = [s for s in sources if s.get("distance", 999) < 1.4]
    if relevant:
        context = "\n\n---\n".join(
            f"[{s['section']}]\n{s['text']}" for s in relevant
        )
        prompt = f"""You are CoTA, the AI co-teaching assistant for DATA643 Time Series Analysis at UMD.

The student's question may be at the edge of the course scope. Answer using the textbook excerpts if they are relevant. Write in clean prose — no brackets, no emoji, no warning flags.

If the excerpts are relevant: answer naturally and note briefly how it connects (or doesn't) to the DATA643 curriculum.
If the excerpts are not relevant: one sentence saying this falls outside the course scope, and suggest the student ask Prof. Forgy (ccforgy@umd.edu).

TEXTBOOK CONTEXT:
{context}

STUDENT QUESTION: {query}

Answer:"""
        return claude.messages.create(
            model=CLAUDE_MODEL, max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        ).content[0].text
    else:
        return (
            "This question appears to fall outside the scope of DATA643. "
            "CoTA is grounded in the course textbook (*Shumway & Stoffer, 4th ed.*, Chapters 1–6) "
            "and the course syllabus.\n\n"
            "For questions beyond the course, please reach out to **Prof. Charles C. Forgy** "
            "(ccforgy@umd.edu) — he can point you toward the right resources."
        )


# ── Source citations ────────────────────────────────────────────────────────────
def render_sources(sources, label="source(s) retrieved"):
    if not sources:
        return
    cards = ""
    for s in sources:
        kind = "Textbook" if s.get("source") == "textbook" else "Syllabus"
        body = s["text"].split("]", 1)[-1].strip()
        preview = body[:480] + ("..." if len(body) > 480 else "")
        cards += f"""
        <div class="citation-block">
          <div class="citation-source">{kind} &nbsp;·&nbsp; {s['section']}</div>
          <div class="citation-text">{preview}</div>
        </div>"""

    st.markdown(f"""
    <details style="margin-top:10px;">
      <summary style="cursor:pointer; font-size:12px; font-weight:600;
        color:#0770A2; letter-spacing:0.4px; text-transform:uppercase;
        list-style:none; padding:6px 0; user-select:none;">
        &#9656; &nbsp;View evidence &mdash; {len(sources)} {label}
      </summary>
      <div style="margin-top:6px;">{cards}</div>
    </details>
    """, unsafe_allow_html=True)


# ── Risk label helper ───────────────────────────────────────────────────────────
RISK_META = {
    "concept":      ("Concept question · answered from textbook", "risk-concept"),
    "policy":       ("Policy question · grounded in syllabus",    "risk-policy"),
    "sensitive":    ("Routing to human support",                   "risk-sensitive"),
    "homework":     ("Assignment · here to guide, not solve",      "risk-beyond"),
    "beyond_scope": ("Beyond course scope",                        "risk-beyond"),
}


def render_risk(risk: str):
    label, css = RISK_META.get(risk, ("Question", "risk-concept"))
    st.markdown(f'<span class="risk-label {css}">{label}</span>', unsafe_allow_html=True)


# ── Chat history ────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "assistant" and "risk" in msg:
            render_risk(msg["risk"])
        st.markdown(msg["content"])
        if msg.get("sources"):
            src_type = "textbook excerpt(s)" if any(
                s.get("source") == "textbook" for s in msg["sources"]
            ) else "syllabus excerpt(s)"
            render_sources(msg["sources"], label=src_type)


# ── Suggested prompts ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown('<p class="prompt-section-label">Concept questions</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Explain ARIMA models — what do AR, I, and MA each mean?", use_container_width=True):
            st.session_state.pending = "Can you explain ARIMA models? What do the AR, I, and MA parts each mean and how do they work together?"
            st.rerun()
    with c2:
        if st.button("What is spectral density and why is it useful?", use_container_width=True):
            st.session_state.pending = "What is spectral density and why is it useful in time series analysis?"
            st.rerun()
    with c3:
        if st.button("Walk me through what Chapter 1 covers", use_container_width=True):
            st.session_state.pending = "Can you walk me through what Chapter 1 of Shumway & Stoffer covers?"
            st.rerun()

    st.markdown('<p class="prompt-section-label">Policy questions</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        if st.button("What is the late policy for homework?", use_container_width=True):
            st.session_state.pending = "What is the late policy for homework assignments?"
            st.rerun()
    with p2:
        if st.button("How is the final grade calculated?", use_container_width=True):
            st.session_state.pending = "How is the final grade calculated? What is the grading breakdown?"
            st.rerun()
    with p3:
        if st.button("When is HW3 due and what does it cover?", use_container_width=True):
            st.session_state.pending = "When is Homework 3 due and what does it cover?"
            st.rerun()


# ── Chat input ──────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask CoTA anything about DATA643...")
if "pending" in st.session_state:
    user_input = st.session_state.pending
    del st.session_state.pending

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Classifying question..."):
            risk, reason = classify_risk(user_input)

        render_risk(risk)
        sources = []

        if risk == "concept":
            with st.spinner("Searching Shumway & Stoffer Ch. 1–6..."):
                sources = retrieve_textbook(user_input, k=TOP_K)
            with st.spinner("Generating answer..."):
                answer = answer_concept(user_input, sources)

        elif risk == "policy":
            with st.spinner("Searching course syllabus..."):
                sources = retrieve_syllabus(user_input, k=TOP_K)
            with st.spinner("Grounding answer in syllabus..."):
                answer = answer_policy(user_input, sources)

        elif risk == "sensitive":
            with st.spinner("Preparing response..."):
                answer = answer_sensitive(user_input)

        elif risk == "homework":
            with st.spinner("Looking at what this problem covers..."):
                sources = retrieve_textbook(user_input, k=3)
            with st.spinner("Preparing guidance..."):
                answer = answer_homework(user_input, sources)

        else:
            with st.spinner("Checking textbook for anything relevant..."):
                sources = retrieve_textbook(user_input, k=3)
            with st.spinner("Assessing course coverage..."):
                answer = answer_beyond(user_input, sources)
            if not any(s.get("distance", 999) < 1.4 for s in sources):
                sources = []

        st.markdown(answer)

        if sources:
            src_type = "textbook excerpt(s)" if any(
                s.get("source") == "textbook" for s in sources
            ) else "syllabus excerpt(s)"
            render_sources(sources, label=src_type)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "risk": risk,
            "sources": sources,
        })


# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-footer">
  CoTA · Co-Teaching Assistant · DATA643 Time Series Analysis · Fall 2025<br>
  Grounded in <em>Shumway &amp; Stoffer, Time Series Analysis and Its Applications (4th ed.)</em>
  and the course syllabus. Built on participatory research with graduate students and TAs.
</div>
""", unsafe_allow_html=True)
