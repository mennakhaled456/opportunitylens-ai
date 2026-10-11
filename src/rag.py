import os

from dotenv import load_dotenv

load_dotenv()

os.environ["HF_HOME"] = os.getenv(
    "HF_HOME",
    r"E:\huggingface_cache"
)

os.environ["HF_HUB_CACHE"] = os.getenv(
    "HF_HUB_CACHE",
    r"E:\huggingface_cache\hub"
)


from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


KNOWLEDGE_BASE_PATH = Path("data/knowledge_base")


def load_knowledge_base():
    documents = []

    print(f"Looking for knowledge base at: {KNOWLEDGE_BASE_PATH.resolve()}")

    files = list(KNOWLEDGE_BASE_PATH.glob("*.txt"))

    print(f"Found {len(files)} text files.")

    for file_path in files:
        text = file_path.read_text(encoding="utf-8").strip()

        print(f"  {file_path.name}: {len(text)} characters")

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": file_path.name}
                )
            )

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks.")

    return chunks


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_vector_store():
    documents = load_knowledge_base()

    if not documents:
        raise ValueError(
            "No non-empty .txt files were found in "
            "data/knowledge_base."
        )

    chunks = split_documents(documents)

    if not chunks:
        raise ValueError(
            "Documents were loaded, but no chunks were created."
        )

    embeddings = create_embeddings()

    # Check that embeddings are actually being produced
    test_embedding = embeddings.embed_query("test query")

    print(f"Embedding size: {len(test_embedding)}")

    if not test_embedding:
        raise ValueError("Embedding model returned an empty vector.")

    vector_store = FAISS.from_documents(
        chunks,
        embeddings
    )

    return vector_store


def retrieve_context(vector_store, query, k=4):
    documents = vector_store.similarity_search(
        query,
        k=k
    )

    return [
        {
            "content": document.page_content,
            "source": document.metadata.get(
                "source",
                "Unknown"
            )
        }
        for document in documents
    ]


def get_context_text(vector_store, query, k=4):
    results = retrieve_context(
        vector_store,
        query,
        k
    )

    if not results:
        return "No relevant information found."

    return "\n\n---\n\n".join(
        f"Source: {result['source']}\n{result['content']}"
        for result in results
    )