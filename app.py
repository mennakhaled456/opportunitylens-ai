import html
import json
import os

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.pipeline import analyze_opportunity_with_context
from src.cv_page import render_cv_page
from src.scoring import WEIGHTS

st.set_page_config(page_title="OpportunityLens AI", page_icon="🔍", layout="wide")

# ----------------------------------------------------------------- design
PRIMARY, GOOD, WARN, BAD = "#6366F1", "#10B981", "#F59E0B", "#EF4444"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.block-container {{ padding-top: 2rem; max-width: 1150px; }}
#MainMenu, footer {{ visibility: hidden; }}

.hero {{
  background: linear-gradient(135deg, {PRIMARY} 0%, #8B5CF6 55%, #06B6D4 100%);
  border-radius: 24px; padding: 38px 42px; color: #fff; margin-bottom: 26px;
  box-shadow: 0 18px 50px rgba(99,102,241,.28);
}}
.hero h1 {{ margin: 0; font-size: 2.4rem; font-weight: 800; letter-spacing: -.02em; }}
.hero p {{ margin: 8px 0 0; font-size: 1.1rem; opacity: .92; }}

.card {{
  background: var(--secondary-background-color); border: 1px solid rgba(148,163,184,.25);
  border-radius: 18px; padding: 20px 22px; margin-bottom: 14px;
  box-shadow: 0 6px 22px rgba(0,0,0,.06);
}}
.card h4 {{ margin: 0 0 6px; font-size: 1.02rem; }}
.card p {{ margin: 0; opacity: .85; font-size: .95rem; line-height: 1.5; }}

.item {{
  border-left: 5px solid var(--c); background: var(--secondary-background-color);
  border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; font-size: .95rem; line-height: 1.5;
}}
.section-title {{ font-size: 1.25rem; font-weight: 700; margin: 26px 0 12px; }}

.ring-wrap {{ position: relative; width: 178px; height: 178px; margin: 0 auto; }}
.ring {{
  position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), rgba(148,163,184,.25) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 16px), #000 calc(100% - 15px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 16px), #000 calc(100% - 15px));
}}
.ring-text {{
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}}
.ring-num {{ font-size: 3rem; font-weight: 800; line-height: 1; color: var(--c); }}
.ring-sub {{ font-size: .85rem; opacity: .6; }}
.badge {{
  display: inline-block; padding: 7px 18px; border-radius: 999px; font-weight: 700;
  color: #fff; background: var(--c); margin-top: 14px;
}}
.bar-row {{ margin-bottom: 11px; }}
.bar-label {{ display: flex; justify-content: space-between; font-size: .9rem; margin-bottom: 4px; }}
.bar-track {{ height: 10px; border-radius: 999px; background: rgba(148,163,184,.25); overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 999px; background: var(--c); }}
.stat {{ text-align: center; }}
.stat b {{ display: block; font-size: 1.9rem; }}
.stat span {{ opacity: .7; font-size: .85rem; }}
div.stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, {PRIMARY}, #8B5CF6); border: none; border-radius: 14px;
  height: 3rem; font-weight: 700; box-shadow: 0 10px 26px rgba(99,102,241,.3);
}}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- data
SAMPLES = {
    "Real post (Tips Hindawi LLM internship)": """فرصة تدريب في مجال الـ LLMs & AI

Ready to start your journey in AI & Large Language Models?
Join our hands-on internship program designed to take you from beginner to building real AI applications using modern LLM tools.

What You'll Learn:
- Fundamentals of AI & Large Language Models
- Prompt Engineering & working with models like Mistral
- Building AI-powered apps (chatbots, assistants)
- Retrieval-Augmented Generation (RAG) & embeddings
- Fine-tuning basics & model optimization
- Working with tools like LangChain & vector databases
- Real-world projects & use cases

Duration:
6 weeks (1.5 months)

Why Join?
- Hands-on projects using real AI tools
- Mentorship from AI engineers
- Build a strong portfolio in AI & LLMs
- Learn skills in high demand globally

Who Can Apply?
Students, fresh graduates, and anyone interested in AI & LLMs (no experience required)

Apply Now:
https://lnkd.in/diHjPYZg

Comment "Applied" after applying!""",
    "Good internship (TechVision AI)": """We are looking for a Junior Machine Learning Intern.

Company: TechVision AI

The internship is a 3-month remote program.
Interns will work on real machine learning projects
and receive mentorship from experienced engineers.

Requirements:
- Basic Python knowledge
- Basic understanding of machine learning
- Good communication skills

The internship requires 20 hours per week.
The company website is available and the application
is submitted through an official company email.

Compensation is not mentioned in the description.""",
    "Suspicious offer": """URGENT!!! Data Entry Assistant needed. Earn $5000 per week working from home!
No experience needed. No interview. Guaranteed job.
To start, send a copy of your national ID, your bank account number,
and a registration fee of $50 to our WhatsApp. Limited spots, reply today!""",
    "Vague unpaid role": """Marketing Intern wanted. Full-time, 9 AM to 6 PM, 6 days a week.
Unpaid. Responsibilities will be explained later.
Possibility of employment after completion. Must have 3 years of experience.""",
    "Write my own": "",
}

CATEGORIES = [
    ("career_relevance", "Career Relevance"),
    ("learning_potential", "Learning Potential"),
    ("mentorship", "Mentorship"),
    ("company_credibility", "Company Credibility"),
    ("compensation", "Compensation"),
    ("workload", "Workload"),
    ("transparency", "Transparency"),
]

SHORT = {
    "career_relevance": "Career",
    "learning_potential": "Learning",
    "mentorship": "Mentorship",
    "company_credibility": "Credibility",
    "compensation": "Compensation",
    "workload": "Workload",
    "transparency": "Transparency",
}

VERDICT_ORDER = ["Recommended", "Consider with Caution", "High Risk"]


def esc(value) -> str:
    """Escape model text before it goes into HTML."""
    return html.escape(str(value))


def tone(score: int) -> str:
    return GOOD if score >= 70 else WARN if score >= 40 else BAD


def verdict_color(score: int) -> str:
    return GOOD if score >= 80 else WARN if score >= 40 else BAD


def plot(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def build_report(result, text: str) -> str:
    b = result.score_breakdown
    lines = [
        "# OpportunityLens AI — Opportunity Report",
        "",
        f"**Overall score:** {result.score}/100  ",
        f"**Verdict:** {result.verdict}",
        "",
        "## Score breakdown",
        *[f"- {label} ({int(WEIGHTS[k] * 100)}%): {getattr(b, k)}/100" for k, label in CATEGORIES],
        "",
        "## Strengths",
        *([f"- {s}" for s in result.strengths] or ["- None identified"]),
        "",
        "## Risks",
        *([f"- {s}" for s in result.risks] or ["- None identified"]),
        "",
        "## Missing information",
        *[f"- {s}" for s in result.missing_information],
        "",
        "## Questions to ask",
        *[f"{i}. {q}" for i, q in enumerate(result.questions_to_ask, 1)],
        "",
        "## Recommendation",
        result.recommendation,
        "",
        "---",
        "## Original description",
        text.strip(),
        "",
        "_Generated by OpportunityLens AI. Decision support only; verify every opportunity independently._",
    ]
    return "\n".join(lines)


def items_html(items, color, empty):
    """items must already be safe HTML (escape text with esc() before passing)."""
    if not items:
        return f'<div class="item" style="--c:{color}; opacity:.75">{empty}</div>'
    return "".join(f'<div class="item" dir="auto" style="--c:{color}">{i}</div>' for i in items)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🔍 OpportunityLens")
    st.caption("AI-powered internship & job analyzer")
    language = st.radio("Report language", ["English", "العربية"], horizontal=True)
    LANG = "Arabic" if language == "العربية" else "English"
    page = st.radio(
        "Navigate",
        ["🔍 Analyze", "🎯 CV Match", "📊 Evaluation", "🧠 How it works", "ℹ️ About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("⚠️ Decision support only. Always verify a company and never pay fees or share ID/bank details before an official contract.")

# ----------------------------------------------------------------- pages
if page == "🔍 Analyze":
    st.markdown(
        '<div class="hero"><h1>🔍 OpportunityLens AI</h1>'
        "<p>Understand the opportunity before you commit.</p></div>",
        unsafe_allow_html=True,
    )

    choice = st.selectbox("Start from an example or write your own", list(SAMPLES.keys()))
    text = st.text_area(
        "Job / internship description",
        value=SAMPLES[choice],
        height=240,
        key=f"text_{choice}",
        placeholder="Paste the full opportunity description here...",
    )

    if st.button("🔍 Analyze Opportunity", type="primary"):
        if len(text.strip()) < 40:
            st.warning("Please paste a longer description.")
        else:
            try:
                with st.spinner("Retrieving guidelines and analyzing the opportunity..."):
                    res, ctx = analyze_opportunity_with_context(text, LANG)
                st.session_state.update(result=res, context=ctx, analyzed_text=text)
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"Analysis failed: {e}")

    result = st.session_state.get("result")
    if result:
        b = result.score_breakdown
        col = verdict_color(result.score)

        st.markdown('<div class="section-title">📊 Result</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.1, 1.3, 1.3])
        with c1:
            st.markdown(
                f'<div class="card" style="text-align:center">'
                f'<div class="ring-wrap" style="--p:{result.score}; --c:{col}">'
                f'<div class="ring"></div>'
                f'<div class="ring-text"><div class="ring-num">{result.score}</div>'
                f'<div class="ring-sub">out of 100</div></div></div>'
                f'<div class="badge" style="--c:{col}">{esc(result.verdict)}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            fig = go.Figure(
                go.Scatterpolar(
                    r=[getattr(b, k) for k, _ in CATEGORIES] + [getattr(b, CATEGORIES[0][0])],
                    theta=[SHORT[k] for k, _ in CATEGORIES] + [SHORT[CATEGORIES[0][0]]],
                    fill="toself",
                    line=dict(color=PRIMARY, width=2),
                    fillcolor="rgba(99,102,241,0.30)",
                )
            )
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="rgba(148,163,184,.35)"),
                    angularaxis=dict(gridcolor="rgba(148,163,184,.35)"),
                ),
                showlegend=False, height=300, margin=dict(l=70, r=70, t=30, b=30),
                paper_bgcolor="rgba(0,0,0,0)", font=dict(size=11),
            )
            plot(fig)
        with c3:
            bars = ""
            for k, label in CATEGORIES:
                v = getattr(b, k)
                bars += (
                    f'<div class="bar-row"><div class="bar-label"><span>{label} '
                    f'<small style="opacity:.55">({int(WEIGHTS[k] * 100)}%)</small></span><b>{v}</b></div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{v}%; --c:{tone(v)}"></div></div></div>'
                )
            st.markdown(f'<div class="card">{bars}</div>', unsafe_allow_html=True)

        s1, s2, s3 = st.columns(3)
        for box, n, lab, c in [
            (s1, len(result.strengths), "Strengths", GOOD),
            (s2, len(result.risks), "Risks", BAD),
            (s3, len(result.missing_information), "Missing details", WARN),
        ]:
            box.markdown(
                f'<div class="card stat"><b style="color:{c}">{n}</b><span>{lab}</span></div>',
                unsafe_allow_html=True,
            )

        t1, t2, t3, t4 = st.tabs(
            ["🟢 Strengths & risks", "❓ Missing & questions", "📌 Recommendation", "🧠 Evidence (RAG)"]
        )
        with t1:
            a, bcol = st.columns(2)
            a.markdown("#### 🟢 Strengths")
            a.markdown(
                items_html([esc(s) for s in result.strengths], GOOD, "No genuine strengths identified."),
                unsafe_allow_html=True,
            )
            bcol.markdown("#### 🔴 Risks")
            bcol.markdown(
                items_html([esc(s) for s in result.risks], BAD, "No clear risks identified."),
                unsafe_allow_html=True,
            )
        with t2:
            a, bcol = st.columns(2)
            a.markdown("#### ❓ Missing information")
            a.markdown(
                items_html([esc(s) for s in result.missing_information], WARN, "Nothing important is missing."),
                unsafe_allow_html=True,
            )
            bcol.markdown("#### 💬 Questions you should ask")
            bcol.markdown(
                items_html(
                    [f"<b>{i}.</b> {esc(q)}" for i, q in enumerate(result.questions_to_ask, 1)],
                    PRIMARY,
                    "No questions generated.",
                ),
                unsafe_allow_html=True,
            )
        with t3:
            st.markdown(
                f'<div class="item" dir="auto" style="--c:{col}; font-size:1.02rem">{esc(result.recommendation)}</div>',
                unsafe_allow_html=True,
            )
        with t4:
            st.caption("Passages retrieved from the knowledge base with embeddings + FAISS and given to the LLM as context.")
            st.text(st.session_state.get("context", ""))

        st.download_button(
            "⬇️ Download report (Markdown)",
            data=build_report(result, st.session_state.get("analyzed_text", text)),
            file_name="opportunity_report.md",
            mime="text/markdown",
        )

elif page == "🎯 CV Match":
    render_cv_page(LANG)

elif page == "📊 Evaluation":
    st.markdown(
        '<div class="hero"><h1>📊 Evaluation</h1>'
        "<p>How well do the verdicts match labelled test cases?</p></div>",
        unsafe_allow_html=True,
    )

    def show_eval(path, source):
        if not os.path.exists(path):
            st.info(f"No results yet. Run evaluate.py to create {path}.")
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        m1, m2, m3 = st.columns(3)
        m1.metric("Accuracy", f"{data['accuracy']:.0%}")
        recall = data.get("high_risk_recall")
        m2.metric("High Risk caught", f"{recall:.0%}" if recall is not None else "n/a")
        m3.metric("Cases answered", f"{data['answered']}/{data['n']}")

        df = pd.DataFrame(data["rows"])
        ok = df[df["predicted"].notna()]

        st.markdown('<div class="section-title">Confusion matrix</div>', unsafe_allow_html=True)
        cm = pd.crosstab(ok["expected"], ok["predicted"]).reindex(
            index=VERDICT_ORDER, columns=VERDICT_ORDER, fill_value=0
        )
        st.caption("Rows = expected verdict, columns = predicted verdict.")
        st.dataframe(cm, use_container_width=True)

        st.markdown('<div class="section-title">All cases</div>', unsafe_allow_html=True)
        st.dataframe(
            df[["id", "expected", "predicted", "score", "correct"]],
            use_container_width=True,
            hide_index=True,
        )

        wrong = df[~df["correct"]]
        if len(wrong):
            st.markdown('<div class="section-title">Mistakes</div>', unsafe_allow_html=True)
            st.dataframe(
                wrong[["id", "expected", "predicted", "score", "error"]],
                use_container_width=True,
                hide_index=True,
            )
        st.caption(f"Generated by evaluate.py from {source}. Small test set, so treat it as a sanity check, not a benchmark.")

    tab_main, tab_hold = st.tabs(["Main set", "Held-out set"])
    with tab_main:
        show_eval("eval_results.json", "eval_cases.json")
    with tab_hold:
        st.caption("Written after the prompt and scoring were fixed, so it was not used for tuning.")
        show_eval("eval_holdout_results.json", "eval_holdout.json")

elif page == "🧠 How it works":
    st.markdown(
        '<div class="hero"><h1>🧠 How it works</h1><p>From a pasted description to a decision report.</p></div>',
        unsafe_allow_html=True,
    )
    st.graphviz_chart(
        """
digraph G {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#6366F1", fontcolor="white", color="#6366F1", fontname="Helvetica", margin="0.2,0.12"];
  edge [color="#94A3B8"];
  A [label="Opportunity\\ntext"];
  B [label="RAG retrieval\\n(embeddings + FAISS)"];
  K [label="Knowledge base\\n(guidelines, red flags)", fillcolor="#0EA5E9", color="#0EA5E9"];
  C [label="LLM chain\\n(Gemini / Groq backup)"];
  D [label="Pydantic\\noutput parser"];
  E [label="Python scoring\\n(fixed weights)", fillcolor="#10B981", color="#10B981"];
  R [label="Rule-based\\nred-flag check", fillcolor="#EF4444", color="#EF4444"];
  F [label="Dashboard\\n+ report"];
  A -> B; K -> B; B -> C; A -> C; C -> D; D -> E; A -> R; R -> E; E -> F;
}
"""
    )
    steps = [
        ("1 · Retrieve", "The description is embedded and matched against a curated knowledge base of internship guidelines, red flags and evaluation criteria."),
        ("2 · Analyze", "A prompt-engineered LLM chain rates seven categories using only the description and the retrieved evidence."),
        ("3 · Parse", "A Pydantic parser forces the answer into a strict schema, so the output is always structured."),
        ("4 · Score", "Python (not the LLM) calculates the final score with fixed weights, which keeps the math reproducible. Rule-based red flags cap the score."),
        ("5 · Protect", "Retries, a backup model and a result cache keep the app working when a model is overloaded."),
    ]
    cols = st.columns(len(steps))
    for c, (t, d) in zip(cols, steps):
        c.markdown(f'<div class="card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚖️ Scoring weights</div>', unsafe_allow_html=True)
    rows = "".join(
        f'<div class="bar-row"><div class="bar-label"><span>{label}</span><b>{int(WEIGHTS[k] * 100)}%</b></div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{WEIGHTS[k] * 100 * 4}%; --c:{PRIMARY}"></div></div></div>'
        for k, label in CATEGORIES
    )
    st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)
    st.markdown(
        f"**Verdicts:** <span style='color:{GOOD}'>80–100 Recommended</span> · "
        f"<span style='color:{WARN}'>40–79 Consider with Caution</span> · "
        f"<span style='color:{BAD}'>0–39 High Risk</span>",
        unsafe_allow_html=True,
    )

else:
    st.markdown(
        '<div class="hero"><h1>ℹ️ About</h1><p>Why OpportunityLens exists.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
**The problem.** Students and fresh graduates see many internships, jobs and programs, but descriptions are often vague or misleading.

**The solution.** OpportunityLens turns a description into a decision report: what you get, what is risky, what is missing, and what to ask before applying. A CV match tool then shows which skills you already have, which to build, and ranks several opportunities by how well your CV fits them.

**Built with.** Streamlit · LangChain · Gemini · FAISS · Hugging Face sentence-transformers · Pydantic

**Limitations.**
- The knowledge base is small and hand-written.
- The app reads only the text you paste; it cannot verify that a company is real.
- CV ranking measures skill fit only, not the quality or safety of the opportunity. Use it together with the opportunity score.
- CV upload reads text-based PDFs and DOCX files; scanned PDFs and some Arabic PDFs may need to be pasted instead.
- Report content can be switched to Arabic, but the interface labels stay in English.
- AI output can be wrong. Treat the report as decision support, not a guarantee.
"""
    )