from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

INDEX_PATH = Path("temp/llama/default_index")

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = Ollama(model="gemma3:1b")

storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
index = load_index_from_storage(storage_context, embed_model=embed_model)

query_engine = index.as_query_engine(llm=llm)
response = query_engine.query("What is baldrick pest ?")
print(response)
