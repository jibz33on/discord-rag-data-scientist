# Discord RAG FAQ Chatbot

> A production-grade RAG pipeline deployed as a Discord bot — answers domain-specific FAQ queries using Azure OpenAI, MongoDB Atlas vector search, and a benchmark-validated retrieval system.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-GPT--3.5_Turbo-0078D4?logo=microsoftazure)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB_Atlas-Vector_DB-47A248?logo=mongodb)](https://www.mongodb.com/atlas)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?logo=discord&logoColor=white)](https://discord.com/developers)

---

## Results

| Metric | Score |
|--------|-------|
| Test accuracy | **100%** |
| Average token overlap vs. reference answers | **69.2%** |
| Evaluation method | Structured benchmark dataset |
| Retrieval | Top-3 documents per query |

Evaluated against a structured benchmark dataset with reference answer pairs. 100% of test queries returned a relevant response; token overlap measures how closely generated answers match reference text, accounting for paraphrase.

---

## What This Is

A Discord bot that answers FAQ questions using a full RAG stack — not keyword matching, not a static lookup table. Documents are chunked and embedded upfront; at query time, MongoDB Atlas vector search retrieves the top-3 most semantically relevant chunks, which are passed as context to GPT-3.5 Turbo.

The data science component is the full pipeline: ingestion, preprocessing, chunking strategy, embedding, vector store indexing, retriever config, and systematic evaluation. The Discord bot is the delivery mechanism.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Data Layer (MongoDB Atlas)                                  │
│  Raw docs → chunked → embedded → stored as vector docs       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Processing Layer (RAG Pipeline)                             │
│  Query → Sentence Transformers embed → Atlas vector search   │
│  → top-3 chunks → prompt assembly → Azure OpenAI generate   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Interface Layer (Discord Bot + FastAPI)                     │
│  Discord message → FastAPI endpoint → RAG pipeline → reply  │
└─────────────────────────────────────────────────────────────┘
```

### Ingestion Pipeline

```
Raw Documents
    → Text extraction + cleaning
    → Chunking (fixed-size with overlap)
    → Sentence Transformers embeddings
    → MongoDB Atlas vector collection
```

### Query Pipeline

```
Discord Message
    → FastAPI receives query
    → Embed query (Sentence Transformers)
    → MongoDB Atlas $vectorSearch (top-3)
    → Construct prompt: [system] + [retrieved context] + [user query]
    → Azure OpenAI GPT-3.5 Turbo
    → Post reply to Discord channel
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Azure OpenAI GPT-3.5 Turbo |
| Vector database | MongoDB Atlas Vector Search |
| Embeddings | Sentence Transformers |
| RAG framework | LangChain |
| API layer | FastAPI |
| Bot interface | Discord.py |
| Language | Python 3.11 |

---

## Setup

### Prerequisites

- Python 3.11+
- MongoDB Atlas cluster with vector search enabled
- Azure OpenAI deployment (GPT-3.5 Turbo)
- Discord bot token

### Installation

```bash
git clone https://github.com/jibz33on/discord-rag-data-scientist
cd discord-rag-data-scientist

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

```env
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo
MONGODB_URI=mongodb+srv://...
MONGODB_DB=rag_db
MONGODB_COLLECTION=documents
DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=...
```

### Ingest Documents

```bash
python scripts/ingest.py --docs-dir ./data/docs
```

This chunks documents, generates embeddings, and upserts to MongoDB Atlas.

### Run

```bash
# Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# Start Discord bot
python bot/discord_bot.py
```

---

## Project Structure

```
discord-rag-data-scientist/
├── app/
│   ├── main.py             # FastAPI app
│   └── rag_pipeline.py     # Core RAG logic
├── bot/
│   └── discord_bot.py      # Discord bot client
├── scripts/
│   ├── ingest.py           # Document ingestion
│   └── evaluate.py         # Benchmark evaluation
├── data/
│   ├── docs/               # Source documents
│   └── benchmark/          # Evaluation dataset (Q&A pairs)
├── embeddings/
│   └── encoder.py          # Sentence Transformers wrapper
└── requirements.txt
```

---

## Evaluation

The retrieval and generation pipeline was validated against a structured benchmark dataset of question-answer pairs:

```bash
python scripts/evaluate.py --benchmark data/benchmark/qa_pairs.json
```

Metrics computed:
- **Accuracy:** Did the system return a response? (100%)
- **Token overlap:** ROUGE-style token overlap between generated and reference answers (69.2% average)

This isn't a vanity metric — token overlap at 69.2% on paraphrased reference answers indicates the model is retrieving correct context and generating substantively correct responses, not just fluent-sounding ones.

---

## Author

**Jibin Kunjumon** — AI Engineer  
[GitHub](https://github.com/jibz33on) · [LinkedIn](https://linkedin.com/in/jibin-kunjumon)
