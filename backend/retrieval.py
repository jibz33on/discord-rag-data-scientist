# backend/retrieval.py
import numpy as np
from pymongo import MongoClient
import config
from backend.embeddings import embed_texts  # ensure this exists
import argparse
import sys

# =========================
# 1. Connect to MongoDB
# =========================
client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB_NAME]
collection = db[config.MONGO_COLLECTION]
print(f"✅ Connected to MongoDB: {config.MONGO_DB_NAME}.{config.MONGO_COLLECTION}")

# =========================
# 2. Helper functions
# =========================
def insert_documents(chunks, wipe: bool = False):
    """
    Embed texts and insert into MongoDB.
    :param chunks: list of text strings OR list of dicts with 'text' key
    :param wipe: if True, will delete existing documents after confirmation (interactive confirmation happens in CLI only)
    """
    # Normalize to texts
    texts = [c if isinstance(c, str) else c.get('text') for c in chunks]
    embeddings = embed_texts(texts)  # returns numpy array or list-like

    documents_to_insert = []
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        documents_to_insert.append({
            "_id": i,
            "text": text,
            "embedding": np.asarray(emb).tolist(),
            "source": f"doc_{i+1}"
        })

    if wipe:
        # When called programmatically, avoid interactive confirmation here.
        # CLI will pass wipe=True only after confirmation.
        collection.delete_many({})  # actual wipe
        print("⚠️ Collection wiped (delete_many executed).")

    # Insert documents
    if len(documents_to_insert) > 0:
        collection.insert_many(documents_to_insert)
        print(f"✅ Inserted {len(documents_to_insert)} documents into MongoDB.")
    else:
        print("No documents to insert.")

def mongodb_vector_search(query_text, top_k=3):
    """ Atlas Vector Search using $vectorSearch. """
    q_emb = embed_texts([query_text])[0].tolist()
    pipeline = [
        {"$vectorSearch": {
            "index": config.INDEX_NAME,
            "path": "embedding",
            "queryVector": q_emb,
            "numCandidates": top_k * 5,
            "limit": top_k
        }},
        {"$project": {"_id": 1, "text": 1, "source": 1, "score": {"$meta": "vectorSearchScore"}}}
    ]
    return list(collection.aggregate(pipeline))

def fallback_search(query_text, top_k=3):
    """ Manual cosine similarity fallback if Atlas $vectorSearch not available. """
    q_emb = np.asarray(embed_texts([query_text])[0], dtype=np.float32)
    qnorm = np.linalg.norm(q_emb)
    sims = []
    for d in collection.find({}, {"_id": 1, "text": 1, "source": 1, "embedding": 1}):
        d_emb = np.asarray(d["embedding"], dtype=np.float32)
        denom = qnorm * np.linalg.norm(d_emb)
        score = float(np.dot(q_emb, d_emb) / denom) if denom != 0 else 0.0
        sims.append({"_id": d["_id"], "text": d["text"], "source": d["source"], "score": score})
    return sorted(sims, key=lambda x: x["score"], reverse=True)[:top_k]

def test_search(query="What is Python programming?", top_k=3):
    """Quick demo of retrieval."""
    print(f"\n🔎 Query: {query}")
    try:
        results = mongodb_vector_search(query, top_k=top_k)
        if results:
            print("✅ Atlas Vector Search Results:")
            for r in results:
                print(f" - {r['source']} | score={r['score']:.4f}")
            return results
    except Exception as e:
        print("⚠️ Atlas search failed, falling back:", str(e))

    results = fallback_search(query, top_k=top_k)
    print("🟡 Fallback Results:")
    for r in results:
        print(f" - {r['source']} | score={r['score']:.4f}")
    return results

# =========================
# CLI: allow safe insert with explicit --wipe flag
# =========================
def _cli_insert_sample_chunks(wipe: bool):
    # Example minimal chunks, replace or call insert_documents() programmatically as needed
    chunks = [
        "Python is a high-level programming language created by Guido van Rossum in 1991.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data automatically."
    ]
    insert_documents(chunks, wipe=wipe)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="Wipe collection before inserting sample documents (requires confirmation).")
    parser.add_argument("--test-search", action="store_true", help="Run test_search after inserting/connecting.")
    args = parser.parse_args()

    if args.wipe:
        confirm = input("Type YES to confirm wiping the collection and inserting sample docs: ")
        if confirm != "YES":
            print("Wipe aborted by user. No changes made.")
            sys.exit(0)
        _cli_insert_sample_chunks(wipe=True)
    else:
        print("No wipe flag provided; running without modifying collection.")
    if args.test_search:
        test_search()
