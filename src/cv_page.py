"""CV Match page: upload a CV, compare it with one or several opportunities, rank them."""
import html
import re

import streamlit as st

from .cv_match import analyze_cv_match
from .cv_reader import extract_cv_text

PRIMARY, GOOD, WARN, BAD = "#6366F1", "#10B981", "#F59E0B", "#EF4444"
MAX_OPPS = 5


def _esc(value) -> str:
    return html.escape(str(value))


def _color(score: int) -> str:
    return GOOD if score >= 70 else WARN if score >= 40 else BAD


def _items(items, color, empty):
    if not items:
        return f'<div class="item" style="--c:{color}; opacity:.75">{empty}</div>'
    return "".join(
        f'<div class="item" dir="auto" style="--c:{color}">{_esc(i)}</div>' for i in items
    )


def _title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:70]
    return "Opportunity"


def _split(raw: str):
    parts = re.split(r"\n\s*-{3,}\s*\n", "\n" + raw + "\n")
    return [p.strip() for p in parts if len(p.strip()) >= 40]


def render_cv_page(lang: str):
    st.markdown(
        '<div class="hero"><h1>🎯 CV Match</h1>'
        "<p>Upload your CV and see which opportunities fit you best.</p></div>",
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------- step 1: CV
    st.markdown("#### 1 · Your CV")
    uploaded = st.file_uploader("Upload your CV (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])
    if uploaded is not None:
        sig = f"{uploaded.name}-{uploaded.size}"
        if st.session_state.get("cv_sig") != sig:
            try:
                extracted = extract_cv_text(uploaded)
                st.session_state["cv_sig"] = sig
                st.session_state["cv_text"] = extracted
                if len(extracted) < 40:
                    st.warning("Almost no text was found. A scanned PDF has no text layer, so paste your CV below instead.")
            except Exception as e:
                st.error(f"Could not read the file: {e}")

    cv_text = st.text_area(
        "CV text (you can edit it, or paste it here instead of uploading)",
        height=200,
        key="cv_text",
        placeholder="Your skills, projects, courses and experience...",
    )
    st.caption(
        "🔒 The file is read in memory and not saved by the app. Its text is sent to the AI model "
        "to make the comparison, so remove your phone number, address and ID first."
    )

    # ---------------------------------------------------- step 2: opportunities
    st.markdown("#### 2 · Opportunities")
    opps_raw = st.text_area(
        "Opportunity descriptions",
        value=st.session_state.get("analyzed_text", ""),
        height=200,
        key="cv_opps",
        placeholder="Paste one opportunity, or several separated by a line containing only ---",
    )
    st.caption(f"To rank several, paste them one after another with a line containing only `---` between them (up to {MAX_OPPS}).")

    if st.button("🎯 Match & rank", type="primary"):
        opps = _split(opps_raw)
        if len(cv_text.strip()) < 40:
            st.warning("Please upload or paste your CV first.")
        elif not opps:
            st.warning("Please paste at least one opportunity (a few lines).")
        else:
            if len(opps) > MAX_OPPS:
                st.info(f"Only the first {MAX_OPPS} opportunities are compared.")
            opps = opps[:MAX_OPPS]
            results = []
            progress = st.progress(0.0)
            for i, opp in enumerate(opps, 1):
                try:
                    match = analyze_cv_match(opp, cv_text, lang)
                    results.append({"title": _title(opp), "match": match, "error": None})
                except Exception as e:
                    results.append({"title": _title(opp), "match": None, "error": str(e)[:200]})
                progress.progress(i / len(opps))
            progress.empty()
            results.sort(key=lambda r: r["match"].match_score if r["match"] else -1, reverse=True)
            st.session_state["cv_ranking"] = results

    # ------------------------------------------------------------- results
    results = st.session_state.get("cv_ranking")
    if not results:
        return

    if len(results) > 1:
        st.markdown('<div class="section-title">🏆 Ranking by CV fit</div>', unsafe_allow_html=True)
        rows = ""
        for rank, r in enumerate(results, 1):
            title = _esc(r["title"])
            if r["match"]:
                s = r["match"].match_score
                rows += (
                    f'<div class="bar-row"><div class="bar-label" dir="auto"><span>{rank}. {title}</span><b>{s}</b></div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{s}%; --c:{_color(s)}"></div></div></div>'
                )
            else:
                rows += f'<div class="bar-row"><div class="bar-label"><span>{rank}. {title}</span><b>failed</b></div></div>'
        st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)

    for rank, r in enumerate(results, 1):
        m = r["match"]
        if m is None:
            st.error(f"#{rank} {r['title']}: {r['error']}")
            continue
        col = _color(m.match_score)
        with st.expander(f"#{rank} · {r['title']} — {m.match_score}/100", expanded=(rank == 1)):
            c1, c2 = st.columns([1, 2])
            c1.markdown(
                f'<div class="card" style="text-align:center">'
                f'<div class="ring-wrap" style="--p:{m.match_score}; --c:{col}">'
                f'<div class="ring"></div>'
                f'<div class="ring-text"><div class="ring-num">{m.match_score}</div>'
                f'<div class="ring-sub">match / 100</div></div></div></div>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                f'<div class="item" dir="auto" style="--c:{col}; font-size:1.02rem">{_esc(m.summary)}</div>'
                f'<div class="card">'
                f'<div class="bar-row"><div class="bar-label"><span>Meets stated requirements (60%)</span><b>{m.requirements_coverage}</b></div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{m.requirements_coverage}%; --c:{_color(m.requirements_coverage)}"></div></div></div>'
                f'<div class="bar-row"><div class="bar-label"><span>Background relevance (40%)</span><b>{m.background_relevance}</b></div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{m.background_relevance}%; --c:{_color(m.background_relevance)}"></div></div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            g1, g2 = st.columns(2)
            g1.markdown("**✅ Skills you already have**")
            g1.markdown(_items(m.matching_skills, GOOD, "No matching skills found."), unsafe_allow_html=True)
            g2.markdown("**⚠️ Skill gaps**")
            g2.markdown(_items(m.skill_gaps, BAD, "No gaps found."), unsafe_allow_html=True)
            st.markdown("**🛠️ How to close the gaps**")
            st.markdown(_items(m.improvement_tips, PRIMARY, "No tips generated."), unsafe_allow_html=True)