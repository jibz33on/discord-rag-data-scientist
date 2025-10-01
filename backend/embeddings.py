
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


from sentence_transformers import SentenceTransformer
import config

# keep model in memory so it’s not reloaded every call
_model = None  

def get_model():
    """load the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(config.MODEL_NAME)
        print(f"✅ Loaded embedding model: {config.MODEL_NAME}")
    return _model


def embed_texts(texts):
    """
    Embed a list of texts into vectors.
    Returns a numpy array of shape (n, EMBED_DIM).
    """
    model = get_model()
    return model.encode(texts, convert_to_numpy=True)


# Quick demo 
if __name__ == "__main__":
    sample = ["Python is a programming language.", "Machine learning lets computers learn from data."]
    vectors = embed_texts(sample)
    print("Embedding shape:", vectors.shape)
    print("First vector (preview):", vectors[0][:8])

    try:
        EMBED_DIM = int(vectors.shape[1])
        print("Inferred EMBED_DIM from embeddings.py:", EMBED_DIM)
    except Exception as e:
        print("Could not infer EMBED_DIM:", e)
