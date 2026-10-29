from langchain_core.tools import tool

from knowledge.retriever import search_documents


@tool
def search_knowledge_base(query: str) -> dict:
    """Search internal support documents, FAQs, and policies.

    Use this tool to find information about product behavior,
    troubleshooting, company policies, and common support questions.

    Returns relevant excerpts with their source filenames.
    """

    results = search_documents(query=query, top_k=4)

    if not results:
        return {
            "ok": True,
            "results": [],
            "message": (
                "No relevant information was found in the knowledge base."
            ),
        }

    return {
        "ok": True,
        "results": [
            {
                "source": result["source"],
                "chunk_index": result["chunk_index"],
                "text": result["text"],
                "score": result["score"],
            }
            for result in results
        ],
    }