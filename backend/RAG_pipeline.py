# backend/pipeline.py

from typing import Dict, List
import config
import re
from backend.embeddings import embed_texts
from backend import retrieval
from backend import llm



# =========================
# 1. Build context string
# =========================
def build_context_from_docs(docs: List[Dict], per_doc_chars: int = 1000) -> str:
    """
    Build a single context string from retrieved docs.
    Keeps up to per_doc_chars characters but extends to finish the current sentence
    (so we don't cut off useful sentences mid-way).
    Returns a string like: "[source:doc_1] snippet...\n\n[source:doc_2] snippet..."
    """
    parts = []
    for d in docs:
        src = d.get("source") or f"doc_{d.get('_id')}"
        text = d.get("text", "") or ""
        # normalize whitespace
        snippet = re.sub(r'\s+', ' ', text).strip()
        if len(snippet) <= per_doc_chars:
            text_snippet = snippet
        else:
            head = snippet[:per_doc_chars]
            tail = snippet[per_doc_chars:per_doc_chars + 1000]  # lookahead to complete sentence
            m = re.search(r'([.!?])', tail)
            if m:
                end_idx = per_doc_chars + m.end()
                text_snippet = snippet[:end_idx].strip()
            else:
                text_snippet = head.strip()
        parts.append(f"[source:{src}] {text_snippet}")
    return "\n\n".join(parts)

# =========================
# 2. Full RAG pipeline
# =========================
def run_rag_pipeline(question: str, top_k: int = 3, debug: bool = False) -> Dict:
    """
    End-to-end Retrieval-Augmented Generation pipeline:
      1. Retrieve docs from MongoDB (Atlas or fallback)
      2. Build context string
      3. Format prompt
      4. Call Azure OpenAI
      5. Return structured result
    """
    # --- Step 1: Retrieve ---
    try:
        docs = retrieval.mongodb_vector_search(question, top_k=top_k)
        if not docs:
            raise RuntimeError("Atlas returned no results")
    except Exception:
        docs = retrieval.fallback_search(question, top_k=top_k)

    normalized = []
    for d in docs:
        normalized.append({
            "_id": d.get("_id"),
            "text": d.get("text", ""),
            "source": d.get("source") or f"doc_{d.get('_id')}",
            "score": d.get("score")
        })

    if debug:
        print(f"🔎 Retrieved {len(normalized)} docs")

    # --- Step 2: Build context ---
    context = build_context_from_docs(normalized)

    # --- Step 3: Format prompt ---
    user_prompt = llm.build_user_prompt(context, question)

    # --- Step 4: Call LLM ---
    answer = llm.call_azure_chat(llm.SYSTEM_PROMPT, user_prompt, debug=debug)

    # --- Step 5: Detect used sources ---
    used_sources = []
    for d in normalized:
        if f"[source:{d['source']}]" in answer:
            used_sources.append(d["source"])

    return {
        "question": question,
        "answer": answer,
        "docs": normalized,
        "sources": used_sources,
        "context": context,
    }


# =========================
# 3. Demo
# =========================
if __name__ == "__main__":
    demo_q = "Who created Python and when?"
    res = run_rag_pipeline(demo_q, debug=True)

    print("\n=== FINAL RAG RESULT ===")
    print("Q:", res["question"])
    print("A:", res["answer"])
    print("Sources:", res["sources"])
    print("Retrieved docs:", [d["_id"] for d in res["docs"]])
