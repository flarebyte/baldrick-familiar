from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
DATA_DIR = Path("temp/data")
INDEX_DIR = Path("temp/llama")
INDEX_NAME = "default_index"

INDEX_PATH = INDEX_DIR / INDEX_NAME
INDEX_PATH.mkdir(parents=True, exist_ok=True)

documents = SimpleDirectoryReader(DATA_DIR).load_data()

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

index.storage_context.persist(persist_dir=INDEX_PATH)

print(f"✅ Index saved to: {INDEX_PATH}")
