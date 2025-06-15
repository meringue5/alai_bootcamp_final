# 코드 검색을 위한 벡터스토어 클래스 정의
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from embeddings import get_embedding_model
import config

class VectorStore:
    def __init__(self, embedding_model=None, **kwargs):
        # 임베딩 모델이 없으면 기본 모델 사용
        if embedding_model is None:
            embedding_model = get_embedding_model()
        self.embedding_model = embedding_model
        self.vectorstore = FAISS(embedding_function=self.embedding_model.embed_query, **kwargs)

    def add_documents(self, documents):
        """문서 리스트를 벡터스토어에 추가합니다."""
        docs = [Document(page_content=doc) for doc in documents]
        self.vectorstore.add_documents(docs)

    def similarity_search(self, query, k=4):
        """쿼리와 유사한 문서를 검색합니다."""
        return self.vectorstore.similarity_search(query, k=k)

    def save(self, path):
        """벡터스토어를 파일로 저장합니다."""
        self.vectorstore.save(path)

    def load(self, path):
        """벡터스토어를 파일에서 불러옵니다."""
        self.vectorstore = FAISS.load(path, self.embedding_model.embed_query)
