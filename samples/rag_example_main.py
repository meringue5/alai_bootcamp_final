"""
Build a simple langgraph conversation agent that can answer questions about a given text, based on RAGs.
It should continue conversation loop with user, unless user types FINISH.
given text: joddal.pdf

source code should follow the pipleline below:
- Extraction: The document is written in Korean. It consits of multiple pages with tables and comments. Choose a suitable extractor.
- Splitting: Use SemanticChunkSplitter
- Embedding & Vector Store: Use FAISS
- Retriever: MultiQueryRetriever
  - Use "langchain.retrievers.multi_query" logger with INFO level.
  - Prompt template:
    You are an AI language model assistant. 
    Your task is to generate five different versions of the given user question to retrieve relevant documents from a vector database. 
    By generating multiple perspectives on the user question, your goal is to help the user overcome some of the limitations of the distance-based similarity search. 
    Your response should be a list of values separated by new lines, eg: `foo\nbar\nbaz\n`

    #ORIGINAL QUESTION: 
    {question}

    #Answer in Korean:
  - Create LLM chain in LCEL.

To understand how to implement, sample_rag.py can be used as a reference.
"""

import os
import logging
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# MultiQueryRetriever의 로깅 레벨을 INFO로 설정합니다.
logging.basicConfig(level=logging.INFO)
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

# AOAI 환경변수 세팅
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")
AOAI_API_KEY = os.getenv("AOAI_API_KEY")
AOAI_DEPLOY_GPT4O = os.getenv("AOAI_DEPLOY_GPT4O")
AOAI_DEPLOY_GPT4O_MINI = os.getenv("AOAI_DEPLOY_GPT4O_MINI")
AOAI_DEPLOY_EMBED_3_LARGE = os.getenv("AOAI_DEPLOY_EMBED_3_LARGE")

# 1. Extraction: PDF 문서 로드
loader = PyMuPDFLoader("joddal.pdf")
docs = loader.load()

# 3. Embedding & Vector Store: FAISS 임베딩 모델 생성
embeddings = AzureOpenAIEmbeddings(
    model=AOAI_DEPLOY_EMBED_3_LARGE,
    openai_api_version="2024-02-01",
    api_key=AOAI_API_KEY,
    azure_endpoint=AOAI_ENDPOINT
)

# 2. Splitting: SemanticChunker로 문서 분할 (임베딩 객체 필요)
chunker = SemanticChunker(embeddings)
split_documents = chunker.split_documents(docs)

# 분할된 문서로 벡터스토어 생성
vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

# 4. Retriever: MultiQueryRetriever 설정
multi_query_prompt = PromptTemplate.from_template(
    """You are an AI language model assistant. \nYour task is to generate five different versions of the given user question to retrieve relevant documents from a vector database. \nBy generating multiple perspectives on the user question, your goal is to help the user overcome some of the limitations of the distance-based similarity search. \nYour response should be a list of values separated by new lines, eg: `foo\nbar\nbaz\n`\n\n#ORIGINAL QUESTION: \n{question}\n\n#Answer in Korean:"""
)
llm_for_retriever = AzureChatOpenAI(
    openai_api_version="2024-02-01",
    azure_deployment=AOAI_DEPLOY_GPT4O_MINI,
    temperature=0.0,
    api_key=AOAI_API_KEY,
    azure_endpoint=AOAI_ENDPOINT
)

retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=llm_for_retriever,
    prompt=multi_query_prompt
)

# 5. LLM Chain in LCEL: QA 프롬프트 및 체인 생성
qa_prompt = PromptTemplate.from_template(
    """You are an assistant for question-answering tasks.\nUse the following pieces of retrieved context to answer the question.\nIf you don't know the answer, just say that you don't know.\nAnswer in Korean.\n\n#Context:\n{context}\n\n#Question:\n{question}\n\n#Answer:"""
)
llm_for_qa = AzureChatOpenAI(
    openai_api_version="2024-02-01",
    azure_deployment=AOAI_DEPLOY_GPT4O_MINI,
    temperature=0.0,
    api_key=AOAI_API_KEY,
    azure_endpoint=AOAI_ENDPOINT
)
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | qa_prompt
    | llm_for_qa
    | StrOutputParser()
)

# 유니코드 인코딩 문제 방지를 위한 입력 텍스트 정제 함수
# (surrogate 등 문제 문자를 제거/치환)
def sanitize_text(text):
    # 유니코드 인코딩 에러 방지용
    return text.encode("utf-8", "replace").decode("utf-8")

# 6. 대화 루프: FINISH 입력 시까지 반복
print("질문을 입력하세요. 종료하려면 'FINISH'를 입력하세요.")
while True:
    user_input = input("\n질문: ")
    if user_input.strip().upper() == "FINISH":
        print("대화를 종료합니다.")
        break
    sanitized_input = sanitize_text(user_input)  # 입력값 정제
    response = chain.invoke(sanitized_input)
    print(f"\n답변: {response}\n")



