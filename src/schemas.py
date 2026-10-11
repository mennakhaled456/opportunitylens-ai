from pydantic import BaseModel, Field
from typing import List


class ScoreBreakdown(BaseModel):
    career_relevance: int = Field(
        ge=0,
        le=100,
        description="How relevant the opportunity is to the applicant's career goals"
    )

    learning_potential: int = Field(
        ge=0,
        le=100,
        description="How much the opportunity can contribute to learning and skill development"
    )

    mentorship: int = Field(
        ge=0,
        le=100,
        description="Quality and clarity of mentorship provided"
    )

    company_credibility: int = Field(
        ge=0,
        le=100,
        description="Credibility signals provided by the opportunity description"
    )

    compensation: int = Field(
        ge=0,
        le=100,
        description="Quality and transparency of compensation"
    )

    workload: int = Field(
        ge=0,
        le=100,
        description="Reasonableness and clarity of the expected workload"
    )

    transparency: int = Field(
        ge=0,
        le=100,
        description="How clearly the opportunity communicates important details"
    )


class OpportunityAnalysis(BaseModel):

    score: int = Field(
        ge=0,
        le=100,
        description="Overall weighted opportunity score from 0 to 100"
    )

    verdict: str = Field(
        description="Overall verdict: Recommended, Consider with Caution, or High Risk"
    )

    score_breakdown: ScoreBreakdown = Field(
        description="Weighted evaluation of the opportunity across seven categories"
    )

    strengths: List[str] = Field(
        description="Positive aspects of the opportunity"
    )

    risks: List[str] = Field(
        description="Potential risks or red flags"
    )

    missing_information: List[str] = Field(
        description="Important information missing from the opportunity description"
    )

    questions_to_ask: List[str] = Field(
        description="Questions the applicant should ask before accepting"
    )

    recommendation: str = Field(
        description="Final recommendation explaining whether the applicant should consider the opportunity"
    )