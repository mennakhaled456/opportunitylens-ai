"""CV match: compare a CV / skills list against an opportunity description."""
from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .chains import create_llm
from .llm_calls import generate_structured

REQUIREMENTS_WEIGHT = 0.6
BACKGROUND_WEIGHT = 0.4


class CVMatch(BaseModel):
    requirements_coverage: int = Field(
        ge=0, le=100,
        description="Share of the opportunity's STATED requirements or prerequisites that the CV meets. 100 if none are stated.",
    )
    background_relevance: int = Field(
        ge=0, le=100,
        description="How relevant the CV's existing skills and projects are to the topics and work of the opportunity",
    )
    match_score: int = Field(
        ge=0, le=100,
        description="Overall fit from 0 to 100 (recomputed by the application)",
    )
    summary: str = Field(description="Two sentence summary of the fit")
    matching_skills: List[str] = Field(description="Skills in the CV that the opportunity needs or uses")
    skill_gaps: List[str] = Field(description="Requirements or topics from the opportunity that the CV does not show")
    improvement_tips: List[str] = Field(description="Practical steps to close the gaps before applying")


def analyze_cv_match(opportunity_text: str, cv_text: str, language: str = "English") -> CVMatch:
    client = create_llm()
    parser = PydanticOutputParser(pydantic_object=CVMatch)

    prompt = f"""
You are OpportunityLens AI. Compare the applicant's CV with the opportunity.

RULES:
- Use ONLY information written in the CV and in the opportunity.
- Do not invent or assume skills. If the CV does not show a skill, list it as a gap.
- requirements_coverage (0-100): the share of the STATED requirements or prerequisites
  (for example "basic Python", "2 years of experience") that the CV meets.
  Topics that the program will TEACH are not requirements.
  If the opportunity says no experience is required, or states no requirements, use 100.
- background_relevance (0-100): how relevant the CV's existing skills, projects and
  courses are to the topics and work of the opportunity.
- match_score: set it to your best overall estimate. The application recomputes it.
- skill_gaps may include topics the program teaches; they are things to learn, not penalties.
- Keep every list short: at most 6 items, each under 20 words.
- Write ALL text fields in {language}. Keep JSON keys and numbers unchanged.
- Return ONLY valid JSON. No Markdown and no text outside the JSON.

OPPORTUNITY:
{opportunity_text[:6000]}

CV:
{cv_text[:6000]}

Return JSON matching this structure:

{parser.get_format_instructions()}
"""
    result = generate_structured(client, prompt, parser, opportunity_text)

    # Python computes the final number, so the math is reproducible.
    result.match_score = max(
        0,
        min(
            100,
            round(
                REQUIREMENTS_WEIGHT * result.requirements_coverage
                + BACKGROUND_WEIGHT * result.background_relevance
            ),
        ),
    )
    return result