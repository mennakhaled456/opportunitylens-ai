from src.rag import build_vector_store, get_context_text


print("Building knowledge base...")

vector_store = build_vector_store()

print("Knowledge base successfully created!")

print("\nTesting retrieval...\n")

query = """
What are the warning signs that an internship
may require further investigation?
"""

context = get_context_text(
    vector_store,
    query
)

print(context)