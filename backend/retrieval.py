# backend/retrieval.py

import numpy as np
from pymongo import MongoClient

import config
from backend.embeddings import embed_texts   # 🔑 re-use embeddings.py

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

def insert_documents(chunks):
    """
    Embed texts and insert into MongoDB.
    :param chunks: list of text strings
    """
    embeddings = embed_texts(chunks)   # 🔑 call embeddings.py
    documents_to_insert = []
    for i, (text, emb) in enumerate(zip(chunks, embeddings)):
        documents_to_insert.append({
            "_id": i,
            "text": text,
            "embedding": emb.tolist(),
            "source": f"doc_{i+1}"
        })

    collection.delete_many({})  # clear old data
    collection.insert_many(documents_to_insert)

    print(f"✅ Inserted {len(documents_to_insert)} documents into MongoDB.")


def mongodb_vector_search(query_text, top_k=3):
    """
    Atlas Vector Search using $vectorSearch.
    """
    q_emb = embed_texts([query_text])[0].tolist()   # 🔑 use embed_texts
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
    """
    Manual cosine similarity fallback if Atlas $vectorSearch not available.
    """
    q_emb = np.asarray(embed_texts([query_text])[0], dtype=np.float32)  # 🔑 reuse embeddings.py
    qnorm = np.linalg.norm(q_emb)
    sims = []

    for d in collection.find({}, {"_id": 1, "text": 1, "source": 1, "embedding": 1}):
        d_emb = np.asarray(d["embedding"], dtype=np.float32)
        denom = qnorm * np.linalg.norm(d_emb)
        score = float(np.dot(q_emb, d_emb) / denom) if denom != 0 else 0.0
        sims.append({"_id": d["_id"], "text": d["text"], "source": d["source"], "score": score})

    return sorted(sims, key=lambda x: x["score"], reverse=True)[:top_k]


def test_search():
    """Quick demo of retrieval."""
    query = "What is Python programming?"
    print(f"\n🔎 Query: {query}")

    try:
        results = mongodb_vector_search(query, top_k=3)
        if results:
            print("✅ Atlas Vector Search Results:")
            for r in results:
                print(f" - {r['source']} | score={r['score']:.4f}")
            return
    except Exception as e:
        print("⚠️ Atlas search failed, falling back:", str(e))

    results = fallback_search(query, top_k=3)
    print("🟡 Fallback Results:")
    for r in results:
        print(f" - {r['source']} | score={r['score']:.4f}")


# =========================
# Run test if executed directly
# =========================
if __name__ == "__main__":
    chunks = [
        "Python is a high-level programming language created by Guido van Rossum in 1991.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data automatically."
    ]
    insert_documents(chunks)
    test_search()
