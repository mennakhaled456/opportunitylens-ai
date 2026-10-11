🔍 OpportunityLens AI

Understand an internship or job opportunity before you commit.

Students and fresh graduates see many internships and programs, but the descriptions are often vague or misleading. OpportunityLens AI turns a pasted description into a decision report: a score, a verdict, strengths, risks, missing information and questions to ask before applying. You can also upload your CV to see how well you fit, and to rank several opportunities against it.

Built as a course project for the Tips Hindawi LLM & AI internship program.

Show Image

Features
Opportunity analysis: a 7-category score (0 to 100) and a verdict: Recommended, Consider with Caution or High Risk.
RAG with evidence: the description is matched against a knowledge base of internship guidelines and red flags (sentence-transformer embeddings + FAISS). The retrieved passages are shown in the app.
Deterministic scoring: the LLM only rates each category. Python computes the final score with fixed weights, so the math is reproducible.
Rule-based red flags: requests for fees or deposits, ID or bank details, cheque schemes and "guaranteed job / no interview" claims cap the score, whatever the LLM says.
CV match and ranking: upload a PDF, DOCX or TXT CV and rank up to 5 opportunities by fit (60% stated requirements, 40% background relevance), with skill gaps and tips.
English and Arabic reports: strengths, risks, questions and recommendations can be generated in either language.
Reliability: result cache, Gemini with a Groq backup model, strict Pydantic output parsing and temperature 0.
Evaluation page: labelled test cases with accuracy, High Risk recall and a confusion matrix.
Screenshots
Arabic report	CV ranking
Show Image	Show Image
Evaluation	Architecture
Show Image	Show Image
How it works
Opportunity text
      │
      ├──► Rule-based red-flag check (regex) ─────────────┐
      │                                                    ▼
      └──► RAG retrieval (embeddings + FAISS)  ──► LLM chain ──► Pydantic parser ──► Python scoring ──► Dashboard + report
           over the knowledge base                (Gemini,                            (fixed weights,
                                                   Groq backup)                        red-flag cap)
Retrieve: the description is embedded and matched against the knowledge base.
Analyze: a prompt-engineered LLM chain rates seven categories using only the description and the retrieved evidence.
Parse: a Pydantic parser forces the answer into a strict schema.
Score: Python calculates the overall score and verdict. Hard red flags cap the score at 35.
Protect: a cache, retries and a backup model keep the app working when a model is overloaded or out of quota.
Scoring
Category	Weight
Career relevance	20%
Learning potential	20%
Mentorship	15%
Company credibility	15%
Compensation	10%
Workload	10%
Transparency	10%

Verdicts: 80 to 100 Recommended, 40 to 79 Consider with Caution, 0 to 39 High Risk.

Evaluation
Set	Cases	Accuracy	High Risk caught
Main set (thresholds were calibrated on it)	12	100% (12/12)	100%
Held-out set (written after the thresholds were fixed)	11	100% (11/11)	100%

How the numbers came about:

The first run, with verdict thresholds of 90 and 70, scored 58% (7/12). The scores themselves were sensible, but every "caution" case was labelled High Risk, so the thresholds were too strict. I recalibrated them to 80 and 40.
Because I tuned the thresholds on the first 12 cases, a perfect score there proves little. I wrote a held-out set afterwards. Its first 8 cases scored 88% (7/8) on their first run. I then added 3 harder cases (scams with no fee or ID request, and a legitimate post that mentions no fee) to test the red-flag rules.
The final numbers above come from a clean run after setting the model temperature to 0 and emptying the cache.
Most cases were answered by Gemini. Three (risk_03, hold_nofee_02, hold_scam_nofee_01) were answered by the Groq backup model because the Gemini quota ran out. All three still landed in the expected verdict.
Both sets are small. Treat the results as a sanity check, not a benchmark.

Results are stored in eval_results.json and eval_holdout_results.json and shown on the app's Evaluation page. eval_results_v1.json keeps the result from before the recalibration.

Setup

Requires Python 3.10 or newer.

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Copy .env.example to .env and add your keys:

GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

Run the app:

python -m streamlit run app.py

Run the evaluation (about 30 to 60 minutes if the models are slow):

python evaluate.py --fresh
python evaluate.py --cases eval_holdout.json --out eval_holdout_results.json --fresh
Project structure
app.py                    Streamlit app (Analyze, CV Match, Evaluation, How it works, About)
evaluate.py               runs labelled test cases and saves accuracy results
eval_cases.json           main test set (12 cases)
eval_holdout.json         held-out test set (11 cases)
eval_results.json         results for the main set
eval_holdout_results.json results for the held-out set
eval_results_v1.json      main-set results before the threshold recalibration
rescore.py                recomputes verdicts from saved scores without calling the API
test_flags.py             tests for the red-flag rules
requirements.txt
.env.example
data/knowledge_base/      guidelines and red-flag documents used for retrieval
src/rag.py                load, split, embed, FAISS retriever
src/chains.py             analysis prompt and chain
src/llm_calls.py          cache, Gemini, Groq fallback, temperature 0
src/schemas.py            Pydantic models for structured output
src/scoring.py            weights, verdicts, red-flag cap
src/redflags.py           rule-based red-flag detection
src/pipeline.py           analyze_opportunity_with_context()
src/cv_match.py           CV versus opportunity comparison
src/cv_reader.py          text extraction from PDF, DOCX and TXT
src/cv_page.py            CV Match page
Limitations
The knowledge base is small and hand-written.
The app reads only the text you paste. It cannot verify that a company is real.
The embedding model is English-only, so Arabic job descriptions retrieve less well than English ones.
The red-flag rules match English text only.
CV ranking measures skill fit, not the quality or safety of an opportunity. Use it together with the opportunity score.
Scanned PDFs have no text layer, and some Arabic PDFs extract with reversed letters. Paste the CV text instead.
Report content can be generated in Arabic, but the interface labels stay in English.
Scores can vary slightly between models (Gemini and the Groq backup).
AI output can be wrong. This is decision support, not a guarantee. Always verify a company, and never pay fees or share ID or bank details before an official contract.
Privacy

The CV file is read in memory and is not saved by the app. Its text is sent to the AI model to make the comparison, so remove your phone number, address and ID before using it. The result cache (cache.json) stores model answers on your machine and is excluded from Git.

Built with

Streamlit · LangChain · Google Gemini · Groq · FAISS · Hugging Face sentence-transformers · Pydantic · Plotly