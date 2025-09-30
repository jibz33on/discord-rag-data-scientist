# 📘 Learning Guide: RAG Chatbot with MongoDB & Azure OpenAI

This guide explains the complete workflow of building a Retrieval-Augmented Generation (RAG) chatbot.  
It breaks down each section of the notebook with detailed explanations and **paper sketches** (ASCII diagrams).

---

## 🔹 Section 1: Knowledge Base

**Goal:** Convert raw text into structured documents.

- Start with long raw text documents.
- Convert each into a LangChain `Document` object:
  - `page_content` → actual text
  - `metadata` → labels (`source`, `doc_id`)

**Paper Sketch:**
```text
[Raw long docs]
    ├─ Doc 1: "Python is a high-level language..."
    ├─ Doc 2: "Machine learning is a subset of AI..."
    ├─ Doc 3: "Web development involves..."
    └─ Doc 4: "Discord bots are applications..."

     │
     ▼

[LangChain Documents]
    ├─ Document(page_content="Python...", metadata={"source": "doc_1", "doc_id": 0})
    ├─ Document(page_content="Machine learning...", metadata={"source": "doc_2", "doc_id": 1})
    ├─ Document(page_content="Web development...", metadata={"source": "doc_3", "doc_id": 2})
    └─ Document(page_content="Discord bots...", metadata={"source": "doc_4", "doc_id": 3})

---

## 🔹 Section 2: Chunking & Splitting

**Goal:** Break down long documents into smaller, overlapping chunks.

- Use `RecursiveCharacterTextSplitter` (chunk_size = 1000, overlap = 50).
- Overlap prevents losing boundary info.
- Extract `chunks_texts` for embeddings.

**Paper Sketch:**
```text
[LangChain Documents]
     │
     ▼
RecursiveCharacterTextSplitter (chunk_size=1000, overlap=50)
     │
     ▼
Chunks created:
    ├─ Chunk 1 (1000 chars)
    ├─ Chunk 2 (last 50 overlap + 950 new)
    └─ Chunk 3 (and so on...)

Each chunk keeps:
    page_content = "chunk text"
    metadata = {"source": "doc_X", "doc_id": Y}
🔹 Section 3: Embeddings
Goal: Represent chunks as vectors.

Use all-MiniLM-L6-v2 (SentenceTransformer).

Each chunk → 384-dim embedding.

Collect all embeddings in doc_embeddings (matrix: num_chunks × 384).

Pair embeddings back with chunk text + metadata to form documents_to_insert.

Paper Sketch:

text
Copy code
[Chunk Texts]
     │
     ▼
Embedding Model (MiniLM-L6-v2)
     │
     ▼
doc_embeddings (num_chunks × 384)
     ├─ [0.12, -0.45, 0.33, ...] ← Chunk 1
     ├─ [0.05,  0.99, -0.10, ...] ← Chunk 2
     └─ [0.77, -0.21,  0.14, ...] ← Chunk 3

     │
     ▼
documents_to_insert:
    ├─ {"_id": 0, "text": "Python...", "embedding": [...], "source": "doc_1"}
    ├─ {"_id": 1, "text": "Machine learning...", "embedding": [...], "source": "doc_2"}
    └─ {"_id": 2, "text": "Web development...", "embedding": [...], "source": "doc_3"}
🔹 Section 4: MongoDB Atlas Integration
Goal: Store vectors in a database and enable semantic search.

Insert documents_to_insert into MongoDB Atlas.

Create a vector index (numDimensions = 384, metric = cosine).

Run queries by embedding user input and searching with $vectorSearch.

Retrieve top-k most similar chunks.

Paper Sketch:

text
Copy code
Insert:
[documents_to_insert] ──> MongoDB Collection

Index:
Index name = vector_index
Path = embedding
numDimensions = 384
similarity = cosine

Query:
User Q = "Who created Python?"
     │
     ▼
Embed Query → [384-dim vector]
     │
     ▼
$vectorSearch in MongoDB
     │
     ▼
Top-k docs returned:
    ├─ {"_id": 0, "text": "Python created by Guido...", "source": "doc_1", "score": 0.99}
    └─ {"_id": 3, "text": "Python emphasizes readability...", "source": "doc_1", "score": 0.87}
🔹 Section 5: LLM Integration & Prompt Engineering
Goal: Make the LLM answer only from retrieved context (avoid hallucination).

Configure Azure OpenAI GPT-3.5 Turbo.

Create prompts:

System prompt → strict rules (only use provided context, cite sources, say “I don’t know” if missing).

User prompt → inserts {context} and {question}.

Build context from retrieved documents using build_context_from_docs().

Call Azure GPT with call_azure_chat().

rag_query() = retrieval + context + prompt + LLM → answer.

Paper Sketch:

text
Copy code
User Question: "Who created Python?"
     │
     ▼
MongoDB Vector Search → Top-k Docs
     │
     ▼
build_context_from_docs()
     │
     ▼
Context string:
    [source:doc_1] Python was created by Guido van Rossum in 1991.

Prompt:
SYSTEM_PROMPT = "Answer ONLY using context. Cite sources."
USER_PROMPT =
    CONTEXT:
    [source:doc_1] Python...

    QUESTION:
    Who created Python?

    ANSWER:

     │
     ▼
Azure GPT-3.5 Turbo
     │
     ▼
Answer:
"Python was created by Guido van Rossum in 1991. [source:doc_1]"
🔹 Section 6: Full RAG Pipeline
Goal: Orchestrate the entire workflow into a single function.

retrieve_docs_for_query() → embed query, run Atlas $vectorSearch, fallback if needed, normalize results.

build_rag_prompt() → build context string from retrieved docs + insert into system/user templates.

call_llm_for_rag() → wrapper around Azure GPT call.

run_rag_pipeline() → end-to-end: retrieve → prompt → LLM → extract sources → return structured result.

Paper Sketch:

text
Copy code
[User Question]
     │
     ▼
retrieve_docs_for_query()
   (embed query → Atlas vectorSearch → fallback if needed)
     │
     ▼
Top-k Docs (normalized: _id, text, source, score)
     │
     ▼
build_rag_prompt()
   (assemble context string + system & user prompts)
     │
     ▼
call_llm_for_rag()
   (send prompts to Azure GPT-3.5 Turbo)
     │
     ▼
Azure GPT → Answer
     │
     ▼
Extract sources [source:doc_X]
     │
     ▼
Return structured result:
{
  "question": "Who created Python?",
  "answer": "Python was created by Guido van Rossum in 1991. [source:doc_1]",
  "docs": [...],
  "sources": ["doc_1"],
  "context": "[source:doc_1] Python..."
}
✅ Final Overview (End-to-End)
Full pipeline in one sketch:

text
Copy code
[Raw Docs] 
     ▼
LangChain Documents
     ▼
Chunking & Splitting
     ▼
Embeddings (MiniLM, 384-dim)
     ▼
MongoDB Atlas (vector index)
     ▼
User Query → Embed
     ▼
MongoDB $vectorSearch → Top-k Docs
     ▼
Context Builder → Prompt
     ▼
Azure GPT-3.5 Turbo
     ▼
Answer (grounded + citations)
