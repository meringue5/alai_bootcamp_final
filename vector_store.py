# 코드 검색을 위한 벡터스토어 클래스 정의
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from embeddings import get_embedding_model
import config

class VectorStore:
    def __init__(self, embedding_model=None, **kwargs):
        """간단한 FAISS 벡터스토어 래퍼"""

        if embedding_model is None:
            embedding_model = get_embedding_model()
        self.embedding_model = embedding_model
        # 초기에는 인덱스를 생성하지 않는다 (임베딩 호출 방지)
        self.vectorstore = None

    def add_documents(self, documents):
        """문서 리스트를 벡터스토어에 추가합니다."""
        docs = [Document(page_content=doc) for doc in documents]
        if self.vectorstore is None:
            # 첫 추가 시점에 인덱스 생성
            self.vectorstore = FAISS.from_documents(docs, self.embedding_model)
        else:
            self.vectorstore.add_documents(docs)

    def similarity_search(self, query, k=4):
        """쿼리와 유사한 문서를 검색합니다."""
        if self.vectorstore is None:
            return []
        return self.vectorstore.similarity_search(query, k=k)

    def save(self, path):
        """벡터스토어를 파일로 저장합니다."""
        if self.vectorstore is not None:
            self.vectorstore.save(path)

    def load(self, path):
        """벡터스토어를 파일에서 불러옵니다."""
        self.vectorstore = FAISS.load(path, self.embedding_model.embed_query)
