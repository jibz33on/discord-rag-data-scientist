# Embedding models — research & comparison

---

## Goal

Short, practical research note to compare embedding options for RAG / semantic search / clustering.  
Highlight strengths, weaknesses, typical use cases, and an evaluation plan so you can select one for the assignment.

---

## Quick summary (one-liners)

- **Sentence Transformers (SBERT)** — proven semantic embeddings, many open-source variants; good for reproducible experiments and on-prem.  
- **BGE (e.g., bge-en-large, bge-m3)** — strong open-source all-rounder for RAG, consistently top performer in clinical IR and general retrieval.  
- **nomic-embed-text** — lightweight open-source embedder; fast, good for short/direct queries.  
- **mxbai-embed-large** — balanced mid-size model; better for long/contextual queries than nomic.  
- **SFR-Embedding-Mistral** — fine-tuned large model optimized for embeddings; strong but compute-heavy.  
- **OpenAI Embeddings** — high-quality managed API (e.g., `text-embedding-3-large`); easy integration, costly at scale.  
- **Cohere / Voyage AI** — API-first alternatives to OpenAI; strong multilingual and enterprise-ready.  
- **Hugging Face models (general)** — wide selection, flexible, and fine-tuneable; quality varies, benchmarking needed.  

---

## What to compare (evaluation criteria)

1. **Semantic quality** — retrieval Recall@K, MRR, clustering purity.  
2. **Latency / throughput** — time per embedding, batch efficiency.  
3. **Cost** — API $ per 1k tokens vs infra cost for self-hosted.  
4. **Memory / size** — embedding dimension & model weights.  
5. **Licensing & restrictions** — open-source license vs API terms.  
6. **Language & domain support** — multilingual, medical, legal robustness.  
7. **Ease of deployment** — managed API vs self-hosting setup.  
8. **Ecosystem integrations** — vector DB and framework support.  

---

## Decision guidance (at-a-glance)

| Model family                | Best when… |
|-----------------------------|------------|
| **SBERT / MiniLM**          | You want small, fast, reproducible embeddings on-prem. |
| **BGE (bge-en-large / m3)** | You want a strong, open-source general-purpose embedder for RAG (context-heavy queries). |
| **nomic-embed-text**        | You’re resource-limited and mostly handle short, direct queries. |
| **mxbai-embed-large**       | You need a middle ground: better than nomic, lighter than bge-m3. |
| **SFR-Embedding-Mistral**   | You have GPU infra and want high-quality embeddings from a large fine-tuned model. |
| **OpenAI / Cohere / Voyage**| You want fast prototyping or production-ready embeddings via API, and can afford cost/privacy tradeoffs. |
| **Hugging Face encoders**   | You want flexibility to fine-tune for a specific domain. |

---

## Comparison table (fill in after experiments)

| Model                        | Dim  | Size  | Latency (ms/q) | Recall@5 |   MRR | Cost (est) | License  | Notes |
|-------------------------------|-----:|------:|---------------:|---------:|------:|-----------:|---------:|-------|
| SBERT: all-MiniLM-L6-v2       |  384 |  33M  |               - |       -  |    -  | free/self  | MIT      | Fast, compact baseline |
| BGE-en-large-v1.5             | 1024 | 335M  |               - |       -  |    -  | free/self  | Apache-2 | Strong general IR model |
| bge-m3                        | 1024 | 567M  |               - |    0.72 | 0.68  | free/self  | Apache-2 | Top open-source performer; excels at long/contextual Qs |
| nomic-embed-text              |  768 | 137M  |               - |    0.57 |    -  | free/self  | Apache-2 | Lightweight; strong on short queries |
| mxbai-embed-large             | 1024 | 334M  |               - |    0.59 |    -  | free/self  | Apache-2 | Balanced; good for contextual queries |
| SFR-Embedding-Mistral         | 4096 |   7B  |               - |       -  |    -  | free/self  | Apache-2 | Fine-tuned large model; strong but resource-heavy |
| OpenAI text-embedding-3-large | 3072 | API   |              35 |    0.80 | 0.72 | $$ / API   | API-only | High-quality, easy to integrate |
| Cohere embeddings             | 1024+| API   |               - |       -  |    -  | $$ / API   | API-only | Multilingual, enterprise support |
| Voyage AI embeddings          | 1024+| API   |               - |       -  |    -  | $$ / API   | API-only | Optimized for RAG, competitive with OpenAI |

*(Replace “-” with measured values after your own evaluation.)*

---

## Short write-ups (per family)

### SentenceTransformers (SBERT)
- **Strengths:** proven baseline; many pre-trained variants tuned for semantic similarity; efficient.  
- **Weaknesses:** infra management at scale; some models slow on CPU.  
- **When to use:** reproducible research, offline experiments, cost-sensitive projects.  

### BGE (bge-en-large, bge-m3)
- **Strengths:** consistently top-performing in clinical IR & RAG benchmarks; good efficiency; open-source.  
- **Weaknesses:** mid-size; embedding generation slower than smallest models.  
- **When to use:** default open-source embedder for most RAG apps.  

### nomic-embed-text
- **Strengths:** small, fast, lightweight; good for short/direct queries.  
- **Weaknesses:** struggles with implied or long-context queries.  
- **When to use:** resource-limited scenarios, low-latency apps.  

### mxbai-embed-large
- **Strengths:** better at long/contextual queries; good tradeoff size vs perf.  
- **Weaknesses:** slower than nomic, less strong than bge-m3.  
- **When to use:** middle ground between small and large open-source models.  

### SFR-Embedding-Mistral
- **Strengths:** fine-tuned for embeddings; outperforms vanilla Mistral.  
- **Weaknesses:** very resource-heavy.  
- **When to use:** high-end infra with need for strong embeddings.  

### OpenAI / Cohere / Voyage
- **Strengths:** easy API, strong performance, no infra burden.  
- **Weaknesses:** cost, privacy risk (data leaves org), vendor lock-in.  
- **When to use:** prototyping, SaaS production, non-sensitive data.  

### Hugging Face models (general)
- **Strengths:** huge ecosystem, many specialized encoders, ability to fine-tune.  
- **Weaknesses:** quality varies; evaluation needed.  
- **When to use:** domain-specific customization and open-source experiments.  

---

## Extra note: (OpenAI vs Cohere vs E5)

A recent walkthrough compared three popular embedding options on messy, real-world data:

- **OpenAI (`ada-002`, 1536 dims):** strong baseline, reliable, but higher storage footprint and slower ingestion than Cohere.  
- **Cohere embeddings (1024 dims):** slightly faster ingestion; sometimes returned more context-rich results than OpenAI; strong multilingual support.  
- **E5 (768–1024 dims, open-source):** lightweight and efficient; base model weaker than APIs, but large variant can be competitive. Requires `passage:` / `query:` prefixing.

**Key takeaways:**  
- OpenAI = easy & strong default.  
- Cohere = good balance of quality + speed, especially for multilingual.  
- E5 = best when self-hosting or storage/cost efficiency matters (large version recommended).  

---



