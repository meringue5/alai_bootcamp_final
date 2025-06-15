from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from .embeddings import get_embedding_model
from . import config


class CodeVectorStore:
    def __init__(self, path: str = config.VECTORSTORE_PATH):
        self.path = path
        self.embeddings = get_embedding_model()
        try:
            self.store = FAISS.load_local(path, self.embeddings)
        except Exception:
            self.store = FAISS.from_documents([], self.embeddings)

    def add_code(self, code: str, metadata: dict | None = None):
        doc = Document(page_content=code, metadata=metadata or {})
        self.store.add_documents([doc])
        self.store.save_local(self.path)

    def similarity_search(self, query: str, k: int = 4):
        return self.store.similarity_search(query, k=k)
