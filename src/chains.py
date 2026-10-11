import os

from dotenv import load_dotenv
from google import genai
from langchain_core.output_parsers import PydanticOutputParser

from .llm_calls import generate_structured
from .schemas import OpportunityAnalysis


load_dotenv()


def create_llm():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from .env"
        )

    return genai.Client(api_key=api_key)


def create_analysis_chain():

    client = create_llm()

    parser = PydanticOutputParser(
        pydantic_object=OpportunityAnalysis
    )

    def analyze(inputs):

        language = inputs.get("language", "English")
        cache_key = (
            inputs["opportunity"]
            if language == "English"
            else inputs["opportunity"] + f"\n[lang:{language}]"
        )

        prompt = f"""
You are OpportunityLens AI, an AI-powered career opportunity
evaluation system.

Your task is to carefully evaluate the following internship or
career opportunity using the retrieved knowledge base.

You must evaluate the opportunity using these seven categories
and EXACT weights:

1. Career Relevance — 20%
2. Learning Potential — 20%
3. Mentorship — 15%
4. Company Credibility — 15%
5. Compensation — 10%
6. Workload — 10%
7. Transparency — 10%

Each category score must be an integer from 0 to 100.

SCORING GUIDELINES:

Career Relevance:
Evaluate how relevant the opportunity is to the career skills
and experience described in the opportunity.

Learning Potential:
Evaluate opportunities for practical learning, skill development,
real projects, technologies, and professional growth.

Mentorship:
Evaluate the availability and clarity of mentorship or guidance.

Company Credibility:
Evaluate only credibility signals explicitly present in the
opportunity description or retrieved knowledge.

Compensation:
Evaluate compensation strictly based on available information.

If compensation is not mentioned, do not assume it is paid.
Treat missing compensation as missing information and reduce the
score appropriately.

Workload:
Evaluate whether the expected workload is reasonable and clearly
explained.

Transparency:
Evaluate how clearly the opportunity communicates important
details such as responsibilities, compensation, schedule,
requirements, mentorship, and application process.

OVERALL SCORE:

Calculate the overall score using EXACTLY:

Career Relevance × 0.20
+ Learning Potential × 0.20
+ Mentorship × 0.15
+ Company Credibility × 0.15
+ Compensation × 0.10
+ Workload × 0.10
+ Transparency × 0.10

The final score must be an integer from 0 to 100.

VERDICT RULES:

80–100 = Recommended

40–79 = Consider with Caution

0–39 = High Risk

IMPORTANT RULES:

- Do not invent facts.
- Only use information from the opportunity or retrieved knowledge.
- If information is not mentioned, identify it as missing.
- A red flag does NOT automatically mean the opportunity is a scam.
- Separate confirmed problems from missing information.
- Do not make assumptions about the company.
- Give practical and specific reasoning.
- Make sure the overall score follows the weighted formula.
- Write ALL text fields (strengths, risks, missing_information, questions_to_ask, recommendation) in {language}. Keep JSON keys and numbers unchanged.
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not add text outside the JSON.
- Only list a strength if it is a genuine benefit to the applicant. Do not list basic facts (such as a job title or remote work) as strengths. If the opportunity shows clear scam indicators, return an empty strengths list.


RETRIEVED KNOWLEDGE:
{inputs["context"]}

OPPORTUNITY:
{inputs["opportunity"]}

Return JSON matching this structure:

{parser.get_format_instructions()}
"""

        # Cache -> Gemini (with retries) -> backup model
        return generate_structured(client, prompt, parser, cache_key)

    return analyze, parser