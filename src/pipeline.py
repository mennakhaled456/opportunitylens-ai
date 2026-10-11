from functools import lru_cache

from .rag import build_vector_store, get_context_text
from .chains import create_analysis_chain
from .scoring import apply_deterministic_score


@lru_cache(maxsize=1)
def get_vector_store():
    """Build the FAISS store once and reuse it."""
    return build_vector_store()


def analyze_opportunity_with_context(opportunity_text: str, language: str = "English"):
    """Returns (result, context) so the UI can show what RAG retrieved."""

    vector_store = get_vector_store()

    context = get_context_text(vector_store, opportunity_text, k=4)

    chain, parser = create_analysis_chain()

    result = chain(
        {"context": context, "opportunity": opportunity_text, "language": language}
    )

    # Python calculates the final score and verdict (not the LLM)
    result = apply_deterministic_score(result, opportunity_text)

    return result, context


def analyze_opportunity(opportunity_text: str):
    """Same as before: returns only the result (used by evaluate.py and test_pipeline.py)."""
    result, _ = analyze_opportunity_with_context(opportunity_text)
    return result