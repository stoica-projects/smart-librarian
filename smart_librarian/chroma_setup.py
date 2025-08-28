from typing import List
from smart_librarian.config import CHROMA_DIR, EMBED_MODEL
from openai import OpenAI

client = OpenAI()

try:
    from chromadb import PersistentClient
    _client = PersistentClient(path=CHROMA_DIR)
except Exception:
    import chromadb
    try:
        from chromadb.config import Settings
        _client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
    except Exception:
        _client = chromadb.EphemeralClient()

try:
    from chromadb.utils.embedding_functions import EmbeddingFunction
except Exception:
    class EmbeddingFunction:
        pass

class OpenAIEmbedder(EmbeddingFunction):
    def __init__(self, openai_client: OpenAI, model: str):
        self.client = openai_client
        self.model = model
    def __call__(self, texts: List[str]):
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

embedder = OpenAIEmbedder(client, EMBED_MODEL)

def recreate_collection(name: str):
    try:
        _client.delete_collection(name)
    except Exception:
        pass
    return _client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedder,
    )

def get_collection(name: str):
    return _client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedder,
    )
