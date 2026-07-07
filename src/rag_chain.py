import chromadb
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL, CHROMA_DB_PATH, call_llm
from src.rbac import get_allowed_collections
from src.guardrails import contains_pii, is_out_of_scope


def answer_query(query: str, role: str) -> dict:
    if contains_pii(query):
        return {
            "answer": "I can't process requests containing personal information.",
            "blocked": True,
            "reason": "pii",
        }
    if is_out_of_scope(query):
        return {
            "answer": "That's outside what I can help with. Please ask about company information.",
            "blocked": True,
            "reason": "out_of_scope",
        }

    allowed_collections = get_allowed_collections(role)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(query).tolist()

    all_chunks = []
    sources = []
    for coll_name in allowed_collections:
        try:
            collection = client.get_collection(name=coll_name)
        except Exception:
            continue
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "distances"],
        )
        if results["documents"] and results["documents"][0]:
            for i, dist in enumerate(results["distances"][0]):
                if dist < 1.0:
                    all_chunks.append(results["documents"][0][i])
            if any(d < 1.0 for d in results["distances"][0]):
                sources.append(coll_name)

    if not all_chunks:
        return {
            "answer": "I don't have access to information that would answer that.",
            "blocked": False,
            "reason": "no_access",
        }

    context = "\n\n".join(all_chunks)
    system_prompt = (
        "You are a helpful company assistant. Answer based only on the provided context. "
        "If the context doesn't contain the answer, say you don't know."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
    llm_response = call_llm(user_prompt, system_prompt=system_prompt)
    return {
        "answer": llm_response,
        "blocked": False,
        "sources": sources,
        "reason": None,
    }
