"""
faq_rag.py
----------
RAG retriever for the EmerClinic FAQ agent.
Loads all .md files from rag_docs/, chunks them, embeds with
OpenAI text-embedding-3-small, and persists to ChromaDB.

On first run  → builds + persists the vector store
On later runs → loads from disk (no re-embedding)

Public API (unchanged from previous version):
    retrieve_faq(query, k=3)          -> list[dict]   # id, title, content, score, source
    format_retrieved_context(docs)    -> str
    rebuild_vectorstore()             -> None          # call after editing rag_docs/
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DOCS_DIR        = Path(__file__).parent / "rag_docs"
CHROMA_DIR      = Path(__file__).parent.parent / "chroma_db"
COLLECTION      = "emerclinic_faq"
EMBED_MODEL     = "text-embedding-3-small"
DEFAULT_K       = 3
SCORE_THRESHOLD = 0.25


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBED_MODEL)


def _load_raw_documents() -> list[Document]:
    """Read every .md file in rag_docs/ into a LangChain Document."""
    docs = []
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        docs.append(Document(
            page_content=text,
            metadata={
                "source": md_file.name,
                "topic":  md_file.stem.replace("_", " ").title(),
            },
        ))
    if not docs:
        raise FileNotFoundError(f"No .md files found in {DOCS_DIR}")
    return docs


def _chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    return splitter.split_documents(docs)


def _build_vectorstore() -> Chroma:
    print("[faq_rag] Building vector store — runs once, then cached on disk.")
    chunks = _chunk_documents(_load_raw_documents())
    store = Chroma.from_documents(
        documents=chunks,
        embedding=_get_embeddings(),
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_DIR),
    )
    print(f"[faq_rag] Indexed {len(chunks)} chunks from {len(_load_raw_documents())} docs.")
    return store


def _load_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=_get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def _store_exists() -> bool:
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


# ---------------------------------------------------------------------------
# Module-level init
# ---------------------------------------------------------------------------

_vectorstore: Chroma = _load_vectorstore() if _store_exists() else _build_vectorstore()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve_faq(query: str, k: int = DEFAULT_K) -> list[dict]:
    """
    Return the top-k most relevant FAQ chunks for the given query.
    Each result is a dict with keys: title, content, source, score.
    """
    docs_and_scores: list[tuple[Document, float]] = _vectorstore.similarity_search_with_score(query, k=k)

    return [
        {
            "title":   doc.metadata.get("topic", ""),
            "content": doc.page_content.strip(),
            "source":  doc.metadata.get("source", ""),
            "score":   round(float(score), 4),
        }
        for doc, score in docs_and_scores
    ]



def format_retrieved_context(docs: list[dict]) -> str:
    """Format retrieved docs into a context block for the LLM system prompt."""
    if not docs:
        return ""
    sections = []
    for doc in docs:
        header = f"### {doc['title']}  (source: {doc['source']})"
        sections.append(f"{header}\n{doc['content']}")
    return "\n\n".join(sections)


def rebuild_vectorstore() -> None:
    """
    Wipe and rebuild the vector store from scratch.
    Run this after adding or editing files in rag_docs/.
    """
    global _vectorstore
    if _store_exists():
        import shutil
        shutil.rmtree(CHROMA_DIR)
        print("[faq_rag] Cleared existing vector store.")
    _vectorstore = _build_vectorstore()
    print("[faq_rag] Rebuild complete.")


# ---------------------------------------------------------------------------
# Quick smoke test — python faq_rag.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_queries = [
        "What is included in the Premium plan?",
        "How do I export patient data as CSV?",
        "My payment failed, what happens next?",
        "How do I set up Google Calendar sync?",
        "Is EmerClinic HIPAA compliant?",
        "How do I add a new provider?",
        "What roles can I assign to staff?",
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        results = retrieve_faq(q)
        if results:
            print(f"  → {len(results)} chunk(s) — top: [{results[0]['source']}]")
            print(f"  → {results[0]['content'][:120]}...")
        else:
            print("  → No relevant chunks found")
