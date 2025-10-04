from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

documents = SimpleDirectoryReader("temp/data").load_data()

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

llm = Ollama(model="gemma3:1b")
query_engine = index.as_query_engine(llm=llm)

response = query_engine.query("How do I use regex in aws athena")
print(response)