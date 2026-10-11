from src.pipeline import analyze_opportunity


opportunity = """
We are looking for a Junior Machine Learning Intern.

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

Compensation is not mentioned in the description.
"""


print("Analyzing opportunity...")
print("-" * 50)

result = analyze_opportunity(opportunity)

print("\nRESULT")
print("=" * 50)

print(f"\nOverall Score: {result.score}/100")
print(f"Verdict: {result.verdict}")

print("\nScore Breakdown:")
print(
    f"- Career Relevance: "
    f"{result.score_breakdown.career_relevance}/100"
)
print(
    f"- Learning Potential: "
    f"{result.score_breakdown.learning_potential}/100"
)
print(
    f"- Mentorship: "
    f"{result.score_breakdown.mentorship}/100"
)
print(
    f"- Company Credibility: "
    f"{result.score_breakdown.company_credibility}/100"
)
print(
    f"- Compensation: "
    f"{result.score_breakdown.compensation}/100"
)
print(
    f"- Workload: "
    f"{result.score_breakdown.workload}/100"
)
print(
    f"- Transparency: "
    f"{result.score_breakdown.transparency}/100"
)

print("\nStrengths:")
for item in result.strengths:
    print(f"- {item}")

print("\nRisks:")
for item in result.risks:
    print(f"- {item}")

print("\nMissing Information:")
for item in result.missing_information:
    print(f"- {item}")

print("\nQuestions to Ask:")
for item in result.questions_to_ask:
    print(f"- {item}")

print("\nRecommendation:")
print(result.recommendation)